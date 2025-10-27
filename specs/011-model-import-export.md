# Model Import/Export Tools - Gem-Flux MCP Server

**Type**: MCP Tool Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding MCP tool architecture)
- Read: 002-data-formats.md (for model data format specifications)
- Read: 010-model-storage.md (for understanding model storage and lifecycle)

## Purpose

This specification defines the model import and export tools that enable users to:
- Import existing metabolic models from COBRApy JSON format into the server session
- Export models from the server session to COBRApy JSON format for use in other tools
- Integrate Gem-Flux with external metabolic modeling workflows
- Share models with visualization tools (Escher), analysis platforms (MATLAB COBRA, KBase), and version control systems

These tools bridge the gap between session-based storage (in-memory) and persistent external storage (files).

## Core Design Principles

**COBRApy JSON as Standard Format**:
- COBRApy JSON is the native and primary model format
- Human-readable text format compatible with version control
- Preserves all model metadata (reactions, metabolites, genes, notes, annotations)
- Works with Escher metabolic pathway visualization
- No conversion or translation needed

**Validation on Import**:
- Verify JSON structure conforms to COBRApy format
- Check for required fields (reactions, metabolites)
- Validate reaction stoichiometry and bounds
- Detect and report malformed data

**Seamless Integration**:
- Imported models work identically to built models
- Exported models compatible with COBRApy `load_json_model()`
- No loss of information in round-trip (import → export)

---

## Tool 1: import_model_json

### Purpose

Import a metabolic model from COBRApy JSON format into the server session.

### Input Parameters

```python
{
    "json_string": str,              # Complete model in COBRApy JSON format
    "model_name": str | None = None  # Optional: Override model name from JSON
}
```

**Field Specifications**:

- **json_string**: Model data in COBRApy JSON format
  - Type: String
  - Format: Valid JSON string representing a COBRApy model
  - Size: Typically 100 KB - 50 MB (depends on model size)
  - Required fields in JSON:
    - `"reactions"`: Array of reaction objects
    - `"metabolites"`: Array of metabolite objects
    - `"genes"`: Array of gene objects (can be empty)
    - `"id"`: Model identifier string
  - Optional fields: `"name"`, `"compartments"`, `"notes"`, `"annotation"`

- **model_name**: Override the model name
  - Type: String or null
  - Default: Use `"name"` field from JSON, fallback to `"id"` field
  - Purpose: Provide human-readable name if JSON lacks one

### Output Structure

```python
{
    "success": true,
    "model_id": "model_20251027_a3f9b2",      # Generated session model ID
    "name": "E. coli core model",              # Model name
    "source_id": "e_coli_core",                # Original model ID from JSON
    "num_reactions": 95,                       # Number of reactions
    "num_metabolites": 72,                     # Number of metabolites
    "num_genes": 137,                          # Number of genes
    "objective": "BIOMASS_Ecoli_core_w_GAM",   # Objective reaction ID
    "compartments": ["c", "e"],                # Compartment list
    "import_timestamp": "2025-10-27T10:15:30Z" # When imported
}
```

**Field Descriptions**:

- **model_id**: Newly generated model ID for session storage (follows format from 010-model-storage.md)
- **name**: Human-readable model name (from JSON or parameter)
- **source_id**: Original model ID from JSON file (preserved for tracking)
- **num_reactions**: Count of reactions in model
- **num_metabolites**: Count of unique metabolites
- **num_genes**: Count of genes (gene-protein-reaction associations)
- **objective**: Current objective reaction ID
- **compartments**: List of cellular compartments (e.g., cytosol, extracellular)
- **import_timestamp**: ISO 8601 timestamp of import

### Behavior

**Import Process**:

1. **Parse JSON**: Parse `json_string` into Python dictionary
2. **Validate Structure**: Check for required fields (`reactions`, `metabolites`, `id`)
3. **Load into COBRApy**: Use COBRApy's JSON parsing to create `Model` object
4. **Validate Model**: Check model integrity (stoichiometry, bounds, objective)
5. **Generate model_id**: Create unique session ID using format from 010-model-storage.md
6. **Store Model**: Add to MODEL_STORAGE with generated model_id
7. **Return Metadata**: Return model statistics and identifiers

