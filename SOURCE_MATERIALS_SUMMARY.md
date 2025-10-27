# Gem-Flux MCP Server - Source Materials Summary

**Date**: October 26, 2025
**Status**: ✅ Ready for Phase 0 Spec Generation

This document summarizes all source materials gathered for the Gem-Flux MCP server project before running the specification generation loop.

---

## Project Overview

**Project Name**: Gem-Flux MCP Server

**Purpose**: A Model Context Protocol (MCP) server for metabolic modeling workflows, enabling AI assistants and co-workers to:
- Build metabolic models from protein sequences
- Create growth media compositions
- Gapfill models for specific conditions
- Run flux balance analysis (FBA)
- Support strain design, metabolic engineering, and protein function discovery

**Target Users**: Metabolic engineers, synthetic biologists, researchers using AI-assisted workflows

**Distribution**: GitHub repository, installed locally or on remote servers (not cloud)

**Package Manager**: UV (modern Python package manager)

---

## MVP Requirements (v0.1.0)

The minimum viable product must provide these 4 core functions:

### 1. build_media
Build a growth medium from a list of compounds (using ModelSEED IDs)

### 2. build_model
Build a metabolic model from a dictionary of protein IDs → sequences
Uses ModelSEEDpy (dev branch) for model construction

### 3. gapfill_model
Gapfill a model in a specified media to enable growth
Uses ModelSEEDpy gapfilling algorithms

### 4. run_fba
Run flux balance analysis on a gapfilled model
Uses COBRApy for FBA calculations

---

## Source Materials Collected

### 1. ModelSEEDpy Build Example
**Location**: `specs-source/build_metabolic_model/build_model.ipynb`

**Content**: Complete Jupyter notebook showing:
- Loading ModelSEED templates (Core-V5.2, GramNegModelTemplateV6)
- Creating genome from FASTA file
- Annotating with RAST
- Building base model with MSBuilder
- ATP gapfilling with MSATPCorrection
- Genome-scale gapfilling with MSGapfill
- Setting media and running FBA

**Key Insights**:
- Exact ModelSEEDpy API usage patterns
- Template loading and configuration
- Multi-stage gapfilling process
- Integration with COBRApy for final FBA

**Version Requirement**: ModelSEEDpy dev branch from https://github.com/Fxe/ModelSEEDpy (documented in `ModelSEEDpy_dev_required.rtf`)

### 2. ModelSEED Database Files
**Location**: `specs-source/references/modelseed-database/`

**Files**:
- `compounds.tsv` (33,993 lines) - Compound database with IDs, names, formulas
- `reactions.tsv` (43,775 lines) - Reaction database with equations, EC numbers
- `DATABASE_README.md` - Database structure documentation

**Purpose**: Enable LLM-friendly compound/reaction lookups
**Source**: https://github.com/ModelSEED/ModelSEEDDatabase (master branch)

**Guide Created**: `modelseed-database-guide.md` explains:
- Database structure and usage
- Required MCP tools for lookups
- Implementation strategies
- Common use cases

### 3. COBRApy Documentation
**Location**: `specs-source/references/cobrapy-reference.md`

**Content**: Comprehensive guide covering:
- Model I/O (JSON format - `load_json_model`, `save_json_model`)
- Flux Balance Analysis (`model.optimize()`, `slim_optimize()`)
- Model manipulation (reactions, metabolites, constraints)
- Setting medium and exchange bounds
- Solution objects and interpretation
- Batch operations and parallelization
- Best practices for MCP server implementation

**Version**: COBRApy 0.27.0
**Source**: https://cobrapy.readthedocs.io/en/latest/

### 4. UV Package Manager Guide
**Location**: `specs-source/references/uv-package-manager.md`

**Content**: Complete guide for:
- Installing UV
- Creating virtual environments
- Managing dependencies with pyproject.toml
- GitHub Actions integration
- Best practices for distributable projects
- Quick command reference

**Purpose**: UV will be the package manager for the project
**Source**: https://docs.astral.sh/uv/

### 5. MCP Server Reference
**Location**: `specs-source/references/mcp-server-reference.md`

**Content**: Comprehensive MCP server specification showing:
- FastMCP framework usage
- OAuth 2.1 authentication with PKCE
- Tool definitions (with examples for research/hypothesis system)
- Resource definitions
- Prompt templates
- Error handling and rate limiting
- Deployment patterns

**Purpose**: Reference architecture for MCP servers
**Source**: Pre-existing in repository (AI Co-Scientist example)

### 6. CLI vs MCP Analysis
**Location**: `specs-source/references/CLI-and-MCP/`

**Files** (7 documents):
- `01-research-summary.md` - Why both CLI and MCP interfaces matter
- `02-current-spec-analysis.md` - Analysis of existing specifications
- `03-modern-cli-examples.md` - Modern CLI patterns (gh, kubectl)
- `04-modern-mcp-examples.md` - Modern MCP patterns (terminalcp)
- `05-authentication-security.md` - OAuth 2.1, PKCE, security
- `06-specification-proposal.md` - Proposed dual-interface architecture
- `07-phase16-implementation-plan.md` - Implementation roadmap

