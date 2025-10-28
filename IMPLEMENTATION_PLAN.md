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

- [x] **Task 7**: Create logging infrastructure
  - Create `src/gem_flux_mcp/logging.py` module
  - Configure log levels (DEBUG, INFO, WARNING, ERROR)
  - Set up console and file logging handlers
  - Write unit tests for logging (tests/unit/test_logging.py)
  - Test logging output and verify coverage ≥80% (achieved 100%)

- [x] **Task 8**: Create error handling module
  - Create `src/gem_flux_mcp/errors.py`
  - Define custom exceptions (ValidationError, NotFoundError, InfeasibilityError, LibraryError, DatabaseError, ServerError, TimeoutError)
  - Define JSON-RPC 2.0 compliant error responses with build_error_response()
  - Add common error constructors (model_not_found_error, media_not_found_error, etc.)
  - Write comprehensive unit tests (45 tests, 100% coverage)

- [x] **Task 9**: Create data types module
  - Create `src/gem_flux_mcp/types.py`
  - Define Pydantic models for all core MCP tools (build_media, build_model, gapfill_model, run_fba)
  - Define models for database lookup tools (compound/reaction search and lookup)
  - Define error response types
  - Write comprehensive unit tests (37 tests, 99.18% coverage)
  - All validation logic working correctly

- [x] **Task 10**: Write unit tests for infrastructure
  - Test logging configuration (43 tests, 100% coverage - test_logging.py)
  - Test error response formatting (45 tests, 100% coverage - test_errors.py)
  - Test data type validation (37 tests, 99.18% coverage - test_types.py)
  - Verify 100% coverage for infrastructure (✅ 99.41% total coverage achieved)

---

### Phase 2: Database & Templates

- [x] **Task 11**: Implement database loader module
  - Create `src/gem_flux_mcp/database/loader.py` (103 lines, 85.44% coverage)
  - Implement `load_compounds_database()` function (pandas TSV reader with validation)
  - Implement `load_reactions_database()` function (pandas TSV reader with validation)
  - Add validation for required columns (9 compound cols, 11 reaction cols)
  - Handle missing/corrupted files with clear DatabaseError messages
  - Implement `parse_aliases()` function for structured alias dictionaries
  - Implement `validate_compound_id()` and `validate_reaction_id()` functions
  - 32 comprehensive unit tests, all passing

- [x] **Task 12**: Implement database indexing
  - Create `src/gem_flux_mcp/database/index.py` module (291 lines, 100% coverage)
  - Implement `DatabaseIndex` class with O(1) primary lookups (by ID)
  - Add secondary search methods: by name, abbreviation, EC numbers
  - Create lowercase columns for case-insensitive searching
  - Implement existence checks: `compound_exists()`, `reaction_exists()`
  - Performance verified: <1ms per lookup (tested with 1000 lookups < 1s)
  - 37 comprehensive unit tests, all passing (test_database_index.py)

- [x] **Task 13**: Implement alias parsing
  - ✅ Already implemented in `loader.py`: `parse_aliases()` function
  - Parses pipe-separated aliases: `"KEGG: C00031|BiGG: glc__D"`
  - Handles semicolon-separated multiple IDs: `"BiGG: id1;id2"`
  - Returns structured dict: `{"KEGG": ["C00031"], "BiGG": ["glc__D"]}`
  - Handles malformed aliases gracefully (skip, continue)
  - Tested in test_database_loader.py (10 alias parsing tests)

- [x] **Task 14**: Implement compound ID validation
  - ✅ Already implemented in `loader.py`: `validate_compound_id()` function
  - Validates format: `cpd\d{5}` regex pattern
  - Returns tuple: (is_valid, error_message)
  - Used during database loading for validation
  - Tested in test_database_loader.py (3 validation tests)

- [x] **Task 15**: Implement reaction ID validation
  - ✅ Already implemented in `loader.py`: `validate_reaction_id()` function
  - Validates format: `rxn\d{5}` regex pattern
  - Returns tuple: (is_valid, error_message)
  - Used during database loading for validation
  - Tested in test_database_loader.py (3 validation tests)

- [x] **Task 16**: Write database loader unit tests
  - ✅ Already implemented in test_database_loader.py (32 tests, all passing)
  - Tests successful database loading (compounds & reactions)
  - Tests handling of missing files (DatabaseError)
  - Tests handling of corrupted TSV (parse errors)
  - Tests validation of row counts (>30k compounds, >35k reactions)
  - Tests alias parsing with various formats (10 tests)
  - Tests ID validation (invalid formats, duplicates)
  - Coverage: 85.44% for loader.py

- [x] **Task 17**: Implement template loader module
  - Create `src/gem_flux_mcp/templates/loader.py` (66 lines, 95.45% coverage)
  - Implement `load_template()` function (reads JSON, uses MSTemplateBuilder)
  - Implement `load_templates()` for startup (loads all templates, updates cache)
  - Implement `get_template()` for O(1) runtime access
  - Implement `validate_template_name()` and `list_available_templates()`
  - Store in dict: `{"GramNegative": MSTemplate, ...}` via TEMPLATE_CACHE global
  - Log template statistics (reaction counts, load time)
  - 20 comprehensive unit tests, all passing (test_template_loader.py)

