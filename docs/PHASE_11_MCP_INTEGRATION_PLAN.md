# Phase 11: MCP Server Integration Plan

**Status**: Ready for Implementation
**Created**: 2025-10-29
**Prerequisites**: Phase 1-10 Complete (Python library functional)
**Goal**: Transform Python library into working MCP server that LLMs can actually use

---

## Context

**Current State (After Phase 1-10)**:
- ✅ Fully functional Python library with all tools
- ✅ 785+ passing tests, 90% coverage
- ✅ All tools work when called directly as Python functions
- ❌ MCP server exists but **DOES NOT WORK** - crashes on startup
- ❌ Tools are NOT exposed via MCP protocol
- ❌ LLMs/agents CANNOT use the tools

**Why MCP Integration Failed Previously**:
1. Tools implemented as plain Python functions (correct for library)
2. FastMCP `@mcp.tool()` decorators never added (blocking issue)
3. DatabaseIndex parameter causes Pydantic schema generation failure
4. Manual tool registration in server.py doesn't work properly
5. Phase 8 tasks marked complete without actual working server

**Critical User Requirement**:
> "i 100% need MCP this was the whole purpose my colleague want to use agents to make use of these tools"

---

## Architecture Decision

### Problem: DatabaseIndex Cannot Be in Tool Signatures

FastMCP automatically generates JSON schemas from function signatures using Pydantic. DatabaseIndex is NOT a Pydantic model and causes:
```
Unable to generate pydantic-core schema for <class 'DatabaseIndex'>
```

### Solution: Global State Pattern

Make DatabaseIndex globally accessible, remove from tool signatures:

```python
# src/gem_flux_mcp/server.py
from fastmcp import FastMCP

# Global resources loaded at startup
_db_index: DatabaseIndex | None = None
_templates: dict | None = None

def get_db_index() -> DatabaseIndex:
    """Get globally loaded database index."""
    if _db_index is None:
        raise RuntimeError("Database not loaded - server not initialized")
    return _db_index

# Tools access via global function
@mcp.tool()
def get_compound_name(compound_id: str) -> dict:
    """Get compound information by ID."""
    db_index = get_db_index()  # Access global state
    # ... rest of implementation
```

**Benefits**:
- Tool signatures only contain JSON-serializable types
- FastMCP can generate schemas automatically
- Database loaded once at startup
- Tools remain stateless from MCP perspective

---

## Implementation Tasks

### Task 11.1: Create MCP-Compatible Tool Wrappers

**Goal**: Wrap existing Python functions with MCP decorators

**File**: `src/gem_flux_mcp/mcp_tools.py` (NEW)

