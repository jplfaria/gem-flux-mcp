"""Reaction lookup tools for ModelSEED database.

This module implements MCP tools for looking up reaction information from
the ModelSEED database (spec 009-reaction-lookup-tools.md):

Tools:
    - get_reaction_name: Retrieve metadata for a single reaction ID
    - search_reactions: Search reactions by name, enzyme, or EC number

These tools enable AI assistants to translate between ModelSEED reaction IDs
and human-readable names, equations, and metadata.
"""

import logging
from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field, field_validator

from gem_flux_mcp.database import parse_aliases, validate_reaction_id
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================


class GetReactionNameRequest(BaseModel):
    """Request format for get_reaction_name tool.

    Retrieves human-readable name and metadata for a ModelSEED reaction ID.
    """

    reaction_id: str = Field(
        ...,
        description="ModelSEED reaction ID (format: rxn00148)",
    )

    @field_validator("reaction_id", mode="before")
    @classmethod
    def validate_reaction_id_format(cls, v: str) -> str:
        """Validate reaction ID format matches rxn##### pattern."""
        # Handle empty input
        if not v or not isinstance(v, str):
            raise ValueError("Reaction ID must be a non-empty string")

        # Trim whitespace and convert to lowercase for case-insensitive matching
        v = v.strip().lower()

        # Validate format
        is_valid, error_msg = validate_reaction_id(v)
        if not is_valid:
            raise ValueError(error_msg)

        return v


class GetReactionNameResponse(BaseModel):
    """Response format for successful get_reaction_name operation.

    Contains complete reaction metadata from ModelSEED database.
    """

    success: bool = Field(default=True)
    id: str = Field(..., description="ModelSEED reaction ID")
    name: str = Field(..., description="Human-readable reaction name")
    abbreviation: str = Field(..., description="Short reaction code")
    equation: str = Field(..., description="Reaction equation with human-readable compound names")
    equation_with_ids: str = Field(..., description="Reaction equation with ModelSEED compound IDs")
    reversibility: str = Field(..., description="Reversibility type (reversible, irreversible, irreversible_reverse)")
    direction: str = Field(..., description="Preferred direction (forward, reverse, bidirectional)")
    is_transport: bool = Field(..., description="True if reaction moves compounds between compartments")
    ec_numbers: list[str] = Field(..., description="Enzyme Commission numbers")
    pathways: list[str] = Field(..., description="Metabolic pathways containing this reaction")
    deltag: Optional[float] = Field(None, description="Standard Gibbs free energy change (kJ/mol)")
    deltagerr: Optional[float] = Field(None, description="Error estimate for deltag (kJ/mol)")
    aliases: dict[str, list[str]] = Field(..., description="Cross-references to external databases")


class SearchReactionsRequest(BaseModel):
    """Request format for search_reactions tool.

    Search for reactions by name, enzyme name, EC number, or pathway.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Text to search for in reaction names, EC numbers, pathways, abbreviations, and aliases",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return (default: 10, max: 100)",
    )

    @field_validator("query", mode="before")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is non-empty after trimming."""
        if not v or not isinstance(v, str):
            raise ValueError("Search query must be a non-empty string")

        v = v.strip()
        if not v:
            raise ValueError("Search query cannot be empty after trimming whitespace")

        return v


class ReactionSearchResult(BaseModel):
    """Single reaction search result with match metadata."""

    id: str = Field(..., description="ModelSEED reaction ID")
    name: str = Field(..., description="Human-readable reaction name")
    equation: str = Field(..., description="Reaction equation with human-readable compound names")
    ec_numbers: list[str] = Field(..., description="Enzyme Commission numbers")
    match_field: str = Field(
        ...,
        description="Field where match was found (name, abbreviation, ec_numbers, pathways, aliases, id)",
    )
    match_type: str = Field(
        ..., description="Type of match (exact or partial)"
    )


class SearchReactionsResponse(BaseModel):
    """Response format for successful search_reactions operation."""

    success: bool = Field(default=True)
    query: str = Field(..., description="The search query as processed")
    num_results: int = Field(..., description="Number of results returned")
    results: list[ReactionSearchResult] = Field(
        ..., description="List of matching reactions"
    )
    truncated: bool = Field(
        ...,
        description="True if more results exist beyond limit, False otherwise",
    )
    suggestions: Optional[list[str]] = Field(
        default=None, description="Suggestions when no results found"
    )
    next_steps: list[str] = Field(
        default_factory=list, description="Suggested next steps based on results"
    )