- [x] **Task 18**: Implement template validation
  - ✅ Implemented `validate_template()` function in loader.py
  - ✅ Verifies template has reactions, metabolites, compartments (non-empty)
  - ✅ Logs template statistics at DEBUG level (reaction count, metabolite count, compartments)
  - ✅ Integrated into `load_template()` - validation runs after template build
  - ✅ Raises DatabaseError with specific error codes (INVALID_TEMPLATE_NO_REACTIONS, etc.)
  - ✅ 11 comprehensive tests added to test_template_loader.py (all passing)
  - ✅ Coverage: 96% for loader.py (75 statements, 3 missed)

- [x] **Task 19**: Implement ATP gapfill media loading
  - ✅ Created `src/gem_flux_mcp/media/atp_loader.py` module
  - ✅ Implemented `load_atp_media()` function calling ModelSEEDpy's `load_default_medias()`
  - ✅ Returns list of tuples: [(MSMedia, min_objective), ...]
  - ✅ Stores 54 media compositions in ATP_MEDIA_CACHE global
  - ✅ Graceful error handling: FileNotFoundError and generic Exception caught
  - ✅ Non-fatal failures: logs warning and returns empty list (ATP correction can be skipped)
  - ✅ Logs success message with media count
  - ✅ Helper functions: `get_atp_media()`, `has_atp_media()`, `get_atp_media_info()`
  - ✅ 16 comprehensive unit tests in tests/unit/test_atp_media_loader.py (all passing)
  - ✅ Coverage: 100% for atp_loader.py (30 statements, 0 missed)
  - ✅ Full test suite: 241 tests passing, 96.72% coverage

- [x] **Task 20**: Write template loader unit tests
  - ✅ 32 comprehensive unit tests in tests/unit/test_template_loader.py (31 passing, 1 skipped)
  - ✅ Coverage: 96% for templates/loader.py (75 statements, 3 missed)
  - ✅ Tests cover: validate_template, load_template, load_templates, get_template, validate_template_name, list_available_templates
  - ✅ All error cases tested: missing files, invalid JSON, build failures, validation failures
  - ✅ MSTemplateBuilder properly mocked for unit testing

---

### Phase 3: Session Storage

- [x] **Task 21**: Implement model storage module
  - ✅ Created `src/gem_flux_mcp/storage/models.py` (84 statements, 96.43% coverage)
  - ✅ Implemented in-memory dict storage: `MODEL_STORAGE: dict[str, Any] = {}`
  - ✅ Implemented `store_model(model_id, model)` function with collision detection
  - ✅ Implemented `retrieve_model(model_id)` function with error handling
  - ✅ Implemented `list_model_ids()` function (sorted alphabetically)
  - ✅ Implemented `model_exists()`, `delete_model()`, `clear_all_models()`, `get_model_count()` helper functions
  - ✅ Implemented `generate_model_id(state)` for auto-generated IDs
  - ✅ Implemented `generate_model_id_from_name()` with collision handling
  - ✅ Implemented `transform_state_suffix()` for gapfilling state transitions
  - ✅ Added `storage_collision_error()` to errors.py
  - ✅ 38 comprehensive unit tests in tests/unit/test_model_storage.py (all passing)
  - ✅ Full test suite: 279 tests passing, 96.71% coverage

- [x] **Task 22**: Implement model ID generation
  - ✅ Already implemented in Task 21 (`src/gem_flux_mcp/storage/models.py` lines 23-42)
  - ✅ Implemented `generate_model_id(state="draft")` function
  - ✅ Format: `model_{timestamp}_{random}.{state}`
  - ✅ Example: `model_20251027_143052_a3f9b2.draft`
  - ✅ Ensures uniqueness with timestamp + random suffix

- [x] **Task 23**: Implement user-provided model ID handling
  - ✅ Already implemented in Task 21 (`src/gem_flux_mcp/storage/models.py` lines 45-100)
  - ✅ Implemented `generate_model_id_from_name(name, state, existing_ids)` function
  - ✅ Checks for collisions with existing model IDs
  - ✅ Appends timestamp + microseconds if collision: `E_coli_K12_20251027_143052_123456.draft`
  - ✅ Preserves user's custom name when possible
  - ✅ Max retries with exponential backoff for collision resolution

- [x] **Task 24**: Implement state suffix transformation
  - ✅ Already implemented in Task 21 (`src/gem_flux_mcp/storage/models.py` lines 103-149)
  - ✅ Implemented `transform_state_suffix(model_id)` function
  - ✅ Transforms `.draft` → `.draft.gf`
  - ✅ Transforms `.gf` → `.gf.gf`
  - ✅ Transforms `.draft.gf` → `.draft.gf.gf`
  - ✅ Preserves base name during transformation