**Model Integration**:
- Imported model stored identically to models created by `build_model`
- Can be used immediately with `gapfill_model`, `run_fba`, and other tools
- Original model ID preserved in metadata for reference
- Model name can be overridden via `model_name` parameter

**Validation Steps**:
- JSON syntax validation (parseable as JSON)
- COBRApy format validation (contains required fields)
- Model integrity checks (no duplicate IDs, valid stoichiometry)
- Objective validation (objective reaction exists in model)

### Error Conditions

#### InvalidJSONError

**Condition**: `json_string` is not valid JSON syntax

**Response**:
```json
{
  "success": false,
  "error_type": "InvalidJSONError",
  "message": "Failed to parse JSON: Expecting ',' delimiter at line 42 column 5",
  "details": {
    "parse_error": "Expecting ',' delimiter",
    "line": 42,
    "column": 5
  },
  "suggestion": "Check JSON syntax. Common issues: missing commas, unquoted keys, trailing commas."
}
```

#### InvalidModelFormatError

**Condition**: JSON is valid but does not conform to COBRApy model format

**Response**:
```json
{
  "success": false,
  "error_type": "InvalidModelFormatError",
  "message": "Missing required field 'reactions' in model JSON",
  "details": {
    "missing_fields": ["reactions"],
    "found_fields": ["metabolites", "genes", "id"]
  },
  "suggestion": "Ensure JSON contains COBRApy model format with 'reactions', 'metabolites', and 'id' fields."
}
```

#### ModelValidationError

**Condition**: Model structure is invalid (duplicate IDs, invalid stoichiometry, missing objective)

**Response**:
```json
{
  "success": false,
  "error_type": "ModelValidationError",
  "message": "Model validation failed: Duplicate reaction ID 'PGI' found",
  "details": {
    "validation_errors": [
      {"type": "duplicate_id", "entity": "reaction", "id": "PGI"},
      {"type": "missing_objective", "message": "No objective reaction set"}
    ]
  },
  "suggestion": "Fix duplicate IDs and ensure an objective is defined."
}
```

#### ModelTooLargeError

**Condition**: Model exceeds reasonable size limits (future)

**Response**:
```json
{
  "success": false,
  "error_type": "ModelTooLargeError",
  "message": "Model size exceeds maximum: 50 MB (limit: 50 MB)",
  "details": {
    "model_size_mb": 50,
    "limit_mb": 50,
    "num_reactions": 15000
  },
  "suggestion": "Model is too large for import. Consider splitting into smaller models or contact support."
}
```

**Note**: MVP has no size limits; this error is reserved for future versions.

### Example Usage

#### Example 1: Import E. coli Core Model

```
User: "Import the E. coli core model from this JSON file"
[User provides JSON content]

AI Assistant calls import_model_json:
{
    "json_string": "{\"id\": \"e_coli_core\", \"reactions\": [...], \"metabolites\": [...]}"
}

Response:
{
    "success": true,
    "model_id": "model_20251027_a3f9b2",
    "name": "E. coli core model",
    "source_id": "e_coli_core",
    "num_reactions": 95,
    "num_metabolites": 72,
    "num_genes": 137,
    "objective": "BIOMASS_Ecoli_core_w_GAM"
}

AI: "I've imported the E. coli core model. It contains 95 reactions and 72 metabolites.
The model is now available as model_20251027_a3f9b2 and ready for analysis."
```

#### Example 2: Import and Rename Model

```
User: "Import this model and call it 'My Strain'"

AI Assistant calls import_model_json:
{
    "json_string": "{...}",
    "model_name": "My Strain"
}

Response:
{
    "success": true,
    "model_id": "model_20251027_b5c3d1",
    "name": "My Strain",
    "source_id": "original_model_id",
    "num_reactions": 842
}

AI: "I've imported your model as 'My Strain' (model_20251027_b5c3d1) with 842 reactions."
```

#### Example 3: Import Invalid JSON

```
User: "Import this model"
[User provides malformed JSON]

AI Assistant calls import_model_json:
{
    "json_string": "{\"reactions\": [...]"  // Missing closing brace
}

Response:
{
    "success": false,
    "error_type": "InvalidJSONError",
    "message": "Failed to parse JSON: Unexpected end of JSON input"
}

AI: "The JSON you provided is malformed (unexpected end of input).
Please check that all braces and brackets are properly closed."
```

