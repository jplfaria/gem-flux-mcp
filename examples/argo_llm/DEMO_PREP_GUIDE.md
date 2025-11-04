# Demo Preparation Guide

## Pre-Demo Checklist

### 1. Environment Setup
```bash
# Ensure VPN is connected to ANL
# Start argo-proxy (should already be running)
argo-proxy

# Verify ModelSEED database is present
ls -la data/database/
# Should see: compounds.tsv, reactions.tsv, templates/*.json
```

### 2. Run Comprehensive Tests
```bash
# Test ALL tools individually + workflows (recommended before demo!)
uv run python examples/argo_llm/test_all_tools_comprehensive.py

# Test with GPT-5 (reasoning model)
uv run python examples/argo_llm/test_all_tools_comprehensive.py gpt-5

# Test with Claude Sonnet 4
uv run python examples/argo_llm/test_all_tools_comprehensive.py claude-sonnet-4
```

**Expected output**: 80%+ success rate across all tests

### 3. Quick Model Comparison Test
```bash
# Verify all 3 models work
uv run python examples/argo_llm/interactive_workflow.py test-models
```

**Expected output**: All 3 models (gpt-4o, gpt-5, claude-sonnet-4) return glucose formula

## Demo Scripts

### Script 1: Simple Database Queries (2 min)
```bash
uv run python examples/argo_llm/interactive_workflow.py interactive gpt-4o
```

**What to say**:
> "This is our Gem-Flux MCP running through Argo. Let me show you natural language queries against the ModelSEED database."

**Commands to run**:
```
You: What is the molecular formula of glucose (cpd00027)?
You: Find compounds with ATP in their name
You: What reactions involve glucose?
```

### Script 2: Media Creation Workflow (3 min)
**What to say**:
> "Now let's create growth media using natural language. The LLM will call our build_media tool."

**Commands to run**:
```
You: Create a minimal media called 'demo_media' with glucose, water, oxygen, phosphate, and ammonia
You: What media have we created?
You: List all the compounds in demo_media
```

### Script 3: Model Building Pipeline (5 min)
**What to say**:
> "Here's the complete pipeline: build a model, gapfill it, and run FBA - all with natural language."

**Commands to run**:
```
You: Build a model called 'demo_ecoli' from these sequences: MKLAVLGAAGIGSTVAYGAANQALKLGDRVAIEPTDTVLGQALLKREGADVAQVSTGAG

You: Gapfill demo_ecoli on demo_media

You: Run FBA on demo_ecoli with demo_media and tell me the growth rate
```

### Script 4: Model Comparison with GPT-5 (3 min)
**What to say**:
> "Let's switch to GPT-5, the reasoning model, and compare results."

```bash
# Switch model
uv run python examples/argo_llm/interactive_workflow.py interactive gpt-5
```

**Commands to run**:
```
You: What is the difference between aerobic and anaerobic respiration?
You: Build a model for anaerobic growth and gapfill it
```

## Demo Tips

### Do's ✓
- **Start simple**: Database queries first, then workflows
- **Explain what's happening**: "The LLM is calling the get_compound_name tool..."
- **Show errors gracefully**: If something fails, explain it's research code
- **Highlight multi-model support**: Switch between gpt-4o, gpt-5, claude-sonnet-4
- **Emphasize natural language**: "No code needed, just describe what you want"

### Don'ts ✗
- **Don't rush**: Let the LLM think (it takes 2-5 seconds per call)
- **Don't use complex workflows first**: Build up complexity gradually
- **Don't panic if tool call fails**: LLM will usually retry or explain the error
- **Don't skip the setup**: Make sure argo-proxy is running!

## Troubleshooting

### Issue: "Connection refused" error
```bash
# Check argo-proxy is running
ps aux | grep argo-proxy

# Restart if needed
argo-proxy
```

### Issue: "ModelSEED database not found"
```bash
# Verify database files
ls -la data/database/

# Re-download if missing (see main README)
```

### Issue: Tool call failures
- **Cause**: LLM sometimes sends wrong parameter types
- **Fix**: Rephrase the query more explicitly
- **Example**: Instead of "Create media with glucose", say "Create media with glucose (cpd00027) at 10 mmol/gDW/hr"

### Issue: Slow responses
- **Cause**: GPT-5 and Claude are slower than GPT-4o
- **Fix**: Use gpt-4o for quick demos
- **Note**: This is expected for reasoning models

## After Demo Questions

**Q: Can this run in Claude Desktop?**
A: Yes! We have a guide in `docs/MCP_WORKING_DIRECTORY_GUIDE.md` for adding MCP Resources.

**Q: Does it work with other LLMs?**
A: Yes! Through Argo we support GPT-4o, GPT-5, Claude Sonnet 4, and others. Easy to add more models.

**Q: How does it know where files are?**
A: Currently through system prompt with `Path.cwd()`. For production, we'd add MCP Resources. See the guide.

**Q: Can it handle real genome-scale models?**
A: Yes! The small demo sequences are just for speed. It works with full FASTA files.

**Q: What's the BioScrounger integration plan?**
A: This MCP will be accessible through BioScrounger's Claude Code interface. Users can build models with natural language through the scrounger platform.

## Quick Reference

### All Tools Available (11 total)
1. `get_compound_name` - Look up compound by ID
2. `search_compounds` - Search compounds by name
3. `get_reaction_name` - Look up reaction by ID
4. `search_reactions` - Search reactions by name
5. `build_media` - Create growth media
6. `list_media` - List session media
7. `build_model` - Build model from sequences
8. `list_models` - List session models
9. `delete_model` - Delete a model
10. `gapfill_model` - Gapfill for growth
11. `run_fba` - Run flux balance analysis

### Available Models
- `gpt-4o`: Fast, good for most tasks
- `gpt-5`: Reasoning model (slower, more thoughtful)
- `claude-sonnet-4`: Anthropic's latest

### File Locations
- **Interactive script**: `examples/argo_llm/interactive_workflow.py`
- **Test script**: `examples/argo_llm/test_all_tools_comprehensive.py`
- **Documentation**: `docs/ARGO_LLM_INTEGRATION_SUMMARY.md`
- **Working dir guide**: `docs/MCP_WORKING_DIRECTORY_GUIDE.md`

## Post-Demo Follow-Up

After successful demo:
1. Share the `ARGO_LLM_INTEGRATION_SUMMARY.md` document
2. Offer to walk through the code architecture
3. Discuss production deployment (MCP Resources, Claude Desktop integration)
4. Plan next steps for BioScrounger integration
