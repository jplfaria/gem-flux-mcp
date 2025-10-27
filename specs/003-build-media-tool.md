# build_media Tool Specification - Gem-Flux MCP Server

**Type**: Tool Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding ModelSEED identifiers and terminology)
- Read: 002-data-formats.md (for media specification format details)

## Purpose

The `build_media` tool creates a growth medium composition from a list of ModelSEED compound IDs. It defines which nutrients are available to a metabolic model and at what uptake/secretion rates. The tool validates all compound IDs against the ModelSEED database and returns a media object with human-readable compound names that can be used by subsequent operations (gapfilling and FBA).

## Tool Overview

**What it does**:
- Creates a growth medium from ModelSEED compound IDs
- Validates all compound IDs against the ModelSEED database
- Applies default uptake bounds to all compounds
- Allows custom bounds for specific compounds
- Returns media_id for use in gapfill_model and run_fba
- Provides human-readable compound names for LLM interpretation

**What it does NOT do**:
- Does not suggest which compounds to include (AI assistant's role)
- Does not optimize media composition
- Does not validate biological plausibility
- Does not modify existing media (creates new media each time)

## Input Specification

### Input Parameters

```json
{
  "compounds": [
    "cpd00027",
    "cpd00007",
    "cpd00001",
    "cpd00009",
    "cpd00067",
    "cpd00013"
  ],
  "default_uptake": 100.0,
  "custom_bounds": {
    "cpd00027": [-5, 100],
    "cpd00007": [-10, 100]
  }
}
```

### Parameter Descriptions

**compounds** (required)
- Type: Array of strings
- Format: Each string must match pattern `cpd\d{5}` (e.g., "cpd00027")
- Minimum length: 1 compound
- Maximum length: No hard limit (practical limit ~500 for performance)
- Purpose: List of compounds available in the growth medium
- Validation: All compound IDs must exist in ModelSEED database
- Typical values:
  - Minimal media: 10-30 compounds (glucose + salts)
  - Rich media: 100+ compounds (complex media like LB)

**default_uptake** (optional)
- Type: Number (float)
- Default: 100.0
- Units: mmol/gDW/h (millimoles per gram dry weight per hour)
- Range: 0.0 to 1000.0 (typical: 10.0 to 100.0)
- Purpose: Default maximum uptake rate for all compounds not specified in custom_bounds
- Applied as: Lower bound = -default_uptake, Upper bound = 100.0
- Example: default_uptake=100.0 creates bounds (-100, 100) for each compound

**custom_bounds** (optional)
- Type: Object mapping compound IDs to [lower, upper] arrays
- Format: `{"cpd00027": [-5, 100], "cpd00007": [-10, 100]}`
- Purpose: Override default bounds for specific compounds
- Lower bound: Negative number representing maximum uptake rate
- Upper bound: Positive number representing maximum secretion rate
- Validation: lower < upper, both must be valid numbers
- Use cases:
  - Limit carbon source uptake: `"cpd00027": [-5, 100]` (5 mmol/gDW/h glucose max)
  - Aerobic vs anaerobic: `"cpd00007": [-10, 100]` vs `"cpd00007": [0, 0]`
  - Secretion only: `"cpd00011": [0, 100]` (CO2 out, no uptake)

### Validation Rules

**Pre-validation** (before processing):
1. `compounds` array must not be empty
2. All compound IDs must match format `cpd\d{5}`
3. All compound IDs must exist in ModelSEED database
4. `default_uptake` must be positive number if provided
5. All custom_bounds keys must be in the compounds list
6. All custom_bounds must have lower < upper
7. No duplicate compound IDs in compounds list

**Validation Behavior**:
- If any compound ID is invalid, return error listing ALL invalid IDs
- If any bound is invalid, return error with specific compound and bound issue
- Do not create partial media - either fully valid or error

## Output Specification

### Successful Response

```json
{
  "success": true,
  "media_id": "media_20251027_a3f9b2",
  "compounds": [
    {
      "id": "cpd00027",
      "name": "D-Glucose",
      "formula": "C6H12O6",
      "bounds": [-5, 100]
    },
    {
      "id": "cpd00007",
      "name": "O2",
      "formula": "O2",
      "bounds": [-10, 100]
    },
    {
      "id": "cpd00001",
      "name": "H2O",
      "formula": "H2O",
      "bounds": [-100, 100]
    },
    {
      "id": "cpd00009",
      "name": "Phosphate",
      "formula": "HO4P",
      "bounds": [-100, 100]
    },
    {
      "id": "cpd00067",
      "name": "H+",
      "formula": "H",
      "bounds": [-100, 100]
    },
    {
      "id": "cpd00013",
      "name": "NH3",
      "formula": "H3N",
      "bounds": [-100, 100]
    }
  ],
  "num_compounds": 6,
  "media_type": "minimal",
  "default_uptake_rate": 100.0,
  "custom_bounds_applied": 2
}
```

### Output Fields

**success**
- Type: Boolean
- Value: `true` for successful media creation
- Always present

**media_id**
- Type: String
- Format: `media_<timestamp>_<random_id>`
- Example: `"media_20251027_a3f9b2"`
- Purpose: Unique identifier to reference this media in gapfill_model and run_fba
- Scope: Valid only within current server session
- Lifecycle: Cleared when server restarts

**compounds**
- Type: Array of compound objects
- Length: Same as input compounds array
- Order: Same order as input compounds array
- Each object contains:
  - **id**: Original ModelSEED compound ID
  - **name**: Human-readable compound name from database
  - **formula**: Molecular formula from database
  - **bounds**: Applied bounds [lower, upper] as array of two numbers
- Purpose: Enable LLM to understand media composition in human terms

**num_compounds**
- Type: Integer
- Value: Total count of compounds in media
- Purpose: Quick summary statistic

**media_type**
- Type: String
- Values: "minimal" or "rich"
- Heuristic: "minimal" if num_compounds < 50, "rich" otherwise
- Purpose: High-level classification for LLM context

**default_uptake_rate**
- Type: Number (float)
- Value: The default_uptake value used (from input or default)
- Purpose: Document default bounds applied

**custom_bounds_applied**
- Type: Integer
- Value: Count of compounds with custom bounds
- Purpose: Summary of customization level

### Error Responses

**Invalid Compound IDs**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid compound IDs not found in ModelSEED database",
  "details": {
    "invalid_ids": ["cpd99999", "cpd88888"],
    "valid_example": "cpd00027",
    "num_invalid": 2,
    "num_valid": 4
  },
  "suggestion": "Use search_compounds tool to find valid compound IDs by name. Example: search_compounds('glucose')"
}
```

**Empty Compounds List**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Compounds list cannot be empty",
  "details": {
    "compounds_provided": 0,
    "minimum_required": 1
  },
  "suggestion": "Provide at least one compound ID. For minimal media, include carbon source (e.g., cpd00027 for glucose), electron acceptor (e.g., cpd00007 for O2), and essential nutrients."
}
```

