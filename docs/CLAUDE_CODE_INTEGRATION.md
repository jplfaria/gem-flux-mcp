# Claude Code Integration Guide

**Live Debugging Setup for Gem-Flux MCP**

This guide shows how to integrate the Gem-Flux MCP server with Claude Code on macOS for live debugging and testing.

---

## Prerequisites

1. **Claude Code installed** on macOS
2. **argo-proxy running** at `http://localhost:8000/v1`
3. **Gem-Flux MCP repository** cloned at `/Users/jplfaria/repos/gem-flux-mcp`
4. **Python environment** set up with dependencies installed

---

## Quick Start

### 1. Verify argo-proxy is Running

```bash
# Check if argo-proxy is running
ps aux | grep argo-proxy

# If not running, start it from the gem-flux-mcp directory
cd /Users/jplfaria/repos/gem-flux-mcp
argo-proxy -c argo-config.yaml
```

Expected output:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. Configure Claude Code MCP Settings

Claude Code uses MCP servers defined in its configuration file. Add the Gem-Flux MCP server:

**Location**: `~/.config/claude-code/mcp_settings.json`

```json
{
  "mcpServers": {
    "gem-flux": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/jplfaria/repos/gem-flux-mcp",
        "run",
        "python",
        "-m",
        "gem_flux_mcp"
      ],
      "env": {
        "PYTHONPATH": "/Users/jplfaria/repos/gem-flux-mcp/src"
      }
    }
  }
}
```

**Explanation**:
- `command`: Use `uv` to run the MCP server in the virtual environment
- `args`: Specify the project directory and the server command
- `env`: Ensure Python can find the gem_flux_mcp package

### 3. Restart Claude Code

After updating the MCP settings:
1. Quit Claude Code completely (Cmd+Q)
2. Reopen Claude Code
3. The Gem-Flux MCP server should now be available

### 4. Verify MCP Server is Loaded

In Claude Code, ask:
```
What MCP tools are available?
```

You should see tools like:
- `get_compound_name`
- `search_compounds`
- `build_media`
- `build_model`
- `gapfill_model`
- `run_fba`
- And more...

---

## Testing the Integration

### Test 1: Simple Compound Search

In Claude Code, ask:
```
What is the ModelSEED ID for glucose?
```

**Expected behavior**: Claude should use the `search_compounds` tool and return compound IDs.

### Test 2: Build Media

```
Create a media called 'claude_test_media' with compounds cpd00001, cpd00009, and cpd00027
```

**Expected behavior**: Claude should use the `build_media` tool and create a TSV file in `/Users/jplfaria/repos/gem-flux-mcp/media/`

### Test 3: Build Model

```
Build a model named 'claude_test_model' with this sequence: MKKYTCTVCGYIYNPEDGDPDNGVNPGTDFKDIPDDWVCPLCGVGKDQFEEVEE
```

**Expected behavior**: Claude should use the `build_model` tool and create model files in `/Users/jplfaria/repos/gem-flux-mcp/models/`

### Test 4: Gapfilling Workflow

```
Build a model named 'gapfill_test' with sequence MKKYTCTVCGYIYNPEDGDPDNGVNPGTDFKDIPDDWVCPLCGVGKDQFEEVEE,
then create media 'minimal_glucose' with compounds cpd00001, cpd00009, cpd00027,
then gapfill the model on that media
```

**Expected behavior**: Claude should execute all three steps sequentially using multiple tools.

---

## Live Debugging with Claude Code

### Advantages of Claude Code for Debugging

1. **Real-time Tool Execution**: You can see Claude calling MCP tools in real-time
2. **Error Visibility**: Tool errors are displayed immediately in the conversation
3. **Iterative Testing**: Quickly test different queries and prompts
4. **File System Access**: Claude Code can read/write files, making it easy to inspect outputs
5. **Direct Communication**: You're in the same environment as the MCP server

### Debugging Workflow

1. **Monitor Logs**: Keep a terminal open with MCP server logs
   ```bash
   # In one terminal, watch MCP server logs
   cd /Users/jplfaria/repos/gem-flux-mcp
   tail -f logs/mcp_server.log  # If logging is configured
   ```

2. **Test Tool Calls**: In Claude Code, explicitly request tool usage
   ```
   Use the get_compound_name tool to look up cpd00027
   ```

3. **Inspect Tool Parameters**: Ask Claude to show what it's passing
   ```
   Show me the exact parameters you're passing to build_media
   ```

4. **Check Output Files**: Verify tool outputs
   ```
   Show me the contents of media/claude_test_media.tsv
   ```

