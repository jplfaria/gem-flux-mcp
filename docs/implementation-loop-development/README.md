# Implementation Loop Development

This directory contains resources for **Phase 1: Implementation Loop** - the AI-assisted development phase that follows cleanroom specification generation.

---

## What's in This Directory

### `/to-use-later/` - Template Files for New Projects

When you're ready to begin implementation (after Phase 0 spec generation is complete), copy these files to your new project:

#### Core Loop Files

1. **run-implementation-loop.sh** (1133 lines)
   - Main implementation loop orchestration
   - Quality gate execution
   - Context optimization integration
   - Error handling and logging
   - **Copy to**: `scripts/development/run-implementation-loop.sh`

2. **CLAUDE.md** (608 lines)
   - Implementation guidelines for Claude
   - Test organization rules
   - Workflow requirements
   - Context optimization notes
   - **Copy to**: project root `CLAUDE.md`

#### Testing Infrastructure

3. **conftest.py** (729 lines)
   - pytest configuration
   - BAML mocking system (if using BAML)
   - Test fixtures
   - **Copy to**: `tests/conftest.py`
   - **Customize**: Update mocks for your project's interfaces

4. **test_expectations.json** (621 lines - from CogniscientAssistant)
   - Template showing must_pass/may_fail test structure
   - Phase-based test expectations
   - Real LLM test markers
   - **Copy to**: `tests/integration/test_expectations.json`
   - **Customize**: Create expectations for YOUR phases

#### Context Optimization (Optional but Recommended)

5. **context_relevance.py** (589 lines)
   - Specification relevance scoring
   - Component detection
   - Confidence calculation
   - 40-90% context reduction
   - **Copy to**: `src/utils/context_relevance.py`
   - **Customize**: Update critical_specs and component_map

---

## Quick Start (After Phase 0 Complete)

### Step 1: Copy Template Files

```bash
# From your new project directory
GEM_FLUX=/path/to/gem-flux-mcp

# Core loop files
mkdir -p scripts/development
cp $GEM_FLUX/docs/implementation-loop-development/to-use-later/run-implementation-loop.sh \
   scripts/development/
chmod +x scripts/development/run-implementation-loop.sh

cp $GEM_FLUX/docs/implementation-loop-development/to-use-later/CLAUDE.md ./

# Test infrastructure
mkdir -p tests/unit tests/integration
cp $GEM_FLUX/docs/implementation-loop-development/to-use-later/conftest.py \
   tests/
cp $GEM_FLUX/docs/implementation-loop-development/to-use-later/test_expectations.json \
   tests/integration/

# Context optimization (optional)
mkdir -p src/utils
cp $GEM_FLUX/docs/implementation-loop-development/to-use-later/context_relevance.py \
   src/utils/
```

### Step 2: Customize Files

See **Phase 1 Implementation Loop Guide** (`/docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md`) for detailed customization instructions.

### Step 3: Create Implementation Plan

Create `IMPLEMENTATION_PLAN.md` from your specifications (see Phase 1 guide).

### Step 4: Run the Loop

```bash
./scripts/development/run-implementation-loop.sh
```

---

## Template File Descriptions

### run-implementation-loop.sh

**Purpose**: Main implementation loop that orchestrates AI-assisted development

**Key Features**:
- **Phase Detection**: Automatically finds current phase and next task
- **Context Optimization**: Reduces context size by 40-90% using ACE-FCA
- **Quality Gates**:
  - Gate 1: Test execution (must_pass tests)
  - Gate 2: Coverage check (≥80% for unit tests)
  - Gate 3: Integration tests (regression detection)
  - Gate 4: Context optimization validation
- **Error Handling**: Stops on failure, logs errors, provides recovery steps
- **Progress Tracking**: Logs iterations, shows completed/remaining tasks

**Customization Points**:
- Line 30-35: Adjust max iterations (default 100)
- Line 138-166: Add custom phases to detection
- Line 755-870: Modify quality gate thresholds
- Line 400-450: Customize context optimization logic

