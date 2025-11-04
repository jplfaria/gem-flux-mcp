# MCP Working Directory & File Management Guide

## Your Question: How Does the LLM Know Where Files Are?

**Short Answer**: The LLM doesn't automatically know! You must either:
1. Provide **absolute paths** in the system prompt
2. Add **file browsing tools** to MCP
3. Use **MCP Resources** (recommended)

---

## Current Implementation

### What We Have Now

**Session-Based Storage** (in memory):
- `build_media` → Creates media, stores in `session.media` dict
- `build_model` → Creates model, stores in `session.models` dict
- `list_media` / `list_models` → Lists what's in session

**File-Based Tools**:
- `build_model(fasta_file_path="/abs/path/to/genome.faa")` → Reads FASTA file
- Models/results are stored in SESSION MEMORY, not files

**Problem**: When you say "build a model for this genome", the LLM needs:
- The full path to the FASTA file
- Where to save outputs (if saving to disk)

---

## Solution 1: System Prompt with Working Directory (Current Approach)

```python
system_prompt = f"""You are a metabolic modeling assistant.

Working directory: {Path.cwd()}
Data directory: {Path.cwd() / 'data'}

When users mention files, assume they are relative to the working directory.

Examples:
- "data/genomes/ecoli.faa" → {Path.cwd()}/data/genomes/ecoli.faa
- "models/mymodel.json" → {Path.cwd()}/models/mymodel.json

Always use absolute paths when calling tools.
"""
```

**Pros**:
- Simple
- Works with current implementation
- LLM can infer full paths

**Cons**:
- LLM must remember to convert relative → absolute paths
- No file browsing capability
- User must know file names

---

## Solution 2: Add MCP Resources (Recommended for Production)

MCP has a built-in **Resources** protocol for this!

```python
@mcp.resource("file://working_dir")
def get_working_directory_listing():
    """List files in working directory."""
    return {
        "files": list(Path.cwd().rglob("*")),
        "cwd": str(Path.cwd())
    }

@mcp.resource("file://{path}")
def read_file_content(path: str):
    """Read file contents."""
    return Path(path).read_text()
```

**Pros**:
- Standard MCP approach
- LLM can browse files
- Works with Claude Desktop, ChatGPT Desktop, etc.

**Cons**:
- More complex to implement
- Need to add resource handlers

---

## Solution 3: Add File Management Tools

```python
@mcp.tool()
def list_directory(path: str = ".") -> dict:
    """List files in a directory.

    Args:
        path: Directory path (default: current directory)

    Returns:
        List of files and directories
    """
    dir_path = Path(path).resolve()
    files = [f.name for f in dir_path.iterdir()]
    return {
        "path": str(dir_path),
        "files": files
    }

@mcp.tool()
def read_fasta_file(file_path: str) -> dict:
    """Read a FASTA file and return protein sequences.

    Args:
        file_path: Path to FASTA file

    Returns:
        Dict with sequences
    """
    from Bio import SeqIO
    sequences = [str(rec.seq) for rec in SeqIO.parse(file_path, "fasta")]
    return {"sequences": sequences, "count": len(sequences)}
```

**Pros**:
- LLM can explore filesystem
- Natural conversation flow
- Easy to implement

**Cons**:
- Adds more tools (payload size concerns)
- Security implications (file access)

---

## For Claude Desktop / ChatGPT Desktop

When using with desktop apps, you want MCP Resources:

### Claude Desktop Config (`~/Library/Application Support/Claude/claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "gem-flux": {
      "command": "uv",
      "args": ["run", "gem-flux-mcp"],
      "env": {
        "WORKING_DIR": "/path/to/your/project"
      }
    }
  }
}
```

### What Happens:
1. User opens Claude Desktop
2. Claude loads your MCP server
3. MCP server exposes:
   - **Tools** (`build_model`, `run_fba`, etc.)
   - **Resources** (`file://working_dir`, `file://{path}`)
4. User says: "Build a model from ecoli.faa"
5. Claude:
   - Calls `file://working_dir` resource → sees available files
   - Finds `ecoli.faa` in the list
   - Calls `build_model(fasta_file_path="/{working_dir}/ecoli.faa")`

