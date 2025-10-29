# Model Storage and Persistence - Gem-Flux MCP Server

**Type**: Storage Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding session management and model lifecycle)
- Read: 002-data-formats.md (for model representation formats and model ID conventions)
- Read: 004-build-model-tool.md (for understanding how models are created)

## Purpose

This specification defines how metabolic models and media compositions are stored during a server session. It covers the storage lifecycle, model ID generation, session-based storage architecture, and the transition path to persistent storage in future versions.

## Core Design Principles

**Session-Based Storage for MVP**:
- Models and media stored in memory only
- Storage cleared when server restarts
- No file I/O for model persistence in MVP
- Simple, fast, no database dependencies

**Future-Proof Design**:
- Model ID format supports future persistence
- Clear separation between session storage and persistent storage
- Defined upgrade path to file-based or database storage

**Simplicity First**:
- No complex data structures
- Direct dictionary-based storage
- Fast O(1) lookups by ID
- Minimal memory footprint for typical workloads

## Storage Architecture

### In-Memory Storage Structure

**Server maintains two primary storage dictionaries**:

```python
# Conceptual storage structure (not implementation)
MODEL_STORAGE = {
    "model_20251027_143052_a3f9b2.draft": <COBRApy Model object>,
    "model_20251027_143052_a3f9b2.draft.gf": <COBRApy Model object>,
    "E_coli_K12.draft": <COBRApy Model object>,
    "E_coli_K12.draft.gf": <COBRApy Model object>,
    "model_20251027_150312_b4k8c1.draft": <COBRApy Model object>,
    # ... additional models
}

MEDIA_STORAGE = {
    "media_20251027_143052_x1y2z3": <MSMedia object>,
    "media_20251027_150312_p9q8r7": <MSMedia object>,
    # ... additional media
}
```

**Storage Characteristics**:
- Models stored as COBRApy `Model` objects
- Media stored as ModelSEEDpy `MSMedia` objects
- Keys are unique identifiers (model_id, media_id)
- Values are mutable objects (can be modified by tools)
- No size limits enforced (MVP)
- No expiration or cleanup (except on restart)

### Model ID Format

**Structure**: `<base_name>.<state_suffix>`

**Components**:
- **Base name**: Either auto-generated or user-provided
  - Auto-generated: `model_<timestamp>_<random>`
    - Timestamp: `YYYYMMDD_HHMMSS` format (e.g., `20251027_143052`)
    - Random: 6 alphanumeric characters (e.g., `a3f9b2`)
  - User-provided: Custom name (e.g., `E_coli_K12`)
- **State suffix**: Indicates model processing state
  - `.draft` - Built but not gapfilled
  - `.gf` - Gapfilled (source was already gapfilled)
  - `.draft.gf` - Built as draft, then gapfilled

**Examples**:
- `model_20251027_143052_a3f9b2.draft` - Newly built draft model
- `model_20251027_143052_a3f9b2.draft.gf` - Draft model after gapfilling
- `E_coli_K12.draft` - User-named draft model
- `E_coli_K12.draft.gf` - User-named model after gapfilling
- `model_20251027_150312_b4k8c1.gf.gf` - Gapfilled model, gapfilled again

**Generation Rules**:
1. Timestamp uses server's local time (YYYYMMDD_HHMMSS)
2. Random suffix generated using cryptographically secure random
3. ID uniqueness verified before storage (regenerate if collision)
4. User names: If collision detected, append `_<timestamp>` before state suffix
5. State suffix updated based on operation:
   - `build_model` always creates `.draft` suffix
   - `gapfill_model` transforms state suffix (see State Transitions below)

**ID Characteristics**:
- Length: 28-50 characters (auto-generated), varies (user-provided)
- Format: Alphanumeric with underscores and dots
- Sortable: Timestamp prefix enables chronological sorting
- Unique: Random suffix or timestamp prevents collisions
- Traceable: State suffix indicates processing history

### State Transitions

**State suffix transformations during gapfilling**:

1. **Input: `.draft`**
   - Operation: First gapfilling of draft model
   - Output: Replace `.draft` with `.draft.gf`
   - Example: `model_abc.draft` → `model_abc.draft.gf`

2. **Input: `.gf`**
   - Operation: Gapfilling an already-gapfilled model
   - Output: Append `.gf` (becomes `.gf.gf`)
   - Example: `model_abc.gf` → `model_abc.gf.gf`