**Key Insight**: Recommends dual interface (CLI + MCP) for maximum reach, but **we're focusing on MCP only** for MVP

### 7. Additional MCP Tools Specification
**Location**: `specs-source/references/additional-mcp-tools.md`

**Content**: Specification of 34 additional tools beyond MVP:
- Model I/O and persistence
- Batch operations
- Model comparison
- Constraint modification (knockouts, overexpression)
- Media optimization
- Production strain design
- Pathway analysis
- Visualization data preparation

**Purpose**: Roadmap for future phases (v0.2.0 - v0.5.0)

---

## Technology Stack

### Core Dependencies

**ModelSEEDpy** (dev branch)
- Source: https://github.com/Fxe/ModelSEEDpy/tree/dev
- Purpose: Model building, gapfilling, media creation
- Templates: GramNegative, GramPositive, Core

**COBRApy** (≥0.27.0)
- Source: https://pypi.org/project/cobra/
- Purpose: Flux balance analysis, model I/O (JSON)
- Features: FBA, FVA, pFBA, knockout screens

**FastMCP** (latest)
- Purpose: MCP server framework
- Features: OAuth 2.1, tool/resource/prompt definitions

**Pandas** (≥2.0.0)
- Purpose: ModelSEED database queries, data manipulation

### Development Tools

**UV** - Package manager and virtual environment
**pytest** - Testing framework
**ruff** - Linter and formatter
**mypy** - Type checker

### Python Version
**Python 3.11+** (specified in `.python-version`)

---

## Key Design Decisions

### 1. ModelSEED Database Integration
LLMs need human-readable names for compounds and reactions. Required tools:
- `get_compound_name(compound_id)` → Returns "D-Glucose" for "cpd00027"
- `get_reaction_name(reaction_id)` → Returns "hexokinase" for "rxn00148"
- `search_compounds(query)` → Find compounds by name
- `search_reactions(query)` → Find reactions by name

**Implementation**: Load TSV files into pandas DataFrames at server startup

### 2. Model I/O Format
**Primary format**: COBRApy JSON
- Human-readable
- Version control friendly
- Native to COBRApy (no conversion)
- Works with Escher visualization

**Alternative formats** (future): SBML for interoperability

### 3. Deployment Architecture
- **Local installation**: Users clone repo, run `uv sync`, start server
- **Remote server**: Same installation, accessible to team
- **Not cloud**: No cloud deployment for MVP

### 4. Authentication
For MVP: Local-only, no authentication required
For future: OAuth 2.1 + PKCE (patterns documented in MCP reference)

### 5. Batch Operation Limits
- Maximum 100 models per batch operation
- Prevents resource exhaustion
- Can be adjusted based on server capacity

---

## MCP Tools Architecture

### MVP Tools (4 required)

```python
@mcp.tool()
def build_media(compounds: list[str]) -> dict:
    """Build media from ModelSEED compound IDs."""

@mcp.tool()
def build_model(protein_sequences: dict[str, str], template: str) -> dict:
    """Build model from protein ID → sequence mapping."""

@mcp.tool()
def gapfill_model(model_id: str, media: dict) -> dict:
    """Gapfill model to enable growth in media."""

@mcp.tool()
def run_fba(model_id: str, media: dict, objective: str) -> dict:
    """Run flux balance analysis."""
```

### ModelSEED Database Tools (required for LLM support)

```python
@mcp.tool()
def get_compound_name(compound_id: str) -> dict:
    """Get human-readable name for compound."""

@mcp.tool()
def get_reaction_name(reaction_id: str) -> dict:
    """Get human-readable name and equation for reaction."""

@mcp.tool()
def search_compounds(query: str, limit: int) -> list[dict]:
    """Search compounds by name."""

@mcp.tool()
def search_reactions(query: str, limit: int) -> list[dict]:
    """Search reactions by name."""
```

### Model I/O Tools (Phase 2)

```python
@mcp.tool()
def import_model_json(json_string: str) -> dict:
    """Import model from JSON."""

@mcp.tool()
def export_model_json(model_id: str) -> dict:
    """Export model to JSON."""
```

---

## Workflow Example

**User Goal**: Build a model for E. coli and analyze glucose utilization

**Steps**:
1. **Build media**: `build_media(['cpd00027', 'cpd00007', 'cpd00001', ...])` → glucose + O2 + H2O + salts
2. **Build model**: `build_model(protein_sequences, 'GramNegative')` → Draft model
3. **Gapfill**: `gapfill_model(model_id, media)` → Add missing reactions
4. **Run FBA**: `run_fba(model_id, media, 'bio1')` → Get growth rate and fluxes
5. **Interpret**: LLM uses `get_reaction_name()` to explain which pathways are active

---

## Directory Structure

