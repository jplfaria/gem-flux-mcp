# Gem-Flux MCP Server

A Model Context Protocol (MCP) server for genome-scale metabolic modeling with ModelSEEDpy and COBRApy. Build, gapfill, and analyze metabolic models through an AI-friendly interface.

## Status

✅ **Phase 0 Complete** - All cleanroom specifications generated and validated
🚀 **Ready for Phase 1** - Implementation can begin

## Branch Structure

- **`main`** - Stable branch with completed Phase 0 specifications
- **`phase-0-specs`** - Archival branch preserving the completed specification phase
- **`phase-1-implementation`** - Active development branch for implementation (current)

## Project Overview

Gem-Flux MCP Server enables AI assistants and developers to:
- Build genome-scale metabolic models from protein sequences
- Create and manage growth media compositions
- Gapfill models for growth in specific media conditions
- Run flux balance analysis (FBA) to predict metabolic capabilities
- Query ModelSEED compound and reaction databases

**Key Features:**
- 🧬 Template-based model building (GramNegative, GramPositive, Core)
- 🔬 Automatic RAST annotation integration
- 🧪 Two-stage gapfilling (ATP correction + genome-scale)
- 📊 Comprehensive FBA with flux analysis
- 🗃️ Session-based model and media storage
- 🔍 ModelSEED database search and lookup tools

## Project Structure

```
gem-flux-mcp/
├── specs/                          # 20 complete specifications (Phase 0 ✅)
│   ├── 001-system-overview.md      # Architecture and design
│   ├── 002-data-formats.md         # Data structures and IDs
│   ├── 003-build-media-tool.md     # Media creation tool
│   ├── 004-build-model-tool.md     # Model building tool
│   ├── 005-gapfill-model-tool.md   # Gapfilling tool
│   ├── 006-run-fba-tool.md         # FBA execution tool
│   ├── 007-database-integration.md # Database loading
│   ├── 008-compound-lookup-tools.md
│   ├── 009-reaction-lookup-tools.md
│   ├── 010-model-storage.md        # Session storage
│   ├── 011-model-import-export.md  # Model I/O (future)
│   ├── 012-complete-workflow.md    # End-to-end examples
│   ├── 013-error-handling.md       # JSON-RPC errors
│   ├── 014-installation.md         # Setup guide
│   ├── 015-mcp-server-setup.md     # MCP configuration
│   ├── 016-future-tools-roadmap.md # Post-MVP features
│   ├── 017-template-management.md  # Template loading
│   ├── 018-session-management-tools.md
│   ├── 019-predefined-media-library.md
│   └── 020-documentation-requirements.md
│
├── data/                           # Predefined resources
│   └── media/                      # 4 standard growth media (JSON)
│       ├── glucose_minimal_aerobic.json
│       ├── glucose_minimal_anaerobic.json
│       ├── pyruvate_minimal_aerobic.json
│       └── pyruvate_minimal_anaerobic.json
│
├── docs/                           # Development methodology guides
│   ├── spec-development/           # Phase 0 resources
│   │   └── PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md
│   └── implementation-loop-development/  # Phase 1 resources
│       └── PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md
│
├── specs-source/                   # Reference materials used for specs
│   ├── build_metabolic_model/      # ModelSEEDpy examples
│   ├── guidelines.md               # Specification guidelines
│   └── references/                 # Database files, docs
│
├── CONFLICT_RESOLUTION_PLAN.md     # Phase 0 conflict resolution
├── REVIEW_SUMMARY.md               # Comprehensive spec review
├── SOURCE_MATERIALS_SUMMARY.md     # Reference materials index
├── SPECS_PLAN.md                   # Original specification plan
└── README.md                       # This file
```

## Development Methodology

This project follows a **two-phase AI-assisted development methodology**:

### ✅ Phase 0: Cleanroom Specification Generation (COMPLETE)

