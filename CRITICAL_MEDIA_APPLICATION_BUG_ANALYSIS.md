# CRITICAL BUG ANALYSIS: Media Application in Gapfilling and FBA

**Date**: 2025-10-29
**Severity**: CRITICAL
**Status**: Root cause identified, fix ready

---

## Executive Summary

We found TWO critical bugs in how media constraints are applied:

1. **Variable Name Bug**: `gapfill_model.py` treats compound IDs as if they were reaction IDs
2. **API Misuse Bug**: Both files use direct bound setting instead of COBRApy's `.medium` property

These bugs cause media constraints to NEVER be applied, resulting in 0.0 growth rates even for models that should grow.

---

## The Bugs

### Bug #1: Compound ID vs Reaction ID Confusion (gapfill_model.py)

**Location**: `src/gem_flux_mcp/tools/gapfill_model.py:167-174`

**Current Code**:
```python
media_constraints = media.get_media_constraints(cmp="e0")
for reaction_id, (lower_bound, upper_bound) in media_constraints.items():  # ❌ WRONG
    if reaction_id in model.reactions:  # ❌ ALWAYS FALSE
        reaction = model.reactions.get_by_id(reaction_id)
        reaction.lower_bound = lower_bound
        reaction.upper_bound = upper_bound
```

**What Actually Happens**:
```python
# get_media_constraints() returns:
{'cpd00027_e0': (-5, 100), 'cpd00007_e0': (-10, 100), ...}  # COMPOUND IDs

# Loop iteration:
reaction_id = 'cpd00027_e0'  # This is a COMPOUND ID, not a reaction ID!

# Lookup:
if 'cpd00027_e0' in model.reactions:  # FALSE - model has 'EX_cpd00027_e0'
    # This block NEVER executes!
```

**Why It Fails**:
- `get_media_constraints()` returns dict with **compound IDs** as keys (`cpd00027_e0`)
- Model reactions have **exchange reaction IDs** (`EX_cpd00027_e0`)
- Missing "EX_" prefix means lookup always fails
- No media constraints are ever applied!

---

### Bug #2: Wrong Media Application Method (Both Files)

**Locations**:
- `src/gem_flux_mcp/tools/gapfill_model.py:167-174`
- `src/gem_flux_mcp/tools/run_fba.py:135-155`

**What We Do**:
```python
# Set bounds directly on reactions
reaction.lower_bound = lower_bound  # -5.0
reaction.upper_bound = upper_bound  # 100.0
```

**What ModelSEEDpy Reference Does**:
```python
# Use COBRApy's .medium property
medium = {}
for cpd, (lb, ub) in media.get_media_constraints().items():
    rxn_exchange = f'EX_{cpd}'  # Add EX_ prefix
    if rxn_exchange in model.reactions:
        medium[rxn_exchange] = math.fabs(lb)  # POSITIVE uptake rate

model.medium = medium  # Special property that resets ALL exchanges first
```

**Why `.medium` Property Matters**:

COBRApy's `.medium` property (from `cobra/core/model.py`):
1. **Closes ALL exchange reactions** (sets all to 0)
2. **Opens only specified reactions** with given uptake rates
3. **Expects positive values** (e.g., 5.0 means -5.0 to 1000.0 bounds)
4. **Is the canonical way** to apply media in COBRApy

Direct bound setting:
- Does NOT close other exchanges
- Leaves model in inconsistent state
- Can have conflicts between media

---

## Evidence from Reference Implementation

**Source**: `/Users/jplfaria/repos/gem-flux-mcp/specs-source/build_metabolic_model/build_model.ipynb`

**Cell `8efdcd34-ffc0-4837-a8a2-1896d7121019`**:
```python
def integrate_to_model_medium(media, model, prefix='EX_'):
    """Convert MSMedia to COBRApy medium dict."""
    medium = {}
    for cpd, (lb, ub) in media.get_media_constraints().items():
        rxn_exchange = f'{prefix}{cpd}'  # EX_cpd00027_e0
        if rxn_exchange in model.reactions:
            medium[rxn_exchange] = math.fabs(lb)  # Positive uptake rate
        else:
            print('not in model', cpd)
    return medium

# Apply media
model_gapfilled.medium = integrate_to_model_medium(media_glucose, model_gapfilled)
model_gapfilled.objective = 'bio1'
model_gapfilled.summary()  # Shows growth!
```

