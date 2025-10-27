# COBRApy Reference for Gem-Flux MCP Server

**Purpose**: Comprehensive reference for using COBRApy (Constraint-Based Reconstruction and Analysis in Python) for flux balance analysis in metabolic models.

**Version**: COBRApy 0.27.0
**Documentation**: https://cobrapy.readthedocs.io/en/latest/

## Table of Contents

1. [Overview](#overview)
2. [Model I/O - JSON Format](#model-io---json-format)
3. [Flux Balance Analysis](#flux-balance-analysis)
4. [Model Manipulation](#model-manipulation)
5. [Batch Operations](#batch-operations)
6. [Best Practices for MCP Server](#best-practices-for-mcp-server)

---

## Overview

COBRApy is the standard Python package for constraint-based metabolic modeling. It provides:
- **FBA (Flux Balance Analysis)**: Optimize metabolic flux distributions
- **Model I/O**: Read/write models in multiple formats (JSON, SBML, YAML, MATLAB)
- **Model manipulation**: Modify reactions, metabolites, constraints
- **Advanced analyses**: FVA, pFBA, knockout studies, media optimization

### Key Concepts

- **Model**: A metabolic network with reactions, metabolites, and genes
- **Reaction**: A biochemical transformation with stoichiometry and bounds
- **Metabolite**: A chemical compound consumed or produced by reactions
- **Objective**: The reaction or combination of reactions to optimize (usually biomass)
- **Flux**: The rate of a reaction (in mmol/gDW/h typically)
- **Bounds**: Lower and upper limits on reaction flux

---

## Model I/O - JSON Format

### Loading Models from JSON

```python
from cobra.io import load_json_model

# Load a model from JSON file
model = load_json_model("path/to/model.json")

# The model is now a cobra.Model object
print(f"Model: {model.id}")
print(f"Reactions: {len(model.reactions)}")
print(f"Metabolites: {len(model.metabolites)}")
print(f"Genes: {len(model.genes)}")
```

**Function Signature**:
```python
def load_json_model(filename: str) -> cobra.Model:
    """Load a cobra model from a JSON file.

    Args:
        filename: Path to JSON file

    Returns:
        cobra.Model: The loaded model
    """
```

### Saving Models to JSON

```python
from cobra.io import save_json_model

# Save model to JSON
save_json_model(model, "output_model.json")

# JSON is human-readable and version-control friendly
```

**Function Signature**:
```python
def save_json_model(model: cobra.Model, filename: str,
                    sort: bool = False, pretty: bool = False) -> None:
    """Save a cobra model as JSON.

    Args:
        model: The model to save
        filename: Output file path
        sort: Sort keys for reproducibility (slower)
        pretty: Pretty-print JSON (larger files)
    """
```

### JSON Format Characteristics

**Advantages**:
- ✅ Human-readable text format
- ✅ Works well with version control (git)
- ✅ Compatible with Escher visualization tool
- ✅ Native COBRApy format (no conversion needed)
- ✅ Preserves all model metadata

**Disadvantages**:
- ❌ Not as widely supported as SBML for other tools
- ❌ Larger file sizes than SBML
- ❌ COBRApy-specific (not a universal standard)

**Use JSON when**:
- Working primarily with COBRApy
- Need version control-friendly format
- Integrating with Escher visualizations
- Prioritizing human readability

**Use SBML when**:
- Sharing models with other tools (MATLAB COBRA, KBase, etc.)
- Need standards compliance
- Interoperating with non-Python tools

### Other I/O Formats Supported

```python
from cobra.io import (
    load_model,          # Auto-detect format
    read_sbml_model,     # SBML format (XML)
    write_sbml_model,    # Export to SBML
    load_matlab_model,   # MATLAB .mat format
    save_matlab_model,   # Export to MATLAB
    load_yaml_model,     # YAML format
    save_yaml_model,     # Export to YAML
)

# Auto-detect format
model = load_model("textbook")  # Load built-in test model
model = load_model("model.xml")  # Auto-detects SBML
model = load_model("model.json")  # Auto-detects JSON
```

---

## Flux Balance Analysis

### Basic FBA with optimize()

```python
# Run FBA
solution = model.optimize()

# Check if optimization succeeded
if solution.status == "optimal":
    print(f"Objective value: {solution.objective_value}")
    print(f"Biomass flux: {solution.fluxes['BIOMASS_Ecoli_core_w_GAM']}")
else:
    print(f"Optimization failed: {solution.status}")
```

**Solution Object Attributes**:
```python
solution.objective_value  # Objective function value (float)
solution.status          # Solver status: 'optimal', 'infeasible', 'unbounded'
solution.fluxes          # pandas.Series of reaction fluxes
solution.shadow_prices   # pandas.Series of metabolite shadow prices
solution.reduced_costs   # pandas.Series of reduced costs
```

### Fast FBA with slim_optimize()

When you only need the objective value (not full flux distribution):

```python
# 10-20x faster than optimize()
objective_value = model.slim_optimize()

# Use this for:
# - Parameter screening
# - Batch optimizations where only objective matters
# - Quick feasibility checks
```

**Performance Comparison**:
```python
import timeit

# Full optimization
timeit.timeit(lambda: model.optimize(), number=100)  # ~147 ms

# Slim optimization
timeit.timeit(lambda: model.slim_optimize(), number=100)  # ~8.9 ms
```

### Interpreting Solutions

```python
solution = model.optimize()

# Access fluxes by reaction ID
glucose_uptake = solution.fluxes['EX_glc__D_e']
print(f"Glucose uptake: {glucose_uptake} mmol/gDW/h")

# Get top fluxes
top_fluxes = solution.fluxes.abs().sort_values(ascending=False).head(10)
print(top_fluxes)

# Find active reactions (non-zero flux)
active_reactions = solution.fluxes[solution.fluxes.abs() > 1e-6]
print(f"Active reactions: {len(active_reactions)}")

# Shadow prices indicate metabolite importance
important_metabolites = solution.shadow_prices.abs().sort_values(ascending=False).head(5)
print("Most important metabolites:", important_metabolites)
```

### Model Summary

```python
# Overall model summary
model.summary()
# Output shows:
# - Objective value
# - Major uptake/secretion fluxes
# - ATP production/consumption

# Metabolite-specific summary
model.metabolites.atp_c.summary()
# Shows all reactions producing/consuming ATP

# Reaction-specific analysis
model.reactions.GAPD.summary()
# Shows reaction equation, bounds, and flux
```

### Changing the Objective

```python
# Set objective by reaction name
model.objective = "ATPM"

# Set objective by reaction object
model.objective = model.reactions.ATPM

# Set objective with coefficient
model.objective = {model.reactions.ATPM: 1.0}

# Multiple objectives (weighted sum)
model.objective = {
    model.reactions.BIOMASS: 1.0,
    model.reactions.ATPM: 0.1
}

# Verify current objective
print(model.objective.expression)
```

### Setting Medium (Exchange Constraints)

```python
# Get current medium
medium = model.medium
print(medium)  # Dict of exchange reaction IDs -> uptake bounds

# Modify medium (IMPORTANT: must retrieve, modify, reassign!)
medium = model.medium
medium['EX_glc__D_e'] = 10.0  # Set glucose uptake to 10 mmol/gDW/h
medium['EX_o2_e'] = 20.0      # Set oxygen uptake to 20
model.medium = medium          # MUST reassign!

# Minimal medium
from cobra.medium import minimal_medium
min_med = minimal_medium(model, 0.1)  # Minimize media for 10% max growth
print(min_med)
```

**Critical Note**: You CANNOT do `model.medium['EX_glc__D_e'] = 10.0` directly. You must:
1. Retrieve: `medium = model.medium`
2. Modify: `medium['EX_glc__D_e'] = 10.0`
3. Reassign: `model.medium = medium`

---

## Model Manipulation

### Modifying Reaction Bounds

```python
# Get a reaction
rxn = model.reactions.ATPM

# Modify bounds
rxn.lower_bound = 0.0
rxn.upper_bound = 1000.0

# Knockout a reaction (set bounds to zero)
rxn.knock_out()

# Check if knocked out
print(rxn.bounds)  # (0.0, 0.0)

# Restore bounds
rxn.lower_bound = -1000.0
```

### Temporary Changes with Context Manager

```python
# Use context manager for temporary modifications
with model:
    model.reactions.ATPM.knock_out()
    solution = model.optimize()
    print(f"Growth without ATPM: {solution.objective_value}")
# After exiting, ATPM bounds are restored automatically

print(f"Normal growth: {model.optimize().objective_value}")
```

### Adding/Removing Reactions

```python
from cobra import Reaction, Metabolite

# Create new metabolite
new_met = Metabolite(
    'new_met_c',
    formula='C6H12O6',
    name='New compound',
    compartment='c'
)

# Create new reaction
new_rxn = Reaction('NEW_RXN')
new_rxn.name = 'My new reaction'
new_rxn.lower_bound = 0.0
new_rxn.upper_bound = 1000.0

# Add metabolites with stoichiometry
new_rxn.add_metabolites({
    model.metabolites.glc__D_c: -1.0,  # Consume glucose
    new_met: 1.0,                       # Produce new_met
    model.metabolites.atp_c: -1.0       # Consume ATP
})

# Add reaction to model
model.add_reactions([new_rxn])

# Remove reaction
model.remove_reactions([new_rxn])
```

### Creating Exchange Reactions

```python
# Add exchange reaction for a metabolite
model.add_boundary(
    model.metabolites.new_met_c,
    type="exchange",  # or "demand", "sink"
    reaction_id="EX_new_met_e",
    lb=-1000.0,  # Uptake allowed
    ub=1000.0    # Secretion allowed
)
```

---

## Batch Operations

### Running Multiple FBA Simulations

```python
# Screen different glucose uptake rates
glucose_rates = [0, 5, 10, 15, 20]
results = []

for rate in glucose_rates:
    with model:  # Temporary changes
        medium = model.medium
        medium['EX_glc__D_e'] = rate
        model.medium = medium
        solution = model.optimize()
        results.append({
            'glucose_rate': rate,
            'growth_rate': solution.objective_value,
            'status': solution.status
        })

import pandas as pd
df = pd.DataFrame(results)
print(df)
```

### Knockout Screening

```python
from cobra.flux_analysis import single_gene_deletion, single_reaction_deletion

# Single gene deletions
gene_deletion_results = single_gene_deletion(model, model.genes[:10])
print(gene_deletion_results)

# Single reaction deletions
reaction_deletion_results = single_reaction_deletion(
    model, model.reactions[:20]
)
print(reaction_deletion_results)

# Double gene deletions (combinatorial)
from cobra.flux_analysis import double_gene_deletion
double_deletion_results = double_gene_deletion(
    model, model.genes[:5]
)
```

### Flux Variability Analysis (FVA)

```python
from cobra.flux_analysis import flux_variability_analysis

# Run FVA on all reactions
fva_result = flux_variability_analysis(model)
print(fva_result)  # DataFrame with 'minimum' and 'maximum' columns

# FVA on specific reactions
fva_result = flux_variability_analysis(
    model,
    reaction_list=model.reactions[:10],
    fraction_of_optimum=0.9  # Require 90% optimal growth
)

# Loopless FVA (more biologically realistic)
fva_loopless = flux_variability_analysis(model, loopless=True)
```

### Parsimonious FBA (pFBA)

```python
from cobra.flux_analysis import pfba

# Minimize total flux while maintaining optimal growth
pfba_solution = pfba(model)

# Compare total flux
standard_solution = model.optimize()
print(f"Standard FBA total flux: {standard_solution.fluxes.abs().sum()}")
print(f"pFBA total flux: {pfba_solution.fluxes.abs().sum()}")
```

### Parallel Processing

```python
from multiprocessing import Pool

def optimize_with_glucose_rate(rate):
    """Helper function for parallel optimization."""
    model_copy = model.copy()
    medium = model_copy.medium
    medium['EX_glc__D_e'] = rate
    model_copy.medium = medium
    solution = model_copy.optimize()
    return {'rate': rate, 'growth': solution.objective_value}

# Run in parallel
glucose_rates = list(range(0, 21))
with Pool(processes=4) as pool:
    results = pool.map(optimize_with_glucose_rate, glucose_rates)

df = pd.DataFrame(results)
```

---

## Best Practices for MCP Server

### 1. Model Caching

```python
# Load models once at server startup
MODEL_CACHE = {}

def get_model(model_id):
    """Load model with caching."""
    if model_id not in MODEL_CACHE:
        MODEL_CACHE[model_id] = load_json_model(f"models/{model_id}.json")
    return MODEL_CACHE[model_id].copy()  # Always return a copy!
```

### 2. Error Handling

```python
def run_fba_safely(model):
    """Run FBA with comprehensive error handling."""
    try:
        solution = model.optimize()

        if solution.status == "optimal":
            return {
                'status': 'success',
                'objective_value': solution.objective_value,
                'fluxes': solution.fluxes.to_dict()
            }
        elif solution.status == "infeasible":
            return {
                'status': 'infeasible',
                'error': 'Model has no feasible solution. Check constraints.'
            }
        elif solution.status == "unbounded":
            return {
                'status': 'unbounded',
                'error': 'Model is unbounded. Check objective and bounds.'
            }
        else:
            return {
                'status': 'failed',
                'error': f'Unknown solver status: {solution.status}'
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }
```

### 3. Input Validation

```python
def validate_medium(medium_dict, model):
    """Validate medium dictionary before applying."""
    errors = []

    for rxn_id, flux in medium_dict.items():
        # Check reaction exists
        if rxn_id not in model.reactions:
            errors.append(f"Reaction {rxn_id} not found in model")
            continue

        # Check it's an exchange reaction
        rxn = model.reactions.get_by_id(rxn_id)
        if not rxn_id.startswith('EX_'):
            errors.append(f"{rxn_id} is not an exchange reaction")

        # Check flux value is valid
        if not isinstance(flux, (int, float)):
            errors.append(f"Invalid flux value for {rxn_id}: {flux}")

        if flux < 0:
            errors.append(f"Flux for {rxn_id} should be positive (uptake bound)")

    return errors
```

### 4. Response Formatting

```python
def format_fba_response(solution, model):
    """Format FBA solution for MCP response."""
    if solution.status != "optimal":
        return {
            'success': False,
            'status': solution.status,
            'objective_value': None,
            'fluxes': {}
        }

    # Only return non-zero fluxes
    significant_fluxes = solution.fluxes[solution.fluxes.abs() > 1e-6]

    return {
        'success': True,
        'status': 'optimal',
        'objective_value': float(solution.objective_value),
        'active_reactions': len(significant_fluxes),
        'fluxes': {
            rxn_id: float(flux)
            for rxn_id, flux in significant_fluxes.items()
        },
        'summary': {
            'total_flux': float(solution.fluxes.abs().sum()),
            'uptake_reactions': len([f for f in significant_fluxes if f < 0]),
            'secretion_reactions': len([f for f in significant_fluxes if f > 0])
        }
    }
```

### 5. Batch Operation Limits

```python
MAX_BATCH_SIZE = 100  # Limit batch operations

def validate_batch_size(items, operation_name):
    """Prevent excessive batch operations."""
    if len(items) > MAX_BATCH_SIZE:
        raise ValueError(
            f"{operation_name} limited to {MAX_BATCH_SIZE} items. "
            f"Received {len(items)}. Please split into smaller batches."
        )
```

---

## Common Use Cases for Gem-Flux MCP Server

### Use Case 1: Build Model and Run FBA

```python
@mcp.tool()
def run_fba(model_json: str, medium: dict) -> dict:
    """Run FBA on a model with specified medium.

    Args:
        model_json: Model as JSON string
        medium: Dict of exchange reactions and uptake bounds

    Returns:
        FBA results with objective value and fluxes
    """
    import json
    import tempfile
    from cobra.io import load_json_model

    # Save JSON to temp file and load
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(model_json)
        temp_path = f.name

    model = load_json_model(temp_path)

    # Apply medium
    model.medium = medium

    # Run FBA
    solution = model.optimize()

    return format_fba_response(solution, model)
```

### Use Case 2: Gapfill and Return Model

```python
@mcp.tool()
def gapfill_model(model_json: str, medium: dict) -> dict:
    """Gapfill model to enable growth in medium.

    Returns model as JSON with added reactions.
    """
    # This would integrate with ModelSEEDpy's gapfilling
    # Then export the gapfilled model as JSON

    from cobra.io import save_json_model
    import tempfile

    # ... gapfilling logic ...

    # Export model to JSON
    with tempfile.NamedTemporaryFile(mode='r', suffix='.json', delete=False) as f:
        save_json_model(gapfilled_model, f.name)
        f.seek(0)
        model_json = f.read()

    return {
        'model_json': model_json,
        'reactions_added': added_reactions,
        'growth_rate': final_growth_rate
    }
```

### Use Case 3: Batch FBA with Different Media

```python
@mcp.tool()
def batch_fba(model_json: str, media_list: list[dict]) -> list[dict]:
    """Run FBA with multiple media compositions.

    Args:
        model_json: Model as JSON string
        media_list: List of medium dicts

    Returns:
        List of FBA results for each medium
    """
    validate_batch_size(media_list, "batch_fba")

    model = load_model_from_json_string(model_json)

    results = []
    for i, medium in enumerate(media_list):
        with model:  # Temporary changes
            model.medium = medium
            solution = model.optimize()
            results.append({
                'medium_index': i,
                'objective_value': solution.objective_value,
                'status': solution.status
            })

    return results
```

---

## Summary

COBRApy provides all the tools needed for the Gem-Flux MCP server's FBA functionality:

✅ **Model I/O**: `load_json_model()`, `save_json_model()` for model persistence
✅ **FBA**: `model.optimize()` for flux balance analysis
✅ **Fast FBA**: `model.slim_optimize()` for batch operations
✅ **Constraints**: `model.medium` for setting exchange bounds
✅ **Batch ops**: Context managers, FVA, knockout screens

**Key Points for MCP Implementation**:
- Always use `model.copy()` when caching models
- Use context managers (`with model:`) for temporary changes
- Remember medium assignment must be: get → modify → reassign
- Return JSON-serializable results (convert pandas Series to dict)
- Validate inputs before applying to models
- Handle infeasible/unbounded solutions gracefully
- Use `slim_optimize()` for batch operations when possible

This reference covers all COBRApy functionality needed for the Gem-Flux MCP server MVP and beyond.