**Completed deliverables:**
- ✅ 20 comprehensive behavioral specifications
- ✅ All 91 model_id format conflicts resolved (_gf → .gf)
- ✅ JSON-RPC 2.0 compliant error responses
- ✅ MCP protocol 2025-06-18 compatibility
- ✅ Comprehensive failure handling and recovery
- ✅ 4 predefined media compositions
- ✅ Complete documentation requirements

**See:** `/docs/spec-development/PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md`

### 🚀 Phase 1: Implementation Loop (READY TO BEGIN)

Implement code with AI assistance following the specifications:

1. **Create implementation plan** - Break specs into atomic tasks
2. **Set up project structure** - Initialize Python project with UV
3. **Run implementation loop** - AI implements with test-driven development
4. **Quality gates** - Tests (≥80% coverage), no regressions
5. **Context optimization** - Only load relevant specs

**Branch:** `phase-1-implementation` (current)

**Documentation:** See `/docs/implementation-loop-development/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md`

**⚠️ IMPORTANT:** Do not start implementation without explicit user approval.

## Technology Stack

### Core Dependencies
- **Python 3.11+** - Language runtime
- **UV** - Fast Python package manager
- **FastMCP** - MCP server framework
- **ModelSEEDpy** - Metabolic model building (dev branch required)
- **COBRApy** - Constraint-based modeling (≥0.27.0)

### MCP Protocol
- **Protocol Version:** 2025-06-18 (latest stable)
- **Transport:** JSON-RPC 2.0
- **Features:** Tools, Logging

## Quick Start (After Implementation)

```bash
# Install dependencies
uv sync

# Start MCP server
uv run fastmcp dev server.py

# Server will be ready at localhost:8080
```

## MCP Tools (8 tools in MVP)

### Core Modeling Tools
1. **build_media** - Create growth medium from compounds
2. **build_model** - Build metabolic model from protein sequences
3. **gapfill_model** - Gapfill model for growth in specific media
4. **run_fba** - Execute flux balance analysis

### Database Lookup Tools
5. **get_compound_name** - Lookup compound by ModelSEED ID
6. **get_reaction_name** - Lookup reaction by ModelSEED ID
7. **search_compounds** - Search compounds by name or formula
8. **search_reactions** - Search reactions by name or EC number

### Session Management Tools (3 additional)
9. **list_models** - List all models in current session
10. **list_media** - List all media in current session
11. **delete_model** - Delete model from session

## Example Workflow

```python
# 1. Build a metabolic model
result = build_model(
    protein_sequences={"prot1": "MKLVIN...", "prot2": "MKQHKA..."},
    template="GramNegative",
    annotate_with_rast=True
)
# Returns: model_20251027_abc123.draft

# 2. Gapfill for growth in glucose minimal media
result = gapfill_model(
    model_id="model_20251027_abc123.draft",
    media_id="glucose_minimal_aerobic",
    target_growth_rate=0.01
)
# Returns: model_20251027_abc123.draft.gf (4 reactions added)

# 3. Run FBA to predict growth
result = run_fba(
    model_id="model_20251027_abc123.draft.gf",
    media_id="glucose_minimal_aerobic"
)
# Returns: growth_rate=0.874 hr⁻¹, active fluxes
```

## Documentation

- **Specifications:** All 20 specs in `/specs/` directory
- **Phase 0 Guide:** Cleanroom specification methodology
- **Phase 1 Guide:** Implementation loop instructions
- **API Reference:** Auto-generated from tool docstrings (future)

## Testing

**Requirements (Phase 1):**
- Unit tests for all tools
- Integration tests for complete workflows
- Minimum 80% code coverage
- No regressions on spec compliance

## Contributing

1. Read the specifications in `/specs/`
2. Follow Phase 1 Implementation Loop methodology
3. Maintain test coverage ≥80%
4. All changes must align with specifications

## License

[MIT License - to be added]

## Support

- **Issues:** https://github.com/jplfaria/gem-flux-mcp/issues
- **Specifications:** See `/specs/` directory

---

**Current Status:** Phase 0 complete ✅ | Phase 1 ready to begin 🚀

*Generated using cleanroom methodology - specifications define WHAT, implementation defines HOW.*
