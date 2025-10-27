# Phase 1 Preparation Plan - Gem-Flux MCP Server

**Status**: Analysis Complete - Awaiting User Approval to Execute
**Branch**: phase-1-implementation
**Date**: October 27, 2025

---

## Executive Summary

Before starting Phase 1 implementation, we need to:
1. **Reorganize data files** - Move database/template files from `specs-source/` to `data/`
2. **Set up implementation structure** - Copy template files to proper locations
3. **Configure UV virtual environment** - Handle ModelSEEDpy dev branch requirement
4. **Update specification references** - Ensure all specs point to correct data paths
5. **Create implementation plan** - Break down 20 specs into atomic implementation tasks

**Critical Issues Identified**:
- ✅ ModelSEED database files (50MB total) in wrong location
- ✅ Template JSON files (24MB total) in wrong location
- ✅ No UV/virtual environment configuration
- ✅ Implementation loop templates not copied to project
- ✅ Specifications reference old paths

---

## 1. Data File Reorganization

### Current State (INCORRECT)

```
specs-source/references/modelseed-database/
├── compounds.tsv                    # 12 MB - WRONG LOCATION
├── reactions.tsv                    # 37 MB - WRONG LOCATION
└── DATABASE_README.md

specs-source/build_metabolic_model/
├── Core-V5.2.json                  # 891 KB - WRONG LOCATION
├── GramNegModelTemplateV6.json     # 23 MB - WRONG LOCATION
└── build_model.ipynb
```

### Target State (CORRECT)

```
data/
├── database/                        # NEW: ModelSEED database
│   ├── compounds.tsv               # 12 MB - MOVE HERE
│   ├── reactions.tsv               # 37 MB - MOVE HERE
│   └── README.md                   # Document database structure
│
├── templates/                       # NEW: ModelSEED templates
│   ├── Core-V5.2.json             # 891 KB - MOVE HERE
│   ├── GramNegModelTemplateV6.json # 23 MB - MOVE HERE
│   └── README.md                   # Document template usage
│
└── media/                          # EXISTING: Predefined media
    ├── glucose_minimal_aerobic.json
    ├── glucose_minimal_anaerobic.json
    ├── pyruvate_minimal_aerobic.json
    ├── pyruvate_minimal_anaerobic.json
    └── README.md
```

### Rationale

**Why move to `data/`?**
1. Runtime files belong in `data/`, not `specs-source/`
2. `specs-source/` is for spec generation reference only
3. Server needs predictable paths: `./data/database/`, `./data/templates/`
4. Consistent with `data/media/` structure already in place
5. Specifications (007, 015, 017) expect files in `data/`

### Action Items

```bash
# Create new directories
mkdir -p data/database
mkdir -p data/templates

# Move database files (50 MB total)
mv specs-source/references/modelseed-database/compounds.tsv data/database/
mv specs-source/references/modelseed-database/reactions.tsv data/database/

# Move template files (24 MB total)
mv specs-source/build_metabolic_model/Core-V5.2.json data/templates/
mv specs-source/build_metabolic_model/GramNegModelTemplateV6.json data/templates/

# Create README files documenting structure
# (details in Section 6)
```

---

## 2. Specification Updates Required

### Files Referencing Data Paths

**specs/007-database-integration.md**
- Line ~50: Database file paths
- **Update**: Change from generic `./database/` to `./data/database/`
- **Verify**: Loading behavior section references correct paths

**specs/015-mcp-server-setup.md**
- Line ~84: `GEM_FLUX_DATABASE_DIR` environment variable
- Line ~85: `GEM_FLUX_TEMPLATE_DIR` environment variable
- **Update**: Default values should be `./data/database` and `./data/templates`

**specs/017-template-management.md**
- Template loading paths
- **Update**: Reference `./data/templates/` for JSON files

**specs/019-predefined-media-library.md**
- Line ~149-159: Media file locations
- **Status**: Already correct (`data/media/`)

### Update Strategy

1. Read each specification file
2. Search for path references
3. Update to new `data/` structure
4. Verify cross-references are consistent
5. Commit as single "chore: update data file paths in specifications"

