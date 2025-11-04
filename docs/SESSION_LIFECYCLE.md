# Session Lifecycle Documentation

**Gem-Flux MCP Server - Session Management**
**Version**: MVP v0.1.0
**Status**: Implementation Documentation

---

## Overview

The Gem-Flux MCP Server uses **session-based storage** for metabolic models and media compositions. All data is stored in-memory and cleared when the server restarts. This document describes the complete lifecycle of models and media from creation to deletion.

---

## Model Lifecycle

### Model States

Models progress through distinct states during their lifecycle:

```
Creation (draft) → Modification (gapfilling) → Analysis (FBA) → Deletion
```

Each state is represented by a **state suffix** in the model ID:
- `.draft` - Newly built model, not gapfilled
- `.draft.gf` - Draft model after first gapfilling
- `.gf` - Gapfilled model (source was already gapfilled)
- `.draft.gf.gf` - Draft model gapfilled twice
- Additional `.gf` appended for each gapfilling iteration

### 1. Creation Phase

**Tool**: `build_model`

**Input**:
- Protein sequences (dict or FASTA file)
- Template name (e.g., "GramNegative")
- Optional: User-provided model name

**Process**:
1. Validate protein sequences (amino acid alphabet)
2. Load ModelSEED template from template cache
3. Create MSGenome from protein sequences
4. Create MSBuilder with genome and template
5. Build base model (template matching)
6. Add ATPM (ATP maintenance) reaction
7. Generate model ID with `.draft` suffix
8. Store model in `MODEL_STORAGE` dictionary
9. Collect statistics (reactions, metabolites, genes)

**Output**:
```json
{
  "success": true,
  "model_id": "model_20251027_143052_abc123.draft",
  "num_reactions": 856,
  "num_metabolites": 742,
  "num_genes": 150,
  "template_used": "GramNegative",
  "compartments": ["c0", "e0", "p0"]
}
```

**Storage State**:
```python
MODEL_STORAGE = {
  "model_20251027_143052_abc123.draft": <COBRApy Model object>
}
```

### 2. Modification Phase (Gapfilling)

**Tool**: `gapfill_model`

**Input**:
- `model_id`: ID of draft model to gapfill
- `media_id`: Target media for growth
- `target_growth_rate`: Minimum growth rate (default: 0.01)

**Process**:
1. Retrieve draft model from `MODEL_STORAGE`
2. Create deep copy (preserve original)
3. Load target media from `MEDIA_STORAGE`
4. Run ATP correction stage (MSATPCorrection)
5. Run genome-scale gapfilling (MSGapfill)
6. Integrate gapfilling solutions into model
7. Transform model ID state suffix: `.draft` → `.draft.gf`
8. Store gapfilled model with new ID
9. Original draft model remains unchanged

**Output**:
```json
{
  "success": true,
  "model_id": "model_20251027_143052_abc123.draft.gf",
  "original_model_id": "model_20251027_143052_abc123.draft",
  "reactions_added": [
    {
      "id": "rxn05459_c0",
      "name": "fumarate reductase",
      "direction": "forward"
    }
  ],
  "num_reactions_added": 5,
  "growth_rate_before": 0.0,
  "growth_rate_after": 0.874
}
```

**Storage State**:
```python
MODEL_STORAGE = {
  "model_20251027_143052_abc123.draft": <Original draft model>,
  "model_20251027_143052_abc123.draft.gf": <Gapfilled model>
}
```

**Key Behavior**: Original model is **preserved**. Gapfilling creates a **new model** with transformed state suffix.

### 3. Analysis Phase (FBA)

**Tool**: `run_fba`

**Input**:
- `model_id`: Model to analyze (typically `.draft.gf` model)
- `media_id`: Media for FBA
- `objective`: Objective function (default: "bio1")

**Process**:
1. Retrieve model from `MODEL_STORAGE` (read-only)
2. Create temporary copy for FBA
3. Load media from `MEDIA_STORAGE`
4. Apply media constraints to exchange reactions
5. Set objective function
6. Run FBA: `solution = model.optimize()`
7. Extract fluxes, filter by threshold
8. Separate uptake/secretion fluxes
9. Enrich with compound/reaction names from database
10. Original model in storage **unchanged**

