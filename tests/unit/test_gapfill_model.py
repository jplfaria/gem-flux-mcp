"""
Unit tests for gapfill_model tool.

Tests validation, ATP correction, genome-scale gapfilling, and error handling.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import copy

from gem_flux_mcp.tools.gapfill_model import (
    validate_gapfill_inputs,
    check_baseline_growth,
    run_atp_correction,
    run_genome_scale_gapfilling,
    integrate_gapfill_solution,
    enrich_reaction_metadata,
    gapfill_model,
)
from gem_flux_mcp.errors import ValidationError, NotFoundError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_model():
    """Create mock COBRApy model."""
    model = Mock()
    model.reactions = []
    model.metabolites = []

    # Add biomass reaction
    bio_rxn = Mock()
    bio_rxn.id = "bio1"
    model.reactions.append(bio_rxn)

    # Add notes dict
    model.notes = {"template_used": "GramNegative"}

    # Mock optimize
    solution = Mock()
    solution.status = "optimal"
    solution.objective_value = 0.0
    model.optimize = Mock(return_value=solution)

    # Mock add_reactions
    model.add_reactions = Mock()

    return model


@pytest.fixture
def mock_media():
    """Create mock MSMedia object."""
    media = Mock()
    media.id = "media_001"
    media.get_media_constraints = Mock(return_value={"cpd00027_e0": (-5, 100)})
    return media


@pytest.fixture
def mock_template():
    """Create mock MSTemplate object."""
    template = Mock()
    template.reactions = Mock()

    # Mock reactions.get_by_id
    mock_reaction = Mock()
    mock_reaction.id = "rxn00001_c"
    mock_reaction.to_reaction = Mock(return_value=Mock(
        id="rxn00001_c0",
        lower_bound=0,
        upper_bound=1000,
    ))

    template.reactions.get_by_id = Mock(return_value=mock_reaction)
    template.reactions.__contains__ = Mock(return_value=True)

    return template


@pytest.fixture
def setup_storage(mock_model, mock_media):
    """Setup model and media storage."""
    with patch("gem_flux_mcp.tools.gapfill_model.MODEL_STORAGE") as model_storage, \
         patch("gem_flux_mcp.tools.gapfill_model.MEDIA_STORAGE") as media_storage:

        model_storage.__getitem__ = Mock(side_effect=lambda k: mock_model if k == "model_001.draft" else None)
        model_storage.__contains__ = Mock(side_effect=lambda k: k == "model_001.draft")
        model_storage.keys = Mock(return_value=["model_001.draft"])

        media_storage.__getitem__ = Mock(side_effect=lambda k: mock_media if k == "media_001" else None)
        media_storage.__contains__ = Mock(side_effect=lambda k: k == "media_001")
        media_storage.keys = Mock(return_value=["media_001"])

        yield model_storage, media_storage


# ============================================================================
# Test validate_gapfill_inputs
# ============================================================================


def test_validate_gapfill_inputs_success(setup_storage):
    """Test successful validation."""
    model_storage, media_storage = setup_storage

    with patch("gem_flux_mcp.tools.gapfill_model.model_exists", return_value=True), \
         patch("gem_flux_mcp.tools.gapfill_model.media_exists", return_value=True), \
         patch("gem_flux_mcp.tools.gapfill_model.retrieve_model") as mock_retrieve:

        # Setup model with biomass
        mock_model = Mock()
        bio_rxn = Mock()
        bio_rxn.id = "bio1"
        mock_model.reactions = [bio_rxn]
        mock_retrieve.return_value = mock_model

        # Should not raise
        validate_gapfill_inputs(
            model_id="model_001.draft",
            media_id="media_001",
            target_growth_rate=0.01,
            gapfill_mode="full",
        )


def test_validate_gapfill_inputs_model_not_found():
    """Test validation fails when model not found."""
    with patch("gem_flux_mcp.tools.gapfill_model.model_exists", return_value=False), \
         patch("gem_flux_mcp.tools.gapfill_model.MODEL_STORAGE", {"other_model": Mock()}):

        with pytest.raises(NotFoundError) as exc_info:
            validate_gapfill_inputs(
                model_id="nonexistent",
                media_id="media_001",
                target_growth_rate=0.01,
                gapfill_mode="full",
            )

        assert exc_info.value.error_code == "MODEL_NOT_FOUND"
        assert "nonexistent" in exc_info.value.message


def test_validate_gapfill_inputs_media_not_found():
    """Test validation fails when media not found."""
    with patch("gem_flux_mcp.tools.gapfill_model.model_exists", return_value=True), \
         patch("gem_flux_mcp.tools.gapfill_model.media_exists", return_value=False), \
         patch("gem_flux_mcp.tools.gapfill_model.MEDIA_STORAGE", {"other_media": Mock()}):

        with pytest.raises(NotFoundError) as exc_info:
            validate_gapfill_inputs(
                model_id="model_001.draft",
                media_id="nonexistent",
                target_growth_rate=0.01,
                gapfill_mode="full",
            )

        assert exc_info.value.error_code == "MEDIA_NOT_FOUND"
        assert "nonexistent" in exc_info.value.message


def test_validate_gapfill_inputs_negative_growth_rate():
    """Test validation fails with negative growth rate."""
    with patch("gem_flux_mcp.tools.gapfill_model.model_exists", return_value=True), \
         patch("gem_flux_mcp.tools.gapfill_model.media_exists", return_value=True):

        with pytest.raises(ValidationError) as exc_info:
            validate_gapfill_inputs(
                model_id="model_001.draft",
                media_id="media_001",
                target_growth_rate=-0.01,
                gapfill_mode="full",
            )

        assert exc_info.value.error_code == "INVALID_TARGET_GROWTH_RATE"
        assert "positive" in exc_info.value.message.lower()


def test_validate_gapfill_inputs_zero_growth_rate():
    """Test validation fails with zero growth rate."""
    with patch("gem_flux_mcp.tools.gapfill_model.model_exists", return_value=True), \
         patch("gem_flux_mcp.tools.gapfill_model.media_exists", return_value=True):

        with pytest.raises(ValidationError) as exc_info:
            validate_gapfill_inputs(
                model_id="model_001.draft",
                media_id="media_001",
                target_growth_rate=0.0,
                gapfill_mode="full",
            )

        assert exc_info.value.error_code == "INVALID_TARGET_GROWTH_RATE"


def test_validate_gapfill_inputs_invalid_mode():
    """Test validation fails with invalid gapfill_mode."""
    with patch("gem_flux_mcp.tools.gapfill_model.model_exists", return_value=True), \
         patch("gem_flux_mcp.tools.gapfill_model.media_exists", return_value=True):

        with pytest.raises(ValidationError) as exc_info:
            validate_gapfill_inputs(
                model_id="model_001.draft",
                media_id="media_001",
                target_growth_rate=0.01,
                gapfill_mode="invalid_mode",
            )

        assert exc_info.value.error_code == "INVALID_GAPFILL_MODE"
        assert "full" in str(exc_info.value.details)


def test_validate_gapfill_inputs_no_biomass():
    """Test validation with model lacking biomass reaction.

    Per gapfill_model.py lines 142-147, missing biomass now logs WARNING
    instead of raising ValidationError. This allows offline model building
    (annotate_with_rast=False) and API correctness tests with empty models.
    ModelSEEDpy itself doesn't require biomass for gapfilling.
    """
    with patch("gem_flux_mcp.tools.gapfill_model.model_exists", return_value=True), \
         patch("gem_flux_mcp.tools.gapfill_model.media_exists", return_value=True), \
         patch("gem_flux_mcp.tools.gapfill_model.retrieve_model") as mock_retrieve:

        # Model without biomass
        mock_model = Mock()
        mock_model.reactions = []  # No biomass reaction
        mock_retrieve.return_value = mock_model

        # Should NOT raise ValidationError - just logs warning and proceeds
        # No exception means validation passed (with warning logged)
        validate_gapfill_inputs(
            model_id="model_001.draft",
            media_id="media_001",
            target_growth_rate=0.01,
            gapfill_mode="full",
        )
        # Success - validation completed without raising exception


# ============================================================================
# Test check_baseline_growth
# ============================================================================


def test_check_baseline_growth_optimal(mock_model, mock_media):
    """Test baseline growth check with optimal solution."""
    mock_model.optimize.return_value.status = "optimal"
    mock_model.optimize.return_value.objective_value = 0.5

    growth_rate = check_baseline_growth(mock_model, mock_media)

    assert growth_rate == 0.5
    mock_media.get_media_constraints.assert_called()
    mock_model.optimize.assert_called_once()


def test_check_baseline_growth_infeasible(mock_model, mock_media):
    """Test baseline growth check with infeasible solution."""
    mock_model.optimize.return_value.status = "infeasible"

    growth_rate = check_baseline_growth(mock_model, mock_media)

    assert growth_rate == 0.0


def test_check_baseline_growth_exception(mock_model, mock_media):
    """Test baseline growth check handles exceptions."""
    mock_model.optimize.side_effect = Exception("FBA failed")

    growth_rate = check_baseline_growth(mock_model, mock_media)

    assert growth_rate == 0.0


# ============================================================================
# Test integrate_gapfill_solution
# ============================================================================


def test_integrate_gapfill_solution_empty():
    """Test integration with empty solution."""
    mock_model = Mock()
    mock_template = Mock()

    solution = {"new": {}, "reversed": {}}

    added = integrate_gapfill_solution(mock_model, mock_template, solution)

    assert len(added) == 0
    mock_model.add_reactions.assert_not_called()


def test_integrate_gapfill_solution_new_reactions(mock_template):
    """Test integration with new reactions."""
    mock_model = Mock()
    mock_model.add_reactions = Mock()

    solution = {
        "new": {
            "rxn00001_c0": ">",
            "rxn00002_c0": "<",
        },
        "reversed": {},
    }

    with patch("gem_flux_mcp.tools.gapfill_model.get_reaction_constraints_from_direction") as mock_bounds:
        mock_bounds.side_effect = [(0, 1000), (-1000, 0)]

        added = integrate_gapfill_solution(mock_model, mock_template, solution)

    assert len(added) == 2
    assert added[0]["id"] == "rxn00001_c0"
    assert added[0]["direction"] == ">"
    assert added[1]["id"] == "rxn00002_c0"
    assert added[1]["direction"] == "<"


def test_integrate_gapfill_solution_skip_exchanges(mock_template):
    """Test integration skips exchange reactions."""
    mock_model = Mock()

    solution = {
        "new": {
            "rxn00001_c0": ">",
            "EX_cpd00027_e0": ">",  # Exchange - should be skipped
        },
        "reversed": {},
    }

    with patch("gem_flux_mcp.tools.gapfill_model.get_reaction_constraints_from_direction", return_value=(0, 1000)):
        added = integrate_gapfill_solution(mock_model, mock_template, solution)

    assert len(added) == 1
    assert added[0]["id"] == "rxn00001_c0"


# ============================================================================
# Test enrich_reaction_metadata
# ============================================================================


def test_enrich_reaction_metadata_success():
    """Test reaction metadata enrichment."""
    reactions = [
        {"id": "rxn00001_c0", "direction": ">", "bounds": [0, 1000]},
        {"id": "rxn00002_c0", "direction": "<", "bounds": [-1000, 0]},
    ]

    mock_db = Mock()
    mock_db.get_reaction_by_id = Mock(side_effect=[
        {"name": "hexokinase", "equation": "glucose + ATP => G6P + ADP"},
        {"name": "phosphofructokinase", "equation": "F6P + ATP => FBP + ADP"},
    ])

    enriched = enrich_reaction_metadata(reactions, mock_db)

    assert len(enriched) == 2
    assert enriched[0]["name"] == "hexokinase"
    assert enriched[0]["direction"] == "forward"
    assert enriched[0]["compartment"] == "c0"
    assert enriched[1]["direction"] == "reverse"


def test_enrich_reaction_metadata_unknown_reaction():
    """Test enrichment handles unknown reactions."""
    reactions = [
        {"id": "rxn99999_c0", "direction": ">", "bounds": [0, 1000]},
    ]

    mock_db = Mock()
    mock_db.get_reaction_by_id = Mock(return_value=None)

    enriched = enrich_reaction_metadata(reactions, mock_db)

    assert len(enriched) == 1
    assert enriched[0]["name"] == "Unknown reaction"
    assert enriched[0]["equation"] == ""


def test_enrich_reaction_metadata_direction_mapping():
    """Test direction symbol to string mapping."""
    reactions = [
        {"id": "rxn00001_c0", "direction": ">", "bounds": [0, 1000]},
        {"id": "rxn00002_c0", "direction": "<", "bounds": [-1000, 0]},
        {"id": "rxn00003_c0", "direction": "=", "bounds": [-1000, 1000]},
    ]

    mock_db = Mock()
    mock_db.get_reaction_by_id = Mock(return_value={"name": "test", "equation": ""})

    enriched = enrich_reaction_metadata(reactions, mock_db)

    assert enriched[0]["direction"] == "forward"
    assert enriched[1]["direction"] == "reverse"
    assert enriched[2]["direction"] == "reversible"


# ============================================================================
# Test gapfill_model - Already Meets Target
# ============================================================================


def test_gapfill_model_already_meets_target(setup_storage):
    """Test gapfilling when model already meets target growth."""
    model_storage, media_storage = setup_storage

    with patch("gem_flux_mcp.tools.gapfill_model.validate_gapfill_inputs"), \
         patch("gem_flux_mcp.tools.gapfill_model.retrieve_model") as mock_retrieve_model, \
         patch("gem_flux_mcp.tools.gapfill_model.retrieve_media") as mock_retrieve_media, \
         patch("gem_flux_mcp.tools.gapfill_model.check_baseline_growth", return_value=0.5), \
         patch("gem_flux_mcp.tools.gapfill_model.transform_state_suffix", return_value="model_001.draft.gf"), \
         patch("gem_flux_mcp.tools.gapfill_model.store_model") as mock_store, \
         patch("copy.deepcopy") as mock_deepcopy:

        mock_model = Mock()
        mock_model.reactions = [Mock()]
        mock_model.metabolites = [Mock()]
        mock_retrieve_model.return_value = mock_model
        mock_deepcopy.return_value = mock_model

        mock_media = Mock()
        mock_retrieve_media.return_value = mock_media

        mock_db = Mock()

        result = gapfill_model(
            model_id="model_001.draft",
            media_id="media_001",
            db_index=mock_db,
            target_growth_rate=0.01,
        )

        assert result["success"] is True
        assert result["model_id"] == "model_001.draft.gf"
        assert result["gapfilling_successful"] is True
        assert result["num_reactions_added"] == 0
        assert result["growth_rate_before"] == 0.5
        assert result["growth_rate_after"] == 0.5
        mock_store.assert_called_once()


# ============================================================================
# Test gapfill_model - Full Workflow
# ============================================================================


def test_gapfill_model_full_workflow(setup_storage):
    """Test complete gapfilling workflow."""
    model_storage, media_storage = setup_storage

    mock_db = Mock()

    with patch("gem_flux_mcp.tools.gapfill_model.validate_gapfill_inputs"), \
         patch("gem_flux_mcp.tools.gapfill_model.retrieve_model") as mock_retrieve_model, \
         patch("gem_flux_mcp.tools.gapfill_model.retrieve_media") as mock_retrieve_media, \
         patch("gem_flux_mcp.tools.gapfill_model.check_baseline_growth") as mock_baseline, \
         patch("gem_flux_mcp.tools.gapfill_model.get_template") as mock_get_template, \
         patch("gem_flux_mcp.tools.gapfill_model.run_atp_correction") as mock_atp, \
         patch("gem_flux_mcp.tools.gapfill_model.run_genome_scale_gapfilling") as mock_gapfill, \
         patch("gem_flux_mcp.tools.gapfill_model.integrate_gapfill_solution") as mock_integrate, \
         patch("gem_flux_mcp.tools.gapfill_model.enrich_reaction_metadata") as mock_enrich, \
         patch("gem_flux_mcp.tools.gapfill_model.transform_state_suffix", return_value="model_001.draft.gf"), \
         patch("gem_flux_mcp.tools.gapfill_model.store_model"), \
         patch("copy.deepcopy") as mock_deepcopy:

        # Setup mocks
        mock_model = Mock()
        mock_model.reactions = [Mock()]
        mock_model.metabolites = [Mock()]
        mock_model.notes = {"template_used": "GramNegative"}
        mock_retrieve_model.return_value = mock_model
        mock_deepcopy.return_value = mock_model

        mock_media = Mock()
        mock_media.get_media_constraints = Mock(return_value={"cpd00027_e0": (-5, 100)})
        mock_retrieve_media.return_value = mock_media

        # Baseline: 0.0 before, 0.874 after
        mock_baseline.side_effect = [0.0, 0.874]

        # Templates
        mock_template = Mock()
        mock_template.reactions = []
        mock_get_template.return_value = mock_template

        # ATP correction
        mock_atp.return_value = {
            "performed": True,
            "media_tested": 54,
            "media_passed": 50,
            "media_failed": 4,
            "reactions_added": 2,
            "failed_media_examples": [],
            "tests": [],
        }

        # Genome-scale gapfilling
        mock_gapfill.return_value = {
            "performed": True,
            "solution_found": True,
            "reactions_added": 3,
            "new_reactions": 3,
            "reversed_reactions": 0,
            "solution": {"new": {}, "reversed": {}},
        }

        # Integration
        mock_integrate.return_value = [
            {"id": "rxn00001_c0", "direction": ">", "bounds": [0, 1000]},
        ]

        # Enrichment
        mock_enrich.return_value = [
            {
                "id": "rxn00001_c0",
                "name": "hexokinase",
                "equation": "glucose + ATP => G6P + ADP",
                "direction": "forward",
                "compartment": "c0",
                "bounds": [0, 1000],
                "source": "template_gapfill",
            }
        ]

        result = gapfill_model(
            model_id="model_001.draft",
            media_id="media_001",
            db_index=mock_db,
            target_growth_rate=0.01,
            gapfill_mode="full",
        )

        assert result["success"] is True
        assert result["model_id"] == "model_001.draft.gf"
        assert result["gapfilling_successful"] is True
        assert result["num_reactions_added"] == 1
        assert result["growth_rate_before"] == 0.0
        assert result["growth_rate_after"] == 0.874
        assert result["atp_correction"]["performed"] is True
        assert result["genomescale_gapfill"]["performed"] is True


# ============================================================================
# Test Error Handling
# ============================================================================


def test_gapfill_model_validation_error():
    """Test gapfilling handles validation errors."""
    mock_db = Mock()

    with patch("gem_flux_mcp.tools.gapfill_model.validate_gapfill_inputs") as mock_validate:
        mock_validate.side_effect = ValidationError(
            message="Invalid input",
            error_code="VALIDATION_ERROR",
        )

        with pytest.raises(ValidationError):
            gapfill_model(
                model_id="model_001.draft",
                media_id="media_001",
                db_index=mock_db,
                target_growth_rate=-1,
            )


def test_gapfill_model_not_found_error():
    """Test gapfilling handles not found errors."""
    mock_db = Mock()

    with patch("gem_flux_mcp.tools.gapfill_model.validate_gapfill_inputs") as mock_validate:
        mock_validate.side_effect = NotFoundError(
            message="Model not found",
            error_code="MODEL_NOT_FOUND",
        )

        with pytest.raises(NotFoundError):
            gapfill_model(
                model_id="nonexistent",
                media_id="media_001",
                db_index=mock_db,
                target_growth_rate=0.01,
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