---

### CLAUDE.md

**Purpose**: Guidelines that Claude reads during implementation

**Key Sections**:
- **Reading Requirements**: How much context to read before implementation
- **Implementation Workflow**: 4-step process (Check Status → One Task → Test-First → Commit)
- **Test Organization**: Directory structure and naming conventions
- **Real LLM Testing**: Guidelines for testing AI behaviors
- **BAML Requirements**: When to use BAML vs mocks (if applicable)
- **Critical Rules**: Non-negotiable implementation principles

**Customization Points**:
- **Line 27-38**: Project Context - update with YOUR project name and technologies
- **Line 95-135**: Real LLM Testing - remove if not using AI models
- **Line 175-192**: BAML Prompt Requirements - remove if not using BAML
- **Line 585-608**: Context Optimization - keep as-is or customize confidence thresholds

---

### conftest.py

**Purpose**: pytest configuration and test fixtures

**Key Features**:
- **BAML Mocking** (lines 8-303): Mock BAML client to avoid import errors
  - Remove if not using BAML
  - Keep structure if mocking other services
- **Mock Types** (lines 603-701): Create mock types for interfaces
- **pytest Hooks** (lines 8-13): Configure test behavior
- **Fixtures** (throughout): Reusable test setup

**Customization Points**:
- **Lines 16-303**: Replace BAML mocks with YOUR service mocks
- **Lines 305-600**: Add fixtures for YOUR components
- **Lines 603-701**: Add mock types for YOUR interfaces

**If Not Using BAML**:
```python
# Simplified conftest.py template
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_your_service():
    """Mock your external service."""
    mock = MagicMock()
    mock.some_method = AsyncMock(return_value="result")
    return mock
```

---

### test_expectations.json

**Purpose**: Define which tests must pass vs may fail per phase

**Structure**:
```json
{
  "phase_N": {
    "name": "Phase Name",
    "must_pass": ["critical_test_1", "critical_test_2"],
    "may_fail": ["future_integration_test"],
    "real_llm_tests": ["test_with_actual_model"],
    "notes": "Explanation"
  }
}
```

**Customization**:
1. **Define YOUR phases**: Match your IMPLEMENTATION_PLAN.md phases
2. **Specify must_pass**: Tests that BLOCK progress if failed
3. **Specify may_fail**: Tests allowed to fail (waiting for future components)
4. **Optional real_llm_tests**: Tests run manually, not in automated loop
5. **Add notes**: Explain why tests may fail

**Example for Generic Project**:
```json
{
  "phase_1": {
    "name": "Core Infrastructure",
    "must_pass": [
      "test_models_creation",
      "test_database_connection",
      "test_config_loading"
    ],
    "may_fail": [],
    "notes": "Foundation phase - all tests must pass"
  },
  "phase_2": {
    "name": "API Layer",
    "must_pass": [
      "test_api_endpoints",
      "test_request_validation"
    ],
    "may_fail": [
      "test_full_integration"
    ],
    "notes": "Integration test may fail until Phase 3 database ready"
  }
}
```

---

### context_relevance.py

**Purpose**: ACE-FCA context optimization - select relevant specs instead of loading all

**Key Features**:
- **Critical Specs** (lines 30-35): Always include these specs (e.g., system-overview, core-principles)
- **Component Detection** (lines 79-136): Map task descriptions to specific component specs
- **Scoring System** (lines 138-199): Calculate relevance scores using TF-IDF
- **Confidence Calculation** (lines 397-426): Determine if optimization is reliable
- **Fallback Logic**: Use full context if confidence < 0.4

**Customization Points**:
```python
# Line 30-35: Critical specs (always include)
self.critical_specs = [
    "001-system-overview.md",
    "002-core-principles.md",
    # Add YOUR critical specs
]

# Line 60-77: Component map (task keywords → spec file)
self.component_map = {
    "AuthManager": "020-authentication.md",
    "OAuth": "020-authentication.md",
    "DatabaseManager": "015-database.md",
    # Add YOUR components
}
```