**Output**:
```json
{
  "success": true,
  "objective_value": 0.874,
  "status": "optimal",
  "fluxes": {
    "bio1": 0.874,
    "EX_cpd00027_e0": -5.0,
    "rxn00148_c0": 5.0
  },
  "uptake_fluxes": {
    "cpd00027": {
      "name": "D-Glucose",
      "flux": -5.0
    }
  }
}
```

**Storage State**: Unchanged (FBA is read-only operation)

### 4. Query Phase (Session Management)

**Tools**: `list_models`, `delete_model`

**list_models**:
- Query all models in `MODEL_STORAGE`
- Extract metadata (state, reaction count, created timestamp)
- Filter by state if requested ("draft", "gapfilled", "all")
- Sort chronologically (oldest first)
- Return model list with statistics

**delete_model**:
- Validate model ID exists in storage
- Remove from `MODEL_STORAGE` dictionary
- Memory freed automatically (Python garbage collection)
- Cannot be undone (session-scoped)

### 5. Session End Phase

**Event**: Server shutdown or restart

**Process**:
1. Stop accepting new requests
2. Wait for active requests to complete (timeout: 30s)
3. Log session statistics:
   - Total models created
   - Total storage used
4. Clear `MODEL_STORAGE` dictionary
5. Python garbage collection frees memory
6. Exit server

**Result**: **All models are lost**. No persistence across server restarts in MVP.

---

## Media Lifecycle

### Media States

Media compositions are **immutable** after creation. No modification operations exist.

```
Creation → Usage → Session End
```

Media IDs have **no state suffixes** (unlike models).

### 1. Creation Phase

**Tool**: `build_media`

**Input**:
- `compounds`: List of ModelSEED compound IDs
- `default_uptake`: Default uptake bound (default: 100.0 mmol/gDW/h)
- `custom_bounds`: Optional custom bounds for specific compounds

**Process**:
1. Validate all compound IDs exist in database
2. Apply default bounds: `(-default_uptake, 100.0)`
3. Override with custom bounds for specific compounds
4. Create MSMedia object (ModelSEEDpy)
5. Generate media ID: `media_<timestamp>_<random>`
6. Store in `MEDIA_STORAGE` dictionary
7. Enrich response with compound names from database
8. Classify as "minimal" (<50 compounds) or "rich" (≥50 compounds)

**Output**:
```json
{
  "success": true,
  "media_id": "media_20251027_143052_x1y2z3",
  "compounds": [
    {
      "id": "cpd00027",
      "name": "D-Glucose",
      "bounds": [-5, 100]
    }
  ],
  "num_compounds": 18,
  "media_type": "minimal"
}
```

**Storage State**:
```python
MEDIA_STORAGE = {
  "media_20251027_143052_x1y2z3": <MSMedia object>
}
```

### 2. Usage Phase

**Tools**: `gapfill_model`, `run_fba`

**Behavior**:
- Media retrieved from storage (read-only)
- Applied as constraints to model exchange reactions
- Media object in storage **unchanged**
- Multiple models can use same media
- Media cannot be modified after creation

**If Modifications Needed**:
- Create **new media** with `build_media`
- Original media remains in storage
- Use new media ID for subsequent operations

### 3. Predefined Media

**Source**: `data/media/*.json` files loaded at startup

**Available Predefined Media**:
1. `glucose_minimal_aerobic` - 18 compounds (glucose + O2)
2. `glucose_minimal_anaerobic` - 17 compounds (glucose, no O2)
3. `pyruvate_minimal_aerobic` - 18 compounds (pyruvate + O2)
4. `pyruvate_minimal_anaerobic` - 17 compounds (pyruvate, no O2)

**Storage**:
- Loaded at server startup
- Stored with fixed media IDs (names above)
- Flagged as `is_predefined: true` in `list_media`
- Cannot be deleted
- Available across entire server session

### 4. Query Phase

**Tool**: `list_media`

**Process**:
- Query all media in `MEDIA_STORAGE`
- Extract metadata (compound count, media type)
- Get first 3 compounds for preview
- Count predefined vs user-created media
- Sort chronologically
- Return media list with statistics

**Output**:
```json
{
  "success": true,
  "media": [
    {
      "media_id": "glucose_minimal_aerobic",
      "is_predefined": true,
      "num_compounds": 18,
      "media_type": "minimal"
    },
    {
      "media_id": "media_20251027_x1y2z3",
      "is_predefined": false,
      "num_compounds": 20,
      "media_type": "minimal"
    }
  ],
  "total_media": 2,
  "predefined_media": 1,
  "user_created_media": 1
}
```