---

## 3. Implementation Loop Template Files

### Current State

Templates are in: `docs/implementation-loop-development/to-use-later/`
- ✅ run-implementation-loop.sh (1,133 lines)
- ✅ CLAUDE.md (608 lines)
- ✅ conftest.py (729 lines)
- ✅ test_expectations.json (621 lines)
- ✅ context_relevance.py (589 lines)

### Target Locations (Per README.md)

```
gem-flux-mcp/
├── scripts/
│   └── development/
│       └── run-implementation-loop.sh    # COPY FROM to-use-later/
│
├── tests/
│   ├── conftest.py                       # ADAPT FROM to-use-later/
│   └── integration/
│       └── test_expectations.json        # CUSTOMIZE FROM to-use-later/
│
├── src/
│   └── utils/
│       └── context_relevance.py          # COPY FROM to-use-later/
│
└── CLAUDE.md                             # CUSTOMIZE FROM to-use-later/
```

### Customization Requirements

#### A. run-implementation-loop.sh

**Lines to Update:**
- Line 30-35: Set max iterations (suggest 50 for MVP)
- Line 138-166: Phase detection - adapt to our 20 specs
- Line 400-450: Context optimization - update critical specs list
- Line 755-870: Quality gates - adjust coverage threshold if needed

**Critical Specs for This Project** (context_relevance.py compatibility):
```python
self.critical_specs = [
    "001-system-overview.md",         # Always include
    "002-data-formats.md",            # Core data structures
    "013-error-handling.md",          # Error patterns
    "015-mcp-server-setup.md",        # Server configuration
]
```

#### B. CLAUDE.md

**Lines to Customize:**
- Line 27-38: **Project Context** - Update to:
  ```markdown
  **Project**: Gem-Flux MCP Server
  **Technologies**: FastMCP, ModelSEEDpy (dev), COBRApy, MCP 2025-06-18
  **Purpose**: Genome-scale metabolic modeling via MCP tools
  ```
- Line 95-135: **Real LLM Testing** - REMOVE (not using LLMs in our tools)
- Line 175-192: **BAML Requirements** - REMOVE (not using BAML)
- Line 585-608: **Context Optimization** - KEEP (using ACE-FCA)

#### C. conftest.py

**Major Changes Needed:**
- Lines 16-303: **REMOVE BAML mocks** (not using BAML)
- Add new fixtures for:
  - `mock_msgenome` - Mock ModelSEEDpy MSGenome
  - `mock_msbuilder` - Mock ModelSEEDpy MSBuilder
  - `mock_msgapfill` - Mock ModelSEEDpy MSGapfill
  - `mock_msmedia` - Mock ModelSEEDpy MSMedia
  - `mock_cobra_model` - Mock COBRApy Model
  - `mock_database_loader` - Mock database loading

**New Structure:**
```python
# Simplified conftest.py for Gem-Flux
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import pandas as pd

@pytest.fixture
def mock_database():
    """Mock ModelSEED database DataFrames."""
    compounds_df = pd.DataFrame({
        'id': ['cpd00027', 'cpd00007'],
        'name': ['D-Glucose', 'O2'],
        # ... other columns
    })
    reactions_df = pd.DataFrame({
        'id': ['rxn00001', 'rxn00002'],
        'name': ['Reaction 1', 'Reaction 2'],
        # ... other columns
    })
    return {'compounds': compounds_df, 'reactions': reactions_df}

@pytest.fixture
def mock_msgenome():
    """Mock ModelSEEDpy MSGenome."""
    mock = MagicMock()
    mock.add_fasta = MagicMock()
    return mock

# ... similar fixtures for other ModelSEEDpy/COBRApy components
```

#### D. test_expectations.json

