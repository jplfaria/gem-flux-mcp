# run_fba Tool

## Overview

The `run_fba` tool executes Flux Balance Analysis (FBA) to predict growth rates and metabolic fluxes under specified media conditions. This is the primary analysis tool for examining model behavior.

**Location**: `src/gem_flux_mcp/tools/run_fba.py`

## What It Does

- Executes flux balance analysis (FBA) using COBRApy
- Applies media constraints to exchange reactions
- Optimizes objective function (typically biomass production)
- Returns flux distributions with compound/reaction names
- Identifies uptake and secretion fluxes
- Handles infeasible and unbounded models

## What It Does NOT Do

- Does not modify the model (read-only operation)
- Does not perform flux variability analysis (FVA)
- Does not minimize total flux (pFBA)
- Does not analyze pathway essentiality

## Function Signature

```python
def run_fba(
    model_id: str,
    media_id: str,
    db_index: DatabaseIndex,
    objective: str = "bio1",
    maximize: bool = True,
    flux_threshold: float = 1e-6,
) -> dict[str, Any]
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model_id` | `str` | Yes | - | Model identifier from session storage |
| `media_id` | `str` | Yes | - | Media identifier from session storage |
| `db_index` | `DatabaseIndex` | Yes | - | Database index for name lookups |
| `objective` | `str` | No | `"bio1"` | Objective reaction ID to optimize |
| `maximize` | `bool` | No | `True` | Maximize (True) or minimize (False) |
| `flux_threshold` | `float` | No | `1e-6` | Minimum absolute flux to report |

## Return Value

```python
{
    "success": bool,
    "model_id": str,
    "media_id": str,
    "objective_reaction": str,
    "objective_value": float,  # Growth rate
    "status": str,  # "optimal"
    "solver_status": str,
    "active_reactions": int,
    "total_reactions": int,
    "total_flux": float,
    "fluxes": dict[str, float],  # All significant fluxes
    "uptake_fluxes": [
        {
            "compound_id": str,
            "compound_name": str,
            "flux": float,  # Negative value
            "reaction_id": str
        }
    ],
    "secretion_fluxes": [
        {
            "compound_id": str,
            "compound_name": str,
            "flux": float,  # Positive value
            "reaction_id": str
        }
    ],
    "summary": {
        "uptake_reactions": int,
        "secretion_reactions": int,
        "internal_reactions": int
    },
    "top_fluxes": [
        {
            "reaction_id": str,
            "reaction_name": str,
            "flux": float,
            "direction": str  # "forward" or "reverse"
        }
    ]
}
```

## Usage Examples

### Example 1: Basic FBA

```python
from gem_flux_mcp.tools.run_fba import run_fba

result = run_fba(
    model_id="ecoli_model.draft.gf",
    media_id="glucose_minimal",
    db_index=db_index
)

print(f"Growth rate: {result['objective_value']:.4f}")
print(f"Active reactions: {result['active_reactions']}/{result['total_reactions']}")
```

### Example 2: Analyzing Uptake and Secretion

```python
result = run_fba(
    model_id="ecoli_model.draft.gf",
    media_id="glucose_minimal",
    db_index=db_index,
    flux_threshold=0.001  # Higher threshold for major fluxes
)

print("Uptake fluxes:")
for flux in result['uptake_fluxes']:
    print(f"  {flux['compound_name']}: {abs(flux['flux']):.2f}")

print("\nSecretion fluxes:")
for flux in result['secretion_fluxes']:
    print(f"  {flux['compound_name']}: {flux['flux']:.2f}")
```

### Example 3: ATP Maintenance Optimization

```python
# Minimize ATP maintenance
result = run_fba(
    model_id="ecoli_model.draft.gf",
    media_id="glucose_minimal",
    db_index=db_index,
    objective="ATPM_c0",
    maximize=False  # Minimize ATP consumption
)

print(f"Minimum ATP required: {result['objective_value']:.4f}")
```

## Understanding FBA Results

### Growth Rate (objective_value)

For E. coli on glucose minimal media:
- **0.5544**: Expected growth rate (matches experimental data)
- **0.0**: No growth (model needs gapfilling)
- **>1.0**: Unrealistic (model may need constraints)

### Uptake Fluxes (Negative Values)

Compounds entering the cell:
- Glucose (cpd00027): Carbon source
- Oxygen (cpd00007): Electron acceptor
- Phosphate (cpd00009): Biomass precursor
- Ammonium (cpd00013): Nitrogen source

### Secretion Fluxes (Positive Values)

Compounds leaving the cell:
- CO2 (cpd00011): Respiration byproduct
- H2O (cpd00001): Metabolic byproduct
- Protons (cpd00067): Maintains pH balance