### 5. Session End Phase

**Event**: Server shutdown or restart

**Process**:
1. Log media statistics
2. Clear `MEDIA_STORAGE` dictionary
3. Memory freed automatically

**Result**: All user-created media lost. Predefined media reloaded on next startup.

---

## Model ID Format and Generation

### Auto-Generated Model IDs

**Format**: `model_<timestamp>_<random>.<state>`

**Components**:
- Prefix: `"model_"`
- Timestamp: `YYYYMMDD_HHMMSS` (local server time)
- Random suffix: 6 alphanumeric characters (lowercase letters + digits)
- State suffix: `.draft`, `.gf`, `.draft.gf`, etc.

**Examples**:
```
model_20251027_143052_abc123.draft
model_20251027_150312_x7z9p2.draft.gf
model_20251028_091530_m4n8k1.gf
```

**Generation Algorithm**:
```python
import time
import random
import string

def generate_model_id(state: str = "draft") -> str:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_suffix = ''.join(
        random.choices(string.ascii_lowercase + string.digits, k=6)
    )
    return f"model_{timestamp}_{random_suffix}.{state}"
```

### User-Provided Model Names

**Format**: `<user_name>.<state>`

**Examples**:
```
E_coli_K12.draft
B_subtilis_168.draft.gf
my_organism.gf
```

**Collision Handling**:
- If name already exists in storage, append timestamp + microseconds
- Example: `E_coli_K12_20251027_143052_123456.draft`
- Preserves user's custom name when possible

### State Suffix Transformations

**Gapfilling Transformations**:

| Input State | Operation | Output State |
|-------------|-----------|--------------|
| `.draft` | First gapfill | `.draft.gf` |
| `.gf` | Re-gapfill | `.gf.gf` |
| `.draft.gf` | Re-gapfill | `.draft.gf.gf` |
| `.draft.gf.gf` | Re-gapfill | `.draft.gf.gf.gf` |

**Transformation Logic**:
```python
def transform_state_suffix(model_id: str) -> str:
    if model_id.endswith(".draft"):
        # First gapfilling of draft model
        return model_id.replace(".draft", ".draft.gf")
    else:
        # Append .gf for any other state
        return f"{model_id}.gf"
```

**Examples**:
```python
transform_state_suffix("model_abc.draft")        # → "model_abc.draft.gf"
transform_state_suffix("model_abc.gf")           # → "model_abc.gf.gf"
transform_state_suffix("model_abc.draft.gf")     # → "model_abc.draft.gf.gf"
transform_state_suffix("E_coli_K12.draft")       # → "E_coli_K12.draft.gf"
```

---

## Media ID Format and Generation

### Auto-Generated Media IDs

**Format**: `media_<timestamp>_<random>`

**Components**:
- Prefix: `"media_"`
- Timestamp: `YYYYMMDD_HHMMSS` (local server time)
- Random suffix: 6 alphanumeric characters

**Examples**:
```
media_20251027_143052_x1y2z3
media_20251027_150312_p9q8r7
media_20251028_091530_a4b8c2
```

**Generation Algorithm**:
```python
def generate_media_id() -> str:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_suffix = ''.join(
        random.choices(string.ascii_lowercase + string.digits, k=6)
    )
    return f"media_{timestamp}_{random_suffix}"
```

### Predefined Media IDs

**Format**: Human-readable names (no timestamp)

**Examples**:
```
glucose_minimal_aerobic
glucose_minimal_anaerobic
pyruvate_minimal_aerobic
pyruvate_minimal_anaerobic
```

**Characteristics**:
- Fixed names (defined in `data/media/*.json`)
- Loaded at server startup
- No random suffix or timestamp
- Flagged as `is_predefined: true` in `list_media`

---

## Session Storage Architecture

### Storage Structure

**In-Memory Dictionaries**:
```python
# Model storage (key: model_id, value: COBRApy Model object)
MODEL_STORAGE: dict[str, Any] = {}

# Media storage (key: media_id, value: MSMedia object)
MEDIA_STORAGE: dict[str, Any] = {}
```

### Storage Operations