- [x] **Task 25**: Implement media storage module
  - ✅ Created `src/gem_flux_mcp/storage/media.py` (50 statements, 100% coverage)
  - ✅ Implemented in-memory dict storage: `MEDIA_STORAGE: dict[str, Any] = {}`
  - ✅ Implemented `store_media(media_id, media)` function with collision detection
  - ✅ Implemented `retrieve_media(media_id)` function with error handling
  - ✅ Implemented `list_media_ids()` function (sorted alphabetically)
  - ✅ Implemented `media_exists()`, `delete_media()`, `clear_all_media()`, `get_media_count()` helper functions

- [x] **Task 26**: Implement media ID generation
  - ✅ Implemented `generate_media_id()` function
  - ✅ Format: `media_{timestamp}_{random}`
  - ✅ Example: `media_20251027_143052_x1y2z3`
  - ✅ Ensures uniqueness with timestamp + random suffix
  - ✅ 36 comprehensive unit tests in tests/unit/test_media_storage.py (all passing)
  - ✅ Full test suite: 315 tests passing, 96.93% coverage

- [x] **Task 27**: Implement storage error handling
  - ✅ Already implemented in Task 8 (`src/gem_flux_mcp/errors.py`)
  - ✅ Defined `model_not_found_error()` with available models list (lines 298-325)
  - ✅ Defined `media_not_found_error()` with available media list (lines 327-354)
  - ✅ Defined `storage_collision_error()` for retry exhaustion (lines 534-558)
  - ✅ All error functions include helpful suggestions and detailed context
  - ✅ Used by storage modules for consistent error responses

- [x] **Task 28**: Implement session storage initialization
  - Initialize empty storage dicts on server startup
  - Set up ID generation counters
  - Configure storage limits (100 models, 50 media for MVP)
  - Log initialization complete

- [x] **Task 29**: Implement storage cleanup on shutdown
  - Clear all models from storage
  - Clear all media from storage
  - Log storage statistics before clearing
  - Free memory (Python garbage collection)

- [x] **Task 30**: Write storage unit tests
  - Test model storage and retrieval
  - Test media storage and retrieval
  - Test model ID generation (auto and user-provided)
  - Test state suffix transformation
  - Test collision handling
  - Test ModelNotFoundError and MediaNotFoundError

---

### Phase 4: Database Lookup Tools

- [x] **Task 31**: Implement get_compound_name tool
  - Create `src/gem_flux_mcp/tools/compound_lookup.py` ✓
  - Input: `{"compound_id": "cpd00027"}` ✓
  - Validate compound_id format and existence ✓
  - Query database for compound record ✓
  - Parse aliases into structured dict ✓
  - Return: name, abbreviation, formula, mass, charge, inchikey, smiles, aliases ✓
  - Unit tests: tests/unit/test_get_compound_name.py (14 tests, 100% coverage) ✓

- [x] **Task 32**: Implement search_compounds tool
  - Added to `src/gem_flux_mcp/tools/compound_lookup.py` ✓
  - Input: `{"query": "glucose", "limit": 10}` ✓
  - Search in order: exact ID, exact name, exact abbreviation, partial name, formula, aliases ✓
  - Priority-based ranking: exact matches first (1-3), then partial (4-6) ✓
  - Alphabetical sorting within same priority level ✓
  - Duplicate removal (keep highest priority match) ✓
  - Return: list of compound objects with match_field and match_type ✓
  - Truncation flag when more results exist beyond limit ✓
  - Suggestions included when no results found ✓
  - Unit tests: tests/unit/test_search_compounds.py (26 tests, 100% coverage) ✓
  - Full test suite: 386 passed, 97.57% coverage ✓

- [x] **Task 33**: Implement get_reaction_name tool
  - ✅ Created `src/gem_flux_mcp/tools/reaction_lookup.py` (130 statements, 90.77% coverage)
  - ✅ Implemented `GetReactionNameRequest` and `GetReactionNameResponse` models
  - ✅ Implemented `get_reaction_name()` function with O(1) database lookup
  - ✅ Implemented helper functions: `parse_reversibility_and_direction()`, `parse_ec_numbers()`, `parse_pathways()`, `format_equation_readable()`
  - ✅ Parses equation with IDs and human-readable names
  - ✅ Parses reversibility symbols (>, <, =) to readable strings
  - ✅ Parses EC numbers, pathways (with database prefix removal), aliases
  - ✅ Returns complete metadata: name, abbreviation, equation, equation_with_ids, reversibility, direction, is_transport, ec_numbers, pathways, deltag, deltagerr, aliases
  - ✅ 32 comprehensive unit tests in tests/unit/test_get_reaction_name.py (all passing)
  - ✅ Full test suite: 418 tests passing (386 + 32 new), 97.57% coverage

- [x] **Task 34**: Implement search_reactions tool
  - ✅ Added to `src/gem_flux_mcp/tools/reaction_lookup.py` (222 statements, 94.59% coverage)
  - ✅ Implemented `SearchReactionsRequest` and `SearchReactionsResponse` models
  - ✅ Implemented `ReactionSearchResult` model for individual search results
  - ✅ Implemented `search_reactions()` function with priority-based matching (O(n) linear search)
  - ✅ Search priority order: exact ID → exact name → exact abbreviation → EC number → partial name → aliases → pathways
  - ✅ Duplicate removal keeps highest priority match only
  - ✅ Alphabetical sorting within same priority level
  - ✅ Truncation flag when more results exist beyond limit
  - ✅ Suggestions included when no results found
  - ✅ Results include formatted equation and parsed EC numbers
  - ✅ 25 comprehensive unit tests in tests/unit/test_search_reactions.py (all passing)
  - ✅ Fixed DatabaseIndex to handle empty DataFrames (added empty check before .str operations)
  - ✅ Full test suite: 443 tests passing (418 + 25 new), 97.02% coverage

