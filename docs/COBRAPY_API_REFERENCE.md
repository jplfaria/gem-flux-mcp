# COBRApy API Reference for Gem-Flux MCP

**Generated**: 2025-10-29
**Purpose**: Verified API signatures for COBRApy used in Gem-Flux MCP

This document provides the **actual** API signatures from COBRApy to ensure correct usage.

---

## cobra.Model - Core Model Class

### Constructor

```python
Model(
    id_or_model=None,  # str or Model instance
    name=None          # Optional model name
)
```

### Key Methods

```python
.optimize(
    objective_sense=None,  # 'max' or 'min'
    raise_error=False      # Whether to raise on infeasibility
) -> Solution

.summary(
    solution=None,  # Use specific solution or last optimization
    fva=None        # Include flux variability analysis
) -> ModelSummary

.copy() -> Model
# Create deep copy of model
```

### Key Attributes

```python
.id                    # Model identifier (str)
.name                  # Model name (str)
.reactions             # DictList of Reaction objects
.metabolites           # DictList of Metabolite objects
.genes                 # DictList of Gene objects
.compartments          # Dict of compartment IDs
.objective             # Current objective function
.objective_direction   # 'max' or 'min'
.medium                # Dict of exchange reaction uptake rates
```

---

## cobra.Reaction - Reaction Class

### Key Attributes

```python
.id                    # Reaction identifier (str)
.name                  # Reaction name (str)
.lower_bound           # Minimum flux (float)
.upper_bound           # Maximum flux (float)
.bounds                # Tuple (lower_bound, upper_bound)
.metabolites           # Dict of {Metabolite: stoichiometry}
.genes                 # FrozenSet of Gene objects
.gene_reaction_rule    # Boolean gene rule (str)
.flux                  # Flux value after optimization (float)
```

### Key Methods

```python
.build_reaction_string(use_metabolite_names=False) -> str
# Returns reaction equation string

.get_compartments() -> set
# Returns set of compartments involved
```

---

## cobra.Metabolite - Metabolite Class

### Key Attributes

```python
.id                    # Metabolite identifier (str)
.name                  # Metabolite name (str)
.formula               # Chemical formula (str)
.charge                # Charge (int)
.compartment           # Compartment ID (str)
.annotation            # Dict of database annotations
```

---

## cobra.Solution - Optimization Result

### Key Attributes

```python
.status                # Optimization status: 'optimal', 'infeasible', 'unbounded'
.objective_value       # Objective value (float) or None
.fluxes                # Series of reaction fluxes
```

### Common Status Values

- `"optimal"` - Solution found
- `"infeasible"` - No feasible solution (model can't achieve objective)
- `"unbounded"` - Objective can increase indefinitely
- `"time_limit"` - Solver timeout

---

## cobra.io - Model I/O Functions

### Save Model to JSON

```python
from cobra.io import save_json_model

save_json_model(
    model,              # Model instance
    filename,           # str, Path, or file handle
    sort=False,         # Sort reactions/metabolites
    pretty=False,       # Pretty-print JSON
    **kwargs            # Additional json.dump() kwargs
) -> None
```

**Example**:
```python
from cobra.io import save_json_model

save_json_model(model, "my_model.json")
save_json_model(model, "my_model.json", pretty=True)  # Pretty-printed
```

### Load Model from JSON

```python
from cobra.io import load_json_model

load_json_model(
    filename            # str, Path, or file handle
) -> Model
```

**Example**:
```python
from cobra.io import load_json_model

model = load_json_model("my_model.json")
```

### Other I/O Formats

```python
from cobra.io import (
    save_matlab_model,   # Save to .mat
    load_matlab_model,   # Load from .mat
    write_sbml_model,    # Save to SBML XML
    read_sbml_model,     # Load from SBML XML
)
```

---

## Common Usage Patterns

### Run FBA

```python
# Basic optimization
solution = model.optimize()

if solution.status == "optimal":
    print(f"Growth rate: {solution.objective_value}")
    print(f"Glucose uptake: {solution.fluxes['EX_glc__D_e']}")
else:
    print(f"Optimization failed: {solution.status}")
```

### Apply Media Constraints

```python
# Manually set exchange reaction bounds
for rxn_id in model.reactions:
    if rxn_id.startswith('EX_'):
        model.reactions.get_by_id(rxn_id).lower_bound = 0  # Block uptake

# Allow specific compounds
model.reactions.get_by_id('EX_glc__D_e').lower_bound = -10  # Allow glucose
model.reactions.get_by_id('EX_o2_e').lower_bound = -20      # Allow oxygen
```

### Copy and Modify Model

```python
# Create working copy
model_copy = model.copy()

# Modify copy without affecting original
model_copy.reactions.get_by_id('PFK').knock_out()
solution = model_copy.optimize()
```

### Get Reaction Information

```python
reaction = model.reactions.get_by_id('PFK')

print(f"Name: {reaction.name}")
print(f"Equation: {reaction.build_reaction_string()}")
print(f"Bounds: {reaction.bounds}")
print(f"Genes: {reaction.genes}")
print(f"GPR: {reaction.gene_reaction_rule}")
```

---

## Audit Results

### ✅ run_fba.py - COMPLIANT

- ✅ Uses `.optimize()` correctly
- ✅ Uses `.reactions` attribute correctly
- ✅ Uses `.metabolites` attribute correctly
- ✅ Uses `.lower_bound` and `.upper_bound` correctly

### ✅ gapfill_model.py - COMPLIANT

- ✅ Uses `.optimize()` correctly
- ✅ Uses `.reactions` attribute correctly
- ✅ Uses `.add_reactions()` correctly (from MSBuilder, not manual)
- ✅ Uses `.lower_bound` and `.upper_bound` correctly

---

## Common Mistakes to Avoid

### ❌ WRONG → ✅ CORRECT

```python
# Accessing reactions
reaction = model.reactions['PFK']                  # ❌ KeyError
reaction = model.reactions.get_by_id('PFK')        # ✅ Correct

# Setting bounds
reaction.bounds = -10, 10                          # ❌ Might not work
reaction.lower_bound = -10
reaction.upper_bound = 10                          # ✅ Correct

# Checking solution
if solution:                                       # ❌ Solution object is truthy
if solution.status == "optimal":                   # ✅ Correct

# Applying media
media.apply_to_model(model)                        # ❌ MSMedia method doesn't exist
constraints = media.get_media_constraints()
for rxn_id, (lb, ub) in constraints.items():
    model.reactions.get_by_id(rxn_id).bounds = (lb, ub)  # ✅ Correct
```

---

## Integration with ModelSEEDpy

ModelSEEDpy classes like `MSBuilder` return COBRApy `Model` objects:

```python
# MSBuilder creates COBRApy models
builder = MSBuilder(genome, template, name)
model = builder.build_base_model("my_model")  # Returns cobra.Model

# Can use COBRApy methods directly
solution = model.optimize()
save_json_model(model, "output.json")
```

---

## API Verification

To verify COBRApy APIs:

```bash
# Check Model methods
uv run python -c "from cobra import Model; print(dir(Model))"

# Check method signature
uv run python -c "import inspect; from cobra import Model; print(inspect.signature(Model.optimize))"

# Check io functions
uv run python -c "from cobra import io; print(dir(io))"
```

---

**Rule**: Always use `.get_by_id()` for accessing reactions/metabolites, and check `solution.status` before using results.
