# ModelSEEDpy + COBRApy Compatibility Guide

## Purpose

This document provides detailed technical guidance for teams building genome-scale metabolic models with ModelSEEDpy and running FBA simulations with COBRApy. It focuses on two major compatibility challenges that cause runtime errors and unexpected behavior.

**Target Audience**: Computational biologists and bioinformaticians performing metabolic modeling, gapfilling, and flux balance analysis across multiple media conditions.

**Key Use Cases**:
- Building draft genome-scale models from genomes
- Gapfilling models to grow on specific carbon sources
- Running FBA simulations across diverse media formulations
- Integrating gapfilling solutions into working models

---

## Challenge #1: Compartment Suffix Mismatch

### The Problem

**Symptom**: After running ModelSEEDpy gapfilling successfully, you attempt to integrate the gapfill solution by adding reactions to your COBRApy model. The code fails with `KeyError` when looking up reactions in the template.

**Example Error**:
```
KeyError: 'rxn05481_c0'
# When trying: template.reactions.get_by_id('rxn05481_c0')
```

**What's Happening**: ModelSEEDpy gapfilling returns reaction IDs with indexed compartment suffixes (`_c0`, `_e0`), but the ModelSEED biochemistry template stores reactions with non-indexed suffixes (`_c`, `_e`).

**Impact**: Cannot integrate gapfilling solutions into models without manual ID conversion.

### Root Cause Explanation

**ModelSEEDpy Compartment Indexing**:
- ModelSEEDpy uses **indexed compartments** when building models: `_c0`, `_e0`, `_p0`
- This allows multiple instances of the same compartment (e.g., `_c0` and `_c1` for two different cytoplasms)
- Design rationale: Support multi-organism community models where each organism has separate compartments

**ModelSEED Template Storage**:
- The ModelSEED biochemistry template stores reactions with **non-indexed compartments**: `_c`, `_e`, `_p`
- Template reactions are abstract definitions used across all models
- Examples: `rxn05481_c` (glucose-6-phosphate isomerase), `rxn00062_c` (succinate dehydrogenase)

**Why the Mismatch Occurs**:
1. ModelSEEDpy builds your model with indexed compartments (`metabolite_c0`, `reaction_c0`)
2. Gapfilling identifies missing reactions needed for growth
3. Gapfilling returns solution with indexed IDs: `{'rxn05481_c0': '>', 'rxn00062_c0': '>'}`
4. You try to look up `rxn05481_c0` in the template to get reaction details
5. Template only has `rxn05481_c` → KeyError

### The Solution

**Core Pattern**: Strip the trailing `0` from compartment suffixes when looking up reactions in the template.

**Implementation**:

```python
def integrate_gapfill_solution(template, model, gapfill_result):
    """
    Integrate gapfill solution by adding reactions from template to model.

    Parameters:
    -----------
    template : cobra.Model
        ModelSEED template model (reactions have _c, _e suffixes)
    model : cobra.Model
        Your organism-specific model (reactions have _c0, _e0 suffixes)
    gapfill_result : dict
        Result from ModelSEEDpy gapfilling, format:
        {
            'new': {'rxn05481_c0': '>', 'rxn00062_c0': '<', ...},
            'reversed': {...},
            ...
        }

    Returns:
    --------
    list : Added cobra.Reaction objects
    """
    added_reactions = []
    gap_sol = {}

    # Process gapfill solution
    for rxn_id, direction in gapfill_result.get('new', {}).items():
        # Skip exchange reactions (added separately)
        if rxn_id.startswith('EX_'):
            continue

        # Convert indexed compartment to non-indexed for template lookup
        # rxn05481_c0 → rxn05481_c
        # rxn00062_e0 → rxn00062_e
        if rxn_id.endswith('0'):
            template_rxn_id = rxn_id[:-1]  # Remove trailing '0'
        else:
            template_rxn_id = rxn_id  # Already non-indexed

        # Verify reaction exists in template
        if template_rxn_id not in template.reactions:
            print(f"Warning: {template_rxn_id} not found in template")
            continue

        # Get reaction bounds from direction
        lb, ub = get_reaction_constraints_from_direction(direction)
        gap_sol[template_rxn_id] = (lb, ub)

    # Add reactions to model
    for rxn_id, (lb, ub) in gap_sol.items():
        # Get reaction from template
        template_reaction = template.reactions.get_by_id(rxn_id)

        # Convert to model format (this handles compartment indexing)
        # Template rxn05481_c becomes model rxn05481_c0
        model_reaction = template_reaction.copy()
        model_reaction.lower_bound = lb
        model_reaction.upper_bound = ub

        # Add to model
        model.add_reactions([model_reaction])
        added_reactions.append(model_reaction)

    return added_reactions


def get_reaction_constraints_from_direction(direction):
    """
    Convert ModelSEEDpy direction symbol to COBRApy bounds.

    Parameters:
    -----------
    direction : str
        '>' : forward only (e.g., A → B)
        '<' : reverse only (e.g., A ← B)
        '=' : reversible (e.g., A ⇌ B)

    Returns:
    --------
    tuple : (lower_bound, upper_bound)
    """
    if direction == '>':
        return (0, 1000)      # Forward only
    elif direction == '<':
        return (-1000, 0)     # Reverse only
    elif direction == '=':
        return (-1000, 1000)  # Reversible
    else:
        raise ValueError(f"Unknown direction: {direction}")
```

