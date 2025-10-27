# Session Management Tools - Gem-Flux MCP Server

**Type**: Tool Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding session management)
- Read: 010-model-storage.md (for model storage architecture and IDs)
- Read: 002-data-formats.md (for model and media formats)

## Purpose

This specification defines three MCP tools for managing models and media within a server session: `list_models`, `delete_model`, and `list_media`. These tools enable users to discover what models and media exist in the current session, inspect their properties, and remove items they no longer need.

## Core Design Principles

**Session Visibility**:
- Users can see all models and media created in current session
- Clear metadata helps identify and manage resources
- State suffixes make model lineage visible

**Explicit Deletion**:
- Users must explicitly delete models/media
- No automatic cleanup (MVP)
- Deletion cannot be undone (session-scoped)

**Helpful Metadata**:
- List tools provide enough context for decision-making
- Timestamps show creation order
- State suffixes show processing history

---

## list_models Tool

### Purpose

List all metabolic models currently stored in the server session with their metadata.

### Input Specification

```json
{
  "filter_state": "all"  // Optional: "all", "draft", "gapfilled"
}
```

**Parameter Descriptions**:

**filter_state** (optional)
- Type: String
- Default: `"all"`
- Valid values:
  - `"all"` - Return all models regardless of state
  - `"draft"` - Return only models with `.draft` suffix (not gapfilled)
  - `"gapfilled"` - Return only models with `.gf` or `.draft.gf` suffixes
- Purpose: Filter models by processing state
- Case-insensitive

### Output Specification

**Successful Response**:

```json
{
  "success": true,
  "models": [
    {
      "model_id": "model_20251027_143052_abc123.draft",
      "model_name": null,
      "state": "draft",
      "num_reactions": 856,
      "num_metabolites": 742,
      "num_genes": 150,
      "template_used": "GramNegative",
      "created_at": "2025-10-27T14:30:52Z",
      "derived_from": null
    },
    {
      "model_id": "model_20251027_143052_abc123.draft.gf",
      "model_name": null,
      "state": "gapfilled",
      "num_reactions": 892,
      "num_metabolites": 768,
      "num_genes": 150,
      "template_used": "GramNegative",
      "created_at": "2025-10-27T14:35:18Z",
      "derived_from": "model_20251027_143052_abc123.draft"
    },
    {
      "model_id": "E_coli_K12.draft.gf",
      "model_name": "E_coli_K12",
      "state": "gapfilled",
      "num_reactions": 901,
      "num_metabolites": 775,
      "num_genes": 200,
      "template_used": "GramNegative",
      "created_at": "2025-10-27T15:12:45Z",
      "derived_from": "E_coli_K12.draft"
    }
  ],
  "total_models": 3,
  "models_by_state": {
    "draft": 0,
    "gapfilled": 3
  }
}
```

**Field Descriptions**:

**success**
- Type: Boolean
- Value: `true` for successful listing

**models**
- Type: Array of objects
- Sorted by: `created_at` (chronological order, oldest first)
- Each object contains:
  - **model_id**: Unique model identifier with state suffix
  - **model_name**: User-provided name or `null` if auto-generated
  - **state**: Processing state ("draft", "gapfilled")
  - **num_reactions**: Reaction count
  - **num_metabolites**: Metabolite count
  - **num_genes**: Gene count
  - **template_used**: Template name used for model building
  - **created_at**: ISO 8601 timestamp of model creation
  - **derived_from**: Model ID this was derived from, or `null` if original

**total_models**
- Type: Integer
- Value: Total number of models returned (after filtering)

**models_by_state**
- Type: Object
- Value: Breakdown of models by state
- Keys: "draft", "gapfilled"
- Values: Count of models in each state

### State Classification

**State determination from model_id**:
- `.draft` suffix → state: "draft"
- `.gf` suffix → state: "gapfilled"
- `.draft.gf` suffix → state: "gapfilled"
- `.draft.gf.gf` suffix → state: "gapfilled"
- Any suffix containing `.gf` → state: "gapfilled"

### Behavioral Specification

**Step 1: Parse Input**
1. Get `filter_state` parameter (default to "all")
2. Validate filter_state is one of: "all", "draft", "gapfilled"
3. Normalize to lowercase

**Step 2: Query Model Storage**
1. Retrieve all models from MODEL_STORAGE dictionary
2. For each model:
   - Extract metadata from COBRApy Model object
   - Determine state from model_id suffix
   - Apply filter if specified
   - Collect model information

**Step 3: Apply Filtering**
1. If `filter_state == "all"`: Include all models
2. If `filter_state == "draft"`: Include only models where state == "draft"
3. If `filter_state == "gapfilled"`: Include only models where state == "gapfilled"

**Step 4: Sort and Count**
1. Sort models by `created_at` timestamp (oldest first)
2. Count total models after filtering
3. Count models by state (draft vs gapfilled)

**Step 5: Return Response**
1. Return sorted list with metadata
2. Include summary statistics

### Error Responses

