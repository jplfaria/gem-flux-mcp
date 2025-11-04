# gapfill_model Tool Specification - Gem-Flux MCP Server

**Type**: Tool Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding ModelSEED gapfilling workflow)
- Read: 002-data-formats.md (for model and media data formats)
- Read: 003-build-media-tool.md (for media_id usage)
- Read: 004-build-model-tool.md (for model_id and draft model characteristics)

## Purpose

The `gapfill_model` tool adds missing reactions to a draft metabolic model to enable growth in a specified medium. It uses ModelSEEDpy's gapfilling algorithms to identify and add the minimal set of reactions required to achieve a target growth rate. The tool performs two-stage gapfilling: ATP correction (ensuring ATP production works across different media) followed by genome-scale gapfilling (adding reactions for growth in the target medium).

## Tool Overview

**What it does**:
- Takes a draft model (from build_model) and target medium (from build_media)
- Performs two-stage gapfilling process:
  1. **ATP Correction**: Tests ATP production across multiple standard media
  2. **Genome-scale Gapfilling**: Adds minimal reactions for growth in target medium
- Identifies which reactions need to be added
- Returns a new gapfilled model with added reactions
- Provides before/after growth rate comparison
- Lists all reactions added during gapfilling

**What it does NOT do**:
- Does not guarantee biological accuracy (adds reactions from template, not genome)
- Does not validate pathway completeness
- Does not optimize reaction selection (minimizes count only)
- Does not modify the original model (creates new gapfilled model)
- Does not perform iterative refinement

## Input Specification

### Input Parameters

```json
{
  "model_id": "model_20251027_b4k8c1",
  "media_id": "media_20251027_a3f9b2",
  "target_growth_rate": 0.01,
  "allow_all_non_grp_reactions": true,
  "gapfill_mode": "full"
}
```

### Parameter Descriptions

**model_id** (required)
- Type: String
- Format: Model identifier from build_model tool
- Example: `"model_20251027_b4k8c1"`
- Purpose: Identifies which draft model to gapfill
- Validation: Must exist in current session
- Source: Output from build_model tool
- Typical pattern: Draft models that cannot grow without gapfilling

**media_id** (required)
- Type: String
- Format: Media identifier from build_media tool
- Example: `"media_20251027_a3f9b2"`
- Purpose: Specifies growth conditions for gapfilling
- Validation: Must exist in current session
- Source: Output from build_media tool
- Use case: Model will be gapfilled to grow in this specific medium

**target_growth_rate** (optional)
- Type: Number (float)
- Default: 0.01
- Units: 1/h (per hour growth rate)
- Range: 0.001 to 10.0 (typical: 0.01 to 1.0)
- Purpose: Minimum growth rate that gapfilling must achieve
- Lower values: Easier to achieve, fewer reactions added
- Higher values: May require more reactions or be infeasible
- Typical value: 0.01 (1% of maximum for draft models)

**allow_all_non_grp_reactions** (optional)
- Type: Boolean
- Default: `true`
- Purpose: Allow non-gene-associated reactions during gapfilling
- When `true`: Gapfilling can add any template reaction
- When `false`: Only add reactions with gene associations
- MVP default: `true` (more permissive, better chance of finding solution)

**gapfill_mode** (optional)
- Type: String
- Default: `"full"`
- Valid values:
  - `"full"`: Perform both ATP correction and genome-scale gapfilling
  - `"atp_only"`: Perform only ATP correction phase
  - `"genomescale_only"`: Skip ATP correction, only genome-scale gapfilling
- Purpose: Control which gapfilling stages to run
- Recommendation: Use "full" for MVP (most comprehensive)

### Validation Rules

**Pre-validation** (before processing):
1. `model_id` must exist in current session
2. `media_id` must exist in current session
3. `target_growth_rate` must be positive number > 0
4. `gapfill_mode` must be one of: "full", "atp_only", "genomescale_only"
5. Model biomass reaction check (warning only):
   - If model has no biomass reaction, log warning but allow gapfilling
   - This accommodates offline model building (annotate_with_rast=False) which produces empty models
   - Gapfilling empty models may not be meaningful, but is allowed for testing/API correctness

**Validation Behavior**:
- If model_id not found, return error with list of available models
- If media_id not found, return error with list of available media
- If target_growth_rate is invalid, suggest typical range
- If validation fails, return error before starting gapfilling

## Output Specification

### Successful Response

```json
{
  "success": true,
  "model_id": "model_20251027_b4k8c1.gf",
  "original_model_id": "model_20251027_b4k8c1",
  "media_id": "media_20251027_a3f9b2",
  "growth_rate_before": 0.0,
  "growth_rate_after": 0.874,
  "target_growth_rate": 0.01,
  "gapfilling_successful": true,
  "num_reactions_added": 4,
  "reactions_added": [
    {
      "id": "rxn05459_c0",
      "name": "Shikimate kinase",
      "equation": "cpd00036[c0] + cpd00038[c0] => cpd00126[c0] + cpd00008[c0]",
      "direction": "forward",
      "compartment": "c0",
      "source": "template_gapfill"
    },
    {
      "id": "rxn05481_c0",
      "name": "3-dehydroquinate synthase",
      "equation": "cpd00126[c0] => cpd00309[c0] + cpd00009[c0]",
      "direction": "reverse",
      "compartment": "c0",
      "source": "template_gapfill"
    },
    {
      "id": "rxn00599_c0",
      "name": "Chorismate synthase",
      "equation": "cpd00309[c0] => cpd00117[c0] + cpd00009[c0]",
      "direction": "forward",
      "compartment": "c0",
      "source": "template_gapfill"
    },
    {
      "id": "rxn02185_c0",
      "name": "Anthranilate synthase",
      "equation": "cpd00117[c0] + cpd00001[c0] => cpd00056[c0] + cpd00011[c0]",
      "direction": "reverse",
      "compartment": "c0",
      "source": "template_gapfill"
    }
  ],
  "exchange_reactions_added": [
    {
      "id": "EX_cpd01981_e0",
      "name": "Exchange for cpd01981",
      "metabolite": "cpd01981",
      "metabolite_name": "Unknown compound",
      "source": "auto_generated"
    }
  ],
  "atp_correction": {
    "performed": true,
    "media_tested": 27,
    "media_passed": 27,
    "media_failed": 0,
    "reactions_added": 0
  },
  "genomescale_gapfill": {
    "performed": true,
    "reactions_added": 4,
    "reversed_reactions": 0,
    "new_reactions": 4
  },
  "model_properties": {
    "num_reactions": 860,
    "num_metabolites": 743,
    "is_draft": false,
    "requires_further_gapfilling": false
  }
}
```