**Customize for Our Phases:**
```json
{
  "phase_1": {
    "name": "Database Integration",
    "must_pass": [
      "test_load_compounds_database",
      "test_load_reactions_database",
      "test_database_indexing"
    ],
    "may_fail": [],
    "notes": "Foundation - all must pass"
  },
  "phase_2": {
    "name": "Template Management",
    "must_pass": [
      "test_load_gram_negative_template",
      "test_load_core_template"
    ],
    "may_fail": [],
    "notes": "Template loading required before model building"
  },
  "phase_3": {
    "name": "Build Media Tool",
    "must_pass": [
      "test_build_media_basic",
      "test_media_validation"
    ],
    "may_fail": [
      "test_full_workflow"
    ],
    "notes": "Full workflow needs model building (Phase 4)"
  }
  // ... phases 4-15 for remaining tools
}
```

#### E. context_relevance.py

**Update Component Map** (Lines 60-77):
```python
self.component_map = {
    # Database tools
    "get_compound_name": "008-compound-lookup-tools.md",
    "get_reaction_name": "009-reaction-lookup-tools.md",
    "search_compounds": "008-compound-lookup-tools.md",
    "search_reactions": "009-reaction-lookup-tools.md",
    "database": "007-database-integration.md",

    # Core modeling tools
    "build_media": "003-build-media-tool.md",
    "build_model": "004-build-model-tool.md",
    "gapfill_model": "005-gapfill-model-tool.md",
    "run_fba": "006-run-fba-tool.md",

    # Session management
    "list_models": "018-session-management-tools.md",
    "list_media": "018-session-management-tools.md",
    "delete_model": "018-session-management-tools.md",

    # Infrastructure
    "MSGenome": "004-build-model-tool.md",
    "MSBuilder": "004-build-model-tool.md",
    "MSGapfill": "005-gapfill-model-tool.md",
    "MSMedia": "003-build-media-tool.md",
    "COBRApy": "006-run-fba-tool.md",
    "template": "017-template-management.md",
}
```

---

## 4. UV and Virtual Environment Setup

### Critical Issue: ModelSEEDpy Dev Branch

**From specs/014-installation.md:**
```
ModelSEEDpy requires the dev branch:
pip install git+https://github.com/ModelSEED/ModelSEEDpy.git@dev
```

**Why This Matters:**
- User's machine may have stable ModelSEEDpy installed globally
- Dev branch has breaking changes required for our specs
- Virtual environment isolates project dependencies
- UV provides fast, reliable environment management

### UV Configuration: pyproject.toml

**Create `pyproject.toml`:**
```toml
[project]
name = "gem-flux-mcp"
version = "0.1.0"
description = "MCP server for genome-scale metabolic modeling"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [
    { name = "João Paulo Lima Faria" }
]

dependencies = [
    "fastmcp>=0.2.0",
    "cobra>=0.27.0",
    # ModelSEEDpy from dev branch - handled via [tool.uv.sources]
    "modelseedpy",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
]

[tool.uv.sources]
modelseedpy = { git = "https://github.com/Fxe/ModelSEEDpy.git", branch = "dev" }
# CRITICAL: Must use Fxe fork, not ModelSEED official repo
# Specs were written based on Fxe/ModelSEEDpy@dev behavior

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/conftest.py"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
fail_under = 80

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]  # Line too long (handled by black)
```

### UV Commands

```bash
# Initialize UV project (creates .venv/)
uv init

# Install dependencies
uv sync

# Install with dev dependencies
uv sync --extra dev

# Run server
uv run python -m gem_flux_mcp.server

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing
```

### .gitignore Updates

```gitignore
# Virtual environment
.venv/
venv/
ENV/

# UV
uv.lock
.uv/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Implementation loop artifacts
.implementation_logs/
.implementation_flags
optimized_prompt.md
```

---

## 5. Project Directory Structure (Complete)

### Final Structure for Phase 1

