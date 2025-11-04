# Pattern: Global State for MCP Tool Wrappers

**Status**: 📋 Documented (Implementation in Phase 11)
**Discovered**: Session 10 (Iteration 1, Phase 10)
**Category**: MCP Integration / Architecture

## Problem

FastMCP automatically generates JSON schemas from tool function signatures using Pydantic. When tool signatures include non-serializable custom classes (like `DatabaseIndex`), the server crashes on startup:

```
PydanticSchemaGenerationError: Unable to generate pydantic-core schema for <class 'DatabaseIndex'>
```

This prevents the MCP server from starting and makes tools inaccessible to LLM agents.

## Root Cause

**Architectural Mismatch**:
1. Core tool functions designed with `DatabaseIndex` parameter
2. FastMCP requires all parameters to be JSON-serializable
3. `DatabaseIndex` is custom class with complex internal state
4. Pydantic cannot auto-generate schema for custom classes

**Example of Broken Design**:
```python
# Core function (good design)
def build_media(
    compounds: list[str],
    default_uptake: float,
    custom_bounds: dict[str, tuple[float, float]] | None,
    db_index: DatabaseIndex  # ❌ Not JSON-serializable!
) -> dict:
    """Create growth medium..."""
    return create_medium(compounds, db_index)
```

**What Happens**:
```python
# FastMCP tries to register this as MCP tool
@mcp.tool()  # ❌ CRASHES: Cannot create schema for DatabaseIndex
def build_media(..., db_index: DatabaseIndex) -> dict:
    pass
```

## Solution

**Architecture: Global State Pattern**

Separate concerns:
1. **Core functions** - Take `DatabaseIndex` parameter (library usage)
2. **MCP wrappers** - No `DatabaseIndex` parameter (MCP usage)
3. **Global state** - Load resources once at startup, access via helpers

### Implementation

**Step 1: Global State in server.py**

```python
# src/gem_flux_mcp/server.py

from typing import Optional
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.templates.loader import ModelSEEDTemplates

# Global state (loaded once at startup)
_db_index: Optional[DatabaseIndex] = None
_templates: Optional[ModelSEEDTemplates] = None

def get_db_index() -> DatabaseIndex:
    """Get the global database index.

    Returns:
        DatabaseIndex: The loaded database index

    Raises:
        RuntimeError: If database not loaded yet
    """
    if _db_index is None:
        raise RuntimeError("Database not loaded. Call load_resources() first.")
    return _db_index

def get_templates() -> ModelSEEDTemplates:
    """Get the global template collection.

    Returns:
        ModelSEEDTemplates: The loaded templates

    Raises:
        RuntimeError: If templates not loaded yet
    """
    if _templates is None:
        raise RuntimeError("Templates not loaded. Call load_resources() first.")
    return _templates

def load_resources() -> None:
    """Load database and templates into global state.

    Called once at server startup before registering tools.
    """
    global _db_index, _templates

    logger.info("Loading database...")
    compounds_df = load_compounds_database("data/database/compounds.tsv")
    reactions_df = load_reactions_database("data/database/reactions.tsv")
    _db_index = DatabaseIndex(compounds_df, reactions_df)

    logger.info("Loading templates...")
    _templates = load_all_templates("data/templates/")

    logger.info("✅ Resources loaded successfully")
```

**Step 2: MCP Tool Wrappers in mcp_tools.py**

