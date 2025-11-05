# Interpretation Design Decisions

**Date**: 2025-11-05
**Context**: Centralized Prompts Migration (v0.3.0)

---

## Overview

During the centralized prompts migration, we extracted `next_steps` arrays and the `build_model` interpretation to markdown files. However, we deliberately **kept** the `gapfill_model` and `run_fba` interpretations in Python code.

This document explains the rationale and provides guidance for future decisions.

---

## What Was Extracted

### ✅ Extracted to Markdown

1. **next_steps arrays** (8 tools)
   - `prompts/next_steps/*.md`
   - Simple bullet-point lists with conditional logic
   - Human-readable workflow guidance
   - Easy to edit by non-developers

2. **build_model interpretation** (1 tool)
   - `prompts/interpretations/build_model.md`
   - Text-based categorization (e.g., "High-quality draft model")
   - Simple threshold checks on reaction counts
   - No calculations, just conditional text

---

## What Was Kept in Code

### ❌ Kept in Python

1. **gapfill_model interpretation**
   - Complex nested dictionary with mixed data types
   - Contains calculations (rounding, percentages)
   - Contains business logic with numeric thresholds
   - Contains structured data (growth_improvement dict)

2. **run_fba interpretation**
   - Algorithmic logic (detecting oxygen uptake)
   - Numeric threshold logic (growth assessment: > 0.5, > 0.1, > 0.01)
   - Data lookups (finding carbon source in flux arrays)
   - Mixed string and numeric fields

---

## The Decision Rule

### Extract to Markdown When:

✅ **Simple text categorization**
- Output is purely text descriptions
- No calculations, just conditional text selection
- Example: "High-quality draft model" vs "Moderate draft model"

✅ **Human-readable lists**
- Bullet-point guidance (next_steps)
- Workflow suggestions
- Static or conditionally-selected text items

✅ **Non-developer editable**
- Prompt wording improvements don't require understanding code
- Changes don't affect data structures or logic
- Can be A/B tested by team members

✅ **No business logic**
- No numeric thresholds that affect behavior
- No calculations or transformations
- Pure presentation layer

### Keep in Code When:

❌ **Complex data structures**
- Nested dictionaries with mixed types
- Structured JSON responses
- Data that will be processed by downstream code

❌ **Contains calculations**
- Rounding, percentages, aggregations
- Mathematical operations on data
- Example: `round(growth_rate, 6)`, `unknown_pct = (unknown_count / total) * 100`

❌ **Contains business logic**
- Numeric thresholds that define behavior
- Example: `growth_rate > 0.5` → "Fast growth"
- These thresholds may need to be tuned based on scientific validation

❌ **Data lookups and transformations**
- Querying arrays (e.g., finding oxygen in uptake_fluxes)
- Conditional logic based on computed values
- Example: `has_oxygen = any(f["compound_id"] == "cpd00007" for f in uptake_fluxes)`

---

## Examples

### Example 1: build_model interpretation (✅ Extracted)

**Why extracted:**
```markdown
{% if num_reactions > 1500 %}
High-quality draft model with extensive reaction coverage
{% elif num_reactions > 800 %}
Moderate draft model with reasonable pathway coverage
{% else %}
Low-coverage draft model - may indicate poor genome annotation
{% endif %}
```

- Pure text selection based on simple threshold
- No calculations (num_reactions is passed as variable)
- Easy to improve wording
- Thresholds are straightforward (1500, 800)

### Example 2: gapfill_model interpretation (❌ Kept in Code)

**Why kept in code:**
```python
interpretation = {
    "overview": overview,  # Conditional text based on success flag
    "growth_improvement": {
        "before": round(growth_rate_before, 6),  # Calculation
        "after": round(growth_rate_after, 6),     # Calculation
        "target": target_growth_rate,
        "met_target": gapfilling_successful,
    },
    "gapfilling_assessment": (
        f"Minimal gapfilling ({num_reactions} reactions)" if num_reactions < 10 else
        f"Moderate gapfilling ({num_reactions} reactions)" if num_reactions < 50 else
        f"Extensive gapfilling ({num_reactions} reactions) - may indicate poor annotation quality"
    ),
}

if unknown_count > 0:
    interpretation["pathway_coverage_note"] = (
        f"{unknown_count} of {num_reactions} reactions "
        f"({unknown_pct}%) lack pathway annotations in database"
    )
```

