# Testing Guidelines for Gem-Flux MCP Server

This document establishes testing best practices for the Gem-Flux MCP Server project, based on patterns that emerged during implementation.

## Flaky Logging Tests - Lesson Learned

### ❌ DON'T: Test Logging Output with caplog

**Problem**: Tests that assert on log messages using pytest's `caplog` fixture are **flaky** and fail intermittently.

```python
# ❌ FLAKY - DO NOT USE THIS PATTERN
def test_something(caplog):
    """Test that warns about missing data."""
    do_something()
    assert "warning message" in caplog.text  # ❌ Fails intermittently
```

**Why This Fails**:
- pytest's `caplog` doesn't reliably capture logs when running the full test suite
- Works when running individual tests but fails in CI/full suite
- Creates false negatives that block implementation progress
- Occurred in iterations 2, 4, 5, and 10 during development

### ✅ DO: Test Functional Behavior

**Solution**: Test the **observable behavior** of the system, not the logging side effects.

```python
# ✅ STABLE - USE THIS PATTERN
def test_something():
    """Test that handles missing data gracefully."""
    result = do_something()

    # Test functional behavior
    assert result.status == "success"
    assert len(result.data) == expected_count
    assert invalid_item not in result.data
```

## Testing Patterns by Scenario

### Pattern 1: Error Handling with Graceful Degradation

When testing functions that catch errors and continue operation:

```python
# ✅ Test that the system degrades gracefully
def test_load_media_file_not_found(clear_cache):
    """Test handling of FileNotFoundError during loading."""
    with patch('module.load_function') as mock_load:
        mock_load.side_effect = FileNotFoundError("File not found")

        result = load_media()

    # Test functional behavior
    assert result == []  # Returns empty, doesn't crash
    assert len(CACHE) == 0  # Cache not corrupted
    assert has_media() is False  # System knows there's no media
```

### Pattern 2: Warnings About Missing/Invalid Data

When testing functions that warn about missing exchange reactions, compounds, etc:

```python
# ✅ Test that invalid data is handled correctly
def test_apply_media_missing_exchange(mock_model, mock_media):
    """Test that missing exchange reactions are skipped gracefully."""
    mock_media["bounds"]["cpd99999"] = (-5, 100)  # Invalid compound

    apply_media_to_model(mock_model, mock_media)

    # Test functional behavior
    assert mock_model.medium is not None
    assert "EX_cpd99999_e0" not in mock_model.medium  # Invalid skipped
    assert "EX_cpd00027_e0" in mock_model.medium  # Valid applied
```

### Pattern 3: Success Cases with State Changes

When testing functions that log success and update state:

```python
# ✅ Test that state is correctly updated
def test_load_media_success(clear_cache, mock_media_data):
    """Test successful media loading populates cache."""
    with patch('module.load_function') as mock_load:
        mock_load.return_value = mock_media_data

        result = load_media()

    # Test functional behavior
    assert len(CACHE) == 3  # Cache populated
    assert CACHE == mock_media_data  # Correct data
    assert result == mock_media_data  # Correct return
```

### Pattern 4: Integration Tests with Multiple Steps

When testing complete workflows:

```python
# ✅ Test the complete behavior chain
def test_full_workflow(clear_cache, mock_data):
    """Test complete workflow: load, check, retrieve."""
    # Initial state
    assert has_media() is False
    assert get_media() == []

    # Load
    with patch('module.load_function') as mock_load:
        mock_load.return_value = mock_data
        load_media()

    # Verify all state transitions
    assert has_media() is True
    assert len(get_media()) == 3
    assert get_media_info()[0]["id"] == "expected_id"
```

## When Logging Tests ARE Appropriate

There are specific cases where logging tests are valuable, but they should be **integration tests**, not unit tests:

### ✅ Acceptable: Dedicated Logging Integration Tests

```python
# tests/integration/test_logging_integration.py

def test_logging_configuration():
    """Integration test verifying logging is configured correctly."""
    # Run this as a separate integration test, not in unit test suite
    # Use subprocess or separate test session
    pass
```

**When to use logging tests**:
- Dedicated logging configuration tests (separate test file)
- Tests that verify log levels are set correctly
- Tests run in isolation, not in the full unit test suite
- Explicitly labeled as integration tests

## Pre-commit Hook

A pre-commit hook has been added to catch `caplog` usage in new tests:

```bash
# .pre-commit-config.yaml
- id: no-caplog-in-tests
  name: Check for caplog in tests
  entry: scripts/hooks/check-caplog.sh
  language: script
  files: ^tests/.*\.py$
```

This hook warns developers when adding new tests with caplog patterns, directing them to this document.

## Summary

| Pattern | Status | Use Case |
|---------|--------|----------|
| `assert "msg" in caplog.text` | ❌ **NEVER** | Flaky, fails in full suite |
| Test functional behavior | ✅ **ALWAYS** | Stable, meaningful tests |
| Test state changes | ✅ **ALWAYS** | Cache, models, session |
| Test error handling | ✅ **ALWAYS** | Graceful degradation |
| Dedicated logging tests | ⚠️ **RARELY** | Integration tests only |

## Questions?

If you encounter a situation where you think logging assertions are necessary, ask:

1. **What functional behavior can I test instead?**
2. **What state change does this operation cause?**
3. **How does the system behave differently after this operation?**

If you can answer any of these, test that instead of the log message.

---

**Version**: 1.0
**Last Updated**: 2025-10-28
**Related Issues**: Iterations 2, 4, 5, 10 (flaky test failures)
