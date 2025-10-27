# Claude AI Co-Scientist Implementation Guidelines

**Core Philosophy: IMPLEMENT FROM SPECS. Build behavior exactly as specified.**

## 📖 Reading Requirements

### Before Implementation
- Read ALL specs in specs/ directory first
- Understand the complete system before coding
- Trust the specs - they define all behaviors

### During Implementation
- **New file**: Read ENTIRE file before modifying
- **Small file (<500 lines)**: Read completely
- **Large file (500+ lines)**: Read at least 1500 lines
- **ALWAYS** understand existing code before adding new code

## 📁 Test Organization

### Test Directory Structure
- **Unit tests**: `tests/unit/test_*.py` - Test individual components
- **Integration tests**: `tests/integration/test_phase*_*.py` - Test system workflows
- **NO other test subdirectories** - Don't create tests/baml/, tests/agents/, etc.
- **NO tests in root tests/ directory** - All tests must be in unit/ or integration/

### Test Naming Convention
- Unit test: `tests/unit/test_<module_name>.py`
- Integration test: `tests/integration/test_phase<N>_<feature>.py`
- Example: `tests/unit/test_task_queue.py`, `tests/integration/test_phase3_queue_workflow.py`

## 🔄 Implementation Workflow

### 1. Check Status
```bash
# At start of each iteration, check for errors
if [ -f ".implementation_flags" ]; then
    if grep -q "INTEGRATION_REGRESSION=true" .implementation_flags; then
        echo "❌ Fix regression before continuing"
    elif grep -q "IMPLEMENTATION_ERROR=true" .implementation_flags; then
        echo "❌ Fix implementation to match specs"
    fi
    # After fixing: rm .implementation_flags
fi
```

### 2. One Task Per Iteration
- Pick FIRST unchecked [ ] task from IMPLEMENTATION_PLAN.md
- Implement it COMPLETELY with tests
- Don't start multiple tasks
- Each iteration MUST have passing tests before commit

### 3. Test-First Development
- Write failing tests BEFORE implementation
- Implement minimal code to pass tests
- All tests must pass (pytest)
- Coverage must meet 80% threshold
- Integration tests use test_expectations.json

### 4. Commit and Continue
```bash
# Only if all tests pass:
git add -A
git commit -m "feat: implement [component] - [what you did]"
# Then exit - the loop will continue
```

## 🧪 Testing Requirements

### Integration Test Categories
- **✅ Pass**: Implementation correct
- **⚠️ Expected Failure**: Tests in `may_fail` list
- **❌ Critical Failure**: Tests in `must_pass` list failed
- **❌ Unexpected Failure**: Unlisted tests failed
- **❌ Regression**: Previously passing test fails

### Test Expectations
The file `tests/integration/test_expectations.json` defines:
- `must_pass`: Critical tests that block progress
- `may_fail`: Tests allowed to fail (waiting for future components)
- `description`: Phase description and context

### ModelSEEDpy Mocking Requirements
When adding new tests:
1. **Update `/tests/conftest.py`** with ModelSEEDpy mocks
2. **Mock MSGenome, MSBuilder, MSGapfill, MSMedia** classes
3. **Mock database loading** to avoid 49 MB file I/O in tests
4. **Mock COBRApy Model** for FBA operations
5. Test with actual ModelSEEDpy for integration tests

## 🛡️ Security & Configuration

### Environment Variables
- `GEM_FLUX_DATABASE_DIR`: Path to ModelSEED database files (default: ./data/database)
- `GEM_FLUX_TEMPLATE_DIR`: Path to template JSON files (default: ./data/templates)
- **NEVER** commit sensitive paths or credentials to git
- Use .env file for local development (already in .gitignore)

## 🏗️ Technical Stack

### Core Technologies
- **Python 3.11 ONLY (NOT 3.12+)**: CRITICAL - Python 3.12+ removed distutils module which scikit-learn 1.2.0 requires (ModelSEEDpy dependency). Must use 3.11.
- **FastMCP**: MCP server framework for tool registration
- **ModelSEEDpy (Fxe/dev)**: CRITICAL - must use Fxe fork, not official repo
- **COBRApy**: Genome-scale metabolic modeling
- **pytest**: Comprehensive testing with ≥80% coverage
- **UV**: Package manager with virtual environment isolation

## 🔧 MCP Tool Development Best Practices

### Overview: FastMCP Tool Development

FastMCP tools expose metabolic modeling capabilities through the MCP protocol:

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| **MCP Tools** | Core modeling operations | build_media, build_model, gapfill_model, run_fba |
| **Database Tools** | Compound/reaction lookup | Search and retrieve from ModelSEED database |
| **Session Tools** | Model management | list_models, list_media, delete_model |

**Golden Rule:** Each tool implements ONE modeling operation following the spec exactly.

### Tool Design Principles for Gem-Flux

✅ **Core Principles:**
- **Spec-driven**: Implement EXACTLY what's in specs/ directory
- **Single responsibility**: Each tool does ONE thing well
- **Error handling**: Return JSON-RPC 2.0 compliant errors
- **Type safety**: Use Pydantic models for all inputs/outputs
- **Session isolation**: Models stored with .gf extension for uniqueness

