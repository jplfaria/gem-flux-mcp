# run_fba Tool Specification - Gem-Flux MCP Server

**Type**: Tool Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding FBA workflow)
- Read: 002-data-formats.md (for FBA result format details)
- Read: 003-build-media-tool.md (for media_id usage)
- Read: 004-build-model-tool.md (for model_id usage)
- Read: 005-gapfill-model-tool.md (for gapfilled model characteristics)

## Purpose

The `run_fba` tool executes Flux Balance Analysis (FBA) on a metabolic model to predict growth rates and metabolic fluxes. It uses COBRApy to solve a linear programming problem that maximizes (or minimizes) an objective function (typically biomass production) subject to stoichiometric and thermodynamic constraints. The tool returns optimal flux distributions, growth predictions, and uptake/secretion patterns in human-readable format for LLM interpretation.

## Tool Overview

**What it does**:
- Executes flux balance analysis on a metabolic model
- Applies media constraints to exchange reactions
- Optimizes objective function (default: biomass production)
- Returns predicted growth rate and flux distributions
- Identifies active metabolic pathways
- Summarizes uptake and secretion fluxes with compound names
- Handles infeasible and unbounded model conditions

**What it does NOT do**:
- Does not modify the model (read-only operation)
- Does not perform iterative optimization
- Does not validate biological feasibility of solutions
- Does not analyze pathway essentiality (use knockout tools for that)
- Does not compute flux variability ranges (FVA)
- Does not minimize total flux (pFBA)

## Input Specification

### Input Parameters

```json
{
  "model_id": "model_20251027_b4k8c1.gf",
  "media_id": "media_20251027_a3f9b2",
  "objective": "bio1",
  "maximize": true,
  "flux_threshold": 1e-6
}
```

### Parameter Descriptions

**model_id** (required)
- Type: String
- Format: Model identifier from build_model or gapfill_model
- Example: `"model_20251027_b4k8c1.gf"`
- Purpose: Identifies which model to analyze
- Validation: Must exist in current session
- Source: Output from build_model or gapfill_model tools
- Typical use: Gapfilled models (with .gf suffix) for growth analysis

**media_id** (required)
- Type: String
- Format: Media identifier from build_media tool
- Example: `"media_20251027_a3f9b2"`
- Purpose: Defines nutrient availability and exchange bounds
- Validation: Must exist in current session
- Source: Output from build_media tool
- Effect: Sets bounds on all exchange reactions (EX_ reactions)

**objective** (optional)
- Type: String
- Default: `"bio1"`
- Format: Reaction ID in the model
- Purpose: Specifies which reaction to optimize
- Validation: Reaction must exist in model
- Common values:
  - `"bio1"`: Biomass production (growth)
  - `"ATPM_c0"`: ATP maintenance
  - Any metabolic reaction ID for flux maximization
- Typical use: Keep default for growth prediction

**maximize** (optional)
- Type: Boolean
- Default: `true`
- Purpose: Optimization direction
- When `true`: Maximize objective (e.g., maximize growth)
- When `false`: Minimize objective (e.g., minimize ATP usage)
- Typical use: `true` for growth, `false` for metabolic burden analysis

**flux_threshold** (optional)
- Type: Number (float)
- Default: `1e-6`
- Units: mmol/gDW/h
- Purpose: Minimum absolute flux to report in results
- Fluxes with |flux| < threshold are considered zero
- Lower values: More reactions in output
- Higher values: Cleaner output, only significant fluxes
- Typical range: `1e-9` to `1e-3`

### Validation Rules

**Pre-validation** (before processing):
1. `model_id` must exist in current session
2. `media_id` must exist in current session
3. `objective` reaction must exist in model (if specified)
4. `flux_threshold` must be positive number ≥ 0
5. Model must be feasible (check during FBA execution)

**Validation Behavior**:
- If model_id not found, return error with list of available models
- If media_id not found, return error with list of available media
- If objective reaction not found, return error with list of potential objectives
- If validation fails, return error before running FBA

## Output Specification

### Successful Response (Optimal Solution)