**Invalid Filter State**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid filter_state parameter",
  "details": {
    "provided": "gapfill",
    "valid_values": ["all", "draft", "gapfilled"]
  },
  "suggestion": "Use 'all', 'draft', or 'gapfilled' for filter_state parameter."
}
```

**Empty Model Storage**:
```json
{
  "success": true,
  "models": [],
  "total_models": 0,
  "models_by_state": {
    "draft": 0,
    "gapfilled": 0
  }
}
```

### Example Usage Scenarios

**Example 1: List All Models**

```
User: "Show me all my models"

AI Assistant calls list_models:
{"filter_state": "all"}

Response: { "models": [...], "total_models": 5 }

AI: "You have 5 models in your session:
- model_20251027_143052_abc123.draft (draft, 856 reactions)
- model_20251027_143052_abc123.draft.gf (gapfilled, 892 reactions)
- E_coli_K12.draft.gf (gapfilled, 901 reactions)
- ..."
```

**Example 2: List Only Draft Models**

```
User: "Which models haven't been gapfilled yet?"

AI Assistant calls list_models:
{"filter_state": "draft"}

Response: {
  "models": [{"model_id": "model_xyz.draft", ...}],
  "total_models": 1
}

AI: "You have 1 draft model that hasn't been gapfilled:
- model_xyz.draft (856 reactions, GramNegative template)"
```

---

## delete_model Tool

### Purpose

Delete a metabolic model from the current session storage.

### Input Specification

```json
{
  "model_id": "model_20251027_143052_abc123.draft"
}
```

**Parameter Descriptions**:

**model_id** (required)
- Type: String
- Format: Must match exact model_id including state suffix
- Case-sensitive
- Must exist in current session storage
- Examples:
  - `"model_20251027_143052_abc123.draft"`
  - `"E_coli_K12.draft.gf"`

### Output Specification

**Successful Response**:

```json
{
  "success": true,
  "deleted_model_id": "model_20251027_143052_abc123.draft",
  "message": "Model deleted successfully"
}
```

**Field Descriptions**:

**success**
- Type: Boolean
- Value: `true` for successful deletion

**deleted_model_id**
- Type: String
- Value: The model_id that was deleted (confirmation)

**message**
- Type: String
- Value: Human-readable confirmation message

### Behavioral Specification

**Step 1: Validate Input**
1. Verify `model_id` parameter provided
2. Verify `model_id` is non-empty string

**Step 2: Check Existence**
1. Query MODEL_STORAGE for `model_id`
2. If not found, return error (model doesn't exist)

**Step 3: Delete Model**
1. Remove model from MODEL_STORAGE dictionary
2. Memory freed automatically (Python garbage collection)

**Step 4: Return Confirmation**
1. Return success response with deleted model_id

### Error Responses

**Model Not Found**:
```json
{
  "success": false,
  "error_type": "ModelNotFoundError",
  "message": "Model not found in session",
  "details": {
    "model_id": "model_nonexistent.draft",
    "available_models": ["model_abc.draft", "model_xyz.draft.gf"]
  },
  "suggestion": "Use list_models tool to see available models."
}
```

**Missing model_id Parameter**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Missing required parameter 'model_id'",
  "suggestion": "Provide model_id to delete."
}
```

### Example Usage Scenarios

**Example 1: Delete Draft Model**

```
User: "Delete the draft model, I only need the gapfilled version"

AI Assistant calls list_models to find draft:
{"filter_state": "draft"}

Response: {"models": [{"model_id": "model_abc.draft", ...}]}

AI Assistant calls delete_model:
{"model_id": "model_abc.draft"}

Response: {"success": true, "deleted_model_id": "model_abc.draft"}

AI: "I've deleted the draft model (model_abc.draft).
You still have the gapfilled version (model_abc.draft.gf)."
```

**Example 2: Delete Specific Model by Name**

```
User: "Delete E_coli_K12 draft model"

AI Assistant calls delete_model:
{"model_id": "E_coli_K12.draft"}

Response: {"success": true}

AI: "Deleted model E_coli_K12.draft successfully."
```

---

## list_media Tool

### Purpose

List all growth media compositions currently stored in the server session with their metadata.

### Input Specification

```json
{}
```

No input parameters required.

### Output Specification

**Successful Response**:

```json
{
  "success": true,
  "media": [
    {
      "media_id": "media_20251027_143052_x1y2z3",
      "media_name": null,
      "num_compounds": 18,
      "media_type": "minimal",
      "compounds_preview": [
        {"id": "cpd00027", "name": "D-Glucose"},
        {"id": "cpd00007", "name": "O2"},
        {"id": "cpd00001", "name": "H2O"}
      ],
      "created_at": "2025-10-27T14:30:45Z"
    },
    {
      "media_id": "glucose_minimal_aerobic",
      "media_name": "glucose_minimal_aerobic",
      "num_compounds": 18,
      "media_type": "minimal",
      "compounds_preview": [
        {"id": "cpd00027", "name": "D-Glucose"},
        {"id": "cpd00007", "name": "O2"},
        {"id": "cpd00001", "name": "H2O"}
      ],
      "created_at": "2025-10-27T00:00:00Z"
    }
  ],
  "total_media": 2,
  "predefined_media": 4,
  "user_created_media": 1
}
```