#### Store Model
```python
def store_model(model_id: str, model: Any) -> None:
    """Store model in session storage.

    Raises:
        StorageCollisionError: If model_id already exists
    """
    if model_id in MODEL_STORAGE:
        raise StorageCollisionError(...)
    MODEL_STORAGE[model_id] = model
```

#### Retrieve Model
```python
def retrieve_model(model_id: str) -> Any:
    """Retrieve model from session storage.

    Raises:
        ModelNotFoundError: If model_id not found
    """
    if model_id not in MODEL_STORAGE:
        raise ModelNotFoundError(...)
    return MODEL_STORAGE[model_id]
```

#### Delete Model
```python
def delete_model(model_id: str) -> None:
    """Delete model from session storage.

    Raises:
        ModelNotFoundError: If model_id not found
    """
    if model_id not in MODEL_STORAGE:
        raise ModelNotFoundError(...)
    del MODEL_STORAGE[model_id]
```

### Storage Limits (MVP)

**No Hard Limits Enforced**:
- Models: Unlimited (constrained by server memory)
- Media: Unlimited (constrained by server memory)
- Model size: Unlimited (typical: 10-50 MB per model)

**Practical Constraints**:
- Typical model: ~10-50 MB in memory
- Reasonable session: 10-100 models
- Large session: 100-1000 models (may exceed memory)

**Future Limits** (v0.2.0+):
- Configurable max models per session (e.g., 100)
- Configurable max media per session (e.g., 50)
- Automatic eviction (FIFO or LRU)
- Persistent storage option

---

## Complete Workflow Example

### Scenario: Build and Analyze E. coli Model

**Step 1: Create Media**
```
User: "Create glucose minimal media"

AI → build_media({
  "compounds": ["cpd00027", "cpd00007", "cpd00001", ...],
  "custom_bounds": {"cpd00027": (-5, 100)}
})

Response:
{
  "success": true,
  "media_id": "media_20251027_143052_x1y2z3",
  "num_compounds": 18,
  "media_type": "minimal"
}

Storage State:
MEDIA_STORAGE = {
  "media_20251027_143052_x1y2z3": <MSMedia object>
}
```

**Step 2: Build Model**
```
User: "Build model from my E. coli proteins"

AI → build_model({
  "protein_sequences": {...},
  "template": "GramNegative"
})

Response:
{
  "success": true,
  "model_id": "model_20251027_143100_abc123.draft",
  "num_reactions": 856
}

Storage State:
MODEL_STORAGE = {
  "model_20251027_143100_abc123.draft": <Draft Model>
}
MEDIA_STORAGE = {
  "media_20251027_143052_x1y2z3": <MSMedia object>
}
```

**Step 3: Gapfill Model**
```
User: "Gapfill for growth in glucose media"

AI → gapfill_model({
  "model_id": "model_20251027_143100_abc123.draft",
  "media_id": "media_20251027_143052_x1y2z3"
})

Response:
{
  "success": true,
  "model_id": "model_20251027_143100_abc123.draft.gf",
  "original_model_id": "model_20251027_143100_abc123.draft",
  "num_reactions_added": 5,
  "growth_rate_after": 0.874
}

Storage State:
MODEL_STORAGE = {
  "model_20251027_143100_abc123.draft": <Original Draft>,
  "model_20251027_143100_abc123.draft.gf": <Gapfilled Model>
}
```

**Step 4: Run FBA**
```
User: "Run FBA and show top fluxes"

AI → run_fba({
  "model_id": "model_20251027_143100_abc123.draft.gf",
  "media_id": "media_20251027_143052_x1y2z3"
})

Response:
{
  "success": true,
  "objective_value": 0.874,
  "status": "optimal",
  "top_fluxes": [
    {"id": "bio1", "name": "Biomass", "flux": 0.874},
    {"id": "rxn00148_c0", "name": "hexokinase", "flux": 5.0}
  ]
}

Storage State: Unchanged (FBA is read-only)
```

**Step 5: List Models**
```
User: "Show me all my models"

AI → list_models({"filter_state": "all"})

Response:
{
  "success": true,
  "models": [
    {
      "model_id": "model_20251027_143100_abc123.draft",
      "state": "draft",
      "num_reactions": 856
    },
    {
      "model_id": "model_20251027_143100_abc123.draft.gf",
      "state": "gapfilled",
      "num_reactions": 861
    }
  ],
  "total_models": 2
}
```

