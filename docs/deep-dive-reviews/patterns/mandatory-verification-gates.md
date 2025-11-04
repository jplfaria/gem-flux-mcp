# Pattern: Mandatory Verification Gates

**Status**: 📋 Documented (To Be Applied)
**Discovered**: Session 10 (Iteration 1, Phase 10)
**Category**: Project Management / Quality Assurance

## Problem

Tasks marked complete `[x]` in implementation plan without verifying functionality actually works. This creates false sense of progress and hides critical gaps until much later.

**Example from Phase 8**:
```markdown
- [x] Task 71: Implement FastMCP server initialization
- [x] Task 73: Implement tool registration with FastMCP
- [x] Task 75: Implement server startup sequence
```

**Reality**:
- ❌ Server crashes on startup with Pydantic error
- ❌ No @mcp.tool() decorators implemented
- ❌ Tools not accessible via MCP protocol
- ❌ **0% functional** despite marked 100% complete

## Root Cause

**Tasks marked complete based on**:
- ✅ File exists (`server.py` created)
- ✅ Function exists (`register_tools()` defined)
- ✅ Code compiles (no syntax errors)

**NOT based on**:
- ❌ Code runs without errors
- ❌ Tests pass
- ❌ End-to-end functionality verified
- ❌ Integration with other components works

**Result**: "Works on paper, fails in practice"

## Solution

**Add Explicit Verification Requirements to Every Task**

Each task must specify:
1. **What** needs to be done
2. **How** to verify it works
3. **Evidence** required before marking complete

### Template

```markdown
- [ ] **Task N**: Brief description

  **Implementation**:
  - What code changes are needed
  - What files to create/modify

  **Verification**:
  - How to test it works
  - Commands to run
  - Expected output

  **Success Criteria**:
  - [ ] Specific criterion 1
  - [ ] Specific criterion 2
  - [ ] Evidence provided (screenshot/log/test output)

  **DO NOT** mark complete until ALL criteria met
```

## Complete Example

### Phase 8 Task 71 (Before - Broken)

```markdown
- [x] **Task 71**: Implement FastMCP server initialization
```

**What Happened**:
- File created: `server.py`
- Functions written: `create_server()`, `load_resources()`
- Marked complete ✅
- **Never tested startup** ❌

**Result**: Server crashes, Phase 8 marked complete anyway

---

### Phase 8 Task 71 (After - With Verification Gate)

```markdown
- [ ] **Task 71**: Implement FastMCP server initialization

  **Implementation**:
  - Create `src/gem_flux_mcp/server.py`
  - Implement `create_server()` function
  - Implement `load_resources()` function
  - Handle FastMCP initialization

  **Verification**:
  ```bash
  # Server must start without errors
  uv run python -m gem_flux_mcp.server

  # Expected output:
  # [INFO] Loading database...
  # [INFO] Loading templates...
  # [INFO] ✅ Resources loaded successfully
  # [INFO] Server ready - MCP tools available
  # [INFO] Listening on stdio...
  ```

  **Success Criteria**:
  - [ ] Server starts without crashing
  - [ ] No Pydantic schema errors in logs
  - [ ] Database loads successfully
  - [ ] Templates load successfully
  - [ ] Server reaches "ready" state
  - [ ] Integration test passes: `test_server_starts_successfully()`
  - [ ] Evidence: Log output showing successful startup

  **MANDATORY GATE**: DO NOT mark [x] until server actually starts!
```

**What This Prevents**:
- ❌ Marking complete when server crashes
- ❌ Missing Pydantic errors
- ❌ Skipping integration test
- ❌ False sense of progress

---

### Phase 11 Task 11.1 (With Verification Gate)

