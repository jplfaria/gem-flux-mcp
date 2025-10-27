# Gem-Flux MCP Server Implementation Plan

**Status**: Phase 1 - Implementation Ready
**Created**: 2025-10-27
**Methodology**: Comprehensive plan based on all 20 cleanroom specifications

---

## Overview

This plan implements the **Gem-Flux MCP Server**, a Model Context Protocol server that provides AI assistants with tools for building, gapfilling, and analyzing genome-scale metabolic models using ModelSEEDpy and COBRApy.

**Key Facts**:
- **20 specifications** analyzed and incorporated
- **8 MCP tools** to implement
- **Session-based storage** (models/media in-memory for MVP)
- **Model ID format**: Uses `.gf` suffix notation (e.g., `model.draft`, `model.draft.gf`)
- **Python 3.11 ONLY** - Python 3.12+ incompatible (missing distutils for scikit-learn dependency)
- **ModelSEEDpy Fork**: Must use Fxe/dev branch (not official repo)

---

## Implementation Phases

### Phase 1: Foundation & Infrastructure (Tasks 1-10)
Core project setup, dependencies, and basic infrastructure

### Phase 2: Database & Templates (Tasks 11-20)
ModelSEED database loading, template management, and data access

### Phase 3: Session Storage (Tasks 21-30)
In-memory model/media storage with .gf suffix handling

### Phase 4: Database Lookup Tools (Tasks 31-40)
Compound and reaction lookup/search tools

### Phase 5: Core MCP Tools - Part 1 (Tasks 41-50)
build_media and build_model tools

### Phase 6: Core MCP Tools - Part 2 (Tasks 51-60)
gapfill_model and run_fba tools

### Phase 7: Session Management Tools (Tasks 61-70)
list_models, delete_model, list_media tools

### Phase 8: MCP Server Setup (Tasks 71-80)
FastMCP server initialization, tool registration, startup/shutdown

### Phase 9: Integration & Testing (Tasks 81-90)
End-to-end workflows, integration tests, error handling

### Phase 10: Documentation & Finalization (Tasks 91-100)
README, examples, deployment guide, final validation

---

## Detailed Task List

### Phase 1: Foundation & Infrastructure

- [x] **Task 1**: Create project package structure
  - Create `src/gem_flux_mcp/` directory
  - Create `__init__.py` files for all packages
  - Set up `tests/unit/` and `tests/integration/` directories
  - Verify package can be imported

- [x] **Task 2**: Configure pyproject.toml with dependencies
  - Add Python 3.11 requirement (NOT 3.12+)
  - Add ModelSEEDpy from Fxe/dev fork: `git+https://github.com/Fxe/ModelSEEDpy.git@dev`
  - Add COBRApy >=0.27.0
  - Add FastMCP (latest)
  - Add Pandas >=2.0.0
  - Add development dependencies (pytest, pytest-cov, mypy, ruff)

- [x] **Task 3**: Set up Python 3.11 virtual environment with UV
  - Verify Python 3.11 available
  - Run `uv sync` to install dependencies
  - Verify ModelSEEDpy Fxe/dev fork installed correctly
  - Test import: `from modelseedpy import MSBuilder`

- [x] **Task 4**: Create database directory structure
  - Create `data/database/` directory
  - Create placeholder for `compounds.tsv` and `reactions.tsv`
  - Create `.gitignore` entries for large database files
  - Document database source URLs in README

- [x] **Task 5**: Create templates directory structure
  - Create `data/templates/` directory
  - Create placeholder for template JSON files
  - Document template sources in README
  - Verify template files can be loaded

- [x] **Task 6**: Set up pytest configuration
  - Create `pytest.ini` with test discovery settings
  - Configure coverage thresholds (>=80%)
  - Set up test fixtures directory
  - Create conftest.py with ModelSEEDpy mocks

- [ ] **Task 7**: Create logging infrastructure
  - Create `src/gem_flux_mcp/logging.py` module
  - Configure log levels (DEBUG, INFO, WARNING, ERROR)
  - Set up console and file logging handlers
  - Write unit tests for logging (tests/unit/test_logging.py)
  - Test logging output and verify coverage ≥80%

- [ ] **Task 8**: Create error handling module
  - Create `src/gem_flux_mcp/errors.py`
  - Define custom exceptions (ModelNotFoundError, MediaNotFoundError, etc.)
  - Define JSON-RPC 2.0 compliant error responses
  - Add error message templates