### Output Fields

**success**
- Type: Boolean
- Value: `true` for successful gapfilling
- Always present

**model_id**
- Type: String
- Format: Model ID with transformed state suffix
- State transformation:
  - Input `.draft` → Output `.draft.gf`
  - Input `.gf` → Output `.gf.gf`
  - Input `.draft.gf` → Output `.draft.gf.gf`
- Example: `"model_20251027_b4k8c1.draft.gf"` (from `model_20251027_b4k8c1.draft`)
- Purpose: Identifier for the new gapfilled model
- Scope: Valid within current server session
- Used by: run_fba tool for flux analysis

**original_model_id**
- Type: String
- Value: The model_id that was gapfilled
- Purpose: Track provenance of gapfilled model
- Note: Original model remains unchanged in session

**media_id**
- Type: String
- Value: The media used for gapfilling
- Purpose: Document which conditions the model can grow in

**growth_rate_before**
- Type: Number (float)
- Value: Growth rate of original model in target media
- Units: 1/h (per hour)
- Typical: 0.0 for draft models (infeasible)
- Purpose: Baseline comparison

**growth_rate_after**
- Type: Number (float)
- Value: Growth rate of gapfilled model in target media
- Units: 1/h (per hour)
- Should be: ≥ target_growth_rate
- Purpose: Verify gapfilling achieved target

**target_growth_rate**
- Type: Number (float)
- Value: The minimum growth rate requested
- Purpose: Document gapfilling objective

**gapfilling_successful**
- Type: Boolean
- Value: `true` if growth_rate_after ≥ target_growth_rate
- Value: `false` if gapfilling could not achieve target
- Purpose: Quick success check

**num_reactions_added**
- Type: Integer
- Value: Total count of reactions added (excludes exchanges)
- Purpose: Summary of gapfilling extent
- Typical range: 0-50 reactions for prokaryotic models

**reactions_added**
- Type: Array of reaction objects
- Length: num_reactions_added
- Each object contains:
  - **id**: Reaction ID with compartment suffix
  - **name**: Human-readable reaction name from database
  - **equation**: Stoichiometric equation (human-readable)
  - **direction**: "forward", "reverse", or "reversible"
  - **compartment**: Compartment code (c0, e0, p0)
  - **source**: "template_gapfill" or "atp_correction"
- Purpose: Enable LLM to explain what pathways were completed

**exchange_reactions_added**
- Type: Array of exchange reaction objects
- Purpose: List any new exchange reactions auto-generated
- Each object contains:
  - **id**: Exchange reaction ID (EX_ prefix)
  - **name**: Human-readable description
  - **metabolite**: Compound ID being exchanged
  - **metabolite_name**: Human-readable compound name
  - **source**: "auto_generated"

**atp_correction**
- Type: Object with ATP correction stage results
- **performed**: Boolean - whether ATP correction ran
- **media_tested**: Number of standard media tested
- **media_passed**: Number of media where ATP production works
- **media_failed**: Number of media where ATP production failed
- **reactions_added**: Reactions added during ATP correction
- Purpose: Document ATP correction stage outcomes

**genomescale_gapfill**
- Type: Object with genome-scale gapfilling results
- **performed**: Boolean - whether genome-scale gapfilling ran
- **reactions_added**: Count of reactions added
- **reversed_reactions**: Count of existing reactions reversed
- **new_reactions**: Count of new reactions added
- Purpose: Document genome-scale gapfilling outcomes

**model_properties**
- Type: Object with updated model statistics
- **num_reactions**: Total reactions in gapfilled model
- **num_metabolites**: Total metabolites in gapfilled model
- **is_draft**: Should be `false` after successful gapfilling
- **requires_further_gapfilling**: `false` if achieved target growth
- Purpose: Summary of final model state

### Failure Handling Behavior

**Gapfilling Failure Scenarios**:

The gapfill_model tool can fail at different stages. The behavior depends on whether gapfilling is run standalone or as part of a full pipeline (build + gapfill).

#### Scenario 1: Standalone Gapfilling Failure

When gapfilling an **existing draft model** that was previously created by build_model:

**Behavior**:
1. Return error response (gapfilling_successful: false)
2. Keep original draft model unchanged in session
3. No gapfilled model created (.gf suffix not added)
4. Provide diagnostic information and recovery suggestions

**Example Response**:
```json
{
  "success": false,
  "error_type": "GapfillingInfeasibleError",
  "message": "Could not find gapfilling solution to achieve target growth rate",
  "details": {
    "model_id": "model_001.draft",
    "original_model_preserved": true,
    "model_id_retained": "model_001.draft",
    "media_id": "media_001",
    "target_growth_rate": 0.01,
    "max_achievable_growth": 0.0,
    "stage_failed": "genomescale_gapfill"
  },
  "recovery_options": [
    "Add more compounds to the medium (check for missing essential nutrients)",
    "Use a lower target_growth_rate (try 0.001)",
    "Use a different template (try GramPositive or Core)",
    "Check if biomass precursors are available in media"
  ],
  "suggestion": "The original draft model (model_001.draft) is still available. Try modifying the medium or lowering the target growth rate."
}
```

