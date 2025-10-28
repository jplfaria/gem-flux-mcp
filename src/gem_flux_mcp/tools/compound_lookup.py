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