- [ ] **Task 9**: Create data types module
  - Create `src/gem_flux_mcp/types.py`
  - Define TypedDict classes for request/response formats
  - Define Pydantic models for validation
  - Document all data structures

- [ ] **Task 10**: Write unit tests for infrastructure
  - Test logging configuration
  - Test error response formatting
  - Test data type validation
  - Verify 100% coverage for infrastructure

---

### Phase 2: Database & Templates

- [ ] **Task 11**: Implement database loader module
  - Create `src/gem_flux_mcp/database/loader.py`
  - Implement `load_compounds_database()` function (pandas TSV reader)
  - Implement `load_reactions_database()` function
  - Add validation for required columns
  - Handle missing/corrupted files with clear errors

- [ ] **Task 12**: Implement database indexing
  - Create indexed DataFrames for O(1) lookup by ID
  - Index compounds by: id, name (lowercase), abbreviation
  - Index reactions by: id, name (lowercase), abbreviation, EC numbers
  - Verify lookup performance (<1ms per query)

- [ ] **Task 13**: Implement alias parsing
  - Parse pipe-separated aliases: `"KEGG: C00031|BiGG: glc__D"`
  - Handle semicolon-separated multiple IDs: `"BiGG: id1;id2"`
  - Return structured dict: `{"KEGG": ["C00031"], "BiGG": ["glc__D"]}`
  - Handle malformed aliases gracefully (skip, continue)

- [ ] **Task 14**: Implement compound ID validation
  - Validate format: `cpd\d{5}` regex pattern
  - Check existence in database
  - Return ValidationError for invalid format
  - Return CompoundNotFoundError for non-existent IDs

- [ ] **Task 15**: Implement reaction ID validation
  - Validate format: `rxn\d{5}` regex pattern
  - Check existence in database
  - Return ValidationError for invalid format
  - Return ReactionNotFoundError for non-existent IDs

- [ ] **Task 16**: Write database loader unit tests
  - Test successful database loading
  - Test handling of missing files
  - Test handling of corrupted TSV
  - Test validation of row counts (>30k compounds, >35k reactions)
  - Test alias parsing with various formats

- [ ] **Task 17**: Implement template loader module
  - Create `src/gem_flux_mcp/templates/loader.py`
  - Implement `load_template()` function (reads JSON, uses MSTemplateBuilder)
  - Load GramNegative, GramPositive, Core templates
  - Store in dict: `{"GramNegative": MSTemplate, ...}`
  - Log template statistics (reaction counts)

- [ ] **Task 18**: Implement template validation
  - Verify template has reactions, metabolites, compartments
  - Count reactions per template
  - Validate biomass reaction exists
  - Handle invalid templates gracefully (log warning, skip)

- [ ] **Task 19**: Implement ATP gapfill media loading
  - Load default media via `load_default_medias()` from ModelSEEDpy
  - Store 54 media compositions for ATP correction
  - Handle loading failures gracefully
  - Log number of media loaded

- [ ] **Task 20**: Write template loader unit tests
  - Test successful template loading
  - Test handling of missing template files
  - Test handling of invalid JSON
  - Test template validation
  - Mock MSTemplateBuilder for testing

---

### Phase 3: Session Storage

- [ ] **Task 21**: Implement model storage module
  - Create `src/gem_flux_mcp/storage/models.py`
  - Implement in-memory dict storage: `models: dict[str, cobra.Model] = {}`
  - Implement `store_model(model_id, model)` function
  - Implement `retrieve_model(model_id)` function
  - Implement `list_model_ids()` function

- [ ] **Task 22**: Implement model ID generation
  - Implement `generate_model_id(state="draft")` function
  - Format: `model_{timestamp}_{random}.{state}`
  - Example: `model_20251027_143052_a3f9b2.draft`
  - Ensure uniqueness (check existing IDs, regenerate if collision)

- [ ] **Task 23**: Implement user-provided model ID handling
  - Implement `generate_model_id_from_name(name, state, existing_ids)` function
  - Check for collisions with existing model IDs
  - Append timestamp if collision: `E_coli_K12_20251027_143052.draft`
  - Preserve user's custom name when possible

- [ ] **Task 24**: Implement state suffix transformation
  - Implement `transform_state_suffix(model_id)` function
  - Transform `.draft` → `.draft.gf`
  - Transform `.gf` → `.gf.gf`
  - Transform `.draft.gf` → `.draft.gf.gf`
  - Preserve base name during transformation