**User Impact**:
- Draft model remains usable for retry attempts
- User can modify media composition
- User can adjust target growth rate
- User can inspect draft model with other tools

#### Scenario 2: Full Pipeline Failure (Build + Gapfill)

When gapfilling is triggered **automatically as part of build_model** with `auto_gapfill=true`:

**Behavior**:
1. Draft model (.draft) is created and stored successfully
2. Gapfilling is attempted on draft model
3. If gapfilling fails:
   - Return draft model_id in response
   - Include error details about gapfilling failure
   - Set gapfilling_successful: false
   - Provide recovery suggestions
4. Draft model remains available for manual retry

**Example Response**:
```json
{
  "success": true,
  "model_id": "model_20251027_b4k8c1.draft",
  "model_name": "E_coli_K12",
  "num_reactions": 856,
  "num_metabolites": 739,
  "num_genes": 1371,
  "template_used": "GramNegative",
  "annotation_method": "RAST",
  "is_draft": true,
  "gapfilling_attempted": true,
  "gapfilling_successful": false,
  "gapfilling_error": {
    "error_type": "GapfillingInfeasibleError",
    "message": "Could not find gapfilling solution to achieve target growth rate",
    "details": {
      "media_id": "glucose_minimal_aerobic",
      "target_growth_rate": 0.01,
      "max_achievable_growth": 0.0,
      "stage_failed": "genomescale_gapfill",
      "possible_causes": [
        "Target medium missing essential nutrients",
        "Model template missing required pathways"
      ]
    }
  },
  "next_steps": [
    "Draft model created successfully and saved as model_20251027_b4k8c1.draft",
    "Gapfilling failed, but you can retry manually with different conditions",
    "Try: gapfill_model with modified media or lower target_growth_rate",
    "Draft model can be used for inspection and manual gapfilling"
  ]
}
```

**Key Characteristics**:
- `success: true` (draft model was created successfully)
- `model_id` contains `.draft` suffix (not `.draft.gf`)
- `gapfilling_attempted: true` and `gapfilling_successful: false`
- `gapfilling_error` object contains full error details
- Draft model is stored and available for retry

#### Scenario 3: ATP Correction Failure

When ATP correction stage fails for many media:

**Behavior**:
1. ATP correction attempts to gapfill for ATP production
2. Some media may fail to achieve ATP production
3. This is **acceptable** - not all media need to pass
4. Genome-scale gapfilling proceeds with available corrections
5. ATP failures documented in response

**Example Response**:
```json
{
  "success": true,
  "model_id": "model_001.draft.gf",
  "atp_correction": {
    "performed": true,
    "media_tested": 54,
    "media_passed": 35,
    "media_failed": 19,
    "reactions_added": 3,
    "failed_media_examples": [
      "Etho.O2",
      "mal-L",
      "Pyr.SO4"
    ],
    "note": "Some ATP test media failed, but this is acceptable. Model can still grow in target medium."
  },
  "genomescale_gapfill": {
    "performed": true,
    "reactions_added": 5
  }
}
```

**Tolerance**:
- ATP correction failures are **not fatal**
- As long as genome-scale gapfilling succeeds, overall gapfilling succeeds
- Failed ATP media documented for transparency

#### Scenario 4: Partial Gapfilling (Achieves Some Growth)

When gapfilling achieves growth but below target:

**Behavior**:
1. Gapfilling finds some reactions
2. Growth rate improved but still < target_growth_rate
3. Return as partial success with warning

**Example Response**:
```json
{
  "success": true,
  "model_id": "model_001.draft.gf",
  "growth_rate_before": 0.0,
  "growth_rate_after": 0.005,
  "target_growth_rate": 0.01,
  "gapfilling_successful": false,
  "num_reactions_added": 12,
  "warning": "Gapfilling improved growth but did not reach target. Model can grow at 0.005 1/h (target was 0.01 1/h).",
  "suggestion": "Try: 1) Add more nutrients to medium, 2) Lower target_growth_rate to 0.005, or 3) Use different template"
}
```