❌ **Don't:**
- Deviate from spec behavior
- Mix multiple operations in one tool
- Use model_id format (use .gf notation instead)
- Skip error handling for failure cases

### Example Tool Structure

```python
from fastmcp import FastMCP
from pydantic import BaseModel

class BuildMediaRequest(BaseModel):
    compounds: list[str]
    media_id: str

mcp = FastMCP("Gem-Flux")

@mcp.tool()
async def build_media(request: BuildMediaRequest) -> dict:
    """Create growth media from compounds."""
    try:
        # Load compounds from database
        # Create MSMedia object
        # Store in session
        return {"media_id": request.media_id, "compounds": ...}
    except Exception as e:
        return {"error": str(e), "code": -32603}
```

**Key Pattern:** FastMCP decorator + Pydantic validation + session storage.

## 🧬 ModelSEEDpy Integration

### Critical Requirements

1. **Fxe Fork ONLY**: Must use `https://github.com/Fxe/ModelSEEDpy.git` dev branch
   - Specs written against this specific version
   - Official repo has different behavior
   - Already configured in pyproject.toml

2. **Database Loading**:
   - Compounds: `data/database/compounds.tsv` (33,993 compounds, 12 MB)
   - Reactions: `data/database/reactions.tsv` (43,775 reactions, 37 MB)
   - Use ModelSEEDDatabase class for loading

3. **Template Management**:
   - GramNegative: `data/templates/GramNegModelTemplateV6.json` (23 MB, 2,138 reactions)
   - Core: `data/templates/Core-V5.2.json` (891 KB, 452 reactions)
   - Load via MSTemplateManager

### Common Patterns

```python
# Database loading
from modelseedpy import ModelSEEDDatabase
db = ModelSEEDDatabase.load_database(
    compounds_path="data/database/compounds.tsv",
    reactions_path="data/database/reactions.tsv"
)

# Model building
from modelseedpy import MSGenome, MSBuilder
genome = MSGenome.from_fasta("genome.fasta")
builder = MSBuilder(genome, template, db)
model = builder.build()

# Gapfilling
from modelseedpy import MSGapfill
gapfiller = MSGapfill(model, default_gapfill_media)
solution = gapfiller.run_gapfilling()

# FBA
solution = model.optimize()
```

### Implementation Phases (TBD - AI will generate)

The implementation will be planned by the AI based on the 20 specifications:

**Core Tools** (4):
- build_media: Create growth media from compounds
- build_model: Build metabolic models (RAST/FASTA/dict)
- gapfill_model: Gapfill models with failure handling
- run_fba: Execute flux balance analysis

**Database Tools** (3):
- Database integration: Load ModelSEED database
- Compound lookup: Search and retrieve compounds
- Reaction lookup: Search and retrieve reactions

**Session & Storage** (4):
- Model storage: Session-based model storage
- Model import/export: I/O operations (future)
- Template management: ModelSEED template loading
- Session management: list_models, list_media, delete_model

**System & Architecture** (9):
- System overview, data formats, workflows
- Error handling, installation, MCP setup
- Documentation and future roadmap

## 🚨 Critical Rules

1. **Follow specs exactly** - no deviations from specs/ directory
2. **Use .gf notation** - model IDs use ecoli.gf NOT ecoli_gf (underscore conflicts resolved)
3. **JSON-RPC 2.0 errors** - all errors must be compliant
4. **Maintain ≥80% test coverage** - always
5. **One atomic feature per iteration** - complete with tests
6. **Session isolation** - models stored in-memory with unique .gf IDs
7. **Update IMPLEMENTATION_PLAN.md** - after each task
8. **ModelSEEDpy Fxe fork** - never use official repo

## 📋 Working Memory

Maintain a TODO list between iterations:
```markdown
## Current TODO List
1. [ ] Current task from IMPLEMENTATION_PLAN.md
2. [ ] Files to read before modifying
3. [ ] Tests to write
4. [ ] Integration points to verify
5. [ ] Refactoring opportunities
6. [ ] Duplicate code to remove
```

Remember: The specs are your truth. Implement exactly what's specified.

## 🎯 Context Optimization Guidelines

### ACE-FCA Integration Status

The development loop has been enhanced with ACE-FCA context optimization principles:

#### Context Relevance Scoring
- **Intelligent Spec Selection**: 3-7 most relevant specifications based on current task
- **Automatic Fallback**: Full context when optimization confidence is low
- **Quality Validation**: Context selections validated against phase requirements

#### Usage
- **Automatic**: Context optimization runs automatically during development loop
- **Monitoring**: Metrics logged to `.context_optimization_metrics.log`
- **Manual Control**: Can be disabled with `.context_optimization_disabled` file

#### Quality Requirements
- **Same Standards Apply**: All existing quality gates must pass with optimized context
- **Fallback Guarantee**: System automatically uses full context if quality issues detected
- **Coverage Maintained**: ≥80% test coverage required regardless of context optimization

### Implementation Priority

Context optimization is production-ready and should be used for all development iterations.