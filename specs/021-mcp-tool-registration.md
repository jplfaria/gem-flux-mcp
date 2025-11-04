# MCP Tool Registration Specification

**Type**: MCP Integration Specification
**Status**: Phase 11 - MCP Integration
**Version**: MVP v0.1.0
**Supersedes**: 015-mcp-server-setup.md (partial)

## Prerequisites

- Read: **015-mcp-server-setup.md** (server setup foundations)
- Read: **001-system-overview.md** (overall architecture)
- Understand: FastMCP framework and @mcp.tool() decorator pattern
- Understand: JSON schema generation from Python type hints

## Purpose

This specification defines how Python library functions are wrapped as MCP tools with proper FastMCP decorators, how global state is managed to avoid Pydantic schema issues, and how tools are registered for LLM/agent consumption.

## Problem Statement

**Original Implementation Issue**:
- Tools implemented as plain Python functions with `DatabaseIndex` parameters
- FastMCP cannot generate Pydantic schemas for non-serializable types (DatabaseIndex)
- Server crashes on startup: "Unable to generate pydantic-core schema for DatabaseIndex"
- Tools never properly registered with MCP protocol

**Root Cause**:
DatabaseIndex is a custom class that:
1. Is NOT a Pydantic model
2. Cannot be serialized to JSON
3. Cannot appear in tool signatures for FastMCP
4. Must be globally available, not passed as parameter

## Architecture Solution

### Global State Pattern

**Principle**: Resources loaded at server startup are stored globally, accessed via getter functions.

**Benefits**:
- Tool signatures contain only JSON-serializable types
- FastMCP can auto-generate schemas from type hints
- Resources loaded once, reused across all tool calls
- No serialization/deserialization overhead

**Pattern**:
```python
# server.py - Global state
_db_index: Optional[DatabaseIndex] = None

def get_db_index() -> DatabaseIndex:
    """Get globally loaded database index."""
    if _db_index is None:
        raise RuntimeError("Server not initialized")
    return _db_index

def load_resources(config):
    global _db_index
    # Load database and store globally
    _db_index = DatabaseIndex(compounds_df, reactions_df)
```

### MCP Tool Wrapper Pattern

**Principle**: Thin wrappers around core library functions, removing non-serializable parameters.

**Benefits**:
- Core library functions unchanged (still testable as Python)
- MCP wrappers handle global state access
- Clean separation of concerns
- @mcp.tool() decorators only on wrappers

**Pattern**:
```python
# mcp_tools.py - MCP wrappers
from fastmcp import FastMCP
from gem_flux_mcp.server import get_db_index
from gem_flux_mcp.tools.build_media import build_media as _build_media

mcp = FastMCP("gem-flux-mcp")

@mcp.tool()
def build_media(
    compounds: list[str],
    default_uptake: float = 100.0,
    custom_bounds: dict[str, tuple[float, float]] | None = None
) -> dict:
    """Create a growth medium from ModelSEED compound IDs."""
    db_index = get_db_index()  # Access global state
    return _build_media(compounds, default_uptake, custom_bounds, db_index)
```

## Tool Registration Specification

### File Structure

```
src/gem_flux_mcp/
├── server.py           # Server initialization, global state
├── mcp_tools.py        # MCP tool wrappers (NEW)
└── tools/              # Core library functions (unchanged)
    ├── build_media.py
    ├── build_model.py
    ├── gapfill_model.py
    ├── run_fba.py
    ├── compound_lookup.py
    ├── reaction_lookup.py
    ├── list_models.py
    ├── delete_model.py
    └── list_media.py
```

### MCP Tool Requirements

Each MCP tool wrapper MUST:

1. **Use @mcp.tool() decorator**
   ```python
   @mcp.tool()
   def tool_name(...) -> dict:
   ```

2. **Have JSON-serializable signature**
   - Allowed types: str, int, float, bool, list, dict, tuple, None
   - Type hints REQUIRED for all parameters and return value
   - NO custom classes (DatabaseIndex, MSMedia, COBRApy Model, etc.)

3. **Have comprehensive docstring**
   - Summary line (what tool does)
   - Args section with all parameters documented
   - Returns section describing output structure
   - Example section showing typical usage
   - Docstring becomes tool description for LLMs

4. **Access global state via getters**
   ```python
   db_index = get_db_index()  # NOT passed as parameter
   ```