**Characteristics**:
- `success: true` (gapfilling ran and improved model)
- `gapfilling_successful: false` (didn't meet target)
- Gapfilled model (.gf) is created and stored
- User can use model at achieved growth rate or retry

#### Failure Recovery Workflow

**For Standalone Gapfilling Failure**:
1. User receives error with draft model_id
2. User can:
   - Modify media (add nutrients)
   - Lower target_growth_rate
   - Try different template (rebuild model)
   - Inspect draft model to diagnose issues
3. Retry gapfill_model with modified parameters

**For Full Pipeline Failure**:
1. User receives draft model_id in response
2. build_model reports gapfilling_successful: false
3. User can:
   - Accept draft model and manually gapfill later
   - Retry gapfill_model with different media
   - Inspect draft model to understand gaps
4. Draft model remains in session for manual retry

**Common Recovery Strategies**:

| Issue | Recovery Strategy |
|-------|-------------------|
| Missing essential nutrients | Use build_media to add compounds (nitrogen, sulfur, cofactors) |
| Target too high | Lower target_growth_rate (try 0.001 instead of 0.01) |
| Template mismatch | Rebuild model with different template (GramPositive, Core) |
| Media too minimal | Use predefined media (glucose_minimal_aerobic) |
| Complex biosynthesis | Allow more reactions (keep allow_all_non_grp_reactions=true) |

### Error Responses

**Model Not Found**:
```json
{
  "success": false,
  "error_type": "ModelNotFoundError",
  "message": "Model ID not found in current session",
  "details": {
    "requested_model_id": "model_invalid",
    "available_models": [
      "model_20251027_b4k8c1",
      "model_20251027_x9y2z3"
    ],
    "num_available": 2
  },
  "suggestion": "Use one of the available model IDs from build_model outputs. Models are only available within current session."
}
```

**Media Not Found**:
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

**Gapfilling Infeasible**:
```json
{
  "success": false,
  "error_type": "GapfillingInfeasibleError",
  "message": "Could not find gapfilling solution to achieve target growth rate",
  "details": {
    "model_id": "model_001.draft",
    "original_model_preserved": true,
    "model_id_retained": "model_001.draft",
    "media_id": "media_001",
    "target_growth_rate": 0.01,
    "max_achievable_growth": 0.0,
    "stage_failed": "genomescale_gapfill",
    "template_reactions_available": 2000,
    "possible_causes": [
      "Target medium missing essential nutrients",
      "Model template missing required pathways",
      "Target growth rate too high for available reactions"
    ]
  },
  "recovery_options": [
    "Add more compounds to the medium (check for missing essential nutrients)",
    "Use a lower target_growth_rate (try 0.001)",
    "Use a different template (try GramPositive or Core)",
    "Check if biomass precursors are available in media"
  ],
  "suggestion": "The original draft model (model_001.draft) is still available. Try modifying the medium or lowering the target growth rate."
}
```

**Invalid Target Growth Rate**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid target growth rate specified",
  "details": {
    "provided_value": -0.01,
    "issue": "Growth rate must be positive",
    "valid_range": [0.001, 10.0],
    "typical_range": [0.01, 1.0],
    "recommendation": 0.01
  },
  "suggestion": "Use a positive growth rate. Typical values: 0.01 for permissive gapfilling, 0.1 for moderate, 0.5+ for stringent."
}
```

**Model Has No Biomass Reaction** (Warning only, not an error):
- If model has no biomass reaction, a warning is logged but gapfilling proceeds
- This accommodates offline model building (annotate_with_rast=False) which may produce empty models
- Note: Gapfilling empty models may not produce meaningful results, but is allowed for testing purposes

**Gapfilling Timeout**:
```json
{
  "success": false,
  "error_type": "GapfillingTimeoutError",
  "message": "Gapfilling exceeded maximum time limit",
  "details": {
    "model_id": "model_001",
    "media_id": "media_001",
    "stage": "genomescale_gapfill",
    "time_elapsed": 600,
    "timeout_limit": 600
  },
  "suggestion": "Large models or complex gapfilling may take too long. Try: 1) Use simpler media with fewer compounds, 2) Use lower target_growth_rate, or 3) Use Core template for faster gapfilling."
}
```

## Behavioral Specification

### Two-Stage Gapfilling Process

The gapfilling follows the ModelSEEDpy workflow from build_model.ipynb:

#### Stage 1: ATP Correction (MSATPCorrection)

**Purpose**: Ensure ATP production pathways work across multiple media conditions

**Process**:
1. Load default test media (54 standard media from ModelSEEDpy)
2. For each test medium:
   - Set model medium to test conditions
   - Attempt to activate ATPM reaction (ATP maintenance)
   - Check if ATP production is feasible
3. For media where ATP production fails:
   - Run targeted gapfilling to enable ATP production
   - Add minimal reactions from Core template
4. Integrate ATP correction solutions into model
5. Expand model to genome-scale template

**Why ATP Correction Matters**:
- Draft models often have broken ATP production pathways
- ATP is required for growth (biomass reaction needs ATP)
- Testing across multiple media finds pathway gaps
- Ensures model robustness across conditions

**ATP Correction Outcomes**:
- **Best case**: All 54 media pass without additions (0 reactions added)
- **Typical case**: 20-30 media pass, few reactions added for others
- **Worst case**: Many media fail, requires multiple reactions
- **Some media**: No solution found (acceptable, noted in output)

**Default Test Media Examples**:
- Glc.O2: Glucose + oxygen (aerobic)
- Glc: Glucose only (anaerobic)
- Ac.O2: Acetate + oxygen
- Pyr.O2: Pyruvate + oxygen
- Glyc.O2: Glycerol + oxygen
- And 49 more variations...

#### Stage 2: Genome-Scale Gapfilling (MSGapfill)

**Purpose**: Add minimal reactions to enable growth in target medium

**Process**:
1. Load gapfilled model from ATP correction stage
2. Set model medium to target media (from media_id)
3. Attempt FBA to check current growth rate
4. If growth < target_growth_rate:
   - Formulate gapfilling problem as MILP
   - Minimize: number of reactions added
   - Constraint: achieve target_growth_rate
   - Source: reactions from template (GramNegative, etc.)
5. Solve gapfilling MILP
6. If solution found:
   - Add reactions to model
   - Auto-generate exchange reactions for new metabolites
   - Create new model with .gf suffix
7. Verify final growth rate meets target

**Gapfilling Strategy**:
- **Minimize reactions**: Add as few reactions as possible
- **Template-based**: Only add reactions from template
- **Directionality**: Can add reactions forward, reverse, or bidirectional
- **Exchange generation**: Auto-create EX_ reactions for boundary metabolites

**Why Genome-Scale Gapfilling is Needed**:
- ATP correction only fixes energy metabolism
- Biosynthetic pathways may still be incomplete
- Biomass precursors may not be synthesizable
- Genome-scale gapfilling completes missing pathways

### Complete Gapfilling Workflow

**Step 1: Validate Input**
1. Check model_id exists in session
2. Check media_id exists in session
3. Verify target_growth_rate is valid
4. Verify model has biomass reaction
5. If any validation fails, return error

**Step 2: Load Model and Media**
1. Retrieve COBRApy model from session: `session.models[model_id]`
2. Retrieve MSMedia object from session: `session.media[media_id]`
3. Create copy of model for gapfilling (preserve original)

**Step 3: Check Baseline Growth**
1. Set model medium to target media
2. Run FBA: `solution = model.optimize()`
3. Record baseline growth rate
4. If already meets target, skip gapfilling (return original with note)

**Step 4: Load Templates**
1. Load Core template for ATP correction
2. Load genome-scale template (same as used in build_model)
3. Templates loaded from ModelSEEDpy template library

**Step 5: ATP Correction (if gapfill_mode includes it)**
1. Create MSATPCorrection object:
   - Model: draft model
   - Core template: Core-V5.2
   - Test media: 54 default media
   - ATPM reaction: ATPM_c0
2. Run `evaluate_growth_media()` to test all media
3. Run `determine_growth_media()` to identify which media need gapfilling
4. Run `apply_growth_media_gapfilling()` to add ATP pathway reactions
5. Run `expand_model_to_genome_scale()` to add genome-scale template
6. Run `build_tests()` to create test conditions
7. Collect ATP correction statistics

**Step 6: Genome-Scale Gapfilling (if gapfill_mode includes it)**
1. Create MSGapfill object:
   - Model: ATP-corrected model
   - Template: genome-scale template
   - Test conditions: from ATP correction
   - Target: bio1 (biomass)
2. Run `run_gapfilling(media, target_growth_rate)`:
   - Formulate MILP problem
   - Solve for minimal reaction set
   - Return solution: {reversed: {}, new: {rxn_id: direction}}
3. Parse gapfilling solution
4. Integrate reactions into model

**Step 7: Integrate Gapfilling Solutions**
1. For each reaction in solution:
   - Load reaction from template
   - Convert to COBRApy reaction
   - Set directionality (forward, reverse, reversible)
   - Add to model
2. Auto-generate exchange reactions:
   - Find boundary metabolites (e0 compartment)
   - Create EX_ reactions for new metabolites
   - Add to model

**Step 8: Verify Gapfilling Success**
1. Set model medium to target media
2. Run FBA on gapfilled model
3. Check growth_rate_after ≥ target_growth_rate
4. If successful: proceed to finalize
5. If failed: return error with diagnostics

**Step 9: Finalize Gapfilled Model**
1. Generate new model_id: `{original_model_id}.gf`
2. Store gapfilled model in session: `session.models[new_model_id] = gapfilled_model`
3. Keep original model unchanged
4. Collect statistics on added reactions

**Step 10: Build Response**
1. Query ModelSEED database for reaction names/equations
2. Build reactions_added array with human-readable info
3. Compile ATP correction and genome-scale stats
4. Return success response

### Gapfilling Solution Format

From ModelSEEDpy, gapfilling returns:

```python
{
  'reversed': {},  # Existing reactions reversed
  'new': {
    'rxn05459_c0': '>',   # Forward direction
    'rxn05481_c0': '<',   # Reverse direction
    'rxn00599_c0': '>',   # Forward
    'rxn02185_c0': '<',   # Reverse
    'EX_cpd01981_e0': '>' # Exchange reaction
  },
  'media': <MSMedia object>,
  'target': 'bio1',
  'minobjective': 0.01
}
```

**Direction Symbols**:
- `>` = Forward direction (0, 1000 bounds)
- `<` = Reverse direction (-1000, 0 bounds)
- `=` = Reversible (-1000, 1000 bounds)

### Reaction Integration Pattern

```python
from modelseedpy.core.msmodel import get_reaction_constraints_from_direction