**Key Points**:
1. ✅ Adds "EX_" prefix to compound IDs
2. ✅ Converts negative bounds to positive with `math.fabs()`
3. ✅ Uses `.medium` property, not direct bound setting
4. ✅ This is how ModelSEEDpy intends media to be applied

---

## Impact Analysis

### What This Bug Causes

**In Gapfilling**:
```python
# check_baseline_growth() is called TWICE:
growth_rate_before = check_baseline_growth(model, media)  # Returns 0.0 (no media!)
# ... gapfilling adds reactions ...
growth_rate_after = check_baseline_growth(model, media)   # Returns 0.0 (no media!)
```

**Result**:
- Gapfilling reports growth_rate_after = 0.562 (from internal gapfilling FBA with media)
- But check_baseline_growth reports 0.0 (no media applied)
- The 0.562 comes from MSGapfill's internal verification, NOT our check_baseline_growth!

**In FBA**:
```python
apply_media_to_model(model, media)  # Silently does nothing!
solution = model.optimize()          # Runs with no media constraints
```

**Result**:
- FBA always returns 0.0 growth
- Model cannot uptake ANY nutrients
- User sees "optimal" status but 0.0 objective value

---

## The Complete Picture

### What Actually Happened in User's Notebook

**Cell 10 (Gapfilling)**:
```
Growth rate after: 0.562 hr⁻¹
```
- This 0.562 came from **MSGapfill's internal FBA**, which applies media correctly
- Our `check_baseline_growth()` also ran but returned 0.0 (bug #1)
- We reported the MSGapfill value, not our broken check

**Cell 12 (Run FBA)**:
```
Objective value: -0.000 hr⁻¹
```
- Our `apply_media_to_model()` silently failed (bug #1)
- FBA ran with NO media constraints
- Model cannot uptake glucose/O2 → cannot grow
- Returned 0.0 growth (shown as -0.000 before objective_direction fix)

**The Saved JSON**:
- Contains gapfilled reactions (they were integrated correctly)
- But exchange bounds are in "default" state (not media-constrained)
- When reloaded and FBA run, same bug happens → 0.0 growth

---

## The Fix

### Fix #1: gapfill_model.py - check_baseline_growth()

**File**: `src/gem_flux_mcp/tools/gapfill_model.py`
**Lines**: 154-189

**Replace**:
```python
def check_baseline_growth(model: Any, media: Any) -> float:
    """Check if model can grow on given media.

    Args:
        model: COBRApy model
        media: MSMedia object or dict

    Returns:
        Growth rate (objective value)
    """
    try:
        # Apply media constraints
        if hasattr(media, "get_media_constraints"):
            # MSMedia object
            media_constraints = media.get_media_constraints(cmp="e0")

            # Apply constraints to exchange reactions
            for reaction_id, (lower_bound, upper_bound) in media_constraints.items():
                if reaction_id in model.reactions:
                    reaction = model.reactions.get_by_id(reaction_id)
                    reaction.lower_bound = lower_bound
                    reaction.upper_bound = upper_bound
```

**With**:
```python
def check_baseline_growth(model: Any, media: Any) -> float:
    """Check if model can grow on given media.

    Uses COBRApy's .medium property for correct media application.

    Args:
        model: COBRApy model
        media: MSMedia object or dict

    Returns:
        Growth rate (objective value)
    """
    import math

    try:
        # Apply media constraints using .medium property
        if hasattr(media, "get_media_constraints"):
            # MSMedia object - build medium dict
            medium = {}
            media_constraints = media.get_media_constraints(cmp="e0")

            for compound_id, (lower_bound, upper_bound) in media_constraints.items():
                # Convert compound ID to exchange reaction ID
                exchange_rxn_id = f"EX_{compound_id}"

                if exchange_rxn_id in model.reactions:
                    # .medium property expects POSITIVE uptake rates
                    medium[exchange_rxn_id] = math.fabs(lower_bound)
                else:
                    logger.debug(f"Exchange reaction {exchange_rxn_id} not in model")

            # Apply media using .medium property (closes all exchanges first)
            model.medium = medium
            logger.debug(f"Applied media to {len(medium)} exchange reactions")
```

**Changes**:
1. ✅ Renamed `reaction_id` → `compound_id` (correct semantics)
2. ✅ Added "EX_" prefix: `exchange_rxn_id = f"EX_{compound_id}"`
3. ✅ Convert to positive with `math.fabs(lower_bound)`
4. ✅ Use `.medium` property instead of direct bounds

---

### Fix #2: run_fba.py - apply_media_to_model()

**File**: `src/gem_flux_mcp/tools/run_fba.py`
**Lines**: 110-196

**Replace the MSMedia path (lines 130-155)**:
```python
if hasattr(media_data, "get_media_constraints"):
    # MSMedia object - use get_media_constraints() method
    media_constraints = media_data.get_media_constraints(cmp="e0")

    # Apply each constraint to the model's exchange reactions
    applied_count = 0
    for compound_id, (lower_bound, upper_bound) in media_constraints.items():
        # Convert compound ID to exchange reaction ID
        reaction_id = f"EX_{compound_id}"

        if reaction_id in model.reactions:
            reaction = model.reactions.get_by_id(reaction_id)
            reaction.lower_bound = lower_bound
            reaction.upper_bound = upper_bound
            applied_count += 1
```

**With**:
```python
if hasattr(media_data, "get_media_constraints"):
    # MSMedia object - build medium dict for .medium property
    import math
    medium = {}
    media_constraints = media_data.get_media_constraints(cmp="e0")

    for compound_id, (lower_bound, upper_bound) in media_constraints.items():
        # Convert compound ID to exchange reaction ID
        exchange_rxn_id = f"EX_{compound_id}"

        if exchange_rxn_id in model.reactions:
            # .medium property expects POSITIVE uptake rates
            medium[exchange_rxn_id] = math.fabs(lower_bound)
        else:
            logger.debug(f"Exchange reaction {exchange_rxn_id} not in model")

    # Apply using .medium property (closes all exchanges first)
    model.medium = medium
    logger.info(f"Applied media to {len(medium)} exchange reactions using .medium property")
```

**Changes**:
1. ✅ Build `medium` dict instead of setting bounds directly
2. ✅ Convert to positive with `math.fabs(lower_bound)`
3. ✅ Use `.medium` property
4. ✅ Improved logging

---

## Expected Results After Fix

### Gapfilling
```python
growth_rate_before = check_baseline_growth(model, media)
# Before fix: 0.0 (media not applied)
# After fix:  0.0 (correct - draft model cannot grow)

# ... gapfilling ...

growth_rate_after = check_baseline_growth(model, media)
# Before fix: 0.0 (media not applied)
# After fix:  0.562 (correct - gapfilled model can grow!)
```

### FBA
```python
result = run_fba(model_id="E_coli_K12.draft.gf", media_id="glucose_minimal_aerobic")
# Before fix: 0.0 (media not applied)
# After fix:  0.562 (correct - model grows on glucose!)
```

---

## Testing Plan

1. **Unit tests**: Verify `.medium` property is used
2. **Integration test**: Run full workflow (build → gapfill → FBA)
3. **Notebook**: Re-run with fresh kernel
4. **Verify**: Growth rate should be positive (0.5-0.9 hr⁻¹)

---

## Related Issues

- ✅ Fixed: `model.objective_direction` not set (commit fecc7e0)
- ✅ Will fix: Media application bugs (this document)
- ⚠️ To verify: Exchange reaction bounds in saved JSON

---

## References

- ModelSEEDpy reference: `specs-source/build_metabolic_model/build_model.ipynb`
- COBRApy medium property: `cobra/core/model.py` (`.medium` setter)
- Our implementation: `src/gem_flux_mcp/tools/gapfill_model.py`, `src/gem_flux_mcp/tools/run_fba.py`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-29
**Status**: Ready for implementation