```
gem-flux-mcp/
├── .git/
├── .github/                          # CI/CD (future)
├── .venv/                            # UV virtual environment (gitignored)
│
├── data/                             # Runtime data files
│   ├── database/                     # ModelSEED database (49 MB)
│   │   ├── compounds.tsv
│   │   ├── reactions.tsv
│   │   └── README.md
│   ├── templates/                    # ModelSEED templates (24 MB)
│   │   ├── Core-V5.2.json
│   │   ├── GramNegModelTemplateV6.json
│   │   └── README.md
│   └── media/                        # Predefined media (already exists)
│       ├── glucose_minimal_aerobic.json
│       ├── glucose_minimal_anaerobic.json
│       ├── pyruvate_minimal_aerobic.json
│       ├── pyruvate_minimal_anaerobic.json
│       └── README.md
│
├── docs/                             # Documentation
│   ├── spec-development/
│   │   └── PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md
│   └── implementation-loop-development/
│       ├── PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md
│       ├── README.md
│       └── to-use-later/             # Template files (source)
│
├── scripts/                          # Development scripts
│   └── development/
│       └── run-implementation-loop.sh  # COPY FROM to-use-later/
│
├── specs/                            # 20 specifications (Phase 0)
│   ├── 001-system-overview.md
│   ├── ... (all 20 specs)
│   └── 020-documentation-requirements.md
│
├── specs-source/                     # Reference materials (Phase 0 only)
│   ├── build_metabolic_model/
│   ├── guidelines.md
│   └── references/
│
├── src/                              # Source code (Phase 1)
│   ├── gem_flux_mcp/                 # Main package
│   │   ├── __init__.py
│   │   ├── server.py                 # MCP server entry point
│   │   ├── tools/                    # MCP tool implementations
│   │   │   ├── __init__.py
│   │   │   ├── build_media.py
│   │   │   ├── build_model.py
│   │   │   ├── gapfill_model.py
│   │   │   ├── run_fba.py
│   │   │   └── ...
│   │   ├── database/                 # Database loading
│   │   │   ├── __init__.py
│   │   │   └── loader.py
│   │   ├── templates/                # Template management
│   │   │   ├── __init__.py
│   │   │   └── manager.py
│   │   └── utils/                    # Utilities
│   │       ├── __init__.py
│   │       ├── context_relevance.py  # COPY FROM to-use-later/
│   │       └── session_storage.py
│   └── __init__.py
│
├── tests/                            # Test suite (Phase 1)
│   ├── conftest.py                   # ADAPT FROM to-use-later/
│   ├── unit/                         # Unit tests
│   │   ├── test_build_media.py
│   │   ├── test_build_model.py
│   │   └── ...
│   └── integration/                  # Integration tests
│       ├── test_expectations.json    # CUSTOMIZE FROM to-use-later/
│       ├── test_phase1_database.py
│       └── ...
│
├── .gitignore
├── CLAUDE.md                         # CUSTOMIZE FROM to-use-later/
├── IMPLEMENTATION_PLAN.md            # To be created
├── pyproject.toml                    # UV configuration (to be created)
├── README.md
└── ... (other root files)
```

---

## 6. README Files to Create

### data/database/README.md

```markdown
# ModelSEED Database Files

This directory contains the ModelSEED biochemistry database files required
for compound and reaction lookups.

## Files

- **compounds.tsv** (12 MB) - 33,993 compounds with IDs, names, formulas, aliases
- **reactions.tsv** (37 MB) - 43,775 reactions with IDs, names, equations, EC numbers

## Source

Downloaded from: https://github.com/ModelSEED/ModelSEEDDatabase
Version: Latest as of October 2025

## Loading

These files are loaded at server startup by `src/gem_flux_mcp/database/loader.py`.
See specification: specs/007-database-integration.md

## Format

Tab-separated values (TSV) with columns documented in:
specs-source/references/modelseed-database/DATABASE_README.md
```

### data/templates/README.md

```markdown
# ModelSEED Templates

This directory contains ModelSEED template files used for genome-scale
metabolic model reconstruction.

## Files

- **Core-V5.2.json** (891 KB) - Core metabolic template (452 reactions)
- **GramNegModelTemplateV6.json** (23 MB) - Gram-negative bacteria template (2,138 reactions)

## Source

Templates from ModelSEEDpy package:
https://github.com/ModelSEED/ModelSEEDpy

## Usage

Templates are loaded at server startup by `src/gem_flux_mcp/templates/manager.py`.
See specification: specs/017-template-management.md

## Template Selection

- **GramNegative**: Default for most bacteria (E. coli, etc.)
- **Core**: Used for ATP correction gapfilling phase
- **GramPositive**: (Future) For Gram-positive bacteria
```

