# Integration Testing Best Practices for Gem-Flux MCP

This guide documents best practices for writing integration tests that interact with session storage and external libraries (ModelSEEDpy, COBRApy).

## Session Storage in Tests

Gem-Flux MCP uses in-memory session storage for models and media. When writing integration tests, proper storage management is critical for test isolation and reliability.

### ✅ DO: Clear Storage Between Tests

**Always use an autouse fixture to clear both MODEL_STORAGE and MEDIA_STORAGE:**

```python
from gem_flux_mcp.storage.models import MODEL_STORAGE
from gem_flux_mcp.storage.media import MEDIA_STORAGE

@pytest.fixture(autouse=True)
def cleanup_storage():
    """Clear storage before and after each test."""
    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()  # Clear BOTH storages
    yield
    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()
```

**Why**: Storage persists across test boundaries. Without explicit clearing, tests may:
- See leftover data from previous tests
- Have non-deterministic behavior
- Pass when run alone but fail in test suites
- Have order-dependent results

### ✅ DO: Verify Storage Operations

**Always verify that storage operations succeeded:**

```python
@pytest.fixture
def test_media():
    """Create test media with verification."""
    media = create_test_media()
    store_media("test_id", media)

    # Verify storage succeeded
    assert media_exists("test_id"), "Media storage failed in fixture"
    assert "test_id" in MEDIA_STORAGE, "Media not in MEDIA_STORAGE dict"

    yield "test_id"

    # Cleanup handled by autouse fixture
```

**Why**: Storage operations can fail silently or be affected by unknown state. Immediate verification catches issues at the source.

### ❌ DON'T: Assume Storage State

**Bad - No verification:**
```python
# ❌ Assumes storage is clean and operations succeed
store_media("test_id", media)
yield "test_id"  # May fail if storage is not clean or store failed
```

**Good - With verification:**
```python
# ✅ Verifies storage state before proceeding
store_media("test_id", media)
assert "test_id" in MEDIA_STORAGE
yield "test_id"
```

### ✅ DO: Use Module vs Function Scope Appropriately

**Module scope**: For expensive setup that can be safely shared across all tests in a module:
```python
@pytest.fixture(scope="module")
def db_index():
    """Load database once per test module."""
    compounds_df = load_compounds_database("data/database/compounds.tsv")
    reactions_df = load_reactions_database("data/database/reactions.tsv")
    return DatabaseIndex(compounds_df, reactions_df)
```

**Function scope**: For test-specific state that must be isolated:
```python
@pytest.fixture  # Default: function scope
def test_model():
    """Create fresh model for each test."""
    return build_test_model()
```

**Why**:
- Module scope: Expensive operations (loading databases, templates) run once
- Function scope: Ensures test isolation, each test gets clean state
- Mixing scopes improperly can cause state leakage

---

## Working Patterns from Existing Tests

### Pattern 1: Explicit Storage Management

**From**: `test_phase10_session_management.py`

```python
@pytest.fixture(autouse=True)
def setup_storage():
    """Setup storage before and after each test."""
    # Clear ALL storage at start
    clear_all_models()
    clear_all_media()

    # Load known state
    load_predefined_media()
    for media_name, media_data in PREDEFINED_MEDIA_CACHE.items():
        MEDIA_STORAGE[media_name] = media_data["compounds"]

    yield

    # Clear ALL storage at end
    clear_all_models()
    clear_all_media()
```

**Key Points**:
- ✅ Clears both model and media storage
- ✅ Loads known, controlled state
- ✅ Cleans up after test completes
- ✅ Ensures deterministic starting state

### Pattern 2: Direct Storage with Verification

**From**: `test_phase11_complete_workflow.py`

```python
def test_storage_operations():
    """Test with inline storage and verification."""
    # Store directly in test body
    media_id = "test_glucose"
    media_data = {
        "cpd00027_e0": (-5, 100),
        "cpd00007_e0": (-10, 100),
    }
    store_media(media_id, media_data)

    # Verify immediately
    assert media_id in MEDIA_STORAGE, "Media not stored"
    assert MEDIA_STORAGE[media_id] == media_data, "Media data mismatch"

    # Use stored media
    model_id = build_and_store_model()
    result = gapfill_model(model_id, media_id, ...)

    # Verify result
    assert result["success"]
```