5. **Return dict (NOT Pydantic model)**
   - FastMCP can serialize dicts automatically
   - Pydantic models optional (but add complexity)
   - Spec 002-data-formats.md defines return structure

### Tool Registration Order

**Startup Sequence**:
1. Load global resources (database, templates) → `server.py:load_resources()`
2. Import mcp_tools module → Triggers @mcp.tool() decorators
3. Get FastMCP instance → `mcp_tools.mcp`
4. Server ready → Call `mcp.run()`

**Code Flow**:
```python
# server.py:main()
load_resources(config)           # Step 1: Load into global state
from gem_flux_mcp import mcp_tools  # Step 2: Import triggers registration
mcp_server = mcp_tools.mcp       # Step 3: Get server instance
mcp_server.run()                 # Step 4: Start accepting requests
```

## Tool Specifications

### Core Modeling Tools

#### build_media

**Signature**:
```python
@mcp.tool()
def build_media(
    compounds: list[str],
    default_uptake: float = 100.0,
    custom_bounds: dict[str, tuple[float, float]] | None = None
) -> dict:
```

**Changes from Library Function**:
- Removed: `db_index: DatabaseIndex` parameter
- Added: `db_index = get_db_index()` call inside function

**Wrapper Implementation**:
```python
@mcp.tool()
def build_media(
    compounds: list[str],
    default_uptake: float = 100.0,
    custom_bounds: dict[str, tuple[float, float]] | None = None
) -> dict:
    """Create a growth medium from ModelSEED compound IDs.

    Args:
        compounds: List of ModelSEED compound IDs (e.g., ["cpd00027", "cpd00007"])
        default_uptake: Default uptake bound in mmol/gDW/h (default: 100.0)
        custom_bounds: Optional dict mapping compound IDs to (lower, upper) bounds

    Returns:
        dict: Media creation result
            - success: True if media created successfully
            - media_id: Unique media identifier
            - compounds: List of compound dicts with IDs, names, bounds
            - num_compounds: Total compound count
            - media_type: "minimal" (<50 compounds) or "rich" (>=50)

    Example:
        build_media(
            compounds=["cpd00027", "cpd00007", "cpd00001"],
            custom_bounds={"cpd00027": (-5, 100)}
        )
    """
    db_index = get_db_index()
    from gem_flux_mcp.tools.build_media import build_media as _build_media
    return _build_media(compounds, default_uptake, custom_bounds, db_index)
```

#### build_model

**Signature**:
```python
@mcp.tool()
async def build_model(
    protein_sequences: dict[str, str] | None = None,
    fasta_file_path: str | None = None,
    template: str = "GramNegative",
    model_name: str | None = None,
    annotate_with_rast: bool = False
) -> dict:
```

**Changes from Library Function**:
- NONE - build_model doesn't use db_index
- Kept async (FastMCP supports async tools)

**Wrapper Implementation**:
```python
@mcp.tool()
async def build_model(
    protein_sequences: dict[str, str] | None = None,
    fasta_file_path: str | None = None,
    template: str = "GramNegative",
    model_name: str | None = None,
    annotate_with_rast: bool = False
) -> dict:
    """Build a metabolic model from protein sequences.

    Args:
        protein_sequences: Dict mapping protein IDs to amino acid sequences
        fasta_file_path: Path to FASTA file (alternative to protein_sequences)
        template: ModelSEED template name (GramNegative, GramPositive, Core)
        model_name: Optional user-provided model name
        annotate_with_rast: Whether to use RAST annotation service

    Returns:
        dict: Model build result
            - success: True if model built successfully
            - model_id: Unique model identifier (e.g., "E_coli_K12.draft")
            - num_reactions: Total reactions in model
            - num_metabolites: Total metabolites in model
            - num_genes: Total genes in model
            - template_used: Template name used for building
            - has_biomass_reaction: Whether biomass reaction present
            - is_draft: True (ungapfilled model)

    Example:
        await build_model(
            protein_sequences={"prot1": "MKLVINLV..."},
            template="GramNegative",
            model_name="E_coli_K12"
        )
    """
    from gem_flux_mcp.tools.build_model import build_model as _build_model
    return await _build_model(
        protein_sequences, fasta_file_path, template, model_name, annotate_with_rast
    )
```

#### gapfill_model

