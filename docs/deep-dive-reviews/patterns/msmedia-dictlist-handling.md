# Pattern: MSMedia DictList Handling

**Status**: ✅ Resolved
**Discovered**: Session 10 (Iteration 1, Phase 10)
**Category**: Dependency Integration

## Problem

ModelSEEDpy's `MSMedia.mediacompounds` attribute is a COBRApy `DictList` object, not a standard Python dict. Attempting to call `.items()` on it results in:

```
AttributeError: DictList has no attribute or entry items
```

This breaks any code that assumes standard dict behavior.

## Root Cause

**Assumption**: External library objects behave like Python built-ins

```python
# Assumed this would work:
for cpd_id, bounds in media.mediacompounds.items():
    process(cpd_id, bounds)
```

**Reality**: COBRApy uses custom `DictList` class
- Has dict-like `__getitem__` access
- Is iterable over keys
- Does NOT have `.items()` method

## Solution

**Iterate over keys, then access by key**:

```python
# ✅ CORRECT
for cpd_id in media.mediacompounds:
    cpd_data = media.mediacompounds[cpd_id]
    if isinstance(cpd_data, (list, tuple)) and len(cpd_data) >= 2:
        bounds = (cpd_data[0], cpd_data[1])
        process(cpd_id, bounds)
```

## Complete Example

### Before (Broken)

```python
def apply_media_to_model(model: Any, media_data: Any) -> None:
    """Apply media constraints to model."""
    if hasattr(media_data, "mediacompounds"):
        # ❌ WRONG: .items() doesn't exist on DictList
        bounds_dict = {
            cpd_id: (min_flux, max_flux)
            for cpd_id, (min_flux, max_flux, *_) in media_data.mediacompounds.items()
        }
    elif isinstance(media_data, dict):
        bounds_dict = media_data.get("bounds", {})
```

**Error**:
```
Traceback (most recent call last):
  File "/Users/jplfaria/repos/gem-flux-mcp/src/gem_flux_mcp/tools/run_fba.py", line 131, in apply_media_to_model
    for cpd_id, (min_flux, max_flux, *_) in media_data.mediacompounds.items()
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/jplfaria/miniconda3/lib/python3.11/site-packages/cobra/core/dictlist.py", line 527, in __getattr__
    raise AttributeError(f"DictList has no attribute or entry {attr}")
AttributeError: DictList has no attribute or entry items
```

### After (Working)

```python
def apply_media_to_model(model: Any, media_data: Any) -> None:
    """Apply media constraints to model."""
    if hasattr(media_data, "mediacompounds"):
        # ✅ CORRECT: Iterate keys, access by key
        bounds_dict = {}
        for cpd_id in media_data.mediacompounds:
            cpd_data = media_data.mediacompounds[cpd_id]
            # cpd_data is tuple: (min_flux, max_flux, ...)
            if isinstance(cpd_data, (list, tuple)) and len(cpd_data) >= 2:
                bounds_dict[cpd_id] = (cpd_data[0], cpd_data[1])
            else:
                logger.warning(f"Unexpected format for {cpd_id}: {cpd_data}")
                continue
    elif isinstance(media_data, dict):
        bounds_dict = media_data.get("bounds", {})
```

## Benefits

1. **Works with COBRApy DictList**: No AttributeError
2. **Handles dict fallback**: Still supports plain dict format
3. **Type-safe**: Validates tuple structure before unpacking
4. **Robust**: Logs warning for unexpected formats instead of crashing

## When to Apply

Apply this pattern when:
- Working with ModelSEEDpy `MSMedia` objects
- Accessing `MSMedia.mediacompounds` attribute
- Any COBRApy object that uses `DictList` internally
- Integrating with libraries that have custom dict-like classes

## Loop Improvement Opportunities

1. **Integration Tests with Real Objects**
   ```python
   # tests/integration/test_msmedia_handling.py
   def test_apply_media_with_real_msmedia_object():
       """Test with actual ModelSEEDpy MSMedia object."""
       media = MSMedia.from_dict(...)  # Real object
       apply_media_to_model(model, media)
       assert no errors
   ```

2. **Documentation**
   ```python
   def apply_media_to_model(model: Any, media_data: Any) -> None:
       """Apply media constraints to model.

       Args:
           media_data: MSMedia object or dict with bounds
                      Note: MSMedia.mediacompounds is COBRApy DictList,
                      not standard dict. Iterate keys, don't use .items()
       """
   ```

3. **Type Hints**
   ```python
   from typing import Union
   from modelseedpy.core.msmedium import MSMedia

   def apply_media_to_model(
       model: cobra.Model,
       media_data: Union[MSMedia, dict[str, tuple[float, float]]]
   ) -> None:
       """Makes expected types explicit."""
   ```

## Related Files

- `src/gem_flux_mcp/tools/run_fba.py:125-138` - Implementation
- `examples/01_basic_workflow.ipynb` - Usage example
- `tests/unit/test_run_fba.py` - Should add DictList test case

## Related Patterns

- [Observability](observability.md) - Logging warnings for unexpected formats
- (Dependency Integration Pattern - future)

## Related Sessions

- [Session 10](../sessions/session-10-iteration-01-phase10-critical-audit.md) - Discovery and fix

## Impact

**Before Fix**:
- ❌ Notebooks crashed at Cell 10 (run_fba)
- ❌ Users couldn't complete basic workflow
- ❌ Poor error message (internal DictList AttributeError)

**After Fix**:
- ✅ Notebooks work with both MSMedia and dict
- ✅ Graceful handling of unexpected formats
- ✅ Clear warnings for edge cases

**Prevented Issues**:
- User frustration with broken notebooks
- Support burden ("why doesn't FBA work?")
- Need for emergency patch after release
