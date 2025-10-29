# Next Task for Implementation Loop

**IMPORTANT**: Read this file before proceeding with implementation.

---

## Current Status

**Phase 8**: INCOMPLETE (40% complete)
- Server skeleton exists but crashes on startup
- MCP tools NOT registered (no @mcp.tool() decorators)
- Pydantic schema error prevents server from starting
- **DO NOT continue Phase 8 with current approach**

**Phase 11**: NOT STARTED (CRITICAL - Required for MCP)
- Correct solution to complete MCP server integration
- Uses global state pattern to avoid Pydantic serialization issues
- Must be completed before Phase 8 can be marked done

---

## What You Should Do

### Start with Phase 11 Task 11.1

**Task**: Create MCP tool wrappers in `src/gem_flux_mcp/mcp_tools.py`

**Why Phase 11, not Phase 8?**
- Phase 8 tried to register tools with DatabaseIndex in signatures
- FastMCP cannot serialize DatabaseIndex → Pydantic schema error
- Phase 11 uses global state pattern (correct approach)
- See `docs/PHASE_11_MCP_INTEGRATION_PLAN.md` for complete details

**Priority**: CRITICAL
- User stated: "i 100% need MCP this was the whole purpose"
- MCP server must work for user's colleagues to use agents
- This is the main project purpose

---

## Phase 11 Task 11.1 Details

### What to Create

**File**: `src/gem_flux_mcp/mcp_tools.py` (NEW FILE)

### Implementation Requirements

1. **Import FastMCP and helpers**:
   ```python
   from fastmcp import FastMCP
   from gem_flux_mcp.server import get_db_index, get_templates
   ```

2. **Wrap all 11 tools with @mcp.tool() decorators**:
   - build_media
   - search_compounds
   - get_compound
   - search_reactions
   - get_reaction
   - build_model
   - gapfill_model
   - run_fba
   - list_models
   - list_media
   - delete_model

3. **Remove DatabaseIndex from tool signatures**:
   - ❌ OLD: `def build_media(..., db_index: DatabaseIndex) -> dict:`
   - ✅ NEW: `def build_media(...) -> dict:` (access via `get_db_index()`)

4. **Add comprehensive docstrings for LLMs**:
   - Explain what tool does
   - Describe parameters clearly
   - Provide usage examples
   - Format for LLM consumption

### Example (build_media wrapper)

```python
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
                  These are glucose and oxygen respectively.
        default_uptake: Maximum uptake rate (mmol/gDW/h) for all compounds.
                       Default is 100.0. Lower values create more restrictive media.
        custom_bounds: Optional custom bounds for specific compounds.
                      Format: {'cpd00027': (-5, 100)} sets glucose uptake to -5 min, 100 max.

    Returns:
        Dictionary containing:
        - success: bool - Whether operation succeeded
        - media_id: str - Unique identifier for created media (e.g., "media_20251029_143052_x1y2z3")
        - compounds: list - List of compounds with metadata
        - num_compounds: int - Total number of compounds in media

    Example:
        To create a simple glucose + oxygen aerobic medium:
        >>> build_media(
        ...     compounds=["cpd00027", "cpd00007"],
        ...     default_uptake=10.0
        ... )
        {
            "success": true,
            "media_id": "media_20251029_143052_x1y2z3",
            "compounds": [
                {"id": "cpd00027", "name": "D-Glucose", ...},
                {"id": "cpd00007", "name": "Oxygen", ...}
            ],
            "num_compounds": 2
        }
    """
    # Access global database index (no parameter!)
    db_index = get_db_index()

    # Create request object from parameters
    from gem_flux_mcp.tools.media_builder import BuildMediaRequest, build_media as _build_media
    request = BuildMediaRequest(
        compounds=compounds,
        default_uptake=default_uptake,
        custom_bounds=custom_bounds or {}
    )

    # Call core function with db_index
    return _build_media(request, db_index)
```

### Success Criteria

**DO NOT mark Task 11.1 complete until**:
- [ ] File `src/gem_flux_mcp/mcp_tools.py` created
- [ ] All 11 tools have @mcp.tool() decorators
- [ ] No DatabaseIndex in any tool signature
- [ ] All parameters are JSON-serializable (str, int, float, list, dict, Optional)
- [ ] Comprehensive docstrings added for LLM consumption
- [ ] Server imports mcp_tools (verify in server.py)
- [ ] Tests pass (if server startup test exists)

---

## Reference Documents

**MUST READ**:
1. `docs/PHASE_11_MCP_INTEGRATION_PLAN.md` - Complete 5-task implementation guide
2. `specs/021-mcp-tool-registration.md` - Technical specification
3. `MCP_INTEGRATION_STATUS.md` - Executive summary of current vs desired state

**Supporting Docs**:
- `IMPLEMENTATION_PLAN_AUDIT.md` - Why Phase 8 is incomplete
- `YOUR_QUESTIONS_ANSWERED.md` - Context and rationale

---

## Architecture: Global State Pattern

### The Problem (Phase 8 Approach)

```python
# ❌ THIS CRASHES - Pydantic can't serialize DatabaseIndex
def build_media(compounds: list[str], db_index: DatabaseIndex) -> dict:
    pass
```

### The Solution (Phase 11 Approach)

```python
# server.py - Global state
_db_index: Optional[DatabaseIndex] = None

def get_db_index() -> DatabaseIndex:
    if _db_index is None:
        raise RuntimeError("Database not loaded")
    return _db_index

# mcp_tools.py - Wrapper (JSON-serializable signature)
@mcp.tool()
def build_media(compounds: list[str]) -> dict:  # ✅ No DatabaseIndex!
    db_index = get_db_index()  # Access global
    return _build_media(request, db_index)  # Call core function
```

---

## Critical Reminders

### ❌ DO NOT

1. Try to fix Phase 8 without global state pattern
2. Add `arbitrary_types_allowed=True` to Pydantic (doesn't work)
3. Include DatabaseIndex in MCP tool signatures
4. Mark tasks complete without verification
5. Guess function signatures (check actual core function signatures)

### ✅ DO

1. Start with Phase 11 Task 11.1 (create mcp_tools.py)
2. Follow `docs/PHASE_11_MCP_INTEGRATION_PLAN.md` exactly
3. Use global state pattern (get_db_index(), get_templates())
4. Verify server starts after each change
5. Test with real MCP client before marking complete

---

## Verification Gate

**MANDATORY**: Phase 11 is NOT complete until:

```bash
# Server must start successfully
uv run python -m gem_flux_mcp.server

# Expected output:
# [INFO] Loading database...
# [INFO] Loading templates...
# [INFO] ✅ Resources loaded successfully
# [INFO] Server ready - MCP tools available

# Test client must successfully call tools
python scripts/test_mcp_client.py

# Expected: Successfully calls build_media, search_compounds, etc.
```

If server crashes or tools aren't accessible, **Phase 11 is NOT complete**.

---

## Summary

**Start here**: Phase 11 Task 11.1 - Create `src/gem_flux_mcp/mcp_tools.py`

**Why**: Phase 8 incomplete, Phase 11 is correct approach

**Goal**: Get MCP server working so user's colleagues can use agents

**Reference**: `docs/PHASE_11_MCP_INTEGRATION_PLAN.md`

**Gate**: Server must start + test_mcp_client.py must work

---

**Good luck! This is critical for project success.** 🚀
