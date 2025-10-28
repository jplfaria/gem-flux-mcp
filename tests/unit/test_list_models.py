"""Unit tests for list_models tool.

Tests the list_models MCP tool according to specification
018-session-management-tools.md.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from gem_flux_mcp.tools.list_models import (
    list_models,
    classify_model_state,
    extract_model_name,
    extract_model_metadata,
)
from gem_flux_mcp.types import ListModelsRequest
from gem_flux_mcp.storage.models import MODEL_STORAGE, clear_all_models


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear model storage before and after each test."""
    clear_all_models()
    yield
    clear_all_models()


def create_mock_model(
    num_reactions=856,
    num_metabolites=742,
    num_genes=150,
    template="GramNegative",
    created_at=None,
    derived_from=None,
):
    """Create a mock COBRApy Model object."""
    model = MagicMock()
    model.reactions = [None] * num_reactions
    model.metabolites = [None] * num_metabolites
    model.genes = [None] * num_genes
    model.notes = {
        "template_used": template,
        "created_at": created_at or datetime.utcnow().isoformat() + "Z",
        "derived_from": derived_from,
    }
    return model


# =============================================================================
# Test classify_model_state
# =============================================================================


def test_classify_model_state_draft():
    """Test classification of draft models."""
    assert classify_model_state("model_abc.draft") == "draft"


def test_classify_model_state_gapfilled():
    """Test classification of gapfilled models."""
    assert classify_model_state("model_abc.gf") == "gapfilled"
    assert classify_model_state("model_abc.draft.gf") == "gapfilled"
    assert classify_model_state("model_abc.draft.gf.gf") == "gapfilled"


def test_classify_model_state_no_suffix():
    """Test classification of model without clear suffix."""
    # Fallback to draft
    assert classify_model_state("model_abc") == "draft"


# =============================================================================
# Test extract_model_name
# =============================================================================


def test_extract_model_name_auto_generated():
    """Test extraction of model name from auto-generated ID."""
    assert extract_model_name("model_20251027_143052_abc123.draft") is None


def test_extract_model_name_user_provided():
    """Test extraction of model name from user-provided ID."""
    assert extract_model_name("E_coli_K12.draft") == "E_coli_K12"
    assert extract_model_name("B_subtilis_168.draft.gf") == "B_subtilis_168"


# =============================================================================
# Test extract_model_metadata
# =============================================================================


def test_extract_model_metadata_draft():
    """Test metadata extraction for draft model."""
    model = create_mock_model(
        num_reactions=856,
        num_metabolites=742,
        num_genes=150,
        template="GramNegative",
        created_at="2025-10-27T14:30:52Z",
        derived_from=None,
    )

    metadata = extract_model_metadata("model_abc.draft", model)

    assert metadata.model_id == "model_abc.draft"
    assert metadata.model_name is None
    assert metadata.state == "draft"
    assert metadata.num_reactions == 856
    assert metadata.num_metabolites == 742
    assert metadata.num_genes == 150
    assert metadata.template_used == "GramNegative"
    assert metadata.created_at == "2025-10-27T14:30:52Z"
    assert metadata.derived_from is None


def test_extract_model_metadata_gapfilled():
    """Test metadata extraction for gapfilled model."""
    model = create_mock_model(
        num_reactions=892,
        num_metabolites=768,
        num_genes=150,
        template="GramNegative",
        created_at="2025-10-27T14:35:18Z",
        derived_from="model_abc.draft",
    )

    metadata = extract_model_metadata("model_abc.draft.gf", model)

    assert metadata.model_id == "model_abc.draft.gf"
    assert metadata.state == "gapfilled"
    assert metadata.num_reactions == 892
    assert metadata.derived_from == "model_abc.draft"


def test_extract_model_metadata_user_named():
    """Test metadata extraction for user-named model."""
    model = create_mock_model()

    metadata = extract_model_metadata("E_coli_K12.draft", model)

    assert metadata.model_name == "E_coli_K12"


# =============================================================================
# Test list_models
# =============================================================================


def test_list_models_empty_storage():
    """Test listing models when storage is empty."""
    request = ListModelsRequest(filter_state="all")
    response = list_models(request)

    assert response["success"] is True
    assert response["total_models"] == 0
    assert len(response["models"]) == 0
    assert response["models_by_state"]["draft"] == 0
    assert response["models_by_state"]["gapfilled"] == 0


def test_list_models_all_filter():
    """Test listing all models without filtering."""
    # Add draft model
    draft_model = create_mock_model(created_at="2025-10-27T14:30:00Z")
    MODEL_STORAGE["model_abc.draft"] = draft_model

    # Add gapfilled model
    gf_model = create_mock_model(
        num_reactions=892, created_at="2025-10-27T14:35:00Z"
    )
    MODEL_STORAGE["model_abc.draft.gf"] = gf_model

    request = ListModelsRequest(filter_state="all")
    response = list_models(request)

    assert response["success"] is True
    assert response["total_models"] == 2
    assert len(response["models"]) == 2
    assert response["models_by_state"]["draft"] == 1
    assert response["models_by_state"]["gapfilled"] == 1