### Common Mistakes

**Mistake #1: Using gapfill IDs directly with template**
```python
# WRONG - will fail with KeyError
for rxn_id in gapfill_result['new']:
    template_rxn = template.reactions.get_by_id(rxn_id)  # KeyError!
```

**Mistake #2: Removing compartment suffix entirely**
```python
# WRONG - removes too much
template_rxn_id = rxn_id.split('_')[0]  # 'rxn05481_c0' → 'rxn05481'
# Template needs: 'rxn05481_c' not 'rxn05481'
```

**Mistake #3: Hardcoding compartment types**
```python
# WRONG - assumes all reactions are cytoplasmic
template_rxn_id = rxn_id.replace('_c0', '_c')
# Fails for periplasmic (_p0) or extracellular (_e0) reactions
```

**Correct Pattern**:
```python
# RIGHT - strips trailing '0' only, preserves compartment type
if rxn_id.endswith('0'):
    template_rxn_id = rxn_id[:-1]  # Handles _c0, _e0, _p0, etc.
```

### Testing Your Implementation

**Test Case 1: Cytoplasmic Reaction**
```python
gapfill_result = {'new': {'rxn05481_c0': '>'}}
# Should look up: 'rxn05481_c' in template
# Should add: 'rxn05481_c0' to model
```

**Test Case 2: Extracellular Reaction**
```python
gapfill_result = {'new': {'rxn00062_e0': '<'}}
# Should look up: 'rxn00062_e' in template
# Should add: 'rxn00062_e0' to model
```

**Test Case 3: Mixed Compartments**
```python
gapfill_result = {
    'new': {
        'rxn05481_c0': '>',
        'rxn00062_e0': '<',
        'rxn09876_p0': '='
    }
}
# Should handle all three compartment types correctly
```

**Validation Code**:
```python
def validate_gapfill_integration(template, model, gapfill_result):
    """Test that all gapfilled reactions can be found and added."""
    errors = []

    for rxn_id in gapfill_result.get('new', {}).keys():
        if rxn_id.startswith('EX_'):
            continue

        # Convert to template ID
        template_rxn_id = rxn_id[:-1] if rxn_id.endswith('0') else rxn_id

        # Check template has reaction
        if template_rxn_id not in template.reactions:
            errors.append(f"Template missing: {template_rxn_id}")

        # Check compartment suffix handling
        if not template_rxn_id.endswith(('_c', '_e', '_p')):
            errors.append(f"Invalid template suffix: {template_rxn_id}")

    if errors:
        print("Validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print(f"Validation PASSED: {len(gapfill_result.get('new', {}))} reactions")
        return True
```

### Why This Matters

**Without proper handling**:
- Gapfilling succeeds but integration fails
- Hours of compute time wasted on gapfilling
- Cannot test if gapfilled model actually grows
- Difficult to debug (error occurs far from root cause)

**With proper handling**:
- Seamless workflow from gapfilling → model integration → FBA
- Can iterate rapidly on different media conditions
- Reproducible model building pipeline
- Clear separation between template and model namespaces

