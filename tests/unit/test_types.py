"""Unit tests for gem_flux_mcp.types module.

Tests all Pydantic models for:
- Valid input acceptance
- Invalid input rejection
- Field validation
- Default value handling
- Custom validators
"""

import pytest
from pydantic import ValidationError

from gem_flux_mcp.types import (
    # Build Media
    BuildMediaRequest,
    BuildMediaResponse,
    CompoundInfo,
    # Build Model
    BuildModelRequest,
    BuildModelResponse,
    ModelStatistics,
    ModelProperties,
    # Gapfill Model
    GapfillModelRequest,
    GapfillModelResponse,
    ReactionAdded,
    ExchangeReactionAdded,
    ATPCorrectionStats,
    GenomescaleGapfillStats,
    GapfilledModelProperties,
    # Run FBA
    RunFBARequest,
    RunFBAResponse,
    UptakeFlux,
    SecretionFlux,
    FBASummary,
    TopFlux,
    # Database Lookups
    CompoundLookupResult,
    CompoundSearchResult,
    CompoundSearchResponse,
    ReactionLookupResult,
    ReactionSearchResult,
    ReactionSearchResponse,
    # Errors
    ErrorResponse,
    ErrorDetails,
)


# =============================================================================
# Build Media Request Tests
# =============================================================================


class TestBuildMediaRequest:
    """Tests for BuildMediaRequest validation."""

    def test_valid_minimal_request(self):
        """Test minimal valid request with default values."""
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007"]
        )
        assert request.compounds == ["cpd00027", "cpd00007"]
        assert request.default_uptake == 100.0
        assert request.custom_bounds is None

    def test_valid_with_custom_bounds(self):
        """Test valid request with custom bounds."""
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007"],
            default_uptake=50.0,
            custom_bounds={
                "cpd00027": [-5.0, 100.0],
                "cpd00007": [-10.0, 100.0]
            }
        )
        assert request.default_uptake == 50.0
        assert "cpd00027" in request.custom_bounds
        assert request.custom_bounds["cpd00027"] == [-5.0, 100.0]

    def test_invalid_compound_id_format(self):
        """Test rejection of invalid compound ID formats."""
        with pytest.raises(ValidationError) as exc_info:
            BuildMediaRequest(compounds=["glucose", "cpd00007"])

        errors = exc_info.value.errors()
        assert any("Invalid compound ID format" in str(e["ctx"]["error"]) for e in errors)

    def test_invalid_compound_id_too_short(self):
        """Test rejection of compound ID with wrong length."""
        with pytest.raises(ValidationError):
            BuildMediaRequest(compounds=["cpd001"])

    def test_empty_compounds_list(self):
        """Test rejection of empty compounds list."""
        with pytest.raises(ValidationError) as exc_info:
            BuildMediaRequest(compounds=[])

        errors = exc_info.value.errors()
        assert any(e["type"] == "too_short" for e in errors)

    def test_negative_default_uptake(self):
        """Test rejection of negative default_uptake."""
        with pytest.raises(ValidationError):
            BuildMediaRequest(
                compounds=["cpd00027"],
                default_uptake=-10.0
            )

    def test_zero_default_uptake(self):
        """Test rejection of zero default_uptake."""
        with pytest.raises(ValidationError):
            BuildMediaRequest(
                compounds=["cpd00027"],
                default_uptake=0.0
            )

    def test_invalid_custom_bounds_format(self):
        """Test rejection of invalid bounds format (not 2-element list)."""
        with pytest.raises(ValidationError) as exc_info:
            BuildMediaRequest(
                compounds=["cpd00027"],
                custom_bounds={"cpd00027": [-5.0]}  # Missing upper bound
            )

        errors = exc_info.value.errors()
        assert any("must be [lower, upper] array" in str(e["ctx"]["error"]) for e in errors)

    def test_invalid_custom_bounds_order(self):
        """Test rejection of bounds with lower >= upper."""
        with pytest.raises(ValidationError) as exc_info:
            BuildMediaRequest(
                compounds=["cpd00027"],
                custom_bounds={"cpd00027": [100.0, -5.0]}  # Reversed
            )

        errors = exc_info.value.errors()
        assert any("lower" in str(e["ctx"]["error"]) and "upper" in str(e["ctx"]["error"]) for e in errors)