**Key Points**:
- ✅ Stores media in test body (not fixture)
- ✅ Verifies storage immediately after operation
- ✅ Clear cause-and-effect relationship
- ✅ Easy to debug if something fails

### Pattern 3: Module-Level Database, Function-Level State

**From**: `test_modelseedpy_api_correctness.py`

```python
@pytest.fixture(scope="module")
def db_index():
    """Load database once for all tests."""
    compounds_df = load_compounds_database("data/database/compounds.tsv")
    reactions_df = load_reactions_database("data/database/reactions.tsv")
    return DatabaseIndex(compounds_df, reactions_df)

@pytest.fixture(scope="module")
def templates():
    """Load templates once for all tests."""
    from gem_flux_mcp.templates.loader import TEMPLATE_CACHE
    templates_dict = load_templates()
    TEMPLATE_CACHE.clear()
    TEMPLATE_CACHE.update(templates_dict)
    return templates_dict

@pytest.fixture  # Function scope - per test
def glucose_media():
    """Create fresh media for each test."""
    media = MSMedia.from_dict({...})
    media.id = "test_glucose_aerobic"
    store_media("test_glucose_aerobic", media)

    # Verify storage succeeded
    assert media_exists("test_glucose_aerobic")

    yield "test_glucose_aerobic"
```

**Key Points**:
- ✅ Expensive operations (DB, templates) run once per module
- ✅ Test-specific state (media, models) created per test
- ✅ Storage verification ensures fixture succeeded
- ✅ Proper separation of shared vs isolated state

---

## Common Pitfalls and Solutions

### Pitfall 1: Incomplete Cleanup Fixtures

❌ **Problem - Only clears models:**
```python
@pytest.fixture(autouse=True)
def cleanup():
    MODEL_STORAGE.clear()  # Only models!
    yield
    MODEL_STORAGE.clear()
```

**Issue**: Media storage contains stale data from previous tests

✅ **Solution - Clear all storage:**
```python
@pytest.fixture(autouse=True)
def cleanup():
    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()  # Clear media too
    yield
    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()
```

### Pitfall 2: No Storage Verification

❌ **Problem - Assumes success:**
```python
@pytest.fixture
def test_media():
    store_media("test_id", media)
    yield "test_id"  # Assumes it worked
```

**Issue**: If storage fails, test continues with invalid state

✅ **Solution - Verify immediately:**
```python
@pytest.fixture
def test_media():
    store_media("test_id", media)
    assert media_exists("test_id"), "Storage failed"
    yield "test_id"
```

### Pitfall 3: Module Scope for Test-Specific State

❌ **Problem - Shared mutable state:**
```python
@pytest.fixture(scope="module")  # Shared across tests!
def shared_media():
    media = create_media()
    # First test modifies media
    # Subsequent tests see modified version
    return media
```

**Issue**: Tests affect each other through shared mutable objects

✅ **Solution - Function scope for isolation:**
```python
@pytest.fixture  # Function scope - fresh per test
def test_media():
    media = create_media()
    # Each test gets its own copy
    return media
```

### Pitfall 4: No Cleanup After Test

❌ **Problem - State persists:**
```python
@pytest.fixture
def test_model():
    model_id = build_and_store_model()
    yield model_id
    # No cleanup - model stays in storage
```

**Issue**: Next test may see this model unexpectedly

✅ **Solution - Use autouse cleanup:**
```python
@pytest.fixture(autouse=True)
def cleanup():
    MODEL_STORAGE.clear()
    yield
    MODEL_STORAGE.clear()  # Clears ALL models after test

@pytest.fixture
def test_model():
    model_id = build_and_store_model()
    yield model_id
    # Cleanup handled by autouse fixture
```

---

## Testing with Real ModelSEEDpy Objects

### Prefer Real Objects Over Mocks

**For Integration Tests:**
```python
# ✅ Good - Uses real ModelSEEDpy
def test_media_creation():
    from modelseedpy.core.msmedia import MSMedia

    media = MSMedia.from_dict({
        'cpd00027_e0': (-5, 100),
        'cpd00007_e0': (-10, 100),
    })

    assert media is not None
    constraints = media.get_media_constraints(cmp="e0")
    assert 'cpd00027_e0' in constraints
```