```json
{
  "success": true,
  "model_id": "model_20251027_b4k8c1.gf",
  "media_id": "media_20251027_a3f9b2",
  "objective_reaction": "bio1",
  "objective_value": 0.874,
  "status": "optimal",
  "solver_status": "optimal",
  "active_reactions": 423,
  "total_reactions": 860,
  "total_flux": 2841.5,
  "fluxes": {
    "bio1": 0.874,
    "EX_cpd00027_e0": -5.0,
    "EX_cpd00007_e0": -10.234,
    "EX_cpd00011_e0": 8.456,
    "EX_cpd00001_e0": -15.2,
    "rxn00148_c0": 5.0,
    "rxn00200_c0": 4.123,
    "rxn00209_c0": 3.871
    // ... only reactions with |flux| > flux_threshold
  },
  "uptake_fluxes": [
    {
      "compound_id": "cpd00027",
      "compound_name": "D-Glucose",
      "formula": "C6H12O6",
      "flux": -5.0,
      "reaction_id": "EX_cpd00027_e0"
    },
    {
      "compound_id": "cpd00007",
      "compound_name": "O2",
      "formula": "O2",
      "flux": -10.234,
      "reaction_id": "EX_cpd00007_e0"
    },
    {
      "compound_id": "cpd00001",
      "compound_name": "H2O",
      "formula": "H2O",
      "flux": -15.2,
      "reaction_id": "EX_cpd00001_e0"
    }
  ],
  "secretion_fluxes": [
    {
      "compound_id": "cpd00011",
      "compound_name": "CO2",
      "formula": "CO2",
      "flux": 8.456,
      "reaction_id": "EX_cpd00011_e0"
    }
  ],
  "summary": {
    "uptake_reactions": 15,
    "secretion_reactions": 8,
    "internal_reactions": 400,
    "reversible_active": 150,
    "irreversible_active": 273
  },
  "top_fluxes": [
    {
      "reaction_id": "bio1",
      "reaction_name": "Biomass production",
      "flux": 0.874,
      "direction": "forward"
    },
    {
      "reaction_id": "EX_cpd00001_e0",
      "reaction_name": "H2O exchange",
      "flux": -15.2,
      "direction": "reverse"
    },
    {
      "reaction_id": "EX_cpd00007_e0",
      "reaction_name": "O2 exchange",
      "flux": -10.234,
      "direction": "reverse"
    },
    {
      "reaction_id": "EX_cpd00011_e0",
      "reaction_name": "CO2 exchange",
      "flux": 8.456,
      "direction": "forward"
    },
    {
      "reaction_id": "rxn00148_c0",
      "reaction_name": "Hexokinase",
      "flux": 5.0,
      "direction": "forward"
    }
  ]
}
```

### Output Fields

**success**
- Type: Boolean
- Value: `true` for successful FBA completion
- Always present

**model_id**
- Type: String
- Value: The model analyzed
- Purpose: Document which model was used

**media_id**
- Type: String
- Value: The media applied
- Purpose: Document growth conditions

**objective_reaction**
- Type: String
- Value: Reaction ID that was optimized
- Default: "bio1" (biomass)
- Purpose: Clarify what was being maximized/minimized

**objective_value**
- Type: Number (float)
- Value: Optimized value of objective function
- Units: Depends on objective reaction
  - For biomass: 1/h (per hour growth rate)
  - For flux reactions: mmol/gDW/h
- Typical range: 0.1 - 2.0 hr⁻¹ for bacterial growth
- Purpose: Predicted growth rate or objective flux

**status**
- Type: String
- Value: High-level optimization status
- Possible values:
  - `"optimal"`: Solution found successfully
  - `"infeasible"`: No feasible solution exists
  - `"unbounded"`: Objective can grow infinitely
  - `"failed"`: Solver error
- Purpose: Quick check of FBA outcome

**solver_status**
- Type: String
- Value: Detailed solver status from COBRApy
- Matches COBRApy status strings exactly
- Purpose: Debugging and detailed diagnostics

**active_reactions**
- Type: Integer
- Value: Count of reactions with |flux| > flux_threshold
- Typical: 30-50% of total reactions
- Purpose: Indicate metabolic activity level

**total_reactions**
- Type: Integer
- Value: Total number of reactions in model
- Purpose: Context for active_reactions percentage

**total_flux**
- Type: Number (float)
- Value: Sum of absolute values of all fluxes
- Units: mmol/gDW/h
- Formula: Σ|flux_i| for all reactions i
- Purpose: Overall metabolic activity measure

**fluxes**
- Type: Object mapping reaction IDs to flux values
- Only includes reactions with |flux| > flux_threshold
- Negative flux = reverse direction (relative to model definition)
- Positive flux = forward direction
- Purpose: Complete flux distribution for analysis

**uptake_fluxes**
- Type: Array of compound uptake objects
- Only includes exchange reactions with negative flux
- Each object contains:
  - **compound_id**: ModelSEED compound ID
  - **compound_name**: Human-readable name from database
  - **formula**: Molecular formula
  - **flux**: Negative number (uptake rate in mmol/gDW/h)
  - **reaction_id**: Exchange reaction ID (EX_ prefix)
