# Changelog

All notable changes to the Gem-Flux MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2025-11-04

### Changed
- **README.md** - Major simplification and restructuring (70% reduction)
  - Reduced from 1,356 lines to 407 lines
  - MCP Tools section reduced from 432 lines to 28 lines (95% reduction)
  - Removed verbose tool documentation (link to `docs/tools/` instead)
  - Streamlined Quick Start to 3 clear steps
  - Focused on getting users running fast
  - All detailed content moved to appropriate doc files

### Added
- **README_MIGRATION_NOTES.md** - Documentation of what was moved where
- **README_COMPARISON.md** - Before/after comparison and metrics

### Philosophy
- Get users running in <5 minutes
- README is for quick start, not comprehensive docs
- Link to detailed documentation for deep dives
- Follows GitHub best practices for README length

---

## [0.1.1] - 2025-11-04

### Added
- **StructBioReasoner Integration** - Complete integration guide and README section
  - Documentation of MCP protocol compatibility
  - Step-by-step integration instructions
  - Example MetabolicModeler agent implementation
  - Use cases combining protein engineering with metabolic modeling

### Changed
- **StructBioReasoner Integration Guide** (`docs/STRUCTBIOREASONER_INTEGRATION_GUIDE.md`)
  - Updated server command to use correct `python -m gem_flux_mcp` format
  - Added compatibility status (✅ READY)
  - Clarified MCP protocol compatibility details

- **README.md** - Added "Integration with StructBioReasoner" section
  - Overview of StructBioReasoner capabilities
  - How Gem-Flux extends StructBioReasoner
  - Quick setup instructions
  - Example use cases

---

## [0.1.0] - 2025-11-04

### Added

#### Core Features
- **MCP Server Implementation** - FastMCP-based server for genome-scale metabolic modeling
- **11 MCP Tools** for metabolic modeling workflows:
  - `build_media` - Create growth media compositions from ModelSEED compounds
  - `build_model` - Build draft metabolic models from protein sequences
  - `gapfill_model` - Two-stage gapfilling (ATP correction + genome-scale)
  - `run_fba` - Flux balance analysis with detailed flux distributions
  - `get_compound_name` - Look up compound details by ID
  - `search_compounds` - Search 33,993 ModelSEED compounds
  - `get_reaction_name` - Look up reaction details by ID
  - `search_reactions` - Search 43,775 ModelSEED reactions
  - `list_models` - Browse models in current session
  - `list_media` - Browse media compositions
  - `delete_model` - Remove models from session

#### Database Integration
- **ModelSEED Database Loader** - Fast TSV parsing with pandas
- **Database Index** - Efficient lookup with multiple search strategies
- **33,993 Compounds** with names, formulas, SMILES, InChI keys, external IDs
- **43,775 Reactions** with equations, EC numbers, pathways, reversibility

#### Template System
- **Template Loader** - Supports ModelSEED reconstruction templates
- **3 Templates Included**:
  - GramNegative (2,138 reactions) - Default for Gram-negative bacteria
  - GramPositive (1,986 reactions) - For Gram-positive bacteria
  - Core (452 reactions) - Minimal core metabolism

#### Media Library
- **Predefined Media** - 4 minimal media compositions:
  - `glucose_minimal_aerobic` - Glucose + O2 (18 compounds)
  - `glucose_minimal_anaerobic` - Glucose without O2 (17 compounds)
  - `pyruvate_minimal_aerobic` - Pyruvate + O2 (18 compounds)
  - `pyruvate_minimal_anaerobic` - Pyruvate without O2 (17 compounds)

#### Session Management
- **In-Memory Storage** - Fast session-scoped model/media storage
- **Model ID Transformations** - Automatic suffixing (.draft, .gf, .draft.gf)
- **Storage Limits** - Configurable max models per session (default: 100)

#### Error Handling
- **Custom Error Classes** - NotFoundError, InfeasibleModelError, ValidationError, etc.
- **Rich Error Messages** - Context-aware error reporting with suggestions
- **Validation** - Parameter validation for all tools

#### Argo LLM Integration (Experimental)
- **ArgoMCPClient** - OpenAI-compatible client for Argo Gateway
- **MCP Tool Conversion** - Convert MCP tools to OpenAI function calling format
- **Multi-Model Support** - Tested with Claude Sonnet 4, GPT-4o, Claude Sonnet 4.5
- **Production Configuration** - Reliability-tested configs with 80% success rate
- **Enhanced Prompts** - Phase 2 system prompts with tool-specific guidance

### Documentation