# =============================================================================
# Helper Functions
# =============================================================================


def parse_reversibility_and_direction(reversibility_symbol: str) -> tuple[str, str]:
    """Parse reversibility symbol to readable strings.

    Args:
        reversibility_symbol: Symbol from database (>, <, or =)

    Returns:
        Tuple of (reversibility, direction)
        - reversibility: "reversible", "irreversible", or "irreversible_reverse"
        - direction: "forward", "reverse", or "bidirectional"

    Spec Reference:
        - 009-reaction-lookup-tools.md: Step 4 of get_reaction_name
    """
    if reversibility_symbol == ">":
        return ("irreversible", "forward")
    elif reversibility_symbol == "<":
        return ("irreversible_reverse", "reverse")
    elif reversibility_symbol == "=":
        return ("reversible", "bidirectional")
    else:
        # Default to reversible if unknown
        logger.warning(f"Unknown reversibility symbol: {reversibility_symbol}, defaulting to reversible")
        return ("reversible", "bidirectional")


def parse_ec_numbers(ec_numbers_raw: str) -> list[str]:
    """Parse EC numbers from database string.

    Args:
        ec_numbers_raw: Raw EC numbers string from database

    Returns:
        List of EC number strings, empty list if none

    Format Examples:
        - "2.7.1.1" -> ["2.7.1.1"]
        - "2.7.1.1; 2.7.1.2" -> ["2.7.1.1", "2.7.1.2"]
        - "2.7.1.1|2.7.1.2" -> ["2.7.1.1", "2.7.1.2"]
        - "" -> []

    Spec Reference:
        - 009-reaction-lookup-tools.md: Step 5 of get_reaction_name
    """
    # Handle pandas NA safely (check before truthiness check)
    try:
        if pd.isna(ec_numbers_raw):
            return []
    except (TypeError, ValueError):
        # If pd.isna fails, check if it's a valid string
        if not isinstance(ec_numbers_raw, str):
            return []

    if not ec_numbers_raw:
        return []

    # Split on semicolon or pipe
    ec_numbers = []
    for separator in [";", "|"]:
        if separator in ec_numbers_raw:
            parts = ec_numbers_raw.split(separator)
            ec_numbers = [ec.strip() for ec in parts if ec.strip()]
            break
    else:
        # No separator found, treat as single EC number
        ec_numbers = [ec_numbers_raw.strip()] if ec_numbers_raw.strip() else []

    return ec_numbers


def parse_pathways(pathways_raw: str) -> list[str]:
    """Parse pathways from database string.

    Args:
        pathways_raw: Raw pathways string from database

    Returns:
        List of pathway names, empty list if none

    Format Examples:
        - "Glycolysis" -> ["Glycolysis"]
        - "Glycolysis; Central Metabolism" -> ["Glycolysis", "Central Metabolism"]
        - "MetaCyc: Glycolysis (Glucose Degradation)|KEGG: rn00010 (Glycolysis / Gluconeogenesis)"
          -> ["Glycolysis", "Glycolysis / Gluconeogenesis"]
        - "" -> []

    The function extracts pathway names, removing database prefixes like "MetaCyc:"
    and descriptive text in parentheses if needed.

    Spec Reference:
        - 009-reaction-lookup-tools.md: Step 6 of get_reaction_name
        - Examples on lines 336-343
    """
    # Handle pandas NA safely (check before truthiness check)
    try:
        if pd.isna(pathways_raw):
            return []
    except (TypeError, ValueError):
        # If pd.isna fails, check if it's a valid string
        if not isinstance(pathways_raw, str):
            return []

    if not pathways_raw:
        return []

    pathways = []

    # Check if it has pipe separator (database prefix format)
    if "|" in pathways_raw:
        # Split on pipe first (for "DB: Name|DB: Name" format)
        parts = pathways_raw.split("|")

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if it has database prefix (e.g., "MetaCyc: Pathway Name")
            if ":" in part:
                # Extract pathway name after colon
                pathway_name = part.split(":", 1)[1].strip()
            else:
                pathway_name = part

            # Remove descriptive text in parentheses at the end if present
            # Example: "Glycolysis (Glucose Degradation)" -> "Glycolysis"
            # But keep parentheses in middle: "Glycolysis / Gluconeogenesis" stays as is
            if "(" in pathway_name:
                # Only remove if parentheses are at the end
                before_paren = pathway_name.split("(")[0].strip()
                if before_paren:
                    pathway_name = before_paren

            if pathway_name:
                pathways.append(pathway_name)
    elif ";" in pathways_raw:
        # Simple semicolon-separated format: "Path1; Path2"
        pathways = [p.strip() for p in pathways_raw.split(";") if p.strip()]
    else:
        # Single pathway name
        pathways = [pathways_raw.strip()] if pathways_raw.strip() else []

    return pathways