**Signature**:
```python
@mcp.tool()
def gapfill_model(
    model_id: str,
    media_id: str,
    target_growth_rate: float = 0.01,
    allow_all_non_grp_reactions: bool = True,
    gapfill_mode: str = "full"
) -> dict:
```

**Changes from Library Function**:
- Removed: `db_index: DatabaseIndex` parameter
- Added: `db_index = get_db_index()` call inside function

#### run_fba

**Signature**:
```python
@mcp.tool()
def run_fba(
    model_id: str,
    media_id: str,
    objective: str = "bio1",
    maximize: bool = True,
    flux_threshold: float = 1e-6
) -> dict:
```

**Changes from Library Function**:
- NONE - run_fba doesn't use db_index

### Database Lookup Tools

#### get_compound_name

**Signature**:
```python
@mcp.tool()
def get_compound_name(compound_id: str) -> dict:
```

**Changes from Library Function**:
- Removed: `request: GetCompoundNameRequest` parameter
- Removed: `db_index: DatabaseIndex` parameter
- Added: Direct `compound_id: str` parameter
- Added: `request = GetCompoundNameRequest(compound_id=compound_id)` wrapper
- Added: `db_index = get_db_index()` call

**Rationale**: LLMs pass simple strings, not Request objects

#### search_compounds

**Signature**:
```python
@mcp.tool()
def search_compounds(query: str, limit: int = 10) -> dict:
```

**Changes from Library Function**:
- Removed: `request: SearchCompoundsRequest` parameter
- Removed: `db_index: DatabaseIndex` parameter
- Added: Direct parameters `query: str, limit: int`
- Added: `request = SearchCompoundsRequest(...)` wrapper

#### get_reaction_name

**Signature**:
```python
@mcp.tool()
def get_reaction_name(reaction_id: str) -> dict:
```

**Changes**: Same pattern as get_compound_name

#### search_reactions

**Signature**:
```python
@mcp.tool()
def search_reactions(query: str, limit: int = 10) -> dict:
```

**Changes**: Same pattern as search_compounds

### Session Management Tools

#### list_models

**Signature**:
```python
@mcp.tool()
def list_models(filter_state: str = "all") -> dict:
```

**Changes from Library Function**:
- Removed: `request: ListModelsRequest` parameter
- Added: Direct `filter_state: str` parameter
- Added: `request = ListModelsRequest(filter_state=filter_state)` wrapper

#### delete_model

**Signature**:
```python
@mcp.tool()
def delete_model(model_id: str) -> dict:
```

**Changes from Library Function**:
- Removed: `request: DeleteModelRequest` parameter
- Added: Direct `model_id: str` parameter

#### list_media

**Signature**:
```python
@mcp.tool()
def list_media() -> dict:
```

**Changes from Library Function**:
- Removed: `request: ListMediaRequest` parameter (no parameters needed)

## Global State Management

### Global Variables

**Location**: `src/gem_flux_mcp/server.py`

**Variables**:
```python
# Global resources (loaded at startup, read-only after initialization)
_db_index: Optional[DatabaseIndex] = None
_templates: Optional[dict] = None
_mcp_server: Optional[FastMCP] = None
```

**Initialization**:
```python
def load_resources(config: dict) -> None:
    """Load resources into global state."""
    global _db_index, _templates

    # Load database
    compounds_df = load_compounds_database(...)
    reactions_df = load_reactions_database(...)
    _db_index = DatabaseIndex(compounds_df, reactions_df)

    # Load templates
    _templates = load_templates(...)
```

### Accessor Functions

**Purpose**: Provide safe access to global state with error handling

**Functions**:
```python
def get_db_index() -> DatabaseIndex:
    """Get globally loaded database index.

    Returns:
        DatabaseIndex: The loaded database index

    Raises:
        RuntimeError: If server not initialized
    """
    if _db_index is None:
        raise RuntimeError(
            "Database not loaded - server not initialized properly. "
            "This indicates a bug in server startup sequence."
        )
    return _db_index


def get_templates() -> dict:
    """Get globally loaded templates.

    Returns:
        dict: Templates dictionary keyed by template name

    Raises:
        RuntimeError: If server not initialized
    """
    if _templates is None:
        raise RuntimeError(
            "Templates not loaded - server not initialized properly. "
            "This indicates a bug in server startup sequence."
        )
    return _templates
```

