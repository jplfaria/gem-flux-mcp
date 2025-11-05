"""Media builder tool for ModelSEED media creation.

This module implements the build_media MCP tool as specified in
003-build-media-tool.md.

Tool:
    - build_media: Create growth media from ModelSEED compound IDs

This tool validates compound IDs, applies bounds, creates MSMedia objects,
and stores them in session storage with enriched metadata.
"""

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator
from modelseedpy import MSMedia

from gem_flux_mcp.database import validate_compound_id
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.errors import ValidationError, invalid_compound_ids_error
from gem_flux_mcp.storage.media import generate_media_id, store_media

logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================


def _get_next_steps() -> list[str]:
    """Get next_steps from centralized prompt."""
    from gem_flux_mcp.prompts import render_prompt
    next_steps_text = render_prompt("next_steps/build_media")
    return [
        line.strip()[2:].strip()
        for line in next_steps_text.split("\n")
        if line.strip().startswith("-")
    ]


# =============================================================================
# Request/Response Models
# =============================================================================


class BuildMediaRequest(BaseModel):
    """Request format for build_media tool.

    Creates a growth medium from ModelSEED compound IDs with configurable
    uptake/secretion bounds.
    """

    compounds: list[str] = Field(
        ...,
        min_length=1,
        description="List of ModelSEED compound IDs (e.g., ['cpd00027', 'cpd00007'])",
    )
    default_uptake: float = Field(
        default=100.0,
        gt=0.0,
        le=1000.0,
        description="Default maximum uptake rate (mmol/gDW/h) for all compounds",
    )
    custom_bounds: dict[str, tuple[float, float]] = Field(
        default_factory=dict,
        description="Custom bounds for specific compounds: {'cpd00027': (-5, 100)}",
    )

    @field_validator("compounds", mode="before")
    @classmethod
    def validate_compounds_list(cls, v: list[str]) -> list[str]:
        """Validate compounds list is non-empty and contains valid formats."""
        if not v or not isinstance(v, list):
            raise ValueError("Compounds list must be a non-empty list")

        if len(v) == 0:
            raise ValueError("Compounds list cannot be empty")

        # Trim whitespace and convert to lowercase
        cleaned = []
        for cpd_id in v:
            if not isinstance(cpd_id, str):
                raise ValueError(f"Compound ID must be string, got {type(cpd_id)}")
            cleaned_id = cpd_id.strip().lower()
            cleaned.append(cleaned_id)

        # Check for duplicates
        seen = set()
        duplicates = set()
        for cpd_id in cleaned:
            if cpd_id in seen:
                duplicates.add(cpd_id)
            seen.add(cpd_id)

        if duplicates:
            raise ValueError(
                f"Duplicate compound IDs found: {', '.join(sorted(duplicates))}"
            )

        # Validate format for each compound
        invalid_formats = []
        for cpd_id in cleaned:
            is_valid, error_msg = validate_compound_id(cpd_id)
            if not is_valid:
                invalid_formats.append(cpd_id)

        if invalid_formats:
            raise ValueError(
                f"Invalid compound ID format: {', '.join(invalid_formats)}. "
                f"Expected 'cpd' followed by exactly 5 digits (e.g., cpd00027)"
            )

        return cleaned

    @field_validator("custom_bounds", mode="before")
    @classmethod
    def validate_custom_bounds(cls, v: dict) -> dict:
        """Validate custom bounds format and values."""
        if not isinstance(v, dict):
            return {}

        validated = {}
        for cpd_id, bounds in v.items():
            # Validate compound ID format
            cleaned_id = cpd_id.strip().lower()
            is_valid, _ = validate_compound_id(cleaned_id)
            if not is_valid:
                raise ValueError(
                    f"Invalid compound ID in custom_bounds: {cpd_id}. "
                    f"Expected 'cpd' followed by exactly 5 digits"
                )

            # Validate bounds format
            if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
                raise ValueError(
                    f"Bounds for {cpd_id} must be a tuple/list of 2 numbers: [lower, upper]"
                )

            lower, upper = bounds
            if not isinstance(lower, (int, float)) or not isinstance(
                upper, (int, float)
            ):
                raise ValueError(
                    f"Bounds for {cpd_id} must be numeric values, got: {bounds}"
                )

            if lower > upper:
                raise ValueError(
                    f"Invalid bounds for {cpd_id}: lower ({lower}) must be less than or equal to upper ({upper})"
                )

            validated[cleaned_id] = (float(lower), float(upper))

        return validated

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation: custom_bounds compounds must be in compounds list."""
        # Check that all custom_bounds keys are in compounds list
        compounds_set = set(self.compounds)
        for cpd_id in self.custom_bounds.keys():
            if cpd_id not in compounds_set:
                raise ValueError(
                    f"Custom bounds specified for compound not in media: {cpd_id}. "
                    f"Add '{cpd_id}' to compounds list first."
                )


class CompoundMetadata(BaseModel):
    """Metadata for a single compound in media."""

    id: str = Field(..., description="ModelSEED compound ID")
    name: str = Field(..., description="Human-readable compound name")
    formula: str = Field(..., description="Molecular formula")
    bounds: tuple[float, float] = Field(..., description="Uptake/secretion bounds")


class BuildMediaResponse(BaseModel):
    """Response format for successful build_media operation."""

    success: bool = Field(default=True)
    media_id: str = Field(..., description="Unique media identifier")
    compounds: list[CompoundMetadata] = Field(
        ..., description="List of compounds with metadata"
    )
    num_compounds: int = Field(..., description="Total number of compounds")
    media_type: str = Field(
        ..., description="Media classification: 'minimal' or 'rich'"
    )
    default_uptake_rate: float = Field(
        ..., description="Default uptake rate used (mmol/gDW/h)"
    )
    custom_bounds_applied: int = Field(
        ..., description="Number of compounds with custom bounds"
    )
    next_steps: list[str] = Field(
        ..., description="Suggested next steps for using this media"
    )


# =============================================================================
# Tool Implementation
# =============================================================================


def build_media(request: BuildMediaRequest, db_index: DatabaseIndex) -> dict:
    """Create growth media from ModelSEED compound IDs.

    This function implements the build_media MCP tool as specified in
    003-build-media-tool.md.

    Process:
        1. Validate all compound IDs exist in database
        2. Create compound bounds dict (default + custom)
        3. Create MSMedia object (placeholder for MVP - will integrate ModelSEEDpy)
        4. Generate unique media_id
        5. Store in session storage
        6. Enrich with database metadata
        7. Return response

    Args:
        request: BuildMediaRequest with compounds, default_uptake, custom_bounds
        db_index: DatabaseIndex instance with loaded compounds database

    Returns:
        Dictionary with media metadata (BuildMediaResponse format)

    Raises:
        ValidationError: If any compound IDs are invalid or not in database

    Performance:
        - Expected time: < 500ms for typical media (20-100 compounds)

    Example:
        >>> request = BuildMediaRequest(
        ...     compounds=["cpd00027", "cpd00007"],
        ...     default_uptake=100.0,
        ...     custom_bounds={"cpd00027": (-5, 100)}
        ... )
        >>> response = build_media(request, db_index)
        >>> print(response["media_id"])
        'media_20251027_143052_x1y2z3'

    Spec Reference:
        - 003-build-media-tool.md: Tool specification
        - 002-data-formats.md: Media data format
        - 010-model-storage.md: Media storage architecture
    """
    logger.info(
        f"Building media: {len(request.compounds)} compounds, "
        f"default_uptake={request.default_uptake}, "
        f"custom_bounds={len(request.custom_bounds)}"
    )

    # Step 1: Validate compound IDs exist in database
    invalid_ids = []
    valid_ids = []

    for cpd_id in request.compounds:
        if db_index.compound_exists(cpd_id):
            valid_ids.append(cpd_id)
        else:
            invalid_ids.append(cpd_id)

    if invalid_ids:
        logger.warning(
            f"Invalid compound IDs found: {len(invalid_ids)} of {len(request.compounds)}"
        )
        raise invalid_compound_ids_error(
            invalid_ids=invalid_ids,
            valid_ids=valid_ids,
            total_provided=len(request.compounds),
        )

    # Step 2: Build bounds dictionary
    # Format: {cpd_id: (lower, upper)} for each compound
    bounds_dict: dict[str, tuple[float, float]] = {}

    for cpd_id in request.compounds:
        if cpd_id in request.custom_bounds:
            # Use custom bounds
            bounds_dict[cpd_id] = request.custom_bounds[cpd_id]
        else:
            # Use default bounds: (-default_uptake, 100.0)
            bounds_dict[cpd_id] = (-request.default_uptake, 100.0)

    logger.debug(f"Built bounds for {len(bounds_dict)} compounds")

    # Step 3: Create MSMedia object using ModelSEEDpy
    # MSMedia.from_dict() expects compound IDs as keys and (lower, upper) tuples as values
    media = MSMedia.from_dict(bounds_dict)
    logger.info(f"Created MSMedia object with {len(bounds_dict)} compounds")

    # Step 4: Generate unique media_id and set it on the MSMedia object
    media_id = generate_media_id()
    media.id = media_id
    logger.info(f"Assigned media_id: {media_id}")

    # Step 5: Store MSMedia object in session storage
    store_media(media_id, media)
    logger.info(f"Stored MSMedia object in session: {media_id}")

    # Step 6: Enrich with database metadata
    compounds_metadata = []
    for cpd_id in request.compounds:
        compound_record = db_index.get_compound_by_id(cpd_id)
        if compound_record is None:
            # Should not happen - we validated above
            logger.error(f"Compound disappeared after validation: {cpd_id}")
            continue

        bounds = bounds_dict[cpd_id]
        metadata = CompoundMetadata(
            id=cpd_id,
            name=compound_record["name"],
            formula=compound_record["formula"],
            bounds=bounds,
        )
        compounds_metadata.append(metadata)

    # Step 7: Classify media type (heuristic: <50 compounds = minimal)
    num_compounds = len(request.compounds)
    media_type = "minimal" if num_compounds < 50 else "rich"

    # Step 8: Build response
    response = BuildMediaResponse(
        media_id=media_id,
        compounds=compounds_metadata,
        num_compounds=num_compounds,
        media_type=media_type,
        default_uptake_rate=request.default_uptake,
        custom_bounds_applied=len(request.custom_bounds),
        next_steps=_get_next_steps(),
    )

    logger.info(
        f"Successfully built media: {media_id} ({media_type}, {num_compounds} compounds)"
    )

    return response.model_dump()
