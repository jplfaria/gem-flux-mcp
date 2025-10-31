# gapfill_model Tool

## Overview

The `gapfill_model` tool adds missing reactions to enable growth in metabolic models. It performs two-stage gapfilling: ATP correction for energy metabolism, followed by genome-scale gapfilling to enable growth in the target medium.

**Location**: `src/gem_flux_mcp/tools/gapfill_model.py`

## What It Does

- Two-stage gapfilling (ATP correction + genome-scale)
- Automatically reuses ATP test conditions from `build_model` (if available)
- Adds minimal reaction set to achieve target growth rate
- Validates growth across multiple media conditions
- Stores gapfilled models with `.gf` suffix

## What It Does NOT Do (MVP Scope)

- Does not validate biological accuracy of added reactions
- Does not optimize reaction selection beyond minimization
- Does not perform iterative refinement
- Does not guarantee complete pathway coverage

## Function Signature

```python
def gapfill_model(
    model_id: str,
    media_id: str,
    db_index: DatabaseIndex,
    target_growth_rate: float = 0.01,
    allow_all_non_grp_reactions: bool = True,
    gapfill_mode: str = "full",
) -> dict[str, Any]
```

## Parameters

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model_id` | `str` | Yes | - | Model identifier (typically `.draft` suffix) |
| `media_id` | `str` | Yes | - | Media identifier for gapfilling conditions |
| `db_index` | `DatabaseIndex` | Yes | - | Database index with loaded compounds/reactions |
| `target_growth_rate` | `float` | No | `0.01` | Minimum growth rate to achieve |
| `allow_all_non_grp_reactions` | `bool` | No | `True` | Allow non-gene-associated reactions |
| `gapfill_mode` | `str` | No | `"full"` | Gapfilling mode: "full", "atp_only", "genomescale_only" |

### Return Value

```python
{
    "success": bool,
    "model_id": str,  # New model ID with .gf suffix
    "original_model_id": str,
    "media_id": str,
    "growth_rate_before": float,
    "growth_rate_after": float,
    "target_growth_rate": float,
    "gapfilling_successful": bool,
    "num_reactions_added": int,
    "reactions_added": [
        {
            "id": str,
            "name": str,
            "equation": str,
            "direction": str,  # "forward", "reverse", "reversible"
            "compartment": str,
            "bounds": [float, float],
            "source": str
        }
    ],
    "atp_correction": {
        "performed": bool,
        "media_tested": int,  # 54 if performed
        "media_passed": int,
        "media_failed": int,
        "reactions_added": int,
        "test_conditions_reused": int,  # If reusing from build_model
        "note": str
    },
    "genomescale_gapfill": {
        "performed": bool,
        "reactions_added": int,
        "reversed_reactions": int,
        "new_reactions": int
    },
    "model_properties": {
        "num_reactions": int,
        "num_metabolites": int,
        "is_draft": bool,
        "requires_further_gapfilling": bool
    }
}
```

## Usage Examples

### Example 1: Complete Gapfilling Workflow

```python
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.database.index import DatabaseIndex

# Gapfill model built with ATP correction
result = gapfill_model(
    model_id="ecoli_demo.draft",
    media_id="glucose_minimal",
    db_index=db_index,
    target_growth_rate=0.01,
    gapfill_mode="full"  # ATP + genome-scale
)

print(f"Gapfilled model: {result['model_id']}")  # ecoli_demo.draft.gf
print(f"Growth before: {result['growth_rate_before']:.6f}")
print(f"Growth after: {result['growth_rate_after']:.6f}")
print(f"Reactions added: {result['num_reactions_added']}")
```

### Example 2: Using Different Gapfill Modes

```python
# ATP correction only
atp_result = gapfill_model(
    model_id="model.draft",
    media_id="glucose_minimal",
    db_index=db_index,
    gapfill_mode="atp_only"  # Only ATP correction
)

# Then genome-scale gapfilling
gs_result = gapfill_model(
    model_id=atp_result["model_id"],  # model.draft.gf
    media_id="glucose_minimal",
    db_index=db_index,
    gapfill_mode="genomescale_only"  # Only genome-scale
)

