# Gem-Flux MCP Server

> A Model Context Protocol (MCP) server for genome-scale metabolic modeling with ModelSEEDpy and COBRApy

[![Tests](https://github.com/jplfaria/gem-flux-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/jplfaria/gem-flux-mcp/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](htmlcov/index.html)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Build, gapfill, and analyze metabolic models through an AI-friendly Model Context Protocol interface.

---

## Quick Start

### Prerequisites

- **Python 3.11** (NOT 3.12+) - Python 3.12+ breaks scikit-learn dependency
- **UV** package manager - [Installation guide](https://docs.astral.sh/uv/)
- **ModelSEED database files** - Download instructions below

### 1. Install

```bash
git clone https://github.com/jplfaria/gem-flux-mcp.git
cd gem-flux-mcp
uv sync
```

### 2. Download Database Files

```bash
mkdir -p data/database data/templates

# ModelSEED database (33,993 compounds, 43,775 reactions)
wget -O data/database/compounds.tsv https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compounds.tsv
wget -O data/database/reactions.tsv https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv

# Templates (from ModelSEEDpy installation)
cp .venv/lib/python3.11/site-packages/modelseedpy/templates/*.json data/templates/
```

### 3. Start Server

```bash
./start-server.sh
```

**Expected output:**
```
[INFO] Loading ModelSEED database from ./data/database
[INFO] Loaded 33,993 compounds, 43,775 reactions
[INFO] Server ready - accepting MCP requests
```

---

## Features

**Core Modeling:**
- Template-based model building from protein sequences
- Two-stage gapfilling (ATP correction + genome-scale)
- Flux balance analysis with detailed flux distributions
- Growth media creation from ModelSEED compound IDs

**Database Integration:**
- Search 33,993 compounds and 43,775 reactions
- Lookup by name, formula, EC number, or pathway
- Cross-reference to KEGG, BiGG, MetaCyc, ChEBI

**Session Management:**
- In-memory model and media storage
- List, filter, and delete models
- Predefined media library (glucose, pyruvate, aerobic/anaerobic)

---

## MCP Tools

Gem-Flux provides 11 MCP tools organized in three categories:

### Core Modeling Tools (4)

1. **`build_media`** - Create growth medium from compound IDs
2. **`build_model`** - Build metabolic model from protein sequences
3. **`gapfill_model`** - Add reactions to enable growth
4. **`run_fba`** - Execute flux balance analysis

### Database Lookup Tools (4)

5. **`get_compound_name`** - Lookup compound by ID
6. **`search_compounds`** - Search compounds by name/formula
7. **`get_reaction_name`** - Lookup reaction by ID
8. **`search_reactions`** - Search reactions by name/EC/pathway

### Session Management Tools (3)

9. **`list_models`** - List all models in session
10. **`delete_model`** - Remove model from session
11. **`list_media`** - List all media in session

**Detailed tool documentation:** See [docs/tools/README.md](docs/tools/README.md)

---

## Example Workflow

Complete workflow from protein sequences to flux predictions:

```python
from gem_flux_mcp.tools import build_model, gapfill_model, run_fba

# 1. Build draft model from protein sequences
model = await build_model(
    protein_sequences={
        "prot_001": "MKLVINLVGNSGLGKSTFTQRLIN...",
        "prot_002": "MKQHKAMIVALERFRKEKRDAALL..."
    },
    template="GramNegative",
    model_name="E_coli_K12"
)
# Returns: model_id="E_coli_K12.draft"

# 2. Gapfill for growth in glucose minimal media
gapfilled = gapfill_model(
    model_id="E_coli_K12.draft",
    media_id="glucose_minimal_aerobic",  # Predefined media
    target_growth_rate=0.01
)
# Returns: model_id="E_coli_K12.draft.gf", reactions_added=5

# 3. Run FBA to predict fluxes
fba = run_fba(
    model_id="E_coli_K12.draft.gf",
    media_id="glucose_minimal_aerobic"
)
# Returns: objective_value=0.874 (growth rate in hr⁻¹)
```

**More examples:** See [notebooks/](notebooks/) for Jupyter notebook examples

---

## Installation

### System Requirements

- **Python:** 3.11.x only (3.12+ breaks dependencies)
- **Memory:** 4 GB minimum, 8 GB recommended
- **Disk:** 2 GB (includes database files)

### Why Python 3.11?

Python 3.12+ removed `distutils`, breaking `scikit-learn 1.2.0` (ModelSEEDpy dependency). Use Python 3.11.x.

```bash
# Check version
python --version  # Must be 3.11.x

# Install Python 3.11
brew install python@3.11          # macOS
sudo apt install python3.11       # Ubuntu/Debian
```

### Installing UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uv --version
```

---

## Usage

### Starting the Server

```bash
# Basic start
./start-server.sh

# Custom host/port
export GEM_FLUX_HOST=0.0.0.0
export GEM_FLUX_PORT=9090
./start-server.sh

# Manual start
uv run python -m gem_flux_mcp.server
```

### Connecting to Server

The server uses **Model Context Protocol (MCP)** with JSON-RPC 2.0 transport.

**MCP Request Example:**
```json
{
  "jsonrpc": "2.0",
  "id": "call_123",
  "method": "tools/call",
  "params": {
    "name": "build_media",
    "arguments": {
      "compounds": ["cpd00027", "cpd00007"],
      "default_uptake": 100.0
    }
  }
}
```

### Integration with StructBioReasoner

Gem-Flux MCP integrates seamlessly with [StructBioReasoner](https://github.com/jplfaria/StructBioReasoner), enabling metabolic modeling within multi-agent protein engineering workflows.

**Quick Setup:**
1. Add Gem-Flux MCP server to StructBioReasoner config
2. Create MetabolicModeler agent (optional)
3. Use gem-flux tools from any agent

**Full guide:** [docs/STRUCTBIOREASONER_INTEGRATION_GUIDE.md](docs/STRUCTBIOREASONER_INTEGRATION_GUIDE.md)

### Optional: LLM Integration with Argo

Enable natural language interaction via Argo LLM Gateway:

```bash
# Install argo-proxy (separate from gem-flux-mcp)
pip install argo-proxy

# Start proxy
argo-proxy  # Port 8000

# Use ArgoMCPClient
from gem_flux_mcp.argo_client import ArgoMCPClient
client = ArgoMCPClient()
client.initialize_sync()
response = client.chat("Build a model for E. coli genome 83333.1")
```

**Note:** Argo is optional. Gem-Flux works without it for Python API and MCP integration.

**Full guide:** [docs/ARGO_LLM_RELIABILITY_RESEARCH.md](docs/ARGO_LLM_RELIABILITY_RESEARCH.md)

---

## Configuration

Configure via environment variables:

```bash
# Server binding
export GEM_FLUX_HOST="localhost"     # Default: localhost
export GEM_FLUX_PORT="8080"          # Default: 8080

# Resource paths
export GEM_FLUX_DATABASE_DIR="./data/database"
export GEM_FLUX_TEMPLATE_DIR="./data/templates"

# Logging
export GEM_FLUX_LOG_LEVEL="INFO"    # DEBUG, INFO, WARNING, ERROR
export GEM_FLUX_LOG_FILE="./gem-flux.log"

# Storage limits
export GEM_FLUX_MAX_MODELS="100"
export GEM_FLUX_MAX_MEDIA="50"
```

---

## Development

### Running Tests

```bash
# All tests (785 tests, 90% coverage)
uv run pytest

# Specific test types
uv run pytest tests/unit/           # Unit tests only
uv run pytest tests/integration/    # Integration tests only

# With coverage
uv run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
uv run ruff check src/      # Linting
uv run mypy src/            # Type checking
uv run black src/           # Formatting
```

---

## Troubleshooting

### Common Issues

**Python 3.12+ error:**
```
ModuleNotFoundError: No module named 'distutils'
```
**Solution:** Use Python 3.11.x (see [Installation](#installation))

**Database not found:**
```
[ERROR] Database file not found: data/database/compounds.tsv
```
**Solution:** Download database files (see [Quick Start](#quick-start))

**Template not found:**
```
[ERROR] Required template missing: GramNegModelTemplateV6.json
```
**Solution:** Copy templates from ModelSEEDpy installation
```bash
cp .venv/lib/python3.11/site-packages/modelseedpy/templates/*.json data/templates/
```

**Gapfilling infeasible:**
```
InfeasibilityError: Cannot find reactions to enable growth
```
**Solutions:**
- Try richer media (more compounds)
- Lower `target_growth_rate` (default: 0.01)
- Verify media composition with `list_media()`

**Debug mode:**
```bash
export GEM_FLUX_LOG_LEVEL=DEBUG
./start-server.sh
```

---

## Documentation

**Tool Documentation:**
- [docs/tools/README.md](docs/tools/README.md) - Complete tool reference
- [docs/tools/build_model.md](docs/tools/build_model.md) - Model building guide
- [docs/tools/gapfill_model.md](docs/tools/gapfill_model.md) - Gapfilling guide
- [docs/tools/run_fba.md](docs/tools/run_fba.md) - FBA execution guide

**Integration Guides:**
- [docs/STRUCTBIOREASONER_INTEGRATION_GUIDE.md](docs/STRUCTBIOREASONER_INTEGRATION_GUIDE.md)
- [docs/ARGO_LLM_RELIABILITY_RESEARCH.md](docs/ARGO_LLM_RELIABILITY_RESEARCH.md)

**Specifications:**
- [specs/001-system-overview.md](specs/001-system-overview.md) - Architecture
- [specs/002-data-formats.md](specs/002-data-formats.md) - Data structures
- [specs/](specs/) - 20 cleanroom specifications

**Development:**
- [docs/TESTING.md](docs/TESTING.md) - Testing guide
- [docs/ATP_CORRECTION.md](docs/ATP_CORRECTION.md) - ATP correction feature
- [.claude/CLAUDE.md](.claude/CLAUDE.md) - AI development guidelines

---

## Contributing

We welcome contributions! Key requirements:

- **Python 3.11** with type hints
- **Tests first** (TDD) - maintain ≥80% coverage
- **All tests pass** - `uv run pytest` returns 0
- **Code quality** - `ruff check` and `mypy` pass
- **Google-style docstrings**

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Support

- **Issues:** https://github.com/jplfaria/gem-flux-mcp/issues
- **Documentation:** [docs/](docs/) and [specs/](specs/)
- **Contact:** Jose P. Faria (jplfaria@anl.gov)

---

## Acknowledgments

**Built with:**
- [ModelSEEDpy](https://github.com/Fxe/ModelSEEDpy) - Metabolic model building
- [COBRApy](https://github.com/opencobra/cobrapy) - Constraint-based modeling
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework
- [UV](https://github.com/astral-sh/uv) - Python package manager

**Data:**
- [ModelSEED Database](https://github.com/ModelSEED/ModelSEEDDatabase) - Biochemistry database

---

**Status:** Production-ready MVP v0.1.0
**Last Updated:** November 4, 2025
