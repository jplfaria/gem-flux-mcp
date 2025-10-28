# Pattern: Flaky Caplog Tests

**Discovered**: Session 3 (Iteration 10)
**Frequency**: 4 occurrences before systematic fix (iterations 2, 4, 5, 10)
**Status**: ✅ Resolved with comprehensive solution

## Problem

Tests using pytest's `caplog` fixture to assert on log messages are **flaky**:
- Pass when run individually: `pytest tests/unit/test_foo.py::test_bar`
- Fail intermittently in full suite: `pytest tests/`
- Create false negatives that block valid implementations

## Root Cause

pytest's `caplog` doesn't reliably capture log messages when running the full test suite, even though it works for individual tests.

## Anti-Pattern

```python
# ❌ FLAKY - DO NOT USE
def test_something(caplog):
    """Test that warns about missing data."""
    do_something()
    assert "warning message" in caplog.text  # Fails intermittently
```

## Solution

Test **functional behavior** instead of logging side effects:

```python
# ✅ STABLE - USE THIS
def test_something():
    """Test that handles missing data gracefully."""
    result = do_something()

    # Test observable behavior
    assert result.status == "success"
    assert len(result.data) == expected_count
    assert invalid_item not in result.data
```

## Implementation Examples

### Error Handling with Graceful Degradation
```python
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

### Missing/Invalid Data Warnings
```python
def test_apply_media_missing_exchange(mock_model, mock_media):
    """Test that missing exchange reactions are skipped gracefully."""
    mock_media["bounds"]["cpd99999"] = (-5, 100)  # Invalid compound
    apply_media_to_model(mock_model, mock_media)

    # Test functional behavior
    assert mock_model.medium is not None
    assert "EX_cpd99999_e0" not in mock_model.medium  # Invalid skipped
    assert "EX_cpd00027_e0" in mock_model.medium  # Valid applied
```

## Comprehensive Fix Applied

### 1. Fixed All Existing Tests
- `test_run_fba.py`: 1 flaky assertion → functional behavior test
- `test_atp_media_loader.py`: 6 flaky assertions → functional behavior tests
- **Total**: 7 flaky tests eliminated

### 2. Created Documentation
- `docs/testing-guidelines.md`: Comprehensive guide with DO/DON'T patterns
- Clear examples for 4 testing scenarios
- Quick reference table

### 3. Added Prevention
- Pre-commit hook: `scripts/hooks/check-caplog.sh`
- Detects `assert.*caplog.text` patterns
- Provides actionable error messages
- References testing guidelines

## Impact

**Before Fix** (4 occurrences):
- Each occurrence costs 10-15 minutes to debug
- Pattern would continue indefinitely
- Developer frustration
- False negatives blocking progress

**After Fix**:
- ✅ 0 caplog assertions remaining
- ✅ Pre-commit hook prevents new instances
- ✅ Documentation guides correct patterns
- ✅ Pattern will never recur

## Key Principle

**Test what the system DOES, not what it LOGS**

Logging is a side effect. Test the main effect:
- State changes (cache populated, model updated)
- Return values (empty list, success status)
- System behavior (graceful degradation, error handling)

## Related Files

- Solution: `docs/testing-guidelines.md`
- Prevention: `scripts/hooks/check-caplog.sh`, `.pre-commit-config.yaml`
- Session: [Session 3](../sessions/session-03-iteration-10.md)

## References

- Iteration 2: First occurrence
- Iteration 4: Second occurrence
- Iteration 5: Third occurrence
- Iteration 10: Fourth occurrence → Systematic fix applied