**Invalid Compound ID Format**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid compound ID format",
  "details": {
    "invalid_formats": ["compound_001", "glc"],
    "expected_format": "cpd followed by 5 digits",
    "examples": ["cpd00001", "cpd00027", "cpd00007"]
  },
  "suggestion": "ModelSEED compound IDs must match pattern 'cpd' followed by exactly 5 digits. Use search_compounds to find IDs by name."
}
```

**Invalid Bounds**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid bounds for compound",
  "details": {
    "compound_id": "cpd00027",
    "provided_bounds": [100, -5],
    "issue": "lower bound must be less than upper bound",
    "valid_example": [-5, 100]
  },
  "suggestion": "Bounds format: [lower, upper] where lower < upper. Use negative lower bound for uptake, positive upper bound for secretion."
}
```

**Custom Bounds for Unknown Compound**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Custom bounds specified for compound not in media",
  "details": {
    "compound_id": "cpd00100",
    "in_compounds_list": false
  },
  "suggestion": "Add 'cpd00100' to the compounds array before specifying custom bounds for it."
}
```

**Duplicate Compound IDs**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Duplicate compound IDs found in compounds list",
  "details": {
    "duplicate_ids": ["cpd00027"],
    "occurrences": {
      "cpd00027": 2
    }
  },
  "suggestion": "Remove duplicate compound IDs from the compounds list. Each compound should appear only once."
}
```

## Behavioral Specification

### Media Creation Process