class TestBuildMediaResponse:
    """Tests for BuildMediaResponse structure."""

    def test_valid_response(self):
        """Test creation of valid response."""
        response = BuildMediaResponse(
            media_id="media_001",
            compounds=[
                CompoundInfo(
                    id="cpd00027",
                    name="D-Glucose",
                    formula="C6H12O6",
                    bounds=[-5.0, 100.0]
                )
            ],
            num_compounds=1,
            media_type="minimal",
            default_uptake_rate=100.0,
            custom_bounds_applied=1
        )
        assert response.success is True
        assert response.media_id == "media_001"
        assert len(response.compounds) == 1
        assert response.media_type == "minimal"

    def test_rich_media_type(self):
        """Test rich media type classification."""
        response = BuildMediaResponse(
            media_id="media_002",
            compounds=[CompoundInfo(id=f"cpd{i:05d}", name=f"Compound {i}", formula="C1H1O1", bounds=[-100.0, 100.0]) for i in range(60)],
            num_compounds=60,
            media_type="rich",
            default_uptake_rate=100.0,
            custom_bounds_applied=0
        )
        assert response.media_type == "rich"


# =============================================================================
# Build Model Request Tests
# =============================================================================


class TestBuildModelRequest:
    """Tests for BuildModelRequest validation."""

    def test_valid_with_protein_sequences(self):
        """Test valid request with protein_sequences dict."""
        request = BuildModelRequest(
            protein_sequences={
                "prot_001": "MKLVINLV",
                "prot_002": "MKQHKAMI"
            },
            template="GramNegative"
        )
        assert len(request.protein_sequences) == 2
        assert request.template == "GramNegative"
        assert request.annotate_with_rast is True

    def test_valid_with_fasta_file(self):
        """Test valid request with fasta_file_path."""
        request = BuildModelRequest(
            fasta_file_path="/path/to/proteins.faa",
            template="GramPositive",
            annotate_with_rast=False
        )
        assert request.fasta_file_path == "/path/to/proteins.faa"
        assert request.protein_sequences is None
        assert request.annotate_with_rast is False

    def test_invalid_amino_acids(self):
        """Test rejection of invalid amino acid characters."""
        with pytest.raises(ValidationError) as exc_info:
            BuildModelRequest(
                protein_sequences={"prot_001": "MKLXVINLV"},  # X is invalid
                template="GramNegative"
            )

        errors = exc_info.value.errors()
        assert any("Invalid amino acids" in str(e["ctx"]["error"]) for e in errors)

    def test_empty_sequence(self):
        """Test rejection of empty protein sequence."""
        with pytest.raises(ValidationError) as exc_info:
            BuildModelRequest(
                protein_sequences={"prot_001": ""},
                template="GramNegative"
            )

        errors = exc_info.value.errors()
        assert any("Empty sequence" in str(e["ctx"]["error"]) for e in errors)

    def test_both_inputs_provided(self):
        """Test rejection when both input methods provided."""
        with pytest.raises(ValidationError) as exc_info:
            BuildModelRequest(
                protein_sequences={"prot_001": "MKLVINLV"},
                fasta_file_path="/path/to/file.faa",
                template="GramNegative"
            )

        errors = exc_info.value.errors()
        assert any("Cannot provide both" in str(e["ctx"]["error"]) for e in errors)

    def test_neither_input_provided(self):
        """Test rejection when no input method provided."""
        with pytest.raises(ValidationError) as exc_info:
            BuildModelRequest(template="GramNegative")

        errors = exc_info.value.errors()
        assert any("Must provide either" in str(e["ctx"]["error"]) for e in errors)

    def test_invalid_template(self):
        """Test rejection of invalid template name."""
        with pytest.raises(ValidationError):
            BuildModelRequest(
                protein_sequences={"prot_001": "MKLVINLV"},
                template="InvalidTemplate"
            )

    def test_case_insensitive_amino_acids(self):
        """Test that amino acids are case-insensitive (converted to upper)."""
        request = BuildModelRequest(
            protein_sequences={"prot_001": "mklvinlv"},  # lowercase
            template="Core"
        )
        # Should not raise error - validator converts to upper