# Convert direction symbol to bounds
direction = '>'  # Forward
bounds = get_reaction_constraints_from_direction(direction)
# Returns: (0, 1000)

direction = '<'  # Reverse
bounds = get_reaction_constraints_from_direction(direction)
# Returns: (-1000, 0)
```

## Example Usage Scenarios

### Example 1: Gapfill for Glucose Minimal Media

**User Intent**: "Gapfill my E. coli model for growth in glucose minimal media"

**AI Assistant Workflow**:
1. User has already created model_001 (from build_model)
2. User has already created media_001 (glucose minimal media from build_media)
3. Call gapfill_model:

```json
{
  "model_id": "model_001",
  "media_id": "media_001",
  "target_growth_rate": 0.01
}
```

**Response**:
```json
{
  "success": true,
  "model_id": "model_001.gf",
  "growth_rate_before": 0.0,
  "growth_rate_after": 0.874,
  "gapfilling_successful": true,
  "num_reactions_added": 4,
  "reactions_added": [
    {
      "id": "rxn05459_c0",
      "name": "Shikimate kinase",
      "direction": "forward"
    },
    {
      "id": "rxn05481_c0",
      "name": "3-dehydroquinate synthase",
      "direction": "reverse"
    },
    {
      "id": "rxn00599_c0",
      "name": "Chorismate synthase",
      "direction": "forward"
    },
    {
      "id": "rxn02185_c0",
      "name": "Anthranilate synthase",
      "direction": "reverse"
    }
  ],
  "atp_correction": {
    "performed": true,
    "media_tested": 54,
    "media_passed": 54,
    "reactions_added": 0
  }
}
```

**AI Response to User**:
"I've successfully gapfilled your E. coli model (model_001.gf) for growth in glucose minimal media. The model can now grow at 0.874 1/h (up from 0.0). I added 4 reactions from the shikimate and chorismate biosynthesis pathways. The ATP correction stage passed all 54 test media without needing additional reactions, indicating the model's energy metabolism is already complete."

### Example 2: Gapfilling Failure - Missing Nutrients

**User Intent**: "Gapfill for growth in a very minimal medium"

**AI Assistant Attempt**:
```json
{
  "model_id": "model_001",
  "media_id": "media_very_minimal",
  "target_growth_rate": 0.01
}
```

**Error Response**:
```json
{
  "success": false,
  "error_type": "GapfillingInfeasibleError",
  "message": "Could not find gapfilling solution to achieve target growth rate",
  "details": {
    "target_growth_rate": 0.01,
    "max_achievable_growth": 0.0,
    "possible_causes": [
      "Target medium missing essential nutrients",
      "Model template missing required pathways"
    ]
  },
  "suggestion": "Try adding more compounds to the medium. Essential nutrients may be missing."
}
```

**AI Recovery**:
1. Call `build_media` with more complete nutrient set
2. Retry gapfilling with new media
3. AI: "The minimal medium was too restrictive. I've created a more complete minimal medium (media_002) with essential salts and nitrogen sources. Let me retry gapfilling..."

### Example 3: Already Growing (No Gapfilling Needed)

**User Intent**: "Gapfill my model for rich media"

**AI Assistant Call**:
```json
{
  "model_id": "model_complete",
  "media_id": "media_rich",
  "target_growth_rate": 0.01
}
```

**Response**:
```json
{
  "success": true,
  "model_id": "model_complete.gf",
  "growth_rate_before": 0.95,
  "growth_rate_after": 0.95,
  "gapfilling_successful": true,
  "num_reactions_added": 0,
  "reactions_added": [],
  "atp_correction": {
    "performed": true,
    "media_tested": 54,
    "media_passed": 54,
    "reactions_added": 0
  },
  "genomescale_gapfill": {
    "performed": false,
    "note": "Model already meets target growth rate"
  }
}
```

**AI Response to User**:
"Your model (model_complete) is already growing at 0.95 1/h in the rich media, which exceeds the target of 0.01 1/h. No gapfilling was needed. I've created model_complete.gf which is identical to the original but ready for FBA analysis."

### Example 4: ATP Correction Adds Reactions

**User Intent**: "Gapfill a minimal core metabolism model"

**AI Assistant Call**:
```json
{
  "model_id": "model_core_minimal",
  "media_id": "media_glucose",
  "target_growth_rate": 0.01
}
```

**Response**:
```json
{
  "success": true,
  "model_id": "model_core_minimal.gf",
  "growth_rate_before": 0.0,
  "growth_rate_after": 0.45,
  "num_reactions_added": 8,
  "atp_correction": {
    "performed": true,
    "media_tested": 54,
    "media_passed": 27,
    "media_failed": 27,
    "reactions_added": 5,
    "failed_media_examples": [
      "Etho.O2",
      "mal-L",
      "Pyr.SO4",
      "H2.SO4"
    ]
  },
  "genomescale_gapfill": {
    "performed": true,
    "reactions_added": 3
  }
}
```

**AI Response to User**:
"I've gapfilled your core model (model_core_minimal.gf) and it now grows at 0.45 1/h. The ATP correction stage found ATP production issues in 27 of 54 test media and added 5 reactions to fix them. The genome-scale gapfilling then added 3 more reactions for growth in glucose. Total: 8 reactions added."

## Integration with Other Tools

### Depends On: build_model

The gapfill_model tool requires a model from build_model:

**Workflow**:
1. User calls `build_model` → creates draft model → returns model_001
2. User calls `gapfill_model` with model_001.draft → creates gapfilled model → returns model_001.draft.gf

**Draft Model Characteristics** (from build_model):
- Typically cannot grow (growth_rate = 0.0)
- Based on template matching
- May have incomplete pathways
- Missing reactions for biomass precursors

### Depends On: build_media

The gapfill_model tool requires a medium from build_media:

**Workflow**:
1. User calls `build_media` → creates medium → returns media_001
2. User calls `gapfill_model` with media_001 → gapfills for that medium

**Media Requirements**:
- Must contain all essential nutrients for growth
- Carbon source, nitrogen source, electron acceptor
- Cofactors, vitamins (if not synthesizable)

### Used By: run_fba

The gapfilled model is typically used for FBA:

**Workflow**:
1. gapfill_model → creates model_001.draft.gf
2. run_fba with model_001.gf → predicts growth and fluxes

**Expected FBA Results**:
- Status: "optimal"
- Growth rate: ≥ target_growth_rate (often higher)
- Active reactions: All added reactions should have non-zero flux

### Session Storage

**Storage Pattern**:
```python
# Original model preserved
original_model = session.models[model_id]

