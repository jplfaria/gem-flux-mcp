# Claude Desktop Integration Guide

**End-User Deployment for Gem-Flux MCP**

This guide shows how to integrate the Gem-Flux MCP server with Claude Desktop for end-user metabolic modeling workflows.

---

## Prerequisites

1. **Claude Desktop installed** (macOS, Windows, or Linux)
2. **argo-proxy running** at `http://localhost:8000/v1` (optional for Argo LLM features)
3. **Gem-Flux MCP repository** cloned (or installed via pip)
4. **Python 3.11+** with uv package manager

---

## Installation Methods

### Method 1: From Source (Development/Testing)

Use this method if you're developing or testing the MCP server.

#### 1. Clone Repository

```bash
git clone https://github.com/your-org/gem-flux-mcp.git
cd gem-flux-mcp
```

#### 2. Install Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

#### 3. Configure Claude Desktop

**macOS**: Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: Edit `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: Edit `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gem-flux": {
      "command": "uv",
      "args": [
        "--directory",
        "/FULL/PATH/TO/gem-flux-mcp",
        "run",
        "python",
        "-m",
        "gem_flux_mcp"
      ],
      "env": {
        "PYTHONPATH": "/FULL/PATH/TO/gem-flux-mcp/src"
      }
    }
  }
}
```

**Important**: Replace `/FULL/PATH/TO/gem-flux-mcp` with the absolute path to your cloned repository.

#### 4. Restart Claude Desktop

Quit Claude Desktop completely and reopen to load the MCP server.

---

### Method 2: System-Wide Installation (End Users)

Use this method for stable deployments to end users.

#### 1. Install via pip (when published)

```bash
pip install gem-flux-mcp
```

#### 2. Configure Claude Desktop

**macOS**: Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: Edit `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: Edit `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gem-flux": {
      "command": "python",
      "args": [
        "-m",
        "gem_flux_mcp"
      ]
    }
  }
}
```

#### 3. Restart Claude Desktop

Quit and reopen Claude Desktop.

---

## Verification

### Step 1: Check MCP Server Status

Open Claude Desktop and start a new conversation. Ask:

```
What MCP tools are available?
```

You should see 11 Gem-Flux tools:
- `build_media` - Create growth media compositions
- `build_model` - Build metabolic models from protein sequences
- `gapfill_model` - Add reactions to enable growth
- `run_fba` - Run flux balance analysis
- `get_compound_name` - Look up compound details
- `search_compounds` - Search compound database
- `get_reaction_name` - Look up reaction details
- `search_reactions` - Search reaction database
- `list_models` - List models in session
- `delete_model` - Remove model from session
- `list_media` - List media in session

### Step 2: Test Basic Tool

```
What is the ModelSEED ID for glucose?
```

**Expected**: Claude uses `search_compounds` and returns compound IDs like cpd00027.

### Step 3: Test Media Creation

```
Create a minimal media with glucose, water, phosphate, oxygen, and ammonia
```

**Expected**: Claude uses `search_compounds` to find IDs, then `build_media` to create the media.

---

## Example Workflows

### Workflow 1: Compound Lookup

**User Request**:
```
What is glucose in the ModelSEED database?
```

**Expected Claude Behavior**:
1. Use `search_compounds` with query "glucose"
2. Return cpd00027 (D-Glucose) with formula C6H12O6

---

### Workflow 2: Building Growth Media

**User Request**:
```
Create an aerobic glucose minimal media
```

**Expected Claude Behavior**:
1. Search for compounds: glucose, water, O2, phosphate, ammonia
2. Use `build_media` with compound IDs
3. Report media ID and composition

**Example**:
```
I've created an aerobic glucose minimal media with:
- cpd00027: D-Glucose (carbon source)
- cpd00007: O2 (electron acceptor)
- cpd00001: H2O
- cpd00009: Phosphate
- cpd00013: NH3 (nitrogen source)

Media ID: media_20251104_123456_abc123
```

---

### Workflow 3: Model Building from Genome

**User Request**:
```
Build a metabolic model from this E. coli protein FASTA file: ecoli_proteins.fasta
```

**Expected Claude Behavior**:
1. Read the FASTA file
2. Use `build_model` with protein sequences
3. Report model statistics

**Example**:
```
Model built successfully!

Model ID: E_coli_K12.draft
Reactions: 856
Metabolites: 742
Genes: 1,247
Template: GramNegative

Note: This is a draft model. Use gapfill_model to enable growth.
```

---

### Workflow 4: Complete Modeling Pipeline

**User Request**:
```
Build an E. coli model, gapfill it for aerobic glucose growth, and predict the growth rate
```

**Expected Claude Behavior**:
1. Build model from protein sequences
2. Create or use predefined glucose minimal aerobic media
3. Gapfill model on that media
4. Run FBA to predict growth rate