---

## Tool 2: export_model_json

### Purpose

Export a metabolic model from the server session to COBRApy JSON format.

### Input Parameters

```python
{
    "model_id": str,                 # Session model ID to export
    "pretty": bool = False,          # Pretty-print JSON (default: compact)
    "include_metadata": bool = True  # Include export timestamp and source info
}
```

**Field Specifications**:

- **model_id**: Session model identifier
  - Type: String
  - Format: Must match model ID format (e.g., `"model_20251027_a3f9b2"`)
  - Must exist in MODEL_STORAGE
  - Can export any model: draft, gapfilled, modified

- **pretty**: Control JSON formatting
  - Type: Boolean
  - Default: `false` (compact output)
  - `true`: Pretty-printed with indentation (larger files, more readable)
  - `false`: Compact single-line format (smaller files, less readable)

- **include_metadata**: Add export information to model notes
  - Type: Boolean
  - Default: `true`
  - `true`: Add export timestamp and source to model `notes` field
  - `false`: Export model as-is without additional metadata

### Output Structure

```python
{
    "success": true,
    "model_id": "model_20251027_a3f9b2",           # Source model ID
    "json_string": "{\"id\": \"...\", ...}",       # Complete model as JSON string
    "size_bytes": 245678,                          # JSON string size in bytes
    "size_kb": 239.9,                              # Size in kilobytes
    "num_reactions": 856,                          # Model statistics
    "num_metabolites": 761,
    "num_genes": 423,
    "export_timestamp": "2025-10-27T11:30:45Z",    # When exported
    "format": "cobrapy_json_v1"                    # Format identifier
}
```

**Field Descriptions**:

- **json_string**: Complete model serialized as JSON string
  - Ready to save to file or transmit
  - Can be imported back with `import_model_json`
  - Compatible with COBRApy `load_json_model()`

- **size_bytes** / **size_kb**: JSON string size
  - Useful for determining if model is too large to display
  - Typical sizes: 100 KB (small) to 10 MB (large)

- **num_reactions** / **num_metabolites** / **num_genes**: Model statistics for verification

- **export_timestamp**: ISO 8601 timestamp of export

- **format**: Format identifier (`"cobrapy_json_v1"`) for future format versioning

### Behavior

**Export Process**:

1. **Retrieve Model**: Load model from MODEL_STORAGE by model_id
2. **Add Metadata** (if `include_metadata=true`):
   - Add export timestamp to model notes
   - Add source information (Gem-Flux server, model_id)
   - Preserve existing notes
3. **Serialize to JSON**: Use COBRApy's `save_json_model()` functionality
4. **Format JSON**: Apply pretty-printing if requested
5. **Calculate Size**: Measure JSON string size in bytes
6. **Return Output**: Return JSON string and metadata

**Metadata Addition** (when `include_metadata=true`):
```python
# Added to model.notes field (conceptual)
{
    "export_info": {
        "source": "Gem-Flux MCP Server",
        "session_model_id": "model_20251027_a3f9b2",
        "export_timestamp": "2025-10-27T11:30:45Z",
        "gem_flux_version": "v0.1.0"
    }
}
```

**Compatibility**:
- Exported JSON is standard COBRApy format
- Can be loaded with: `cobra.io.load_json_model(filename)`
- Can be imported back to Gem-Flux with `import_model_json`
- Compatible with Escher, MATLAB COBRA, and other tools

### Error Conditions

#### ModelNotFoundError

**Condition**: `model_id` does not exist in MODEL_STORAGE

**Response**:
```json
{
  "success": false,
  "error_type": "ModelNotFoundError",
  "message": "Model 'model_20251027_xyz789' not found in current session",
  "details": {
    "requested_id": "model_20251027_xyz789",
    "available_models": [
      "model_20251027_a3f9b2",
      "model_20251027_a3f9b2.gf"
    ],
    "num_available": 2
  },
  "suggestion": "Use one of the available model IDs. Note: Models are lost on server restart."
}
```

#### SerializationError

**Condition**: Model cannot be serialized to JSON (extremely rare)