3. **Input: `.draft.gf`**
   - Operation: Re-gapfilling a previously gapfilled draft
   - Output: Append `.gf` (becomes `.draft.gf.gf`)
   - Example: `model_abc.draft.gf` → `model_abc.draft.gf.gf`

**State Flow Diagram**:
```
build_model → model.draft
              ↓ gapfill_model
          model.draft.gf
              ↓ gapfill_model (again)
          model.draft.gf.gf
              ↓ gapfill_model (again)
          model.draft.gf.gf.gf
          ... (continues)
```

### ID Generation Algorithm

**Auto-Generated IDs**:
```python
import time
import random
import string

def generate_model_id(state: str = "draft") -> str:
    """Generate unique auto-generated model ID.

    Args:
        state: Model state ("draft", "gf", "draft.gf", etc.)

    Returns:
        Model ID like "model_20251027_143052_a3f9b2.draft"
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")  # Local time
    random_suffix = ''.join(
        random.choices(string.ascii_lowercase + string.digits, k=6)
    )
    return f"model_{timestamp}_{random_suffix}.{state}"

# Examples:
# generate_model_id("draft") → "model_20251027_143052_x7k9m2.draft"
# generate_model_id("draft.gf") → "model_20251027_150312_b4n8p1.draft.gf"
```

**User-Provided Names with Collision Handling**:
```python
def generate_model_id_from_name(
    model_name: str,
    state: str = "draft",
    existing_ids: set = None
) -> str:
    """Generate model ID from user-provided name.

    Args:
        model_name: User's custom name (e.g., "E_coli_K12")
        state: Model state ("draft", "gf", "draft.gf", etc.)
        existing_ids: Set of existing model IDs to check collisions

    Returns:
        Model ID with state suffix
    """
    base_id = f"{model_name}.{state}"

    # Check for collision
    if existing_ids and base_id in existing_ids:
        # Append timestamp to avoid collision
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_id = f"{model_name}_{timestamp}.{state}"

    return base_id

# Examples:
# generate_model_id_from_name("E_coli_K12", "draft", set())
#   → "E_coli_K12.draft"
#
# generate_model_id_from_name("E_coli_K12", "draft", {"E_coli_K12.draft"})
#   → "E_coli_K12_20251027_143052.draft"  # Collision avoided
```

**State Suffix Transformation**:
```python
def transform_state_suffix(current_model_id: str) -> str:
    """Transform model ID state suffix for gapfilling.

    Args:
        current_model_id: Existing model ID with state suffix

    Returns:
        New model ID with updated state suffix
    """
    # Split base name and state suffix
    parts = current_model_id.rsplit('.', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid model ID format: {current_model_id}")

    base_name, current_state = parts

    # Transform state based on current state
    if current_state == "draft":
        new_state = "draft.gf"
        # Keep same base name
        return f"{base_name}.{new_state}"
    else:
        # Append .gf for any other state
        return f"{current_model_id}.gf"

# Examples:
# transform_state_suffix("model_abc.draft") → "model_abc.draft.gf"
# transform_state_suffix("model_abc.gf") → "model_abc.gf.gf"
# transform_state_suffix("model_abc.draft.gf") → "model_abc.draft.gf.gf"
# transform_state_suffix("E_coli_K12.draft") → "E_coli_K12.draft.gf"
```

### Media ID Format

**Structure**: `media_<timestamp>_<random>`

**Components**:
- Prefix: `"media_"`
- Timestamp: `YYYYMMDD_HHMMSS` format
- Separator: `"_"`
- Random suffix: 6 alphanumeric characters

**Examples**:
- `media_20251027_143052_x1y2z3` - Glucose minimal media
- `media_20251027_150312_p9q8r7` - Rich media composition

**Generation follows same algorithm as auto-generated model IDs**.

## Model Lifecycle

### Lifecycle Stages

**1. Creation**
- Tool: `build_model`
- Action: Generate model_id with `.draft` state, build COBRApy model, store in MODEL_STORAGE
- Output: model_id (e.g., `model_20251027_143052_abc123.draft`) returned to caller
- Storage: Draft model stored with generated ID
- State: `.draft` suffix indicates ungapfilled

**2. Modification (Gapfilling)**
- Tool: `gapfill_model`
- Action:
  1. Load model by ID from MODEL_STORAGE
  2. Perform gapfilling operation
  3. Generate new model_id by transforming state suffix
  4. Store gapfilled model with new ID