---

## Challenge #2: Media Format Conversion

### The Problem

**Symptom**: You have media formulations stored in ModelSEED JSON format (from ModelSEED database or custom media files). When you try to apply them to COBRApy models for FBA simulations, the media doesn't work correctly or you get unexpected errors.

**Example Error**:
```
# Media file contains: {'cpd00007': [-10, 100], 'cpd00001': [-10, 100]}
# You try: model.medium = media_dict
# Result: No effect or KeyError - model doesn't recognize compound IDs
```

**What's Happening**: ModelSEED media files use **compound IDs** with **negative uptake rates**, while COBRApy models need **exchange reaction IDs** with **positive uptake rates**.

**Impact**: Cannot use published media formulations or share media definitions across tools.

### Root Cause Explanation

**ModelSEED Media Format**:
- Uses **compound IDs**: `cpd00007` (oxygen), `cpd00001` (water), `cpd00027` (glucose)
- Stores **[min_flux, max_flux]** bounds: `[-10, 100]` means uptake up to 10, secretion up to 100
- Negative values indicate **uptake** (into cell), positive indicate **secretion** (out of cell)
- Unitless flux rates (typically mmol/gDW/hr assumed)

**Example ModelSEED Media File** (`glucose_minimal.json`):
```json
{
  "cpd00027": [-10, 100],   // Glucose: uptake 10, secrete 100
  "cpd00001": [-100, 100],  // H2O: unlimited exchange
  "cpd00007": [-100, 100],  // O2: unlimited exchange
  "cpd00009": [-100, 100],  // Phosphate: unlimited exchange
  "cpd00011": [-100, 100],  // CO2: unlimited exchange
  "cpd00012": [-100, 100],  // NH3: unlimited exchange
  "cpd00034": [-100, 100],  // Zn2+: unlimited exchange
  "cpd00058": [-100, 100],  // Cu2+: unlimited exchange
  "cpd00099": [-100, 100]   // Cl-: unlimited exchange
}
```

**COBRApy Medium Format**:
- Uses **exchange reaction IDs**: `EX_cpd00007_e0`, `EX_cpd00001_e0`, `EX_cpd00027_e0`
- Stores **positive uptake rates only**: `{'EX_cpd00027_e0': 10}` means uptake 10
- Exchange reactions are **special reaction objects** in the model
- Format: `model.medium = {'EX_rxn_id': uptake_rate, ...}`

**Why the Mismatch Occurs**:
1. Media files from ModelSEED database use compound IDs + negative rates
2. COBRApy models use exchange reaction IDs + positive rates
3. Exchange reaction naming isn't standardized (multiple possible formats)
4. Not all compounds have corresponding exchange reactions in all models
5. Models may be missing expected exchange reactions (especially trace metals)

### The Solution

**Core Pattern**: Convert compound IDs → exchange reaction IDs, flip negative rates to positive, handle missing exchanges gracefully.

**Implementation**:

