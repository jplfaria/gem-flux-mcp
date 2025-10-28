"""Data types and Pydantic models for Gem-Flux MCP Server.

This module defines all data structures used for:
- MCP tool request/response formats
- Database query results
- Model and media representations
- FBA and gapfilling results

All types follow the specifications in specs/002-data-formats.md and
individual tool specifications.
"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Build Media Tool Types (spec: 003-build-media-tool.md)
# =============================================================================


class BuildMediaRequest(BaseModel):
    """Request format for build_media tool.

    Creates growth media from ModelSEED compound IDs with configurable bounds.
    """

    compounds: List[str] = Field(
        ...,
        min_length=1,
        description="List of ModelSEED compound IDs (format: cpd00027)"
    )
    default_uptake: float = Field(
        default=100.0,
        gt=0.0,
        description="Default maximum uptake rate (mmol/gDW/h)"
    )
    custom_bounds: Optional[Dict[str, List[float]]] = Field(
        default=None,
        description="Custom [lower, upper] bounds for specific compounds"
    )

    @field_validator("compounds")
    @classmethod
    def validate_compound_ids(cls, v: List[str]) -> List[str]:
        """Ensure all compound IDs match cpd##### format."""
        import re
        pattern = re.compile(r'^cpd\d{5}$')
        for cpd_id in v:
            if not pattern.match(cpd_id):
                raise ValueError(
                    f"Invalid compound ID format: {cpd_id}. "
                    f"Expected format: cpd##### (e.g., cpd00027)"
                )
        return v

    @field_validator("custom_bounds")
    @classmethod
    def validate_custom_bounds(cls, v: Optional[Dict[str, List[float]]]) -> Optional[Dict[str, List[float]]]:
        """Ensure custom bounds have valid [lower, upper] format."""
        if v is None:
            return v

        for cpd_id, bounds in v.items():
            if len(bounds) != 2:
                raise ValueError(
                    f"Custom bounds for {cpd_id} must be [lower, upper] array"
                )
            lower, upper = bounds
            if lower >= upper:
                raise ValueError(
                    f"Invalid bounds for {cpd_id}: lower ({lower}) must be < upper ({upper})"
                )
        return v


class CompoundInfo(BaseModel):
    """Compound information with metadata from ModelSEED database."""

    id: str = Field(..., description="ModelSEED compound ID")
    name: str = Field(..., description="Human-readable compound name")
    formula: str = Field(..., description="Molecular formula")
    bounds: List[float] = Field(..., description="Applied [lower, upper] bounds")


class BuildMediaResponse(BaseModel):
    """Response format for successful build_media operation."""

    success: bool = Field(default=True)
    media_id: str = Field(..., description="Unique media identifier")
    compounds: List[CompoundInfo] = Field(..., description="Compounds with metadata")
    num_compounds: int = Field(..., description="Total compound count")
    media_type: Literal["minimal", "rich"] = Field(
        ...,
        description="Classification: minimal (<50 compounds) or rich (>=50)"
    )
    default_uptake_rate: float = Field(..., description="Default uptake value used")
    custom_bounds_applied: int = Field(..., description="Count of custom bounds")


# =============================================================================
# Build Model Tool Types (spec: 004-build-model-tool.md)
# =============================================================================