class TestBuildModelResponse:
    """Tests for BuildModelResponse structure."""

    def test_valid_response(self):
        """Test creation of valid response."""
        response = BuildModelResponse(
            model_id="model_001.draft",
            model_name="E_coli_K12",
            num_reactions=856,
            num_metabolites=742,
            num_genes=150,
            num_exchange_reactions=95,
            template_used="GramNegative",
            has_biomass_reaction=True,
            biomass_reaction_id="bio1",
            compartments=["c0", "e0", "p0"],
            has_atpm=True,
            atpm_reaction_id="ATPM_c0",
            statistics=ModelStatistics(
                reactions_by_compartment={"c0": 715, "e0": 95, "p0": 46},
                metabolites_by_compartment={"c0": 580, "e0": 95, "p0": 67},
                reversible_reactions=412,
                irreversible_reactions=444,
                transport_reactions=78
            ),
            model_properties=ModelProperties(
                is_draft=True,
                requires_gapfilling=True,
                estimated_growth_without_gapfilling=0.0
            )
        )
        assert response.success is True
        assert response.model_id.endswith(".draft")
        assert len(response.compartments) == 3


# =============================================================================
# Gapfill Model Request Tests
# =============================================================================


class TestGapfillModelRequest:
    """Tests for GapfillModelRequest validation."""

    def test_valid_minimal_request(self):
        """Test minimal valid request with defaults."""
        request = GapfillModelRequest(
            model_id="model_001.draft",
            media_id="media_001"
        )
        assert request.target_growth_rate == 0.01
        assert request.allow_all_non_grp_reactions is True
        assert request.gapfill_mode == "full"

    def test_valid_with_custom_parameters(self):
        """Test valid request with custom parameters."""
        request = GapfillModelRequest(
            model_id="model_001.draft",
            media_id="media_001",
            target_growth_rate=0.1,
            allow_all_non_grp_reactions=False,
            gapfill_mode="atp_only"
        )
        assert request.target_growth_rate == 0.1
        assert request.gapfill_mode == "atp_only"

    def test_negative_target_growth_rate(self):
        """Test rejection of negative target growth rate."""
        with pytest.raises(ValidationError):
            GapfillModelRequest(
                model_id="model_001.draft",
                media_id="media_001",
                target_growth_rate=-0.01
            )

    def test_zero_target_growth_rate(self):
        """Test rejection of zero target growth rate."""
        with pytest.raises(ValidationError):
            GapfillModelRequest(
                model_id="model_001.draft",
                media_id="media_001",
                target_growth_rate=0.0
            )

    def test_invalid_gapfill_mode(self):
        """Test rejection of invalid gapfill_mode."""
        with pytest.raises(ValidationError):
            GapfillModelRequest(
                model_id="model_001.draft",
                media_id="media_001",
                gapfill_mode="invalid_mode"
            )


class TestGapfillModelResponse:
    """Tests for GapfillModelResponse structure."""

    def test_valid_successful_response(self):
        """Test creation of successful gapfill response."""
        response = GapfillModelResponse(
            model_id="model_001.draft.gf",
            original_model_id="model_001.draft",
            media_id="media_001",
            growth_rate_before=0.0,
            growth_rate_after=0.874,
            target_growth_rate=0.01,
            gapfilling_successful=True,
            num_reactions_added=4,
            reactions_added=[
                ReactionAdded(
                    id="rxn05459_c0",
                    name="Shikimate kinase",
                    equation="cpd00036[c0] + cpd00038[c0] => cpd00126[c0] + cpd00008[c0]",
                    direction="forward",
                    compartment="c0",
                    source="template_gapfill"
                )
            ],
            exchange_reactions_added=[],
            atp_correction=ATPCorrectionStats(
                performed=True,
                media_tested=54,
                media_passed=54,
                media_failed=0,
                reactions_added=0
            ),
            genomescale_gapfill=GenomescaleGapfillStats(
                performed=True,
                reactions_added=4,
                reversed_reactions=0,
                new_reactions=4
            ),
            model_properties=GapfilledModelProperties(
                num_reactions=860,
                num_metabolites=743,
                is_draft=False,
                requires_further_gapfilling=False
            )
        )
        assert response.success is True
        assert response.gapfilling_successful is True
        assert response.growth_rate_after > response.growth_rate_before