```python
# src/gem_flux_mcp/mcp_tools.py (NEW FILE)

from gem_flux_mcp.server import get_db_index, get_templates
from gem_flux_mcp.tools.media_builder import build_media as _build_media
from gem_flux_mcp.tools.build_model import build_model as _build_model

@mcp.tool()
def build_media(
    compounds: list[str],
    default_uptake: float = 100.0,
    custom_bounds: dict[str, tuple[float, float]] | None = None
) -> dict:
    """Create a growth medium from ModelSEED compound IDs.

    This tool validates compound IDs against the ModelSEED database,
    creates a medium with the specified compounds, and stores it
    in session storage for use with model building and simulation.

    Args:
        compounds: List of ModelSEED compound IDs (e.g., ['cpd00027', 'cpd00007'])
        default_uptake: Maximum uptake rate (mmol/gDW/h) for all compounds (default: 100.0)
        custom_bounds: Custom bounds for specific compounds, e.g., {'cpd00027': (-5, 100)}

    Returns:
        Dictionary with media_id, compounds list, and metadata

    Example:
        >>> build_media(
        ...     compounds=["cpd00027", "cpd00007"],  # glucose + oxygen
        ...     default_uptake=10.0
        ... )
        {
            "success": true,
            "media_id": "media_20251029_143052_x1y2z3",
            "compounds": [...],
            "num_compounds": 2
        }
    """
    # Access global state (no DatabaseIndex in signature!)
    db_index = get_db_index()

    # Create request object
    from gem_flux_mcp.tools.media_builder import BuildMediaRequest
    request = BuildMediaRequest(
        compounds=compounds,
        default_uptake=default_uptake,
        custom_bounds=custom_bounds or {}
    )

    # Call core function with db_index
    return _build_media(request, db_index)


@mcp.tool()
def build_model(
    model_source: str,
    model_type: str,
    media_id: str | None = None
) -> dict:
    """Build a metabolic model from genomic data.

    ... comprehensive docstring for LLM ...
    """
    db_index = get_db_index()
    templates = get_templates()

    from gem_flux_mcp.tools.build_model import BuildModelRequest
    request = BuildModelRequest(
        model_source=model_source,
        model_type=model_type,
        media_id=media_id
    )

    return _build_model(request, db_index, templates)
```

**Step 3: Server Registration**

```python
# src/gem_flux_mcp/server.py

def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    # Load resources FIRST
    load_resources()

    # CRITICAL: Import mcp_tools to register @mcp.tool() decorators
    import gem_flux_mcp.mcp_tools

    # Create server (tools already registered via decorators)
    server = FastMCP("gem-flux-mcp")

    return server
```

## Benefits

### 1. **Clean Separation of Concerns**

```python
# Core function (library usage)
def build_media(request, db_index: DatabaseIndex) -> dict:
    """Can be used directly as Python library."""
    pass

# MCP wrapper (MCP protocol usage)
@mcp.tool()
def build_media(compounds: list[str], ...) -> dict:
    """JSON-serializable signature for MCP."""
    db_index = get_db_index()
    return _build_media(request, db_index)
```

### 2. **FastMCP Compatibility**

```python
# ✅ All parameters JSON-serializable
@mcp.tool()
def build_media(
    compounds: list[str],          # ✅ JSON array
    default_uptake: float,         # ✅ JSON number
    custom_bounds: dict | None     # ✅ JSON object or null
) -> dict:                          # ✅ JSON object
    pass
```

### 3. **Single Resource Load**

```python
# Load once at startup (efficient)
load_resources()

# Used by all 11 tools (no reloading)
db_index = get_db_index()
```

### 4. **Consistent Error Handling**

```python
def get_db_index() -> DatabaseIndex:
    if _db_index is None:
        raise RuntimeError("Database not loaded")
    return _db_index
```

## Trade-offs

### Advantages
- ✅ FastMCP compatibility (JSON-serializable signatures)
- ✅ Efficient (load once, use many times)
- ✅ Clean separation (core vs MCP wrappers)
- ✅ Testable (can mock get_db_index())

### Disadvantages
- ⚠️ Global state (mutable shared state)
- ⚠️ Startup order dependency (must load resources first)
- ⚠️ Not thread-safe by default (FastMCP is async, so OK)
- ⚠️ Two layers (core function + wrapper)