---

## 7. Implementation Plan Creation

### Approach: Empty File + AI Generation (Original Methodology)

**IMPORTANT**: Following the original CogniscientAssistant methodology, we create an **empty** IMPLEMENTATION_PLAN.md file. The AI will generate the comprehensive plan on the first loop iteration by analyzing all 20 specifications.

**Why this approach:**
1. AI knows the specs best (just generated them in Phase 0)
2. Proven successful in reference implementation
3. Saves 60+ minutes of manual plan creation
4. AI determines optimal task breakdown and dependencies

### What Gets Created

**Empty file with header only:**

```markdown
# Implementation Plan - Gem-Flux MCP Server

<!-- AI will generate this plan on first loop iteration -->
<!-- Plan will be created by analyzing all 20 specifications -->
```

**What AI will generate on first loop run:**
- 15-20 phases based on specification dependencies
- 100+ atomic implementation tasks
- Time estimates per phase
- Integration test checkpoints
- Must-pass vs may-fail test categorization

**Example of what AI might generate** (for reference only):
- [ ] Create pyproject.toml with UV configuration
- [ ] Set up src/gem_flux_mcp/ package structure
- [ ] Create src/gem_flux_mcp/database/loader.py
- [ ] Write tests/unit/test_database_loader.py
- [ ] Implement load_compounds_database()
- [ ] Implement load_reactions_database()
- [ ] Test database indexing for O(1) lookup
- [ ] Integration test: Load both databases

## Phase 2: Template Management (3-4 hours)
- [ ] Create src/gem_flux_mcp/templates/manager.py
- [ ] Write tests/unit/test_template_manager.py
- [ ] Implement load_template(template_name)
- [ ] Test GramNegative template loading
- [ ] Test Core template loading
- [ ] Integration test: Template manager + database

## Phase 3: MCP Server Setup (4-6 hours)
- [ ] Create src/gem_flux_mcp/server.py
- [ ] Configure FastMCP server instance
- [ ] Implement server startup sequence
- [ ] Load database at startup
- [ ] Load templates at startup
- [ ] Write tests/integration/test_server_startup.py
- [ ] Test health check (server ready)

## Phase 4: Session Storage (2-3 hours)
- [ ] Create src/gem_flux_mcp/utils/session_storage.py
- [ ] Write tests/unit/test_session_storage.py
- [ ] Implement models storage (dict)
- [ ] Implement media storage (dict)
- [ ] Implement ID generation (model_id, media_id)
- [ ] Test storage limits (100 models max)

## Phase 5: Build Media Tool (6-8 hours)
- [ ] Create src/gem_flux_mcp/tools/build_media.py
- [ ] Write tests/unit/test_build_media.py
- [ ] Implement parameter validation
- [ ] Implement MSMedia creation from compounds
- [ ] Implement custom bounds handling
- [ ] Register tool with MCP server
- [ ] Integration test: build_media → session storage

## Phase 6: Database Lookup Tools (4-6 hours)
- [ ] Create src/gem_flux_mcp/tools/database_lookups.py
- [ ] Write tests/unit/test_database_lookups.py
- [ ] Implement get_compound_name(compound_id)
- [ ] Implement get_reaction_name(reaction_id)
- [ ] Implement search_compounds(query)
- [ ] Implement search_reactions(query)
- [ ] Register all 4 tools with MCP server

## Phase 7: Build Model Tool (12-16 hours) - MOST COMPLEX
- [ ] Create src/gem_flux_mcp/tools/build_model.py
- [ ] Write tests/unit/test_build_model.py
- [ ] Implement protein sequence validation
- [ ] Implement FASTA file parsing
- [ ] Implement MSGenome creation
- [ ] Implement RAST annotation integration
- [ ] Implement MSBuilder model building
- [ ] Implement model_id generation
- [ ] Register tool with MCP server
- [ ] Integration test: build_model → session storage