5. **Test Error Handling**: Try invalid inputs
   ```
   What is the name of compound cpd99999?
   ```

### Common Debugging Scenarios

#### Scenario 1: Tool Not Found

**Symptom**: Claude says "I don't have access to that tool"

**Debug Steps**:
1. Check `~/.config/claude-code/mcp_settings.json` is correct
2. Restart Claude Code
3. Verify MCP server starts without errors:
   ```bash
   cd /Users/jplfaria/repos/gem-flux-mcp
   uv run python -m gem_flux_mcp
   ```

#### Scenario 2: Tool Execution Fails

**Symptom**: Tool returns an error

**Debug Steps**:
1. Check the exact error message in Claude Code
2. Run the tool manually to isolate the issue:
   ```python
   from gem_flux_mcp.server import initialize_server, create_server

   initialize_server()
   server = create_server()

   # Test tool directly
   result = await server.call_tool("get_compound_name", {"compound_id": "cpd00027"})
   print(result)
   ```

3. Check dependencies are installed:
   ```bash
   cd /Users/jplfaria/repos/gem-flux-mcp
   uv pip list | grep -E "(modelseedpy|cobra)"
   ```

#### Scenario 3: Wrong Parameters Passed

**Symptom**: Claude passes incorrect parameter types/formats

**Debug Steps**:
1. Check tool schema in `src/gem_flux_mcp/server.py`
2. Test with explicit parameter format:
   ```
   Call build_media with:
   - media_name: "test" (string)
   - compound_ids: ["cpd00001", "cpd00009"] (list of strings)
   ```

3. If issue persists, this indicates a prompt engineering problem - consider using Phase 2 enhanced prompts

---

## Switching Between Phase 1 and Phase 2

Claude Code doesn't directly support system prompts for MCP servers, but you can influence behavior through conversation context.

### Method 1: In-Conversation Guidance (Recommended)

Start each Claude Code session with context:

**For Phase 1 (Default) Behavior**:
```
I'm going to use Gem-Flux MCP tools. Remember:
1. Always use tools, never answer from memory
2. Validate parameters before calling tools
3. Execute all requested operations
```

**For Phase 2 (Enhanced) Behavior**:
```
I'm going to use Gem-Flux MCP tools. Remember these CRITICAL rules:

TOOL-SPECIFIC GUIDANCE:
- get_compound_name: Takes SINGLE compound ID (string like "cpd00027")
- build_media: compound_ids must be a LIST: ["cpd00001", "cpd00009"]
- build_model: sequences is a dict: {"gene1": "MKKY..."}
- gapfill_model: Model and media must exist first

PARAMETER CHECKLIST:
1. All REQUIRED parameters provided
2. Parameter types match (string, list, dict)
3. Lists are actually lists, not single strings
4. Compound IDs follow format "cpd#####"

COMMON ERRORS TO AVOID:
❌ WRONG: build_media(compound_ids="cpd00027")
✅ RIGHT: build_media(compound_ids=["cpd00027"])
```

### Method 2: Custom MCP Server Wrapper (Advanced)

Create a wrapper script that applies system prompts:

**File**: `/Users/jplfaria/repos/gem-flux-mcp/scripts/mcp_wrapper_phase2.sh`

```bash
#!/bin/bash
export GEMFLUX_SYSTEM_PROMPT="phase2"
cd /Users/jplfaria/repos/gem-flux-mcp
uv run python -m gem_flux_mcp
```

Update `mcp_settings.json`:
```json
{
  "mcpServers": {
    "gem-flux-phase2": {
      "command": "/Users/jplfaria/repos/gem-flux-mcp/scripts/mcp_wrapper_phase2.sh",
      "args": []
    }
  }
}
```

Then modify `src/gem_flux_mcp/server.py` to read the environment variable and apply the appropriate prompt.

---

## Testing Phase 2 Improvements

### Failed Phase 1 Tests to Retry

These tests failed in Phase 1 (0/3 passed) and should be tested with Phase 2 guidance:

#### Test 1: get_compound_name
```
What is the name of compound cpd00027?
```

**Phase 1 Issue**: Model answered from memory instead of using tool

**Phase 2 Guidance**: Start session with:
```
Use the get_compound_name tool to look up compound cpd00027.
Remember: you MUST use the tool, never answer from memory.
```

#### Test 2: build_media
```
Create a media called 'phase2_test_media' with compounds cpd00001, cpd00009, and cpd00027
```

**Phase 1 Issue**: Model passed string instead of list for compound_ids

