# Pattern: Structured TODOs

**Discovered**: Session 1 (Iteration 7)
**Frequency**: Common placeholder pattern
**Status**: ⚠️ Template established, apply to future TODOs

## Problem

Generic TODO comments provide no context about urgency, dependencies, or implementation approach:

```python
# TODO: Integrate with ModelSEEDpy MSMedia.from_dict() in next iteration
```

**Issues**:
- No timeline or urgency indication
- No explanation of why it's needed
- No reference to specification or examples
- No context about current state

**Impact**: Future developers (or AI loop) might skip, delay, or incorrectly implement the TODO, potentially breaking dependent features.

## Solution Template

Structure TODOs to answer four key questions:

```python
# TODO (URGENCY - Context): Brief description
# Timeline: When this must be completed
# Reason: Why this is needed / what depends on it
# Integration: Reference to spec/docs/examples
# Current: What the current state/workaround is
```

## Real Example

**Before**:
```python
# TODO: Integrate with ModelSEEDpy MSMedia.from_dict() in next iteration
```

**After**:
```python
# TODO (CRITICAL - Required before Phase 6): Integrate ModelSEEDpy MSMedia.from_dict()
# Timeline: Must be completed before Task 51 (gapfill_model implementation)
# Reason: gapfill_model and run_fba tools require real MSMedia objects from ModelSEEDpy
# Integration: See spec 003-build-media-tool.md lines 320-340 for MSMedia.from_dict() pattern
# Current: Storing dict representation for Phase 5 unit testing only
```

## Four Key Questions

### 1. WHEN (Timeline)
- When must this be completed?
- What phase/task/milestone depends on this?
- Is there a deadline?

**Examples**:
- `Timeline: Must be completed before Task 51 (gapfill_model)`
- `Timeline: Required for Phase 6 integration testing`
- `Timeline: Defer until MVP+1 (not blocking current work)`

### 2. WHY (Reason)
- Why is this needed?
- What breaks if we don't do this?
- What feature/tool depends on this?

**Examples**:
- `Reason: gapfill_model requires real MSMedia objects`
- `Reason: Performance optimization for large models (current O(n²))`
- `Reason: User-facing error messages need compound names`

### 3. HOW (Integration)
- Where is the spec/documentation?
- Are there examples to follow?
- What's the implementation approach?

**Examples**:
- `Integration: See spec 003-build-media-tool.md lines 320-340`
- `Integration: Follow pattern in build_model.py:245-260`
- `Integration: ModelSEEDpy docs: https://...`

### 4. WHAT (Current State)
- What's the current workaround?
- Why is the temporary solution insufficient?
- What's the limitation?

**Examples**:
- `Current: Storing dict representation (works for unit tests only)`
- `Current: Using linear search (acceptable for <100 items)`
- `Current: Skipping validation (assumes trusted input)`

## Urgency Levels

Use consistent urgency markers:

- `CRITICAL` - Blocks upcoming work, must be done soon
- `HIGH` - Important for quality/completeness, do before next phase
- `MEDIUM` - Nice to have, do when time permits
- `LOW` - Future enhancement, defer to post-MVP

## Benefits

1. **Prevents blockers**: Clearly identifies critical work
2. **Guides implementation**: References specs and examples
3. **Context preservation**: Future developers understand the why
4. **Prioritization**: Urgency markers enable proper scheduling

## Loop Improvement Opportunity

The implementation loop could:
1. Detect placeholder TODO patterns
2. Prompt for the four key pieces of information
3. Generate structured TODO automatically

## Related Files

- Example: `src/gem_flux_mcp/tools/media_builder.py:272-276`
- Session: [Session 1](../sessions/session-01-iteration-07.md)

## Impact

**Session 1 Impact**:
- Prevented Phase 6 blocker
- Documented critical MSMedia integration requirement
- Established pattern for future TODOs