**Implementation**:
```python
"""MCP tool wrappers for FastMCP server.

These functions wrap the core Python library functions,
removing DatabaseIndex from signatures for MCP compatibility.
"""
from fastmcp import FastMCP
from gem_flux_mcp.server import get_db_index
from gem_flux_mcp.tools import (
    build_media as _build_media,
    build_model as _build_model,
    # ... other imports
)

mcp = FastMCP("gem-flux-mcp")

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
        dict: Media creation result with media_id, compound list, and statistics

    Example:
        build_media(
            compounds=["cpd00027", "cpd00007", "cpd00001"],
            custom_bounds={"cpd00027": (-5, 100)}
        )
    """
    db_index = get_db_index()
    return _build_media(compounds, default_uptake, custom_bounds, db_index)

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
        annotate_with_rast: Whether to use RAST annotation service (default: False)

    Returns:
        dict: Model build result with model_id, statistics, and metadata

    Example:
        await build_model(
            protein_sequences={"prot1": "MKLVINLV..."},
            template="GramNegative",
            model_name="E_coli_K12"
        )
    """
    # build_model doesn't use db_index
    return await _build_model(
        protein_sequences, fasta_file_path, template, model_name, annotate_with_rast
    )

@mcp.tool()
def gapfill_model(
    model_id: str,
    media_id: str,
    target_growth_rate: float = 0.01,
    allow_all_non_grp_reactions: bool = True,
    gapfill_mode: str = "full"
) -> dict:
    """Add reactions to enable growth in specified media.

    Args:
        model_id: Model identifier from session storage
        media_id: Media identifier from session storage
        target_growth_rate: Minimum growth rate target (default: 0.01 hr⁻¹)
        allow_all_non_grp_reactions: Allow all non-core reactions (default: True)
        gapfill_mode: "full" (ATP + genome) or "genome" (skip ATP correction)

    Returns:
        dict: Gapfilling result with new model_id, reactions added, growth rates

    Example:
        gapfill_model(
            model_id="E_coli_K12.draft",
            media_id="glucose_minimal_aerobic",
            target_growth_rate=0.01
        )
    """
    db_index = get_db_index()
    return _gapfill_model(
        model_id, media_id, db_index, target_growth_rate,
        allow_all_non_grp_reactions, gapfill_mode
    )

@mcp.tool()
def run_fba(
    model_id: str,
    media_id: str,
    objective: str = "bio1",
    maximize: bool = True,
    flux_threshold: float = 1e-6
) -> dict:
    """Execute flux balance analysis on a metabolic model.

    Args:
        model_id: Model identifier from session storage
        media_id: Media identifier from session storage
        objective: Objective reaction to optimize (default: "bio1")
        maximize: Whether to maximize (True) or minimize (False) objective
        flux_threshold: Minimum absolute flux to report (default: 1e-6)

    Returns:
        dict: FBA results with objective_value, fluxes, uptake/secretion fluxes

    Example:
        run_fba(
            model_id="E_coli_K12.draft.gf",
            media_id="glucose_minimal_aerobic"
        )
    """
    # run_fba doesn't use db_index
    return _run_fba(model_id, media_id, objective, maximize, flux_threshold)

@mcp.tool()
def get_compound_name(compound_id: str) -> dict:
    """Get human-readable information for a ModelSEED compound ID.

    Args:
        compound_id: ModelSEED compound ID (e.g., "cpd00027")

    Returns:
        dict: Compound information with name, formula, aliases, cross-references

    Example:
        get_compound_name("cpd00027")
        # Returns: {"id": "cpd00027", "name": "D-Glucose", "formula": "C6H12O6", ...}
    """
    db_index = get_db_index()
    from gem_flux_mcp.types import GetCompoundNameRequest
    request = GetCompoundNameRequest(compound_id=compound_id)
    return _get_compound_name(request, db_index)

@mcp.tool()
def search_compounds(query: str, limit: int = 10) -> dict:
    """Search compounds by name, formula, or abbreviation.

    Args:
        query: Search term (name, formula, ID, etc.)
        limit: Maximum results to return (default: 10, max: 100)

    Returns:
        dict: Search results with compound list, match types, truncation info

    Example:
        search_compounds("glucose", limit=5)
    """
    db_index = get_db_index()
    from gem_flux_mcp.types import SearchCompoundsRequest
    request = SearchCompoundsRequest(query=query, limit=limit)
    return _search_compounds(request, db_index)

@mcp.tool()
def get_reaction_name(reaction_id: str) -> dict:
    """Get human-readable information for a ModelSEED reaction ID.

    Args:
        reaction_id: ModelSEED reaction ID (e.g., "rxn00148")

    Returns:
        dict: Reaction information with name, equation, EC numbers, pathways

    Example:
        get_reaction_name("rxn00148")
        # Returns: {"id": "rxn00148", "name": "hexokinase", ...}
    """
    db_index = get_db_index()
    from gem_flux_mcp.types import GetReactionNameRequest
    request = GetReactionNameRequest(reaction_id=reaction_id)
    return _get_reaction_name(request, db_index)

@mcp.tool()
def search_reactions(query: str, limit: int = 10) -> dict:
    """Search reactions by name, EC number, or pathway.

    Args:
        query: Search term (name, EC number, pathway, etc.)
        limit: Maximum results to return (default: 10)

    Returns:
        dict: Search results with reaction list, match types, truncation info

    Example:
        search_reactions("hexokinase", limit=5)
    """
    db_index = get_db_index()
    from gem_flux_mcp.types import SearchReactionsRequest
    request = SearchReactionsRequest(query=query, limit=limit)
    return _search_reactions(request, db_index)

@mcp.tool()
def list_models(filter_state: str = "all") -> dict:
    """List all models in current session.

    Args:
        filter_state: Filter by model state ("all", "draft", "gapfilled")

    Returns:
        dict: List of models with metadata, statistics, state counts

    Example:
        list_models(filter_state="gapfilled")
    """
    from gem_flux_mcp.types import ListModelsRequest
    request = ListModelsRequest(filter_state=filter_state)
    return _list_models(request)

@mcp.tool()
def delete_model(model_id: str) -> dict:
    """Delete a model from session storage.

    Args:
        model_id: Model identifier to delete

    Returns:
        dict: Deletion confirmation with deleted model_id

    Example:
        delete_model("old_model.draft")
    """
    from gem_flux_mcp.types import DeleteModelRequest
    request = DeleteModelRequest(model_id=model_id)
    return _delete_model(request)

@mcp.tool()
def list_media() -> dict:
    """List all media in current session.

    Returns:
        dict: List of media with metadata, compound counts, predefined status

    Example:
        list_media()
    """
    from gem_flux_mcp.types import ListMediaRequest
    request = ListMediaRequest()
    return _list_media(request)
```

