# Gem-Flux MCP Server: Example Notebooks

This directory contains Jupyter notebooks demonstrating how to use the Gem-Flux MCP Server for metabolic modeling.

## 📚 Notebooks Overview

### 1. Basic Workflow (`01_basic_workflow.ipynb`)

Complete workflow from protein sequences to flux analysis.

**What You'll Learn:**
- How to create growth media
- How to build draft metabolic models
- How to gapfill models for growth
- How to run Flux Balance Analysis (FBA)
- How to interpret FBA results

**Covers:**
- `build_media` tool
- `build_model` tool
- `gapfill_model` tool
- `run_fba` tool

**Duration:** ~15 minutes

---

### 2. Database Lookups (`02_database_lookups.ipynb`)

Search and retrieve compound/reaction information from the ModelSEED database.

**What You'll Learn:**
- How to search for compounds by name or formula
- How to lookup compound details by ID
- How to search for reactions by name, EC number, or pathway
- How to lookup reaction details by ID
- How to use priority-based search

**Covers:**
- `get_compound_name` tool
- `search_compounds` tool
- `get_reaction_name` tool
- `search_reactions` tool

**Duration:** ~10 minutes

---

### 3. Session Management (`03_session_management.ipynb`)

Manage models and media in the server session.

**What You'll Learn:**
- How to list all models in the current session
- How to filter models by state (draft vs gapfilled)
- How to delete models from storage
- How to list media compositions
- How to understand model state transitions

**Covers:**
- `list_models` tool
- `delete_model` tool
- `list_media` tool
- Model ID format and state suffixes
- Predefined media library

**Duration:** ~10 minutes

---

### 4. Error Handling and Recovery (`04_error_handling.ipynb`)

Handle common errors and recover gracefully.