**Step 1: Validate Input**
1. Check compounds array is not empty
2. Validate all compound IDs match format `cpd\d{5}`
3. Query ModelSEED database to verify all compound IDs exist
4. If any validation fails, return error with all issues (don't stop at first error)

**Step 2: Validate Custom Bounds**
1. For each custom_bounds entry:
   - Verify compound_id is in compounds list
   - Verify bounds format is [lower, upper] array
   - Verify lower < upper
   - Verify both are valid numbers
2. If any validation fails, return error

**Step 3: Create MSMedia Object**
1. Generate unique media_id (format: `media_<timestamp>_<random>`)
2. For each compound in compounds list:
   - If compound has custom_bounds: use those bounds
   - Otherwise: use (-default_uptake, 100.0)
   - Add compartment suffix _e0 to compound ID internally
3. Create MSMedia object via `MSMedia.from_dict()`

**Step 4: Enrich with Database Information**
1. Query ModelSEED database for each compound
2. Retrieve: name, formula, aliases
3. Build response compounds array with enriched data

**Step 5: Generate Response**
1. Return success response with:
   - Generated media_id
   - Enriched compounds array
   - Summary statistics
2. Store MSMedia object in session storage keyed by media_id

### Bound Interpretation

**Negative Lower Bound = Uptake**:
- Bound: `[-5, 100]`
- Meaning: Maximum uptake rate is 5 mmol/gDW/h
- During FBA: Exchange reaction can have flux up to -5

**Positive Upper Bound = Secretion**:
- Bound: `[-5, 100]`
- Meaning: Maximum secretion rate is 100 mmol/gDW/h
- During FBA: Exchange reaction can have flux up to +100

**Zero Bounds = Blocked**:
- Bound: `[0, 0]`
- Meaning: No exchange allowed (compound unavailable)
- Use case: Model anaerobic conditions by blocking O2

**Unrestricted**:
- Bound: `[-1000, 1000]`
- Meaning: Effectively unlimited exchange
- Use case: Rich media with abundant nutrients

### Media Classification Heuristic

**Minimal Media** (num_compounds < 50):
- Defined composition
- Essential nutrients only
- Typical: glucose + salts + nitrogen source
- Example: M9 minimal media (~20 compounds)

**Rich Media** (num_compounds ≥ 50):
- Complex composition
- Many amino acids, vitamins, cofactors
- Typical: LB, YPD, complex media (100+ compounds)

This is a heuristic only - not a strict biological definition.

## Example Usage Scenarios

### Example 1: Glucose Minimal Media (Aerobic)

**User Intent**: "Create a minimal glucose medium for E. coli under aerobic conditions"

**AI Assistant Approach**:
1. Identify essential compounds:
   - Carbon source: cpd00027 (D-Glucose)
   - Electron acceptor: cpd00007 (O2)
   - Essential nutrients: H2O, NH3, phosphate, sulfate, trace metals
2. Set glucose uptake limit (5 mmol/gDW/h is typical)
3. Call build_media:

```json
{
  "compounds": [
    "cpd00027",  "cpd00007",  "cpd00001",  "cpd00009",
    "cpd00011",  "cpd00013",  "cpd00067",  "cpd00099",
    "cpd00149",  "cpd00205",  "cpd00254",  "cpd00971",
    "cpd10515",  "cpd10516",  "cpd00063",  "cpd00030",
    "cpd00034",  "cpd00048",  "cpd00058",  "cpd00244"
  ],
  "default_uptake": 100.0,
  "custom_bounds": {
    "cpd00027": [-5, 100],
    "cpd00007": [-10, 100]
  }
}
```

**Response**:
```json
{
  "success": true,
  "media_id": "media_001",
  "compounds": [
    {"id": "cpd00027", "name": "D-Glucose", "formula": "C6H12O6", "bounds": [-5, 100]},
    {"id": "cpd00007", "name": "O2", "formula": "O2", "bounds": [-10, 100]},
    ...
  ],
  "num_compounds": 20,
  "media_type": "minimal"
}
```

**AI Response to User**:
"I've created a glucose minimal medium (media_001) with 20 essential compounds. Glucose uptake is limited to 5 mmol/gDW/h, and oxygen is available at 10 mmol/gDW/h for aerobic respiration."

### Example 2: Anaerobic Conditions

**User Intent**: "Create the same medium but for anaerobic growth"

**AI Assistant Approach**:
1. Same compounds as aerobic
2. Block oxygen by setting bounds to [0, 0]
3. Call build_media:

```json
{
  "compounds": ["cpd00027", "cpd00007", ...],
  "default_uptake": 100.0,
  "custom_bounds": {
    "cpd00027": [-5, 100],
    "cpd00007": [0, 0]
  }
}
```

**Response**:
```json
{
  "success": true,
  "media_id": "media_002",
  "compounds": [
    {"id": "cpd00027", "name": "D-Glucose", "bounds": [-5, 100]},
    {"id": "cpd00007", "name": "O2", "bounds": [0, 0]},
    ...
  ],
  "num_compounds": 20,
  "media_type": "minimal"
}
```

**AI Response to User**:
"I've created an anaerobic glucose medium (media_002). Oxygen exchange is blocked (bounds [0, 0]), forcing the model to use fermentation pathways."

### Example 3: Rich Media

**User Intent**: "Create a rich LB-like medium"

**AI Assistant Approach**:
1. Include amino acids, nucleotides, vitamins, cofactors
2. No strict uptake limits (use default 100.0)
3. Call build_media:

```json
{
  "compounds": [
    "cpd00027", "cpd00007", "cpd00001", "cpd00009", "cpd00013",
    "cpd00035", "cpd00041", "cpd00051", "cpd00053", "cpd00054",
    "cpd00060", "cpd00065", "cpd00066", "cpd00069", "cpd00084",
    ... // 100+ compounds including all amino acids
  ],
  "default_uptake": 100.0
}
```

**Response**:
```json
{
  "success": true,
  "media_id": "media_003",
  "num_compounds": 120,
  "media_type": "rich"
}
```

**AI Response to User**:
"I've created a rich complex medium (media_003) with 120 compounds including all amino acids, nucleotides, vitamins, and cofactors. This mimics LB medium composition."

### Example 4: Handling Errors

**User Intent**: "Create a glucose medium" (but uses wrong compound ID)

**AI Assistant Attempt** (with error):
```json
{
  "compounds": ["glucose", "cpd00007", "cpd00001"]
}
```

**Error Response**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid compound ID format",
  "details": {
    "invalid_formats": ["glucose"],
    "expected_format": "cpd followed by 5 digits"
  },
  "suggestion": "Use search_compounds to find IDs by name."
}
```

**AI Recovery**:
1. Call `search_compounds("glucose")`
2. Get result: `{"id": "cpd00027", "name": "D-Glucose"}`
3. Retry with correct ID:

```json
{
  "compounds": ["cpd00027", "cpd00007", "cpd00001"]
}
```

**Success Response**:
```json
{
  "success": true,
  "media_id": "media_004"
}
```

**AI Response to User**:
"I've created a glucose minimal medium (media_004). Note: I converted 'glucose' to the ModelSEED ID 'cpd00027' (D-Glucose)."

## Integration with Other Tools

### Used By: gapfill_model

The gapfill_model tool accepts media_id to specify growth conditions:

```json
{
  "model_id": "model_001",
  "media_id": "media_001"
}
```

Gapfilling adds reactions to enable growth in the specified media.

### Used By: run_fba

The run_fba tool accepts media_id to set exchange reaction bounds:

```json
{
  "model_id": "model_001.gf",
  "media_id": "media_001"
}
```

FBA determines optimal flux distribution given media constraints.

### Session Storage

**Lifecycle**:
1. build_media creates MSMedia object
2. MSMedia stored in session dict: `session.media[media_id] = msmedia_object`
3. Later tools retrieve: `msmedia = session.media[media_id]`
4. Cleared on server restart

**Memory Considerations**:
- Each MSMedia object: ~10-50 KB
- Typical session: 1-10 media objects
- Total memory: negligible (<1 MB)

## Data Flow Diagram

```
Input (JSON)
  ↓
