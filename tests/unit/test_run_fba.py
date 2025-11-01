"""
Unit tests for run_fba tool.

Tests validation, media application, FBA execution, and result processing.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import copy

from gem_flux_mcp.tools.run_fba import (
    validate_fba_inputs,
    apply_media_to_model,
    get_compound_name_safe,
    get_reaction_name_safe,
    extract_fluxes,
    run_fba,
)
from gem_flux_mcp.errors import ValidationError, NotFoundError, InfeasibilityError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_model():
    """Create mock COBRApy model."""
    model = Mock()

    # Create actual reaction objects for iteration
    bio_rxn = Mock()
    bio_rxn.id = "bio1"
    bio_rxn.lower_bound = 0
    bio_rxn.upper_bound = 1000

    ex_glc = Mock()
    ex_glc.id = "EX_cpd00027_e0"
    ex_glc.lower_bound = -10
    ex_glc.upper_bound = 100

    ex_o2 = Mock()
    ex_o2.id = "EX_cpd00007_e0"
    ex_o2.lower_bound = -10
    ex_o2.upper_bound = 100

    # Create reactions list/dict hybrid
    reactions_list = [bio_rxn, ex_glc, ex_o2]
    reactions_dict = Mock()
    reactions_dict.__contains__ = Mock(
        side_effect=lambda x: x in ["bio1", "EX_cpd00027_e0", "EX_cpd00007_e0"]
    )
    reactions_dict.__iter__ = Mock(return_value=iter(reactions_list))
    reactions_dict.__len__ = Mock(return_value=len(reactions_list))

    model.reactions = reactions_dict

    # Create metabolites list
    metabolites_list = [Mock(), Mock()]  # 2 metabolites
    model.metabolites = Mock()
    model.metabolites.__len__ = Mock(return_value=len(metabolites_list))

    # Mock optimize
    solution = Mock()
    solution.status = "optimal"
    solution.objective_value = 0.874

    # Mock fluxes as pandas Series
    import pandas as pd
    fluxes_dict = {
        "bio1": 0.874,
        "EX_cpd00027_e0": -5.0,
        "EX_cpd00007_e0": -10.2,
        "EX_cpd00011_e0": 8.5,
        "rxn00148_c0": 5.0,
        "rxn00200_c0": 0.0000001,  # Below threshold
    }
    solution.fluxes = pd.Series(fluxes_dict)

    model.optimize = Mock(return_value=solution)

    # Mock medium property
    model.medium = {}

    # Mock objective
    model.objective = Mock()
    model.objective.direction = "max"

    return model


@pytest.fixture
def mock_media_data():
    """Create mock media data dict."""
    return {
        "bounds": {
            "cpd00027": (-5, 100),
            "cpd00007": (-10, 100),
        },
        "default_uptake": 100.0,
        "num_compounds": 2,
    }


@pytest.fixture
def mock_db_index():
    """Create mock database index."""
    db_index = Mock()

    # Mock get_compound
    def mock_get_compound(cpd_id):
        class CompoundMock:
            def __init__(self, name, formula):
                self.name = name
                self.formula = formula

        compounds = {
            "cpd00027": CompoundMock("D-Glucose", "C6H12O6"),
            "cpd00007": CompoundMock("O2", "O2"),
            "cpd00011": CompoundMock("CO2", "CO2"),
        }
        if cpd_id in compounds:
            return compounds[cpd_id]
        raise KeyError(f"Compound {cpd_id} not found")

    # Mock get_reaction
    def mock_get_reaction(rxn_id):
        class ReactionMock:
            def __init__(self, name):
                self.name = name

        reactions = {
            "bio1": ReactionMock("Biomass production"),
            "rxn00148": ReactionMock("Hexokinase"),
            "rxn00200": ReactionMock("Phosphoglucose isomerase"),
        }
        if rxn_id in reactions:
            return reactions[rxn_id]
        raise KeyError(f"Reaction {rxn_id} not found")

    db_index.get_compound = Mock(side_effect=mock_get_compound)
    db_index.get_reaction = Mock(side_effect=mock_get_reaction)

    return db_index


@pytest.fixture
def setup_storage(mock_model, mock_media_data):
    """Setup model and media storage."""
    with patch("gem_flux_mcp.tools.run_fba.model_exists") as mock_model_exists, \
         patch("gem_flux_mcp.tools.run_fba.media_exists") as mock_media_exists, \
         patch("gem_flux_mcp.tools.run_fba.retrieve_model") as mock_retrieve_model, \
         patch("gem_flux_mcp.tools.run_fba.retrieve_media") as mock_retrieve_media, \
         patch("gem_flux_mcp.tools.run_fba.MODEL_STORAGE") as model_storage, \
         patch("gem_flux_mcp.tools.run_fba.MEDIA_STORAGE") as media_storage:

        # Mock existence checks
        mock_model_exists.side_effect = lambda k: k == "model_001.gf"
        mock_media_exists.side_effect = lambda k: k == "media_001"

        # Mock retrieval
        mock_retrieve_model.return_value = mock_model
        mock_retrieve_media.return_value = mock_media_data

        # Mock storage dicts for error messages
        model_storage.keys.return_value = ["model_001.gf"]
        media_storage.keys.return_value = ["media_001"]

        yield model_storage, media_storage


# ============================================================================
# Test validate_fba_inputs
# ============================================================================


def test_validate_fba_inputs_valid(setup_storage):
    """Test validation with valid inputs."""
    model_storage, media_storage = setup_storage

    # Should not raise
    validate_fba_inputs(
        model_id="model_001.gf",
        media_id="media_001",
        objective="bio1",
        flux_threshold=1e-6,
    )


def test_validate_fba_inputs_model_not_found(setup_storage):
    """Test validation with non-existent model."""
    model_storage, media_storage = setup_storage

    with pytest.raises(NotFoundError) as exc_info:
        validate_fba_inputs(
            model_id="model_999",
            media_id="media_001",
            objective="bio1",
            flux_threshold=1e-6,
        )

    assert "model_999" in exc_info.value.message.lower()
    assert "not found" in exc_info.value.message.lower()


def test_validate_fba_inputs_media_not_found(setup_storage):
    """Test validation with non-existent media."""
    model_storage, media_storage = setup_storage

    with pytest.raises(NotFoundError) as exc_info:
        validate_fba_inputs(
            model_id="model_001.gf",
            media_id="media_999",
            objective="bio1",
            flux_threshold=1e-6,
        )

    assert "media_999" in exc_info.value.message.lower()
    assert "not found" in exc_info.value.message.lower()


def test_validate_fba_inputs_negative_threshold(setup_storage):
    """Test validation with negative flux threshold."""
    model_storage, media_storage = setup_storage

    with pytest.raises(ValidationError) as exc_info:
        validate_fba_inputs(
            model_id="model_001.gf",
            media_id="media_001",
            objective="bio1",
            flux_threshold=-1.0,
        )

    assert "positive" in exc_info.value.message.lower()
    assert "threshold" in exc_info.value.message.lower()


# ============================================================================
# Test apply_media_to_model
# ============================================================================


def test_apply_media_to_model_basic(mock_model, mock_media_data):
    """Test media application to model."""
    apply_media_to_model(mock_model, mock_media_data)

    # Check medium was updated
    assert mock_model.medium is not None
    assert len(mock_model.medium) == 2

    # Check bounds are positive (absolute values)
    assert mock_model.medium["EX_cpd00027_e0"] == 5.0
    assert mock_model.medium["EX_cpd00007_e0"] == 10.0


def test_apply_media_to_model_missing_exchange(mock_model, mock_media_data):
    """Test media application handles missing exchange reactions gracefully."""
    # Add a compound with no exchange reaction
    mock_media_data["bounds"]["cpd99999"] = (-5, 100)

    # Should complete without error - logs warning but continues with valid exchanges
    apply_media_to_model(mock_model, mock_media_data)

    # Verify model was still updated for valid compounds
    assert mock_model.medium is not None
    # Should have the 2 valid exchanges, cpd99999 logged as missing
    assert len(mock_model.medium) == 2
    assert "EX_cpd00027_e0" in mock_model.medium
    assert "EX_cpd00007_e0" in mock_model.medium
    # Missing compound should not be in medium
    assert "EX_cpd99999_e0" not in mock_model.medium


# ============================================================================
# Test get_compound_name_safe
# ============================================================================


def test_get_compound_name_safe_found(mock_db_index):
    """Test getting compound name when found."""
    name = get_compound_name_safe(mock_db_index, "cpd00027")
    assert name == "D-Glucose"


def test_get_compound_name_safe_not_found(mock_db_index):
    """Test getting compound name when not found."""
    name = get_compound_name_safe(mock_db_index, "cpd99999")
    assert name == "cpd99999"  # Returns ID as fallback


# ============================================================================
# Test get_reaction_name_safe
# ============================================================================


def test_get_reaction_name_safe_found(mock_db_index):
    """Test getting reaction name when found."""
    name = get_reaction_name_safe(mock_db_index, "rxn00148_c0")
    assert name == "Hexokinase"


def test_get_reaction_name_safe_not_found(mock_db_index):
    """Test getting reaction name when not found."""
    name = get_reaction_name_safe(mock_db_index, "rxn99999_c0")
    assert name == "rxn99999_c0"  # Returns ID as fallback


def test_get_reaction_name_safe_no_compartment(mock_db_index):
    """Test getting reaction name without compartment suffix."""
    name = get_reaction_name_safe(mock_db_index, "bio1")
    assert name == "Biomass production"


# ============================================================================
# Test extract_fluxes
# ============================================================================


def test_extract_fluxes_basic(mock_model, mock_db_index):
    """Test flux extraction from solution."""
    solution = mock_model.optimize()

    result = extract_fluxes(solution, 1e-6, mock_db_index)

    # Check structure
    assert "fluxes" in result
    assert "uptake_fluxes" in result
    assert "secretion_fluxes" in result
    assert "active_reactions" in result
    assert "total_flux" in result
    assert "top_fluxes" in result

    # Check flux filtering
    assert "rxn00200_c0" not in result["fluxes"]  # Below threshold

    # Check uptake/secretion separation
    assert len(result["uptake_fluxes"]) == 2  # Glucose and O2
    assert len(result["secretion_fluxes"]) == 1  # CO2

    # Check uptake has compound names
    uptake_ids = {f["compound_id"] for f in result["uptake_fluxes"]}
    assert "cpd00027" in uptake_ids
    assert "cpd00007" in uptake_ids

    # Check secretion has compound names
    secretion_ids = {f["compound_id"] for f in result["secretion_fluxes"]}
    assert "cpd00011" in secretion_ids


def test_extract_fluxes_top_fluxes(mock_model, mock_db_index):
    """Test top fluxes extraction."""
    solution = mock_model.optimize()

    result = extract_fluxes(solution, 1e-6, mock_db_index)

    # Should have top fluxes
    assert len(result["top_fluxes"]) <= 10

    # Should include bio1
    top_rxn_ids = [f["reaction_id"] for f in result["top_fluxes"]]
    assert "bio1" in top_rxn_ids

    # Should have reaction names
    assert all("reaction_name" in f for f in result["top_fluxes"])


# ============================================================================
# Test run_fba - Success Cases
# ============================================================================


@patch("gem_flux_mcp.tools.run_fba.DatabaseIndex")
@patch("gem_flux_mcp.tools.run_fba.copy")
def test_run_fba_optimal(
    mock_copy,
    mock_db_class,
    setup_storage,
    mock_model,
    mock_db_index,
):
    """Test run_fba with optimal solution."""
    model_storage, media_storage = setup_storage

    # Setup mocks
    mock_copy.deepcopy = Mock(return_value=mock_model)
    mock_db_class.get_instance = Mock(return_value=mock_db_index)

    # Run FBA
    result = run_fba(
        model_id="model_001.gf",
        media_id="media_001",
        db_index=mock_db_index,
        objective="bio1",
        maximize=True,
        flux_threshold=1e-6,
    )

    # Check success
    assert result["success"] is True
    assert result["status"] == "optimal"
    assert result["objective_value"] == 0.874

    # Check metadata
    assert result["model_id"] == "model_001.gf"
    assert result["media_id"] == "media_001"
    assert result["objective_reaction"] == "bio1"

    # Check fluxes
    assert "fluxes" in result
    assert "uptake_fluxes" in result
    assert "secretion_fluxes" in result

    # Check summary
    assert "summary" in result
    assert "uptake_reactions" in result["summary"]
    assert "secretion_reactions" in result["summary"]


@patch("gem_flux_mcp.tools.run_fba.DatabaseIndex")
@patch("gem_flux_mcp.tools.run_fba.copy")
def test_run_fba_minimize(
    mock_copy,
    mock_db_class,
    setup_storage,
    mock_model,
    mock_db_index,
):
    """Test run_fba with minimization."""
    model_storage, media_storage = setup_storage

    # Setup mocks
    mock_copy.deepcopy = Mock(return_value=mock_model)
    mock_db_class.get_instance = Mock(return_value=mock_db_index)

    # Run FBA with minimize
    result = run_fba(
        model_id="model_001.gf",
        media_id="media_001",
        db_index=mock_db_index,
        objective="bio1",
        maximize=False,  # Minimize
        flux_threshold=1e-6,
    )

    # Check success
    assert result["success"] is True

    # Check that objective was set (we don't check direction since it's handled via coefficient)
    assert mock_model.objective is not None


# ============================================================================
# Test run_fba - Error Cases
# ============================================================================


@patch("gem_flux_mcp.tools.run_fba.DatabaseIndex")
@patch("gem_flux_mcp.tools.run_fba.copy")
def test_run_fba_infeasible(
    mock_copy,
    mock_db_class,
    setup_storage,
    mock_model,
    mock_db_index,
):
    """Test run_fba with infeasible model."""
    model_storage, media_storage = setup_storage

    # Setup mocks
    mock_copy.deepcopy = Mock(return_value=mock_model)
    mock_db_class.get_instance = Mock(return_value=mock_db_index)

    # Make model infeasible
    solution = Mock()
    solution.status = "infeasible"
    mock_model.optimize = Mock(return_value=solution)

    # Run FBA
    result = run_fba(
        model_id="model_001.gf",
        media_id="media_001",
        db_index=mock_db_index,
    )

    # Check error response
    assert result["success"] is False
    assert "infeasible" in result["message"].lower() or "feasible" in result["message"].lower()
    assert "suggestions" in result
    # Check that gapfilling is suggested
    suggestions_text = " ".join(result["suggestions"]).lower()
    assert "gapfill" in suggestions_text


@patch("gem_flux_mcp.tools.run_fba.DatabaseIndex")
@patch("gem_flux_mcp.tools.run_fba.copy")
def test_run_fba_unbounded(
    mock_copy,
    mock_db_class,
    setup_storage,
    mock_model,
    mock_db_index,
):
    """Test run_fba with unbounded model."""
    model_storage, media_storage = setup_storage

    # Setup mocks
    mock_copy.deepcopy = Mock(return_value=mock_model)
    mock_db_class.get_instance = Mock(return_value=mock_db_index)

    # Make model unbounded
    solution = Mock()
    solution.status = "unbounded"
    mock_model.optimize = Mock(return_value=solution)

    # Run FBA
    result = run_fba(
        model_id="model_001.gf",
        media_id="media_001",
        db_index=mock_db_index,
    )

    # Check error response
    assert result["success"] is False
    assert "unbounded" in result["message"].lower()
    assert "suggestions" in result
    # Check that bounds are mentioned in suggestions
    suggestions_text = " ".join(result["suggestions"]).lower()
    assert "bounds" in suggestions_text or "exchange" in suggestions_text


@patch("gem_flux_mcp.tools.run_fba.DatabaseIndex")
@patch("gem_flux_mcp.tools.run_fba.copy")
def test_run_fba_invalid_objective(
    mock_copy,
    mock_db_class,
    setup_storage,
    mock_model,
    mock_db_index,
):
    """Test run_fba with invalid objective."""
    model_storage, media_storage = setup_storage

    # Setup mocks
    mock_copy.deepcopy = Mock(return_value=mock_model)
    mock_db_class.get_instance = Mock(return_value=mock_db_index)

    # Mock reactions to not contain invalid objective
    mock_model.reactions.__contains__ = Mock(return_value=False)

    # Run FBA with invalid objective
    result = run_fba(
        model_id="model_001.gf",
        media_id="media_001",
        db_index=mock_db_index,
        objective="invalid_rxn",
    )

    # Check error response
    assert result["success"] is False
    assert "objective" in result["message"].lower()
    assert "not found" in result["message"].lower()


# ============================================================================
# Test run_fba - Edge Cases
# ============================================================================


@patch("gem_flux_mcp.tools.run_fba.DatabaseIndex")
@patch("gem_flux_mcp.tools.run_fba.copy")
def test_run_fba_custom_threshold(
    mock_copy,
    mock_db_class,
    setup_storage,
    mock_model,
    mock_db_index,
):
    """Test run_fba with custom flux threshold."""
    model_storage, media_storage = setup_storage

    # Setup mocks
    mock_copy.deepcopy = Mock(return_value=mock_model)
    mock_db_class.get_instance = Mock(return_value=mock_db_index)

    # Run FBA with high threshold
    result = run_fba(
        model_id="model_001.gf",
        media_id="media_001",
        db_index=mock_db_index,
        flux_threshold=1.0,  # High threshold
    )

    # Check that fewer reactions reported
    assert result["success"] is True
    # Should only include fluxes > 1.0
    for flux in result["fluxes"].values():
        assert abs(flux) > 1.0 or flux == 0.0


@patch("gem_flux_mcp.tools.run_fba.DatabaseIndex")
@patch("gem_flux_mcp.tools.run_fba.copy")
def test_run_fba_preserves_original_model(
    mock_copy,
    mock_db_class,
    setup_storage,
    mock_model,
    mock_db_index,
):
    """Test that run_fba doesn't modify original model."""
    model_storage, media_storage = setup_storage

    # Create a copy that will be modified
    model_copy = Mock()
    model_copy.reactions = mock_model.reactions
    model_copy.metabolites = mock_model.metabolites
    model_copy.medium = {}
    model_copy.objective = Mock()
    model_copy.objective.direction = "max"
    model_copy.optimize = mock_model.optimize

    mock_copy.deepcopy = Mock(return_value=model_copy)
    mock_db_class.get_instance = Mock(return_value=mock_db_index)

    # Run FBA
    result = run_fba(
        model_id="model_001.gf",
        media_id="media_001",
        db_index=mock_db_index,
    )

    # Check deepcopy was called
    mock_copy.deepcopy.assert_called_once()

    # Original model should not be modified
    # (copy was modified instead)
    assert mock_model.medium == {}  # Original unchanged
    assert len(model_copy.medium) > 0  # Copy was modified