def test_list_models_draft_filter():
    """Test filtering to show only draft models."""
    # Add draft model
    draft_model = create_mock_model()
    MODEL_STORAGE["model_abc.draft"] = draft_model

    # Add gapfilled model
    gf_model = create_mock_model(num_reactions=892)
    MODEL_STORAGE["model_abc.draft.gf"] = gf_model

    request = ListModelsRequest(filter_state="draft")
    response = list_models(request)

    assert response["success"] is True
    assert response["total_models"] == 1
    assert len(response["models"]) == 1
    assert response["models"][0]["state"] == "draft"


def test_list_models_gapfilled_filter():
    """Test filtering to show only gapfilled models."""
    # Add draft model
    draft_model = create_mock_model()
    MODEL_STORAGE["model_abc.draft"] = draft_model

    # Add gapfilled model
    gf_model = create_mock_model(num_reactions=892)
    MODEL_STORAGE["model_abc.draft.gf"] = gf_model

    request = ListModelsRequest(filter_state="gapfilled")
    response = list_models(request)

    assert response["success"] is True
    assert response["total_models"] == 1
    assert len(response["models"]) == 1
    assert response["models"][0]["state"] == "gapfilled"


def test_list_models_sorted_by_created_at():
    """Test that models are sorted by creation timestamp (oldest first)."""
    # Add models in non-chronological order
    model2 = create_mock_model(created_at="2025-10-27T14:35:00Z")
    MODEL_STORAGE["model_2.draft"] = model2

    model1 = create_mock_model(created_at="2025-10-27T14:30:00Z")
    MODEL_STORAGE["model_1.draft"] = model1

    model3 = create_mock_model(created_at="2025-10-27T14:40:00Z")
    MODEL_STORAGE["model_3.draft"] = model3

    request = ListModelsRequest(filter_state="all")
    response = list_models(request)

    assert response["total_models"] == 3
    # Check sorted order (oldest first)
    assert response["models"][0]["model_id"] == "model_1.draft"
    assert response["models"][1]["model_id"] == "model_2.draft"
    assert response["models"][2]["model_id"] == "model_3.draft"


def test_list_models_invalid_filter():
    """Test error when filter_state is invalid."""
    request = ListModelsRequest(filter_state="all")
    # Manually override to test validation
    request.filter_state = "invalid"

    response = list_models(request)

    assert response["success"] is False
    assert "invalid" in response["message"].lower()


def test_list_models_multiple_states():
    """Test listing models with various state transitions."""
    # Draft model
    draft = create_mock_model(created_at="2025-10-27T14:30:00Z")
    MODEL_STORAGE["model_abc.draft"] = draft

    # First gapfill
    gf1 = create_mock_model(
        num_reactions=892, created_at="2025-10-27T14:35:00Z"
    )
    MODEL_STORAGE["model_abc.draft.gf"] = gf1

    # Second gapfill
    gf2 = create_mock_model(
        num_reactions=920, created_at="2025-10-27T14:40:00Z"
    )
    MODEL_STORAGE["model_abc.draft.gf.gf"] = gf2

    request = ListModelsRequest(filter_state="all")
    response = list_models(request)

    assert response["total_models"] == 3
    assert response["models_by_state"]["draft"] == 1
    assert response["models_by_state"]["gapfilled"] == 2


def test_list_models_user_named():
    """Test listing user-named models."""
    model = create_mock_model()
    MODEL_STORAGE["E_coli_K12.draft"] = model

    request = ListModelsRequest(filter_state="all")
    response = list_models(request)

    assert response["total_models"] == 1
    assert response["models"][0]["model_name"] == "E_coli_K12"


def test_list_models_mixed_naming():
    """Test listing mix of auto-generated and user-named models."""
    # Auto-generated
    auto = create_mock_model(created_at="2025-10-27T14:30:00Z")
    MODEL_STORAGE["model_20251027_143052_abc123.draft"] = auto

    # User-named
    user = create_mock_model(created_at="2025-10-27T14:35:00Z")
    MODEL_STORAGE["E_coli_K12.draft"] = user

    request = ListModelsRequest(filter_state="all")
    response = list_models(request)

    assert response["total_models"] == 2
    assert response["models"][0]["model_name"] is None  # Auto-generated
    assert response["models"][1]["model_name"] == "E_coli_K12"  # User-named


def test_list_models_derived_from():
    """Test listing models with derivation tracking."""
    # Draft model
    draft = create_mock_model(created_at="2025-10-27T14:30:00Z")
    MODEL_STORAGE["model_abc.draft"] = draft

    # Derived gapfilled model
    gf = create_mock_model(
        num_reactions=892,
        created_at="2025-10-27T14:35:00Z",
        derived_from="model_abc.draft",
    )
    MODEL_STORAGE["model_abc.draft.gf"] = gf

    request = ListModelsRequest(filter_state="all")
    response = list_models(request)

    assert response["total_models"] == 2
    assert response["models"][0]["derived_from"] is None
    assert response["models"][1]["derived_from"] == "model_abc.draft"


def test_list_models_case_insensitive_filter():
    """Test that filter_state is case-insensitive."""
    model = create_mock_model()
    MODEL_STORAGE["model_abc.draft"] = model

    # Test uppercase
    request = ListModelsRequest(filter_state="all")
    request.filter_state = "ALL"
    response = list_models(request)
    assert response["success"] is True

    # Test mixed case
    request.filter_state = "DrAfT"
    response = list_models(request)
    assert response["success"] is True