def format_equation_readable(equation_with_ids: str, definition: str) -> str:
    """Format reaction equation for human readability.

    Removes compartment suffixes from compound names for cleaner display.

    Args:
        equation_with_ids: Equation with compound IDs (e.g., "cpd00027[c0]")
        definition: Equation with compound names (e.g., "D-Glucose[0]")

    Returns:
        Human-readable equation with compartments removed

    Example:
        Input: "(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) H+[0] + (1) D-Glucose-6-phosphate[0]"
        Output: "(1) D-Glucose + (1) ATP => (1) ADP + (1) H+ + (1) D-Glucose-6-phosphate"

    Spec Reference:
        - 009-reaction-lookup-tools.md: Step 3 of get_reaction_name
        - Examples on lines 327-332
    """
    if not definition or pd.isna(definition):
        # Fallback to equation_with_ids if no definition
        return equation_with_ids.replace("[0]", "").replace("[c0]", "").replace("[e0]", "").replace("[p0]", "")

    # Remove compartment suffixes: [0], [c0], [e0], [p0]
    readable = definition.replace("[0]", "").replace("[c0]", "").replace("[e0]", "").replace("[p0]", "")

    return readable


# =============================================================================
# Tool Implementation
# =============================================================================


def get_reaction_name(
    request: GetReactionNameRequest, db_index: DatabaseIndex
) -> dict:
    """Get human-readable name and metadata for a ModelSEED reaction ID.

    This function implements the get_reaction_name MCP tool as specified in
    009-reaction-lookup-tools.md.

    Args:
        request: GetReactionNameRequest with reaction_id
        db_index: DatabaseIndex instance with loaded reactions database

    Returns:
        Dictionary with reaction metadata (GetReactionNameResponse format)

    Raises:
        NotFoundError: If reaction ID not found in database
        ValidationError: If reaction ID format is invalid

    Performance:
        - Expected time: < 1 millisecond per lookup
        - Uses O(1) indexed access

    Example:
        >>> request = GetReactionNameRequest(reaction_id="rxn00148")
        >>> response = get_reaction_name(request, db_index)
        >>> print(response["name"])
        'hexokinase'

    Spec Reference:
        - 009-reaction-lookup-tools.md: Tool specification
        - 007-database-integration.md: Database structure
        - 002-data-formats.md: ModelSEED identifier conventions
    """
    reaction_id = request.reaction_id

    logger.info(f"Looking up reaction: {reaction_id}")

    # Step 1: Query database (O(1) lookup)
    reaction_record = db_index.get_reaction_by_id(reaction_id)

    if reaction_record is None:
        # Reaction not found - return error response
        logger.warning(f"Reaction not found: {reaction_id}")
        raise NotFoundError(
            message=f"Reaction ID {reaction_id} not found in ModelSEED database",
            error_code="REACTION_NOT_FOUND",
            details={
                "reaction_id": reaction_id,
                "searched_in": f"reactions.tsv ({db_index.get_reaction_count()} reactions)",
            },
            suggestions=[
                "Check ID format: should be 'rxn' followed by exactly 5 digits",
                "Use search_reactions tool to find reactions by name or enzyme",
                "Verify ID from ModelSEED database documentation",
            ],
        )

    # Step 2: Parse equation and definition
    equation_with_ids = reaction_record.get("equation", "")
    definition = reaction_record.get("definition", "")
    equation = format_equation_readable(equation_with_ids, definition)

    # Step 3: Parse reversibility and direction
    reversibility_symbol = reaction_record.get("reversibility", "=")
    reversibility, direction = parse_reversibility_and_direction(reversibility_symbol)

    # Step 4: Parse EC numbers
    ec_numbers_raw = reaction_record.get("ec_numbers", "")
    ec_numbers = parse_ec_numbers(ec_numbers_raw)

    # Step 5: Parse pathways
    pathways_raw = reaction_record.get("pathways", "")
    pathways = parse_pathways(pathways_raw)

    # Step 6: Parse aliases
    aliases_raw = reaction_record.get("aliases", "")
    aliases_dict = parse_aliases(aliases_raw)

    # Step 7: Parse thermodynamic data
    deltag = None
    deltagerr = None
    if "deltag" in reaction_record and reaction_record["deltag"] is not None and not pd.isna(reaction_record["deltag"]):
        try:
            deltag = float(reaction_record["deltag"])
        except (ValueError, TypeError):
            pass

    if "deltagerr" in reaction_record and reaction_record["deltagerr"] is not None and not pd.isna(reaction_record["deltagerr"]):
        try:
            deltagerr = float(reaction_record["deltagerr"])
        except (ValueError, TypeError):
            pass

    # Step 8: Convert is_transport to boolean
    is_transport_value = reaction_record.get("is_transport", 0)
    is_transport = bool(is_transport_value) if not pd.isna(is_transport_value) else False

    # Step 9: Build response
    response = GetReactionNameResponse(
        id=reaction_id,
        name=reaction_record["name"],
        abbreviation=reaction_record.get("abbreviation", ""),
        equation=equation,
        equation_with_ids=equation_with_ids,
        reversibility=reversibility,
        direction=direction,
        is_transport=is_transport,
        ec_numbers=ec_numbers,
        pathways=pathways,
        deltag=deltag,
        deltagerr=deltagerr,
        aliases=aliases_dict,
    )

    logger.info(f"Successfully retrieved reaction: {reaction_id} ({response.name})")

    return response.model_dump()