## Phase 8: Gapfill Model Tool (12-16 hours) - MOST COMPLEX
- [ ] Create src/gem_flux_mcp/tools/gapfill_model.py
- [ ] Write tests/unit/test_gapfill_model.py
- [ ] Implement ATP correction phase
- [ ] Implement genome-scale gapfilling
- [ ] Implement gapfilling solution parsing
- [ ] Implement reaction integration
- [ ] Implement failure handling
- [ ] Register tool with MCP server
- [ ] Integration test: build_model → gapfill_model

## Phase 9: Run FBA Tool (6-8 hours)
- [ ] Create src/gem_flux_mcp/tools/run_fba.py
- [ ] Write tests/unit/test_run_fba.py
- [ ] Implement FBA execution with COBRApy
- [ ] Implement media constraints application
- [ ] Implement flux analysis
- [ ] Implement active reactions filtering
- [ ] Register tool with MCP server
- [ ] Integration test: Complete workflow (build → gapfill → FBA)

## Phase 10: Session Management Tools (3-4 hours)
- [ ] Create src/gem_flux_mcp/tools/session_management.py
- [ ] Write tests/unit/test_session_management.py
- [ ] Implement list_models()
- [ ] Implement list_media()
- [ ] Implement delete_model()
- [ ] Register all 3 tools with MCP server

## Phase 11: Predefined Media Loading (2-3 hours)
- [ ] Create src/gem_flux_mcp/media/predefined.py
- [ ] Write tests/unit/test_predefined_media.py
- [ ] Implement load_predefined_media()
- [ ] Load 4 media JSON files at startup
- [ ] Add to MEDIA_STORAGE at startup
- [ ] Integration test: Predefined media available

## Phase 12: Error Handling & Validation (4-6 hours)
- [ ] Create src/gem_flux_mcp/utils/errors.py
- [ ] Write tests/unit/test_error_handling.py
- [ ] Implement JSON-RPC error responses
- [ ] Implement validation helpers
- [ ] Add error handling to all tools
- [ ] Test error recovery scenarios

## Phase 13: Complete Workflow Tests (6-8 hours)
- [ ] Create tests/integration/test_complete_workflow.py
- [ ] Test: Protein sequences → Draft model
- [ ] Test: FASTA file → Draft model
- [ ] Test: Draft model → Gapfilled model
- [ ] Test: Gapfilled model → FBA results
- [ ] Test: Full pipeline (build + gapfill + FBA)
- [ ] Test: Error scenarios

## Phase 14: Documentation & Examples (4-6 hours)
- [ ] Create examples/ directory
- [ ] Write example scripts for each tool
- [ ] Create API documentation
- [ ] Update README with usage examples
- [ ] Create troubleshooting guide

## Phase 15: Final Integration & Testing (4-6 hours)
- [ ] Run full test suite (all tests)
- [ ] Verify ≥80% code coverage
- [ ] Test server startup/shutdown
- [ ] Test with real ModelSEED data
- [ ] Performance testing
- [ ] Create release checklist
```

**Total Estimated Time**: 80-110 hours of implementation
**With AI Loop**: ~8-11 days (AI does 90% of coding)

---

## 8. Execution Plan (Step-by-Step)

### Step 1: Reorganize Data Files (15 minutes)

```bash
# Create directories
mkdir -p data/database data/templates

# Move files
mv specs-source/references/modelseed-database/compounds.tsv data/database/
mv specs-source/references/modelseed-database/reactions.tsv data/database/
mv specs-source/build_metabolic_model/Core-V5.2.json data/templates/
mv specs-source/build_metabolic_model/GramNegModelTemplateV6.json data/templates/

# Create README files
# (create data/database/README.md - see Section 6)
# (create data/templates/README.md - see Section 6)

# Commit
git add data/
git commit -m "chore: reorganize data files to proper locations

- Move ModelSEED database files to data/database/
- Move template JSON files to data/templates/
- Add README files documenting structure
- Prepares for Phase 1 implementation"
```

### Step 2: Update Specifications (30 minutes)

```bash
# Update spec files with new paths
# - specs/007-database-integration.md
# - specs/015-mcp-server-setup.md
# - specs/017-template-management.md