**Benefits**:
- **40-90% context reduction**: Faster Claude responses, lower costs
- **Maintains quality**: Same test pass rates, same coverage
- **Automatic fallback**: Uses full context if uncertain

**Optional**: Can disable if you prefer full context always (see Phase 1 guide)

---

## Workflow Comparison

### Phase 0: Spec Loop vs Phase 1: Implementation Loop

| **Aspect** | **Phase 0 (Spec Loop)** | **Phase 1 (Implementation Loop)** |
|------------|-------------------------|-----------------------------------|
| **Goal** | Generate specifications | Implement code from specs |
| **Input** | Source materials (papers, docs) | Specifications + Implementation Plan |
| **Output** | specs/*.md files | src/*.py + tests/*.py files |
| **Task Source** | SPECS_PLAN.md | IMPLEMENTATION_PLAN.md |
| **Quality Gates** | Self-review (WHAT not HOW) | Tests (pytest), Coverage (≥80%), Regressions |
| **Context** | All source materials | Selected specs (3-7) via ACE-FCA |
| **Loop Script** | run-spec-loop.sh | run-implementation-loop.sh |
| **Guidelines** | SPECS_CLAUDE.md | CLAUDE.md |
| **Completion** | ALL_TASKS_COMPLETE signal | All [ ] tasks marked [x] |
| **Commits** | Per spec generated | Per task implemented |

---

## File Sizes & Line Counts

From CogniscientAssistant project:

```
run-implementation-loop.sh     1,133 lines  (core loop logic)
CLAUDE.md                        608 lines  (implementation guidelines)
conftest.py                      729 lines  (test fixtures, BAML mocking)
test_expectations.json           621 lines  (quality criteria)
context_relevance.py             589 lines  (ACE-FCA optimization)
---------------------------------------------------
Total                          3,680 lines
```

**Total implementation infrastructure**: ~3,700 lines of battle-tested code

---

## Integration with Existing Projects

If you already have a project with:
- Existing tests → Adapt conftest.py to your test structure
- Different test framework → Modify quality gates in run-implementation-loop.sh
- No Python → Port implementation loop logic to your language
- Different AI provider → Modify Claude invocation in loop script

The **core patterns** (atomic tasks, quality gates, context optimization) are language-agnostic.

---

## Documentation References

For detailed instructions:

1. **Phase 1 Implementation Loop Guide**: `/docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md`
   - Complete step-by-step instructions
   - Customization details
   - Troubleshooting guide
   - Best practices

2. **Phase 0 Cleanroom Spec Guide**: `/docs/PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md`
   - How to generate specs before implementation
   - Prerequisite for Phase 1

3. **CogniscientAssistant Project**: Reference implementation
   - Live example of all concepts
   - 28 specs → 15 phases → production code
   - ~3,700 lines of infrastructure

---

## Support & Questions

**Common Questions**:

**Q: Do I need all template files?**
A: Minimum required: run-implementation-loop.sh, CLAUDE.md, test_expectations.json
   Optional but recommended: context_relevance.py
   Only if using BAML: conftest.py (otherwise create simpler version)

**Q: Can I use this for non-Python projects?**
A: Yes! Core concepts (atomic tasks, quality gates, context optimization) are universal.
   You'll need to port the shell script logic and adapt quality gates to your test framework.

**Q: What if I don't have specifications?**
A: You must complete Phase 0 first. Implementation loop requires specs as input.

**Q: How long does Phase 1 take?**
A: Depends on project size:
   - Small (5-10 components): 2-5 days
   - Medium (10-20 components): 1-2 weeks
   - Large (20+ components): 2-4 weeks
   With automated loop, 90%+ of time is AI working, 10% is human review.

---

## Version History

- **v1.0** (2025-01-15): Initial template collection from CogniscientAssistant
  - Proven in production on 15-phase, 28-spec project
  - 85% implementation complete with high quality
  - Zero regressions after implementing regression detection

---

**Ready to implement?** See `/docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md` for complete instructions.