```python
def convert_media_to_model_format(media_dict, model, default_uptake=10):
    """
    Convert ModelSEED media format to COBRApy model format.

    Parameters:
    -----------
    media_dict : dict
        ModelSEED format: {'cpd00027': [-10, 100], 'cpd00001': [-100, 100], ...}
        Negative values = uptake, positive = secretion

    model : cobra.Model
        COBRApy model with exchange reactions

    default_uptake : float
        Default uptake rate if bounds are unlimited (default: 10)

    Returns:
    --------
    dict : COBRApy format {'EX_cpd00027_e0': 10, 'EX_cpd00001_e0': 100, ...}
    list : Compound IDs that couldn't be matched to exchange reactions

    Notes:
    ------
    - Tries multiple exchange reaction naming formats
    - Handles both list bounds [min, max] and single values
    - Reports missing exchanges for debugging
    """
    model_media = {}
    missing_exchanges = []

    for cpd_id, bounds in media_dict.items():
        # Extract uptake rate from bounds
        if isinstance(bounds, list):
            min_flux, max_flux = bounds
            # Use absolute value of minimum (negative = uptake)
            uptake_rate = abs(min_flux)

            # Handle unlimited uptake (-100 or -1000 often means unlimited)
            if uptake_rate >= 100:
                uptake_rate = default_uptake
        else:
            # Single value (some files use this format)
            uptake_rate = abs(bounds)

        # Try multiple exchange reaction formats
        # Format preference order based on ModelSEEDpy conventions
        possible_exchange_ids = [
            f"EX_{cpd_id}_e0",    # Most common: EX_cpd00027_e0
            f"EX_{cpd_id}_e",     # Alternative: EX_cpd00027_e
            f"EX_{cpd_id}(e)",    # Old format: EX_cpd00027(e)
            f"{cpd_id}_e0",       # Minimal: cpd00027_e0
            f"{cpd_id}_e",        # Minimal alt: cpd00027_e
        ]

        # Try each format until we find a match
        found = False
        for ex_id in possible_exchange_ids:
            if ex_id in model.reactions:
                model_media[ex_id] = uptake_rate
                found = True
                break

        # Track compounds without exchange reactions
        if not found:
            missing_exchanges.append(cpd_id)

    return model_media, missing_exchanges


def load_media_from_file(media_filepath, model, report_missing=True):
    """
    Load ModelSEED media JSON file and convert to COBRApy format.

    Parameters:
    -----------
    media_filepath : str
        Path to ModelSEED media JSON file

    model : cobra.Model
        COBRApy model to apply media to

    report_missing : bool
        Print warning about missing exchange reactions

    Returns:
    --------
    dict : COBRApy media format

    Example:
    --------
    >>> media = load_media_from_file('glucose_minimal.json', model)
    >>> model.medium = media
    >>> solution = model.optimize()
    """
    import json

    # Load ModelSEED format
    with open(media_filepath, 'r') as f:
        modelseed_media = json.load(f)

    # Convert to COBRApy format
    cobra_media, missing = convert_media_to_model_format(modelseed_media, model)

    # Report missing exchanges
    if report_missing and missing:
        print(f"Warning: {len(missing)} compounds lack exchange reactions:")
        print(f"  {', '.join(missing[:10])}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")

    return cobra_media


def apply_media_and_simulate(model, media_filepath, carbon_source_name):
    """
    Complete workflow: load media, apply to model, run FBA.

    Parameters:
    -----------
    model : cobra.Model
        COBRApy model (will be copied, original unchanged)

    media_filepath : str
        Path to ModelSEED media JSON file

    carbon_source_name : str
        Name of carbon source for reporting

    Returns:
    --------
    dict : {
        'carbon_source': str,
        'growth_rate': float,
        'status': str,
        'missing_exchanges': list
    }
    """
    import json
    from copy import deepcopy

    # Copy model to avoid modifying original
    test_model = deepcopy(model)

    # Load media
    with open(media_filepath, 'r') as f:
        modelseed_media = json.load(f)

    # Convert format
    cobra_media, missing = convert_media_to_model_format(
        modelseed_media,
        test_model
    )

    # Apply media
    test_model.medium = cobra_media

    # Run FBA
    solution = test_model.optimize()

    return {
        'carbon_source': carbon_source_name,
        'growth_rate': solution.objective_value if solution.status == 'optimal' else 0.0,
        'status': solution.status,
        'missing_exchanges': missing
    }
```

### Common Mistakes

**Mistake #1: Using compound IDs directly as medium**
```python
# WRONG - model doesn't recognize compound IDs
media = {'cpd00027': 10, 'cpd00001': 100}
model.medium = media  # No effect or KeyError
```

**Mistake #2: Forgetting to flip sign of uptake rates**
```python
# WRONG - negative rates in COBRApy format
media = {'EX_cpd00027_e0': -10}  # Should be positive!
model.medium = media  # May cause unexpected behavior
```

**Mistake #3: Assuming single exchange reaction format**
```python
# WRONG - assumes all models use _e0 format
ex_id = f"EX_{cpd_id}_e0"
model.medium = {ex_id: 10}  # Fails if model uses _e or (e) format
```

**Mistake #4: Not handling missing exchange reactions**
```python
# WRONG - crashes on first missing exchange
for cpd_id, bounds in media.items():
    ex_id = f"EX_{cpd_id}_e0"
    model.medium[ex_id] = abs(bounds[0])  # KeyError if missing!
```