**Field Descriptions**:

**success**
- Type: Boolean
- Value: `true` for successful listing

**media**
- Type: Array of objects
- Sorted by: `created_at` (chronological order)
- Each object contains:
  - **media_id**: Unique media identifier
  - **media_name**: User-provided name or predefined name, or `null`
  - **num_compounds**: Number of compounds in media
  - **media_type**: Classification ("minimal" or "rich")
  - **compounds_preview**: First 3 compounds (ID and name)
  - **created_at**: ISO 8601 timestamp of media creation

**total_media**
- Type: Integer
- Value: Total number of media (predefined + user-created)

**predefined_media**
- Type: Integer
- Value: Count of predefined media from library

**user_created_media**
- Type: Integer
- Value: Count of media created by user via build_media

### Behavioral Specification

**Step 1: Query Media Storage**
1. Retrieve all media from MEDIA_STORAGE dictionary
2. Include predefined media from library
3. For each media:
   - Extract metadata from MSMedia object
   - Classify as minimal vs rich (< 50 compounds = minimal)
   - Get first 3 compounds for preview

**Step 2: Sort and Count**
1. Sort media by `created_at` timestamp
2. Count total media
3. Count predefined vs user-created

**Step 3: Return Response**
1. Return sorted list with metadata
2. Include summary statistics

### Error Responses

**Empty Media Storage**:
```json
{
  "success": true,
  "media": [],
  "total_media": 0,
  "predefined_media": 0,
  "user_created_media": 0
}
```

### Example Usage Scenarios

**Example 1: List All Media**

```
User: "What media do I have available?"

AI Assistant calls list_media:
{}

Response: {
  "media": [
    {"media_id": "glucose_minimal_aerobic", "num_compounds": 18},
    {"media_id": "media_xyz", "num_compounds": 20}
  ],
  "total_media": 2
}

AI: "You have 2 media available:
- glucose_minimal_aerobic: 18 compounds (minimal, predefined)
- media_xyz: 20 compounds (minimal, user-created)"
```

---

## Integration with Existing Tools

### Workflow Integration

**Typical Session Workflow**:

1. **Build models**:
   ```
   build_model → model_abc.draft
   ```

2. **List models** (check what exists):
   ```
   list_models → ["model_abc.draft"]
   ```

3. **Gapfill**:
   ```
   gapfill_model(model_abc.draft) → model_abc.draft.gf
   ```

4. **List again** (see both versions):
   ```
   list_models → ["model_abc.draft", "model_abc.draft.gf"]
   ```

5. **Delete draft** (only need gapfilled):
   ```
   delete_model(model_abc.draft)
   ```

6. **Final check**:
   ```
   list_models → ["model_abc.draft.gf"]
   ```

### Used By Other Tools

**gapfill_model**:
- Can use `list_models` to find draft models needing gapfilling
- AI can suggest "You have 3 draft models, would you like me to gapfill them?"

**run_fba**:
- Can use `list_models` to find available models for FBA
- Can use `list_media` to find available media

### Memory Management

**When to use delete_model**:
- Intermediate draft models no longer needed
- Failed/abandoned model building attempts
- Session cleanup before shutdown

**Benefits**:
- Reduce memory usage in long sessions
- Keep storage organized
- Avoid confusion with many similar models

## Performance Considerations

### list_models Performance

**Expected Performance**:
- Storage size: 1-100 models typical
- Listing time: < 10 ms for 100 models
- Metadata extraction: O(n) where n = number of models
- Sorting: O(n log n) but n is small

**Performance is Acceptable**: Listing is fast even with many models

### delete_model Performance

**Expected Performance**:
- Deletion time: O(1) dictionary deletion
- Memory freed: Depends on model size (1-5 MB typical)
- Total time: < 1 ms

**Performance is Acceptable**: Instant deletion

### list_media Performance

**Expected Performance**:
- Similar to list_models
- Typically fewer media than models (5-20 media vs 10-100 models)
- Performance: < 10 ms

## Future Enhancements

### Post-MVP Features (Not in Specification)

**v0.2.0 - Advanced Filtering**:
- Filter by template, reaction count, creation date
- Search models by name pattern
- Tag-based organization

**v0.3.0 - Batch Operations**:
- `delete_all_drafts()` - Delete all draft models at once
- `delete_models(model_ids: list)` - Delete multiple models
- Bulk operations for cleanup

**v0.4.0 - Model Metadata**:
- User-provided descriptions
- Model tags/categories
- Model provenance tracking

**v0.5.0 - Export/Import**:
- Export model list to JSON
- Import previously exported models
- Session state persistence

## Related Specifications

- **010-model-storage.md**: Model storage architecture and IDs
- **002-data-formats.md**: Model and media data formats
- **004-build-model-tool.md**: Model creation
- **005-gapfill-model-tool.md**: Model gapfilling

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 019-predefined-media-library.md