**Phase 2 Guidance**: Start session with:
```
I need to build media. Remember: compound_ids must be a LIST of strings,
even for a single compound. Use ["cpd00001"] not "cpd00001".
```

#### Test 3: gapfill_model
```
Build a model named 'phase2_gapfill_test' with sequence MKKYTCTVCGYIYNPEDGDPDNGVNPGTDFKDIPDDWVCPLCGVGKDQFEEVEE,
then create media 'phase2_minimal' with compounds cpd00001, cpd00009, cpd00027,
then gapfill the model on that media
```

**Phase 1 Issue**: Model skipped intermediate steps

**Phase 2 Guidance**: Start session with:
```
I need to run a gapfilling workflow. Remember:
1. First build the model
2. Then build the media
3. Finally gapfill (model and media must exist first)
Execute ALL steps, don't skip any.
```

---

## Monitoring and Metrics

### Track Success Rates

Keep a log of queries and outcomes:

```bash
# Create a test log
cd /Users/jplfaria/repos/gem-flux-mcp
mkdir -p test_logs
echo "Date,Query,Tool,Success,Notes" > test_logs/claude_code_tests.csv
```

After each test, log results:
```
2025-01-04,What is glucose?,search_compounds,YES,Correctly used tool
2025-01-04,Build media test,build_media,NO,Passed string instead of list
```

### Compare Phase 1 vs Phase 2

Run the same queries with and without Phase 2 guidance, tracking:
- Tool call success rate
- Parameter format correctness
- Workflow completion rate
- Response time

**Target**: Phase 2 should improve from Phase 1 baseline:
- Phase 1: 80% overall success (12/15 tests)
- Phase 2 Target: 85-90% success

---

## Troubleshooting

### MCP Server Won't Start

**Check 1**: Verify Python environment
```bash
cd /Users/jplfaria/repos/gem-flux-mcp
uv run python -c "import gem_flux_mcp; print('OK')"
```

**Check 2**: Check for port conflicts
```bash
lsof -i :8000  # argo-proxy uses this port
```

**Check 3**: Check file permissions
```bash
ls -la /Users/jplfaria/repos/gem-flux-mcp/src/gem_flux_mcp/
```

### Tools Return Errors

**Common Error 1**: "ModuleSEED database not found"
```bash
# Verify database path
ls -la /Users/jplfaria/repos/gem-flux-mcp/data/
```

**Common Error 2**: "Model not found"
```bash
# Check models directory
ls -la /Users/jplfaria/repos/gem-flux-mcp/models/
```

**Common Error 3**: "Media not found"
```bash
# Check media directory
ls -la /Users/jplfaria/repos/gem-flux-mcp/media/
```

### Claude Code Not Recognizing MCP Server

**Solution 1**: Verify config file location
```bash
cat ~/.config/claude-code/mcp_settings.json
```

**Solution 2**: Check Claude Code logs
```bash
# macOS logs location (may vary)
tail -f ~/Library/Logs/claude-code/main.log
```

**Solution 3**: Try absolute paths in config
```json
{
  "mcpServers": {
    "gem-flux": {
      "command": "/Users/jplfaria/repos/gem-flux-mcp/.venv/bin/python",
      "args": [
        "-m",
        "gem_flux_mcp.server"
      ]
    }
  }
}
```

---

## Next Steps

After validating in Claude Code:

1. ✅ **Verify all tools work** in live environment
2. ✅ **Test Phase 2 improvements** on failed Phase 1 tests
3. ✅ **Measure success rates** (target: 85-90%)
4. ✅ **Document any issues** for future improvements
5. ➡️ **Deploy to Claude Desktop** (see CLAUDE_DESKTOP_INTEGRATION.md)

---

## Production Deployment

Once validated in Claude Code, this setup can be deployed to:

1. **Claude Desktop** - For end-user metabolic modeling workflows
2. **CI/CD Pipelines** - Automated testing and validation
3. **Multi-user Environments** - Shared argo-proxy instance

See production deployment checklist in `examples/argo_llm/production_config.py`.

---

## Support and Resources

- **Gem-Flux MCP Docs**: `/Users/jplfaria/repos/gem-flux-mcp/README.md`
- **Argo LLM Research**: `docs/ARGO_LLM_RELIABILITY_RESEARCH.md`
- **Production Config**: `examples/argo_llm/production_config.py`
- **Phase 2 Validation**: `examples/argo_llm/test_phase2_validation.py`

For issues or questions, consult the test results in `ARGO_LLM_RELIABILITY_RESEARCH.md`.