## Error Handling

### MODEL_INFEASIBLE

Model cannot grow in specified media.

```python
{
    "error_code": "MODEL_INFEASIBLE",
    "message": "Model has no feasible solution in the specified media",
    "suggestions": [
        "Model may need gapfilling. Use gapfill_model tool first",
        "Check that media contains essential nutrients (C, N, P, S sources)",
        "Verify exchange reactions exist for media compounds"
    ]
}
```

**Solution**: Gapfill the model or use richer media.

### MODEL_UNBOUNDED

Objective can grow infinitely (model error).

```python
{
    "error_code": "MODEL_UNBOUNDED",
    "message": "Model objective is unbounded (can grow infinitely)",
    "details": {
        "unbounded_exchanges": ["EX_cpd00027_e0", "EX_cpd00007_e0"]
    },
    "suggestions": [
        "Check that all exchange reactions have finite bounds",
        "Verify media was applied correctly",
        "This indicates a model error - rebuild the model"
    ]
}
```

**Solution**: Rebuild the model - this indicates a serious error.

### INVALID_OBJECTIVE

Specified objective reaction not found in model.

```python
{
    "error_code": "INVALID_OBJECTIVE",
    "message": "Objective reaction 'bio99' not found in model",
    "suggestions": [
        "Use 'bio1' for growth optimization",
        "Use 'ATPM_c0' for ATP maintenance"
    ]
}
```

**Solution**: Use valid objective reaction ID (typically "bio1").

## Media Application

FBA applies media constraints using the shared media utility:

1. **Resets exchange bounds** (optional): Closes all exchanges
2. **Applies media constraints**: Opens exchanges from media definition
3. **Preserves gapfilled exchanges**: Keeps reactions added during gapfilling
4. **Sets compartment**: Maps to extracellular space ("e0")

**Important**: Use `reset_exchange_bounds=False` for gapfilled models to preserve gapfilled exchanges.

## Flux Threshold

The `flux_threshold` parameter filters negligible fluxes:

| Threshold | Interpretation | Use Case |
|-----------|---------------|----------|
| `1e-9` | Include nearly all fluxes | Detailed analysis |
| `1e-6` | Standard threshold (default) | Normal analysis |
| `1e-3` | Major fluxes only | High-level overview |
| `0.1` | Very significant fluxes | Summary analysis |

**Recommendation**: Use default `1e-6` for most analyses.

## Implementation Details

### Workflow Steps

1. Validate inputs (model/media exist, valid parameters)
2. Load model and media from session storage
3. Create working copy (preserve original)
4. Apply media constraints to exchange reactions
5. Verify objective reaction exists
6. Set objective function and direction
7. Execute FBA optimization
8. Check solution status (optimal/infeasible/unbounded)
9. Extract and filter fluxes by threshold
10. Separate uptake/secretion fluxes
11. Query database for compound/reaction names
12. Build response with organized flux data

### Key Dependencies

- **COBRApy**: FBA optimization engine
- **DatabaseIndex**: Compound/reaction name lookups
- **Media Utility**: Correct media application

## Performance

**Typical Times**:
- Small models (<500 reactions): <100ms
- E. coli-sized models (~2000 reactions): <500ms
- Large models (>5000 reactions): 1-2 seconds

**Memory Usage**: Minimal (~50MB additional)

## Testing

See test coverage in:
- `tests/integration/test_full_workflow_notebook_replication.py`
- `tests/integration/test_model_persistence_with_media.py`

## Typical Workflow

```python
# Step 1: Build and gapfill model
build_result = await build_model(...)
gapfill_result = gapfill_model(...)

# Step 2: Run FBA
fba_result = run_fba(
    model_id=gapfill_result["model_id"],
    media_id="glucose_minimal",
    db_index=db_index
)

# Step 3: Analyze results
print(f"Growth rate: {fba_result['objective_value']:.4f}")
print(f"Glucose uptake: {abs(fba_result['uptake_fluxes'][0]['flux']):.2f}")

# Step 4: Export fluxes for visualization
import json
with open("fluxes.json", "w") as f:
    json.dump(fba_result['fluxes'], f)
```

## Related Tools

- **Previous**: `gapfill_model` - Enables growth
- **Support**: `build_media` - Creates media conditions
- **Data**: `compound_lookup`, `reaction_lookup` - Metadata queries

## References

- FBA method: [Orth et al. 2010](https://www.nature.com/articles/nbt.1614)
- COBRApy: [Ebrahim et al. 2013](https://doi.org/10.1186/1752-0509-7-74)
- Source code: `src/gem_flux_mcp/tools/run_fba.py`