# Commit
git add specs/
git commit -m "docs: update specifications with correct data file paths

- Update database paths to ./data/database/
- Update template paths to ./data/templates/
- Ensure consistency across all specs"
```

### Step 3: Set Up UV Project (10 minutes)

```bash
# Create pyproject.toml (see Section 4)

# Initialize UV
uv init

# Install dependencies
uv sync

# Verify ModelSEEDpy dev branch installed
uv run python -c "import modelseedpy; print(modelseedpy.__version__)"

# Commit
git add pyproject.toml .gitignore
git commit -m "build: set up UV project with ModelSEEDpy dev branch

- Add pyproject.toml with dependencies
- Configure UV to use ModelSEEDpy@dev
- Set up virtual environment isolation
- Add dev dependencies (pytest, coverage, etc.)"
```

### Step 4: Copy Implementation Loop Templates (20 minutes)

```bash
# Create directories
mkdir -p scripts/development
mkdir -p tests/unit tests/integration
mkdir -p src/gem_flux_mcp/utils

# Copy template files
cp docs/implementation-loop-development/to-use-later/run-implementation-loop.sh \
   scripts/development/
chmod +x scripts/development/run-implementation-loop.sh

cp docs/implementation-loop-development/to-use-later/CLAUDE.md ./
cp docs/implementation-loop-development/to-use-later/test_expectations.json \
   tests/integration/
cp docs/implementation-loop-development/to-use-later/context_relevance.py \
   src/gem_flux_mcp/utils/

# Create simplified conftest.py (see Section 3.C)
# (manually create tests/conftest.py)

# Commit
git add scripts/ tests/ src/ CLAUDE.md
git commit -m "build: add implementation loop infrastructure

- Copy run-implementation-loop.sh from templates
- Add CLAUDE.md implementation guidelines
- Set up test infrastructure with expectations
- Add ACE-FCA context optimization
- Ready for Phase 1 automated development"
```

### Step 5: Customize Template Files (45 minutes)

**Update critical_specs in context_relevance.py** (see Section 3.E)
**Update component_map in context_relevance.py** (see Section 3.E)
**Customize CLAUDE.md** (see Section 3.B)
**Create test_expectations.json phases** (see Section 3.D)

```bash
# Commit customizations
git add src/gem_flux_mcp/utils/context_relevance.py CLAUDE.md \
        tests/integration/test_expectations.json
git commit -m "config: customize implementation loop for Gem-Flux

- Update critical specs list for metabolic modeling
- Add component map for ModelSEEDpy/COBRApy tools
- Remove BAML references from CLAUDE.md
- Define phase-based test expectations"
```

### Step 6: Create Empty IMPLEMENTATION_PLAN.md (2 minutes)

```bash
# Create empty file with header (AI will generate plan on first loop run)
cat > IMPLEMENTATION_PLAN.md << 'EOF'
# Implementation Plan - Gem-Flux MCP Server

<!-- AI will generate this plan on first loop iteration -->
<!-- Plan will be created by analyzing all 20 specifications -->

EOF

# Commit
git add IMPLEMENTATION_PLAN.md
git commit -m "docs: create empty implementation plan for AI generation

- Empty file signals loop to generate plan
- AI will analyze 20 specs and create comprehensive plan
- Follows original CogniscientAssistant methodology"
```

### Step 7: Create Initial Project Structure (15 minutes)

```bash
# Create package structure
mkdir -p src/gem_flux_mcp/{tools,database,templates,utils,media}
touch src/gem_flux_mcp/__init__.py
touch src/gem_flux_mcp/tools/__init__.py
touch src/gem_flux_mcp/database/__init__.py
touch src/gem_flux_mcp/templates/__init__.py
touch src/gem_flux_mcp/utils/__init__.py
touch src/gem_flux_mcp/media/__init__.py

# Create test directories
mkdir -p tests/{unit,integration}
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Commit
git add src/ tests/
git commit -m "build: create initial package structure