- Output: New model_id for gapfilled version
- Storage: Both original AND gapfilled models stored
- Preservation: Original model unchanged, preserved for comparison
- State transition: `.draft` → `.draft.gf`

**3. Query/Analysis**
- Tools: `run_fba`, `list_models` (future), `get_model_info` (future)
- Action: Load model from storage (read-only or temporary modifications)
- Output: Analysis results (fluxes, growth rate, etc.)
- Storage: Model unchanged in storage
- Access: Models can be accessed by exact ID

**4. Session End**
- Event: Server restart or shutdown
- Action: All MODEL_STORAGE and MEDIA_STORAGE cleared
- Result: Models lost (MVP behavior)
- Future: Models persisted to disk before shutdown

### Model Versioning

**Implicit Versioning via State Suffixes**:

```
E_coli_K12.draft            → Original draft model
E_coli_K12.draft.gf         → Draft gapfilled (v1)
E_coli_K12.draft.gf.gf      → Regapfilled (v2)
E_coli_K12.draft.gf.ko      → With knockouts (future, v3)
```

**Versioning Characteristics**:
- No explicit version numbers (MVP)
- Suffix indicates derivation history
- Original models always preserved
- Lineage traceable through naming

**Benefits**:
- Simple: No version database needed
- Transparent: Version history in the ID
- Safe: Modifications never overwrite originals

### Media Lifecycle

**Similar to Model Lifecycle**:

**1. Creation** → `build_media` generates media_id, stores MSMedia object

**2. Usage** → Referenced by `gapfill_model`, `run_fba` (read-only)

**3. Session End** → Cleared on server restart

**No Modification Stage**: Media are immutable once created (create new media for changes)

## Storage Operations

### Store Model

**Operation**: Add model to storage

**Behavior**:
1. Generate unique model_id (verify not in MODEL_STORAGE)
2. Store COBRApy Model object with model_id as key
3. Return model_id to caller

**Constraints**:
- model_id must be unique
- Model object must be valid COBRApy Model
- No size limits (MVP)

**Error Conditions**:
- Collision after retries → ServerError (extremely rare)
- Invalid model object → ValidationError

### Retrieve Model

**Operation**: Load model from storage

**Behavior**:
1. Check if model_id exists in MODEL_STORAGE
2. If exists: Return COBRApy Model object
3. If not exists: Return error

**Constraints**:
- model_id must match exactly (case-sensitive)
- Returns reference to stored object (not a copy by default)

**Error Conditions**:
- model_id not found → ModelNotFoundError with list of available models

### Store Media

**Operation**: Add media to storage

**Behavior**:
1. Generate unique media_id
2. Store MSMedia object with media_id as key
3. Return media_id to caller

**Constraints**:
- media_id must be unique
- Media object must be valid MSMedia
- No size limits (MVP)

### Retrieve Media

**Operation**: Load media from storage

**Behavior**:
1. Check if media_id exists in MEDIA_STORAGE
2. If exists: Return MSMedia object
3. If not exists: Return error

**Error Conditions**:
- media_id not found → MediaNotFoundError with list of available media

### List Models (Helper Operation)

**Operation**: Get all model IDs in current session

**Behavior**:
1. Return list of all keys in MODEL_STORAGE
2. Optionally filter by pattern (e.g., only original models, only gapfilled)
3. Optionally sort by timestamp

**Output Example**:
```json
{
  "success": true,
  "models": [
    {
      "model_id": "model_20251027_a3f9b2",
      "type": "draft",
      "created": "2025-10-27T10:15:30Z"
    },
    {
      "model_id": "model_20251027_a3f9b2.gf",
      "type": "gapfilled",
      "parent": "model_20251027_a3f9b2",
      "created": "2025-10-27T10:18:45Z"
    }
  ],
  "total_models": 2
}
```

**Use Cases**:
- Debugging: See what models exist in current session
- Recovery: Find model_id after connection loss
- Cleanup: Identify models to delete (future)

### List Media (Helper Operation)

**Similar to List Models**:

**Output Example**:
```json
{
  "success": true,
  "media": [
    {
      "media_id": "media_20251027_x1y2z3",
      "num_compounds": 20,
      "media_type": "minimal",
      "created": "2025-10-27T10:12:15Z"
    }
  ],
  "total_media": 1
}
```

## Session Management

### Session Scope

**Definition**: A session is the lifetime of a single server process