**For Unit Tests:**
```python
# ✅ Good - Uses mocks for isolated testing
def test_storage_function(mock_media):
    store_media("test_id", mock_media)
    assert media_exists("test_id")
```

**Why**:
- Integration tests verify library behavior
- Real objects catch API changes
- Mocks are useful for unit tests only

### Verify API Signatures

**Test actual API compatibility:**
```python
def test_msgapfill_api():
    """Verify MSGapfill uses correct parameters."""
    from modelseedpy.core.msgapfill import MSGapfill

    # This will raise TypeError if API is wrong
    gapfiller = MSGapfill(
        model_or_mdlutl=model,  # Correct parameter
        test_conditions=[...],   # Correct parameter
    )

    result = gapfiller.run_gapfilling(
        media=media,
        minimum_obj=0.01,  # Correct parameter (not target=)
    )

    assert result is not None
```

---

## Debugging Storage Issues

### Check Storage State

```python
def print_storage_state():
    """Debug helper to check storage state."""
    print(f"Models in storage: {list(MODEL_STORAGE.keys())}")
    print(f"Media in storage: {list(MEDIA_STORAGE.keys())}")
```

### Verify Storage Identity

```python
def test_storage_identity():
    """Verify all imports reference same storage."""
    from gem_flux_mcp.storage.media import MEDIA_STORAGE as MEDIA1
    from gem_flux_mcp.tools.gapfill_model import MEDIA_STORAGE as MEDIA2

    # Should be the same object
    assert id(MEDIA1) == id(MEDIA2), "Different MEDIA_STORAGE instances!"
```

### Add Assertions in Fixtures

```python
@pytest.fixture
def glucose_media():
    """Create media with verbose verification."""
    media = MSMedia.from_dict({...})
    media.id = "test_glucose"

    print(f"[FIXTURE] Before store: {list(MEDIA_STORAGE.keys())}")
    store_media("test_glucose", media)
    print(f"[FIXTURE] After store: {list(MEDIA_STORAGE.keys())}")

    assert "test_glucose" in MEDIA_STORAGE, (
        f"Media storage failed. Storage contents: {list(MEDIA_STORAGE.keys())}"
    )

    yield "test_glucose"
```

---

## Quick Reference

### Checklist for New Integration Tests

- [ ] Autouse fixture clears both MODEL_STORAGE and MEDIA_STORAGE
- [ ] Module-scoped fixtures for expensive setup (DB, templates)
- [ ] Function-scoped fixtures for test-specific state (models, media)
- [ ] Storage operations verified with assertions
- [ ] Uses real ModelSEEDpy/COBRApy objects (not mocks)
- [ ] No assumptions about storage state
- [ ] Clear error messages in assertions
- [ ] Cleanup handled by autouse fixture

### Template for New Integration Test Module

```python
"""Integration tests for [feature name].

Brief description of what these tests verify.
"""

import pytest
from gem_flux_mcp.storage.models import MODEL_STORAGE
from gem_flux_mcp.storage.media import MEDIA_STORAGE

# Module-scoped expensive setup
@pytest.fixture(scope="module")
def db_index():
    """Load database once for all tests."""
    # Load databases, return index
    pass

# Autouse cleanup for every test
@pytest.fixture(autouse=True)
def cleanup_storage():
    """Clear storage before and after each test."""
    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()
    yield
    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()

# Function-scoped test-specific fixtures
@pytest.fixture
def test_media():
    """Create test media with verification."""
    media = create_media()
    media_id = "test_media"
    store_media(media_id, media)
    assert media_exists(media_id)
    yield media_id

# Tests
class TestFeature:
    """Test [feature] functionality."""

    def test_something(self, db_index, test_media):
        """Test [specific behavior]."""
        # Test implementation
        pass
```

---

## Related Documentation

- **specs/010-model-storage.md**: Storage specification with testing section
- **tests/integration/test_modelseedpy_api_correctness.py**: Example of best practices
- **tests/integration/test_phase10_session_management.py**: Storage management patterns

---

**Last Updated**: 2025-10-29
**Status**: ✅ Ready for use