**Correct Pattern**:
```python
# RIGHT - comprehensive media conversion
media_dict = load_media_file('glucose_minimal.json')
cobra_media, missing = convert_media_to_model_format(media_dict, model)
model.medium = cobra_media  # Safe, handles all edge cases
```

### Testing Your Implementation

**Test Case 1: Basic Glucose Minimal Media**
```python
# ModelSEED format
media_modelseed = {
    'cpd00027': [-10, 100],   # Glucose
    'cpd00001': [-100, 100],  # H2O
    'cpd00007': [-100, 100],  # O2
}

# Expected COBRApy format
media_expected = {
    'EX_cpd00027_e0': 10,
    'EX_cpd00001_e0': 10,   # Capped at default
    'EX_cpd00007_e0': 10,
}

# Test conversion
media_result, missing = convert_media_to_model_format(media_modelseed, model)
assert media_result == media_expected
assert len(missing) == 0
```

**Test Case 2: Media with Missing Exchange Reactions**
```python
# Media includes trace metal not in model
media_modelseed = {
    'cpd00027': [-10, 100],   # Glucose - has exchange
    'cpd00058': [-1, 100],    # Cu2+ - missing exchange
}

# Should handle gracefully
media_result, missing = convert_media_to_model_format(media_modelseed, model)
assert 'EX_cpd00027_e0' in media_result
assert 'cpd00058' in missing
assert len(missing) == 1
```

**Test Case 3: Multiple Exchange Reaction Formats**
```python
# Model with non-standard exchange reactions
model_alt = create_model_with_old_exchange_format()
# Has: EX_cpd00027(e) instead of EX_cpd00027_e0

media_modelseed = {'cpd00027': [-10, 100]}

# Should still work
media_result, missing = convert_media_to_model_format(media_modelseed, model_alt)
assert len(media_result) == 1  # Found alternative format
assert len(missing) == 0
```

**Validation Code**:
```python
def validate_media_conversion(media_filepath, model):
    """
    Comprehensive validation of media conversion.

    Checks:
    - All rates are positive
    - All IDs are exchange reactions in model
    - Model can optimize with applied media
    """
    import json

    # Load and convert
    with open(media_filepath, 'r') as f:
        media_modelseed = json.load(f)

    cobra_media, missing = convert_media_to_model_format(media_modelseed, model)

    # Check 1: All rates positive
    negative_rates = [k for k, v in cobra_media.items() if v < 0]
    if negative_rates:
        print(f"ERROR: Negative rates found: {negative_rates}")
        return False

    # Check 2: All IDs are in model
    invalid_ids = [k for k in cobra_media.keys() if k not in model.reactions]
    if invalid_ids:
        print(f"ERROR: Invalid exchange IDs: {invalid_ids}")
        return False

    # Check 3: Model can optimize
    try:
        test_model = model.copy()
        test_model.medium = cobra_media
        solution = test_model.optimize()

        if solution.status != 'optimal':
            print(f"WARNING: Model status {solution.status} with media")
    except Exception as e:
        print(f"ERROR: Optimization failed: {e}")
        return False

    # Report results
    print(f"Validation PASSED:")
    print(f"  - {len(cobra_media)} exchange reactions set")
    print(f"  - {len(missing)} compounds missing exchanges")
    print(f"  - Growth rate: {solution.objective_value:.4f}")

    return True
```

### Handling Missing Exchange Reactions

**Expected Scenario**: Some compounds in media files may not have corresponding exchange reactions in organism-specific models.

**Common Reasons**:
- Draft models often lack exchange reactions for micronutrients
- Organism may not use certain compounds (organism-specific biology)
- Exchange reactions may use non-standard naming

**Recommended Approach**:

```python
def analyze_missing_exchanges(media_filepath, model):
    """
    Identify which compounds lack exchange reactions.

    Returns categorized list for troubleshooting.
    """
    import json

    with open(media_filepath, 'r') as f:
        media_dict = json.load(f)

    cobra_media, missing = convert_media_to_model_format(media_dict, model)

    print(f"Missing Exchange Reactions: {len(missing)}")
    if missing:
        print(f"  Compounds: {', '.join(missing[:10])}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")

    return missing
```