```
gem-flux-mcp/
├── specs-source/                       # Source materials (this)
│   ├── build_metabolic_model/
│   │   ├── build_model.ipynb          # ModelSEEDpy example
│   │   └── ModelSEEDpy_dev_required.rtf
│   └── references/
│       ├── modelseed-database/
│       │   ├── compounds.tsv          # 33,993 compounds
│       │   ├── reactions.tsv          # 43,775 reactions
│       │   └── DATABASE_README.md
│       ├── modelseed-database-guide.md
│       ├── cobrapy-reference.md
│       ├── uv-package-manager.md
│       ├── additional-mcp-tools.md
│       ├── mcp-server-reference.md
│       └── CLI-and-MCP/               # 7 analysis documents
├── specs/                              # (Will be generated)
├── docs/
│   └── spec-development/
│       └── PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md
├── SPECS_PLAN.md                       # (Will be generated)
├── SOURCE_MATERIALS_SUMMARY.md         # This file
├── run-spec-loop.sh
├── specs-prompt.md
├── SPECS_CLAUDE.md
└── README.md
```

---

## Next Steps

### Immediate Action: Run Specification Loop

```bash
./run-spec-loop.sh
```

**What will happen**:
1. **Iteration 1**: Claude reads ALL source materials and creates `SPECS_PLAN.md`
2. **Iteration 2+**: Claude creates individual spec files (001-system-overview.md, etc.)
3. **Pause between iterations**: Human reviews each spec for quality
4. **Completion**: All specs marked [x] in SPECS_PLAN.md

**Quality Checks** for each spec:
- [ ] Describes **WHAT** (behaviors), not **HOW** (implementation)
- [ ] Clear inputs and outputs defined
- [ ] Interaction patterns specified
- [ ] Examples provided
- [ ] No implementation details (no classes, functions, algorithms)
- [ ] Consistent with source materials

### After Spec Generation Complete

1. **Validate specifications** - All planned specs created, quality verified
2. **Create IMPLEMENTATION_PLAN.md** - Break specs into atomic coding tasks
3. **Set up project structure** - Create src/, tests/, pyproject.toml
4. **Begin Phase 1**: Test-driven implementation with quality gates

---

## Success Criteria

### Phase 0 Complete When:
- [ ] SPECS_PLAN.md fully populated with all specification tasks
- [ ] All tasks in SPECS_PLAN.md marked [x]
- [ ] All spec files created in specs/ directory
- [ ] Specs describe behaviors only (no implementation)
- [ ] Specs cover all MVP tools + ModelSEED database integration
- [ ] Team can implement from specs alone

### MVP Complete When:
- [ ] All 4 core tools implemented and tested
- [ ] ModelSEED database tools working
- [ ] Models can be built, gapfilled, and analyzed
- [ ] Documentation complete
- [ ] GitHub repository ready for distribution

---

## Summary Statistics

**Source Materials**:
- 📁 Directories: 3
- 📄 Documents: 15+
- 📊 Database Files: 2 (77,768 total entries)
- 📓 Jupyter Notebooks: 1
- 🔗 External References: 5 major sources

**Lines of Documentation**:
- ModelSEED Database Guide: ~500 lines
- COBRApy Reference: ~700 lines
- UV Package Manager Guide: ~650 lines
- Additional Tools Spec: ~650 lines
- **Total**: ~4,000+ lines of reference material

**Scope**:
- MVP Tools: 4 (build_media, build_model, gapfill_model, run_fba)
- Database Tools: 4 (compound/reaction name lookups)
- Future Tools: 34 (documented for roadmap)
- **Total Planned**: 42 MCP tools across 5 phases

---

## Questions Resolved

✅ **Which version of ModelSEEDpy?** Dev branch from https://github.com/Fxe/ModelSEEDpy
✅ **Which FBA tool?** COBRApy for FBA, ModelSEEDpy for gapfilling
✅ **Package manager?** UV (fast, modern, unified)
✅ **Deployment?** Local/remote servers, not cloud
✅ **Model format?** COBRApy JSON for I/O
✅ **Database files needed?** compounds.tsv, reactions.tsv from ModelSEED
✅ **Additional tools?** Yes, documented for future phases
✅ **Visualization?** Data export only (Escher, Cytoscape), defer actual viz
✅ **Batch operations?** Yes, with limits (100 models max)
✅ **CLI vs MCP?** MCP only for MVP

---

## Ready for Spec Generation

**Status**: ✅ **All source materials gathered and documented**

**Confidence Level**: **HIGH**
- Complete example notebook showing ModelSEEDpy workflow
- Comprehensive COBRApy reference
- ModelSEED database downloaded and documented
- UV package manager guide complete
- MCP server patterns documented
- Additional tools roadmap defined

**Action Required**: Run `./run-spec-loop.sh` to begin Phase 0 specification generation.

**Estimated Spec Generation Time**: 2-4 hours (10-15 specifications expected)

**Estimated Implementation Time** (after specs):
- Phase 0 (Specs): 2-4 hours
- Phase 1 (MVP Implementation): 2-3 weeks
- Phase 2+ (Additional Features): 4-8 weeks

---

**Document Created**: October 26, 2025
**Last Updated**: October 26, 2025
**Next Review**: After spec generation complete