- [ ] **Task 25**: Implement media storage module
  - Create `src/gem_flux_mcp/storage/media.py`
  - Implement in-memory dict storage: `media: dict[str, MSMedia] = {}`
  - Implement `store_media(media_id, media)` function
  - Implement `retrieve_media(media_id)` function
  - Implement `list_media_ids()` function

- [ ] **Task 26**: Implement media ID generation
  - Implement `generate_media_id()` function
  - Format: `media_{timestamp}_{random}`
  - Example: `media_20251027_143052_x1y2z3`
  - Ensure uniqueness

- [ ] **Task 27**: Implement storage error handling
  - Define ModelNotFoundError with available models list
  - Define MediaNotFoundError with available media list
  - Define StorageCollisionError (rare, after retry exhaustion)
  - Include helpful suggestions in error messages

- [ ] **Task 28**: Implement session storage initialization
  - Initialize empty storage dicts on server startup
  - Set up ID generation counters
  - Configure storage limits (100 models, 50 media for MVP)
  - Log initialization complete

- [ ] **Task 29**: Implement storage cleanup on shutdown
  - Clear all models from storage
  - Clear all media from storage
  - Log storage statistics before clearing
  - Free memory (Python garbage collection)

- [ ] **Task 30**: Write storage unit tests
  - Test model storage and retrieval
  - Test media storage and retrieval
  - Test model ID generation (auto and user-provided)
  - Test state suffix transformation
  - Test collision handling
  - Test ModelNotFoundError and MediaNotFoundError

---

### Phase 4: Database Lookup Tools

- [ ] **Task 31**: Implement get_compound_name tool
  - Create `src/gem_flux_mcp/tools/get_compound_name.py`
  - Input: `{"compound_id": "cpd00027"}`
  - Validate compound_id format and existence
  - Query database for compound record
  - Parse aliases into structured dict
  - Return: name, abbreviation, formula, mass, charge, inchikey, smiles, aliases

- [ ] **Task 32**: Implement search_compounds tool
  - Create `src/gem_flux_mcp/tools/search_compounds.py`
  - Input: `{"query": "glucose", "limit": 10}`
  - Search in order: exact ID, exact name, exact abbreviation, partial name, formula, aliases
  - Rank results: exact matches first, then partial
  - Return: list of compound objects with match_field and match_type

- [ ] **Task 33**: Implement get_reaction_name tool
  - Create `src/gem_flux_mcp/tools/get_reaction_name.py`
  - Input: `{"reaction_id": "rxn00148"}`
  - Validate reaction_id format and existence
  - Query database for reaction record
  - Parse equation (with IDs and with names)
  - Parse reversibility symbol to readable string
  - Parse EC numbers, pathways, aliases
  - Return: name, abbreviation, equation, equation_with_ids, reversibility, direction, is_transport, ec_numbers, pathways, aliases

- [ ] **Task 34**: Implement search_reactions tool
  - Create `src/gem_flux_mcp/tools/search_reactions.py`
  - Input: `{"query": "hexokinase", "limit": 10}`
  - Search in order: exact ID, exact name, exact abbreviation, EC number, partial name, aliases, pathways
  - Rank results: exact matches first, then partial
  - Return: list of reaction objects with match_field and match_type

- [ ] **Task 35**: Implement equation formatting
  - Parse database equation with compound IDs
  - Parse database definition with compound names
  - Remove compartment suffixes `[0]` for readability
  - Format: `"(1) D-Glucose + (1) ATP => (1) ADP + (1) H+ + (1) D-Glucose-6-phosphate"`

- [ ] **Task 36**: Implement pathway parsing
  - Parse pipe-separated pathways: `"MetaCyc: Glycolysis|KEGG: rn00010"`
  - Extract pathway names, remove database prefixes
  - Return array: `["Glycolysis", "Glycolysis / Gluconeogenesis"]`

- [ ] **Task 37**: Write unit tests for get_compound_name
  - Test successful compound lookup (cpd00027 → D-Glucose)
  - Test compound not found error
  - Test invalid format error
  - Test alias parsing

- [ ] **Task 38**: Write unit tests for search_compounds
  - Test exact name match
  - Test partial name match
  - Test formula search
  - Test empty results
  - Test limit parameter

