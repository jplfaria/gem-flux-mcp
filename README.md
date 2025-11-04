# Gem-Flux MCP Server

> A Model Context Protocol (MCP) server for genome-scale metabolic modeling with ModelSEEDpy and COBRApy

[![Tests](https://github.com/jplfaria/gem-flux-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/jplfaria/gem-flux-mcp/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](htmlcov/index.html)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Build, gapfill, and analyze metabolic models through an AI-friendly Model Context Protocol interface.

---

## Features

**Core Modeling Capabilities:**
- **Template-based model building** from protein sequences (GramNegative, GramPositive, Core templates)
- **Two-stage gapfilling** (ATP correction + genome-scale)
- **Flux balance analysis** (FBA) with detailed flux distributions
- **Growth media creation** from ModelSEED compound IDs
- **Session-based storage** (in-memory for MVP v0.1.0)

**Database Integration:**
- **Compound lookup** - Search and retrieve from 33,993 ModelSEED compounds
- **Reaction lookup** - Search and retrieve from 43,775 ModelSEED reactions
- **Metadata enrichment** - Human-readable names, formulas, equations, EC numbers

**Session Management:**
- **List models** - Browse all models in current session
- **List media** - Browse predefined and user-created media
- **Delete models** - Clean up session storage

---

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [MCP Tools](#mcp-tools)
- [Example Workflows](#example-workflows)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

### Prerequisites

- **Python 3.11** (NOT 3.12+) - See [Why Python 3.11?](#why-python-311)
- **UV** package manager - [Installation guide](https://docs.astral.sh/uv/)
- **ModelSEED database files** - See [Database Setup](#database-setup)

### 1. Install Dependencies

```bash
# Clone repository
git clone https://github.com/jplfaria/gem-flux-mcp.git
cd gem-flux-mcp

# Install with UV (creates .venv automatically)
uv sync
```

### 2. Download Database Files

```bash
# Create database directory
mkdir -p data/database

# Download ModelSEED database files (33,993 compounds, 43,775 reactions)
# Option 1: From ModelSEED GitHub
wget -O data/database/compounds.tsv https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compounds.tsv
wget -O data/database/reactions.tsv https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv

# Option 2: Manual download from https://github.com/ModelSEED/ModelSEEDDatabase
```

### 3. Download Template Files

```bash
# Create templates directory
mkdir -p data/templates

# Download ModelSEED templates from ModelSEEDTemplates repository
# GramNegative template (required)
wget -O data/templates/GramNegModelTemplateV6.json https://raw.githubusercontent.com/ModelSEED/ModelSEEDTemplates/main/templates/v6.0/GramNegModelTemplateV6.json

# Core template (required)
wget -O data/templates/Core-V5.2.json https://raw.githubusercontent.com/ModelSEED/ModelSEEDTemplates/main/templates/v6.0/Core-V5.2.json

# Or copy from ModelSEEDpy installation:
# cp .venv/lib/python3.11/site-packages/modelseedpy/templates/*.json data/templates/
```

### 4. Start Server

```bash
# Start MCP server manually:
uv run python -m gem_flux_mcp
```

**Expected output:**
```
Starting Gem-Flux MCP Server...
[INFO] Loading ModelSEED database from ./data/database
[INFO] Loaded 33,993 compounds, 43,775 reactions
[INFO] Loading ModelSEED templates from ./data/templates
[INFO] Loaded 2 templates (GramNegative, Core)
[INFO] Registering MCP tools (11 tools)
[INFO] Server ready - accepting MCP requests
```

---

## Installation

### System Requirements

- **Operating System:** Linux, macOS, or Windows
- **Python:** 3.11.x (3.12+ not supported - see [Why Python 3.11?](#why-python-311))
- **Memory:** 4 GB minimum, 8 GB recommended (for database and template loading)
- **Disk Space:** 2 GB (includes database files and templates)

### Why Python 3.11?

**CRITICAL:** Python 3.12+ removed the `distutils` module, which breaks `scikit-learn 1.2.0`, a dependency of ModelSEEDpy. **You must use Python 3.11.x**.

**Check your Python version:**
```bash
python --version
# Should output: Python 3.11.x
```

**Installing Python 3.11:**
```bash
# macOS (via Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3.11 python3.11-venv

# Windows
# Download from https://www.python.org/downloads/release/python-3118/
```

### Installing UV Package Manager

UV is a fast Python package manager used by this project.

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# Verify installation
uv --version
```

### Database Setup

The ModelSEED database provides compound and reaction metadata.

**Database Files:**
- `data/database/compounds.tsv` (12 MB, 33,993 compounds)
- `data/database/reactions.tsv` (37 MB, 43,775 reactions)

**Source:** https://github.com/ModelSEED/ModelSEEDDatabase

**Download script:**
```bash
#!/bin/bash
# download-database.sh

mkdir -p data/database

echo "Downloading ModelSEED database..."
wget -O data/database/compounds.tsv \
  https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compounds.tsv

wget -O data/database/reactions.tsv \
  https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv

echo "Database files downloaded successfully"
```

### Template Setup

ModelSEED templates define organism-specific reaction sets.

**Required Templates:**
- `GramNegModelTemplateV6.json` (23 MB, 2,138 reactions) - Gram-negative bacteria
- `Core-V5.2.json` (891 KB, 452 reactions) - Core metabolism

**Optional Templates:**
- `GramPosModelTemplateV6.json` - Gram-positive bacteria

Templates are included with ModelSEEDpy. After running `uv sync`, find them at:
```bash
# Find template directory
uv run python -c "import modelseedpy; print(modelseedpy.__file__)"

# Copy templates
cp .venv/lib/python3.11/site-packages/modelseedpy/templates/*.json data/templates/
```

---

## Usage

### Starting the Server

```bash
# Using start script (recommended)
./start-server.sh

# Manual start
uv run python -m gem_flux_mcp.server

# With custom configuration
export GEM_FLUX_HOST=0.0.0.0
export GEM_FLUX_PORT=9090
./start-server.sh
```

### Server Lifecycle

**Startup Sequence:**
1. Load ModelSEED database (compounds, reactions)
2. Load ModelSEED templates (GramNegative, Core, etc.)
3. Load ATP gapfilling media (54 default conditions)
4. Load predefined media library (4 standard media)
5. Initialize session storage (in-memory)
6. Register 11 MCP tools
7. Start server on configured host:port

**Graceful Shutdown:**
- Press `Ctrl+C` to stop server
- Active requests complete (30s timeout)
- Session storage cleared
- Memory freed

### Connecting to Server

The server uses the **Model Context Protocol (MCP)** with JSON-RPC 2.0 transport.

**MCP Protocol Version:** `2025-06-18` (latest stable)

**Capabilities:**
- Tools (11 MCP tools)
- Logging (INFO, WARNING, ERROR)
- Resources (not in MVP)
- Prompts (not in MVP)

**Example MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "call_123",
  "method": "tools/call",
  "params": {
    "name": "build_media",
    "arguments": {
      "compounds": ["cpd00027", "cpd00007", "cpd00001"],
      "default_uptake": 100.0
    }
  }
}
```

### Optional: Argo LLM Integration

Gem-Flux MCP can be used with Large Language Models via Argo Gateway for natural language interaction.

**Important**: `argo-proxy` is **NOT** a Python package dependency. It's a standalone service you install separately if you want LLM integration.

**Gem-Flux MCP works without argo-proxy for:**
- ✅ **Python library usage** - Direct Python API calls (Jupyter notebooks)
- ✅ **MCP server usage** - Integration with MCP clients (StructBioReasoner, other agents)
- ✅ **Direct tool calls** - JSON-RPC requests via MCP protocol

**To enable LLM integration (optional):**

1. Install argo-proxy separately:
```bash
pip install argo-proxy  # In a separate environment, NOT in gem-flux-mcp
```

2. Start argo-proxy:
```bash
argo-proxy  # Starts server on localhost:8000
```

3. Use ArgoMCPClient for natural language interaction:
```python
from gem_flux_mcp.argo_client import ArgoMCPClient

client = ArgoMCPClient()
client.initialize_sync()

# Natural language → Tool calls → Results
response = client.chat("Build a metabolic model for E. coli genome 83333.1")
print(response)
# "I've built a metabolic model with ID 'ecoli_83333.gf'..."
```

**Documentation**: See `docs/ARGO_LLM_RELIABILITY_RESEARCH.md` for comprehensive testing and integration guide.

---

## Integration with StructBioReasoner

Gem-Flux MCP was designed to integrate with [StructBioReasoner](https://github.com/jplfaria/StructBioReasoner), a multi-agent system for protein engineering and computational biology.

**Integration Status**: ✅ **Fully Compatible** - Ready to use

**What StructBioReasoner Provides**:
- Multi-agent system for hypothesis generation
- 10 specialized agents (structural, evolutionary, energetic analysis, etc.)
- Paper2Agent system (converts papers into executable tools)
- Integrated tools: PyMOL, BioPython, OpenMM, AlphaFold, Rosetta, ESM

**How Gem-Flux Extends StructBioReasoner**:
- **Metabolic Modeling Agent**: Build and analyze genome-scale metabolic models
- **Metabolic Pathway Analysis**: Identify essential genes and pathways
- **Growth Predictions**: Test organism growth on different media
- **Flux Analysis**: Analyze metabolic flux distributions

**Integration Guide**: See `docs/STRUCTBIOREASONER_INTEGRATION_GUIDE.md` for complete step-by-step instructions.

**Quick Setup**:
1. Clone StructBioReasoner repository
2. Add Gem-Flux MCP server configuration
3. Create MetabolicModeler agent (optional)
4. Use gem-flux tools from any StructBioReasoner agent

**Example Use Cases**:
- **Protein Engineering + Metabolism**: Predict metabolic impact of enzyme mutations
- **Pathway Analysis**: Identify essential reactions for bioengineering targets
- **Comparative Genomics**: Compare metabolic capabilities across organisms
- **Hypothesis Generation**: Combine structural analysis with metabolic modeling

---

## MCP Tools

### Core Modeling Tools (4)

#### 1. `build_media` - Create Growth Medium

Create a growth medium from ModelSEED compound IDs.

**Input:**
```python
{
  "compounds": ["cpd00027", "cpd00007", "cpd00001", "cpd00009"],  # Required
  "default_uptake": 100.0,  # Optional, default: 100.0 mmol/gDW/h
  "custom_bounds": {  # Optional
    "cpd00027": (-5, 100),  # Limit glucose uptake to 5 mmol/gDW/h
    "cpd00007": (-10, 100)  # Aerobic conditions (10 mmol/gDW/h O2)
  }
}
```

**Output:**
```python
{
  "success": true,
  "media_id": "media_20251029_x1y2z3",
  "compounds": [
    {"id": "cpd00027", "name": "D-Glucose", "bounds": [-5, 100]},
    {"id": "cpd00007", "name": "O2", "bounds": [-10, 100]},
    {"id": "cpd00001", "name": "H2O", "bounds": [-100, 100]},
    {"id": "cpd00009", "name": "Phosphate", "bounds": [-100, 100]}
  ],
  "num_compounds": 4,
  "media_type": "minimal"  # "minimal" (<50 compounds) or "rich" (>=50)
}
```

**Predefined Media Available:**
- `glucose_minimal_aerobic` - Glucose + O2 + minerals
- `glucose_minimal_anaerobic` - Glucose + minerals (no O2)
- `pyruvate_minimal_aerobic` - Pyruvate + O2 + minerals
- `pyruvate_minimal_anaerobic` - Pyruvate + minerals (no O2)

---

#### 2. `build_model` - Build Metabolic Model

Build a genome-scale metabolic model from protein sequences.

**Input (Dict Format):**
```python
{
  "protein_sequences": {  # Option 1: Dict of sequences
    "prot_001": "MKLVINLVGNSGLGKSTFTQRLIN...",
    "prot_002": "MKQHKAMIVALERFRKEKRDAALL..."
  },
  "template": "GramNegative",  # "GramNegative", "GramPositive", "Core"
  "model_name": "E_coli_K12",  # Optional user-provided name
  "annotate_with_rast": false  # Optional, default: false (offline mode)
}
```

**Input (FASTA Format):**
```python
{
  "fasta_file_path": "/path/to/proteins.faa",  # Option 2: FASTA file
  "template": "GramNegative",
  "model_name": "E_coli_K12"
}
```

**Output:**
```python
{
  "success": true,
  "model_id": "E_coli_K12.draft",  # User name + .draft state
  "num_reactions": 856,
  "num_metabolites": 742,
  "num_genes": 150,
  "num_exchange_reactions": 95,
  "template_used": "GramNegative",
  "has_biomass_reaction": true,
  "biomass_reaction_id": "bio1",
  "compartments": ["c0", "e0", "p0"],  # Cytosol, extracellular, periplasm
  "is_draft": true,
  "requires_gapfilling": true
}
```

**Model ID Format:**
- Auto-generated: `model_20251029_143052_a1b2c3.draft`
- User-provided: `E_coli_K12.draft`
- State suffix: `.draft` (ungapfilled), `.gf` (gapfilled), `.draft.gf` (draft→gapfilled)

---

#### 3. `gapfill_model` - Gapfill Model for Growth

Add reactions to enable growth in specified media.

**Input:**
```python
{
  "model_id": "E_coli_K12.draft",  # Model to gapfill
  "media_id": "glucose_minimal_aerobic",  # Target growth medium
  "target_growth_rate": 0.01,  # Optional, default: 0.01 hr⁻¹
  "gapfill_mode": "full"  # "full" (ATP + genome) or "genome" (skip ATP)
}
```

**Output:**
```python
{
  "success": true,
  "model_id": "E_coli_K12.draft.gf",  # New gapfilled model
  "original_model_id": "E_coli_K12.draft",  # Original preserved
  "reactions_added": [
    {
      "id": "rxn05459_c0",
      "name": "fumarate reductase",
      "equation": "Fumarate + NADH => Succinate + NAD",
      "direction": "forward",
      "compartment": "c0"
    }
  ],
  "num_reactions_added": 5,
  "growth_rate_before": 0.0,
  "growth_rate_after": 0.874,
  "gapfilling_successful": true
}
```

**Gapfilling Stages:**
1. **ATP Correction** - Ensure ATP production across 54 test media
2. **Genome-scale** - Add reactions for target media and growth rate

---

#### 4. `run_fba` - Execute Flux Balance Analysis

Predict metabolic fluxes and growth rate.

**Input:**
```python
{
  "model_id": "E_coli_K12.draft.gf",  # Gapfilled model
  "media_id": "glucose_minimal_aerobic",  # Growth medium
  "objective": "bio1",  # Optional, default: biomass reaction
  "maximize": true,  # Optional, default: true (maximize growth)
  "flux_threshold": 1e-6  # Optional, filter small fluxes
}
```

**Output:**
```python
{
  "success": true,
  "objective_value": 0.874,  # Growth rate (hr⁻¹)
  "status": "optimal",  # "optimal", "infeasible", "unbounded"
  "active_reactions": 423,
  "fluxes": {
    "bio1": 0.874,
    "EX_cpd00027_e0": -5.0,  # Glucose uptake
    "EX_cpd00007_e0": -10.234,  # O2 uptake
    "rxn00148_c0": 5.0  # Hexokinase
  },
  "uptake_fluxes": {
    "cpd00027": {"name": "D-Glucose", "flux": -5.0},
    "cpd00007": {"name": "O2", "flux": -10.234}
  },
  "secretion_fluxes": {
    "cpd00011": {"name": "CO2", "flux": 8.456}
  }
}
```

---

### Database Lookup Tools (4)

#### 5. `get_compound_name` - Lookup Compound by ID

Get human-readable information for a ModelSEED compound ID.

**Input:**
```python
{"compound_id": "cpd00027"}
```

**Output:**
```python
{
  "success": true,
  "id": "cpd00027",
  "name": "D-Glucose",
  "abbreviation": "glc__D",
  "formula": "C6H12O6",
  "mass": 180.156,
  "charge": 0,
  "inchikey": "WQZGKKKJIJFFOK-GASJEMHNSA-N",
  "aliases": {
    "KEGG": ["C00031"],
    "BiGG": ["glc__D"],
    "MetaCyc": ["GLC"]
  }
}
```

---

#### 6. `search_compounds` - Search Compounds by Name

Find compounds by name, formula, or abbreviation.

**Input:**
```python
{
  "query": "glucose",  # Search term
  "limit": 10  # Optional, max results (default: 10, max: 100)
}
```

**Output:**
```python
{
  "success": true,
  "query": "glucose",
  "num_results": 15,
  "results": [
    {
      "id": "cpd00027",
      "name": "D-Glucose",
      "formula": "C6H12O6",
      "match_field": "name",
      "match_type": "exact"
    },
    {
      "id": "cpd00221",
      "name": "D-Glucose 6-phosphate",
      "formula": "C6H13O9P",
      "match_field": "name",
      "match_type": "partial"
    }
  ],
  "truncated": true  # More results exist beyond limit
}
```

**Search Priority:**
1. Exact ID match
2. Exact name match
3. Exact abbreviation match
4. Partial name match
5. Formula match
6. Alias match

---

#### 7. `get_reaction_name` - Lookup Reaction by ID

Get human-readable information for a ModelSEED reaction ID.

**Input:**
```python
{"reaction_id": "rxn00148"}
```

**Output:**
```python
{
  "success": true,
  "id": "rxn00148",
  "name": "hexokinase",
  "abbreviation": "HEX1",
  "equation": "D-Glucose + ATP => ADP + H+ + D-Glucose-6-phosphate",
  "equation_with_ids": "(1) cpd00027 + (1) cpd00002 => (1) cpd00008 + (1) cpd00067 + (1) cpd00079",
  "reversibility": "irreversible_forward",
  "direction": ">",
  "ec_numbers": ["2.7.1.1"],
  "pathways": ["Glycolysis", "Central Metabolism"],
  "is_transport": false
}
```

---

#### 8. `search_reactions` - Search Reactions by Name

Find reactions by name, EC number, or pathway.

**Input:**
```python
{
  "query": "hexokinase",  # Search term
  "limit": 10  # Optional, max results (default: 10)
}
```

**Output:**
```python
{
  "success": true,
  "query": "hexokinase",
  "num_results": 3,
  "results": [
    {
      "id": "rxn00148",
      "name": "hexokinase",
      "equation": "D-Glucose + ATP => ADP + H+ + D-Glucose-6-phosphate",
      "ec_numbers": ["2.7.1.1"],
      "match_field": "name",
      "match_type": "exact"
    }
  ]
}
```

**Search Priority:**
1. Exact ID match
2. Exact name match
3. Exact abbreviation match
4. EC number match
5. Partial name match
6. Alias match
7. Pathway match

---

### Session Management Tools (3)

#### 9. `list_models` - List All Models

Browse all models in current session.

**Input:**
```python
{
  "filter_state": "all"  # "all", "draft", "gapfilled"
}
```

**Output:**
```python
{
  "success": true,
  "models": [
    {
      "model_id": "E_coli_K12.draft",
      "name": "E. coli K-12",
      "state": "draft",
      "num_reactions": 856,
      "num_metabolites": 742,
      "template": "GramNegative",
      "created_at": "2025-10-29T14:30:52Z"
    },
    {
      "model_id": "E_coli_K12.draft.gf",
      "name": "E. coli K-12",
      "state": "gapfilled",
      "num_reactions": 861,
      "num_metabolites": 748,
      "template": "GramNegative",
      "created_at": "2025-10-29T14:32:15Z"
    }
  ],
  "total_models": 2,
  "models_by_state": {
    "draft": 1,
    "gapfilled": 1
  }
}
```

---

#### 10. `delete_model` - Delete Model from Session

Remove a model from session storage.

**Input:**
```python
{"model_id": "E_coli_K12.draft"}
```

**Output:**
```python
{
  "success": true,
  "deleted_model_id": "E_coli_K12.draft",
  "message": "Model deleted from session"
}
```

---

#### 11. `list_media` - List All Media

Browse all media in current session.

**Input:**
```python
{}  # No parameters
```

**Output:**
```python
{
  "success": true,
  "media": [
    {
      "media_id": "glucose_minimal_aerobic",
      "name": "Glucose Minimal Aerobic",
      "is_predefined": true,
      "num_compounds": 18,
      "media_type": "minimal",
      "compounds_preview": ["cpd00027", "cpd00007", "cpd00001"]
    },
    {
      "media_id": "media_20251029_x1y2z3",
      "name": "Custom Media",
      "is_predefined": false,
      "num_compounds": 25,
      "media_type": "minimal"
    }
  ],
  "total_media": 2,
  "predefined_media": 1,
  "user_created_media": 1
}
```

---

## Example Workflows

### Complete Workflow: Build → Gapfill → FBA

```python
# Step 1: Create growth medium
media = build_media(
    compounds=["cpd00027", "cpd00007", "cpd00001", "cpd00009", "cpd00011", "cpd00013"],
    custom_bounds={"cpd00027": (-5, 100), "cpd00007": (-10, 100)}
)
# Returns: media_id="glucose_minimal_aerobic"

# Step 2: Build draft model from protein sequences
model = build_model(
    protein_sequences={
        "prot_hexokinase": "MKLVINLVGNSGLGKSTFTQRLINSLQIDEDVRKQLA...",
        "prot_pgk": "MKQHKAMIVALERFRKEKRDAALLNLVRNPVADAGVIH..."
    },
    template="GramNegative",
    model_name="E_coli_K12"
)
# Returns: model_id="E_coli_K12.draft"

# Step 3: Gapfill model for growth in glucose media
gapfilled = gapfill_model(
    model_id="E_coli_K12.draft",
    media_id="glucose_minimal_aerobic",
    target_growth_rate=0.01
)
# Returns: model_id="E_coli_K12.draft.gf", reactions_added=5, growth_rate=0.874

# Step 4: Run FBA to predict fluxes
fba_result = run_fba(
    model_id="E_coli_K12.draft.gf",
    media_id="glucose_minimal_aerobic"
)
# Returns: objective_value=0.874, fluxes={...}, uptake_fluxes={...}

# Step 5: Explore results
glucose = get_compound_name(compound_id="cpd00027")
# Returns: name="D-Glucose", formula="C6H12O6"

hexokinase = get_reaction_name(reaction_id="rxn00148")
# Returns: name="hexokinase", equation="D-Glucose + ATP => ..."
```

### Using Predefined Media

```python
# List available predefined media
media_list = list_media()
# Returns: glucose_minimal_aerobic, glucose_minimal_anaerobic, etc.

# Use predefined media directly
model = build_model(protein_sequences={...}, template="GramNegative")
gapfilled = gapfill_model(model_id=model["model_id"], media_id="glucose_minimal_aerobic")
fba = run_fba(model_id=gapfilled["model_id"], media_id="glucose_minimal_aerobic")
```

### Managing Session Storage

```python
# List all models
models = list_models(filter_state="all")
# Returns: all draft and gapfilled models

# List only draft models
draft_models = list_models(filter_state="draft")

# List only gapfilled models
gapfilled_models = list_models(filter_state="gapfilled")

# Delete unused models
delete_model(model_id="old_model.draft")

# List all media
media = list_media()
```

---

## Configuration

### Environment Variables

Configure server behavior via environment variables:

```bash
# Server binding
export GEM_FLUX_HOST="localhost"  # Default: localhost (0.0.0.0 for remote access)
export GEM_FLUX_PORT="8080"       # Default: 8080

# Resource paths
export GEM_FLUX_DATABASE_DIR="./data/database"    # ModelSEED database location
export GEM_FLUX_TEMPLATE_DIR="./data/templates"   # Template JSON files location

# Logging
export GEM_FLUX_LOG_LEVEL="INFO"            # DEBUG, INFO, WARNING, ERROR
export GEM_FLUX_LOG_FILE="./gem-flux.log"  # Log file path (optional)

# Storage limits (MVP session-based storage)
export GEM_FLUX_MAX_MODELS="100"  # Maximum models in memory
export GEM_FLUX_MAX_MEDIA="50"    # Maximum media in memory
```

### Configuration File (Future)

Configuration files not supported in MVP v0.1.0. Will be added in v0.2.0.

---

## Development

### Project Structure

```
gem-flux-mcp/
├── src/gem_flux_mcp/          # Source code
│   ├── database/              # Database loading and indexing
│   │   ├── loader.py          # Load compounds.tsv and reactions.tsv
│   │   └── index.py           # O(1) lookup indexing
│   ├── templates/             # Template management
│   │   └── loader.py          # Load ModelSEED templates
│   ├── storage/               # Session storage
│   │   ├── models.py          # In-memory model storage
│   │   └── media.py           # In-memory media storage
│   ├── media/                 # Media management
│   │   ├── atp_loader.py      # ATP gapfilling media
│   │   └── predefined_loader.py  # Predefined media library
│   ├── tools/                 # MCP tools
│   │   ├── build_media.py
│   │   ├── build_model.py
│   │   ├── gapfill_model.py
│   │   ├── run_fba.py
│   │   ├── compound_lookup.py
│   │   ├── reaction_lookup.py
│   │   ├── list_models.py
│   │   ├── delete_model.py
│   │   └── list_media.py
│   ├── types.py               # Pydantic models
│   ├── errors.py              # Error handling
│   ├── logging.py             # Logging setup
│   └── server.py              # MCP server (FastMCP)
│
├── tests/                     # Test suite (780+ tests, 90% coverage)
│   ├── unit/                  # Unit tests (32 files)
│   ├── integration/           # Integration tests (6 phases)
│   ├── fixtures/              # Test data
│   └── conftest.py            # Pytest configuration
│
├── data/                      # Data files
│   ├── database/              # ModelSEED database (download separately)
│   │   ├── compounds.tsv
│   │   └── reactions.tsv
│   ├── templates/             # ModelSEED templates (download separately)
│   │   ├── GramNegModelTemplateV6.json
│   │   └── Core-V5.2.json
│   └── media/                 # Predefined media (included)
│       ├── glucose_minimal_aerobic.json
│       ├── glucose_minimal_anaerobic.json
│       ├── pyruvate_minimal_aerobic.json
│       └── pyruvate_minimal_anaerobic.json
│
├── specs/                     # 20 cleanroom specifications
├── docs/                      # Documentation
├── pyproject.toml             # Project configuration
├── start-server.sh            # Server startup script
└── README.md                  # This file
```

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Activate virtual environment
source .venv/bin/activate

# Or use uv run for individual commands
uv run pytest
```

### Code Quality Tools

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/

# Format code
uv run black src/
```

---

## Testing

### Test Suite

**Statistics:**
- **785 tests** total (32 unit test files, 6 integration test phases)
- **90% code coverage** (exceeds 80% requirement)
- **100% pass rate**

### Running Tests

```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run integration tests only
uv run pytest tests/integration/

# Run specific test file
uv run pytest tests/unit/test_build_model.py

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Categories

**Unit Tests (tests/unit/):**
- Database loader and indexer
- Template loader
- Session storage (models, media)
- All 11 MCP tools
- Error handling
- Type validation

**Integration Tests (tests/integration/):**
- Complete workflows (build → gapfill → FBA)
- Database lookup workflows
- Session management
- Error handling and recovery
- Model ID transformations
- Performance benchmarks

### Writing Tests

Follow existing patterns in `tests/unit/` and `tests/integration/`. Use fixtures from `tests/conftest.py`.

**Example unit test:**
```python
def test_build_media_success(mock_database_index):
    """Test successful media creation."""
    result = build_media(
        compounds=["cpd00027", "cpd00007"],
        default_uptake=100.0
    )
    assert result["success"] is True
    assert "media_id" in result
    assert result["num_compounds"] == 2
```

---

## Troubleshooting

### Common Issues

#### 1. Python Version Error

**Symptom:**
```
ModuleNotFoundError: No module named 'distutils'
```

**Solution:**
Use Python 3.11 (not 3.12+). See [Why Python 3.11?](#why-python-311)

---

#### 2. Database Files Not Found

**Symptom:**
```
[ERROR] Database file not found: data/database/compounds.tsv
```

**Solution:**
Download ModelSEED database files:
```bash
mkdir -p data/database
wget -O data/database/compounds.tsv <url>
wget -O data/database/reactions.tsv <url>
```

---

#### 3. Template Files Not Found

**Symptom:**
```
[ERROR] Required template missing: data/templates/GramNegModelTemplateV6.json
```

**Solution:**
Copy templates from ModelSEEDpy installation:
```bash
mkdir -p data/templates
cp .venv/lib/python3.11/site-packages/modelseedpy/templates/*.json data/templates/
```

---

#### 4. Import Error: ModuleSEEDpy

**Symptom:**
```
ModuleNotFoundError: No module named 'modelseedpy'
```

**Solution:**
Ensure you're using Fxe fork:
```bash
uv sync  # Reinstalls from Fxe/ModelSEEDpy@dev
```

---

#### 5. Port Already in Use

**Symptom:**
```
[ERROR] Port 8080 already in use
```

**Solution:**
Change port or kill existing process:
```bash
export GEM_FLUX_PORT=9090
./start-server.sh

# Or kill existing process
lsof -ti:8080 | xargs kill
```

---

#### 6. Model Not Found Error

**Symptom:**
```
ModelNotFoundError: Model 'model_abc.draft' not found
```

**Solution:**
- Check model ID spelling (case-sensitive)
- List available models: `list_models()`
- Remember: Models cleared on server restart (session-based storage)

---

#### 7. Gapfilling Infeasible

**Symptom:**
```
InfeasibilityError: Cannot find reactions to enable growth
```

**Solution:**
- Try richer media (more compounds)
- Lower target_growth_rate (default: 0.01)
- Check model has biomass reaction
- Verify media composition

---

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export GEM_FLUX_LOG_LEVEL=DEBUG
./start-server.sh
```

Debug logs include:
- Database loading details
- Template validation
- Tool execution traces
- FBA solver diagnostics

---

## Documentation

### Available Documentation

**Specifications (specs/):**
- `001-system-overview.md` - Architecture and design
- `002-data-formats.md` - Data structures and IDs
- `003-build-media-tool.md` - Media creation tool spec
- `004-build-model-tool.md` - Model building tool spec
- `005-gapfill-model-tool.md` - Gapfilling tool spec
- `006-run-fba-tool.md` - FBA execution tool spec
- `007-database-integration.md` - Database loading spec
- `008-compound-lookup-tools.md` - Compound lookup spec
- `009-reaction-lookup-tools.md` - Reaction lookup spec
- `010-model-storage.md` - Session storage spec
- `013-error-handling.md` - JSON-RPC error spec
- `014-installation.md` - Installation guide
- `015-mcp-server-setup.md` - Server configuration
- `017-template-management.md` - Template loading
- `018-session-management-tools.md` - Session tools
- `019-predefined-media-library.md` - Media library

**Tool Documentation (docs/tools/):**
- `docs/tools/README.md` - Tool overview and quick reference
- `docs/tools/build_model.md` - Model building tool guide
- `docs/tools/gapfill_model.md` - Gapfilling tool guide
- `docs/tools/run_fba.md` - FBA execution tool guide
- `docs/tools/build_media.md` - Media creation tool guide
- `docs/tools/compound_lookup.md` - Compound lookup tools
- `docs/tools/reaction_lookup.md` - Reaction lookup tools
- `docs/tools/list_models.md` - Model listing tool
- `docs/tools/list_media.md` - Media listing tool
- `docs/tools/delete_model.md` - Model deletion tool

**Development Guides (docs/):**
- `docs/ATP_CORRECTION.md` - ATP correction feature guide
- `docs/TESTING.md` - Testing guide and best practices
- `docs/SESSION_LIFECYCLE.md` - Session management lifecycle
- `.claude/CLAUDE.md` - AI co-scientist guidelines (for development)

### External References

- **ModelSEEDpy:** https://github.com/Fxe/ModelSEEDpy/tree/dev
- **COBRApy:** https://cobrapy.readthedocs.io/
- **ModelSEED Database:** https://github.com/ModelSEED/ModelSEEDDatabase
- **FastMCP:** https://github.com/jlowin/fastmcp
- **UV:** https://docs.astral.sh/uv/
- **MCP Protocol:** https://modelcontextprotocol.io/

---

## Contributing

We welcome contributions! Please follow these guidelines:

### Code Style

- **Python 3.11** syntax and features
- **Type hints** for all functions
- **Docstrings** in Google style
- **Line length:** 100 characters (black formatter)
- **Linting:** ruff (passes `ruff check src/`)
- **Type checking:** mypy (passes `mypy src/`)

### Testing Requirements

- **Write tests first** (test-driven development)
- **Unit tests** for all new functions
- **Integration tests** for workflows
- **Coverage:** Maintain ≥80% code coverage
- **All tests must pass:** `pytest` returns 0 exit code

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Write tests for new functionality
4. Implement feature
5. Ensure all tests pass: `uv run pytest`
6. Ensure coverage: `uv run pytest --cov=src`
7. Run linters: `uv run ruff check src/`
8. Run type checker: `uv run mypy src/`
9. Commit changes: `git commit -m "feat: add my feature"`
10. Push to fork: `git push origin feature/my-feature`
11. Open pull request with description

### Issue Reporting

**Bug Reports:**
- Describe expected vs actual behavior
- Include error messages and stack traces
- Provide minimal reproduction steps
- Specify Python version, OS, UV version

**Feature Requests:**
- Describe use case and motivation
- Reference relevant specifications (if applicable)
- Suggest implementation approach

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Acknowledgments

**Built With:**
- [ModelSEEDpy](https://github.com/Fxe/ModelSEEDpy) - Metabolic model building (Fxe fork)
- [COBRApy](https://github.com/opencobra/cobrapy) - Constraint-based modeling
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework
- [UV](https://github.com/astral-sh/uv) - Fast Python package manager

**Data Sources:**
- [ModelSEED Database](https://github.com/ModelSEED/ModelSEEDDatabase) - Biochemistry database

**Development Methodology:**
- Cleanroom specification (Phase 0)
- Test-driven implementation (Phase 1)
- AI-assisted development (Claude)

---

## Support

- **Issues:** https://github.com/jplfaria/gem-flux-mcp/issues
- **Documentation:** See `/specs/` directory
- **Contact:** Jose P. Faria (jplfaria@anl.gov)

---

## Roadmap

### v0.1.0 (Current - MVP)
- 8 core MCP tools
- Session-based storage
- ModelSEED database integration
- Template-based model building
- Two-stage gapfilling
- FBA execution

### v0.2.0 (Future - Persistence)
- Model import/export (JSON, SBML)
- File-based persistence
- OAuth 2.1 authentication
- Rate limiting
- Audit logging

### v0.3.0 (Future - Advanced Analysis)
- Batch operations (multiple models)
- Knockout analysis
- Constraint modification
- Media optimization

### v0.4.0 (Future - Strain Design)
- Production strain design (OptKnock)
- Pathway analysis
- Flux variability analysis
- Parsimonious FBA

See `specs/016-future-tools-roadmap.md` for complete roadmap (34 additional tools).

---

**Status:** Production-ready MVP v0.1.0
**Last Updated:** October 29, 2025

---