- [x] **Task 35**: Implement equation formatting
  - ✅ Implemented `format_equation_readable()` in `reaction_lookup.py` (lines 301-328)
  - ✅ Parses database equation with compound IDs
  - ✅ Parses database definition with compound names
  - ✅ Removes compartment suffixes `[0]`, `[c0]`, `[e0]`, `[p0]` for readability
  - ✅ Format: `"(1) D-Glucose + (1) ATP => (1) ADP + (1) H+ + (1) D-Glucose-6-phosphate"`
  - ✅ 3 comprehensive unit tests (test_format_equation_readable*)

- [x] **Task 36**: Implement pathway parsing
  - ✅ Implemented `parse_pathways()` in `reaction_lookup.py` (lines 226-298)
  - ✅ Parses pipe-separated pathways: `"MetaCyc: Glycolysis|KEGG: rn00010"`
  - ✅ Extracts pathway names, removes database prefixes like "MetaCyc:", "KEGG:"
  - ✅ Handles descriptive text in parentheses
  - ✅ Returns array: `["Glycolysis", "Glycolysis / Gluconeogenesis"]`
  - ✅ 5 comprehensive unit tests (test_parse_pathways*)

- [x] **Task 37**: Write unit tests for get_compound_name
  - ✅ 14 comprehensive unit tests in tests/unit/test_get_compound_name.py
  - ✅ Test successful compound lookup (cpd00027 → D-Glucose, cpd00001 → H2O, cpd00002 → ATP)
  - ✅ Test compound not found error
  - ✅ Test invalid format errors (too short, wrong prefix, letters in ID)
  - ✅ Test alias parsing
  - ✅ Test case-insensitive lookup
  - ✅ Test whitespace trimming
  - ✅ Test performance (<1ms per lookup with 1000 lookups)
  - ✅ All tests passing, 100% coverage for tool

- [x] **Task 38**: Write unit tests for search_compounds
  - ✅ 26 comprehensive unit tests in tests/unit/test_search_compounds.py
  - ✅ Test exact name match (exact ID, exact name, exact abbreviation)
  - ✅ Test partial name match
  - ✅ Test formula search
  - ✅ Test alias search
  - ✅ Test empty results with suggestions
  - ✅ Test limit parameter (default 10, max 100, validation)
  - ✅ Test priority ordering (exact matches before partial)
  - ✅ Test duplicate removal
  - ✅ Test truncation flag
  - ✅ Test query trimming and case-insensitive matching
  - ✅ All tests passing, 100% coverage for tool

- [x] **Task 39**: Write unit tests for get_reaction_name
  - ✅ 32 comprehensive unit tests in tests/unit/test_get_reaction_name.py
  - ✅ Test successful reaction lookup (rxn00148 → hexokinase)
  - ✅ Test reaction not found error
  - ✅ Test equation formatting (3 tests: test_format_equation_readable*)
  - ✅ Test reversibility parsing (4 tests: forward, reverse, bidirectional, unknown)
  - ✅ Test EC number parsing (4 tests: single, multiple semicolon, multiple pipe, empty)
  - ✅ Test pathway parsing (5 tests: simple, semicolon, database prefix, description, empty)
  - ✅ Test transport reactions
  - ✅ Test thermodynamic data (deltag, deltagerr)
  - ✅ Test multiple pathways and complex pathway strings
  - ✅ All tests passing, 90.77% coverage for tool

- [x] **Task 40**: Write unit tests for search_reactions
  - ✅ 25 comprehensive unit tests in tests/unit/test_search_reactions.py
  - ✅ Test exact name match (exact ID, exact name, exact abbreviation)
  - ✅ Test EC number search
  - ✅ Test pathway search
  - ✅ Test alias search
  - ✅ Test partial name match
  - ✅ Test empty results with suggestions
  - ✅ Test limit parameter (default 10, validation)
  - ✅ Test priority ordering (7 priority levels)
  - ✅ Test duplicate removal (keeps highest priority match)
  - ✅ Test truncation flag
  - ✅ Test equation formatting in results
  - ✅ Test EC number parsing in results
  - ✅ Test alphabetical sorting within same priority
  - ✅ All tests passing, 94.59% coverage for tool

---

### Phase 5: Core MCP Tools - Part 1

- [x] **Task 41**: Implement build_media tool
  - Create `src/gem_flux_mcp/tools/media_builder.py`
  - Input: `{"compounds": ["cpd00027", ...], "default_uptake": 100.0, "custom_bounds": {...}}`
  - Validate all compound IDs exist in database
  - Apply default bounds: `(-default_uptake, 100.0)`
  - Override with custom_bounds for specific compounds
  - Create MSMedia object placeholder (full integration next iteration)
  - Generate media_id
  - Store in session storage
  - Enrich response with compound names from database
  - Return: media_id, compounds with names, num_compounds, media_type