- Sorted by absolute flux (largest uptake first)
- Purpose: LLM-friendly summary of nutrient consumption

**secretion_fluxes**
- Type: Array of compound secretion objects
- Only includes exchange reactions with positive flux
- Each object contains:
  - **compound_id**: ModelSEED compound ID
  - **compound_name**: Human-readable name from database
  - **formula**: Molecular formula
  - **flux**: Positive number (secretion rate in mmol/gDW/h)
  - **reaction_id**: Exchange reaction ID (EX_ prefix)
- Sorted by flux (largest secretion first)
- Purpose: LLM-friendly summary of metabolic products

**summary**
- Type: Object with high-level statistics
- **uptake_reactions**: Count of exchange reactions with uptake
- **secretion_reactions**: Count of exchange reactions with secretion
- **internal_reactions**: Count of non-exchange active reactions
- **reversible_active**: Active reversible reactions
- **irreversible_active**: Active irreversible reactions
- Purpose: Quick statistical overview

**top_fluxes**
- Type: Array of top flux objects
- Limited to top 10 reactions by absolute flux
- Each object contains:
  - **reaction_id**: Reaction ID with compartment
  - **reaction_name**: Human-readable name from database
  - **flux**: Flux value (signed)
  - **direction**: "forward" or "reverse" based on sign
- Sorted by absolute flux (descending)
- Purpose: Highlight most active pathways for LLM interpretation

### Error Response: Infeasible Model

```json
{
  "success": false,
  "model_id": "model_001",
  "media_id": "media_001",
  "objective_reaction": "bio1",
  "objective_value": null,
  "status": "infeasible",
  "error_type": "InfeasibleModelError",
  "message": "Model has no feasible solution in the specified media",
  "details": {
    "possible_causes": [
      "Model needs gapfilling for this medium",
      "Essential nutrients missing from medium",
      "Conflicting constraints (over-constrained)",
      "Biomass precursors unavailable"
    ],
    "media_compounds": 20,
    "model_reactions": 856,
    "exchange_reactions": 95
  },
  "suggestion": "Try: 1) Use gapfill_model to add missing reactions, 2) Check media for essential nutrients (C, N, P, S sources), 3) Verify exchange reactions exist for media compounds.",
  "diagnostics": {
    "biomass_reaction_exists": true,
    "num_constraints": 1598,
    "num_variables": 1712,
    "solver_used": "GLPK"
  }
}
```

### Error Response: Unbounded Model

```json
{
  "success": false,
  "model_id": "model_001",
  "media_id": "media_001",
  "objective_reaction": "bio1",
  "objective_value": null,
  "status": "unbounded",
  "error_type": "UnboundedModelError",
  "message": "Model objective is unbounded (can grow infinitely)",
  "details": {
    "issue": "Model has unconstrained reactions allowing infinite flux",
    "likely_cause": "Missing bounds on exchange reactions or internal loops"
  },
  "suggestion": "This indicates a model error. Check: 1) All exchange reactions have finite bounds, 2) No unconstrained internal reactions, 3) Medium was applied correctly.",
  "diagnostics": {
    "unbounded_exchanges": [
      "EX_cpd00001_e0",
      "EX_cpd00067_e0"
    ],
    "unbounded_count": 2
  }
}
```

### Error Response: Model Not Found

```json
{
  "success": false,
  "error_type": "ModelNotFoundError",
  "message": "Model ID not found in current session",
  "details": {
    "requested_model_id": "model_invalid",
    "available_models": [
      "model_20251027_b4k8c1",
      "model_20251027_b4k8c1.gf",
      "model_20251027_x9y2z3"
    ],
    "num_available": 3
  },
  "suggestion": "Use one of the available model IDs from build_model or gapfill_model outputs. Models are only available within current session."
}
```

### Error Response: Media Not Found

```json
{
  "success": false,
  "error_type": "MediaNotFoundError",
  "message": "Media ID not found in current session",
  "details": {
    "requested_media_id": "media_invalid",
    "available_media": [
      "media_20251027_a3f9b2",
      "media_20251027_k7m8n9"
    ],
    "num_available": 2
  },
  "suggestion": "Use one of the available media IDs from build_media outputs. Media are only available within current session."
}
```

### Error Response: Invalid Objective

```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Objective reaction not found in model",
  "details": {
    "requested_objective": "invalid_rxn",
    "model_id": "model_001",
    "suggested_objectives": [
      "bio1",
      "ATPM_c0"
    ],
    "total_reactions": 856
  },
  "suggestion": "Use 'bio1' for growth optimization or specify a valid reaction ID from the model."
}
```