**Usage in MCP Tools**:
```python
@mcp.tool()
def some_tool(...) -> dict:
    db_index = get_db_index()  # Safe access with error handling
    # ... use db_index
```

## Error Handling

### Startup Errors

**DatabaseIndex Load Failure**:
```python
# server.py:load_resources()
try:
    compounds_df = load_compounds_database(compounds_path)
    reactions_df = load_reactions_database(reactions_path)
    _db_index = DatabaseIndex(compounds_df, reactions_df)
except FileNotFoundError as e:
    logger.error(f"Database files not found: {e}")
    raise  # Fatal - exit server
except Exception as e:
    logger.error(f"Failed to load database: {e}")
    raise  # Fatal - exit server
```

**Behavior**: Server exits with error code 1, logs error message

**Template Load Failure**:
```python
_templates = load_templates(template_dir)
if not _templates:
    raise ValueError("No templates loaded - at least one template required")
```

**Behavior**: Server exits with error code 1

### Runtime Errors

**Uninitialized Global State**:
```python
def get_db_index() -> DatabaseIndex:
    if _db_index is None:
        raise RuntimeError("Database not loaded - server not initialized")
    return _db_index
```

**Behavior**: Tool call fails with RuntimeError, returned as JSON-RPC error to client

**Tool Execution Errors**:
All errors from core library functions (ValidationError, NotFoundError, etc.) are caught by FastMCP and returned as JSON-RPC errors automatically.

## Testing Requirements

### Unit Tests

**test_mcp_tool_wrappers.py**:
1. `test_build_media_wrapper_signature` - Verify signature is MCP-compatible
2. `test_build_media_wrapper_calls_library` - Verify wrapper calls core function
3. `test_wrapper_accesses_global_state` - Verify get_db_index() called
4. Repeat for all 11 tools

**test_global_state.py**:
1. `test_get_db_index_before_init` - Raises RuntimeError
2. `test_get_db_index_after_init` - Returns DatabaseIndex
3. `test_load_resources_success` - Global state populated
4. `test_load_resources_missing_db` - Raises FileNotFoundError

### Integration Tests

**test_mcp_server_integration.py**:
1. `test_server_starts_successfully` - No Pydantic errors
2. `test_all_tools_registered` - 11 tools in tool list
3. `test_tool_schemas_valid` - Each tool has JSON schema
4. `test_build_media_via_mcp` - Call through MCP protocol
5. `test_complete_workflow_via_mcp` - Media → model → gapfill → FBA
6. `test_concurrent_tool_calls` - Multiple simultaneous requests

**test_mcp_client.py** (script):
Test with actual MCP client library, verify LLM can call tools

## Success Criteria

MCP tool registration is successful when:

1. ✅ Server starts without Pydantic schema errors
2. ✅ All 11 tools registered with FastMCP
3. ✅ Tool schemas generated automatically from type hints
4. ✅ MCP client can list all tools with descriptions
5. ✅ MCP client can call each tool successfully
6. ✅ Complete workflows work via MCP protocol
7. ✅ Errors return proper JSON-RPC responses
8. ✅ Integration tests pass
9. ✅ Real LLM clients (Claude/Cursor/Cline) can connect and use tools

## Alignment with Other Specifications

**Depends On**:
- **015-mcp-server-setup.md**: Server initialization sequence
- **002-data-formats.md**: Return value structures
- **013-error-handling.md**: Error response formats

**Extends**:
- **003-006**: Core tool specs (wrappers around these functions)
- **008-009**: Database lookup specs (wrappers around these functions)
- **018**: Session management specs (wrappers around these functions)

**Supersedes**:
- **015-mcp-server-setup.md** lines 214-281 (tool registration pattern)
  - Old spec showed incorrect pattern with db_index in signature
  - This spec defines correct global state pattern

## Future Enhancements

**Post-MVP Improvements** (v0.2.0+):
1. Dependency injection framework (alternative to global state)
2. Pydantic models for return values (better schema generation)
3. Tool versioning (multiple versions of same tool)
4. Tool permissions (per-client access control)
5. Tool rate limiting (prevent abuse)
6. Tool metrics (call counts, latency, errors)

---

**This specification defines the correct MCP tool registration pattern using global state to avoid Pydantic schema issues, enabling LLMs and agents to successfully use metabolic modeling tools via the MCP protocol.**