**Decision Tree for Missing Exchanges**:
```
Missing exchange reactions found
│
├─ Expected micronutrients or trace elements?
│  └─ Often safe: organism may not require these
│
├─ Major carbon/nitrogen/phosphorus sources?
│  └─ PROBLEM: May cause incorrect growth predictions
│     → Verify compound mapping is correct
│     → Consider adding exchange reactions manually
│     → Check if organism actually uses this compound
│
└─ Large number of missing exchanges (>50% of media)?
   └─ PROBLEM: Model/media format mismatch
      → Verify exchange reaction naming conventions
      → Check ModelSEED template version compatibility
```

### Why This Matters

**Without proper conversion**:
- Cannot use published media formulations from ModelSEED
- Cannot share media definitions across projects
- Difficult to reproduce growth phenotypes from literature
- Errors are silent (wrong medium applied but no error message)

**With proper conversion**:
- Seamless integration with ModelSEED database (1000+ media formulations)
- Reproducible FBA simulations across labs
- Can systematically test models on diverse conditions
- Clear error reporting for missing exchanges

---

## Integration Example: Complete Workflow

Here's how Challenges #1 and #2 work together in a complete model building and simulation workflow:

```python
from cobra.io import load_model, save_model
import json
from pathlib import Path

def complete_gapfill_and_test_workflow(
    genome_id,
    template_path,
    carbon_sources_dir,
    output_dir
):
    """
    Complete workflow demonstrating both compatibility challenges.

    Steps:
    1. Build draft model from genome
    2. Gapfill on multiple carbon sources
    3. Integrate gapfill solutions (Challenge #1)
    4. Test growth on all carbon sources (Challenge #2)

    Parameters:
    -----------
    genome_id : str
        Genome ID (e.g., '511145.12' for E. coli K-12)
    template_path : str
        Path to ModelSEED template model
    carbon_sources_dir : str
        Directory containing ModelSEED media JSON files
    output_dir : str
        Directory to save results
    """
    from modelseedpy import MSBuilder, MSGapfill
    import pandas as pd

    # Step 1: Build draft model
    print(f"Building draft model for {genome_id}...")
    builder = MSBuilder.from_genome(genome_id)
    draft_model = builder.build()

    # Load template for gapfilling
    template = load_model(template_path)

    # Step 2: Gapfill on each carbon source
    print(f"\nGapfilling on {len(carbon_sources)} carbon sources...")
    gapfill_results = {}

    for carbon_source_file in Path(carbon_sources_dir).glob('*.json'):
        carbon_source = carbon_source_file.stem

        # Load media
        with open(carbon_source_file, 'r') as f:
            media_dict = json.load(f)

        # Gapfill
        gapfiller = MSGapfill(
            draft_model.copy(),
            default_excretion=100,
            default_uptake=10
        )

        gapfill_solution = gapfiller.run_gapfilling(
            media=media_dict,
            target='bio1'  # Biomass reaction
        )

        gapfill_results[carbon_source] = gapfill_solution

    # Step 3: Integrate gapfill solutions (CHALLENGE #1)
    print(f"\nIntegrating gapfill solutions into model...")
    integrated_model = draft_model.copy()

    all_reactions_to_add = {}
    for carbon_source, gapfill_result in gapfill_results.items():
        for rxn_id, direction in gapfill_result.get('new', {}).items():
            if rxn_id.startswith('EX_'):
                continue

            # CHALLENGE #1 SOLUTION: Convert indexed to non-indexed
            if rxn_id.endswith('0'):
                template_rxn_id = rxn_id[:-1]
            else:
                template_rxn_id = rxn_id

            # Track reactions
            if template_rxn_id not in all_reactions_to_add:
                lb, ub = get_reaction_constraints_from_direction(direction)
                all_reactions_to_add[template_rxn_id] = (lb, ub)

    # Add all unique reactions to model
    for rxn_id, (lb, ub) in all_reactions_to_add.items():
        if rxn_id in template.reactions:
            template_rxn = template.reactions.get_by_id(rxn_id)
            model_rxn = template_rxn.copy()
            model_rxn.lower_bound = lb
            model_rxn.upper_bound = ub
            integrated_model.add_reactions([model_rxn])

    print(f"Added {len(all_reactions_to_add)} unique reactions from gapfilling")

    # Step 4: Test growth on all carbon sources (CHALLENGE #2)
    print(f"\nTesting growth on all carbon sources...")
    results = []

    for carbon_source_file in Path(carbon_sources_dir).glob('*.json'):
        carbon_source = carbon_source_file.stem

        # CHALLENGE #2 SOLUTION: Convert media format
        test_result = apply_media_and_simulate(
            integrated_model,
            str(carbon_source_file),
            carbon_source
        )

        results.append(test_result)

    # Save results
    results_df = pd.DataFrame(results)
    output_path = Path(output_dir) / f'{genome_id}_growth_predictions.csv'
    results_df.to_csv(output_path, index=False)

    # Summary statistics
    print(f"\n=== Results Summary ===")
    print(f"Total carbon sources tested: {len(results)}")
    print(f"Growth predicted: {(results_df['growth_rate'] > 0.01).sum()}")
    print(f"No growth predicted: {(results_df['growth_rate'] <= 0.01).sum()}")
    print(f"Average growth rate: {results_df['growth_rate'].mean():.4f}")
    print(f"\nResults saved to: {output_path}")

    return integrated_model, results_df


# Example usage
if __name__ == '__main__':
    model, results = complete_gapfill_and_test_workflow(
        genome_id='511145.12',  # E. coli K-12
        template_path='template_gramneg.sbml',
        carbon_sources_dir='media/',
        output_dir='results/'
    )
```