### Error Response: Solver Error

```json
{
  "success": false,
  "error_type": "SolverError",
  "message": "FBA solver encountered an error",
  "details": {
    "solver": "GLPK",
    "error_message": "Numerical instability detected",
    "model_id": "model_001",
    "media_id": "media_001"
  },
  "suggestion": "This is a rare solver issue. Try: 1) Rebuild the model, 2) Simplify the medium, 3) Check for extremely large or small flux bounds.",
  "diagnostics": {
    "solver_exit_code": 1,
    "solver_time": 0.234
  }
}
```

## Behavioral Specification

### FBA Execution Workflow

**Step 1: Validate Input**
1. Check model_id exists in session
2. Check media_id exists in session
3. Verify objective reaction exists in model (if specified)
4. Verify flux_threshold is valid positive number
5. If any validation fails, return error immediately

**Step 2: Load Model and Media**
1. Retrieve COBRApy model from session: `session.models[model_id]`
2. Retrieve MSMedia object from session: `session.media[media_id]`
3. Create temporary copy of model (preserve original state)
4. Model operations are read-only (no modifications stored)

**Step 3: Apply Media Constraints**
1. Get media constraints: `media_constraints = media.get_media_constraints()`
2. Convert to COBRApy medium format:
   - Media constraints use compound IDs with compartment: `cpd00027_e0`
   - COBRApy medium uses exchange reaction IDs: `EX_cpd00027_e0`
   - Map each compound to corresponding exchange reaction
   - Set exchange bounds based on media bounds
3. Apply medium to model:
   ```python
   medium = {}
   for cpd_id, (lb, ub) in media_constraints.items():
       rxn_id = f'EX_{cpd_id}'
       if rxn_id in model.reactions:
           medium[rxn_id] = abs(lb)  # COBRApy uses positive uptake bounds
   model.medium = medium
   ```
4. Verify all media compounds have corresponding exchange reactions
5. Warn if media compounds missing from model (not fatal)

**Step 4: Set Objective Function**
1. If objective parameter provided, set model objective to that reaction
2. Otherwise, keep default objective (typically bio1)
3. Set optimization direction (maximize or minimize)
4. Verify objective reaction exists in model
5. Verify objective has valid bounds

**Step 5: Execute FBA**
1. Call COBRApy optimize: `solution = model.optimize()`
2. Optimization solves linear programming problem:
   - Objective: Maximize (or minimize) objective reaction flux
   - Subject to: Stoichiometric constraints (mass balance)
   - Subject to: Flux bounds (thermodynamic and media constraints)
   - Method: Simplex or interior-point algorithm
3. Capture solution status and objective value
4. Handle solver timeout (if exceeds 60 seconds, return error)

**Step 6: Interpret Solution Status**
1. **If status == "optimal"**:
   - Solution found successfully
   - Proceed to extract fluxes
2. **If status == "infeasible"**:
   - No feasible solution exists
   - Return infeasible error response
   - Suggest gapfilling or media modification
3. **If status == "unbounded"**:
   - Objective can grow infinitely (model error)
   - Return unbounded error response
   - Identify unbounded exchange reactions
4. **If status == other**:
   - Solver error or unknown state
   - Return solver error response

**Step 7: Extract and Filter Fluxes**
1. Get full flux distribution: `solution.fluxes` (pandas Series)
2. Filter by threshold: Keep only reactions with |flux| > flux_threshold
3. Convert pandas Series to dictionary for JSON serialization
4. Round fluxes to reasonable precision (e.g., 6 decimal places)
5. Separate fluxes into:
   - Exchange reactions (EX_ prefix)
   - Internal reactions (all others)

**Step 8: Separate Uptake and Secretion**
1. Filter exchange reactions only (EX_ prefix)
2. **Uptake fluxes**: Exchange reactions with negative flux
   - Extract compound ID from reaction ID (EX_cpd00027_e0 → cpd00027)
   - Query ModelSEED database for compound name and formula
   - Create uptake flux object with metadata
   - Sort by absolute flux (largest uptake first)
3. **Secretion fluxes**: Exchange reactions with positive flux
   - Extract compound ID from reaction ID
   - Query ModelSEED database for compound name and formula
   - Create secretion flux object with metadata
   - Sort by flux (largest secretion first)

**Step 9: Identify Top Fluxes**
1. Sort all fluxes by absolute value (descending)
2. Take top 10 reactions
3. For each reaction:
   - Query ModelSEED database for reaction name
   - Determine direction (forward if positive, reverse if negative)
   - Create top flux object with metadata
4. Purpose: Highlight most active pathways for LLM