**Example**:
```
Complete metabolic modeling pipeline executed:

1. Model: E_coli_K12.draft.gf (892 reactions after gapfilling)
2. Media: glucose_minimal_aerobic (18 compounds)
3. Predicted growth rate: 0.874 hr⁻¹

Key metabolic fluxes:
- Glucose uptake: 5.0 mmol/gDW/h
- O2 uptake: 10.2 mmol/gDW/h
- CO2 secretion: 8.5 mmol/gDW/h
```

---

## Usage Tips for End Users

### Tip 1: Be Specific with Compound Names

**Good**: "Create media with D-glucose"
**Better**: "Create media with cpd00027"

**Why**: Specific names or IDs reduce ambiguity.

### Tip 2: Use Predefined Media When Possible

Available predefined media:
- `glucose_minimal_aerobic` - Glucose + O2 (18 compounds)
- `glucose_minimal_anaerobic` - Glucose without O2 (17 compounds)
- `pyruvate_minimal_aerobic` - Pyruvate + O2 (18 compounds)
- `pyruvate_minimal_anaerobic` - Pyruvate without O2 (17 compounds)

**Example**:
```
Gapfill my model on glucose_minimal_aerobic media
```

### Tip 3: Provide FASTA Files for Model Building

Claude Desktop can read files from your system.

**Example**:
```
Build a model from proteins in ~/Desktop/my_genome.fasta using the GramNegative template
```

### Tip 4: Ask for Explanations

Claude can explain results:

```
Why is my predicted growth rate so low?
```

```
What reactions were added during gapfilling and why?
```

---

## Troubleshooting

### Issue 1: Tools Not Available

**Symptom**: Claude says "I don't have access to metabolic modeling tools"

**Solution**:
1. Check `claude_desktop_config.json` path is correct
2. Verify JSON syntax is valid (use JSONLint.com)
3. Restart Claude Desktop completely (Quit, not just close window)
4. Check MCP server can start manually:
   ```bash
   cd /path/to/gem-flux-mcp
   uv run python -m gem_flux_mcp
   ```

### Issue 2: Server Fails to Start

**Symptom**: Tools appear unavailable or error messages in Claude

**Common Causes**:

**Missing Dependencies**:
```bash
cd /path/to/gem-flux-mcp
uv sync
```

**Wrong Python Version**:
```bash
python --version  # Should be 3.11 or 3.12
```

**Database Files Missing**:
```bash
ls data/database/
# Should see: compounds.tsv, reactions.tsv
```

If missing, download from ModelSEED:
```bash
cd data/database
curl -O https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compounds.tsv
curl -O https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv
```

### Issue 3: Tool Returns Errors

**Symptom**: Tool executes but returns error message

**Debug Steps**:

1. Check exact error in Claude's response
2. Test tool directly in Python:
   ```python
   from gem_flux_mcp.server import initialize_server
   initialize_server()

   from gem_flux_mcp.tools.compound_lookup import search_compounds
   result = search_compounds("glucose", limit=5)
   print(result)
   ```

3. Check logs (if configured):
   ```bash
   tail -f /path/to/gem-flux-mcp/logs/server.log
   ```

### Issue 4: Wrong Parameter Formats

**Symptom**: Claude passes incorrect data types

**Solution**: Be explicit in your request:

**Vague**:
```
Build media with glucose
```

**Explicit**:
```
Build media with compound ID cpd00027 (glucose)
```

---

## Configuration Options

### Environment Variables