- [ ] **Task 39**: Write unit tests for get_reaction_name
  - Test successful reaction lookup (rxn00148 → hexokinase)
  - Test reaction not found error
  - Test equation formatting
  - Test reversibility parsing

- [ ] **Task 40**: Write unit tests for search_reactions
  - Test exact name match
  - Test EC number search
  - Test pathway search
  - Test empty results
  - Test limit parameter

---

### Phase 5: Core MCP Tools - Part 1

- [ ] **Task 41**: Implement build_media tool
  - Create `src/gem_flux_mcp/tools/build_media.py`
  - Input: `{"compounds": ["cpd00027", ...], "default_uptake": 100.0, "custom_bounds": {...}}`
  - Validate all compound IDs exist in database
  - Apply default bounds: `(-default_uptake, 100.0)`
  - Override with custom_bounds for specific compounds
  - Create MSMedia object via `MSMedia.from_dict()`
  - Generate media_id
  - Store in session storage
  - Enrich response with compound names from database
  - Return: media_id, compounds with names, num_compounds, media_type

- [ ] **Task 42**: Implement build_media validation
  - Validate compounds list not empty
  - Validate all compound IDs match format `cpd\d{5}`
  - Validate all compound IDs exist in database
  - Validate default_uptake is positive
  - Validate custom_bounds have lower < upper
  - Validate no duplicate compound IDs
  - Return ValidationError with ALL invalid IDs

- [ ] **Task 43**: Implement media classification heuristic
  - If num_compounds < 50: "minimal" media
  - If num_compounds >= 50: "rich" media
  - Return media_type in response

- [ ] **Task 44**: Write unit tests for build_media
  - Test successful media creation (glucose minimal media)
  - Test invalid compound IDs error
  - Test empty compounds list error
  - Test invalid bounds error
  - Test custom_bounds override default

- [ ] **Task 45**: Implement build_model tool (FASTA input)
  - Create `src/gem_flux_mcp/tools/build_model.py`
  - Input: `{"fasta_file_path": "/path/to/proteins.faa", "template": "GramNegative", "model_name": "E_coli_K12", "annotate_with_rast": true}`
  - Validate FASTA file exists and is readable
  - Validate template name is valid
  - Load template from template storage
  - Convert dict to .faa if dict provided (for RAST)
  - Create MSGenome from FASTA (with RAST annotation if enabled)
  - Create MSBuilder with genome and template
  - Call `build_base_model(annotate_with_rast=True/False)`
  - Add ATPM reaction via `add_atpm(model)`
  - Generate model_id with `.draft` state
  - Store model in session storage
  - Collect statistics (num_reactions, num_metabolites, num_genes)
  - Return: model_id, statistics, template_used, compartments

- [ ] **Task 46**: Implement build_model tool (dict input)
  - Handle `protein_sequences` dict input
  - Validate all amino acid sequences contain only valid characters: `[ACDEFGHIKLMNPQRSTVWY]`
  - Convert dict to temporary .faa file for RAST (if annotate_with_rast=true)
  - Create MSGenome from dict (without RAST if offline mode)
  - Rest follows same flow as FASTA input