**Step 10: Compute Summary Statistics**
1. Count uptake reactions (exchange with negative flux)
2. Count secretion reactions (exchange with positive flux)
3. Count internal reactions (non-exchange with flux)
4. Count reversible vs irreversible active reactions
5. Compute total flux (sum of absolute values)
6. Compute percentage of reactions active

**Step 11: Build Response**
1. Assemble all components into response object
2. Include success=true, status="optimal"
3. Include objective value and all computed statistics
4. Return complete FBA result

### Media Application Pattern

**Critical**: COBRApy requires specific medium format

```python
# WRONG - This will not work
model.medium['EX_cpd00027_e0'] = 10.0

# CORRECT - Must retrieve, modify, reassign
medium = model.medium
medium['EX_cpd00027_e0'] = 10.0
model.medium = medium
```

**Media Application Steps**:
1. Retrieve current medium: `medium = model.medium`
2. For each compound in media:
   - Find corresponding exchange reaction
   - Set uptake bound (positive number = absolute value of lower bound)
3. Reassign medium: `model.medium = medium`

**Exchange Reaction Matching**:
- Media constraint: `cpd00027_e0: (-5, 100)`
- Exchange reaction: `EX_cpd00027_e0`
- COBRApy medium entry: `{"EX_cpd00027_e0": 5.0}`
  - Value is positive (absolute value of lower bound)
  - Represents maximum uptake rate

### Flux Interpretation

**Flux Sign Convention**:
- **Positive flux**: Reaction proceeds forward (left to right)
- **Negative flux**: Reaction proceeds reverse (right to left)

**Exchange Reaction Fluxes**:
- **Negative flux**: Uptake (compound consumed from environment)
- **Positive flux**: Secretion (compound produced to environment)

**Examples**:
```
EX_cpd00027_e0: -5.0    →  Glucose uptake at 5.0 mmol/gDW/h
EX_cpd00011_e0: +8.5    →  CO2 secretion at 8.5 mmol/gDW/h
bio1: +0.874            →  Biomass production at 0.874 1/h
rxn00148_c0: +5.0       →  Hexokinase forward at 5.0 mmol/gDW/h
```

### Threshold Filtering

**Purpose**: Reduce noise from numerical solver precision

**Default threshold**: `1e-6` mmol/gDW/h

**Behavior**:
- Fluxes with |flux| < threshold are considered zero
- Not included in fluxes dictionary
- Not counted in active_reactions
- Reduces output size significantly

**Example**:
```python
# Before filtering (1000 reactions, many near-zero)
fluxes = {
  "rxn00001": 5.0,
  "rxn00002": 1e-12,  # Numerical noise
  "rxn00003": 0.5,
  "rxn00004": -1e-15, # Numerical noise
  ...
}

# After filtering with threshold=1e-6 (423 significant reactions)
fluxes = {
  "rxn00001": 5.0,
  "rxn00003": 0.5,
  ...
}
```

## Example Usage Scenarios

### Example 1: Predict Growth in Glucose Minimal Media

**User Intent**: "What is the predicted growth rate for my E. coli model in glucose minimal media?"

**AI Assistant Workflow**:
1. User has model_001.gf (gapfilled E. coli model)
2. User has media_001 (glucose minimal media)
3. Call run_fba:

```json
{
  "model_id": "model_001.gf",
  "media_id": "media_001"
}
```

**Response**:
```json
{
  "success": true,
  "objective_value": 0.874,
  "status": "optimal",
  "active_reactions": 423,
  "uptake_fluxes": [
    {
      "compound_name": "D-Glucose",
      "flux": -5.0
    },
    {
      "compound_name": "O2",
      "flux": -10.234
    }
  ],
  "secretion_fluxes": [
    {
      "compound_name": "CO2",
      "flux": 8.456
    }
  ]
}
```

**AI Response to User**:
"Your E. coli model is predicted to grow at 0.874 hr⁻¹ in glucose minimal media. The model consumes 5.0 mmol/gDW/h of glucose and 10.2 mmol/gDW/h of oxygen, producing 8.5 mmol/gDW/h of CO2. Out of 860 total reactions, 423 (49%) are active during growth."

### Example 2: Analyze Pathway Activity

**User Intent**: "Which pathways are most active during aerobic glucose growth?"

**AI Assistant Workflow**:
1. Run FBA as in Example 1
2. Examine top_fluxes for highest activity reactions
3. Use get_reaction_name to understand pathway context