You can customize MCP server behavior via environment variables in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gem-flux": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/gem-flux-mcp",
        "run",
        "python",
        "-m",
        "gem_flux_mcp"
      ],
      "env": {
        "PYTHONPATH": "/path/to/gem-flux-mcp/src",
        "GEM_FLUX_DATABASE_DIR": "/path/to/custom/database",
        "GEM_FLUX_TEMPLATE_DIR": "/path/to/custom/templates",
        "GEM_FLUX_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

**Available Variables**:
- `GEM_FLUX_DATABASE_DIR` - Custom ModelSEED database location
- `GEM_FLUX_TEMPLATE_DIR` - Custom template location
- `GEM_FLUX_MAX_MODELS` - Max models in session (default: 100)
- `GEM_FLUX_LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)

---

## Advanced: Multi-User Deployment

For organizations deploying to multiple users:

### 1. Shared Installation

Install gem-flux-mcp to a shared location:

```bash
# Install to /opt/gem-flux-mcp
sudo mkdir -p /opt/gem-flux-mcp
sudo git clone https://github.com/your-org/gem-flux-mcp.git /opt/gem-flux-mcp
cd /opt/gem-flux-mcp
sudo uv sync
```

### 2. User Configuration Template

Provide users with this config template:

```json
{
  "mcpServers": {
    "gem-flux": {
      "command": "uv",
      "args": [
        "--directory",
        "/opt/gem-flux-mcp",
        "run",
        "python",
        "-m",
        "gem_flux_mcp"
      ],
      "env": {
        "PYTHONPATH": "/opt/gem-flux-mcp/src",
        "GEM_FLUX_DATABASE_DIR": "/opt/gem-flux-mcp/data/database",
        "GEM_FLUX_TEMPLATE_DIR": "/opt/gem-flux-mcp/data/templates"
      }
    }
  }
}
```

### 3. Update Management

Create an update script:

```bash
#!/bin/bash
# update_gem_flux.sh

cd /opt/gem-flux-mcp
sudo git pull
sudo uv sync

echo "Gem-Flux MCP updated. Users should restart Claude Desktop."
```

---

## Argo LLM Integration (Optional)

If you want to use Argo Gateway for multi-model support:

### 1. Start argo-proxy

```bash
cd /path/to/gem-flux-mcp
argo-proxy -c argo-config.yaml
```

### 2. Verify Argo Connection

The MCP server will automatically detect argo-proxy on localhost:8000.

### 3. Use Argo Models

Argo features are used internally by the MCP server for LLM-powered analysis (future feature).

---

## Performance Considerations

### Model Building

**Typical Times**:
- Small genome (100 proteins): ~5 seconds
- Medium genome (1,000 proteins): ~30 seconds
- Large genome (5,000+ proteins): 2-5 minutes

### Gapfilling

**Typical Times**:
- Minimal media: 30 seconds - 2 minutes
- Rich media: 1-5 minutes
- Complex organisms: 5-15 minutes

**Tip**: For large models, tell Claude:
```
This may take a few minutes. Proceed with gapfilling.
```

### FBA

**Typical Times**:
- Standard FBA: < 1 second
- Large models: 1-5 seconds

---

## Best Practices

### 1. Start Simple

Begin with basic queries before complex workflows:

```
# Start here
What is glucose?

# Then move to
Create a glucose minimal media

# Finally
Build and gapfill an E. coli model
```

### 2. Save Important Models

Models are stored in session only (lost when Claude Desktop closes). Save important results:

```
After building the model, save the model file to ~/Desktop/my_model.json
```

### 3. Use Descriptive Names

```
# Good
Build a model named "ecoli_K12_MG1655"

# Better than
Build a model named "model1"
```

### 4. Ask for Summaries

```
Summarize the gapfilling results in a table showing:
- Reactions added
- Pathways affected
- Growth rate before vs after
```

---

## Limitations and Known Issues

### Current Limitations

1. **Session-scoped storage**: Models/media lost when Claude Desktop closes
2. **No visualization**: FBA results are text-only (future: network visualization)
3. **Single-user**: No concurrent multi-user support yet
4. **Memory limits**: Very large models (>10,000 reactions) may be slow

### Planned Features

- [ ] Persistent model storage (save/load)
- [ ] Network visualization for flux analysis
- [ ] Batch processing multiple models
- [ ] Export to SBML format
- [ ] Integration with BiGG Models database

---

## Support and Resources

### Documentation

- **User Guide**: `/path/to/gem-flux-mcp/README.md`
- **Tool Specifications**: `/path/to/gem-flux-mcp/specs/`
- **Example Notebooks**: `/path/to/gem-flux-mcp/examples/notebooks/`

### Research and Testing

- **Argo LLM Research**: `docs/ARGO_LLM_RELIABILITY_RESEARCH.md`
- **Production Config**: `examples/argo_llm/production_config.py`
- **Test Scripts**: `examples/argo_llm/test_*.py`

### Getting Help

1. Check this guide's Troubleshooting section
2. Review example workflows above
3. Test tools in isolation first
4. Consult tool specifications in `specs/` directory

---

## Comparison: Claude Code vs Claude Desktop

| Feature | Claude Code | Claude Desktop |
|---------|-------------|----------------|
| **Use Case** | Development, debugging | End-user workflows |
| **File Access** | Full read/write | User directories only |
| **Configuration** | Project-specific | Global config |
| **Debugging** | Live logs, inspection | Limited visibility |
| **Target Users** | Developers | Scientists, analysts |
| **Best For** | Testing, validation | Production workflows |

**Recommendation**:
- Use **Claude Code** for testing and debugging the MCP server
- Use **Claude Desktop** for day-to-day metabolic modeling work

---

## Next Steps

After successful deployment:

1. ✅ Verify all tools work correctly
2. ✅ Test common workflows (media, models, FBA)
3. ✅ Train users on basic usage patterns
4. ✅ Collect feedback on tool usage and pain points
5. ➡️ Iterate on tools based on real-world usage

---

## Production Checklist

Before deploying to end users:

- [ ] All dependencies installed
- [ ] Database files downloaded and verified
- [ ] Templates available (GramNegative, GramPositive, Core)
- [ ] MCP server starts without errors
- [ ] All 11 tools accessible in Claude Desktop
- [ ] Basic workflows tested (search, build, gapfill, FBA)
- [ ] User documentation provided
- [ ] Update process documented

---

## Version Information

**Gem-Flux MCP Version**: 0.1.0 (MVP)
**Tested with**: Claude Desktop 1.x
**Python Requirements**: 3.11, 3.12
**Last Updated**: 2025-11-04

---

For issues or questions about Claude Code integration, see `CLAUDE_CODE_INTEGRATION.md`.
