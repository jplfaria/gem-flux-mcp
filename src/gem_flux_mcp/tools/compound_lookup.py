"""Compound lookup tools for ModelSEED database.

This module implements MCP tools for looking up compound information from
the ModelSEED database (spec 008-compound-lookup-tools.md):

Tools:
    - get_compound_name: Retrieve metadata for a single compound ID
    - search_compounds: Search compounds by name, formula, or alias

These tools enable AI assistants to translate between ModelSEED compound IDs
and human-readable names, formulas, and metadata.
"""

import logging
from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field, field_validator

from gem_flux_mcp.database import parse_aliases, validate_compound_id
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.errors import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================


class GetCompoundNameRequest(BaseModel):
    """Request format for get_compound_name tool.

    Retrieves human-readable name and metadata for a ModelSEED compound ID.
    """

    compound_id: str = Field(
        ...,
        description="ModelSEED compound ID (format: cpd00027)",
    )

    @field_validator("compound_id", mode="before")
    @classmethod
    def validate_compound_id_format(cls, v: str) -> str:
        """Validate compound ID format matches cpd##### pattern."""
        # Handle empty input
        if not v or not isinstance(v, str):
            raise ValueError("Compound ID must be a non-empty string")

        # Trim whitespace and convert to lowercase for case-insensitive matching
        v = v.strip().lower()

        # Validate format
        is_valid, error_msg = validate_compound_id(v)
        if not is_valid:
            raise ValueError(error_msg)

        return v


class GetCompoundNameResponse(BaseModel):
    """Response format for successful get_compound_name operation.

    Contains complete compound metadata from ModelSEED database.
    """

    success: bool = Field(default=True)
    id: str = Field(..., description="ModelSEED compound ID")
    name: str = Field(..., description="Human-readable compound name")
    abbreviation: str = Field(..., description="Short compound code")
    formula: str = Field(..., description="Molecular formula")
    mass: float = Field(..., description="Molecular mass in g/mol")
    charge: int = Field(..., description="Ionic charge")
    inchikey: str = Field(..., description="InChI key for structure identification")
    smiles: str = Field(..., description="SMILES notation for chemical structure")
    aliases: dict[str, list[str]] = Field(
        ..., description="Cross-references to external databases"
    )