**Step 6: Cleanup**
```
User: "Delete the draft model, I only need the gapfilled version"

AI → delete_model({
  "model_id": "model_20251027_143100_abc123.draft"
})

Response:
{
  "success": true,
  "deleted_model_id": "model_20251027_143100_abc123.draft"
}

Storage State:
MODEL_STORAGE = {
  "model_20251027_143100_abc123.draft.gf": <Gapfilled Model>
}
```

**Step 7: Server Restart**
```
[Server shuts down]

Storage State:
MODEL_STORAGE = {}  # Cleared
MEDIA_STORAGE = {}  # Cleared (predefined media reloaded on next startup)
```

---

## Error Scenarios

### Model Not Found

**Cause**: Referencing model ID that doesn't exist in storage

**Common Triggers**:
- Typo in model ID
- Model created in previous session (server restarted)
- Model was deleted

**Response**:
```json
{
  "success": false,
  "error_type": "ModelNotFoundError",
  "message": "Model not found in session",
  "details": {
    "model_id": "model_nonexistent.draft",
    "available_models": [
      "model_20251027_abc123.draft",
      "model_20251027_abc123.draft.gf"
    ]
  },
  "suggestion": "Use list_models tool to see available models."
}
```

### Media Not Found

**Cause**: Referencing media ID that doesn't exist in storage

**Response**:
```json
{
  "success": false,
  "error_type": "MediaNotFoundError",
  "message": "Media not found in session",
  "details": {
    "media_id": "media_nonexistent",
    "available_media": [
      "glucose_minimal_aerobic",
      "media_20251027_x1y2z3"
    ]
  },
  "suggestion": "Use list_media tool or build_media to create new media."
}
```

### Storage Collision

**Cause**: Generated model ID already exists (extremely rare)

**Response**:
```json
{
  "success": false,
  "error_type": "StorageCollisionError",
  "message": "Failed to generate unique model ID after retries",
  "details": {
    "attempts": 10,
    "last_attempted_id": "model_20251027_abc123.draft"
  },
  "suggestion": "This is extremely rare. Try again or contact support."
}
```

---

## Session Management Best Practices

### For Users

1. **List models regularly**: Use `list_models` to track what exists in session
2. **Delete unused models**: Free memory with `delete_model`
3. **Export before shutdown**: (Future feature) Export important models before server restart
4. **Use meaningful names**: Provide custom model names for easier identification

### For Developers

1. **Preserve originals**: Never modify models in storage, create copies
2. **Use state suffixes**: Always append `.gf` for gapfilled models
3. **Check existence**: Always verify model/media exists before operations
4. **Clear error messages**: Include available models/media in error responses
5. **Log storage stats**: Track memory usage and model counts

---

## Future Enhancements (v0.2.0+)

### Persistent Storage

**File-Based**:
- Auto-save models to JSON files in `~/.gem-flux/models/`
- Auto-load on server startup
- Session storage becomes cache layer

**Database**:
- SQLite for single-user
- PostgreSQL for multi-user
- Full ACID compliance

### Storage Management

**Features**:
- Configurable storage limits
- LRU eviction policy
- Time-based expiration
- Manual export/import tools

### Multi-User Sessions

**Architecture**:
- Session IDs per user
- Isolated storage namespaces
- Authentication and authorization
- Shared models (opt-in)

---

## Summary

**Key Concepts**:
- ✅ **Session-scoped**: All storage cleared on server restart
- ✅ **State suffixes**: `.draft`, `.draft.gf`, `.gf` track model history
- ✅ **Immutable originals**: Modifications create new models
- ✅ **Read-only analysis**: FBA and queries don't modify storage
- ✅ **Predefined media**: 4 standard media loaded at startup
- ✅ **No persistence**: Models/media lost on shutdown (MVP)

**Lifecycle Stages**:
1. **Creation**: Build model/media, generate ID, store
2. **Modification**: Gapfill model (creates new model with new ID)
3. **Analysis**: Run FBA (read-only, no storage changes)
4. **Query**: List models/media, inspect metadata
5. **Deletion**: Remove from storage (cannot be undone)
6. **Session End**: Clear all storage, memory freed

---

**Document Status**: ✅ Complete
**Last Updated**: October 28, 2025
**Related Specifications**:
- 010-model-storage.md
- 018-session-management-tools.md
- 002-data-formats.md