- [x] **Task 42**: Implement build_media validation
  - Validate compounds list not empty
  - Validate all compound IDs match format `cpd\d{5}`
  - Validate all compound IDs exist in database
  - Validate default_uptake is positive
  - Validate custom_bounds have lower <= upper (allow equal for blocked exchange)
  - Validate no duplicate compound IDs
  - Return ValidationError with ALL invalid IDs

- [x] **Task 43**: Implement media classification heuristic
  - If num_compounds < 50: "minimal" media
  - If num_compounds >= 50: "rich" media
  - Return media_type in response

- [x] **Task 44**: Write unit tests for build_media
  - Test successful media creation (glucose minimal media)
  - Test invalid compound IDs error
  - Test empty compounds list error
  - Test invalid bounds error
  - Test custom_bounds override default

- [x] **Task 45**: Implement build_model tool (FASTA input)
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

- [x] **Task 46**: Implement build_model tool (dict input)
  - Handle `protein_sequences` dict input
  - Validate all amino acid sequences contain only valid characters: `[ACDEFGHIKLMNPQRSTVWY]`
  - Convert dict to temporary .faa file for RAST (if annotate_with_rast=true)
  - Create MSGenome from dict (without RAST if offline mode)
  - Rest follows same flow as FASTA input

- [x] **Task 47**: Implement protein sequence validation
  - Validate non-empty protein_sequences dict OR fasta_file_path (not both)
  - Validate amino acid alphabet: `ACDEFGHIKLMNPQRSTVWY`
  - Report ALL invalid sequences (don't stop at first)
  - Validate no empty sequences
  - Validate no duplicate protein IDs

- [x] **Task 48**: Implement RAST annotation integration
  - If `annotate_with_rast=true`: submit .faa to RAST API
  - Handle RAST network errors gracefully
  - Use RAST results to create MSGenome with functional annotations
  - If `annotate_with_rast=false`: offline template matching only
  - Document RAST vs offline tradeoffs

- [x] **Task 49**: Implement model statistics collection
  - Count total reactions, metabolites, genes
  - Break down reactions by compartment
  - Count exchange reactions (EX_ prefix)
  - Count reversible vs irreversible reactions
  - Identify transport reactions
  - Set `is_draft=true`, `requires_gapfilling=true`

- [x] **Task 50**: Write unit tests for build_model
  - Test successful model building from dict
  - Test successful model building from FASTA
  - Test invalid amino acid sequences error
  - Test invalid template error
  - Test empty protein sequences error
  - Test both inputs provided error
  - Mock MSBuilder, MSGenome for testing

---

### Phase 6: Core MCP Tools - Part 2

- [x] **Task 51**: Implement gapfill_model tool ✓
  - ✅ Created `src/gem_flux_mcp/tools/gapfill_model.py` (187 statements)
  - ✅ Input validation: model_id, media_id, target_growth_rate, gapfill_mode
  - ✅ Load model and media from session storage
  - ✅ Create copy of model (preserve original with deepcopy)
  - ✅ Run ATP correction (MSATPCorrection with default media)
  - ✅ Run genome-scale gapfilling (MSGapfill)
  - ✅ Integrate gapfilling solutions into model
  - ✅ Transform model_id state suffix (`.draft` → `.draft.gf`)
  - ✅ Store gapfilled model with new model_id
  - ✅ Return: new model_id, reactions_added, growth_rate_before/after, statistics
  - ✅ Accepts db_index parameter for reaction metadata enrichment
  - ✅ 20 comprehensive unit tests (100% passing)

- [x] **Task 52**: Implement ATP correction stage ✓
  - ✅ Load default ATP test media (54 media via load_default_medias())
  - ✅ Create MSATPCorrection object with Core template
  - ✅ Run `evaluate_growth_media()` to test all media
  - ✅ Run `determine_growth_media()` to identify failures
  - ✅ Run `apply_growth_media_gapfilling()` to add reactions
  - ✅ Run `expand_model_to_genome_scale()` to add full template
  - ✅ Run `build_tests()` to create test conditions
  - ✅ Collect ATP correction statistics (media tested, passed, failed, reactions added)
  - ✅ Implemented in `run_atp_correction()` function

- [x] **Task 53**: Implement genome-scale gapfilling stage ✓
  - ✅ Create MSGapfill object with ATP-corrected model
  - ✅ Load genome-scale template (from model.notes['template_used'])
  - ✅ Set target media and growth rate
  - ✅ Run `run_gapfilling(media, target_growth_rate)`
  - ✅ Parse gapfilling solution: `{"reversed": {...}, "new": {...}}`
  - ✅ Integrate reactions into model via integrate_gapfill_solution()
  - ✅ Skip exchange reactions (handled separately by MSBuilder)
  - ✅ Verify final growth rate >= target
  - ✅ Implemented in `run_genome_scale_gapfilling()` function

- [x] **Task 54**: Implement gapfilling solution integration ✓
  - ✅ Parse direction symbols: `>` (forward), `<` (reverse), `=` (reversible)
  - ✅ Get reaction from template by ID (handle indexed _c0 → non-indexed _c)
  - ✅ Convert to COBRApy reaction via template_reaction.to_reaction()
  - ✅ Set bounds based on direction using get_reaction_constraints_from_direction()
  - ✅ Add to model with model.add_reactions()
  - ✅ Skip exchange reactions (EX_ prefix)
  - ✅ Implemented in `integrate_gapfill_solution()` function

- [x] **Task 55**: Implement gapfilling failure handling ✓
  - ✅ **Standalone failure**: Raise InfeasibilityError, preserve draft model
  - ✅ **Already meets target**: Create .gf model without gapfilling, return success
  - ✅ **Partial success**: Return with gapfilling_successful=false, note achieved growth
  - ✅ ATP correction failure (acceptable): Document failed media but continue
  - ✅ Genome-scale failure (error): Raise gapfill_infeasible_error with diagnostics
  - ✅ All error paths tested in unit tests
  - Include recovery suggestions in error response
  - Document failure scenarios in error details

- [x] **Task 56**: Enrich gapfilling response with reaction metadata ✓
  - ✅ Query database for reaction name and equation via db_index
  - ✅ Parse compartment from reaction ID (_c0, _e0, _p0)
  - ✅ Map direction symbols to readable strings (>, <, =)
  - ✅ Handle unknown reactions gracefully (name="Unknown reaction")
  - ✅ Build reactions_added array with full metadata
  - ✅ Implemented in `enrich_reaction_metadata()` function
  - ✅ 3 unit tests covering enrichment logic

- [x] **Task 57**: Write unit tests for gapfill_model ✓
  - ✅ Test successful gapfilling (draft → draft.gf) - full workflow test
  - ✅ Test already growing model (no gapfilling needed)
  - ✅ Test gapfilling validation errors
  - ✅ Test model not found error
  - ✅ Test media not found error
  - ✅ Test invalid target growth rate (negative, zero)
  - ✅ Test invalid gapfill_mode
  - ✅ Test no biomass reaction error
  - ✅ Test baseline growth check (optimal, infeasible, exception)
  - ✅ Test integrate_gapfill_solution (empty, new reactions, skip exchanges)
  - ✅ Test enrich_reaction_metadata (success, unknown, direction mapping)
  - ✅ 20 comprehensive unit tests in tests/unit/test_gapfill_model.py
  - ✅ 100% test pass rate

- [x] **Task 58**: Implement run_fba tool
  - ✅ Created `src/gem_flux_mcp/tools/run_fba.py`
  - ✅ Input: `{"model_id": "model_abc.draft.gf", "media_id": "media_001", "objective": "bio1", "maximize": true, "flux_threshold": 1e-6}`
  - ✅ Validate model_id and media_id exist
  - ✅ Load model and media from session storage
  - ✅ Create temporary copy of model (preserve original)
  - ✅ Apply media constraints to exchange reactions
  - ✅ Set objective function (with minimization support)
  - ✅ Run FBA: `solution = model.optimize()`
  - ✅ Extract fluxes, filter by threshold
  - ✅ Separate uptake/secretion fluxes
  - ✅ Enrich with compound/reaction names
  - ✅ Return: objective_value, status, fluxes, uptake_fluxes, secretion_fluxes, top_fluxes, summary
  - ✅ Handle infeasible and unbounded models
  - ✅ 95.33% test coverage

- [x] **Task 59**: Implement media application to model
  - ✅ Get media bounds from dict format (MVP implementation)
  - ✅ Map compound IDs to exchange reaction IDs: `cpd00027` → `EX_cpd00027_e0`
  - ✅ Set uptake bounds (COBRApy uses positive values for uptake)
  - ✅ Apply medium: `model.medium = medium`
  - ✅ Verify all media compounds have exchange reactions
  - ✅ Log warnings for missing exchange reactions

- [x] **Task 60**: Write unit tests for run_fba
  - ✅ Test successful FBA (optimal solution)
  - ✅ Test infeasible model error
  - ✅ Test unbounded model error
  - ✅ Test model not found error
  - ✅ Test media not found error
  - ✅ Test flux threshold filtering
  - ✅ Test minimize vs maximize
  - ✅ Test invalid objective
  - ✅ Test model preservation (deepcopy)
  - ✅ Mock COBRApy model.optimize() for testing
  - ✅ 20 comprehensive unit tests in tests/unit/test_run_fba.py
  - ✅ 100% test pass rate

---

### Phase 7: Session Management Tools

- [x] **Task 61**: Implement list_models tool
  - ✅ Created `src/gem_flux_mcp/tools/list_models.py`
  - ✅ Input: `{"filter_state": "all"}`  # "all", "draft", "gapfilled"
  - ✅ Query MODEL_STORAGE for all models
  - ✅ Extract metadata from each COBRApy Model object
  - ✅ Determine state from model_id suffix
  - ✅ Apply filter if specified
  - ✅ Sort by created_at timestamp (oldest first)
  - ✅ Return: models array, total_models, models_by_state

- [x] **Task 62**: Implement state classification
  - ✅ Implemented classify_model_state() function
  - ✅ `.draft` → state: "draft"
  - ✅ `.gf` or `.draft.gf` or any suffix containing `.gf` → state: "gapfilled"
  - ✅ Include in model metadata

- [x] **Task 63**: Implement delete_model tool
  - ✅ Created `src/gem_flux_mcp/tools/delete_model.py`
  - ✅ Input: `{"model_id": "model_abc.draft"}`
  - ✅ Validate model_id exists in storage
  - ✅ Remove from MODEL_STORAGE dictionary
  - ✅ Memory freed automatically (Python GC)
  - ✅ Return: success, deleted_model_id

- [x] **Task 64**: Implement list_media tool
  - ✅ Created `src/gem_flux_mcp/tools/list_media.py`
  - ✅ Input: `{}` (no parameters)
  - ✅ Query MEDIA_STORAGE for all media
  - ✅ Extract metadata from each MSMedia object
  - ✅ Get first 3 compounds for preview
  - ✅ Sort by created_at timestamp
  - ✅ Count predefined vs user-created media
  - ✅ Return: media array, total_media, predefined_media, user_created_media

- [x] **Task 65**: Write unit tests for list_models
  - ✅ 19 comprehensive unit tests in tests/unit/test_list_models.py
  - ✅ Test listing all models
  - ✅ Test filtering by state (draft, gapfilled)
  - ✅ Test empty storage
  - ✅ Test sorting by timestamp
  - ✅ Test helper functions (classify_model_state, extract_model_name, extract_model_metadata)
  - ✅ Test case-insensitive filter
  - ✅ All tests passing

- [x] **Task 66**: Write unit tests for delete_model
  - ✅ 11 comprehensive unit tests in tests/unit/test_delete_model_tool.py
  - ✅ Test successful deletion
  - ✅ Test model not found error
  - ✅ Test missing model_id parameter error
  - ✅ Test multiple models
  - ✅ Test deletion preserves other models
  - ✅ All tests passing

- [x] **Task 67**: Write unit tests for list_media
  - ✅ 19 comprehensive unit tests in tests/unit/test_list_media.py
  - ✅ Test listing all media
  - ✅ Test empty storage
  - ✅ Test compounds preview (first 3)
  - ✅ Test helper functions (extract_media_name, extract_media_metadata)
  - ✅ Test predefined media handling
  - ✅ Test minimal vs rich classification
  - ✅ All tests passing

- [x] **Task 68**: Implement predefined media library
  - ✅ Created `data/media/` directory with README.md documentation
  - ✅ Created 4 predefined media JSON files (18 & 17 compounds each):
    - `glucose_minimal_aerobic.json` - 18 compounds
    - `glucose_minimal_anaerobic.json` - 17 compounds (no O2)
    - `pyruvate_minimal_aerobic.json` - 18 compounds (pyruvate as carbon source)
    - `pyruvate_minimal_anaerobic.json` - 17 compounds (pyruvate, no O2)
  - ✅ Implemented `load_predefined_media()` function in `src/gem_flux_mcp/media/predefined_loader.py`
  - ✅ Implemented helper functions: `get_predefined_media()`, `has_predefined_media()`, `list_predefined_media_names()`, `get_predefined_media_count()`
  - ✅ Added `is_predefined` field to `MediaInfo` type
  - ✅ Updated `list_media` tool to set `is_predefined` flag
  - ✅ Predefined media stored with fixed names (e.g., "glucose_minimal_aerobic")
  - ✅ 18 comprehensive unit tests in `tests/unit/test_predefined_media_loader.py` (95% coverage, all passing)
  - ✅ All 4 media files load successfully (verified with loader test)
  - ✅ Full test suite: 619 tests passing, 91.47% coverage

- [x] **Task 69**: Write integration tests for session management
  - ✅ Created `tests/integration/test_phase10_session_management.py` with 8 tests
  - ✅ **test_list_models** (must_pass): Tests listing models with filtering by state
  - ✅ **test_list_media** (must_pass): Tests listing media with predefined/user-created counts
  - ✅ **test_delete_model** (must_pass): Tests deleting models and error handling
  - ✅ **test_session_isolation** (must_pass): Tests session-scoped storage independence
  - ✅ test_list_models_with_user_named_models: Tests user-provided model names
  - ✅ test_list_models_chronological_sorting: Tests sorting by created_at timestamp
  - ✅ test_delete_model_workflow_integration: Complete workflow (build → gapfill → list → delete)
  - ✅ test_media_classification: Tests minimal vs rich media classification
  - ✅ All 4 must-pass tests passing (as defined in test_expectations.json Phase 10)
  - ✅ All 8 tests passing with comprehensive coverage of session management tools

- [x] **Task 70**: Document session lifecycle
  - ✅ Created comprehensive `docs/SESSION_LIFECYCLE.md` (490 lines)
  - ✅ Documented model lifecycle: Creation → Modification → Analysis → Deletion → Session End
  - ✅ Documented media lifecycle: Creation → Usage → Session End
  - ✅ Documented ID generation patterns (auto-generated and user-provided)
  - ✅ Documented state suffix transformations (`.draft` → `.draft.gf`, etc.)
  - ✅ Documented storage architecture and operations
  - ✅ Documented complete workflow example
  - ✅ Documented error scenarios (ModelNotFoundError, MediaNotFoundError, StorageCollisionError)
  - ✅ Documented best practices for users and developers
  - ✅ Documented future enhancements (v0.2.0+: persistent storage, multi-user sessions)

---

### Phase 8: MCP Server Setup

- [x] **Task 71**: Implement FastMCP server initialization
  - Create `src/gem_flux_mcp/server.py`
  - Import FastMCP framework
  - Create MCP server instance: `mcp = FastMCP("gem-flux-mcp")`
  - Set server metadata (name, version, description)
  - Set protocol_version: "2025-06-18" (latest MCP protocol)
  - Configure capabilities: tools=True, resources=False, prompts=False, logging=True

- [x] **Task 72**: Implement resource loading on startup
  - Phase 1: Load ModelSEED database (compounds.tsv, reactions.tsv)
  - Phase 2: Load ModelSEED templates (GramNegative, GramPositive, Core)
  - Phase 3: Load ATP gapfilling media (54 default media)
  - Phase 4: Load predefined media library (4 media)
  - Log loading statistics and timing
  - Exit with error if critical resources fail to load

- [x] **Task 73**: Implement tool registration with FastMCP
  - Register all 8 MVP tools using `@mcp.tool()` decorator
  - Tools: build_media, build_model, gapfill_model, run_fba, get_compound_name, get_reaction_name, search_compounds, search_reactions
  - Add session management tools: list_models, delete_model, list_media
  - Use type hints for automatic schema generation
  - Document each tool with comprehensive docstrings
  - Log tool registration statistics

- [x] **Task 74**: Implement session storage initialization
  - Initialize empty MODEL_STORAGE dict
  - Initialize empty MEDIA_STORAGE dict
  - Set up ID generation (timestamp + random)
  - Configure storage limits (100 models, 50 media)
  - Log initialization complete

- [x] **Task 75**: Implement server startup sequence
  - Parse environment variables for configuration
  - Initialize logging (console + file)
  - Load database, templates, media
  - Initialize session storage
  - Register tools
  - Bind to host:port (default: localhost:8080)
  - Log "Server ready" message

- [x] **Task 76**: Implement graceful shutdown
  - Handle SIGINT, SIGTERM signals
  - Stop accepting new requests
  - Wait for active requests to complete (timeout: 30s)
  - Clear session storage (models, media)
  - Log shutdown statistics
  - Exit with code 0

- [x] **Task 77**: Implement configuration via environment variables
  - `GEM_FLUX_HOST`: Host to bind (default: localhost)
  - `GEM_FLUX_PORT`: Port to listen (default: 8080)
  - `GEM_FLUX_DATABASE_DIR`: Database location (default: ./data/database)
  - `GEM_FLUX_TEMPLATE_DIR`: Template location (default: ./data/templates)
  - `GEM_FLUX_LOG_LEVEL`: Log level (default: INFO)
  - `GEM_FLUX_LOG_FILE`: Log file path (default: ./gem-flux.log)

- [x] **Task 78**: Implement server error handling
  - Startup errors: Database load failure, template load failure, port in use
  - Runtime errors: Tool execution failures, invalid MCP requests
  - Return JSON-RPC 2.0 compliant error responses
  - Log errors with context

- [x] **Task 79**: Write unit tests for server setup
  - Test successful server initialization
  - Test database loading failure
  - Test template loading failure
  - Test tool registration
  - Test graceful shutdown

- [x] **Task 80**: Create server startup script
  - Create `start-server.sh` with environment variable configuration
  - Create `pyproject.toml` script entry point
  - Document startup command: `uv run python -m gem_flux_mcp.server`
  - Test server starts and accepts requests

---

### Phase 9: Integration & Testing

- [x] **Task 81**: Write integration test: Complete workflow
  - Test: build_media → build_model → gapfill_model → run_fba
  - Verify model progresses through states: .draft → .draft.gf
  - Verify FBA returns optimal growth rate
  - Verify all intermediate results stored correctly
  - Implementation: tests/integration/test_phase11_complete_workflow.py
  - Tests: test_full_workflow_build_gapfill_fba, test_workflow_with_custom_media, test_end_to_end_error_handling

- [x] **Task 82**: Write integration test: Database lookups
  - ✅ Created `tests/integration/test_phase12_database_lookups.py` with 16 comprehensive tests
  - ✅ Test compound search → lookup workflow (search_compounds → get_compound_name)
  - ✅ Test reaction search → lookup workflow (search_reactions → get_reaction_name)
  - ✅ Test metadata enrichment (aliases, cross-references, equations)
  - ✅ Test performance (O(1) lookups)
  - ✅ Test error handling (not found, no results)
  - ✅ Test priority-based search ordering
  - ✅ Fixed bugs in compound_lookup.py and reaction_lookup.py (Series index vs compound["id"])
  - Note: Tests check dict responses (tools return model.model_dump())

- [x] **Task 83**: Write integration test: Session management
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