# New gapfilled model created
gapfilled_model = create_gapfilled_copy(original_model)
new_model_id = f"{model_id}.gf"
session.models[new_model_id] = gapfilled_model

# Both models available
session.models[model_id]      # Original draft model
session.models[new_model_id]  # Gapfilled model
```

**Memory Considerations**:
- Each gapfilled model: 1-5 MB
- Original model preserved (adds to memory)
- Typical session: 2-4 models (1-2 originals, 1-2 gapfilled)
- Total memory: 10-20 MB (acceptable)

## Data Flow Diagram

```
Input (model_id, media_id, target_growth_rate)
  ↓
Validate model and media exist
  ↓
Load model and media from session
  ↓
Copy model (preserve original)
  ↓
Check baseline growth rate
  ↓
Stage 1: ATP Correction
  - Load default test media
  - Test ATP production in each medium
  - Gapfill for failed media
  - Expand to genome-scale
  ↓
Stage 2: Genome-Scale Gapfilling
  - Set target medium
  - Formulate MILP problem
  - Solve for minimal reaction set
  - Integrate reactions into model
  ↓
Verify final growth rate
  ↓
Generate new model_id (.gf suffix)
  ↓
Store gapfilled model in session
  ↓
Query database for reaction metadata
  ↓
Return response (JSON)
```

## ModelSEEDpy Integration

### ATP Correction Library Usage

```python
from modelseedpy import MSATPCorrection
from modelseedpy.core.msatpcorrection import load_default_medias

# Load default test media (54 media)
default_medias = load_default_medias()
# Returns: [(media, min_objective), ...]