**Response excerpt**:
```json
{
  "top_fluxes": [
    {
      "reaction_id": "bio1",
      "reaction_name": "Biomass production",
      "flux": 0.874
    },
    {
      "reaction_id": "EX_cpd00001_e0",
      "reaction_name": "H2O exchange",
      "flux": -15.2
    },
    {
      "reaction_id": "rxn00148_c0",
      "reaction_name": "Hexokinase",
      "flux": 5.0
    },
    {
      "reaction_id": "rxn00209_c0",
      "reaction_name": "Phosphoglucose isomerase",
      "flux": 4.9
    },
    {
      "reaction_id": "rxn00200_c0",
      "reaction_name": "Pyruvate dehydrogenase",
      "flux": 4.2
    }
  ]
}
```

**AI Response to User**:
"The most active pathways during aerobic glucose growth are:
1. Glycolysis - Starting with hexokinase (5.0 mmol/gDW/h) and phosphoglucose isomerase (4.9)
2. TCA cycle entry - Pyruvate dehydrogenase is highly active (4.2)
3. Respiration - High oxygen uptake (10.2) indicates active oxidative phosphorylation

These fluxes show the model is using aerobic respiration efficiently, consistent with E. coli metabolism in glucose + oxygen conditions."

### Example 3: Compare Aerobic vs Anaerobic Growth

**User Intent**: "How does growth differ between aerobic and anaerobic conditions?"

**AI Assistant Workflow**:
1. Create media_aerobic with O2 available: `cpd00007: (-10, 100)`
2. Create media_anaerobic with O2 blocked: `cpd00007: (0, 0)`
3. Run FBA with media_aerobic → growth_aerobic
4. Run FBA with media_anaerobic → growth_anaerobic
5. Compare results

**Aerobic FBA**:
```json
{
  "model_id": "model_001.gf",
  "media_id": "media_aerobic"
}
```

**Response**:
```json
{
  "objective_value": 0.874,
  "uptake_fluxes": [
    {"compound_name": "D-Glucose", "flux": -5.0},
    {"compound_name": "O2", "flux": -10.2}
  ],
  "secretion_fluxes": [
    {"compound_name": "CO2", "flux": 8.5}
  ]
}
```

**Anaerobic FBA**:
```json
{
  "model_id": "model_001.gf",
  "media_id": "media_anaerobic"
}
```

**Response**:
```json
{
  "objective_value": 0.211,
  "uptake_fluxes": [
    {"compound_name": "D-Glucose", "flux": -9.5}
  ],
  "secretion_fluxes": [
    {"compound_name": "Ethanol", "flux": 12.4},
    {"compound_name": "Acetate", "flux": 5.2},
    {"compound_name": "CO2", "flux": 6.1}
  ]
}
```

**AI Response to User**:
"Comparison of aerobic vs anaerobic growth:

**Aerobic** (with O2):
- Growth rate: 0.874 hr⁻¹
- Glucose uptake: 5.0 mmol/gDW/h
- Main product: CO2 (complete oxidation)

**Anaerobic** (no O2):
- Growth rate: 0.211 hr⁻¹ (24% of aerobic)
- Glucose uptake: 9.5 mmol/gDW/h (1.9x higher)
- Main products: Ethanol (12.4) and Acetate (5.2) via fermentation

The model shows typical E. coli behavior: aerobic respiration is much more efficient (4x growth rate), while anaerobic fermentation requires more glucose to produce the same biomass and generates reduced carbon products instead of complete oxidation to CO2."

### Example 4: Infeasible Model (Needs Gapfilling)

**User Intent**: "Run FBA on my draft model"

**AI Assistant Attempt**:
```json
{
  "model_id": "model_001",
  "media_id": "media_001"
}
```

**Error Response**:
```json
{
  "success": false,
  "status": "infeasible",
  "error_type": "InfeasibleModelError",
  "message": "Model has no feasible solution in the specified media",
  "suggestion": "Try: 1) Use gapfill_model to add missing reactions..."
}
```

**AI Recovery**:
1. Recognize model is draft (not gapfilled)
2. Suggest gapfilling workflow
3. AI: "Your draft model cannot grow in this medium yet. This is expected for ungapfilled models. Let me gapfill it first..."
4. Call gapfill_model
5. Retry run_fba with gapfilled model

**After Gapfilling**:
```json
{
  "model_id": "model_001.gf",
  "media_id": "media_001"
}
```

**Success Response**:
```json
{
  "success": true,
  "objective_value": 0.874,
  "status": "optimal"
}
```

**AI Response to User**:
"Your draft model needed gapfilling. I've gapfilled it (model_001.gf) and now it grows at 0.874 hr⁻¹ in glucose minimal media."

### Example 5: Maximize Specific Metabolite Production