**Session Start**:
- Event: Server startup
- Action: Initialize empty MODEL_STORAGE and MEDIA_STORAGE
- State: No models or media exist

**During Session**:
- Models and media accumulate as tools are called
- All stored objects remain in memory
- No automatic cleanup or expiration

**Session End**:
- Event: Server shutdown, restart, or crash
- Action: All storage cleared (garbage collected)
- Result: All models and media lost

### Single-Session Model (MVP)

**Characteristics**:
- One server process = one session
- No multi-user support (single user, single session)
- No session IDs or authentication
- No session persistence across restarts

**Limitations**:
- Models lost on crash
- No backup or recovery
- No sharing between users
- No long-term storage

**Mitigations**:
- Clear documentation: "Models are session-only"
- Future: Add export_model tool to save before shutdown
- Future: Persistent storage with automatic saving

### Session Cleanup (MVP Behavior)

**No Active Cleanup**:
- Models remain in memory until server restart
- No automatic deletion based on age
- No memory limits enforced

**Future Cleanup Strategies** (v0.2.0+):
- Time-based expiration (e.g., delete after 24 hours)
- LRU eviction (keep only N most recent models)
- Manual delete operation via tool
- Automatic save-to-disk before eviction

## Storage Limits

### MVP Limits (Soft)

**No Hard Limits Enforced**:
- Models: Unlimited (constrained only by server memory)
- Media: Unlimited (constrained only by server memory)
- Model size: Unlimited (typical: 500-1500 reactions)

**Practical Constraints**:
- Server memory: Typical model ~10-50 MB in memory
- Reasonable session: 10-100 models
- Large session: 100-1000 models (may exceed memory)

**Memory Estimation**:
```
Small model (500 reactions):     ~10 MB
Medium model (1500 reactions):   ~30 MB
Large model (5000 reactions):    ~100 MB

100 medium models:               ~3 GB
1000 medium models:              ~30 GB (exceeds typical server)
```

### Future Limits (v0.2.0+)

**Configurable Limits**:
```yaml
storage:
  max_models_per_session: 100
  max_media_per_session: 50
  max_model_size_mb: 500
  auto_cleanup_enabled: true
  cleanup_after_hours: 24
```

**Enforcement**:
- Return error when limit exceeded
- Suggest cleanup or export before continuing
- Automatic eviction of oldest models (if enabled)

## Storage Errors

### ModelNotFoundError

**Condition**: model_id does not exist in MODEL_STORAGE

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
      "model_20251027_a3f9b2.gf",
      "model_20251027_b4k8c1"
    ],
    "num_available": 3
  },
  "suggestion": "Use one of the available model IDs or create a new model with build_model"
}
```

**Common Causes**:
- Typo in model_id
- Model created in previous session (server restarted)
- Model ID from different server instance
- Model deleted (future)

### MediaNotFoundError

**Condition**: media_id does not exist in MEDIA_STORAGE

**Response**:
```json
{
  "success": false,
  "error_type": "MediaNotFoundError",
  "message": "Media 'media_20251027_xyz789' not found in current session",
  "details": {
    "requested_id": "media_20251027_xyz789",
    "available_media": [
      "media_20251027_x1y2z3",
      "media_20251027_p9q8r7"
    ],
    "num_available": 2
  },
  "suggestion": "Use one of the available media IDs or create new media with build_media"
}
```

### StorageCollisionError

**Condition**: Generated model_id or media_id already exists (extremely rare)

**Response**:
```json
{
  "success": false,
  "error_type": "StorageCollisionError",
  "message": "Failed to generate unique model ID after multiple attempts",
  "details": {
    "attempts": 10,
    "last_attempted_id": "model_20251027_a3f9b2"
  },
  "suggestion": "This is extremely rare. Try again or contact support."
}
```

**Mitigation**:
- Retry with new random suffix (up to 10 attempts)
- Use longer random suffix if collisions persist
- Log collision for investigation

## Future: Persistent Storage (v0.2.0+)

### File-Based Persistence

**Storage Location**:
```
~/.gem-flux/models/
  model_20251027_a3f9b2.json
  model_20251027_a3f9b2.gf.json
  model_20251027_b4k8c1.json

~/.gem-flux/media/
  media_20251027_x1y2z3.json
  media_20251027_p9q8r7.json
