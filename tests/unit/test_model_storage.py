"""
Unit tests for model storage module.

Tests storage, retrieval, ID generation, and state transformations
according to specification 010-model-storage.md.
"""

import time
import pytest
from unittest.mock import MagicMock

from gem_flux_mcp.storage.models import (
    generate_model_id,
    generate_model_id_from_name,
    transform_state_suffix,
    store_model,
    retrieve_model,
    model_exists,
    list_model_ids,
    delete_model,
    clear_all_models,
    get_model_count,
    MODEL_STORAGE,
)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear model storage before and after each test."""
    MODEL_STORAGE.clear()
    yield
    MODEL_STORAGE.clear()


# ============================================================================
# Model ID Generation Tests
# ============================================================================


def test_generate_model_id_default_state():
    """Test generating model ID with default state (draft)."""
    model_id = generate_model_id()

    assert model_id.startswith("model_")
    assert model_id.endswith(".draft")

    # Format: model_YYYYMMDD_HHMMSS_random.draft
    parts = model_id.split("_")
    assert len(parts) >= 3  # model, date, time, random

    # Check random suffix (6 chars)
    random_part = parts[-1].split(".")[0]
    assert len(random_part) == 6
    assert random_part.isalnum()


def test_generate_model_id_custom_state():
    """Test generating model ID with custom state suffix."""
    model_id = generate_model_id(state="gf")
    assert model_id.endswith(".gf")

    model_id = generate_model_id(state="draft.gf")
    assert model_id.endswith(".draft.gf")


def test_generate_model_id_empty_state_raises():
    """Test that empty state raises ValueError."""
    with pytest.raises(ValueError, match="State parameter cannot be empty"):
        generate_model_id(state="")

    with pytest.raises(ValueError, match="State parameter cannot be empty"):
        generate_model_id(state=None)


def test_generate_model_id_uniqueness():
    """Test that generated IDs are unique."""
    ids = [generate_model_id() for _ in range(100)]
    assert len(ids) == len(set(ids))  # All unique


# ============================================================================
# User-Provided Model ID Tests
# ============================================================================


def test_generate_model_id_from_name_no_collision():
    """Test generating model ID from user name without collision."""
    model_id = generate_model_id_from_name("E_coli_K12", state="draft")
    assert model_id == "E_coli_K12.draft"


def test_generate_model_id_from_name_with_collision():
    """Test collision handling with timestamp appended."""
    existing_ids = {"E_coli_K12.draft"}

    model_id = generate_model_id_from_name(
        "E_coli_K12",
        state="draft",
        existing_ids=existing_ids,
    )

    # Should append timestamp to avoid collision
    assert model_id.startswith("E_coli_K12_")
    assert model_id.endswith(".draft")
    assert model_id != "E_coli_K12.draft"


def test_generate_model_id_from_name_empty_name_raises():
    """Test that empty model_name raises ValueError."""
    with pytest.raises(ValueError, match="model_name cannot be empty"):
        generate_model_id_from_name("", state="draft")


def test_generate_model_id_from_name_empty_state_raises():
    """Test that empty state raises ValueError."""
    with pytest.raises(ValueError, match="State parameter cannot be empty"):
        generate_model_id_from_name("E_coli", state="")


def test_generate_model_id_from_name_uses_storage_if_no_existing_ids():
    """Test that function uses MODEL_STORAGE if existing_ids not provided."""
    # Add model to storage
    MODEL_STORAGE["E_coli_K12.draft"] = MagicMock()

    # Should detect collision and append timestamp
    model_id = generate_model_id_from_name("E_coli_K12", state="draft")

    assert model_id.startswith("E_coli_K12_")
    assert model_id.endswith(".draft")


def test_generate_model_id_from_name_multiple_collisions():
    """Test that function can resolve multiple collisions."""
    existing_ids = {
        "E_coli_K12.draft",
        "E_coli_K12_20251027_143052_000001.draft",
        "E_coli_K12_20251027_143052_000002.draft",
    }

    model_id = generate_model_id_from_name(
        "E_coli_K12",
        state="draft",
        existing_ids=existing_ids,
        max_retries=10,
    )

    # Should find a unique ID
    assert model_id not in existing_ids
    assert model_id.startswith("E_coli_K12_")
    assert model_id.endswith(".draft")


# ============================================================================
# State Suffix Transformation Tests
# ============================================================================


def test_transform_state_suffix_draft_to_draft_gf():
    """Test transforming .draft to .draft.gf."""
    model_id = transform_state_suffix("model_20251027_abc123.draft")
    assert model_id == "model_20251027_abc123.draft.gf"


def test_transform_state_suffix_gf_to_gf_gf():
    """Test transforming .gf to .gf.gf."""
    model_id = transform_state_suffix("model_20251027_abc123.gf")
    assert model_id == "model_20251027_abc123.gf.gf"


def test_transform_state_suffix_draft_gf_to_draft_gf_gf():
    """Test transforming .draft.gf to .draft.gf.gf."""
    model_id = transform_state_suffix("model_20251027_abc123.draft.gf")
    assert model_id == "model_20251027_abc123.draft.gf.gf"


def test_transform_state_suffix_preserves_base_name():
    """Test that base name is preserved during transformation."""
    model_id = transform_state_suffix("E_coli_K12.draft")
    assert model_id == "E_coli_K12.draft.gf"

    model_id = transform_state_suffix("my_custom_model_123.gf")
    assert model_id == "my_custom_model_123.gf.gf"


def test_transform_state_suffix_empty_raises():
    """Test that empty model_id raises ValueError."""
    with pytest.raises(ValueError, match="model_id cannot be empty"):
        transform_state_suffix("")


def test_transform_state_suffix_no_dot_raises():
    """Test that model_id without state suffix raises ValueError."""
    with pytest.raises(ValueError, match="Invalid model ID format.*no state suffix"):
        transform_state_suffix("model_20251027_abc123")


def test_transform_state_suffix_user_provided_names():
    """Test transformation with user-provided names."""
    assert transform_state_suffix("E_coli_K12.draft") == "E_coli_K12.draft.gf"
    assert transform_state_suffix("B_subtilis_168.gf") == "B_subtilis_168.gf.gf"


# ============================================================================
# Store and Retrieve Tests
# ============================================================================


def test_store_and_retrieve_model():
    """Test storing and retrieving a model."""
    mock_model = MagicMock()
    mock_model.id = "test_model"

    store_model("model_abc.draft", mock_model)

    retrieved = retrieve_model("model_abc.draft")
    assert retrieved is mock_model


def test_store_model_empty_id_raises():
    """Test that empty model_id raises ValueError."""
    with pytest.raises(ValueError, match="model_id cannot be empty"):
        store_model("", MagicMock())


def test_store_model_none_model_raises():
    """Test that None model raises ValueError."""
    with pytest.raises(ValueError, match="model cannot be None"):
        store_model("model_abc.draft", None)


def test_store_model_collision_raises():
    """Test that storing duplicate model_id raises RuntimeError."""
    mock_model = MagicMock()

    store_model("model_abc.draft", mock_model)

    # Try to store with same ID
    with pytest.raises(RuntimeError, match="Failed to generate unique ID"):
        store_model("model_abc.draft", MagicMock())


def test_retrieve_model_not_found_raises():
    """Test that retrieving non-existent model raises KeyError."""
    with pytest.raises(KeyError, match="not found"):
        retrieve_model("model_nonexistent.draft")


def test_retrieve_model_empty_id_raises():
    """Test that empty model_id raises ValueError."""
    with pytest.raises(ValueError, match="model_id cannot be empty"):
        retrieve_model("")


# ============================================================================
# Model Existence Tests
# ============================================================================


def test_model_exists_true():
    """Test model_exists returns True for existing model."""
    mock_model = MagicMock()
    store_model("model_abc.draft", mock_model)

    assert model_exists("model_abc.draft") is True


def test_model_exists_false():
    """Test model_exists returns False for non-existent model."""
    assert model_exists("model_nonexistent.draft") is False


# ============================================================================
# List Model IDs Tests
# ============================================================================


def test_list_model_ids_empty():
    """Test listing model IDs when storage is empty."""
    ids = list_model_ids()
    assert ids == []


def test_list_model_ids_multiple():
    """Test listing multiple model IDs."""
    store_model("model_001.draft", MagicMock())
    store_model("model_002.gf", MagicMock())
    store_model("model_003.draft.gf", MagicMock())

    ids = list_model_ids()
    assert len(ids) == 3
    assert "model_001.draft" in ids
    assert "model_002.gf" in ids
    assert "model_003.draft.gf" in ids


def test_list_model_ids_sorted():
    """Test that model IDs are sorted alphabetically."""
    store_model("model_zzz.draft", MagicMock())
    store_model("model_aaa.gf", MagicMock())
    store_model("model_mmm.draft.gf", MagicMock())

    ids = list_model_ids()
    assert ids == ["model_aaa.gf", "model_mmm.draft.gf", "model_zzz.draft"]


# ============================================================================
# Delete Model Tests
# ============================================================================


def test_delete_model_success():
    """Test successfully deleting a model."""
    mock_model = MagicMock()
    store_model("model_abc.draft", mock_model)

    assert model_exists("model_abc.draft") is True

    delete_model("model_abc.draft")

    assert model_exists("model_abc.draft") is False


def test_delete_model_not_found_raises():
    """Test that deleting non-existent model raises KeyError."""
    with pytest.raises(KeyError, match="not found"):
        delete_model("model_nonexistent.draft")


def test_delete_model_empty_id_raises():
    """Test that empty model_id raises ValueError."""
    with pytest.raises(ValueError, match="model_id cannot be empty"):
        delete_model("")


# ============================================================================
# Clear All Models Tests
# ============================================================================


def test_clear_all_models_empty():
    """Test clearing when storage is empty."""
    count = clear_all_models()
    assert count == 0


def test_clear_all_models_multiple():
    """Test clearing multiple models."""
    store_model("model_001.draft", MagicMock())
    store_model("model_002.gf", MagicMock())
    store_model("model_003.draft.gf", MagicMock())

    count = clear_all_models()
    assert count == 3
    assert get_model_count() == 0


# ============================================================================
# Get Model Count Tests
# ============================================================================


def test_get_model_count_empty():
    """Test getting count when storage is empty."""
    assert get_model_count() == 0


def test_get_model_count_multiple():
    """Test getting count with multiple models."""
    store_model("model_001.draft", MagicMock())
    store_model("model_002.gf", MagicMock())
    store_model("model_003.draft.gf", MagicMock())

    assert get_model_count() == 3


# ============================================================================
# Integration Tests
# ============================================================================


def test_complete_workflow():
    """Test complete model storage workflow."""
    # Generate auto ID
    model_id = generate_model_id(state="draft")
    assert model_id.endswith(".draft")

    # Store model
    mock_model = MagicMock()
    store_model(model_id, mock_model)
    assert model_exists(model_id)

    # Transform state suffix (gapfilling)
    gf_model_id = transform_state_suffix(model_id)
    assert gf_model_id.endswith(".draft.gf")

    # Store gapfilled model
    gf_mock_model = MagicMock()
    store_model(gf_model_id, gf_mock_model)

    # List both models
    ids = list_model_ids()
    assert len(ids) == 2
    assert model_id in ids
    assert gf_model_id in ids

    # Delete draft model
    delete_model(model_id)
    assert model_exists(model_id) is False
    assert model_exists(gf_model_id) is True

    # Clear all
    count = clear_all_models()
    assert count == 1
    assert get_model_count() == 0


def test_user_provided_name_workflow():
    """Test workflow with user-provided model names."""
    # Generate ID from user name
    model_id = generate_model_id_from_name("E_coli_K12", state="draft")
    assert model_id == "E_coli_K12.draft"

    # Store model
    store_model(model_id, MagicMock())

    # Try to create another model with same name (collision)
    model_id_2 = generate_model_id_from_name("E_coli_K12", state="draft")
    assert model_id_2 != "E_coli_K12.draft"
    assert model_id_2.startswith("E_coli_K12_")

    # Store second model
    store_model(model_id_2, MagicMock())

    # Both should exist
    assert model_exists(model_id)
    assert model_exists(model_id_2)


def test_state_transformation_chain():
    """Test chaining multiple state transformations."""
    # Start with draft
    model_id = "model_abc.draft"

    # First gapfilling: .draft → .draft.gf
    model_id = transform_state_suffix(model_id)
    assert model_id == "model_abc.draft.gf"

    # Second gapfilling: .draft.gf → .draft.gf.gf
    model_id = transform_state_suffix(model_id)
    assert model_id == "model_abc.draft.gf.gf"

    # Third gapfilling: .draft.gf.gf → .draft.gf.gf.gf
    model_id = transform_state_suffix(model_id)
    assert model_id == "model_abc.draft.gf.gf.gf"