print(f"Final model: {gs_result['model_id']}")  # model.draft.gf.gf
```

### Example 3: Re-gapfilling on Different Media

```python
# First gapfilling on glucose
glucose_result = gapfill_model(
    model_id="model.draft",
    media_id="glucose_minimal",
    db_index=db_index
)

# Re-gapfill same model on pyruvate
pyruvate_result = gapfill_model(
    model_id=glucose_result["model_id"],  # model.draft.gf
    media_id="pyruvate_minimal",
    db_index=db_index,
    gapfill_mode="genomescale_only"  # ATP already done
)

print(f"Multi-media model: {pyruvate_result['model_id']}")  # model.draft.gf.gf
```

## Gapfilling Stages

### Stage 1: ATP Correction (MSATPCorrection)

**Purpose**: Ensure energy metabolism works correctly across multiple media conditions.

**Process**:
1. Tests ATP production across 54 default media
2. Identifies missing reactions in energy metabolism
3. Adds reactions to fix ATP gaps
4. Expands model to genome-scale template
5. Builds test conditions for genome-scale gapfilling

**When It Runs**:
- Always in `gapfill_mode="full"` or `"atp_only"`
- **Skipped** if test conditions exist from `build_model` ATP correction
- Takes ~3-5 minutes

**Test Conditions Reuse**:
If model was built with `apply_atp_correction=True`, this stage is automatically skipped and the stored test conditions are reused:

```python
"atp_correction": {
    "performed": False,
    "note": "Skipped - ATP correction already applied during build_model",
    "test_conditions_reused": 54
}
```

### Stage 2: Genome-Scale Gapfilling (MSGapfill)

**Purpose**: Add minimal reactions to enable growth in target medium.

**Process**:
1. Uses ATP test conditions for multi-media validation
2. Identifies minimal reaction set for target growth rate
3. Adds reactions from template
4. Creates exchange reactions for new metabolites
5. Verifies growth rate meets target

**When It Runs**:
- Always in `gapfill_mode="full"` or `"genomescale_only"`
- Takes ~5-10 minutes

**Reaction Integration Order**:
Critical for correctness:
1. Add non-exchange reactions from template
2. Call `MSBuilder.add_exchanges_to_model()` for new metabolites
3. Set bounds on exchange reactions

## Gapfill Modes

### Mode: "full" (Default)

Recommended for most use cases.

**Steps**:
1. ATP correction (or reuse from build_model)
2. Genome-scale gapfilling

**Use When**:
- First time gapfilling a draft model
- Building production-ready models
- Need biologically realistic results

### Mode: "atp_only"

ATP correction only, no genome-scale gapfilling.

**Steps**:
1. ATP correction only

**Use When**:
- Model lacks ATP correction
- Want to apply genome-scale gapfilling separately
- Debugging energy metabolism issues

### Mode: "genomescale_only"

Genome-scale gapfilling only, assumes ATP correction already done.

**Steps**:
1. Genome-scale gapfilling only

**Use When**:
- Model already ATP-corrected
- Re-gapfilling on different media
- ATP correction not needed

## Model ID Transformations

Gapfilling adds `.gf` suffix to track state:

```
model.draft → model.draft.gf → model.draft.gf.gf
```

**Progression**:
1. **`.draft`**: Built but not gapfilled
2. **`.draft.gf`**: Gapfilled once
3. **`.draft.gf.gf`**: Re-gapfilled on additional media

## Target Growth Rate

The `target_growth_rate` parameter controls how permissive gapfilling is:

| Value | Interpretation | Use Case |
|-------|---------------|----------|
| `0.001` | Very permissive | Broad media conditions, exploratory |
| `0.01` | Permissive (default) | Standard gapfilling |
| `0.1` | Moderate | More stringent constraints |
| `0.5+` | Stringent | Near-maximal growth required |

**Recommendation**: Start with `0.01` (default) and adjust based on results.

## Error Handling

### Common Errors

**MODEL_NOT_FOUND**
```python
{
    "error_code": "MODEL_NOT_FOUND",
    "message": "Model not found in session",
    "details": {
        "model_id": "unknown_model.draft",
        "available_models": ["ecoli.draft", "bacillus.draft"]
    }
}
```

**MEDIA_NOT_FOUND**
```python
{
    "error_code": "MEDIA_NOT_FOUND",
    "message": "Media not found in session",
    "details": {
        "media_id": "unknown_media",
        "available_media": ["glucose_minimal", "pyruvate_minimal"]
    }
}
```

**MODEL_INFEASIBLE**
```python
{
    "error_code": "MODEL_INFEASIBLE",
    "message": "Gapfilling could not find solution to achieve target growth rate",
    "suggestions": [
        "Try lower target_growth_rate (e.g., 0.001)",
        "Check media contains essential nutrients (C, N, P, S sources)",
        "Verify template has sufficient reactions"
    ]
}
```

**INVALID_TARGET_GROWTH_RATE**
```python
{
    "error_code": "INVALID_TARGET_GROWTH_RATE",
    "message": "Target growth rate must be positive",
    "details": {
        "provided_value": -0.1,
        "valid_range": [0.001, 10.0],
        "typical_range": [0.01, 1.0]
    }
}
```

## Implementation Details

### Workflow Steps

1. **Validate inputs**: Check model/media exist, validate parameters
2. **Load model and media**: Retrieve from session storage
3. **Create working copy**: Preserve original model
4. **Check baseline growth**: Test if model already grows
5. **Load templates**: Get genome-scale and Core templates
6. **Check for test conditions**: Look for stored ATP test conditions
7. **ATP correction** (if needed): Run MSATPCorrection workflow
8. **Genome-scale gapfilling**: Run MSGapfill workflow
9. **Integrate solution**: Add reactions to model
10. **Verify growth**: Check final growth rate meets target
11. **Transform model ID**: Add `.gf` suffix
12. **Store model**: Save in session storage
13. **Enrich metadata**: Add compound/reaction names from database

### Key Dependencies

- **ModelSEEDpy**: Core gapfilling library
- **MSATPCorrection**: ATP correction workflow
- **MSGapfill**: Genome-scale gapfilling
- **MSBuilder**: Exchange reaction creation
- **DatabaseIndex**: Reaction/compound name lookups

### Media Application

Uses shared media utility (`utils/media.py`) for correct media application:
- Sets exchange reaction bounds from media constraints
- Preserves gapfilled exchange reactions
- Handles compartment mapping (`e0`)

## Performance

**Typical Times** (E. coli on glucose minimal):
- ATP correction: ~3-5 minutes (first time)
- ATP correction reuse: <1 second
- Genome-scale gapfilling: ~5-10 minutes
- **Total (full mode)**: ~8-15 minutes

**Memory Usage**:
- Moderate (~500MB-1GB for E. coli-sized models)

## Testing

See test coverage in:
- `tests/integration/test_build_model_integration.py` (gapfilling tests)
- `tests/integration/test_full_workflow_notebook_replication.py` (end-to-end)
- `tests/integration/test_model_persistence_with_media.py` (with gapfilling)

Demo notebook:
- `examples/tool_demos/gapfill_model_demo.ipynb`

## Typical Workflow

```python
# Step 1: Build model with ATP correction
build_result = await build_model(
    fasta_file_path="genome.faa",
    template="GramNegative",
    model_name="my_organism",
    apply_atp_correction=True  # Creates test conditions
)

# Step 2: Gapfill on glucose (reuses ATP test conditions)
gapfill_result = gapfill_model(
    model_id=build_result["model_id"],  # my_organism.draft
    media_id="glucose_minimal",
    db_index=db_index,
    gapfill_mode="full"  # Will reuse ATP test conditions
)

# Step 3: Run FBA to verify growth
fba_result = run_fba(
    model_id=gapfill_result["model_id"],  # my_organism.draft.gf
    media_id="glucose_minimal",
    db_index=db_index
)

print(f"Growth rate: {fba_result['objective_value']}")  # Should be >= 0.01
```

## Related Tools

- **Previous**: `build_model` - Creates draft model
- **Next**: `run_fba` - Analyzes flux distributions
- **Support**: `build_media` - Creates media conditions

## References

- ModelSEED paper: [Henry et al. 2010](https://www.nature.com/articles/nbt.1672)
- ATP correction: See `docs/ATP_CORRECTION.md`
- Source code: `src/gem_flux_mcp/tools/gapfill_model.py`