#### Integration Guides
- **Claude Code Integration** (`docs/CLAUDE_CODE_INTEGRATION.md`) - Live debugging setup
- **Claude Desktop Integration** (`docs/CLAUDE_DESKTOP_INTEGRATION.md`) - End-user deployment
- **Argo LLM Reliability Research** (`docs/ARGO_LLM_RELIABILITY_RESEARCH.md`) - Multi-model testing

#### Tool Documentation
- Individual tool specifications in `docs/tools/` for all 11 tools
- Parameter formats, examples, error handling, and workflows

#### Technical Specifications
- **System Overview** (`specs/001-system-overview.md`) - Architecture overview
- **Data Formats** (`specs/002-data-formats.md`) - Input/output schemas
- **Complete Workflow** (`specs/012-complete-workflow.md`) - End-to-end examples
- 24 total specification documents covering all features

#### Development Guides
- **Testing Guide** (`docs/TESTING.md`) - Unit, integration, and real-LLM testing
- **ATP Correction** (`docs/ATP_CORRECTION.md`) - Feature implementation details
- **Session Lifecycle** (`docs/SESSION_LIFECYCLE.md`) - Storage management patterns

### Testing

- **785 Tests** across unit, integration, and Argo integration suites
- **90% Code Coverage** (exceeds 80% requirement)
- **20/20 Unit Tests Passing** - All core functionality validated
- **15 Integration Tests** - End-to-end workflow validation
- **3 Argo Real-LLM Tests** - Live LLM integration testing (requires argo-proxy)

### Dependencies

#### Core
- **FastMCP 0.2.0+** - MCP server framework
- **COBRApy 0.27.0+** - Constraint-based modeling
- **ModelSEEDpy** (Fxe/dev branch) - Template-based reconstruction
- **pandas 2.0.0+** - Database loading
- **numpy 1.24.0+** - Numerical operations

#### Argo LLM (Optional)
- **openai 1.0.0+** - For Argo Gateway integration
- **httpx 0.28.0+** - For argo-proxy availability checking

#### Development
- **pytest 7.4.0+** - Testing framework
- **pytest-cov 4.1.0+** - Coverage reporting
- **pytest-asyncio 0.21.0+** - Async test support
- **black 23.0.0+** - Code formatting
- **ruff 0.1.0+** - Linting

### Configuration

#### Environment Variables
- `GEM_FLUX_DATABASE_DIR` - ModelSEED database location (default: ./data/database)
- `GEM_FLUX_TEMPLATE_DIR` - Template directory (default: ./data/templates)
- `GEM_FLUX_MAX_MODELS` - Max models in session (default: 100)
- `GEM_FLUX_LOG_LEVEL` - Logging verbosity (default: INFO)

#### Python Requirements
- **Python 3.11.x REQUIRED** - Python 3.12+ not supported (distutils removed)

### Known Limitations

- **Session-scoped storage only** - Models/media lost on server restart
- **No persistent storage** - File-based persistence planned for v0.2.0
- **Python 3.11 only** - Due to ModelSEEDpy dependency chain
- **Memory constraints** - Very large models (>10,000 reactions) may be slow
- **No visualization** - Flux distributions are text-only (visualization planned)

### Contributors

- João Paulo Lima Faria (@jplfaria) - Lead Developer

---

## [Unreleased]

### Planned for v0.2.0
- Persistent model storage (save/load to disk)
- SBML import/export
- Network visualization for flux analysis
- Batch processing support
- Performance optimizations for large models
- Python 3.12+ support (when ModelSEEDpy updated)

---

## Release Notes

### v0.1.0 - Initial Release

This is the first public release of Gem-Flux MCP Server, providing a complete Model Context Protocol interface for genome-scale metabolic modeling.

**Key Highlights:**
- ✅ 11 fully functional MCP tools
- ✅ 785 tests with 90% coverage
- ✅ Complete documentation (specs + guides)
- ✅ Claude Code & Claude Desktop integration
- ✅ Argo LLM support (experimental)
- ✅ Production-ready for metabolic modeling workflows

**Getting Started:**
See [README.md](README.md) for installation and quick start guide.

**Integration:**
- Claude Code: [docs/CLAUDE_CODE_INTEGRATION.md](docs/CLAUDE_CODE_INTEGRATION.md)
- Claude Desktop: [docs/CLAUDE_DESKTOP_INTEGRATION.md](docs/CLAUDE_DESKTOP_INTEGRATION.md)

**Support:**
- GitHub Issues: https://github.com/jplfaria/gem-flux-mcp/issues
- Documentation: [README.md](README.md), [docs/](docs/)

---

[0.1.0]: https://github.com/jplfaria/gem-flux-mcp/releases/tag/v0.1.0
[Unreleased]: https://github.com/jplfaria/gem-flux-mcp/compare/v0.1.0...HEAD
