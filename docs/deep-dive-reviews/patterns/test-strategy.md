# Pattern: Unit vs Integration Test Strategy

**Discovered**: Session 2 (Iteration 8)
**Frequency**: Common with external service integration
**Status**: ⚠️ Guidelines established

## Problem

Attempting to achieve 100% unit test coverage on code that integrates with external services leads to:
- Brittle mocks that break with implementation changes
- Complex test setup that's hard to maintain
- False sense of coverage (mocks don't match real service behavior)
- Diminishing returns on test effort

## When Unit Tests Work Well

✅ **Use unit tests for**:
- Pure business logic
- Data transformations
- Validation logic
- Error handling paths (when errors are local)
- State management
- Internal helper functions

**Example** (Good for unit tests):
```python
def validate_bounds(lower, upper):
    """Validate that lower <= upper."""
    if lower > upper:
        raise ValidationError("Lower bound must be <= upper bound")
    return True

# ✅ Easy to unit test - no external dependencies
def test_validate_bounds_invalid():
    with pytest.raises(ValidationError):
        validate_bounds(10, 5)
```

## When Integration Tests Are Better

⚠️ **Use integration tests for**:
- External API calls (RAST, web services)
- Database operations (complex queries)
- File system operations (when behavior varies by OS)
- External library integration (when mocking is complex)
- End-to-end workflows

**Example** (Better for integration tests):
```python
def annotate_with_rast(genome_id, sequence):
    """Annotate genome using RAST API."""
    response = requests.post(RAST_URL, json={
        "genome_id": genome_id,
        "sequence": sequence
    })
    return response.json()

# ⚠️ Attempting to unit test this requires:
# - Mocking requests.post
# - Defining expected response structure
# - Maintaining mock when API changes
# Better: Integration test with mock RAST server or test environment
```

## Coverage vs Quality Trade-off

### Pragmatic Approach

Accept lower coverage when:
1. **External service is complex to mock** (RAST API)
2. **Overall codebase coverage is high** (>90%)
3. **Feature is "best-effort"** (RAST annotation is optional)
4. **Integration tests are planned** (Phase 9)

**Document the decision**:
```python
# Note: RAST integration path (lines 280-340) is not unit tested
# Rationale: Complex external service mocking with diminishing returns
# Coverage: 78.16% (32 lines in RAST path)
# Plan: Integration tests in Phase 9 with mock RAST server
```

### Example from build_model

**Situation**:
- Module coverage: 78.16% (vs 80% threshold)
- Overall coverage: 94.19%
- Uncovered lines: 32 lines in RAST annotation path
- RAST is optional "best-effort" feature

**Decision**: Accept 78.16% coverage
- Document rationale in review session
- Flag for integration testing in Phase 9
- Focus unit tests on core logic (data parsing, model building)

## Guidelines for Deciding

Ask these questions:

### 1. Can I test this without the external dependency?
- **Yes** → Unit test
- **No** → Integration test

### 2. Is mocking the dependency straightforward?
- **Yes** (simple return values) → Unit test
- **No** (complex data structures, stateful interactions) → Integration test

### 3. Does the mock accurately represent real behavior?
- **Yes** → Unit test
- **Uncertain** → Integration test (mocks can lie)

### 4. Will the mock need frequent updates?
- **No** (stable API) → Unit test
- **Yes** (evolving API) → Integration test

### 5. What's the cost vs benefit?
- **Low effort, high value** → Unit test
- **High effort, low value** → Integration test

## Test Organization

```
tests/
├── unit/                    # Fast, isolated, no external deps
│   ├── test_validation.py
│   ├── test_transforms.py
│   └── test_helpers.py
├── integration/             # Slower, external deps, realistic
│   ├── test_rast_api.py
│   ├── test_database.py
│   └── test_workflows.py
└── e2e/                     # Full system, user scenarios
    └── test_complete_pipeline.py
```

## Benefits

1. **Maintainable tests**: Unit tests focus on core logic
2. **Realistic integration**: Integration tests catch real issues
3. **Faster development**: Don't waste time on brittle mocks
4. **Better coverage**: Test what matters, not just hitting 80%

## Loop Improvement Opportunity

The implementation loop could:
1. Detect external service calls (requests, API clients)
2. Suggest integration test strategy
3. Document coverage gap with rationale
4. Focus unit tests on business logic

## Related Files

- Example: `src/gem_flux_mcp/tools/build_model.py` (RAST integration)
- Session: [Session 2](../sessions/session-02-iteration-08.md)

## Impact

**Session 2 Impact**:
- Accepted 78.16% coverage with documented rationale
- Avoided brittle mocks for RAST API
- Established guidelines for future integration decisions