---

## Best Practices

### For Development (what we have now)

✅ **DO**:
- Include working directory in system prompt
- Ask users for absolute paths when unclear
- Store session data in memory
- Use `Path.cwd()` / `Path.resolve()` to get absolute paths

❌ **DON'T**:
- Assume relative paths will work
- Hardcode paths in tools
- Store sensitive data in working directory

### For Production (Claude Desktop, etc.)

✅ **DO**:
- Implement MCP Resources for file browsing
- Add file reading tools (`list_directory`, `read_fasta_file`)
- Use environment variables for config
- Document required directory structure

❌ **DON'T**:
- Give unrestricted file access
- Expose system directories
- Store credentials in files

---

## Example Workflows

### Workflow 1: With System Prompt (Current)

```python
# User runs script
uv run python examples/argo_llm/interactive_workflow.py

# Script sets working directory in system prompt
system_prompt = f"Working directory: {Path.cwd()}"

# User types:
"Build a model from data/genomes/ecoli.faa"

# LLM interprets as:
"Build a model from /Users/you/gem-flux-mcp/data/genomes/ecoli.faa"

# LLM calls:
build_model(fasta_file_path="/Users/you/gem-flux-mcp/data/genomes/ecoli.faa")
```

### Workflow 2: With File Browsing Tools (Future)

```python
# User types:
"What genomes are available?"

# LLM calls:
list_directory("data/genomes")
# Returns: ["ecoli.faa", "yeast.faa", "human.faa"]

# User types:
"Build a model from ecoli.faa"

# LLM calls:
read_fasta_file("data/genomes/ecoli.faa")
build_model(protein_sequences=[...])
```

### Workflow 3: With MCP Resources (Claude Desktop)

```python
# User opens Claude Desktop
# Claude auto-loads gem-flux MCP

# User types:
"Show me what genomes I have"

# Claude:
# 1. Reads file://working_dir resource
# 2. Filters for .faa files
# 3. Shows user the list

# User types:
"Build a model from ecoli.faa"

# Claude:
# 1. Resolves full path from resource
# 2. Calls build_model with absolute path
```

---

## Model Outputs: Where Do They Go?

### Current Implementation

**In-Memory Session**:
```python
# Model is stored in session.models dict
model_id = "ecoli_model"
session.models[model_id] = cobra_model

# Access later with:
list_models()  # Shows: ["ecoli_model"]
run_fba(model_id="ecoli_model")
gapfill_model(model_id="ecoli_model")
```

**Saving to Disk**:
```python
# Not implemented yet!
# Would need:
@mcp.tool()
def save_model(model_id: str, output_path: str):
    """Save model to disk."""
    model = session.models[model_id]
    cobra.io.save_json_model(model, output_path)
```

### Recommendations

1. **For Interactive Use**: Keep in-memory (current approach)
2. **For Batch Workflows**: Add `save_model` / `load_model` tools
3. **For Claude Desktop**: Add auto-save with configurable output directory

---

## Summary

| Approach | Best For | Implementation Effort |
|----------|----------|----------------------|
| System prompt with paths | Development, testing | ✅ Easy (done!) |
| File management tools | Interactive workflows | ⚠️ Medium |
| MCP Resources | Production, Desktop apps | 🔴 Complex |

**Current Status**: ✅ Working with system prompt approach

**Next Steps**:
1. Add `list_directory` tool for file browsing
2. Add `save_model` / `load_model` tools for persistence
3. Implement MCP Resources for Claude Desktop integration

---

## Testing the Interactive Workflow

```bash
# Test with different modes
uv run python examples/argo_llm/interactive_workflow.py interactive
uv run python examples/argo_llm/interactive_workflow.py scripted
uv run python examples/argo_llm/interactive_workflow.py test-models

# With different models
uv run python examples/argo_llm/interactive_workflow.py interactive gpt-4.5
uv run python examples/argo_llm/interactive_workflow.py interactive o1-preview
```

Try it out! The working directory is set in the system prompt, so you can say things like:
- "What compounds contain ATP?"
- "Create a glucose minimal media"
- "List available models"