class SearchCompoundsRequest(BaseModel):
    """Request format for search_compounds tool.

    Search for compounds by name, formula, alias, or other text.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Text to search for in compound names, formulas, abbreviations, and aliases",
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


class CompoundSearchResult(BaseModel):
    """Single compound search result with match metadata."""

    id: str = Field(..., description="ModelSEED compound ID")
    name: str = Field(..., description="Human-readable compound name")
    abbreviation: str = Field(..., description="Short compound code")
    formula: str = Field(..., description="Molecular formula")
    mass: float = Field(..., description="Molecular mass in g/mol")
    charge: int = Field(..., description="Ionic charge")
    match_field: str = Field(
        ...,
        description="Field where match was found (name, abbreviation, formula, aliases, id)",
    )
    match_type: str = Field(
        ..., description="Type of match (exact or partial)"
    )


class SearchCompoundsResponse(BaseModel):
    """Response format for successful search_compounds operation."""

    success: bool = Field(default=True)
    query: str = Field(..., description="The search query as processed")
    num_results: int = Field(..., description="Number of results returned")
    results: list[CompoundSearchResult] = Field(
        ..., description="List of matching compounds"
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
# Tool Implementation
# =============================================================================


def get_compound_name(
    request: GetCompoundNameRequest, db_index: DatabaseIndex
) -> dict:
    """Get human-readable name and metadata for a ModelSEED compound ID.

    This function implements the get_compound_name MCP tool as specified in
    008-compound-lookup-tools.md.

    Args:
        request: GetCompoundNameRequest with compound_id
        db_index: DatabaseIndex instance with loaded compounds database

    Returns:
        Dictionary with compound metadata (GetCompoundNameResponse format)

    Raises:
        NotFoundError: If compound ID not found in database
        ValidationError: If compound ID format is invalid

    Performance:
        - Expected time: < 1 millisecond per lookup
        - Uses O(1) indexed access

    Example:
        >>> request = GetCompoundNameRequest(compound_id="cpd00027")
        >>> response = get_compound_name(request, db_index)
        >>> print(response["name"])
        'D-Glucose'

    Spec Reference:
        - 008-compound-lookup-tools.md: Tool specification
        - 007-database-integration.md: Database structure
        - 002-data-formats.md: ModelSEED identifier conventions
    """
    compound_id = request.compound_id

    logger.info(f"Looking up compound: {compound_id}")

    # Step 1: Query database (O(1) lookup)
    compound_record = db_index.get_compound_by_id(compound_id)

    if compound_record is None:
        # Compound not found - return error response
        logger.warning(f"Compound not found: {compound_id}")
        raise NotFoundError(
            message=f"Compound ID {compound_id} not found in ModelSEED database",
            error_code="COMPOUND_NOT_FOUND",
            details={
                "compound_id": compound_id,
                "searched_in": f"compounds.tsv ({db_index.get_compound_count()} compounds)",
            },
            suggestions=[
                "Check ID format: should be 'cpd' followed by exactly 5 digits",
                "Use search_compounds tool to find compounds by name",
                "Verify ID from ModelSEED database documentation",
            ],
        )

    # Step 2: Parse aliases from raw string
    aliases_raw = compound_record.get("aliases", "")
    aliases_dict = parse_aliases(aliases_raw)

    # Step 3: Build response
    response = GetCompoundNameResponse(
        id=compound_id,
        name=compound_record["name"],
        abbreviation=compound_record["abbreviation"],
        formula=compound_record["formula"],
        mass=float(compound_record["mass"]) if compound_record["mass"] else 0.0,
        charge=int(compound_record["charge"]) if compound_record["charge"] else 0,
        inchikey=compound_record.get("inchikey", ""),
        smiles=compound_record.get("smiles", ""),
        aliases=aliases_dict,
    )

    logger.info(f"Successfully retrieved compound: {compound_id} ({response.name})")

    return response.model_dump()


def search_compounds(request: SearchCompoundsRequest, db_index: DatabaseIndex) -> dict:
    """Search for compounds by name, formula, alias, or other text.

    This function implements the search_compounds MCP tool as specified in
    008-compound-lookup-tools.md.

    Args:
        request: SearchCompoundsRequest with query and optional limit
        db_index: DatabaseIndex instance with loaded compounds database

    Returns:
        Dictionary with search results (SearchCompoundsResponse format)

    Performance:
        - Expected time: 10-100 milliseconds per search
        - Uses O(n) linear search (acceptable for MVP)

    Search Strategy (spec 008):
        1. Exact ID match
        2. Exact name match (case-insensitive)
        3. Exact abbreviation match (case-insensitive)
        4. Partial name match (case-insensitive)
        5. Formula match (exact)
        6. Alias match (case-insensitive)

    Example:
        >>> request = SearchCompoundsRequest(query="glucose", limit=5)
        >>> response = search_compounds(request, db_index)
        >>> print(f"Found {response['num_results']} compounds")
        Found 5 compounds

    Spec Reference:
        - 008-compound-lookup-tools.md: Tool specification
        - 007-database-integration.md: Search operations
    """
    query = request.query.strip().lower()
    limit = request.limit

    logger.info(f"Searching compounds: query='{query}', limit={limit}")

    # Track all matches with their priority and metadata
    matches: list[tuple[int, pd.Series, str, str]] = []
    # Format: (priority, compound_record, match_field, match_type)
    # Priority: lower number = higher priority (1 = exact ID, 2 = exact name, etc.)

    compounds_df = db_index.compounds_df

    # Step 1: Exact ID match (priority 1)
    if db_index.compound_exists(query):
        compound = db_index.get_compound_by_id(query)
        if compound is not None:
            matches.append((1, compound, "id", "exact"))
            logger.debug(f"Found exact ID match: {query}")

    # Step 2: Exact name match (priority 2)
    exact_name_matches = compounds_df[compounds_df["name_lower"] == query]
    for _, compound in exact_name_matches.iterrows():
        matches.append((2, compound, "name", "exact"))
    if len(exact_name_matches) > 0:
        logger.debug(f"Found {len(exact_name_matches)} exact name matches")

    # Step 3: Exact abbreviation match (priority 3)
    exact_abbr_matches = compounds_df[compounds_df["abbreviation_lower"] == query]
    for _, compound in exact_abbr_matches.iterrows():
        matches.append((3, compound, "abbreviation", "exact"))
    if len(exact_abbr_matches) > 0:
        logger.debug(f"Found {len(exact_abbr_matches)} exact abbreviation matches")

    # Step 4: Partial name match (priority 4)
    partial_name_matches = compounds_df[
        compounds_df["name_lower"].str.contains(query, na=False, regex=False)
        & (compounds_df["name_lower"] != query)  # Exclude exact matches already found
    ]
    for _, compound in partial_name_matches.iterrows():
        matches.append((4, compound, "name", "partial"))
    if len(partial_name_matches) > 0:
        logger.debug(f"Found {len(partial_name_matches)} partial name matches")

    # Step 5: Formula match (exact, priority 5)
    formula_matches = compounds_df[compounds_df["formula"].str.lower() == query]
    for _, compound in formula_matches.iterrows():
        matches.append((5, compound, "formula", "exact"))
    if len(formula_matches) > 0:
        logger.debug(f"Found {len(formula_matches)} formula matches")

    # Step 6: Alias match (priority 6)
    # Check if query appears in aliases column (case-insensitive)
    alias_matches = compounds_df[
        compounds_df["aliases"].str.lower().str.contains(query, na=False, regex=False)
    ]
    for _, compound in alias_matches.iterrows():
        matches.append((6, compound, "aliases", "partial"))
    if len(alias_matches) > 0:
        logger.debug(f"Found {len(alias_matches)} alias matches")

    # Remove duplicates (keep first occurrence with highest priority)
    seen_ids = set()
    unique_matches = []
    for priority, compound, match_field, match_type in sorted(matches, key=lambda x: x[0]):
        compound_id = compound.name  # pandas Series.name is the index value
        if compound_id not in seen_ids:
            seen_ids.add(compound_id)
            unique_matches.append((priority, compound, match_field, match_type))

    # Sort by priority, then alphabetically by name
    unique_matches.sort(key=lambda x: (x[0], x[1]["name"].lower()))

    # Check if truncated
    total_matches = len(unique_matches)
    truncated = total_matches > limit

    # Limit results
    limited_matches = unique_matches[:limit]

    # Build results list
    results = []
    for priority, compound, match_field, match_type in limited_matches:
        result = CompoundSearchResult(
            id=compound.name,  # Series.name is the index value ('id')
            name=compound["name"],
            abbreviation=compound["abbreviation"],
            formula=compound["formula"],
            mass=float(compound["mass"]) if compound["mass"] else 0.0,
            charge=int(compound["charge"]) if compound["charge"] else 0,
            match_field=match_field,
            match_type=match_type,
        )
        results.append(result)

    # Build response
    response = SearchCompoundsResponse(
        query=query,
        num_results=len(results),
        results=results,
        truncated=truncated,
    )

    # Add suggestions if no results
    if len(results) == 0:
        response.suggestions = [
            "Try a more general search term",
            "Check spelling of compound name",
            "Search by formula (e.g., C6H12O6)",
            "Search by database ID from other sources (KEGG, BiGG)",
        ]
        response.next_steps = []
    else:
        # Add context-aware next_steps based on results
        from gem_flux_mcp.prompts import render_prompt
        next_steps_text = render_prompt(
            "next_steps/search_compounds",
            truncated=truncated,
            limit=limit,
            total_matches=total_matches,
        )
        response.next_steps = [
            line.strip()[2:].strip()
            for line in next_steps_text.split("\n")
            if line.strip().startswith("-")
        ]

    logger.info(
        f"Search complete: {len(results)} results returned "
        f"({total_matches} total matches, truncated={truncated})"
    )

    return response.model_dump()