**Response**:
```json
{
  "success": false,
  "error_type": "SerializationError",
  "message": "Failed to serialize model to JSON: Object of type 'NoneType' is not JSON serializable",
  "details": {
    "model_id": "model_20251027_a3f9b2",
    "error_location": "reactions[42].bounds"
  },
  "suggestion": "Model contains invalid data. This may indicate a bug in model construction."
}
```

### Example Usage

#### Example 1: Export Gapfilled Model

```
User: "Export the gapfilled model so I can use it in Escher"

AI Assistant calls export_model_json:
{
    "model_id": "model_20251027_a3f9b2.gf",
    "pretty": true  // Readable format for manual inspection
}

Response:
{
    "success": true,
    "model_id": "model_20251027_a3f9b2.gf",
    "json_string": "{\n  \"id\": \"model_20251027_a3f9b2.gf\",\n  \"reactions\": [\n    ...\n  ]\n}",
    "size_kb": 428.5,
    "num_reactions": 861
}

AI: "I've exported your gapfilled model (861 reactions, 428.5 KB).
The JSON is formatted for readability and ready to import into Escher."

[AI provides json_string to user for saving]
```

#### Example 2: Export Compact Format for Storage

```
User: "Export the model in compact format for version control"

AI Assistant calls export_model_json:
{
    "model_id": "model_20251027_b5c3d1",
    "pretty": false  // Compact format
}

Response:
{
    "success": true,
    "json_string": "{\"id\":\"model_20251027_b5c3d1\",\"reactions\":[...]}",
    "size_kb": 312.8
}

AI: "I've exported your model in compact format (312.8 KB).
This format is smaller and better for version control."
```

#### Example 3: Export Non-Existent Model

```
User: "Export model_001"

AI Assistant calls export_model_json:
{
    "model_id": "model_001"
}

Response:
{
    "success": false,
    "error_type": "ModelNotFoundError",
    "message": "Model 'model_001' not found in current session",
    "available_models": ["model_20251027_a3f9b2", "model_20251027_a3f9b2.gf"]
}

AI: "Model 'model_001' doesn't exist in the current session.
Available models are:
- model_20251027_a3f9b2 (draft)
- model_20251027_a3f9b2.gf (gapfilled)

Did you mean one of these?"
```

---

## Integration with Model Lifecycle

### Import → Modify → Export Workflow

**Complete Round-Trip Example**:

```
1. Import existing model:
   import_model_json(json_string="{...}")
   → model_id: "model_20251027_a3f9b2"

2. Gapfill the imported model:
   gapfill_model(model_id="model_20251027_a3f9b2", media_id="media_001")
   → model_id: "model_20251027_a3f9b2.gf"

3. Run FBA on gapfilled model:
   run_fba(model_id="model_20251027_a3f9b2.gf", media_id="media_001")
   → Growth rate: 0.874 hr⁻¹

4. Export gapfilled model:
   export_model_json(model_id="model_20251027_a3f9b2.gf")
   → json_string: "{...}"

5. Save to file (outside MCP server):
   User saves json_string to "my_gapfilled_model.json"
```

### Session Persistence via Export

**Problem**: Models lost on server restart (010-model-storage.md)

**Solution**: Export models before shutdown

```
User: "Save my work before shutting down the server"

AI Assistant:
1. Lists all models in session
2. Exports each model to JSON
3. Provides JSON strings to user
4. User saves to files

User can later:
- Import models back after server restart
- Share models with collaborators
- Use models in other tools (Escher, MATLAB)
```

### Import Sources

**Common Sources for Import**:

1. **COBRApy Built-in Models**:
   - E. coli core model
   - Salmonella model
   - Textbook examples

2. **BiGG Models Database**:
   - Genome-scale models for many organisms
   - http://bigg.ucsd.edu/

3. **ModelSEED Models**:
   - Models from KBase
   - Community-contributed models

4. **User-Generated Models**:
   - Previously exported Gem-Flux models
   - Models from other metabolic modeling tools
   - Hand-crafted models for educational purposes

5. **Escher-Compatible Models**:
   - Models designed for visualization
   - Often include layout information

---

## Data Format Details

### COBRApy JSON Structure (Reference)

**Top-Level Fields**:
```json
{
  "id": "model_id",                    // Model identifier
  "name": "Human-readable name",       // Model name (optional)
  "compartments": {"c": "cytosol"},    // Compartment definitions
  "reactions": [...],                  // Reaction array
  "metabolites": [...],                // Metabolite array
  "genes": [...],                      // Gene array
  "notes": {...},                      // Metadata and annotations
  "annotation": {...}                  // External database links
}
```