- Set up gem_flux_mcp package with submodules
- Create test directory structure
- Prepare for Phase 1 implementation"
```

### Step 8: Push to GitHub (5 minutes)

```bash
# Push all changes
git push origin phase-1-implementation

# Verify on GitHub
# https://github.com/jplfaria/gem-flux-mcp/tree/phase-1-implementation
```

---

## 9. Pre-Implementation Checklist

Before running `./scripts/development/run-implementation-loop.sh`:

### Prerequisites
- [x] Phase 0 complete (20 specifications)
- [ ] Data files moved to `data/` directory
- [ ] Specifications updated with correct paths
- [ ] UV project set up with pyproject.toml
- [ ] Virtual environment created (.venv/)
- [ ] ModelSEEDpy dev branch installed
- [ ] Implementation loop files copied
- [ ] Template files customized
- [ ] IMPLEMENTATION_PLAN.md created
- [ ] Initial package structure created
- [ ] All changes committed to phase-1-implementation branch
- [ ] Changes pushed to GitHub

### Verification Commands

```bash
# Verify data files exist
ls -lh data/database/*.tsv
ls -lh data/templates/*.json

# Verify UV environment
uv run python -c "import modelseedpy, cobra, fastmcp; print('✓ All imports working')"

# Verify implementation loop script
./scripts/development/run-implementation-loop.sh --check

# Verify test infrastructure
uv run pytest --collect-only
```

---

## 10. Estimated Timeline

### Preparation Phase (Before Implementation)
- Step 1-2: Reorganize & update specs - **45 minutes**
- Step 3-4: Set up UV & copy templates - **30 minutes**
- Step 5: Customize templates - **45 minutes**
- Step 6: Create empty IMPLEMENTATION_PLAN.md - **2 minutes**
- Step 7-8: Create structure & push - **20 minutes**
- **Total preparation**: ~2.5 hours

### First Loop Iteration (Plan Generation)
- AI reads 20 specs and generates plan - **10-15 minutes**
- Human reviews generated plan - **10-15 minutes**
- **Total**: ~30 minutes

### Phase 1 Implementation (With AI Loop)
- 15 phases, 100+ tasks
- Estimated AI coding time: 80-110 hours
- Human review/guidance: 10-15 hours
- **Total Phase 1**: 8-11 days (with 90% automation)

---

## 11. Risk Mitigation

### Risk 1: ModelSEEDpy Dev Branch Issues
**Mitigation**:
- Test installation immediately after UV setup
- Have fallback to specific commit hash if dev branch breaks
- Document version that works

### Risk 2: Template Files Too Large for Git
**Mitigation**:
- Already tracked (not added in this prep)
- Consider Git LFS if team collaboration needed
- Current size (24MB + 49MB = 73MB) acceptable for solo development

### Risk 3: Implementation Loop Failures
**Mitigation**:
- Start with simple Phase 1 (database loading)
- Verify quality gates work before complex phases
- Have manual implementation as fallback

---

## 12. Success Criteria

Phase 1 preparation is complete when:

- [ ] All data files in correct locations (`data/database/`, `data/templates/`)
- [ ] All specifications reference correct paths
- [ ] UV virtual environment working with ModelSEEDpy dev
- [ ] All implementation loop files in place and customized
- [ ] IMPLEMENTATION_PLAN.md created with 15 phases
- [ ] Initial package structure exists
- [ ] All changes committed and pushed to GitHub
- [ ] Can run `./scripts/development/run-implementation-loop.sh` without errors

---

## 13. Next Steps (Awaiting User Approval)

**DO NOT PROCEED WITHOUT EXPLICIT USER APPROVAL**

Once approved, execute in order:
1. Run Step 1: Reorganize data files
2. Run Step 2: Update specifications
3. Run Step 3: Set up UV project
4. Run Step 4-5: Copy and customize templates
5. Run Step 6: Create implementation plan
6. Run Step 7-8: Create structure and push
7. **STOP** - Ask user permission to start implementation loop

---

**Document Status**: Complete - Awaiting User Approval
**Branch**: phase-1-implementation
**Prepared By**: Claude Code
**Date**: October 27, 2025