# Create ATP correction object
atp_correction = MSATPCorrection(
    model,                    # Draft model
    core_template,           # Core template for gapfilling
    default_medias,          # Test media
    compartment='c0',        # Cytosol
    atp_hydrolysis_id='ATPM_c0',
    load_default_medias=False
)

# Run ATP correction workflow
media_eval = atp_correction.evaluate_growth_media()
atp_correction.determine_growth_media()
atp_correction.apply_growth_media_gapfilling()
atp_correction.expand_model_to_genome_scale()
tests = atp_correction.build_tests()

# Access results
for t in tests:
    media_id = t['media'].id
    threshold = t['threshold']
    stats = atp_correction.media_gapfill_stats[t['media']]
    # stats: None (no solution) or {'reversed': {}, 'new': {}}
```

### Genome-Scale Gapfilling Library Usage

```python
from modelseedpy import MSGapfill, MSMedia

# Create target media
media = MSMedia.from_dict({
    'cpd00027': (-5, 100),  # Glucose
    'cpd00007': (-10, 100), # O2
    # ... more compounds
})

# Create gapfill object
gapfill = MSGapfill(
    model,                           # ATP-corrected model
    default_gapfill_templates=[template],  # Genome-scale template
    test_conditions=tests,           # From ATP correction
    default_target='bio1'            # Biomass reaction
)

# Run gapfilling
gapfill_solution = gapfill.run_gapfilling(
    media,
    target=0.01  # Target growth rate
)

# Solution format
# {
#   'reversed': {},
#   'new': {'rxn_id': 'direction'},
#   'media': <MSMedia>,
#   'target': 'bio1',
#   'minobjective': 0.01
# }
```

### Reaction Integration Pattern

```python
from modelseedpy import MSBuilder
from modelseedpy.core.msmodel import get_reaction_constraints_from_direction

def integrate_gapfill_solution(template, model, solution):
    """Integrate gapfilling solution into model."""
    added_reactions = []

    # Process new reactions
    for rxn_id, direction in solution['new'].items():
        # Skip exchange reactions (handled separately)
        if rxn_id.startswith('EX_'):
            continue

        # Convert model reaction ID (indexed) to template reaction ID (non-indexed)
        # Model uses: rxn05481_c0, Template uses: rxn05481_c
        # Strip trailing '0' to convert indexed (_c0) to non-indexed (_c)
        if rxn_id.endswith('0'):
            template_rxn_id = rxn_id[:-1]  # rxn05481_c0 → rxn05481_c
        else:
            template_rxn_id = rxn_id  # Already in template format

        # Get reaction from template
        template_reaction = template.reactions.get_by_id(template_rxn_id)

        # Convert to COBRApy reaction
        model_reaction = template_reaction.to_reaction(model)

        # Set bounds based on direction
        lb, ub = get_reaction_constraints_from_direction(direction)
        model_reaction.lower_bound = lb
        model_reaction.upper_bound = ub

        added_reactions.append(model_reaction)

    # Add all reactions to model
    model.add_reactions(added_reactions)

    # Auto-generate exchange reactions
    exchanges = MSBuilder.add_exchanges_to_model(model)

    return added_reactions, exchanges
```

## Performance Considerations

### Expected Performance

**Typical Execution Time**:
- Small model (100 reactions, Core template): 10-30 seconds
- Medium model (500 reactions, GramNegative): 1-3 minutes
- Large model (1500+ reactions, GramNegative): 3-10 minutes

**Performance Factors**:
1. **Model size**: Larger models take longer
2. **Media complexity**: More compounds = more constraints
3. **Template size**: Larger template = more candidate reactions
4. **ATP correction**: Testing 54 media takes significant time
5. **MILP solving**: Gapfilling is NP-hard, can be slow

**Performance Breakdown**:
- ATP Correction: 60-80% of time (tests many media)
- Genome-scale gapfilling: 20-40% of time
- Reaction integration: < 5% of time

**Timeout Protection**:
- Set maximum gapfilling time: 10 minutes
- If timeout, return error with partial results
- User can retry with simpler conditions

## Quality Requirements

### Correctness
- ✅ Gapfilled model achieves target growth rate
- ✅ All added reactions are from template
- ✅ Directionality correctly applied
- ✅ Original model unchanged in session
- ✅ Exchange reactions auto-generated

### Reliability
- ✅ ATP correction handles media failures gracefully
- ✅ Infeasible gapfilling returns clear error
- ✅ Solver failures caught and reported
- ✅ Partial gapfilling never stored

### Usability
- ✅ Human-readable reaction names in output
- ✅ Before/after growth rates shown
- ✅ Clear indication of which stage failed
- ✅ Helpful suggestions for recovery

### Performance
- ✅ Small models: < 1 minute
- ✅ Medium models: < 5 minutes
- ✅ Timeout at 10 minutes with clear error

## Testing Considerations

### Test Cases

**Valid Inputs**:
1. Draft model in glucose minimal media
2. Draft model in rich media
3. Model that already grows (skip gapfilling)
4. Different target growth rates (0.001, 0.01, 0.1)
5. ATP-only mode
6. Genomescale-only mode
7. Full mode (both stages)

**Invalid Inputs**:
1. Non-existent model_id
2. Non-existent media_id
3. Negative target growth rate
4. Zero target growth rate
5. Invalid gapfill_mode
6. Model without biomass reaction (warning only, not error)

**Edge Cases**:
1. Model already at target growth (0 reactions added)
2. Infeasible gapfilling (no solution exists)
3. All ATP test media fail
4. Large number of reactions needed (>100)
5. Gapfilling timeout

**Expected Outcomes**:
1. **Most cases**: 0-20 reactions added, successful
2. **Complex cases**: 20-50 reactions, may take several minutes
3. **Infeasible cases**: Clear error, helpful suggestions

### Integration Tests

1. build_model → gapfill_model → run_fba (full workflow)
2. Multiple gapfilling with different media
3. Gapfill same model twice (creates two .gf variants)
4. Session persistence of gapfilled models
5. ATP correction with Core template
6. Genome-scale gapfilling with GramNegative template

## Future Enhancements

### Post-MVP Features (Not in Specification)

**v0.2.0 - Gapfilling Options**:
- `gapfill_strategy`: "minimal", "balanced", "permissive"
- `max_reactions`: Cap on number of reactions to add
- `blocked_reactions`: Reactions not to add
- `preferred_reactions`: Reactions to add if possible

**v0.3.0 - Multi-Media Gapfilling**:
- `media_ids`: Array of media (gapfill for all)
- Pareto-optimal gapfilling (minimize reactions across media)

**v0.4.0 - Iterative Gapfilling**:
- `iterative`: Gapfill, test, refine loop
- `max_iterations`: Limit refinement iterations
- Pathway completion verification

**v0.5.0 - Gapfilling Analysis**:
- `explain_gapfilling`: Detailed pathway analysis
- `alternative_solutions`: Other reaction sets
- `gapfilling_confidence`: Score added reactions

## Implementation Notes (Post-MVP Refactoring)

> **⚠️ CRITICAL**: The following patterns were established during Phase 2 refactoring (October 2025). These are MANDATORY patterns to prevent bugs.

### ✅ Canonical Pattern: Exchange Reaction Creation

**CORRECT** - Use ModelSEEDpy's MSBuilder helper:

```python
from modelseedpy.core.msbuilder import MSBuilder