```markdown
- [ ] **Task 11.1**: Create MCP tool wrappers

  **Implementation**:
  - Create `src/gem_flux_mcp/mcp_tools.py`
  - Wrap all 11 tools with @mcp.tool() decorators
  - Remove DatabaseIndex from signatures (use get_db_index())
  - Add comprehensive docstrings for LLMs

  **Verification**:
  ```bash
  # Server must start AND list tools
  uv run python -m gem_flux_mcp.server

  # In another terminal, test tool discovery
  python scripts/test_mcp_client.py --list-tools

  # Expected: All 11 tools listed with correct parameters
  ```

  **Success Criteria**:
  - [ ] All 11 tools have @mcp.tool() decorators
  - [ ] No DatabaseIndex in any tool signature
  - [ ] All parameters are JSON-serializable
  - [ ] Server starts without Pydantic errors
  - [ ] MCP client can list all 11 tools
  - [ ] Tool schemas are valid JSON
  - [ ] Integration test passes: `test_all_tools_registered()`
  - [ ] Evidence: Output of `test_mcp_client.py --list-tools`

  **MANDATORY GATE**: DO NOT mark [x] until MCP client can list tools!
```

---

## Benefits

### 1. **Prevents False Completion**

**Without Gate**:
```
Task 73: Implement tool registration [x]
Reality: No @mcp.tool() decorators, 0% done
```

**With Gate**:
```
Task 73: Implement tool registration [ ]
Verification: MCP client must list tools
Reality: Can't mark [x] until verified working
```

### 2. **Catches Issues Early**

**Without Gate**:
- Phase 8 marked complete
- User discovers MCP broken much later
- Need emergency audit and Phase 11

**With Gate**:
- Server startup test fails
- Issue caught before marking complete
- Fix immediately, no false progress

### 3. **Provides Clear Definition of "Done"**

**Ambiguous**:
```
- [x] Implement feature X
```
(Done means... code written? tests pass? works end-to-end?)

**Explicit**:
```
- [ ] Implement feature X
  Verification: Run command Y, see output Z
  Success: [ ] Command runs, [ ] Tests pass, [ ] Integration works
```

### 4. **Creates Accountability Trail**

```markdown
**Evidence**: Log output showing successful startup
```

Forces capture of proof that verification actually happened.

## When to Apply

Apply verification gates to:
- ✅ **All tasks** in implementation plan
- ✅ **Critical functionality** (server startup, MCP registration, tool calls)
- ✅ **Integration points** (components that must work together)
- ✅ **Phase boundaries** (before moving to next phase)

**Especially Important For**:
- Server/service initialization
- API/protocol integration
- Database loading
- Tool registration
- End-to-end workflows

## Implementation in IMPLEMENTATION_PLAN.md

### Current Format (Insufficient)

```markdown
### Phase 8: MCP Server Setup

- [x] Task 71: Implement FastMCP server initialization
- [x] Task 73: Implement tool registration with FastMCP
- [x] Task 75: Implement server startup sequence
```

### Improved Format (With Gates)

```markdown
### Phase 8: MCP Server Setup

- [ ] **Task 71**: Implement FastMCP server initialization

  **Verification**: Run `uv run python -m gem_flux_mcp.server`
  **Expected**: Server starts, logs show "Server ready"
  **Gate**: ❌ DO NOT mark [x] until server starts successfully

  **Success Criteria**:
  - [ ] Server starts without errors
  - [ ] test_server_starts_successfully() passes
  - [ ] Evidence: Startup log captured

- [ ] **Task 73**: Implement tool registration with FastMCP

  **Verification**: Run `scripts/test_mcp_client.py --list-tools`
  **Expected**: All 11 tools listed with correct parameters
  **Gate**: ❌ DO NOT mark [x] until MCP client lists tools

  **Success Criteria**:
  - [ ] All 11 tools have @mcp.tool() decorators
  - [ ] MCP client can list all tools
  - [ ] test_all_tools_registered() passes
  - [ ] Evidence: MCP tool list output captured
```

## Loop Improvement Opportunities

### 1. Automated Verification Check

```bash
# scripts/development/verify-task-completion.sh

# Before allowing task to be marked [x], run:
verify_task_71() {
    echo "Verifying Task 71: Server startup..."

    # Run server in background
    uv run python -m gem_flux_mcp.server &
    SERVER_PID=$!

    # Wait for startup
    sleep 5

    # Check if still running
    if ps -p $SERVER_PID > /dev/null; then
        echo "✅ Server started successfully"
        kill $SERVER_PID
        return 0
    else
        echo "❌ Server crashed on startup"
        return 1
    fi
}
```