Validate compound IDs
  ↓
Query ModelSEED Database
  ↓ (if valid)
Apply default bounds
  ↓
Override with custom bounds
  ↓
Create MSMedia object (ModelSEEDpy)
  ↓
Generate media_id
  ↓
Store in session
  ↓
Enrich with database metadata
  ↓
Return response (JSON)
```

## ModelSEEDpy Integration

### Library Function Used

```python
from modelseedpy import MSMedia

# Create media from compound bounds dictionary
media = MSMedia.from_dict({
    'cpd00027': (-5, 100),      # D-Glucose
    'cpd00007': (-10, 100),     # O2
    'cpd00001': (-100, 100),    # H2O
    # ... more compounds
})
```

**Note**: ModelSEEDpy expects compound IDs without compartment suffixes as keys, bounds as tuples.

### Internal Representation

After creation, MSMedia internally adds compartment suffixes (_e0):
```python
media.get_media_constraints()
# Returns: {
#   'cpd00027_e0': (-5, 100),
#   'cpd00007_e0': (-10, 100),
#   ...
# }
```

This internal representation is used when setting model.medium during FBA.

## Common Media Compositions

### M9 Minimal Media (Glucose)
Essential components (~20 compounds):
- **Carbon source**: cpd00027 (D-Glucose)
- **Electron acceptor**: cpd00007 (O2)
- **Nitrogen source**: cpd00013 (NH3)
- **Sulfur source**: cpd00048 (Sulfate)
- **Phosphate**: cpd00009 (Phosphate)
- **Water**: cpd00001 (H2O)
- **Protons**: cpd00067 (H+)
- **CO2**: cpd00011 (CO2)
- **Trace metals**: cpd00205 (K+), cpd00254 (Mg2+), cpd00063 (Ca2+), cpd00030 (Mn2+), cpd00034 (Zn2+), cpd00058 (Cu2+), cpd00149 (Co2+), cpd10515 (Fe2+), cpd10516 (Fe3+), cpd00244 (Ni2+), cpd00971 (Na+), cpd00099 (Cl-)

### LB-Rich Media
Complex composition (100+ compounds):
- All 20 amino acids
- Nucleotides (A, T, G, C, U bases)
- Vitamins and cofactors
- Trace metals
- Common metabolic intermediates

### Alternative Carbon Sources
Replace cpd00027 with:
- **cpd00029**: Acetate (C2)
- **cpd00186**: Glycerol (C3)
- **cpd00020**: Pyruvate (C3)
- **cpd00036**: Succinate (C4)
- **cpd00024**: Fumarate (C4)
- **cpd00138**: Lactose (C12)

## Performance Considerations

### Expected Performance

**Typical Execution Time**:
- Minimal media (20 compounds): < 100ms
- Rich media (100 compounds): < 500ms
- Very complex (500 compounds): < 2s

**Performance Factors**:
1. Number of compounds (linear scaling)
2. Database query time (negligible with in-memory pandas)
3. MSMedia object creation (fast)

**No Optimization Required for MVP**: Performance is adequate for all typical use cases.

## Future Enhancements

### Post-MVP Features (Not in Specification)

**v0.2.0 - Media Management**:
- `list_media()` - List all media in session
- `delete_media(media_id)` - Remove media from session
- `export_media(media_id)` - Export media to JSON
- `import_media(json_data)` - Import media from JSON

**v0.3.0 - Media Optimization**:
- `optimize_media(model_id, target_growth)` - Find minimal media for growth
- `compare_media(media_id_1, media_id_2)` - Show differences
- `suggest_media_improvements(model_id, media_id)` - Recommend additions

**v0.4.0 - Predefined Media**:
- Library of standard media (M9, LB, etc.)
- `get_standard_media(name)` - Load from library
- Custom media templates

## Quality Requirements

### Correctness
- ✅ All compound IDs validated against database
- ✅ All bounds applied correctly to MSMedia object
- ✅ Custom bounds override default bounds as expected
- ✅ Generated media_id is unique per call

### Reliability
- ✅ Invalid inputs produce clear error messages
- ✅ Errors include actionable suggestions
- ✅ No partial media creation on validation failure

### Usability
- ✅ Human-readable compound names in response
- ✅ Clear documentation of bounds interpretation
- ✅ Examples for common media types
- ✅ Error messages guide recovery

### Performance
- ✅ Response time < 500ms for typical media (20-100 compounds)
- ✅ Memory usage negligible (< 1MB per session)

## Testing Considerations

### Test Cases

**Valid Inputs**:
1. Minimal media with 10 compounds
2. Rich media with 100+ compounds
3. Custom bounds for all compounds
4. Custom bounds for subset of compounds
5. Default uptake values (10, 100, 1000)
6. Anaerobic media (O2 bounds = [0, 0])

**Invalid Inputs**:
1. Empty compounds list
2. Invalid compound ID format
3. Compound IDs not in database
4. Invalid bounds (lower > upper)
5. Custom bounds for compound not in list
6. Duplicate compound IDs
7. Non-numeric default_uptake

**Edge Cases**:
1. Single compound media
2. Very large media (500+ compounds)
3. All compounds with custom bounds
4. Zero default_uptake
5. Large bounds values (> 1000)

### Integration Tests

1. Create media → use in gapfill_model
2. Create media → use in run_fba
3. Create multiple media in same session
4. Server restart clears media

## Related Specifications

- **001-system-overview.md**: Overall architecture and ModelSEED identifier system
- **002-data-formats.md**: Detailed media data format specification
- **005-gapfill-model-tool.md**: Uses media_id for gapfilling
- **006-run-fba-tool.md**: Uses media_id to set exchange bounds
- **007-database-integration.md**: ModelSEED database loading and queries
- **008-compound-lookup-tools.md**: AI uses to find compound IDs by name

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 004-build-model-tool.md