class BuildModelRequest(BaseModel):
    """Request format for build_model tool.

    Builds metabolic model from protein sequences using template matching.
    Either protein_sequences OR fasta_file_path must be provided (mutually exclusive).
    """

    protein_sequences: Optional[Dict[str, str]] = Field(
        default=None,
        description="Dict mapping protein IDs to amino acid sequences"
    )
    fasta_file_path: Optional[str] = Field(
        default=None,
        description="Path to FASTA file with protein sequences"
    )
    template: Literal["GramNegative", "GramPositive", "Core"] = Field(
        ...,
        description="ModelSEED template for model construction"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Human-readable model name (auto-generated if not provided)"
    )
    annotate_with_rast: bool = Field(
        default=True,
        description="Enable RAST annotation for improved template matching"
    )

    @field_validator("protein_sequences")
    @classmethod
    def validate_protein_sequences(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        """Validate amino acid sequences contain only valid characters."""
        if v is None:
            return v

        valid_amino_acids = set("ACDEFGHIKLMNPQRSTVWY")

        for protein_id, sequence in v.items():
            sequence_upper = sequence.upper()
            invalid_chars = set(sequence_upper) - valid_amino_acids

            if invalid_chars:
                raise ValueError(
                    f"Invalid amino acids in {protein_id}: {sorted(invalid_chars)}. "
                    f"Valid alphabet: ACDEFGHIKLMNPQRSTVWY"
                )

            if len(sequence) == 0:
                raise ValueError(f"Empty sequence for protein {protein_id}")

        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate that exactly one input method is provided."""
        has_sequences = self.protein_sequences is not None
        has_fasta = self.fasta_file_path is not None

        if has_sequences and has_fasta:
            raise ValueError(
                "Cannot provide both protein_sequences and fasta_file_path. "
                "Choose one input method."
            )

        if not has_sequences and not has_fasta:
            raise ValueError(
                "Must provide either protein_sequences or fasta_file_path"
            )


class ModelStatistics(BaseModel):
    """Detailed model statistics breakdown."""

    reactions_by_compartment: Dict[str, int] = Field(
        ...,
        description="Reaction counts per compartment"
    )
    metabolites_by_compartment: Dict[str, int] = Field(
        ...,
        description="Metabolite counts per compartment"
    )
    reversible_reactions: int = Field(..., description="Reversible reaction count")
    irreversible_reactions: int = Field(..., description="Irreversible reaction count")
    transport_reactions: int = Field(..., description="Transport reaction count")


class ModelProperties(BaseModel):
    """Model state and properties."""

    is_draft: bool = Field(..., description="True if model is ungapfilled draft")
    requires_gapfilling: bool = Field(
        ...,
        description="True if model needs gapfilling to grow"
    )
    estimated_growth_without_gapfilling: float = Field(
        default=0.0,
        description="Predicted growth rate before gapfilling"
    )


class BuildModelResponse(BaseModel):
    """Response format for successful build_model operation."""

    success: bool = Field(default=True)
    model_id: str = Field(..., description="Unique model identifier with .draft suffix")
    model_name: str = Field(..., description="Human-readable model name")
    num_reactions: int = Field(..., description="Total reaction count")
    num_metabolites: int = Field(..., description="Total metabolite count")
    num_genes: int = Field(..., description="Gene count (equals protein sequences)")
    num_exchange_reactions: int = Field(..., description="Exchange reaction count")
    template_used: str = Field(..., description="Template used for construction")
    has_biomass_reaction: bool = Field(..., description="Biomass reaction exists")
    biomass_reaction_id: str = Field(..., description="Biomass reaction ID")
    compartments: List[str] = Field(..., description="Compartment codes in model")
    has_atpm: bool = Field(..., description="ATP maintenance reaction added")
    atpm_reaction_id: str = Field(..., description="ATPM reaction ID")
    statistics: ModelStatistics = Field(..., description="Detailed model statistics")
    model_properties: ModelProperties = Field(..., description="Model state flags")


# =============================================================================
# Gapfill Model Tool Types (spec: 005-gapfill-model-tool.md)
# =============================================================================


class GapfillModelRequest(BaseModel):
    """Request format for gapfill_model tool.

    Adds missing reactions to enable growth in specified medium.
    """

    model_id: str = Field(..., description="Model to gapfill")
    media_id: str = Field(..., description="Target growth medium")
    target_growth_rate: float = Field(
        default=0.01,
        gt=0.0,
        description="Minimum growth rate to achieve (1/h)"
    )
    allow_all_non_grp_reactions: bool = Field(
        default=True,
        description="Allow non-gene-associated reactions"
    )
    gapfill_mode: Literal["full", "atp_only", "genomescale_only"] = Field(
        default="full",
        description="Gapfilling stages to run"
    )


class ReactionAdded(BaseModel):
    """Metadata for a reaction added during gapfilling."""

    id: str = Field(..., description="Reaction ID with compartment")
    name: str = Field(..., description="Human-readable reaction name")
    equation: str = Field(..., description="Stoichiometric equation")
    direction: Literal["forward", "reverse", "reversible"] = Field(
        ...,
        description="Direction reaction was added"
    )
    compartment: str = Field(..., description="Compartment code")
    source: Literal["template_gapfill", "atp_correction", "auto_generated"] = Field(
        ...,
        description="Where reaction came from"
    )


class ExchangeReactionAdded(BaseModel):
    """Metadata for auto-generated exchange reaction."""

    id: str = Field(..., description="Exchange reaction ID (EX_ prefix)")
    name: str = Field(..., description="Human-readable description")
    metabolite: str = Field(..., description="Compound ID being exchanged")
    metabolite_name: str = Field(..., description="Compound name")
    source: Literal["auto_generated"] = Field(default="auto_generated")


class ATPCorrectionStats(BaseModel):
    """Statistics from ATP correction stage."""

    performed: bool = Field(..., description="Whether ATP correction ran")
    media_tested: int = Field(..., description="Number of test media")
    media_passed: int = Field(..., description="Media where ATP production works")
    media_failed: int = Field(..., description="Media where ATP production failed")
    reactions_added: int = Field(..., description="Reactions added during ATP correction")


class GenomescaleGapfillStats(BaseModel):
    """Statistics from genome-scale gapfilling stage."""

    performed: bool = Field(..., description="Whether genome-scale gapfilling ran")
    reactions_added: int = Field(..., description="Total reactions added")
    reversed_reactions: int = Field(..., description="Existing reactions reversed")
    new_reactions: int = Field(..., description="New reactions added")


class GapfilledModelProperties(BaseModel):
    """Properties of gapfilled model."""

    num_reactions: int = Field(..., description="Total reactions after gapfilling")
    num_metabolites: int = Field(..., description="Total metabolites after gapfilling")
    is_draft: bool = Field(..., description="Should be False after successful gapfilling")
    requires_further_gapfilling: bool = Field(
        ...,
        description="False if achieved target growth"
    )


class GapfillModelResponse(BaseModel):
    """Response format for successful gapfill_model operation."""

    success: bool = Field(default=True)
    model_id: str = Field(..., description="New gapfilled model ID with .gf suffix")
    original_model_id: str = Field(..., description="Original model ID")
    media_id: str = Field(..., description="Media used for gapfilling")
    growth_rate_before: float = Field(..., description="Growth rate before gapfilling")
    growth_rate_after: float = Field(..., description="Growth rate after gapfilling")
    target_growth_rate: float = Field(..., description="Target growth rate")
    gapfilling_successful: bool = Field(
        ...,
        description="True if growth_rate_after >= target_growth_rate"
    )
    num_reactions_added: int = Field(..., description="Total reactions added")
    reactions_added: List[ReactionAdded] = Field(..., description="Added reactions with metadata")
    exchange_reactions_added: List[ExchangeReactionAdded] = Field(
        ...,
        description="Auto-generated exchange reactions"
    )
    atp_correction: ATPCorrectionStats = Field(..., description="ATP correction results")
    genomescale_gapfill: GenomescaleGapfillStats = Field(
        ...,
        description="Genome-scale gapfilling results"
    )
    model_properties: GapfilledModelProperties = Field(..., description="Final model state")


# =============================================================================
# Run FBA Tool Types (spec: 006-run-fba-tool.md)
# =============================================================================


class RunFBARequest(BaseModel):
    """Request format for run_fba tool.

    Executes flux balance analysis to predict growth and fluxes.
    """

    model_id: str = Field(..., description="Model to analyze")
    media_id: str = Field(..., description="Growth medium to apply")
    objective: str = Field(default="bio1", description="Objective reaction to optimize")
    maximize: bool = Field(default=True, description="True to maximize, False to minimize")
    flux_threshold: float = Field(
        default=1e-6,
        ge=0.0,
        description="Minimum flux to report (mmol/gDW/h)"
    )


class UptakeFlux(BaseModel):
    """Uptake flux with compound metadata."""

    compound_id: str = Field(..., description="ModelSEED compound ID")
    compound_name: str = Field(..., description="Human-readable compound name")
    formula: str = Field(..., description="Molecular formula")
    flux: float = Field(..., description="Negative number (uptake rate)")
    reaction_id: str = Field(..., description="Exchange reaction ID")


class SecretionFlux(BaseModel):
    """Secretion flux with compound metadata."""

    compound_id: str = Field(..., description="ModelSEED compound ID")
    compound_name: str = Field(..., description="Human-readable compound name")
    formula: str = Field(..., description="Molecular formula")
    flux: float = Field(..., description="Positive number (secretion rate)")
    reaction_id: str = Field(..., description="Exchange reaction ID")


class FBASummary(BaseModel):
    """High-level FBA statistics."""

    uptake_reactions: int = Field(..., description="Exchange reactions with uptake")
    secretion_reactions: int = Field(..., description="Exchange reactions with secretion")
    internal_reactions: int = Field(..., description="Non-exchange active reactions")
    reversible_active: int = Field(..., description="Active reversible reactions")
    irreversible_active: int = Field(..., description="Active irreversible reactions")


class TopFlux(BaseModel):
    """Top flux reaction with metadata."""

    reaction_id: str = Field(..., description="Reaction ID with compartment")
    reaction_name: str = Field(..., description="Human-readable reaction name")
    flux: float = Field(..., description="Flux value (signed)")
    direction: Literal["forward", "reverse"] = Field(
        ...,
        description="Direction based on flux sign"
    )


class RunFBAResponse(BaseModel):
    """Response format for successful run_fba operation."""

    success: bool = Field(default=True)
    model_id: str = Field(..., description="Model analyzed")
    media_id: str = Field(..., description="Media applied")
    objective_reaction: str = Field(..., description="Objective reaction optimized")
    objective_value: float = Field(..., description="Optimized objective value")
    status: Literal["optimal", "infeasible", "unbounded", "failed"] = Field(
        ...,
        description="Optimization status"
    )
    solver_status: str = Field(..., description="Detailed solver status")
    active_reactions: int = Field(..., description="Reactions with |flux| > threshold")
    total_reactions: int = Field(..., description="Total reactions in model")
    total_flux: float = Field(..., description="Sum of absolute flux values")
    fluxes: Dict[str, float] = Field(
        ...,
        description="Reaction IDs to flux values (filtered by threshold)"
    )
    uptake_fluxes: List[UptakeFlux] = Field(..., description="Uptake summary with names")
    secretion_fluxes: List[SecretionFlux] = Field(..., description="Secretion summary with names")
    summary: FBASummary = Field(..., description="High-level statistics")
    top_fluxes: List[TopFlux] = Field(..., description="Top 10 fluxes by magnitude")


# =============================================================================
# Database Lookup Types (specs: 008/009-compound/reaction-lookup-tools.md)
# =============================================================================


class CompoundLookupResult(BaseModel):
    """Result from get_compound_name tool."""

    success: bool = Field(default=True)
    id: str = Field(..., description="ModelSEED compound ID")
    name: str = Field(..., description="Primary compound name")
    abbreviation: str = Field(..., description="Short code")
    formula: str = Field(..., description="Molecular formula")
    mass: float = Field(..., description="Molecular mass (g/mol)")
    charge: int = Field(..., description="Net ionic charge")
    inchikey: Optional[str] = Field(None, description="InChI key structure identifier")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    external_ids: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Cross-references to other databases"
    )


class CompoundSearchResult(BaseModel):
    """Single result from search_compounds tool."""

    id: str = Field(..., description="ModelSEED compound ID")
    name: str = Field(..., description="Compound name")
    formula: str = Field(..., description="Molecular formula")
    match_type: Literal["name", "abbreviation", "alias", "formula", "id"] = Field(
        ...,
        description="Field that matched the query"
    )
    relevance_score: float = Field(..., description="Match quality (0-1)")


class CompoundSearchResponse(BaseModel):
    """Response from search_compounds tool."""

    success: bool = Field(default=True)
    query: str = Field(..., description="Search query used")
    num_results: int = Field(..., description="Number of results found")
    results: List[CompoundSearchResult] = Field(..., description="Matching compounds")


class ReactionLookupResult(BaseModel):
    """Result from get_reaction_name tool."""

    success: bool = Field(default=True)
    id: str = Field(..., description="ModelSEED reaction ID")
    name: str = Field(..., description="Primary reaction name")
    abbreviation: str = Field(..., description="Short code")
    equation: str = Field(..., description="Stoichiometric equation with names")
    equation_with_ids: str = Field(..., description="Equation with compound IDs")
    reversibility: Literal["irreversible_forward", "irreversible_reverse", "reversible"] = Field(
        ...,
        description="Reversibility status"
    )
    direction_symbol: Literal[">", "<", "="] = Field(..., description="Direction symbol")
    ec_numbers: List[str] = Field(default_factory=list, description="EC numbers")
    pathways: List[str] = Field(default_factory=list, description="Pathway associations")
    is_transport: bool = Field(..., description="True if transport reaction")
    external_ids: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Cross-references to other databases"
    )


class ReactionSearchResult(BaseModel):
    """Single result from search_reactions tool."""

    id: str = Field(..., description="ModelSEED reaction ID")
    name: str = Field(..., description="Reaction name")
    equation: str = Field(..., description="Stoichiometric equation")
    ec_numbers: List[str] = Field(default_factory=list, description="EC numbers")
    match_type: Literal["name", "abbreviation", "ec", "alias", "pathway", "id"] = Field(
        ...,
        description="Field that matched the query"
    )
    relevance_score: float = Field(..., description="Match quality (0-1)")


class ReactionSearchResponse(BaseModel):
    """Response from search_reactions tool."""

    success: bool = Field(default=True)
    query: str = Field(..., description="Search query used")
    num_results: int = Field(..., description="Number of results found")
    results: List[ReactionSearchResult] = Field(..., description="Matching reactions")


# =============================================================================
# Session Management Tool Types (spec: 018-session-management-tools.md)
# =============================================================================


class ListModelsRequest(BaseModel):
    """Request format for list_models tool."""

    filter_state: Literal["all", "draft", "gapfilled"] = Field(
        default="all",
        description="Filter models by processing state"
    )


class ModelInfo(BaseModel):
    """Model metadata for list_models response."""

    model_id: str = Field(..., description="Unique model identifier with state suffix")
    model_name: Optional[str] = Field(None, description="User-provided name or None")
    state: Literal["draft", "gapfilled"] = Field(..., description="Processing state")
    num_reactions: int = Field(..., description="Reaction count")
    num_metabolites: int = Field(..., description="Metabolite count")
    num_genes: int = Field(..., description="Gene count")
    template_used: str = Field(..., description="Template name used for building")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    derived_from: Optional[str] = Field(None, description="Parent model ID or None")


class ListModelsResponse(BaseModel):
    """Response format for list_models tool."""

    success: bool = Field(default=True)
    models: List[ModelInfo] = Field(..., description="List of model metadata")
    total_models: int = Field(..., description="Total models after filtering")
    models_by_state: Dict[str, int] = Field(..., description="Breakdown by state")


class DeleteModelRequest(BaseModel):
    """Request format for delete_model tool."""

    model_id: str = Field(..., description="Model ID to delete")


class DeleteModelResponse(BaseModel):
    """Response format for delete_model tool."""

    success: bool = Field(default=True)
    deleted_model_id: str = Field(..., description="Confirmation of deleted ID")
    message: str = Field(default="Model deleted successfully")


class MediaInfo(BaseModel):
    """Media metadata for list_media response."""

    media_id: str = Field(..., description="Unique media identifier")
    media_name: Optional[str] = Field(None, description="User/predefined name or None")
    num_compounds: int = Field(..., description="Number of compounds")
    media_type: Literal["minimal", "rich"] = Field(..., description="Classification")
    compounds_preview: List[Dict[str, str]] = Field(
        ...,
        description="First 3 compounds with ID and name"
    )
    created_at: str = Field(..., description="ISO 8601 timestamp")


class ListMediaResponse(BaseModel):
    """Response format for list_media tool."""

    success: bool = Field(default=True)
    media: List[MediaInfo] = Field(..., description="List of media metadata")
    total_media: int = Field(..., description="Total media count")
    predefined_media: int = Field(..., description="Count of predefined media")
    user_created_media: int = Field(..., description="Count of user-created media")


# =============================================================================
# Error Response Types (spec: 013-error-handling.md)
# =============================================================================


class ErrorDetails(BaseModel):
    """Additional error context and diagnostics."""

    model_config = {"extra": "allow"}  # Allow additional fields for specific error types


class ErrorResponse(BaseModel):
    """Standard error response format for all tools.

    Follows JSON-RPC 2.0 error response pattern.
    """

    success: bool = Field(default=False)
    error_type: str = Field(..., description="Error type classification")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[ErrorDetails] = Field(None, description="Additional error context")
    suggestion: Optional[str] = Field(None, description="Recovery suggestion")
