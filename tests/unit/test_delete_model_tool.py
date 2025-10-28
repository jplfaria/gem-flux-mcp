"""Unit tests for delete_model tool.

Tests the delete_model MCP tool according to specification
018-session-management-tools.md.
"""

import pytest
from unittest.mock import MagicMock

from gem_flux_mcp.tools.delete_model import delete_model
from gem_flux_mcp.types import DeleteModelRequest
from gem_flux_mcp.storage.models import MODEL_STORAGE, clear_all_models, store_model


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear model storage before and after each test."""
    clear_all_models()
    yield
    clear_all_models()


def create_mock_model():
    """Create a mock COBRApy Model object."""
    model = MagicMock()
    model.reactions = [None] * 856
    model.metabolites = [None] * 742
    model.genes = [None] * 150
    return model


# =============================================================================
# Test delete_model
# =============================================================================


def test_delete_model_success():
    """Test successful deletion of a model."""
    # Add model to storage
    model = create_mock_model()
    store_model("model_abc.draft", model)

    assert "model_abc.draft" in MODEL_STORAGE

    # Delete model
    request = DeleteModelRequest(model_id="model_abc.draft")
    response = delete_model(request)

    assert response.success is True
    assert response.deleted_model_id == "model_abc.draft"
    assert response.message == "Model deleted successfully"
    assert "model_abc.draft" not in MODEL_STORAGE


def test_delete_model_not_found():
    """Test deletion of non-existent model returns error."""
    request = DeleteModelRequest(model_id="nonexistent_model.draft")
    response = delete_model(request)

    assert response.success is False
    assert "not found" in response.message.lower()
    assert response.details is not None


def test_delete_model_empty_id():
    """Test deletion with empty model_id returns error."""
    request = DeleteModelRequest(model_id="")
    response = delete_model(request)

    assert response.success is False
    assert "missing" in response.message.lower() or "required" in response.message.lower()


def test_delete_model_whitespace_id():
    """Test deletion with whitespace-only model_id returns error."""
    request = DeleteModelRequest(model_id="   ")
    response = delete_model(request)

    assert response.success is False


def test_delete_model_multiple_models():
    """Test deleting one model while others remain."""
    # Add multiple models
    model1 = create_mock_model()
    model2 = create_mock_model()
    model3 = create_mock_model()

    store_model("model_1.draft", model1)
    store_model("model_2.draft", model2)
    store_model("model_3.draft", model3)

    # Delete model 2
    request = DeleteModelRequest(model_id="model_2.draft")
    response = delete_model(request)

    assert response.success is True
    assert "model_1.draft" in MODEL_STORAGE
    assert "model_2.draft" not in MODEL_STORAGE
    assert "model_3.draft" in MODEL_STORAGE


def test_delete_model_gapfilled():
    """Test deleting a gapfilled model."""
    model = create_mock_model()
    store_model("model_abc.draft.gf", model)

    request = DeleteModelRequest(model_id="model_abc.draft.gf")
    response = delete_model(request)

    assert response.success is True
    assert response.deleted_model_id == "model_abc.draft.gf"
    assert "model_abc.draft.gf" not in MODEL_STORAGE


def test_delete_model_user_named():
    """Test deleting a user-named model."""
    model = create_mock_model()
    store_model("E_coli_K12.draft", model)

    request = DeleteModelRequest(model_id="E_coli_K12.draft")
    response = delete_model(request)

    assert response.success is True
    assert response.deleted_model_id == "E_coli_K12.draft"


def test_delete_model_preserves_original():
    """Test that deleting derived model doesn't affect original."""
    # Add draft and gapfilled models
    draft = create_mock_model()
    gf = create_mock_model()

    store_model("model_abc.draft", draft)
    store_model("model_abc.draft.gf", gf)

    # Delete gapfilled model
    request = DeleteModelRequest(model_id="model_abc.draft.gf")
    response = delete_model(request)

    assert response.success is True
    assert "model_abc.draft" in MODEL_STORAGE  # Original preserved
    assert "model_abc.draft.gf" not in MODEL_STORAGE


def test_delete_model_available_models_in_error():
    """Test that error response includes list of available models."""
    # Add some models
    model1 = create_mock_model()
    model2 = create_mock_model()

    store_model("model_1.draft", model1)
    store_model("model_2.draft", model2)

    # Try to delete non-existent model
    request = DeleteModelRequest(model_id="model_nonexistent.draft")
    response = delete_model(request)

    assert response.success is False
    assert response.details is not None
    # Check that available models are listed (details is an ErrorDetails object with attributes)
    assert hasattr(response.details, "available_models") or "available" in response.message.lower()


def test_delete_model_case_sensitive():
    """Test that model_id deletion is case-sensitive."""
    model = create_mock_model()
    store_model("model_abc.draft", model)

    # Try to delete with different case
    request = DeleteModelRequest(model_id="MODEL_ABC.DRAFT")
    response = delete_model(request)

    # Should fail because model_id is case-sensitive
    assert response.success is False
    assert "model_abc.draft" in MODEL_STORAGE  # Original still there


def test_delete_model_twice():
    """Test that deleting the same model twice fails the second time."""
    model = create_mock_model()
    store_model("model_abc.draft", model)

    # First deletion
    request = DeleteModelRequest(model_id="model_abc.draft")
    response1 = delete_model(request)
    assert response1.success is True

    # Second deletion (should fail)
    response2 = delete_model(request)
    assert response2.success is False