**Why this is complex:**
- Nested dictionary with structured data
- Contains calculations: `round(growth_rate_before, 6)`
- Contains business logic: `< 10`, `< 50` thresholds
- Contains conditional key addition: `if unknown_count > 0`
- String interpolation with computed values: `f"{unknown_pct}%"`

### Example 3: run_fba interpretation (❌ Kept in Code)

**Why kept in code:**
```python
# Data lookup from uptake fluxes
has_oxygen = any(f["compound_id"] == "cpd00007" for f in flux_data["uptake_fluxes"])
metabolism_type = "Aerobic respiration" if has_oxygen else "Anaerobic/fermentation"

# Array search for carbon source
carbon_sources = ["cpd00027", "cpd00029", "cpd00020"]
main_carbon = None
for f in flux_data["uptake_fluxes"]:
    if f["compound_id"] in carbon_sources:
        main_carbon = f["compound_id"]
        break

interpretation = {
    "growth_rate_per_hour": round(growth_rate, 3),  # Calculation
    "metabolism_type": metabolism_type,              # From data lookup
    "carbon_source": main_carbon if main_carbon else "Unknown",
    "growth_assessment": (
        "Fast growth" if growth_rate > 0.5 else      # Threshold logic
        "Moderate growth" if growth_rate > 0.1 else
        "Slow growth" if growth_rate > 0.01 else
        "Very slow growth"
    ),
    "model_status": "Model is viable and can grow in specified media"
}
```

**Why this is complex:**
- Data lookups: searching uptake_fluxes for oxygen and carbon sources
- Calculations: `round(growth_rate, 3)`
- Business logic: growth rate thresholds (0.5, 0.1, 0.01)
- Mixed data types: numbers, strings, booleans

---

## Future Considerations

### Pros of Extracting More to Markdown

✅ **Visibility**: All text visible in one place
✅ **A/B Testing**: Easy to test different wording
✅ **Team Collaboration**: Non-developers can improve descriptions
✅ **Version Control**: Git tracks text changes separately

### Cons of Extracting More to Markdown

❌ **Complexity**: Templating logic for nested structures is hard to read
❌ **Fragmentation**: Business logic split between .md and .py
❌ **Type Safety**: No validation for complex data structures in templates
❌ **Debugging**: Harder to trace issues when logic is in templates

### Hybrid Approach (Possible Future)

If we want more interpretations in markdown, we could:

1. **Keep structure in code, text in markdown**:
   ```python
   # Code: Structure and calculations
   interpretation = {
       "growth_improvement": {
           "before": round(growth_rate_before, 6),
           "after": round(growth_rate_after, 6),
           "target": target_growth_rate,
           "met_target": gapfilling_successful,
       },
       "overview": render_prompt(
           "interpretations/gapfill_overview",
           num_reactions=num_reactions,
           num_pathways=pathway_summary['num_pathways_affected'],
           gapfilling_successful=gapfilling_successful,
       ),
       "assessment": render_prompt(
           "interpretations/gapfill_assessment",
           num_reactions=num_reactions,
       ),
   }
   ```

2. **Benefits**:
   - Calculations and structure in code (type-safe)
   - Text descriptions in markdown (easy to edit)
   - Clear separation of concerns

3. **Drawbacks**:
   - More files to maintain
   - Increased complexity
   - Requires careful coordination between .py and .md

---

## Recommendation

**For now (v0.3.0):**
- ✅ Keep current approach: simple text in markdown, complex logic in code
- ✅ This is the right balance for maintainability

**For future (v0.4.0+):**
- Consider hybrid approach if team wants more text-editing flexibility
- Extract text portions of gapfill/run_fba interpretations if needed
- Keep calculations and data structures in code
- Re-evaluate based on actual team usage patterns

---

## Questions to Ask Before Extracting

Before extracting an interpretation to markdown, ask:

1. **Does it contain calculations?** → Keep in code
2. **Does it contain nested data structures?** → Keep in code
3. **Does it have numeric thresholds that might need tuning?** → Keep in code
4. **Is it pure text categorization?** → Extract to markdown
5. **Would non-developers need to edit this?** → Consider extracting
6. **Is the logic simple enough for Jinja2?** → Consider extracting

---

## Related Files

- `prompts/README.md` - General prompts documentation
- `PROMPTS_MIGRATION_COMPLETE.md` - Migration summary
- `baseline_tests/BEFORE_AFTER_COMPARISON.md` - Examples of extracted prompts

---

**Conclusion**: The current split (simple text in markdown, complex logic in code) is the right balance. We can revisit if team needs change.