### Why Acceptable
1. **MCP servers are single-process**: No multi-process issues
2. **FastMCP is async not threaded**: No thread-safety concerns
3. **Resources immutable after load**: No state mutation during runtime
4. **Clear startup sequence**: load_resources() → import mcp_tools → run server

## When to Apply

Apply this pattern when:
- Creating MCP tools with FastMCP
- Tool needs non-serializable dependencies (DatabaseIndex, templates, models)
- Resources can be loaded once at startup
- Single-process server environment

## Loop Improvement Opportunities

### 1. Server Startup Integration Test

```python
# tests/integration/test_mcp_server_integration.py

def test_server_starts_successfully():
    """Verify MCP server starts without Pydantic errors."""
    from gem_flux_mcp.server import create_server

    server = create_server()
    assert server is not None
    # This test would have caught the Pydantic error immediately!

def test_all_tools_registered():
    """Verify all 11 tools are registered with correct signatures."""
    server = create_server()
    tools = server.list_tools()

    assert len(tools) == 11
    for tool in tools:
        # Verify all parameters are JSON-serializable
        for param in tool.parameters:
            assert param.type in ["string", "number", "boolean", "object", "array", "null"]
```

### 2. MCP Client Test Script

```python
# scripts/test_mcp_client.py

"""Prove server works with real MCP client."""

from mcp import ClientSession

async def test_build_media_via_mcp():
    async with ClientSession("gem-flux-mcp") as session:
        result = await session.call_tool(
            "build_media",
            arguments={
                "compounds": ["cpd00027", "cpd00007"],
                "default_uptake": 100.0
            }
        )
        assert result["success"] == True
        assert "media_id" in result
```

### 3. Specification Requirements

```markdown
# specs/015-mcp-server-setup.md

## MCP Tool Signature Requirements

**CRITICAL**: All MCP tool parameters MUST be JSON-serializable.

**Allowed Types**:
- `str`, `int`, `float`, `bool`
- `list[T]` where T is JSON-serializable
- `dict[str, T]` where T is JSON-serializable
- `Optional[T]` where T is JSON-serializable

**NOT Allowed**:
- Custom classes (DatabaseIndex, ModelSEEDTemplates)
- COBRApy objects (Model, Reaction)
- ModelSEEDpy objects (MSMedia, MSModel)

**Solution**: Use global state pattern for shared resources.
```

## Related Files

**To Be Created (Phase 11)**:
- `src/gem_flux_mcp/mcp_tools.py` - MCP tool wrappers
- `tests/integration/test_mcp_server_integration.py` - Server tests
- `scripts/test_mcp_client.py` - Proof of concept

**To Be Modified (Phase 11)**:
- `src/gem_flux_mcp/server.py` - Add global state + helpers

**Documentation**:
- `specs/021-mcp-tool-registration.md` - Complete specification
- `docs/PHASE_11_MCP_INTEGRATION_PLAN.md` - Implementation guide

## Related Patterns

- [Mandatory Verification Gates](mandatory-verification-gates.md) - Prevent false completion
- [Observability](observability.md) - Error handling in wrappers

## Related Sessions

- [Session 10](../sessions/session-10-iteration-01-phase10-critical-audit.md) - Discovery
- (Session 11+ - Implementation, to be created)

## Impact

**Before Pattern** (Phase 8 - Broken):
- ❌ Server crashes on startup with Pydantic error
- ❌ No tools accessible via MCP protocol
- ❌ User's colleagues can't use agents
- ❌ Main project purpose unfulfilled

**After Pattern** (Phase 11 - To Implement):
- ✅ Server starts successfully
- ✅ All 11 tools accessible via MCP
- ✅ LLM agents can discover and call tools
- ✅ Project fulfills main purpose

**Prevented Issues**:
- Emergency patch for broken MCP server
- User abandonment ("MCP doesn't work")
- Days/weeks of debugging without architectural understanding
- Technical debt from ad-hoc fixes