### 2. Integration with Quality Gates

```bash
# scripts/development/run-quality-gates.sh

# Add verification checks
echo "🔍 Verifying task completion..."

# Check if any tasks marked [x] without passing verification
for task in $(get_completed_tasks); do
    if ! verify_task $task; then
        echo "❌ Task $task marked complete but verification fails!"
        exit 1
    fi
done
```

### 3. Template in Implementation Plan

```markdown
## Task Completion Template

When marking any task [x], you MUST:

1. **Implement** the functionality
2. **Verify** it works (run commands, check output)
3. **Test** with integration tests
4. **Capture** evidence (logs, screenshots)
5. **Check** all success criteria met

**If ANY criterion not met, task is NOT complete**
```

## Related Files

**Current Implementation Plan**:
- `IMPLEMENTATION_PLAN.md` - Needs verification gates added

**Phase 11 Tasks** (With Gates):
- See `IMPLEMENTATION_PLAN.md` lines 1042-1121
- Already includes mandatory gates

**Scripts to Create**:
- `scripts/development/verify-task-completion.sh`
- `scripts/test_mcp_client.py`

## Related Patterns

- [Global State for MCP Wrappers](global-state-mcp-wrappers.md) - Technical implementation
- [Observability](observability.md) - Capturing evidence for verification

## Related Sessions

- [Session 10](../sessions/session-10-iteration-01-phase10-critical-audit.md) - Discovery
- [Session 3](../sessions/session-03-iteration-10.md) - Similar systematic fix

## Impact Analysis

### Phase 8 (Without Verification Gates)

**Timeline**:
- **Day 1**: Loop creates server.py, marks tasks [x]
- **Day 2-7**: Continue other phases, assume Phase 8 works
- **Day 8**: User tries to use MCP server
- **Day 8**: Server crashes, discover Phase 8 40% done
- **Day 8-9**: Emergency audit, create Phase 11 plan
- **Day 10+**: Implement actual MCP integration

**Cost**: 9+ days with false progress, emergency rework

---

### Phase 8 (With Verification Gates)

**Timeline**:
- **Day 1**: Loop creates server.py
- **Day 1**: Verification fails (server crashes)
- **Day 1**: Cannot mark [x], issue caught immediately
- **Day 1-2**: Fix Pydantic error, implement global state
- **Day 2**: Verification passes, mark [x]
- **Day 3+**: Continue with confidence

**Cost**: 2 days, no false progress, no rework

**Savings**: 7 days + avoided emergency situation

---

## Before/After Comparison

### Without Verification Gates

```
Phase 8 Tasks: [x][x][x][x][x][x][x][x][x][x]
Actual Status: ❌ 40% functional
User Impact: Server completely broken
Developer Impact: Emergency audit needed
Time Cost: 9+ days of false progress + rework
```

### With Verification Gates

```
Phase 8 Tasks: [ ][ ][ ][x][x][x][x][ ][ ][x]
Actual Status: ✅ Marked tasks actually work
User Impact: Working MCP server
Developer Impact: No surprises, steady progress
Time Cost: 2-3 days, no rework
```

---

## Key Principles

1. **"Done" means "Verified Working"**, not "Code Written"
2. **Evidence Required**: Logs, test output, screenshots
3. **Integration Tests Mandatory**: Prove end-to-end functionality
4. **No Exceptions**: Every task needs verification
5. **Catch Early**: Better to fail verification Day 1 than discover issues later

---

## Adoption Checklist

- [ ] Add verification requirements to all existing tasks
- [ ] Create verification scripts (test_mcp_client.py, etc.)
- [ ] Update loop to check verification before marking [x]
- [ ] Add to task template in docs
- [ ] Train loop on new completion criteria
- [ ] Review all [x] tasks for false completion

---

**Next Steps**: Apply this pattern retroactively to all incomplete tasks, especially Phase 11.
