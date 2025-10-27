# Gem-Flux MCP Server Specification Plan

**Status**: Plan Created
**Date**: October 27, 2025
**Target**: MVP v0.1.0 - MCP Server for Metabolic Modeling

---

## Overview

This plan outlines all specifications needed for the Gem-Flux MCP Server MVP. The server provides an MCP (Model Context Protocol) interface for metabolic modeling workflows, integrating ModelSEEDpy (model building/gapfilling) and COBRApy (flux balance analysis).

**Core Philosophy**: CLEANROOM specifications - describe WHAT the system does, not HOW it's implemented.

---

## Phase 0: Foundation Specifications

### System Architecture and Overview

- [x] **001-system-overview.md** - Complete system architecture, technology stack, data flow
  - MCP server purpose and scope
  - Integration with ModelSEEDpy and COBRApy
  - Overall workflow: media → model → gapfill → FBA
  - Deployment model (local/remote, not cloud)
  - Technology decisions (Python 3.11+, UV, FastMCP)

### Core Data Structures and Formats

- [x] **002-data-formats.md** - Data formats and structures used throughout the system
  - Model representation (COBRApy JSON)
  - Media specification format (compound_id → bounds)
  - Protein sequence format (protein_id → sequence)
  - FBA result format (fluxes, objective, status)
  - ModelSEED compound/reaction IDs
  - Exchange reaction conventions (EX_ prefix)
  - Compartment notation (_c0, _e0)

---

## Phase 1: MVP Core Tools (4 Required)

### Tool Specifications

- [x] **003-build-media-tool.md** - build_media tool specification
  - Create MSMedia from ModelSEED compound IDs
  - Input: list of compound IDs, uptake bounds, custom bounds
  - Output: media_id, compound list with names, validation results
  - Error handling: invalid compound IDs, invalid bounds
  - Example usage from AI assistant perspective

- [x] **004-build-model-tool.md** - build_model tool specification
  - Build metabolic model from protein sequences using MSBuilder
  - Input: protein_sequences dict, template name, options
  - Output: model_id, statistics, metadata
  - ModelSEEDpy workflow: MSGenome → MSBuilder → base model → ATPM
  - Template types: GramNegative, GramPositive, Core
  - Offline mode (no RAST annotation for MVP)
  - Error handling: invalid sequences, template loading failures

- [x] **005-gapfill-model-tool.md** - gapfill_model tool specification
  - Gapfill model using MSGapfill to enable growth in media
  - Input: model_id, media_id, target_growth_rate, options
  - Output: gapfilled_model_id, reactions_added, growth_rate_before/after
  - Two-stage gapfilling: ATP correction → genome-scale gapfilling
  - Test conditions for ATP gapfilling
  - Integration of gapfilling solutions
  - Error handling: infeasible gapfilling, no solution found

- [x] **006-run-fba-tool.md** - run_fba tool specification
  - Execute flux balance analysis using COBRApy
  - Input: model_id, media_id, objective (default: bio1)
  - Output: objective_value, status, fluxes, active_reactions
  - COBRApy optimize() workflow
  - Solution interpretation: optimal, infeasible, unbounded
  - Flux filtering (return only significant fluxes)
  - Error handling: infeasible models, solver failures

---

## Phase 2: ModelSEED Database Integration (4 Required)

### Database Tools for LLM Support

- [x] **007-database-integration.md** - ModelSEED database architecture
  - Database structure: compounds.tsv, reactions.tsv
  - Loading strategy: pandas DataFrames at startup
  - Indexing for O(1) lookup
  - Alias parsing for alternative names
  - Database update procedures

- [x] **008-compound-lookup-tools.md** - Compound lookup tool specifications
  - get_compound_name: ID → name, formula, aliases
  - search_compounds: query → matching compounds
  - Input validation, error handling
  - Case-insensitive search
  - Partial matching support

- [x] **009-reaction-lookup-tools.md** - Reaction lookup tool specifications
  - get_reaction_name: ID → name, equation, EC number
  - search_reactions: query → matching reactions
  - Equation formatting (human-readable)
  - Reversibility indication
  - Pathway information

---

## Phase 3: Model Persistence and I/O

### Model Management

- [x] **010-model-storage.md** - Model persistence specification
  - Session-based model storage (in-memory for MVP)
  - Model ID generation and tracking
  - Model lifecycle: create → modify → export
  - Storage limitations and cleanup
  - Future: file-based persistence

- [x] **011-model-import-export.md** - Model I/O tool specifications
  - import_model_json: Load models from COBRApy JSON
  - export_model_json: Save models to COBRApy JSON
  - JSON format characteristics
  - Validation on import
  - Compatibility with Escher, MATLAB COBRA