- [ ] **Task 47**: Implement protein sequence validation
  - Validate non-empty protein_sequences dict OR fasta_file_path (not both)
  - Validate amino acid alphabet: `ACDEFGHIKLMNPQRSTVWY`
  - Report ALL invalid sequences (don't stop at first)
  - Validate no empty sequences
  - Validate no duplicate protein IDs

- [ ] **Task 48**: Implement RAST annotation integration
  - If `annotate_with_rast=true`: submit .faa to RAST API
  - Handle RAST network errors gracefully
  - Use RAST results to create MSGenome with functional annotations
  - If `annotate_with_rast=false`: offline template matching only
  - Document RAST vs offline tradeoffs

- [ ] **Task 49**: Implement model statistics collection
  - Count total reactions, metabolites, genes
  - Break down reactions by compartment
  - Count exchange reactions (EX_ prefix)
  - Count reversible vs irreversible reactions
  - Identify transport reactions
  - Set `is_draft=true`, `requires_gapfilling=true`

- [ ] **Task 50**: Write unit tests for build_model
  - Test successful model building from dict
  - Test successful model building from FASTA
  - Test invalid amino acid sequences error
  - Test invalid template error
  - Test empty protein sequences error
  - Test both inputs provided error
  - Mock MSBuilder, MSGenome for testing

---

### Phase 6: Core MCP Tools - Part 2

- [ ] **Task 51**: Implement gapfill_model tool
  - Create `src/gem_flux_mcp/tools/gapfill_model.py`
  - Input: `{"model_id": "model_abc.draft", "media_id": "media_001", "target_growth_rate": 0.01, "allow_all_non_grp_reactions": true, "gapfill_mode": "full"}`
  - Validate model_id and media_id exist
  - Load model and media from session storage
  - Create copy of model (preserve original)
  - Run ATP correction (MSATPCorrection)
  - Run genome-scale gapfilling (MSGapfill)
  - Integrate gapfilling solutions into model
  - Transform model_id state suffix (`.draft` → `.draft.gf`)
  - Store gapfilled model with new model_id
  - Return: new model_id, reactions_added, growth_rate_before, growth_rate_after, statistics

- [ ] **Task 52**: Implement ATP correction stage
  - Load default ATP test media (54 media)
  - Create MSATPCorrection object
  - Run `evaluate_growth_media()` to test all media
  - Run `determine_growth_media()` to identify failures
  - Run `apply_growth_media_gapfilling()` to add reactions
  - Run `expand_model_to_genome_scale()` to add full template
  - Run `build_tests()` to create test conditions
  - Collect ATP correction statistics (media tested, passed, failed, reactions added)

- [ ] **Task 53**: Implement genome-scale gapfilling stage
  - Create MSGapfill object with ATP-corrected model
  - Load genome-scale template
  - Set target media and growth rate
  - Run `run_gapfilling(media, target_growth_rate)`
  - Parse gapfilling solution: `{"reversed": {...}, "new": {...}}`
  - Integrate reactions into model
  - Auto-generate exchange reactions for new metabolites
  - Verify final growth rate >= target

- [ ] **Task 54**: Implement gapfilling solution integration
  - Parse direction symbols: `>` (forward), `<` (reverse), `=` (reversible)
  - Get reaction from template by ID
  - Convert to COBRApy reaction
  - Set bounds based on direction
  - Add to model
  - Handle exchange reactions separately

- [ ] **Task 55**: Implement gapfilling failure handling
  - **Standalone failure**: Return error, keep draft model unchanged
  - **Pipeline failure**: Return draft model_id, set gapfilling_successful=false
  - Distinguish between ATP correction failure (acceptable) and genome-scale failure (error)
  - Include recovery suggestions in error response
  - Document failure scenarios in error details

- [ ] **Task 56**: Enrich gapfilling response with reaction metadata
  - For each added reaction, query database for name, equation
  - Format equation for human readability
  - Include pathway information if available
  - Build reactions_added array with metadata

- [ ] **Task 57**: Write unit tests for gapfill_model
  - Test successful gapfilling (draft → draft.gf)
  - Test gapfilling infeasible error
  - Test model not found error
  - Test media not found error
  - Test state suffix transformation
  - Mock MSGapfill, MSATPCorrection for testing

- [ ] **Task 58**: Implement run_fba tool
  - Create `src/gem_flux_mcp/tools/run_fba.py`
  - Input: `{"model_id": "model_abc.draft.gf", "media_id": "media_001", "objective": "bio1", "maximize": true, "flux_threshold": 1e-6}`
  - Validate model_id and media_id exist
  - Load model and media from session storage
  - Create temporary copy of model (preserve original)
  - Apply media constraints to exchange reactions
  - Set objective function
  - Run FBA: `solution = model.optimize()`
  - Extract fluxes, filter by threshold
  - Separate uptake/secretion fluxes
  - Enrich with compound/reaction names
  - Return: objective_value, status, fluxes, uptake_fluxes, secretion_fluxes, top_fluxes, summary

- [ ] **Task 59**: Implement media application to model
  - Get media constraints from MSMedia: `media.get_media_constraints()`
  - Map compound IDs to exchange reaction IDs: `cpd00027_e0` → `EX_cpd00027_e0`
  - Set uptake bounds (COBRApy uses positive values for uptake)
  - Apply medium: `model.medium = medium`
  - Verify all media compounds have exchange reactions

- [ ] **Task 60**: Write unit tests for run_fba
  - Test successful FBA (optimal solution)
  - Test infeasible model error
  - Test unbounded model error
  - Test model not found error
  - Test media not found error
  - Test flux threshold filtering
  - Mock COBRApy model.optimize() for testing

---

### Phase 7: Session Management Tools

- [ ] **Task 61**: Implement list_models tool
  - Create `src/gem_flux_mcp/tools/list_models.py`
  - Input: `{"filter_state": "all"}`  # "all", "draft", "gapfilled"
  - Query MODEL_STORAGE for all models
  - Extract metadata from each COBRApy Model object
  - Determine state from model_id suffix
  - Apply filter if specified
  - Sort by created_at timestamp (oldest first)
  - Return: models array, total_models, models_by_state

- [ ] **Task 62**: Implement state classification
  - Parse state from model_id suffix
  - `.draft` → state: "draft"
  - `.gf` or `.draft.gf` or any suffix containing `.gf` → state: "gapfilled"
  - Include in model metadata

- [ ] **Task 63**: Implement delete_model tool
  - Create `src/gem_flux_mcp/tools/delete_model.py`
  - Input: `{"model_id": "model_abc.draft"}`
  - Validate model_id exists in storage
  - Remove from MODEL_STORAGE dictionary
  - Memory freed automatically (Python GC)
  - Return: success, deleted_model_id

- [ ] **Task 64**: Implement list_media tool
  - Create `src/gem_flux_mcp/tools/list_media.py`
  - Input: `{}` (no parameters)
  - Query MEDIA_STORAGE for all media
  - Extract metadata from each MSMedia object
  - Get first 3 compounds for preview
  - Sort by created_at timestamp
  - Count predefined vs user-created media
  - Return: media array, total_media, predefined_media, user_created_media

- [ ] **Task 65**: Write unit tests for list_models
  - Test listing all models
  - Test filtering by state (draft, gapfilled)
  - Test empty storage
  - Test sorting by timestamp

- [ ] **Task 66**: Write unit tests for delete_model
  - Test successful deletion
  - Test model not found error
  - Test missing model_id parameter error

- [ ] **Task 67**: Write unit tests for list_media
  - Test listing all media
  - Test empty storage
  - Test compounds preview (first 3)

- [ ] **Task 68**: Implement predefined media library
  - Create `data/media/` directory
  - Create 4 predefined media JSON files:
    - `glucose_minimal_aerobic.json`
    - `glucose_minimal_anaerobic.json`
    - `pyruvate_minimal_aerobic.json`
    - `pyruvate_minimal_anaerobic.json`
  - Load predefined media on server startup
  - Store with fixed media_ids (not timestamp-based)

- [ ] **Task 69**: Write integration tests for session management
  - Test: build_model → list_models → delete_model workflow
  - Test: build_media → list_media workflow
  - Test: Multiple models in session, filter by state

- [ ] **Task 70**: Document session lifecycle
  - Document model lifecycle: Creation → Modification → Query → Session End
  - Document media lifecycle: Creation → Usage → Session End
  - Document ID generation patterns
  - Document state suffix transformations

---

### Phase 8: MCP Server Setup

- [ ] **Task 71**: Implement FastMCP server initialization
  - Create `src/gem_flux_mcp/server.py`
  - Import FastMCP framework
  - Create MCP server instance: `mcp = FastMCP("gem-flux-mcp")`
  - Set server metadata (name, version, description)
  - Set protocol_version: "2025-06-18" (latest MCP protocol)
  - Configure capabilities: tools=True, resources=False, prompts=False, logging=True

- [ ] **Task 72**: Implement resource loading on startup
  - Phase 1: Load ModelSEED database (compounds.tsv, reactions.tsv)
  - Phase 2: Load ModelSEED templates (GramNegative, GramPositive, Core)
  - Phase 3: Load ATP gapfilling media (54 default media)
  - Phase 4: Load predefined media library (4 media)
  - Log loading statistics and timing
  - Exit with error if critical resources fail to load

- [ ] **Task 73**: Implement tool registration with FastMCP
  - Register all 8 MVP tools using `@mcp.tool()` decorator
  - Tools: build_media, build_model, gapfill_model, run_fba, get_compound_name, get_reaction_name, search_compounds, search_reactions
  - Add session management tools: list_models, delete_model, list_media
  - Use type hints for automatic schema generation
  - Document each tool with comprehensive docstrings
  - Log tool registration statistics

- [ ] **Task 74**: Implement session storage initialization
  - Initialize empty MODEL_STORAGE dict
  - Initialize empty MEDIA_STORAGE dict
  - Set up ID generation (timestamp + random)
  - Configure storage limits (100 models, 50 media)
  - Log initialization complete

- [ ] **Task 75**: Implement server startup sequence
  - Parse environment variables for configuration
  - Initialize logging (console + file)
  - Load database, templates, media
  - Initialize session storage
  - Register tools
  - Bind to host:port (default: localhost:8080)
  - Log "Server ready" message

- [ ] **Task 76**: Implement graceful shutdown
  - Handle SIGINT, SIGTERM signals
  - Stop accepting new requests
  - Wait for active requests to complete (timeout: 30s)
  - Clear session storage (models, media)
  - Log shutdown statistics
  - Exit with code 0

- [ ] **Task 77**: Implement configuration via environment variables
  - `GEM_FLUX_HOST`: Host to bind (default: localhost)
  - `GEM_FLUX_PORT`: Port to listen (default: 8080)
  - `GEM_FLUX_DATABASE_DIR`: Database location (default: ./data/database)
  - `GEM_FLUX_TEMPLATE_DIR`: Template location (default: ./data/templates)
  - `GEM_FLUX_LOG_LEVEL`: Log level (default: INFO)
  - `GEM_FLUX_LOG_FILE`: Log file path (default: ./gem-flux.log)

- [ ] **Task 78**: Implement server error handling
  - Startup errors: Database load failure, template load failure, port in use
  - Runtime errors: Tool execution failures, invalid MCP requests
  - Return JSON-RPC 2.0 compliant error responses
  - Log errors with context

- [ ] **Task 79**: Write unit tests for server setup
  - Test successful server initialization
  - Test database loading failure
  - Test template loading failure
  - Test tool registration
  - Test graceful shutdown

- [ ] **Task 80**: Create server startup script
  - Create `start-server.sh` with environment variable configuration
  - Create `pyproject.toml` script entry point
  - Document startup command: `uv run python -m gem_flux_mcp.server`
  - Test server starts and accepts requests

---

### Phase 9: Integration & Testing

- [ ] **Task 81**: Write integration test: Complete workflow
  - Test: build_media → build_model → gapfill_model → run_fba
  - Verify model progresses through states: .draft → .draft.gf
  - Verify FBA returns optimal growth rate
  - Verify all intermediate results stored correctly

- [ ] **Task 82**: Write integration test: Database lookups
  - Test: search_compounds → get_compound_name
  - Test: search_reactions → get_reaction_name
  - Verify enrichment of tool outputs with names

- [ ] **Task 83**: Write integration test: Session management
  - Test: Create multiple models → list_models → delete_model
  - Test: Create multiple media → list_media
  - Verify storage limits respected

- [ ] **Task 84**: Write integration test: Error handling
  - Test: Model not found error flow
  - Test: Media not found error flow
  - Test: Invalid compound IDs in build_media
  - Test: Gapfilling infeasible error
  - Test: Infeasible FBA error

- [ ] **Task 85**: Write integration test: Model ID transformations
  - Test: build_model creates .draft suffix
  - Test: gapfill_model transforms .draft → .draft.gf
  - Test: Re-gapfilling appends .gf: .draft.gf → .draft.gf.gf
  - Test: User-provided names preserved

- [ ] **Task 86**: Implement test expectations file
  - Create `tests/integration/test_expectations.json`
  - Define `must_pass` tests (critical path)
  - Define `may_fail` tests (waiting on components)
  - Document phase descriptions

- [ ] **Task 87**: Set up CI/CD pipeline (GitHub Actions)
  - Create `.github/workflows/test.yml`
  - Run tests on Python 3.11 only
  - Check coverage >=80%
  - Run linting (ruff)
  - Run type checking (mypy)

- [ ] **Task 88**: Implement comprehensive error handling test suite
  - Test all error types from spec 013
  - Verify JSON-RPC 2.0 compliance
  - Verify helpful error messages
  - Verify recovery suggestions included

- [ ] **Task 89**: Performance testing
  - Measure startup time (<5 seconds)
  - Measure database query performance (<1ms lookup, <100ms search)
  - Measure FBA performance (<200ms for typical model)
  - Verify memory usage acceptable (check for leaks)

- [ ] **Task 90**: Create comprehensive test fixtures
  - Create test protein sequences (FASTA and dict)
  - Create test ModelSEED compound/reaction IDs
  - Create test media compositions
  - Mock ModelSEEDpy classes in conftest.py

---

### Phase 10: Documentation & Finalization

- [ ] **Task 91**: Write comprehensive README.md
  - Project overview and purpose
  - Installation instructions (Python 3.11, UV, dependencies)
  - Quick start guide
  - List of 8 MCP tools with examples
  - Configuration options
  - Troubleshooting guide

- [ ] **Task 92**: Create example Jupyter notebooks
  - Notebook 1: Basic workflow (build → gapfill → FBA)
  - Notebook 2: Database lookups
  - Notebook 3: Session management
  - Notebook 4: Error handling and recovery

- [ ] **Task 93**: Write CLAUDE.md project instructions
  - Update with final implementation patterns
  - Document .gf notation usage
  - Document ModelSEEDpy Fxe/dev fork requirement
  - Document Python 3.11 requirement

- [ ] **Task 94**: Create deployment guide
  - Local development server setup
  - Remote server deployment (systemd service)
  - Docker deployment (future)
  - Environment variable configuration
  - Security considerations (future)

- [ ] **Task 95**: Write CHANGELOG.md
  - Document v0.1.0 MVP features
  - List all 8 implemented tools
  - Document known limitations
  - Document future roadmap

- [ ] **Task 96**: Create CONTRIBUTING.md
  - Code style guidelines (ruff, mypy)
  - Testing requirements (≥80% coverage)
  - Pull request process
  - Issue reporting guidelines

- [ ] **Task 97**: Update all docstrings
  - Ensure all functions have comprehensive docstrings
  - Include Args, Returns, Raises sections
  - Add usage examples where helpful
  - Verify docstring format consistency

- [ ] **Task 98**: Final validation checklist
  - All 100 tasks completed
  - All tests passing (pytest)
  - Coverage ≥80% (pytest --cov)
  - Type checking passing (mypy)
  - Linting passing (ruff)
  - Server starts successfully
  - All 8 tools registered and functional

- [ ] **Task 99**: Create release preparation
  - Tag v0.1.0 release
  - Generate release notes from CHANGELOG
  - Package distribution (future: PyPI)
  - Announce MVP completion

- [ ] **Task 100**: Post-implementation review
  - Review all 20 specifications for compliance
  - Identify any deviations or improvements
  - Document lessons learned
  - Plan Phase 2 (v0.2.0 persistence features)

---

## Success Criteria

**Implementation is complete when**:

1. ✅ All 100 tasks checked off
2. ✅ All 8 MVP tools functional and tested
3. ✅ Database loaded successfully (33,978+ compounds, 43,775+ reactions)
4. ✅ Templates loaded successfully (GramNegative, GramPositive, Core minimum)
5. ✅ Session storage working with .gf suffix notation
6. ✅ All tests passing with ≥80% coverage
7. ✅ Server starts in <5 seconds
8. ✅ Complete workflow functional: build → gapfill → FBA
9. ✅ Documentation complete (README, examples, deployment guide)
10. ✅ All 20 specifications implemented correctly

---

## Key Implementation Notes

### Critical Requirements
- **Python 3.11 ONLY**: Do not use Python 3.12+ (missing distutils breaks scikit-learn dependency)
- **ModelSEEDpy Fork**: Must use `git+https://github.com/Fxe/ModelSEEDpy.git@dev` (not official repo)
- **Model ID Notation**: Use `.gf` suffix format (e.g., `model.draft`, `model.draft.gf`) NOT underscore
- **JSON-RPC 2.0**: All errors must be compliant with MCP protocol
- **Test Coverage**: Maintain ≥80% coverage at all times

### Architecture Patterns
- **Session-based storage**: In-memory dicts, cleared on restart (MVP)
- **State suffix transformations**: `.draft` → `.draft.gf` → `.draft.gf.gf`
- **Original model preservation**: Gapfilling creates new model, keeps original
- **Database O(1) lookups**: Indexed pandas DataFrames
- **FastMCP tool registration**: Use `@mcp.tool()` decorator with type hints

### Testing Strategy
- **Test-first development**: Write tests before implementation
- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test complete workflows end-to-end
- **Mock external dependencies**: Mock ModelSEEDpy, COBRApy in tests
- **Test expectations**: Define must_pass vs may_fail tests

---

**Plan Status**: ✅ Ready for Implementation
**Next Step**: Begin Phase 1, Task 1 - Create project package structure