**Reaction Object**:
```json
{
  "id": "PGI",
  "name": "Phosphoglucose isomerase",
  "metabolites": {
    "g6p_c": -1.0,
    "f6p_c": 1.0
  },
  "lower_bound": -1000.0,
  "upper_bound": 1000.0,
  "gene_reaction_rule": "b4025",
  "subsystem": "Glycolysis"
}
```

**Metabolite Object**:
```json
{
  "id": "g6p_c",
  "name": "D-Glucose 6-phosphate",
  "compartment": "c",
  "formula": "C6H11O9P",
  "charge": -2
}
```

**Gene Object**:
```json
{
  "id": "b4025",
  "name": "pgi"
}
```

### Size Considerations

**Typical Model Sizes**:
```
Small (core models):      100-500 KB
Medium (genome-scale):    500 KB - 2 MB
Large (community models): 2 MB - 50 MB
```

**Pretty vs Compact**:
```
Compact: 1 MB
Pretty (indented): 1.5 MB (50% larger)
```

**Recommendation**:
- Use **pretty=true** for human inspection and debugging
- Use **pretty=false** for version control and automated processing

---

## Validation Details

### Import Validation Checklist

**Level 1: JSON Syntax**
- [ ] Valid JSON (parseable)
- [ ] No syntax errors

**Level 2: Format Validation**
- [ ] Contains `"id"` field
- [ ] Contains `"reactions"` array
- [ ] Contains `"metabolites"` array
- [ ] Contains `"genes"` array (can be empty)

**Level 3: Structure Validation**
- [ ] Reactions have valid structure (id, metabolites, bounds)
- [ ] Metabolites have valid structure (id, compartment)
- [ ] No duplicate reaction IDs
- [ ] No duplicate metabolite IDs

**Level 4: Integrity Validation**
- [ ] Objective reaction exists in model
- [ ] Reaction stoichiometry references existing metabolites
- [ ] Bounds are valid numbers (lower ≤ upper)
- [ ] Gene-protein-reaction rules parse correctly

**Level 5: Biological Plausibility** (warnings only)
- ⚠️ Objective has reasonable bounds
- ⚠️ Model is not empty (>0 reactions)
- ⚠️ Biomass reaction exists

### Export Validation

**Pre-Export Checks**:
- Model exists in storage
- Model is a valid COBRApy Model object
- Model has at least one reaction

**Post-Export Checks**:
- JSON serialization succeeded
- JSON string is non-empty
- Size is within reasonable limits (< 100 MB)

---

## Performance Characteristics

### Import Performance

**Small Model** (100 reactions):
- Parse JSON: 5-10 ms
- Validate: 10-20 ms
- Store: < 1 ms
- **Total: ~20-30 ms**

**Large Model** (5000 reactions):
- Parse JSON: 50-100 ms
- Validate: 100-200 ms
- Store: < 1 ms
- **Total: ~150-300 ms**

### Export Performance

**Small Model**:
- Retrieve: < 1 ms
- Serialize: 10-20 ms
- Format (compact): 5 ms
- **Total: ~15-25 ms**

**Large Model**:
- Retrieve: < 1 ms
- Serialize: 100-200 ms
- Format (compact): 20 ms
- **Total: ~120-220 ms**

**Pretty Printing**: Adds 50-100% overhead

### Memory Usage

**Import**:
- JSON string: 1x model size
- Parsed object: 2x model size
- COBRApy model: 10-20x model size
- **Peak: ~25x JSON file size**

**Export**:
- COBRApy model: 10-20x final JSON size
- Serialized JSON: 1x final size
- **Peak: ~20x final JSON size**

**Example**: 1 MB JSON file requires ~25 MB RAM during import/export

---

## Future Enhancements (Post-MVP)

### Additional Import Sources (v0.2.0)

**SBML Import**:
```python
@mcp.tool()
def import_model_sbml(sbml_string: str) -> dict:
    """Import model from SBML format."""
```

**MATLAB Import**:
```python
@mcp.tool()
def import_model_matlab(mat_file_base64: str) -> dict:
    """Import model from MATLAB .mat format."""
```