**User Intent**: "Maximize ethanol production instead of growth"

**AI Assistant Workflow**:
1. Identify ethanol exchange reaction (EX_cpd00363_e0)
2. Run FBA with ethanol as objective

```json
{
  "model_id": "model_001.gf",
  "media_id": "media_anaerobic",
  "objective": "EX_cpd00363_e0",
  "maximize": true
}
```

**Response**:
```json
{
  "success": true,
  "objective_reaction": "EX_cpd00363_e0",
  "objective_value": 18.7,
  "status": "optimal",
  "secretion_fluxes": [
    {
      "compound_name": "Ethanol",
      "flux": 18.7
    }
  ],
  "fluxes": {
    "bio1": 0.0,
    "EX_cpd00363_e0": 18.7,
    "EX_cpd00027_e0": -10.0
  }
}
```

**AI Response to User**:
"When optimizing for maximum ethanol production instead of growth, the model can produce up to 18.7 mmol/gDW/h of ethanol from 10.0 mmol/gDW/h glucose. Note that biomass production is zero in this optimization - the model diverts all resources to ethanol instead of growth. For realistic production, you would need to constrain biomass to a minimum value."

## Integration with Other Tools

### Depends On: build_model or gapfill_model

The run_fba tool requires a model:

**Workflow**:
1. build_model → creates draft model → model_001
2. gapfill_model → creates gapfilled model → model_001.draft.gf
3. run_fba with model_001.gf → predicts growth

**Model Requirements**:
- Must have biomass reaction (bio1)
- Must have exchange reactions for media compounds
- Gapfilled models typically required for successful FBA

### Depends On: build_media

The run_fba tool requires a medium:

**Workflow**:
1. build_media → creates medium → media_001
2. run_fba with media_001 → sets exchange bounds

**Media Requirements**:
- Must contain all essential nutrients
- Exchange reactions must exist in model for media compounds

### Used By: Downstream Analysis

FBA results feed into:
- Pathway analysis (identify active pathways)
- Strain design (knockout analysis)
- Media optimization (find limiting nutrients)
- Metabolic engineering (production predictions)

### Session Storage

**Read-Only Operation**:
```python
# FBA does not modify stored model
model = session.models[model_id].copy()  # Work on copy
solution = model.optimize()
# Original model in session unchanged
```

**No Persistence**:
- FBA results not stored in session
- Each run_fba call performs fresh optimization
- Stateless operation

## Data Flow Diagram

```
Input (model_id, media_id, objective)
  ↓
Validate model and media exist
  ↓
Load model and media from session
  ↓
Create temporary model copy
  ↓
Apply media constraints to exchange reactions
  ↓
Set objective function
  ↓
Execute FBA (COBRApy optimize)
  ↓
Check solution status
  ↓
If optimal:
  - Extract flux distribution
  - Filter by threshold
  - Separate uptake/secretion
  - Query database for names
  - Compute statistics
  ↓
If infeasible/unbounded:
  - Return error with diagnostics
  ↓
Build response (JSON)
  ↓
Return to user
```

## COBRApy Integration

### Core FBA Function

```python
from cobra.io import load_json_model

# Load model
model = load_json_model(model_path)

# Set medium
medium = model.medium
for cpd_id, (lb, ub) in media_constraints.items():
    rxn_id = f'EX_{cpd_id}'
    if rxn_id in model.reactions:
        medium[rxn_id] = abs(lb)
model.medium = medium

# Set objective
model.objective = 'bio1'

# Run FBA
solution = model.optimize()

# Extract results
objective_value = solution.objective_value
status = solution.status
fluxes = solution.fluxes.to_dict()
```

### Solution Object Structure

```python
solution.objective_value  # float: optimized objective value
solution.status          # str: 'optimal', 'infeasible', 'unbounded'
solution.fluxes          # pandas.Series: reaction_id → flux
solution.shadow_prices   # pandas.Series: metabolite shadow prices
solution.reduced_costs   # pandas.Series: reaction reduced costs
```

### Fast FBA Alternative (Not Used in MVP)

```python
# slim_optimize() is 10x faster but returns only objective value
objective_value = model.slim_optimize()
# No flux distribution available
# Use for batch screening, not detailed analysis
```

### Model Summary (Alternative Output)

```python
# COBRApy built-in summary
summary = model.summary()
# Returns formatted summary with:
# - Objective value
# - Top uptake/secretion fluxes
# - ATP production/consumption
# Not used in MVP (we build custom summary)
```

## Performance Considerations

### Expected Performance