# =============================================================================
# Run FBA Request Tests
# =============================================================================


class TestRunFBARequest:
    """Tests for RunFBARequest validation."""

    def test_valid_minimal_request(self):
        """Test minimal valid request with defaults."""
        request = RunFBARequest(
            model_id="model_001.draft.gf",
            media_id="media_001"
        )
        assert request.objective == "bio1"
        assert request.maximize is True
        assert request.flux_threshold == 1e-6

    def test_valid_with_custom_objective(self):
        """Test valid request with custom objective."""
        request = RunFBARequest(
            model_id="model_001.draft.gf",
            media_id="media_001",
            objective="ATPM_c0",
            maximize=False,
            flux_threshold=1e-9
        )
        assert request.objective == "ATPM_c0"
        assert request.maximize is False
        assert request.flux_threshold == 1e-9

    def test_negative_flux_threshold(self):
        """Test rejection of negative flux threshold."""
        with pytest.raises(ValidationError):
            RunFBARequest(
                model_id="model_001.draft.gf",
                media_id="media_001",
                flux_threshold=-1e-6
            )


class TestRunFBAResponse:
    """Tests for RunFBAResponse structure."""

    def test_valid_optimal_response(self):
        """Test creation of optimal FBA response."""
        response = RunFBAResponse(
            model_id="model_001.draft.gf",
            media_id="media_001",
            objective_reaction="bio1",
            objective_value=0.874,
            status="optimal",
            solver_status="optimal",
            active_reactions=423,
            total_reactions=860,
            total_flux=2841.5,
            fluxes={"bio1": 0.874, "EX_cpd00027_e0": -5.0},
            uptake_fluxes=[
                UptakeFlux(
                    compound_id="cpd00027",
                    compound_name="D-Glucose",
                    formula="C6H12O6",
                    flux=-5.0,
                    reaction_id="EX_cpd00027_e0"
                )
            ],
            secretion_fluxes=[
                SecretionFlux(
                    compound_id="cpd00011",
                    compound_name="CO2",
                    formula="CO2",
                    flux=8.456,
                    reaction_id="EX_cpd00011_e0"
                )
            ],
            summary=FBASummary(
                uptake_reactions=15,
                secretion_reactions=8,
                internal_reactions=400,
                reversible_active=150,
                irreversible_active=273
            ),
            top_fluxes=[
                TopFlux(
                    reaction_id="bio1",
                    reaction_name="Biomass production",
                    flux=0.874,
                    direction="forward"
                )
            ]
        )
        assert response.success is True
        assert response.status == "optimal"
        assert response.objective_value > 0


# =============================================================================
# Database Lookup Types Tests
# =============================================================================


class TestCompoundLookupResult:
    """Tests for CompoundLookupResult structure."""

    def test_valid_compound_result(self):
        """Test creation of valid compound lookup result."""
        result = CompoundLookupResult(
            id="cpd00027",
            name="D-Glucose",
            abbreviation="glc__D",
            formula="C6H12O6",
            mass=180.156,
            charge=0,
            inchikey="WQZGKKKJIJFFOK-GASJEMHNSA-N",
            aliases=["glucose", "Glc", "dextrose"],
            external_ids={"KEGG": ["C00031"], "BiGG": ["glc__D"]}
        )
        assert result.success is True
        assert result.id == "cpd00027"
        assert "glucose" in result.aliases