```

**Persistence Behavior**:
1. Models automatically saved to disk when created
2. Models loaded from disk on server startup
3. Session storage becomes a cache over file storage
4. Export/import tools for explicit file operations

**Benefits**:
- Survive server restarts
- No data loss on crashes
- Shareable via filesystem
- Git-friendly (JSON format)

### Database Persistence (v0.3.0+)

**Database Schema** (conceptual):
```sql
CREATE TABLE models (
  model_id VARCHAR(50) PRIMARY KEY,
  model_name VARCHAR(255),
  model_data JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  user_id VARCHAR(50),  -- for multi-user support
  parent_model_id VARCHAR(50),  -- lineage tracking
  metadata JSONB
);

CREATE TABLE media (
  media_id VARCHAR(50) PRIMARY KEY,
  media_data JSONB,
  created_at TIMESTAMP,
  user_id VARCHAR(50)
);
```

**Benefits**:
- Multi-user support
- Advanced queries (find all gapfilled models)
- Concurrent access
- Transactional updates
- Metadata indexing

### Migration Path

**Phase 1 (MVP v0.1.0)**: Session-only storage
- In-memory dictionaries
- No persistence
- Simple and fast

**Phase 2 (v0.2.0)**: File-based persistence
- Automatic save to JSON files
- Load on startup
- Session storage becomes cache
- Add import/export tools

**Phase 3 (v0.3.0)**: Database option
- SQLite for single-user
- PostgreSQL for multi-user
- Hybrid: cache + database
- Migration script from files to database

## Storage Performance

### MVP Performance Characteristics

**Store Model**:
- Time: O(1) dictionary insert
- Typical: < 1ms

**Retrieve Model**:
- Time: O(1) dictionary lookup
- Typical: < 1ms

**List Models**:
- Time: O(n) where n = number of models
- Typical: < 10ms for 100 models

**Memory Usage**:
- Per model: 10-100 MB (depends on size)
- 100 models: 1-10 GB RAM
- Recommendation: Monitor memory usage, restart if needed

### Future Performance (Persistent Storage)

**With File Persistence**:
- Store: 10-100ms (serialize + write)
- Retrieve first time: 10-100ms (read + deserialize)
- Retrieve cached: < 1ms (from memory)

**With Database**:
- Store: 5-50ms (serialize + SQL insert)
- Retrieve: 5-50ms (SQL query + deserialize)
- Query metadata: 1-10ms (indexed queries)

## Example Usage Scenarios

### Scenario 1: Basic Model Build and Store

```
User: "Build a model from my E. coli proteins"

AI → build_model(protein_sequences={...}, template="GramNegative")
Server:
  1. Create COBRApy model
  2. Generate model_id: "model_20251027_a3f9b2"
  3. Store in MODEL_STORAGE["model_20251027_a3f9b2"]
  4. Return model_id

AI → User: "Created model model_20251027_a3f9b2 with 856 reactions"
```

### Scenario 2: Gapfill Creates New Model

```
User: "Gapfill that model for glucose media"

AI → gapfill_model(model_id="model_20251027_a3f9b2", media_id="media_001")
Server:
  1. Load MODEL_STORAGE["model_20251027_a3f9b2"]
  2. Perform gapfilling (creates new model)
  3. Generate new model_id: "model_20251027_a3f9b2.gf"
  4. Store in MODEL_STORAGE["model_20251027_a3f9b2.gf"]
  5. Original model still exists at "model_20251027_a3f9b2"
  6. Return new model_id

AI → User: "Gapfilled model created: model_20251027_a3f9b2.gf
             Added 5 reactions. Growth rate now 0.874 hr⁻¹"
```

### Scenario 3: Run FBA (Read-Only)

```
User: "Run FBA on the gapfilled model"

AI → run_fba(model_id="model_20251027_a3f9b2.gf", media_id="media_001")
Server:
  1. Load MODEL_STORAGE["model_20251027_a3f9b2.gf"]
  2. Load MEDIA_STORAGE["media_001"]
  3. Apply media constraints to model (temporary)
  4. Run FBA
  5. Return results
  6. Model in storage unchanged

AI → User: "Growth rate: 0.874 hr⁻¹. Top fluxes: ..."
```

### Scenario 4: Model Not Found

```
User: "Run FBA on model_001"

AI → run_fba(model_id="model_001", media_id="media_001")
Server:
  1. Check MODEL_STORAGE["model_001"]
  2. Not found
  3. Return ModelNotFoundError with available models

Response:
{
  "success": false,
  "error_type": "ModelNotFoundError",
  "available_models": ["model_20251027_a3f9b2", "model_20251027_a3f9b2.gf"]
}