**Typical Execution Time**:
- Small model (100 reactions): < 10ms
- Medium model (500 reactions): 20-50ms
- Large model (1500 reactions): 50-200ms
- Very large model (5000 reactions): 200-500ms

**Performance Factors**:
1. **Model size**: Linear scaling with reaction count
2. **Solver efficiency**: GLPK vs CPLEX vs Gurobi
3. **Model sparsity**: Sparse models solve faster
4. **Numerical conditioning**: Well-conditioned models faster

**Solver Performance**:
- **GLPK** (default, open-source): Good for small-medium models
- **CPLEX** (commercial): 2-5x faster for large models
- **Gurobi** (commercial): Similar to CPLEX

**MVP Uses**: GLPK (default COBRApy solver)

### Optimization Strategies

**Not Needed for MVP**:
- FBA is already very fast (< 200ms for typical models)
- Optimization premature without performance bottleneck
- COBRApy handles efficiency internally

**Future Optimizations** (post-MVP):
- Batch FBA with parameter screening
- Parallel FBA for multiple conditions
- Caching solutions for identical conditions
- Use slim_optimize() when full fluxes not needed

## Quality Requirements

### Correctness
- ✅ FBA solution is mathematically optimal
- ✅ Media constraints correctly applied to exchange reactions
- ✅ Flux threshold filtering removes numerical noise
- ✅ Compound names correctly retrieved from database
- ✅ Uptake/secretion correctly classified by flux sign

### Reliability
- ✅ Infeasible models return clear error messages
- ✅ Unbounded models identified and diagnosed
- ✅ Solver errors caught and reported
- ✅ Numerical precision issues handled (threshold filtering)

### Usability
- ✅ Human-readable compound names in output
- ✅ Top fluxes highlight most active pathways
- ✅ Summary statistics provide overview
- ✅ Error messages suggest recovery actions

### Performance
- ✅ Small models: < 50ms
- ✅ Medium models: < 200ms
- ✅ Large models: < 500ms
- ✅ Timeout protection at 60 seconds

## Testing Considerations

### Test Cases

**Valid Inputs**:
1. Gapfilled model in glucose minimal media
2. Gapfilled model in rich media
3. Model with custom objective (ATPM_c0)
4. Model with minimize=true
5. Different flux thresholds (1e-9, 1e-6, 1e-3)

**Invalid Inputs**:
1. Non-existent model_id
2. Non-existent media_id
3. Non-existent objective reaction
4. Negative flux_threshold
5. Invalid objective format

**Edge Cases**:
1. Draft model (infeasible)
2. Model already optimal without media
3. Single compound medium (very restricted)
4. Zero flux threshold (all reactions in output)
5. Very high flux threshold (only biomass in output)

**Expected Outcomes**:
1. **Optimal**: 80-90% of cases with gapfilled models
2. **Infeasible**: 10-20% (draft models, insufficient media)
3. **Unbounded**: < 1% (model errors only)

### Integration Tests

1. build_media → build_model → gapfill_model → run_fba (complete workflow)
2. Run FBA with different media on same model
3. Run FBA with different objectives
4. Run FBA on draft vs gapfilled models
5. Verify flux conservation (sum of fluxes into/out of each metabolite = 0)
6. Verify exchange fluxes match media bounds

## Future Enhancements

### Post-MVP Features (Not in Specification)

**v0.2.0 - Enhanced FBA**:
- `run_pfba`: Parsimonious FBA (minimize total flux)
- `run_fva`: Flux variability analysis (flux ranges)
- `batch_fba`: Multiple conditions in single call

**v0.3.0 - Advanced Analysis**:
- `single_gene_deletion`: Knockout screening
- `double_gene_deletion`: Combinatorial knockouts
- `flux_sampling`: Sample flux space for variability

**v0.4.0 - Loopless FBA**:
- `run_loopless_fba`: Eliminate thermodynamically infeasible loops
- More biologically realistic flux distributions

**v0.5.0 - Shadow Prices and Sensitivity**:
- Include shadow prices in output (metabolite importance)
- Include reduced costs (reaction importance)
- Sensitivity analysis for media components

## Related Specifications

- **001-system-overview.md**: Overall FBA workflow in system architecture
- **002-data-formats.md**: FBA result format and flux conventions
- **003-build-media-tool.md**: Creates media_id for FBA
- **004-build-model-tool.md**: Creates model_id for FBA
- **005-gapfill-model-tool.md**: Prepares models for successful FBA
- **007-database-integration.md**: Compound/reaction name lookups for output
- **008-compound-lookup-tools.md**: get_compound_name for uptake/secretion
- **009-reaction-lookup-tools.md**: get_reaction_name for top fluxes

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 007-database-integration.md