### Batch Import/Export (v0.2.0)

```python
@mcp.tool()
def batch_import_models(json_strings: list[str]) -> list[dict]:
    """Import multiple models in parallel."""

@mcp.tool()
def batch_export_models(model_ids: list[str]) -> list[dict]:
    """Export multiple models in parallel."""
```

### Model Compression (v0.3.0)

**For Large Models**:
- Option to gzip JSON for reduced size
- Base64 encoding for binary transmission
- Chunked transfer for very large models

### Validation Options (v0.3.0)

**Configurable Validation Levels**:
```python
{
    "validation_level": "strict" | "standard" | "lenient",
    "skip_checks": ["biological_plausibility"]
}
```

---

## Error Handling Summary

| Error Type | Cause | Recovery |
|------------|-------|----------|
| `InvalidJSONError` | Malformed JSON syntax | Fix JSON syntax, validate with JSON linter |
| `InvalidModelFormatError` | Missing required fields | Ensure JSON has `reactions`, `metabolites`, `id` |
| `ModelValidationError` | Invalid model structure | Fix duplicate IDs, invalid stoichiometry |
| `ModelNotFoundError` | model_id doesn't exist | Use correct model_id, check session storage |
| `SerializationError` | Can't convert to JSON | Report bug (extremely rare) |
| `ModelTooLargeError` | Model exceeds limits | Split model or contact support (future) |

---

## Related Specifications

- **010-model-storage.md**: Session-based storage architecture, model IDs, lifecycle
- **002-data-formats.md**: Model data format details
- **004-build-model-tool.md**: Alternative model creation method (from protein sequences)
- **006-run-fba-tool.md**: Using imported models for FBA analysis
- **012-complete-workflow.md**: End-to-end workflows including import/export (future)

---

## Behavioral Contracts

### Import Guarantees

1. **Idempotency**: Importing the same JSON multiple times creates independent models with different model_ids
2. **Preservation**: All model data from JSON is preserved (reactions, metabolites, genes, notes, annotations)
3. **Validation**: Invalid models are rejected with clear error messages
4. **Compatibility**: Any valid COBRApy JSON can be imported

### Export Guarantees

1. **Completeness**: Exported JSON contains all model information
2. **Compatibility**: Exported JSON can be loaded with COBRApy's `load_json_model()`
3. **Round-Trip**: Exported model can be imported back without data loss
4. **Format**: Exported JSON conforms to COBRApy JSON format specification

### Integration Guarantee

**Imported models are functionally identical to built models**:
- Can be gapfilled with `gapfill_model`
- Can be analyzed with `run_fba`
- Can be modified with future tools
- Follow same storage lifecycle rules

---

## Example: Complete Import-Modify-Export Session

```
Session Start
─────────────

User: "Import the E. coli core model from BiGG"

AI → import_model_json:
{
    "json_string": "{\"id\": \"e_coli_core\", ...}",
    "model_name": "E. coli core"
}

Result: model_20251027_a3f9b2 created (95 reactions, 72 metabolites)

─────────────

User: "Create minimal glucose media"

AI → build_media:
{
    "compounds": ["cpd00027", "cpd00007", "cpd00001", ...],
    "custom_bounds": {"cpd00027": (-10, 100)}
}

Result: media_20251027_x1y2z3 created (15 compounds)

─────────────

User: "Gapfill the model for this media"

AI → gapfill_model:
{
    "model_id": "model_20251027_a3f9b2",
    "media_id": "media_20251027_x1y2z3"
}

Result: model_20251027_a3f9b2.gf created (98 reactions, 3 added)

─────────────

User: "Run FBA"

AI → run_fba:
{
    "model_id": "model_20251027_a3f9b2.gf",
    "media_id": "media_20251027_x1y2z3"
}

Result: Growth rate 0.874 hr⁻¹, 48 active reactions

─────────────

User: "Export the gapfilled model so I can visualize it in Escher"

AI → export_model_json:
{
    "model_id": "model_20251027_a3f9b2.gf",
    "pretty": true
}

Result: JSON string (320 KB) ready for Escher

─────────────

AI: "Here's your gapfilled E. coli core model in JSON format.
You can now import this into Escher to visualize the active pathways."

Session Complete
```

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 012-complete-workflow.md