AI → User: "Model 'model_001' not found. Available models:
             - model_20251027_a3f9b2 (draft)
             - model_20251027_a3f9b2.gf (gapfilled)
             Did you mean one of these?"
```

### Scenario 5: Session Restart (Data Loss)

```
[Session 1]
User: "Build model"
AI → build_model(...) → model_id: "model_001"
User: "Gapfill it"
AI → gapfill_model(...) → model_id: "model_001.gf"

[Server restarts]

[Session 2]
User: "Run FBA on model_001.gf"
AI → run_fba(model_id="model_001.gf", ...)
Server: ModelNotFoundError (storage cleared)

AI → User: "That model doesn't exist (server restarted and cleared storage).
             You'll need to rebuild the model from scratch."
```

## Behavioral Contracts

### Storage Consistency

**Guarantee**: Models and media once stored remain unchanged unless explicitly modified

**Behavior**:
- `build_model` creates new model, never modifies existing
- `gapfill_model` creates new model with suffix, preserves original
- `run_fba` reads model without modification
- No background processes modify stored models

**Exception**: Python object mutability means direct modification is possible but not intended

### ID Uniqueness

**Guarantee**: No two models or media will have the same ID within a session

**Behavior**:
- ID generation includes random component
- Collision detection with retry
- Extremely low collision probability (< 1 in 10 billion)

### Session Isolation

**Guarantee**: Models in one session do not affect other sessions (future multi-user)

**MVP Behavior**: Single session only, no isolation needed

**Future Behavior**: Each session maintains separate namespace or user-scoped storage

## Testing Considerations

### Storage Lifecycle in Tests

Session storage is process-scoped and persists across test boundaries unless explicitly cleared.

**Best Practices:**

1. **Clear storage between tests** using `autouse` fixtures:
   ```python
   @pytest.fixture(autouse=True)
   def cleanup_storage():
       MODEL_STORAGE.clear()
       MEDIA_STORAGE.clear()
       yield
       MODEL_STORAGE.clear()
       MEDIA_STORAGE.clear()
   ```

2. **Verify storage operations** in test fixtures:
   ```python
   store_model(model_id, model)
   assert model_exists(model_id), "Storage verification failed"
   ```

3. **Use appropriate fixture scopes**:
   - `scope="module"` for expensive shared setup (databases, templates)
   - `scope="function"` (default) for test-specific state (models, media)

### Storage State Guarantees

- **Within a single test**: Storage state persists for the duration of the test
- **Between tests**: No guarantees unless explicit cleanup is implemented
- **Across test modules**: Storage persists unless cleared
- **Test isolation**: Tests must manage their own storage state

### Integration Test Patterns

See `docs/testing/integration-test-patterns.md` for detailed examples and common patterns.

**Example - Proper Storage Management:**

```python
@pytest.fixture(autouse=True)
def setup_storage():
    """Clear and initialize storage for each test."""
    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()

    # Optional: Load known state
    load_predefined_media()

    yield

    # Cleanup
    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()

@pytest.fixture
def test_model():
    """Create and verify test model."""
    model = build_test_model()
    model_id = "test_model.draft"
    store_model(model_id, model)

    # Verify storage succeeded
    assert model_exists(model_id), "Model storage failed"

    yield model_id

    # Cleanup handled by autouse fixture
```

**Common Pitfalls:**

1. ❌ **Assuming clean storage** - Storage may contain data from previous tests
2. ❌ **No storage verification** - Silent failures leave storage empty
3. ❌ **Wrong fixture scope** - Module-scoped fixtures share state across tests
4. ❌ **Incomplete cleanup** - Forgetting to clear both MODEL_STORAGE and MEDIA_STORAGE

**Solutions:**

1. ✅ Always clear storage at start of each test (autouse fixture)
2. ✅ Verify storage operations with assertions
3. ✅ Use function scope for test-specific state
4. ✅ Clear all storage types in cleanup fixtures

## Related Specifications

- **001-system-overview.md**: Overall session management architecture
- **002-data-formats.md**: Model ID format and model representation
- **004-build-model-tool.md**: Model creation and initial storage
- **005-gapfill-model-tool.md**: Model modification and derivative storage
- **006-run-fba-tool.md**: Model retrieval for analysis
- **011-model-import-export.md**: Future persistent storage operations

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 011-model-import-export.md