---

## Phase 4: Integration and Workflows

### Complete Workflows

- [x] **012-complete-workflow.md** - End-to-end workflow specification
  - Complete example: E. coli model building and analysis
  - Step 1: Create glucose minimal media
  - Step 2: Build model from protein sequences
  - Step 3: Gapfill for growth in media
  - Step 4: Run FBA and interpret results
  - Step 5: Use database tools to explain fluxes
  - Data flow between tools
  - AI assistant interaction patterns

### Error Handling and Validation

- [x] **013-error-handling.md** - Error handling patterns and validation
  - Error response format (success, error_type, message, suggestions)
  - Validation strategies for each tool
  - Common failure modes and recovery
  - Input validation patterns
  - Biological plausibility checks
  - Helpful error messages for LLMs

---

## Phase 5: Installation and Deployment

### Setup and Configuration

- [x] **014-installation.md** - Installation and deployment specification
  - UV package manager setup
  - pyproject.toml structure
  - Python 3.11+ requirement
  - Dependency management (ModelSEEDpy dev, COBRApy, FastMCP, Pandas)
  - Database file packaging
  - Server startup procedures
  - Configuration options

- [x] **015-mcp-server-setup.md** - MCP server configuration
  - FastMCP server initialization
  - Tool registration patterns
  - Server lifecycle (startup, shutdown)
  - Resource loading (templates, database)
  - Error handling at server level
  - Health checks and status

---

## Phase 6: Future Enhancements (Post-MVP)

### Roadmap Specifications

- [x] **016-future-tools-roadmap.md** - Additional tools roadmap
  - Phase 2 (v0.2.0): Model I/O, persistence, constraint modification
  - Phase 3 (v0.3.0): Batch operations, model comparison, media optimization
  - Phase 4 (v0.4.0): Production strain design, pathway analysis
  - Phase 5 (v0.5.0): Advanced batch operations, visualization data export
  - 34 additional tools across 8 categories
  - Reference: additional-mcp-tools.md for complete list

---

## Specification Quality Checklist

Each specification must meet these criteria:

- [ ] Describes WHAT, not HOW (no implementation details)
- [ ] Clear inputs and outputs with types
- [ ] Behavioral contracts specified
- [ ] Error conditions documented
- [ ] Example usage from AI assistant perspective
- [ ] Consistent with source materials (build_model.ipynb, etc.)
- [ ] No Python classes or implementation code
- [ ] Prerequisites section when depending on other specs

---

## Source Materials Reference

All specifications should reference these source materials:

1. **build_model.ipynb** - Complete ModelSEEDpy workflow example
2. **cobrapy-reference.md** - FBA operations and patterns
3. **modelseed-database-guide.md** - Compound/reaction lookup patterns
4. **uv-package-manager.md** - Deployment and dependencies
5. **additional-mcp-tools.md** - Future roadmap (34 additional tools)
6. **mcp-server-reference.md** - MCP server architecture patterns
7. **SOURCE_MATERIALS_SUMMARY.md** - Complete project overview
8. **guidelines.md** - Project-specific patterns

---

## Success Criteria

### Phase 0 Complete When:
- [x] All 16 specification files created
- [x] All checkboxes above marked [x]
- [x] Specifications are CLEANROOM (behavior only, no implementation)
- [x] Complete coverage of MVP tools + database integration
- [x] Team can implement from specs alone without additional research

### MVP Implementation Ready When:
- [ ] Phase 0 specifications complete and reviewed
- [ ] IMPLEMENTATION_PLAN.md created from specs
- [ ] Specifications validated by technical review
- [ ] All ambiguities resolved

---

## Notes

**This is a metabolic modeling MCP server**, not a multi-agent AI research system.

**Focus Areas**:
- ✅ MCP tool interfaces (inputs/outputs)
- ✅ ModelSEEDpy/COBRApy integration (library calls)
- ✅ ModelSEED database queries
- ✅ Data formats and validation
- ✅ AI assistant usage patterns

**Defer to Libraries**:
- ❌ Gapfilling algorithms (ModelSEEDpy)
- ❌ FBA linear programming (COBRApy)
- ❌ Template reaction selection logic
- ❌ ATP gapfilling algorithms

**Keep Specs Simple**:
- Capture library interfaces, not internals
- Specify tool behaviors, not implementations
- Define data contracts, not data structures
- Document workflows, not algorithms

---

**Estimated Specification Time**: 2-4 hours (16 specifications)
**Estimated Implementation Time**: 2-3 weeks after specs complete

**Next Action**: Run `./run-spec-loop.sh` again to create first specification (001-system-overview.md)
