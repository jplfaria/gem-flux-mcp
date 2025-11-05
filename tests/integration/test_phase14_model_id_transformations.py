"""Integration tests for Model ID Transformations.

This module tests model ID state suffix transformations during gapfilling
according to specification 002-data-formats.md (Model ID Format and States).

Key transformations tested:
1. build_model creates .draft suffix
2. gapfill_model transforms .draft → .draft.gf
3. Re-gapfilling appends .gf: .draft.gf → .draft.gf.gf
4. User-provided names preserved through transformations
5. Gapfilling from .gf suffix: .gf → .gf.gf

According to spec 002-data-formats.md:
- .draft: Draft model (not gapfilled)
- .draft.gf: Draft model after gapfilling
- .gf: Gapfilled model (source was already gapfilled)
- .draft.gf.gf: Draft model gapfilled twice

Test expectations: All tests in this module should be must_pass (critical path).
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

# Import storage modules
from gem_flux_mcp.storage.models import (
    MODEL_STORAGE,
    clear_all_models,
    generate_model_id,
    generate_model_id_from_name,
    store_model,
    transform_state_suffix,
)


@pytest.fixture(autouse=True)
def setup_storage():
    """Setup and teardown storage for each test."""
    # Clear all storage before test
    clear_all_models()

    yield

    # Cleanup after test
    clear_all_models()


# ============================================================================
# Test 1: build_model creates .draft suffix
# ============================================================================


def test_build_model_creates_draft_suffix():
    """Test that build_model creates model with .draft suffix.

    According to spec 002-data-formats.md:
    - build_model creates draft models with .draft state
    - Format: model_{timestamp}_{random}.draft
    - Example: model_20251027_143052_x7k9m2.draft

    Verification:
    - Generated model_id ends with .draft
    - Model stored with .draft suffix
    - Draft state correctly applied
    """

    # Generate model_id with draft state (simulates build_model behavior)
    model_id = generate_model_id(state="draft")

    # Verify format
    assert model_id.endswith(".draft"), f"Expected .draft suffix, got: {model_id}"
    assert model_id.startswith("model_"), f"Expected model_ prefix, got: {model_id}"
    assert model_id.count(".") == 1, f"Expected single dot (before draft), got: {model_id}"

    # Create mock model (simulates build_model output)
    model = Mock()
    model.id = model_id.replace(".draft", "")  # COBRApy doesn't include suffix
    model.reactions = [Mock() for _ in range(856)]
    model.metabolites = [Mock() for _ in range(742)]
    model.notes = {
        "template_used": "GramNegative",
        "created_at": datetime.now().isoformat(),
    }

    # Store model (simulates build_model storage)
    store_model(model_id, model)

    # Verify storage
    assert model_id in MODEL_STORAGE, f"Model not stored: {model_id}"
    stored_model = MODEL_STORAGE[model_id]
    assert stored_model == model


def test_build_model_user_provided_name_has_draft_suffix():
    """Test that user-provided names get .draft suffix from build_model.

    According to spec 002-data-formats.md:
    - User can provide custom model_name parameter
    - build_model appends .draft state to custom name
    - Example: E_coli_K12 → E_coli_K12.draft

    Verification:
    - User name preserved
    - .draft suffix applied
    - No timestamp unless collision
    """

    # Generate model_id from user-provided name (simulates build_model behavior)
    user_name = "E_coli_K12"
    model_id = generate_model_id_from_name(
        model_name=user_name,
        state="draft",
        existing_ids=set(),  # No collisions
    )

    # Verify format
    assert model_id == f"{user_name}.draft", f"Expected {user_name}.draft, got: {model_id}"
    # Verify no collision timestamp was added (should be exactly the user name + .draft)
    parts = model_id.split(".")
    assert len(parts) == 2, f"Expected 2 parts (name.draft), got: {parts}"
    assert parts[0] == user_name, f"Expected user name {user_name}, got: {parts[0]}"
    assert parts[1] == "draft", f"Expected 'draft' suffix, got: {parts[1]}"

    # Create and store mock model
    model = Mock()
    model.id = user_name
    model.reactions = [Mock() for _ in range(856)]
    model.notes = {"template_used": "GramNegative"}

    store_model(model_id, model)

    # Verify storage
    assert model_id in MODEL_STORAGE


def test_build_model_collision_handling():
    """Test that build_model handles name collisions with timestamp.

    According to spec 002-data-formats.md:
    - If user name collides with existing model_id, append timestamp
    - Format: {name}_{timestamp}.{state}
    - Example: E_coli_K12_20251027_143052.draft

    Verification:
    - Original model_id unchanged
    - New model_id has timestamp
    - Both stored successfully
    """

    # Create first model with user name
    first_name = "Ecoli_strain1"
    first_model_id = generate_model_id_from_name(
        model_name=first_name, state="draft", existing_ids=set()
    )

    first_model = Mock()
    first_model.id = first_name
    store_model(first_model_id, first_model)

    # Attempt to create second model with same name (collision)
    existing_ids = {first_model_id}
    second_model_id = generate_model_id_from_name(
        model_name=first_name, state="draft", existing_ids=existing_ids
    )

    # Verify collision handling
    assert second_model_id != first_model_id, "Collision not handled"
    assert second_model_id.startswith(first_name), f"Name not preserved: {second_model_id}"
    assert second_model_id.endswith(".draft"), f"State suffix lost: {second_model_id}"
    # Should have timestamp between name and suffix
    assert len(second_model_id.split("_")) > len(first_model_id.split("_")), (
        f"Timestamp not added: {second_model_id}"
    )

    # Store second model
    second_model = Mock()
    second_model.id = first_name + "_timestamped"
    store_model(second_model_id, second_model)

    # Verify both stored
    assert first_model_id in MODEL_STORAGE
    assert second_model_id in MODEL_STORAGE


# ============================================================================
# Test 2: gapfill_model transforms .draft → .draft.gf
# ============================================================================


def test_gapfill_transforms_draft_to_draft_gf():
    """Test that gapfill_model transforms .draft → .draft.gf.

    According to spec 002-data-formats.md:
    - Input: model.draft
    - Output: model.draft.gf
    - Transformation: Replace .draft with .draft.gf
    - Original model preserved

    Verification:
    - New model_id ends with .draft.gf
    - Original model_id (.draft) still exists
    - Base name preserved
    """

    # Create draft model
    draft_model_id = "model_test_001.draft"
    draft_model = Mock()
    draft_model.id = "test_001"
    draft_model.reactions = [Mock() for _ in range(856)]
    store_model(draft_model_id, draft_model)

    # Simulate gapfilling transformation
    gf_model_id = transform_state_suffix(draft_model_id)

    # Verify transformation
    assert gf_model_id == "model_test_001.draft.gf", (
        f"Expected model_test_001.draft.gf, got: {gf_model_id}"
    )
    assert gf_model_id.endswith(".draft.gf"), f"Wrong suffix: {gf_model_id}"
    assert not gf_model_id.endswith(".draft.gf.draft"), f"Incorrect transformation: {gf_model_id}"

    # Create gapfilled model (simulates gapfill_model output)
    gf_model = Mock()
    gf_model.id = "test_001"
    gf_model.reactions = [Mock() for _ in range(860)]  # More reactions after gapfilling
    gf_model.notes = {"gapfilled": True}
    store_model(gf_model_id, gf_model)

    # Verify both models exist (original preserved)
    assert draft_model_id in MODEL_STORAGE, "Original draft model lost"
    assert gf_model_id in MODEL_STORAGE, "Gapfilled model not stored"

    # Verify models are distinct
    assert MODEL_STORAGE[draft_model_id] != MODEL_STORAGE[gf_model_id]


def test_gapfill_preserves_user_provided_name():
    """Test that gapfilling preserves user-provided model name.

    According to spec 002-data-formats.md:
    - User name preserved through gapfilling
    - Example: E_coli_K12.draft → E_coli_K12.draft.gf

    Verification:
    - Base name unchanged
    - Only suffix transformed
    """

    # Create draft model with user-provided name
    user_name = "Bacillus_subtilis_168"
    draft_model_id = f"{user_name}.draft"

    draft_model = Mock()
    draft_model.id = user_name
    store_model(draft_model_id, draft_model)

    # Transform to gapfilled state
    gf_model_id = transform_state_suffix(draft_model_id)

    # Verify user name preserved
    expected = f"{user_name}.draft.gf"
    assert gf_model_id == expected, f"Expected {expected}, got: {gf_model_id}"
    assert gf_model_id.startswith(user_name), f"User name lost: {gf_model_id}"

    # Store gapfilled model
    gf_model = Mock()
    gf_model.id = user_name
    store_model(gf_model_id, gf_model)

    # Verify both exist
    assert draft_model_id in MODEL_STORAGE
    assert gf_model_id in MODEL_STORAGE


# ============================================================================
# Test 3: Re-gapfilling appends .gf: .draft.gf → .draft.gf.gf
# ============================================================================


def test_regapfill_appends_gf_suffix():
    """Test that re-gapfilling appends .gf suffix.

    According to spec 002-data-formats.md:
    - Input: model.draft.gf
    - Output: model.draft.gf.gf
    - Transformation: Append .gf to existing suffix

    Verification:
    - New suffix is .draft.gf.gf
    - Original .draft.gf model preserved
    - Tracks full gapfilling history
    """

    # Create already-gapfilled model
    first_gf_model_id = "model_iterative.draft.gf"
    first_gf_model = Mock()
    first_gf_model.id = "iterative"
    first_gf_model.reactions = [Mock() for _ in range(860)]
    store_model(first_gf_model_id, first_gf_model)

    # Re-gapfill (append .gf)
    second_gf_model_id = transform_state_suffix(first_gf_model_id)

    # Verify transformation
    assert second_gf_model_id == "model_iterative.draft.gf.gf", (
        f"Expected .draft.gf.gf, got: {second_gf_model_id}"
    )
    assert second_gf_model_id.endswith(".gf.gf"), f"Wrong suffix: {second_gf_model_id}"
    assert second_gf_model_id.count(".gf") == 2, (
        f"Expected two .gf suffixes, got: {second_gf_model_id}"
    )

    # Store second gapfilled model
    second_gf_model = Mock()
    second_gf_model.id = "iterative"
    second_gf_model.reactions = [Mock() for _ in range(865)]  # More reactions
    store_model(second_gf_model_id, second_gf_model)

    # Verify all models exist (full history)
    assert first_gf_model_id in MODEL_STORAGE, "First gapfilled model lost"
    assert second_gf_model_id in MODEL_STORAGE, "Second gapfilled model not stored"


def test_multiple_regapfilling_iterations():
    """Test multiple gapfilling iterations preserve history.

    According to spec 002-data-formats.md:
    - Each gapfilling appends .gf
    - Example: .draft → .draft.gf → .draft.gf.gf → .draft.gf.gf.gf

    Verification:
    - Each iteration creates new model_id
    - All previous models preserved
    - Suffix count reflects iteration count
    """

    # Start with draft model
    base_name = "model_multiiter"
    current_id = f"{base_name}.draft"

    model = Mock()
    model.id = "multiiter"
    model.reactions = [Mock() for _ in range(850)]
    store_model(current_id, model)

    # Track all model IDs
    all_ids = [current_id]

    # Perform 4 gapfilling iterations
    for iteration in range(1, 5):
        # Transform suffix
        next_id = transform_state_suffix(current_id)

        # Verify suffix count
        gf_count = next_id.count(".gf")
        assert gf_count == iteration, (
            f"Iteration {iteration}: expected {iteration} .gf suffixes, got {gf_count} in {next_id}"
        )

        # Create new model
        model = Mock()
        model.id = "multiiter"
        model.reactions = [Mock() for _ in range(850 + iteration * 5)]
        store_model(next_id, model)

        all_ids.append(next_id)
        current_id = next_id

    # Verify all 5 models exist (draft + 4 gapfilled)
    assert len(all_ids) == 5
    for model_id in all_ids:
        assert model_id in MODEL_STORAGE, f"Model lost: {model_id}"

    # Verify final model ID format
    final_id = all_ids[-1]
    assert final_id == f"{base_name}.draft.gf.gf.gf.gf", (
        f"Expected {base_name}.draft.gf.gf.gf.gf, got: {final_id}"
    )


# ============================================================================
# Test 4: Gapfilling from .gf suffix: .gf → .gf.gf
# ============================================================================


def test_gapfill_gf_to_gf_gf():
    """Test gapfilling a model with .gf suffix (no .draft).

    According to spec 002-data-formats.md:
    - Input: model.gf (source was already gapfilled)
    - Output: model.gf.gf
    - Transformation: Append .gf

    Verification:
    - New suffix is .gf.gf (not .gf.draft.gf)
    - Original .gf model preserved
    """

    # Create model with .gf suffix (simulates gapfilling an already-gapfilled model)
    gf_model_id = "model_from_gf.gf"
    gf_model = Mock()
    gf_model.id = "from_gf"
    gf_model.reactions = [Mock() for _ in range(900)]
    store_model(gf_model_id, gf_model)

    # Gapfill again (append .gf)
    double_gf_model_id = transform_state_suffix(gf_model_id)

    # Verify transformation
    assert double_gf_model_id == "model_from_gf.gf.gf", (
        f"Expected .gf.gf, got: {double_gf_model_id}"
    )
    assert double_gf_model_id.endswith(".gf.gf"), f"Wrong suffix: {double_gf_model_id}"
    assert ".draft" not in double_gf_model_id, f"Should not add .draft: {double_gf_model_id}"

    # Store double-gapfilled model
    double_gf_model = Mock()
    double_gf_model.id = "from_gf"
    double_gf_model.reactions = [Mock() for _ in range(905)]
    store_model(double_gf_model_id, double_gf_model)

    # Verify both exist
    assert gf_model_id in MODEL_STORAGE
    assert double_gf_model_id in MODEL_STORAGE


# ============================================================================
# Test 5: Complete Transformation Workflow
# ============================================================================


def test_complete_transformation_workflow():
    """Test complete model ID transformation workflow.

    Complete workflow from spec 002-data-formats.md:
    1. build_model → model.draft
    2. gapfill_model → model.draft.gf
    3. gapfill_model (again) → model.draft.gf.gf

    With user-provided name:
    1. build_model(model_name="MyModel") → MyModel.draft
    2. gapfill_model(MyModel.draft) → MyModel.draft.gf
    3. gapfill_model(MyModel.draft.gf) → MyModel.draft.gf.gf

    Verification:
    - All transformations correct
    - All models preserved
    - User name maintained
    """

    # ========================================================================
    # Part 1: Auto-generated IDs
    # ========================================================================

    # Step 1: build_model creates .draft
    auto_id_draft = generate_model_id(state="draft")
    assert auto_id_draft.endswith(".draft")

    model1 = Mock()
    model1.id = "auto"
    store_model(auto_id_draft, model1)

    # Step 2: gapfill transforms to .draft.gf
    auto_id_gf1 = transform_state_suffix(auto_id_draft)
    assert auto_id_gf1.endswith(".draft.gf")

    model2 = Mock()
    model2.id = "auto"
    store_model(auto_id_gf1, model2)

    # Step 3: re-gapfill transforms to .draft.gf.gf
    auto_id_gf2 = transform_state_suffix(auto_id_gf1)
    assert auto_id_gf2.endswith(".draft.gf.gf")

    model3 = Mock()
    model3.id = "auto"
    store_model(auto_id_gf2, model3)

    # Verify all 3 auto-generated models exist
    assert auto_id_draft in MODEL_STORAGE
    assert auto_id_gf1 in MODEL_STORAGE
    assert auto_id_gf2 in MODEL_STORAGE

    # ========================================================================
    # Part 2: User-provided Names
    # ========================================================================

    # Step 1: build_model with user name creates .draft
    user_name = "Salmonella_typhimurium"
    user_id_draft = generate_model_id_from_name(
        model_name=user_name, state="draft", existing_ids=set()
    )
    assert user_id_draft == f"{user_name}.draft"

    model4 = Mock()
    model4.id = user_name
    store_model(user_id_draft, model4)

    # Step 2: gapfill transforms to .draft.gf
    user_id_gf1 = transform_state_suffix(user_id_draft)
    assert user_id_gf1 == f"{user_name}.draft.gf"
    assert user_name in user_id_gf1

    model5 = Mock()
    model5.id = user_name
    store_model(user_id_gf1, model5)

    # Step 3: re-gapfill transforms to .draft.gf.gf
    user_id_gf2 = transform_state_suffix(user_id_gf1)
    assert user_id_gf2 == f"{user_name}.draft.gf.gf"
    assert user_name in user_id_gf2

    model6 = Mock()
    model6.id = user_name
    store_model(user_id_gf2, model6)

    # Verify all 3 user-named models exist
    assert user_id_draft in MODEL_STORAGE
    assert user_id_gf1 in MODEL_STORAGE
    assert user_id_gf2 in MODEL_STORAGE

    # ========================================================================
    # Final verification: All 6 models coexist
    # ========================================================================

    assert len(MODEL_STORAGE) == 6

    # Verify auto-generated IDs are distinct from user-provided IDs
    assert auto_id_draft != user_id_draft
    assert auto_id_gf1 != user_id_gf1
    assert auto_id_gf2 != user_id_gf2


# ============================================================================
# Test 6: Edge Cases and Error Handling
# ============================================================================


def test_transform_state_suffix_edge_cases():
    """Test edge cases in state suffix transformation.

    Edge cases:
    - Model ID without suffix (should not happen, but handle gracefully)
    - Model ID with multiple dots in base name
    - Very long model IDs

    Verification:
    - Transformation logic robust
    - No crashes on edge cases
    """

    # Edge case 1: Multiple dots in base name
    model_id_dots = "model_ecoli.k12.mg1655.draft"
    transformed = transform_state_suffix(model_id_dots)
    assert transformed == "model_ecoli.k12.mg1655.draft.gf", (
        f"Dots in name broke transformation: {transformed}"
    )

    # Edge case 2: Already has multiple .gf suffixes
    model_id_multi = "model_test.draft.gf.gf.gf"
    transformed_multi = transform_state_suffix(model_id_multi)
    assert transformed_multi == "model_test.draft.gf.gf.gf.gf", (
        f"Multiple .gf broke transformation: {transformed_multi}"
    )

    # Edge case 3: Very long base name
    long_name = "a" * 200
    model_id_long = f"{long_name}.draft"
    transformed_long = transform_state_suffix(model_id_long)
    assert transformed_long == f"{long_name}.draft.gf", (
        f"Long name broke transformation: {transformed_long[:50]}..."
    )


def test_state_suffix_idempotency():
    """Test that transformation logic is deterministic.

    Verification:
    - Same input always produces same output
    - No side effects from repeated calls
    """

    model_id = "model_deterministic.draft"

    # Transform multiple times
    result1 = transform_state_suffix(model_id)
    result2 = transform_state_suffix(model_id)
    result3 = transform_state_suffix(model_id)

    # Verify all identical
    assert result1 == result2 == result3
    assert result1 == "model_deterministic.draft.gf"

    # Transform result and verify idempotency
    second_result1 = transform_state_suffix(result1)
    second_result2 = transform_state_suffix(result1)

    assert second_result1 == second_result2
    assert second_result1 == "model_deterministic.draft.gf.gf"


# ============================================================================
# Test 7: Integration with Storage Operations
# ============================================================================


def test_model_id_transformations_with_storage_lifecycle():
    """Test model ID transformations integrate correctly with storage operations.

    Complete lifecycle:
    1. Generate draft model_id
    2. Store draft model
    3. Transform to gapfilled state
    4. Store gapfilled model
    5. Verify both models coexist
    6. Delete draft model
    7. Verify gapfilled model unaffected

    Verification:
    - Storage operations work with transformed IDs
    - Original and transformed models independent
    - Deletion doesn't affect related models
    """

    # Step 1-2: Create and store draft model
    base_name = "lifecycle_test"
    draft_id = f"{base_name}.draft"

    draft_model = Mock()
    draft_model.id = base_name
    draft_model.reactions = [Mock() for _ in range(850)]
    store_model(draft_id, draft_model)

    assert draft_id in MODEL_STORAGE

    # Step 3-4: Transform and store gapfilled model
    gf_id = transform_state_suffix(draft_id)

    gf_model = Mock()
    gf_model.id = base_name
    gf_model.reactions = [Mock() for _ in range(855)]
    store_model(gf_id, gf_model)

    # Step 5: Verify coexistence
    assert draft_id in MODEL_STORAGE
    assert gf_id in MODEL_STORAGE
    assert len(MODEL_STORAGE) == 2

    # Step 6: Delete draft model
    del MODEL_STORAGE[draft_id]

    # Step 7: Verify gapfilled model unaffected
    assert draft_id not in MODEL_STORAGE
    assert gf_id in MODEL_STORAGE
    assert len(MODEL_STORAGE) == 1

    # Verify gapfilled model still accessible
    retrieved_gf = MODEL_STORAGE[gf_id]
    assert retrieved_gf == gf_model
    assert len(retrieved_gf.reactions) == 855