**Key Takeaways**:
1. Challenge #1 (compartment suffix) arises during gapfill integration (Step 3)
2. Challenge #2 (media format) arises during FBA simulation (Step 4)
3. Both must be handled correctly for reproducible results
4. Proper error handling enables debugging complex workflows
5. Clear separation of concerns (gapfilling vs simulation) helps isolate issues

---

## Summary Checklist

Use this checklist when building metabolic modeling pipelines:

### Challenge #1: Compartment Suffixes
- [ ] Strip trailing `0` from gapfill reaction IDs before template lookup
- [ ] Use `rxn_id[:-1]` pattern (works for all compartment types)
- [ ] Don't hardcode compartment types (`_c`, `_e`, etc.)
- [ ] Validate all gapfilled reactions exist in template before integration
- [ ] Test with reactions from multiple compartments

### Challenge #2: Media Format Conversion
- [ ] Convert compound IDs to exchange reaction IDs
- [ ] Flip negative uptake rates to positive values
- [ ] Try multiple exchange reaction naming formats
- [ ] Handle missing exchange reactions gracefully
- [ ] Track and report which compounds lack exchanges
- [ ] Validate converted media works (model optimizes)
- [ ] Categorize missing exchanges (trace metals vs nutrients)

### General Best Practices
- [ ] Copy models before modification (preserve originals)
- [ ] Log all conversion steps for debugging
- [ ] Write validation functions to catch errors early
- [ ] Document expected vs actual exchange reaction formats
- [ ] Test edge cases (unlimited bounds, missing exchanges, etc.)
- [ ] Save intermediate results for reproducibility

---

## Additional Resources

**ModelSEED Biochemistry Database**:
- https://github.com/ModelSEED/ModelSEEDDatabase
- Compound definitions, reaction templates, media formulations

**COBRApy Documentation**:
- https://cobrapy.readthedocs.io/
- Medium constraints, FBA methods, exchange reactions

**ModelSEEDpy GitHub**:
- https://github.com/ModelSEED/ModelSEEDpy
- Gapfilling implementation, compartment indexing rationale

**Common ModelSEED Compounds**:
- cpd00027: D-Glucose
- cpd00001: H2O
- cpd00007: O2
- cpd00011: CO2
- cpd00009: Phosphate
- cpd00012: NH3 (ammonia)
- cpd00034: Zn2+
- cpd00058: Cu2+
- cpd00048: Sulfate

---

## Questions or Issues?

If you encounter other compatibility challenges not covered here:

1. Check if exchange reactions use non-standard naming (e.g., `R_EX_`, `DM_`, etc.)
2. Verify ModelSEED template version matches ModelSEEDpy version
3. Confirm media files use standard ModelSEED compound IDs
4. Test with known working models (E. coli K-12, B. subtilis 168)
5. Enable debug logging in ModelSEEDpy for detailed gapfilling output

**Last Updated**: 2025-10-27