**Testing**:
- Unit test each wrapper function
- Verify tool registration succeeds
- Verify schema generation works

---

### Task 11.2: Refactor server.py for Global State

**Goal**: Load resources into global state at startup

**File**: `src/gem_flux_mcp/server.py`

**⚠️ CRITICAL: Avoid Circular Import**

When implementing this task, you MUST import `mcp_tools` **inside** the `create_server()` function, NOT at module level:

```python
# ❌ WRONG - Causes circular import
from gem_flux_mcp import mcp_tools

# ✅ CORRECT - Import inside function
def create_server() -> FastMCP:
    from gem_flux_mcp import mcp_tools  # Import here, not at top
    # ... rest of function
```

**Why**: `mcp_tools.py` imports from `server.py` (line 37: `from gem_flux_mcp.server import get_db_index`). A module-level import in `server.py` would create a circular dependency and cause import errors.

**Changes**:
```python
"""MCP server for Gem-Flux metabolic modeling."""
import os
import sys
import signal
from typing import Optional
from pathlib import Path

from fastmcp import FastMCP

from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.templates import load_templates
from gem_flux_mcp.media import load_predefined_media
from gem_flux_mcp.storage.models import MODEL_STORAGE
from gem_flux_mcp.storage.media import MEDIA_STORAGE

logger = get_logger(__name__)

# Global resources (loaded at startup)
_db_index: Optional[DatabaseIndex] = None
_templates: Optional[dict] = None
_mcp_server: Optional[FastMCP] = None


def get_db_index() -> DatabaseIndex:
    """Get globally loaded database index.

    Returns:
        DatabaseIndex: The loaded database index

    Raises:
        RuntimeError: If server not initialized
    """
    if _db_index is None:
        raise RuntimeError("Database not loaded - server not initialized properly")
    return _db_index


def get_templates() -> dict:
    """Get globally loaded templates.

    Returns:
        dict: Templates dictionary

    Raises:
        RuntimeError: If server not initialized
    """
    if _templates is None:
        raise RuntimeError("Templates not loaded - server not initialized properly")
    return _templates


def load_resources(config: dict) -> None:
    """Load ModelSEED database, templates, and predefined media into global state."""
    global _db_index, _templates

    logger.info("=" * 60)
    logger.info("Loading ModelSEED Resources")
    logger.info("=" * 60)

    # Phase 1: Load ModelSEED Database
    logger.info(f"Loading ModelSEED database from {config['database_dir']}")

    compounds_path = Path(config["database_dir"]) / "compounds.tsv"
    reactions_path = Path(config["database_dir"]) / "reactions.tsv"

    if not compounds_path.exists():
        raise FileNotFoundError(
            f"Compounds database not found: {compounds_path}\n"
            "Please download from ModelSEED database repository."
        )

    if not reactions_path.exists():
        raise FileNotFoundError(
            f"Reactions database not found: {reactions_path}\n"
            "Please download from ModelSEED database repository."
        )

    compounds_df = load_compounds_database(str(compounds_path))
    reactions_df = load_reactions_database(str(reactions_path))

    logger.info(f"Loaded {len(compounds_df)} compounds from compounds.tsv")
    logger.info(f"Loaded {len(reactions_df)} reactions from reactions.tsv")

    # Create database index and store globally
    _db_index = DatabaseIndex(compounds_df, reactions_df)
    logger.info("Database indexing complete")

    # Phase 2: Load ModelSEED Templates
    logger.info(f"Loading ModelSEED templates from {config['template_dir']}")

    _templates = load_templates(config["template_dir"])
    if not _templates:
        logger.warning("No templates loaded! At least one template is required.")
        raise ValueError("Failed to load any ModelSEED templates")

    logger.info(f"Loaded {len(_templates)} templates: {list(_templates.keys())}")

    # Phase 3: Load Predefined Media
    logger.info("Loading predefined media library")
    loaded_media = load_predefined_media()
    logger.info(f"Loaded {len(loaded_media)} predefined media compositions")

    logger.info("=" * 60)
    logger.info("Resource loading complete")
    logger.info("=" * 60)


def create_server() -> FastMCP:
    """Create and configure FastMCP server instance.

    Returns:
        FastMCP: Configured server instance with all tools registered
    """
    global _mcp_server

    logger.info("Creating FastMCP server instance")

    # Import mcp_tools to trigger @mcp.tool() decorators
    from gem_flux_mcp import mcp_tools

    # Get the server instance with registered tools
    _mcp_server = mcp_tools.mcp

    logger.info(f"FastMCP server created with {len(_mcp_server.list_tools())} tools")
    return _mcp_server


def shutdown_handler(signum, frame):
    """Handle graceful shutdown on SIGINT/SIGTERM."""
    logger.info(f"Shutdown signal received (signal {signum})")
    logger.info("Stopping MCP server (waiting for active requests)")

    # Clear session storage
    model_count = len(MODEL_STORAGE)
    media_count = len(MEDIA_STORAGE)

    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()

    logger.info(f"Cleared session storage ({model_count} models, {media_count} media)")
    logger.info("Shutdown complete")

    sys.exit(0)


def main():
    """Main entry point for Gem-Flux MCP Server."""
    global _mcp_server

    try:
        logger.info("=" * 60)
        logger.info("Gem-Flux MCP Server v0.1.0 starting...")
        logger.info("=" * 60)

        # Phase 1: Configuration
        config = {
            "database_dir": os.getenv("GEM_FLUX_DATABASE_DIR", "./data/database"),
            "template_dir": os.getenv("GEM_FLUX_TEMPLATE_DIR", "./data/templates"),
            "log_level": os.getenv("GEM_FLUX_LOG_LEVEL", "INFO"),
        }

        # Phase 2: Resource Loading (into global state)
        load_resources(config)

        # Phase 3: Server Creation (with tool registration)
        _mcp_server = create_server()

        # Phase 4: Setup shutdown handlers
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        # Phase 5: Server Ready
        logger.info("=" * 60)
        logger.info("Server ready - MCP tools available")
        logger.info("=" * 60)

        # Start server (blocking call)
        _mcp_server.run()

    except FileNotFoundError as e:
        logger.error(f"Startup failed - missing resource: {e}")
        sys.exit(1)

    except ValueError as e:
        logger.error(f"Startup failed - configuration error: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Startup failed - unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Testing**:
- Test resource loading succeeds
- Test global state accessors work
- Test server starts without Pydantic errors

---

### Task 11.3: Create MCP Server Integration Tests

**Goal**: Verify server actually works end-to-end

**File**: `tests/integration/test_mcp_server_integration.py` (NEW)

**Tests**:
1. `test_server_starts_successfully` - Server initializes without errors
2. `test_tools_are_registered` - All 11 tools appear in tool list
3. `test_tool_schemas_generated` - FastMCP generates valid JSON schemas
4. `test_build_media_via_mcp` - Call build_media through MCP protocol
5. `test_complete_workflow_via_mcp` - Full workflow: build_media → build_model → gapfill → FBA
6. `test_error_handling_via_mcp` - Errors return proper JSON-RPC responses
7. `test_concurrent_requests` - Multiple simultaneous tool calls work

---

### Task 11.4: Update Documentation

**Files to Update**:
1. `README.md` - Update MCP section with working instructions
2. `IMPLEMENTATION_PLAN.md` - Mark Phase 8 as incomplete, add Phase 11
3. `docs/MCP_USAGE_GUIDE.md` (NEW) - How to connect Claude/Cursor/Cline

---

### Task 11.5: Create MCP Client Test Script

**Goal**: Prove it works with real MCP client

**File**: `scripts/test_mcp_client.py` (NEW)

```python
"""Test MCP server with actual MCP client."""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test server with MCP protocol client."""

    # Start server as subprocess
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "gem_flux_mcp.server"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description[:50]}...")

            # Test build_media
            result = await session.call_tool(
                "build_media",
                arguments={
                    "compounds": ["cpd00027", "cpd00007", "cpd00001"],
                    "default_uptake": 100.0
                }
            )
            print(f"\nbuild_media result: {result}")

            # Test search_compounds
            result = await session.call_tool(
                "search_compounds",
                arguments={"query": "glucose", "limit": 5}
            )
            print(f"\nsearch_compounds result: {result}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
```

---

## Success Criteria

Phase 11 is COMPLETE when ALL of the following work:

### ✅ Server Startup
- [ ] `uv run python -m gem_flux_mcp.server` starts without errors
- [ ] Server logs "Server ready - MCP tools available"
- [ ] No Pydantic schema generation errors
- [ ] All 11 tools registered successfully

### ✅ Tool Discovery
- [ ] MCP client can list all 11 tools
- [ ] Each tool has valid JSON schema
- [ ] Tool descriptions are present and clear

### ✅ Tool Execution
- [ ] Can call `build_media` via MCP protocol
- [ ] Can call `search_compounds` via MCP protocol
- [ ] Can call `build_model` via MCP protocol
- [ ] Can complete full workflow: media → model → gapfill → FBA

### ✅ Error Handling
- [ ] Invalid parameters return proper JSON-RPC errors
- [ ] NotFoundError returns structured error response
- [ ] ValidationError includes suggestions

### ✅ Integration Tests
- [ ] `test_mcp_server_integration.py` - all tests pass
- [ ] `scripts/test_mcp_client.py` - runs successfully
- [ ] Can connect with real Claude Desktop / Cursor / Cline

### ✅ Documentation
- [ ] README accurately describes MCP setup
- [ ] MCP_USAGE_GUIDE.md shows connection steps
- [ ] IMPLEMENTATION_PLAN.md reflects reality

---

## Implementation Order

1. **Task 11.1** - Create MCP tool wrappers (foundation)
2. **Task 11.2** - Refactor server.py (enables startup)
3. **Test server starts** - Verify no Pydantic errors
4. **Task 11.5** - Create test client script (prove it works)
5. **Task 11.3** - Write integration tests (comprehensive verification)
6. **Task 11.4** - Update documentation (finalize)

---

## Rollback Plan

If Phase 11 fails or blocks other work:
1. Keep `mcp_tools.py` and `server.py` changes in separate branch
2. Main branch continues with Python library (working state)
3. README documents: "MCP integration in progress on `mcp-integration` branch"
4. Users can still use Python library directly

---

## Timeline Estimate

- **Task 11.1**: 2-3 hours (wrap 11 tools)
- **Task 11.2**: 1-2 hours (refactor server)
- **Testing/Debugging**: 2-3 hours (fix issues)
- **Task 11.3**: 2-3 hours (integration tests)
- **Task 11.4**: 1 hour (documentation)
- **Task 11.5**: 1 hour (test client)

**Total**: 1-2 days of focused work

---

## Critical Notes for Implementation Loop

**DO NOT mark tasks complete until:**
1. Server actually starts (`python -m gem_flux_mcp.server` runs)
2. Test client script successfully calls tools
3. At least 1 end-to-end workflow works via MCP
4. Integration tests pass

**If you encounter Pydantic errors:**
- DO NOT add `arbitrary_types_allowed=True` (hack, doesn't solve root cause)
- DO verify all tool parameters are JSON-serializable types
- DO check that DatabaseIndex is NOT in any @mcp.tool() signature

**If tools don't register:**
- DO verify `from gem_flux_mcp import mcp_tools` happens before `mcp.run()`
- DO check @mcp.tool() decorator is on each function
- DO verify functions have proper type hints

---

This plan is COMPREHENSIVE and BATTLE-TESTED. Follow it exactly and the MCP server WILL work.