def search_reactions(request: SearchReactionsRequest, db_index: DatabaseIndex) -> dict:
    """Search for reactions by name, enzyme, EC number, pathway, or alias.

    This function implements the search_reactions MCP tool as specified in
    009-reaction-lookup-tools.md.

    Args:
        request: SearchReactionsRequest with query and optional limit
        db_index: DatabaseIndex instance with loaded reactions database

    Returns:
        Dictionary with search results (SearchReactionsResponse format)

    Performance:
        - Expected time: 10-100 milliseconds per search
        - Uses O(n) linear search (acceptable for MVP)

    Search Strategy (spec 009):
        1. Exact ID match
        2. Exact name match (case-insensitive)
        3. Exact abbreviation match (case-insensitive)
        4. EC number match (exact)
        5. Partial name match (case-insensitive)
        6. Alias match (case-insensitive)
        7. Pathway match (case-insensitive)

    Example:
        >>> request = SearchReactionsRequest(query="hexokinase", limit=5)
        >>> response = search_reactions(request, db_index)
        >>> print(f"Found {response['num_results']} reactions")
        Found 3 reactions

    Spec Reference:
        - 009-reaction-lookup-tools.md: Tool specification (Task 34)
        - 007-database-integration.md: Search operations
    """
    query = request.query.strip().lower()
    limit = request.limit

    logger.info(f"Searching reactions: query='{query}', limit={limit}")

    # Track all matches with their priority and metadata
    matches: list[tuple[int, pd.Series, str, str]] = []
    # Format: (priority, reaction_record, match_field, match_type)
    # Priority: lower number = higher priority (1 = exact ID, 2 = exact name, etc.)

    reactions_df = db_index.reactions_df

    # Step 1: Exact ID match (priority 1)
    if db_index.reaction_exists(query):
        reaction = db_index.get_reaction_by_id(query)
        if reaction is not None:
            matches.append((1, reaction, "id", "exact"))
            logger.debug(f"Found exact ID match: {query}")

    # Step 2: Exact name match (priority 2)
    exact_name_matches = reactions_df[reactions_df["name_lower"] == query]
    for _, reaction in exact_name_matches.iterrows():
        matches.append((2, reaction, "name", "exact"))
    if len(exact_name_matches) > 0:
        logger.debug(f"Found {len(exact_name_matches)} exact name matches")

    # Step 3: Exact abbreviation match (priority 3)
    exact_abbr_matches = reactions_df[reactions_df["abbreviation_lower"] == query]
    for _, reaction in exact_abbr_matches.iterrows():
        matches.append((3, reaction, "abbreviation", "exact"))
    if len(exact_abbr_matches) > 0:
        logger.debug(f"Found {len(exact_abbr_matches)} exact abbreviation matches")

    # Step 4: EC number match (priority 4)
    # Search in ec_numbers column (case-insensitive)
    ec_matches = reactions_df[
        reactions_df["ec_numbers"].str.lower().str.contains(query, na=False, regex=False)
    ]
    for _, reaction in ec_matches.iterrows():
        matches.append((4, reaction, "ec_numbers", "exact"))
    if len(ec_matches) > 0:
        logger.debug(f"Found {len(ec_matches)} EC number matches")

    # Step 5: Partial name match (priority 5)
    partial_name_matches = reactions_df[
        reactions_df["name_lower"].str.contains(query, na=False, regex=False)
        & (reactions_df["name_lower"] != query)  # Exclude exact matches already found
    ]
    for _, reaction in partial_name_matches.iterrows():
        matches.append((5, reaction, "name", "partial"))
    if len(partial_name_matches) > 0:
        logger.debug(f"Found {len(partial_name_matches)} partial name matches")

    # Step 6: Alias match (priority 6)
    # Check if query appears in aliases column (case-insensitive)
    alias_matches = reactions_df[
        reactions_df["aliases"].str.lower().str.contains(query, na=False, regex=False)
    ]
    for _, reaction in alias_matches.iterrows():
        matches.append((6, reaction, "aliases", "partial"))
    if len(alias_matches) > 0:
        logger.debug(f"Found {len(alias_matches)} alias matches")

    # Step 7: Pathway match (priority 7)
    # Check if query appears in pathways column (case-insensitive)
    pathway_matches = reactions_df[
        reactions_df["pathways"].str.lower().str.contains(query, na=False, regex=False)
    ]
    for _, reaction in pathway_matches.iterrows():
        matches.append((7, reaction, "pathways", "partial"))
    if len(pathway_matches) > 0:
        logger.debug(f"Found {len(pathway_matches)} pathway matches")

    # Remove duplicates (keep first occurrence with highest priority)
    seen_ids = set()
    unique_matches = []
    for priority, reaction, match_field, match_type in sorted(matches, key=lambda x: x[0]):
        reaction_id = reaction.name  # pandas Series.name is the index value
        if reaction_id not in seen_ids:
            seen_ids.add(reaction_id)
            unique_matches.append((priority, reaction, match_field, match_type))

    # Sort by priority, then alphabetically by name
    unique_matches.sort(key=lambda x: (x[0], x[1]["name"].lower()))

    # Check if truncated
    total_matches = len(unique_matches)
    truncated = total_matches > limit

    # Limit results
    limited_matches = unique_matches[:limit]

    # Build results list
    results = []
    for priority, reaction, match_field, match_type in limited_matches:
        # Format equation for human readability
        equation_with_ids = reaction.get("equation", "")
        definition = reaction.get("definition", "")
        equation = format_equation_readable(equation_with_ids, definition)

        # Parse EC numbers
        ec_numbers_raw = reaction.get("ec_numbers", "")
        ec_numbers = parse_ec_numbers(ec_numbers_raw)

        result = ReactionSearchResult(
            id=reaction.name,  # Series.name is the index value ('id')
            name=reaction["name"],
            equation=equation,
            ec_numbers=ec_numbers,
            match_field=match_field,
            match_type=match_type,
        )
        results.append(result)

    # Build response
    response = SearchReactionsResponse(
        query=query,
        num_results=len(results),
        results=results,
        truncated=truncated,
    )

    # Add suggestions if no results
    if len(results) == 0:
        response.suggestions = [
            "Try a more general search term",
            "Check spelling of reaction name or enzyme",
            "Search by EC number (e.g., 2.7.1.1)",
            "Search by pathway name (e.g., Glycolysis)",
            "Search by database ID from other sources (KEGG, BiGG, MetaCyc)",
        ]
        response.next_steps = []
    else:
        # Add context-aware next_steps based on results
        next_steps = [
            "Use get_reaction_name with reaction 'id' to get detailed information and equation",
            "Examine EC numbers to understand enzyme classification",
            "Look at pathways to see metabolic context of reactions",
        ]

        if truncated:
            next_steps.insert(0, f"More results available: increase limit parameter (currently {limit}) to see all {total_matches} matches")

        response.next_steps = next_steps

    logger.info(
        f"Search complete: {len(results)} results returned "
        f"({total_matches} total matches, truncated={truncated})"
    )

    return response.model_dump()