# When gapfilling suggests missing exchange reactions
exchange_reactions_to_add = [
    rxn_id for rxn_id in new_reactions.keys()
    if rxn_id.startswith('EX_') and rxn_id not in model.reactions
]

if exchange_reactions_to_add:
    # MSBuilder handles ALL complexity:
    # - Correct stoichiometry
    # - Metabolite creation/linking
    # - Default bounds
    # - All edge cases
    MSBuilder.add_exchanges_to_model(model, uptake_rate=100)

# Then update bounds based on gapfilling directions
for rxn_id, direction in new_reactions.items():
    if rxn_id.startswith('EX_'):
        if rxn_id in model.reactions:
            rxn = model.reactions.get_by_id(rxn_id)
            lb, ub = get_reaction_constraints_from_direction(direction)
            rxn.lower_bound = lb
            rxn.upper_bound = ub
```

**❌ ANTI-PATTERN** - Do NOT manually create exchange reactions:

```python
# ❌ WRONG: Manual exchange creation with COBRApy
from cobra import Reaction, Metabolite

exch_rxn = Reaction(rxn_id)
metabolite = Metabolite(compound_id, compartment='e0')
exch_rxn.add_metabolites({metabolite: 1.0})
exch_rxn.lower_bound = lb
exch_rxn.upper_bound = ub
model.add_reactions([exch_rxn])  # Duplicates MSBuilder logic, misses edge cases
```

**Why This Matters**:
- MSBuilder is ModelSEEDpy's official helper for exchange creation
- Manual creation duplicates internal logic and misses edge cases
- MSBuilder handles metabolite linking, stoichiometry, all compartments
- Reduces code by ~40 lines and eliminates bugs

### ✅ Canonical Pattern: Media Application in check_baseline_growth()

**CORRECT** - Use shared utility:

```python
from gem_flux_mcp.utils.media import apply_media_to_model

def check_baseline_growth(model, media, objective="bio1"):
    # Apply media using shared utility
    apply_media_to_model(model, media, compartment="e0")

    # CRITICAL: Set BOTH objective and direction
    if objective in model.reactions:
        model.objective = objective
        model.objective_direction = "max"  # Don't forget this!

    solution = model.optimize()
    return solution.objective_value if solution.status == "optimal" else 0.0
```

**❌ ANTI-PATTERN** - Do NOT set only model.objective:

```python
# ❌ WRONG: Setting only objective (doesn't change direction!)
model.objective = objective  # Direction stays at previous value!
```

**Why This Matters**:
- COBRApy requires setting BOTH `model.objective` AND `model.objective_direction`
- Setting only `model.objective` does NOT change the optimization direction
- This was a critical bug that caused incorrect growth rate calculations

### Key Implementation Details

1. **Exchange Reactions**
   - Always use `MSBuilder.add_exchanges_to_model()`
   - Never manually create with COBRApy's Reaction/Metabolite classes

2. **Media Application**
   - Use `gem_flux_mcp.utils.media.apply_media_to_model()`
   - Handles both MSMedia objects and dict formats

3. **Objective Setting**
   - Always set BOTH `model.objective` and `model.objective_direction`
   - Default direction is "max" for growth/biomass objectives

4. **Gapfilling Solution Integration**
   - MSGapfill returns solution dict with 'new' and 'reversed' keys
   - Exchange reactions ARE integrated (not skipped)
   - Use MSBuilder for missing exchanges

### Related Code

- **Implementation**: `src/gem_flux_mcp/tools/gapfill_model.py`
- **Shared Utility**: `src/gem_flux_mcp/utils/media.py`
- **Tests**: `tests/unit/test_gapfill_model.py`

## Related Specifications

- **001-system-overview.md**: Overall gapfilling workflow
- **002-data-formats.md**: Gapfilling solution format
- **003-build-media-tool.md**: Creates media_id for gapfilling
- **004-build-model-tool.md**: Creates model_id to gapfill
- **006-run-fba-tool.md**: Analyzes gapfilled models
- **007-database-integration.md**: Reaction name lookups for output

---

**Document Status**: ✅ Ready for Implementation (Updated with refactoring patterns)
**Last Updated**: October 29, 2025 (Post-Phase 2 refactoring)
**Next Spec**: 006-run-fba-tool.md
