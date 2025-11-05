# Remaining Tools Test Plan

**Status**: 5/11 tools tested, 6 remaining
**Next Step**: Test these 6 tools via MCP protocol

---

## Already Tested ✅

1. ✅ **build_media** - Works, creates media with compounds
2. ✅ **search_compounds** - Works, finds compounds by query
3. ✅ **build_model** - Works, now with RAST enabled
4. ✅ **gapfill_model** - Works, now with pathway summary
5. ✅ **list_media** - Works, shows 4 predefined media

---

## Remaining to Test

### 6. run_fba
**Purpose**: Run flux balance analysis on gapfilled model
**Test Case**:
```
mcp__gem-flux__run_fba(
    model_id="ecoli_test.draft.gf",
    media_id="glucose_minimal_aerobic"
)
```
**Expected**: Growth rate > 0, flux distributions
**Check**: Output has interpretation of results

---

### 7. get_compound_name
**Purpose**: Look up compound details by ID
**Test Case**:
```
mcp__gem-flux__get_compound_name(
    compound_id="cpd00027"
)
```
**Expected**: Returns "D-Glucose" with formula, mass
**Check**: Output is helpful for LLM understanding

---

### 8. get_reaction_name
**Purpose**: Look up reaction details by ID
**Test Case**:
```
mcp__gem-flux__get_reaction_name(
    reaction_id="rxn00148"
)
```
**Expected**: Returns reaction name, equation, EC number
**Check**: Output includes biological context

---

### 9. search_reactions
**Purpose**: Search reactions by keyword
**Test Case**:
```
mcp__gem-flux__search_reactions(
    query="hexokinase",
    limit=10
)
```
**Expected**: List of matching reactions with relevance
**Check**: Results are actionable

---

### 10. list_models
**Purpose**: List all models in session
**Test Case**:
```
mcp__gem-flux__list_models()
```
**Expected**: Shows draft and gapfilled models
**Check**: Can filter by state (draft/gapfilled)

---

### 11. delete_model
**Purpose**: Remove model from session
**Test Case**:
```
mcp__gem-flux__delete_model(
    model_id="ecoli_test.draft"
)
```
**Expected**: Confirms deletion
**Check**: Error handling if model doesn't exist

---

## Testing Approach

For each tool:
1. **Call via MCP** (not Python directly)
2. **Check success/failure**
3. **Review output quality**:
   - Is it helpful for an LLM?
   - Does it guide next steps?
   - Is error handling clear?
4. **Note improvements needed** for Phase 2

---

## What to Look For

### Good Signs ✅
- Clear, structured output
- Helpful field names
- Biological context where relevant
- Guidance on next steps

### Issues to Fix in Phase 2 ❌
- Missing `next_steps` field
- No `interpretation` of results
- Unclear error messages
- Too much or too little information

---

## Quick Test Script

When MCP server is connected:

```python
# Test all 6 remaining tools
tests = [
    ("run_fba", {"model_id": "model.gf", "media_id": "glucose_minimal_aerobic"}),
    ("get_compound_name", {"compound_id": "cpd00027"}),
    ("get_reaction_name", {"reaction_id": "rxn00148"}),
    ("search_reactions", {"query": "hexokinase", "limit": 5}),
    ("list_models", {}),
    ("delete_model", {"model_id": "test_model.draft"}),
]

for tool_name, params in tests:
    print(f"\n{'='*60}")
    print(f"Testing: {tool_name}")
    print(f"Params: {params}")

    result = call_mcp_tool(tool_name, params)

    # Check output
    if result.get("success"):
        print("✅ SUCCESS")
        print(f"Output: {summarize(result)}")
    else:
        print("❌ FAILED")
        print(f"Error: {result.get('error')}")

    # Note observations
    print("\nObservations:")
    print("- Has next_steps?", "next_steps" in result)
    print("- Has interpretation?", "interpretation" in result)
    print("- Clear output?", is_clear(result))
```

---

## Expected Timeline

- **Tool testing**: 10-15 minutes (2-3 min per tool)
- **Documentation**: 5 minutes
- **Total**: ~20 minutes

---

## After Testing

Create summary document:
- `reports/all_tools_tested.md`
- List any issues found
- Prioritize Phase 2 improvements
- Ready to move forward

---

## Notes

- Server reconnection was slow during this session
- May need to restart Claude Code for stable MCP connection
- All tests should be via MCP protocol (the honest way)
- Document any surprises or issues for Phase 2