class TestCompoundSearchResponse:
    """Tests for CompoundSearchResponse structure."""

    def test_valid_search_response(self):
        """Test creation of valid search response."""
        response = CompoundSearchResponse(
            query="glucose",
            num_results=2,
            results=[
                CompoundSearchResult(
                    id="cpd00027",
                    name="D-Glucose",
                    formula="C6H12O6",
                    match_type="name",
                    relevance_score=1.0
                ),
                CompoundSearchResult(
                    id="cpd00221",
                    name="D-Glucose 6-phosphate",
                    formula="C6H13O9P",
                    match_type="name",
                    relevance_score=0.85
                )
            ]
        )
        assert response.success is True
        assert response.num_results == 2
        assert len(response.results) == 2


class TestReactionLookupResult:
    """Tests for ReactionLookupResult structure."""

    def test_valid_reaction_result(self):
        """Test creation of valid reaction lookup result."""
        result = ReactionLookupResult(
            id="rxn00148",
            name="hexokinase",
            abbreviation="HEX1",
            equation="D-Glucose + ATP => ADP + H+ + D-Glucose 6-phosphate",
            equation_with_ids="(1) cpd00027[c0] + (1) cpd00002[c0] => (1) cpd00008[c0] + (1) cpd00067[c0] + (1) cpd00079[c0]",
            reversibility="irreversible_forward",
            direction_symbol=">",
            ec_numbers=["2.7.1.1"],
            pathways=["Glycolysis", "Central Metabolism"],
            is_transport=False,
            external_ids={"KEGG": ["R00200"], "BiGG": ["HEX1"]}
        )
        assert result.success is True
        assert result.id == "rxn00148"
        assert "2.7.1.1" in result.ec_numbers


# =============================================================================
# Error Response Tests
# =============================================================================


class TestErrorResponse:
    """Tests for ErrorResponse structure."""

    def test_valid_error_response(self):
        """Test creation of valid error response."""
        error = ErrorResponse(
            error_type="ValidationError",
            message="Invalid compound IDs",
            details=ErrorDetails(),
            suggestion="Use search_compounds to find valid IDs"
        )
        assert error.success is False
        assert error.error_type == "ValidationError"

    def test_minimal_error_response(self):
        """Test minimal error response (no details or suggestion)."""
        error = ErrorResponse(
            error_type="InternalError",
            message="An error occurred"
        )
        assert error.success is False
        assert error.details is None
        assert error.suggestion is None


# =============================================================================
# Integration Tests
# =============================================================================


class TestTypeIntegration:
    """Integration tests across multiple types."""

    def test_build_media_to_run_fba_flow(self):
        """Test type flow from build_media to run_fba."""
        # Build media response
        media_response = BuildMediaResponse(
            media_id="media_001",
            compounds=[
                CompoundInfo(
                    id="cpd00027",
                    name="D-Glucose",
                    formula="C6H12O6",
                    bounds=[-5.0, 100.0]
                )
            ],
            num_compounds=1,
            media_type="minimal",
            default_uptake_rate=100.0,
            custom_bounds_applied=1
        )

        # Use media_id in FBA request
        fba_request = RunFBARequest(
            model_id="model_001.draft.gf",
            media_id=media_response.media_id
        )

        assert fba_request.media_id == "media_001"

    def test_build_model_to_gapfill_flow(self):
        """Test type flow from build_model to gapfill."""
        # Build model response
        model_response = BuildModelResponse(
            model_id="model_001.draft",
            model_name="Test Model",
            num_reactions=100,
            num_metabolites=80,
            num_genes=50,
            num_exchange_reactions=20,
            template_used="Core",
            has_biomass_reaction=True,
            biomass_reaction_id="bio1",
            compartments=["c0", "e0"],
            has_atpm=True,
            atpm_reaction_id="ATPM_c0",
            statistics=ModelStatistics(
                reactions_by_compartment={"c0": 80, "e0": 20},
                metabolites_by_compartment={"c0": 60, "e0": 20},
                reversible_reactions=50,
                irreversible_reactions=50,
                transport_reactions=10
            ),
            model_properties=ModelProperties(
                is_draft=True,
                requires_gapfilling=True
            )
        )

        # Use model_id in gapfill request
        gapfill_request = GapfillModelRequest(
            model_id=model_response.model_id,
            media_id="media_001"
        )

        assert gapfill_request.model_id == "model_001.draft"