**What You'll Learn:**
- How to handle validation errors (invalid IDs, sequences)
- How to handle not found errors (missing models/media)
- How to handle infeasibility errors (model can't grow)
- How to recover from errors with suggested workflows
- Best practices for error prevention

**Covers:**
- Validation errors
- Not found errors
- Infeasibility errors
- Recovery workflows
- Error prevention techniques

**Duration:** ~15 minutes

---

## 🚀 Getting Started

### Prerequisites

1. **Python 3.11** (CRITICAL - Python 3.12+ not supported)
2. **Gem-Flux MCP Server installed**:
   ```bash
   cd /path/to/gem-flux-mcp
   uv sync
   ```
3. **Jupyter installed**:
   ```bash
   uv pip install jupyter
   # OR
   pip install jupyter
   ```
4. **Database and templates downloaded** (see main README.md)

### IMPORTANT: Running the Notebooks

The notebooks need to import the `gem_flux_mcp` package. You have two options:

#### Option 1: Add Setup Cell (Recommended for Development)

Add this as the **FIRST** cell in each notebook:

```python
# Setup: Add parent directory to Python path
import sys
from pathlib import Path
repo_root = Path.cwd().parent
sys.path.insert(0, str(repo_root))
print(f"✓ Added {repo_root} to Python path")
```

Then run all cells normally.

#### Option 2: Install Package in Editable Mode

From the repository root:

```bash
uv pip install -e .
# OR
pip install -e .
```

Then notebooks will work without the setup cell.

### Quick Start

1. **Navigate to examples directory**:
   ```bash
   cd examples
   uv sync
   ```
3. **Database and templates downloaded**:
   - ModelSEED database in `data/database/`
   - Templates in `data/templates/`

### Running the Notebooks

**Option 1: Jupyter Notebook**
```bash
# Activate virtual environment
source .venv/bin/activate

# Start Jupyter
jupyter notebook examples/
```

**Option 2: JupyterLab**
```bash
# Install JupyterLab if needed
uv pip install jupyterlab

# Activate and start
source .venv/bin/activate
jupyter lab examples/
```

**Option 3: VS Code**
1. Open the `gem-flux-mcp` directory in VS Code
2. Install the Jupyter extension
3. Open any `.ipynb` file
4. Select the `.venv` Python kernel

---

## 📖 Recommended Learning Path

### Beginner Path
1. Start with **01_basic_workflow.ipynb**
   - Understand the complete modeling workflow
   - See all tools in action
2. Move to **02_database_lookups.ipynb**
   - Learn how to find compound/reaction IDs
   - Understand database search
3. Then **03_session_management.ipynb**
   - Learn how to manage models
   - Understand model states
4. Finally **04_error_handling.ipynb**
   - Learn common pitfalls
   - Understand error recovery

### Advanced Path
1. **02_database_lookups.ipynb** - Master database queries
2. **01_basic_workflow.ipynb** - Apply to full workflow
3. **04_error_handling.ipynb** - Handle edge cases
4. **03_session_management.ipynb** - Optimize session usage

### Quick Reference Path
- Need to build a model? → **01_basic_workflow.ipynb**
- Need to find a compound? → **02_database_lookups.ipynb**
- Got an error? → **04_error_handling.ipynb**
- Need to list models? → **03_session_management.ipynb**

---

## 🔑 Key Concepts

### Model ID Format

Models have state suffixes indicating processing history:

```
E_coli_K12.draft         → Draft model (not gapfilled)
E_coli_K12.draft.gf      → Gapfilled model
E_coli_K12.draft.gf.gf   → Re-gapfilled model
```

### Predefined Media

Four media compositions available immediately:
- `glucose_minimal_aerobic` - Glucose + O2 (18 compounds)
- `glucose_minimal_anaerobic` - Glucose, no O2 (17 compounds)
- `pyruvate_minimal_aerobic` - Pyruvate + O2 (18 compounds)
- `pyruvate_minimal_anaerobic` - Pyruvate, no O2 (17 compounds)

### ModelSEED IDs

- **Compounds**: `cpd00027` (D-Glucose), `cpd00007` (O2), etc.
- **Reactions**: `rxn00148` (hexokinase), `rxn00200` (phosphofructokinase), etc.
- **Format**: `cpd` or `rxn` + 5-digit number

---

## 💡 Tips and Tricks

### 1. Use Predefined Media
```python
# ✅ Recommended: Use predefined media
media_id = "glucose_minimal_aerobic"

# ❌ Not recommended for beginners: Build custom media
# (Unless you need specific compounds)
```

### 2. Check Model State
```python
# Always check if model is gapfilled before FBA
if ".gf" in model_id:
    print("Model is gapfilled - ready for FBA")
else:
    print("Model needs gapfilling first")
```

### 3. Search Before Building
```python
# Search for compound first
search_response = search_compounds(
    SearchCompoundsRequest(query="glucose", limit=5)
)

# Then use the correct ID
glucose_id = search_response.results[0].id
```

### 4. List Models Regularly
```python
# See what's in your session
list_response = list_models(ListModelsRequest())
print(f"Total models: {list_response.total_models}")
```

### 5. Handle Errors Gracefully
```python
try:
    fba_response = run_fba(request)
except InfeasibilityError:
    print("Model needs gapfilling - running gapfill_model...")
    gapfill_response = gapfill_model(gapfill_request)
```

---

## 🐛 Troubleshooting

### Notebook Won't Start

**Problem**: `jupyter: command not found`

**Solution**:
```bash
# Install Jupyter in the virtual environment
source .venv/bin/activate
uv pip install jupyter
```

---

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'gem_flux_mcp'`

**Solution**:
```bash
# Ensure you're in the correct directory
cd /path/to/gem-flux-mcp

# Activate the virtual environment
source .venv/bin/activate

# Install the package in editable mode
uv pip install -e .
```

---

### Database Not Found

**Problem**: `DatabaseError: File not found: data/database/compounds.tsv`

**Solution**:
1. Download the ModelSEED database files
2. Place them in the correct directory:
   ```
   data/database/compounds.tsv
   data/database/reactions.tsv
   ```
3. See main README.md for download instructions

---

### ModelSEEDpy Errors

**Problem**: `ImportError: cannot import name 'MSBuilder'`

**Solution**:
```bash
# Ensure you have the Fxe/dev fork installed
uv pip uninstall ModelSEEDpy
uv pip install git+https://github.com/Fxe/ModelSEEDpy.git@dev
```

---

### Python Version Error

**Problem**: `ModuleNotFoundError: No module named 'distutils'`

**Solution**:
- **CRITICAL**: You must use Python 3.11 (NOT 3.12+)
- Python 3.12+ removed the `distutils` module
- ModelSEEDpy's dependency (scikit-learn 1.2.0) requires it

```bash
# Check Python version
python --version  # Should be 3.11.x

# If wrong version, install Python 3.11 and recreate venv
pyenv install 3.11.0
pyenv local 3.11.0
rm -rf .venv
uv sync
```

---

## 📊 Example Data

The notebooks use example data that's small enough to run quickly:

### Protein Sequences
```python
protein_sequences = {
    "hexokinase": "MKLVINLVGNSGLGKSTFTQRLIN...",
    "pgk": "MKQHKAMIVALERFRKEKRDAALL...",
    # ... (5 proteins total)
}
```

### Media Compositions
- **Minimal media**: 17-18 compounds
- **Rich media**: 50+ compounds (future examples)

### Expected Results
- **Draft model**: ~850-1500 reactions
- **Gapfilled model**: +5-50 reactions added
- **Growth rate**: 0.1-1.0 hr⁻¹ (E. coli in glucose aerobic)

---

## 🔗 Additional Resources

### Documentation
- [Main README.md](../README.md) - Installation and overview
- [CLAUDE.md](../CLAUDE.md) - Implementation guidelines
- [Session Lifecycle](../docs/SESSION_LIFECYCLE.md) - Detailed session management

### Specifications
All specifications are in the `specs/` directory:
- `001-system-overview.md` - System architecture
- `002-data-formats.md` - Data structures and formats
- `003-build-media-tool.md` - Media creation
- `004-build-model-tool.md` - Model building
- `005-gapfill-model-tool.md` - Gapfilling
- `006-run-fba-tool.md` - Flux balance analysis

### External Resources
- [ModelSEEDpy Documentation](https://github.com/Fxe/ModelSEEDpy/tree/dev)
- [COBRApy Documentation](https://cobrapy.readthedocs.io/)
- [ModelSEED Database](https://github.com/ModelSEED/ModelSEEDDatabase)

---

## 🤝 Contributing

Found an issue or want to add an example notebook?

1. **Report Issues**: [GitHub Issues](https://github.com/user/gem-flux-mcp/issues)
2. **Suggest Examples**: Open an issue with `[Example]` prefix
3. **Submit Notebooks**: Pull requests welcome!

### Example Notebook Template

```python
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Title\n",
    "Brief description\n",
    "## Prerequisites\n",
    "## Setup"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Imports"
   ]
  }
 ]
}
```

---

## 📝 License

These example notebooks are provided under the same license as the main Gem-Flux MCP Server project.

---

## ✨ Notebook Status

| Notebook | Status | Last Updated | Coverage |
|----------|--------|--------------|----------|
| 01_basic_workflow.ipynb | ✅ Complete | 2025-10-29 | All core tools |
| 02_database_lookups.ipynb | ✅ Complete | 2025-10-29 | All database tools |
| 03_session_management.ipynb | ✅ Complete | 2025-10-29 | All session tools |
| 04_error_handling.ipynb | ✅ Complete | 2025-10-29 | All error types |

---

**Happy Modeling!** 🧬🔬
