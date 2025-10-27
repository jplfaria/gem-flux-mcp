# Phase 1: Implementation Loop Guide

**Complete step-by-step guide for implementing code from cleanroom specifications using AI-assisted development**

---

## Overview

Phase 1 is the **implementation phase** that happens AFTER specifications are complete. You implement the system using test-driven development, quality gates, and AI assistance through an automated loop. This ensures high code quality while moving quickly.

**Key Principle**: Implement exactly what specifications describe. Tests guide implementation. Quality gates ensure correctness.

---

## Prerequisites

Before starting Phase 1, you must have:

- ✅ **Completed Phase 0**: All specifications created and validated
- ✅ **Specifications committed**: All specs in git with CLEANROOM principles
- ✅ **Completeness report**: Verification that specs are complete
- ✅ **Understanding**: Team understands system from specs alone

If any prerequisite is missing, **return to Phase 0** and complete it first.

---

## Implementation Loop Architecture

### Core Concept

The implementation loop is an **automated, quality-gated development workflow**:

```
┌─────────────────────────────────────────────────────────────┐
│                    ITERATION START                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  1. DETECT TASK                                              │
│     - Scan IMPLEMENTATION_PLAN.md for first unchecked [ ]    │
│     - Extract task description and context                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. OPTIMIZE CONTEXT (ACE-FCA)                               │
│     - Select 3-7 most relevant specifications                │
│     - Calculate confidence score                             │
│     - Fallback to full context if confidence < 0.4           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. INVOKE CLAUDE                                            │
│     - Provide task, specs, guidelines                        │
│     - Claude writes tests FIRST                              │
│     - Claude implements code to pass tests                   │
│     - Claude marks task [x] in plan                          │
│     - Claude commits changes                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  4. QUALITY GATES                                            │
│     ├─ Gate 1: Tests must pass (pytest)                      │
│     ├─ Gate 2: Coverage ≥ 80% (unit tests)                   │
│     ├─ Gate 3: Integration tests pass (no regressions)       │
│     └─ Gate 4: Context optimization validated                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
                ┌──────┴──────┐
                │             │
            ALL PASS      ANY FAIL
                │             │
                ▼             ▼
           LOG SUCCESS   LOG FAILURE
                │             │
                ▼             ▼
        CHECK COMPLETE    STOP LOOP
                │         (fix manually)
                │
         ┌──────┴──────┐
         │             │
    MORE TASKS    ALL DONE
         │             │
         ▼             ▼
    NEXT ITERATION  CELEBRATE!
```

### Key Features

1. **Test-Driven Development**: Tests written before implementation
2. **Quality Gates**: Automated validation at each iteration
3. **Context Optimization**: Only loads relevant specs (40-90% context reduction)
4. **Error Detection**: Regressions and critical failures caught immediately
5. **Automatic Logging**: All iterations logged for review
6. **Safe Iteration**: Loop stops on failure (requires manual fix)

---

## Directory Structure (After Phase 1 Setup)

```
YourProject/
├── specs/                         # Specifications (from Phase 0)
├── src/                           # Source code (generated in Phase 1)
│   ├── agents/
│   ├── core/
│   ├── tools/
│   └── utils/
├── tests/                         # Tests (generated in Phase 1)
│   ├── unit/
│   │   ├── test_*.py
│   └── integration/
│       ├── test_phase*_*.py
│       └── test_expectations.json
├── docs/
│   ├── implementation-loop-development/
│   │   ├── to-use-later/          # Template files from CogniscientAssistant
│   │   │   ├── run-implementation-loop.sh
│   │   │   ├── CLAUDE.md
│   │   │   ├── conftest.py
│   │   │   ├── test_expectations.json (template)
│   │   │   └── context_relevance.py (if using ACE-FCA)
│   │   └── README.md
│   └── PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md  # This file
├── scripts/
│   └── development/
│       └── run-implementation-loop.sh  # Main loop script
├── IMPLEMENTATION_PLAN.md         # Task checklist
├── CLAUDE.md                      # Implementation guidelines
├── optimized_prompt.md            # Generated prompt (gitignored)
├── .implementation_logs/          # Iteration logs (gitignored)
├── .implementation_flags          # Error state (gitignored)
├── pyproject.toml                 # Python project config
└── README.md
```

---

## Step-by-Step Process

### Phase 1.1: Create Implementation Plan from Specs

#### 1. Analyze Specifications

Read all specifications and identify:
- Components to implement
- Dependencies between components
- Natural implementation order
- Integration points

#### 2. Create IMPLEMENTATION_PLAN.md

**Structure**:
```markdown
# Implementation Plan

## Phase 1: Core Infrastructure

### Data Models
- [ ] Create src/core/models.py with base models
- [ ] Write tests/unit/test_models.py
- [ ] Validate serialization/deserialization

### Task Queue
- [ ] Create src/core/task_queue.py
- [ ] Write tests/unit/test_task_queue.py
- [ ] Test FIFO behavior
- [ ] Test priority handling

### Context Memory
- [ ] Create src/core/context_memory.py
- [ ] Write tests/unit/test_context_memory.py
- [ ] Test file-based storage
- [ ] Test async operations

### Phase 1 Integration Tests
- [ ] Create tests/integration/test_phase1_infrastructure.py
- [ ] Test models + task queue integration
- [ ] Test models + context memory integration

## Phase 2: Authentication & Security

### OAuth 2.1 Implementation
- [ ] Create src/auth/oauth.py
- [ ] Write tests/unit/test_oauth.py
- [ ] Test PKCE flow
- [ ] Test token validation

### Scope Management
- [ ] Create src/auth/scopes.py
- [ ] Write tests/unit/test_scopes.py
- [ ] Test hierarchical permissions
- [ ] Test scope checking

### Phase 2 Integration Tests
- [ ] Create tests/integration/test_phase2_authentication.py
- [ ] Test full OAuth flow
- [ ] Test scope enforcement across components

... (continue for all phases)
```

**Pattern**: Each checkbox is a single, atomic task (5-15 minutes)

#### 3. Use Specifications as Reference

For each implementation task, reference the spec:
```markdown
### Component X
- [ ] Create src/component_x.py (see specs/010-component-x.md)
- [ ] Write tests/unit/test_component_x.py (test behaviors from spec)
- [ ] Implement behavior A (specs/010-component-x.md section 3.1)
- [ ] Implement behavior B (specs/010-component-x.md section 3.2)
```

**Critical**: Implementation plan references specs, but doesn't duplicate them.

---

### Phase 1.2: Copy and Customize Template Files

#### 1. Copy Template Files from gem-flux-mcp

```bash
# Assuming you're in your new project directory
GEM_FLUX_DIR="/path/to/gem-flux-mcp"
COSCIENTIST_DIR="/path/to/CogniscientAssistant"  # If available

# Core implementation loop files
mkdir -p scripts/development
cp $GEM_FLUX_DIR/docs/implementation-loop-development/to-use-later/run-implementation-loop.sh \
   scripts/development/
chmod +x scripts/development/run-implementation-loop.sh

# Implementation guidelines
cp $GEM_FLUX_DIR/docs/implementation-loop-development/to-use-later/CLAUDE.md ./

# Test infrastructure
mkdir -p tests/unit tests/integration
cp $GEM_FLUX_DIR/docs/implementation-loop-development/to-use-later/conftest.py \
   tests/
cp $GEM_FLUX_DIR/docs/implementation-loop-development/to-use-later/test_expectations.json \
   tests/integration/

# Context optimization (optional but recommended)
mkdir -p src/utils
cp $GEM_FLUX_DIR/docs/implementation-loop-development/to-use-later/context_relevance.py \
   src/utils/
```

#### 2. Customize CLAUDE.md

Edit the **Project Context** section:

```markdown
## Project Context

[Your Project Name] implementation follows these specifications:
- specs/001-system-overview.md - Overall architecture
- specs/002-core-principles.md - Design philosophy
- [Add key specs here]

## Technology Stack

- Python [version]
- [Framework 1]
- [Framework 2]
- Testing: pytest
```

#### 3. Create test_expectations.json

```json
{
  "phase_1": {
    "name": "Core Infrastructure",
    "must_pass": [
      "test_models_creation",
      "test_task_queue_fifo",
      "test_context_memory_storage"
    ],
    "may_fail": [],
    "notes": "Foundation phase - all tests must pass"
  },
  "phase_2": {
    "name": "Authentication",
    "must_pass": [
      "test_oauth_pkce_flow",
      "test_token_validation",
      "test_scope_checking"
    ],
    "may_fail": [
      "test_full_integration"
    ],
    "notes": "Integration test may fail until Phase 3 components ready"
  }
}
```

#### 4. Create pyproject.toml

```toml
[project]
name = "your-project-name"
version = "0.1.0"
description = "Your project description"
requires-python = ">=3.11"

dependencies = [
    "pydantic>=2.0.0",
    "httpx>=0.28.0",
    # Add your dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "pytest-mock>=3.14.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
markers = [
    "real_llm: tests that use actual LLM calls (not part of automated loop)",
]
```

#### 5. Update .gitignore

```bash
cat >> .gitignore << 'EOF'

# Implementation loop artifacts
.implementation_logs/
.implementation_flags
.integration_test_state
.context_optimization_disabled
.context_optimization_metrics.log
optimized_prompt.md
prompt.md
.test_output_*.tmp
.iteration_output_*.tmp

# Python build
dist/
build/
*.egg-info/
EOF
```

---

### Phase 1.3: Configure Context Optimization (Optional but Recommended)

Context optimization reduces Claude's context window by 40-90% by selecting only relevant specifications.

#### 1. Edit context_relevance.py

Update the configuration section:

```python
class SpecificationRelevanceScorer:
    def __init__(self, specs_dir: str = "specs"):
        self.specs_dir = specs_dir

        # CUSTOMIZE: Always include these critical specs
        self.critical_specs = [
            "001-system-overview.md",
            "002-core-principles.md",
            # Add your critical specs
        ]

        # CUSTOMIZE: Map component names to spec files
        self.component_map = {
            "AuthManager": "020-authentication.md",
            "OAuth": "020-authentication.md",
            "ComponentA": "030-component-a.md",
            # Add your components
        }
```

#### 2. Test Context Optimization

```bash
# Test that context optimization script works
python3 src/utils/context_relevance.py \
    "Create AuthManager class" \
    "1"  # Phase 1

# Should output:
# Selected specs:
# - 001-system-overview.md
# - 002-core-principles.md
# - 020-authentication.md
# Confidence: 0.85
```

---

### Phase 1.4: Run the Implementation Loop

#### 1. Initialize Python Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Verify pytest works
pytest --version
```

#### 2. Create Initial Commit (Before Loop)

```bash
git add -A
git commit -m "chore: setup implementation phase

- Created IMPLEMENTATION_PLAN.md from specifications
- Copied implementation loop infrastructure
- Configured test framework and quality gates
- Ready to begin test-driven development"
```

#### 3. Start the Implementation Loop

```bash
./scripts/development/run-implementation-loop.sh
```

#### 4. What Happens - Iteration Flow

**Iteration 1**:
```
=== AI-Assisted Implementation Loop ===
Phase: 1 (Core Infrastructure)
Task: Create src/core/models.py with base models

[Context Optimization]
✓ Selected 3 relevant specs (confidence: 0.82)
  - 001-system-overview.md
  - 002-core-principles.md
  - 010-data-models.md

[Invoking Claude]
Reading optimized_prompt.md...
Claude implements:
  1. Creates tests/unit/test_models.py with failing tests
  2. Creates src/core/models.py with base models
  3. Runs tests - all pass
  4. Marks task [x] in IMPLEMENTATION_PLAN.md
  5. Commits: "feat: implement base data models with tests"

[Quality Gates]
✓ Gate 1: All tests passed (4/4)
✓ Gate 2: Unit test coverage 92% (≥ 80% required)
✓ Gate 3: Integration tests N/A (Phase 1, no integration yet)
✓ Gate 4: Context optimization validated

[Iteration Success]
✅ Iteration 1 completed successfully
Recent changes: src/core/models.py, tests/unit/test_models.py
Next task: Create task queue implementation

Press Enter to continue...
```

**Iteration 2** (with failure):
```
=== AI-Assisted Implementation Loop ===
Phase: 2 (Authentication)
Task: Implement OAuth PKCE flow

[Invoking Claude]
Claude implements OAuth...

[Quality Gates]
✓ Gate 1: Tests passed (8/8)
✓ Gate 2: Unit test coverage 85% (≥ 80% required)
✗ Gate 3: Integration test REGRESSION detected!
  Previously passing: test_phase1_infrastructure
  Now failing: test_models_serialization

[Iteration Failed]
❌ REGRESSION DETECTED
Error logged to: .implementation_logs/iteration_2_failed_[timestamp].log

To investigate:
  cat .implementation_logs/latest_failed.log
  pytest tests/integration/test_phase1_infrastructure.py -v

Fix the regression, then:
  rm .implementation_flags
  ./scripts/development/run-implementation-loop.sh

Loop stopped - manual intervention required.
```

#### 5. Handle Failures

When loop stops due to failure:

**Step 1**: Investigate
```bash
# Read failure log
cat .implementation_logs/latest_failed.log

# Run failing tests
pytest tests/integration/test_phase1_infrastructure.py -v --tb=short
```

**Step 2**: Fix the issue
```bash
# Option A: Fix code manually
vim src/core/models.py

# Option B: Ask Claude for help
echo "Fix the serialization regression in models.py" | claude -p
```

**Step 3**: Verify fix
```bash
# Run tests manually
pytest tests/ -v

# Check coverage
pytest tests/unit/ --cov=src --cov-fail-under=80
```

**Step 4**: Commit fix
```bash
git add -A
git commit -m "fix: resolve serialization regression in models"
```

**Step 5**: Clear error flag and resume
```bash
rm .implementation_flags
./scripts/development/run-implementation-loop.sh
```

---

### Phase 1.5: Monitor Progress

#### 1. Check Implementation Status

```bash
# Count completed tasks
grep -c "^\- \[x\]" IMPLEMENTATION_PLAN.md

# Count remaining tasks
grep -c "^\- \[ \]" IMPLEMENTATION_PLAN.md

# Show recent commits
git log --oneline -10
```

#### 2. View Context Optimization Metrics

```bash
# See context optimization log
cat .context_optimization_metrics.log

# Example output:
# 2025-01-15T10:23:45: Task="Create AuthManager" Phase=2 Specs=4 Lines=1234 Optimized=true Confidence=0.87
# 2025-01-15T10:34:12: Task="Implement OAuth" Phase=2 Specs=5 Lines=1456 Optimized=true Confidence=0.91
```

#### 3. Review Test Coverage

```bash
# Unit test coverage
pytest tests/unit/ --cov=src --cov-report=term-missing

# Integration test coverage
pytest tests/integration/ --cov=src --cov-report=term-missing

# Full coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Advanced Features

### Real LLM Testing

For components that use AI (if applicable):

#### 1. Create Real LLM Tests

```python
# tests/integration/test_phase5_generation_real.py
import pytest

@pytest.mark.real_llm
async def test_hypothesis_generation_with_o3():
    """Test hypothesis generation uses o3 model correctly."""
    from src.agents.generation import GenerationAgent

    agent = GenerationAgent(model="o3")
    result = await agent.generate_hypothesis(
        "Why does ice float on water?"
    )

    # Test behavioral expectations (not exact output)
    assert len(result.hypothesis) > 100  # Substantive response
    assert "density" in result.hypothesis.lower()  # Key concept
    # Verify o3 shows reasoning steps
    assert "step" in result.reasoning.lower() or \
           "first" in result.reasoning.lower()
```

#### 2. Run Real LLM Tests Manually

```bash
# NOT part of automated loop (too slow/expensive)
pytest tests/integration/*_real.py -v --real-llm

# Run specific real LLM test
pytest tests/integration/test_phase5_generation_real.py::test_hypothesis_generation_with_o3 -v --real-llm
```

#### 3. Add to test_expectations.json

```json
{
  "phase_5": {
    "must_pass": ["test_generation_agent_init"],
    "real_llm_tests": [
      "test_hypothesis_generation_with_o3",
      "test_debate_generation_with_claude"
    ],
    "notes": "real_llm_tests are optional - run manually before release"
  }
}
```

---

### Disabling Context Optimization

If context optimization causes issues:

#### Temporary Disable (one iteration)
```bash
touch .context_optimization_disabled
./scripts/development/run-implementation-loop.sh
# Loop will use full context for this run
rm .context_optimization_disabled
```

#### Permanent Disable
```bash
# Edit scripts/development/run-implementation-loop.sh
# Find: optimize_context_selection
# Change to: # optimize_context_selection (commented out)
```

---

## Quality Gates Deep Dive

### Gate 1: Test Execution

**Purpose**: Ensure all required tests pass

**Behavior**:
- Runs: `pytest tests/ --tb=short -q`
- Analyzes failures against `test_expectations.json`
- Categories: CRITICAL (must_pass failed), UNEXPECTED (unlisted failed), EXPECTED (may_fail failed)

**Pass Criteria**: No CRITICAL or UNEXPECTED failures

**Example**:
```bash
# All must_pass tests pass: PASS
# Some may_fail tests fail: PASS (allowed)
# One must_pass test fails: FAIL (blocks iteration)
```

---

### Gate 2: Coverage Check

**Purpose**: Maintain code quality with 80% coverage threshold

**Behavior**:
- Runs: `pytest tests/unit/ --cov=src --cov-fail-under=80`
- Unit tests must meet 80% threshold
- Integration tests checked for information only

**Pass Criteria**: Unit test coverage ≥ 80%

**Example**:
```bash
# Coverage 92%: PASS
# Coverage 79%: FAIL
# Coverage 80%: PASS (exactly at threshold)
```

---

### Gate 3: Integration Tests & Regression Detection

**Purpose**: Catch regressions (previously passing tests now fail)

**Behavior**:
- Runs: `pytest tests/integration/test_phase{3..N}_*.py`
- Compares to `.integration_test_state` (last passing state)
- Sets `.implementation_flags` if regression detected

**Pass Criteria**: No regressions AND no CRITICAL/UNEXPECTED failures

**Example**:
```bash
# All integration tests pass: PASS
# New integration test fails (in may_fail): PASS
# Previously passing test fails: FAIL (REGRESSION)
```

---

### Gate 4: Context Optimization Validation

**Purpose**: Ensure context optimization didn't miss critical specs

**Behavior**:
- Validates selected specs against phase requirements
- Checks: critical specs included, component spec detected
- Disables optimization temporarily if validation fails

**Pass Criteria**: Validation succeeds OR optimization disabled

**Example**:
```bash
# Phase 5, selected specs include generation-agent.md: PASS
# Phase 5, selected specs missing generation-agent.md: FAIL
```

---

## Troubleshooting

### Problem: Loop stops immediately after start

**Cause**: No unchecked tasks in IMPLEMENTATION_PLAN.md

**Fix**:
```bash
# Check for tasks
grep "^\- \[ \]" IMPLEMENTATION_PLAN.md

# If empty, either:
# 1. All tasks complete (success!)
# 2. Task format wrong (fix format)
```

---

### Problem: Tests pass locally but fail in loop

**Cause**: Environment differences or test isolation issues

**Fix**:
```bash
# Run tests same way loop does
pytest tests/ --tb=short -q

# Check for:
# - Hardcoded paths
# - Time-dependent tests
# - Shared state between tests
```

---

### Problem: Context optimization misses important spec

**Cause**: Component detection failed or scoring too low

**Fix**:
```python
# Edit src/utils/context_relevance.py
# Add to component_map:
self.component_map = {
    "YourComponent": "030-your-component.md",
    # Force inclusion for specific tasks
}

# Or add to critical_specs:
self.critical_specs = [
    "001-system-overview.md",
    "030-your-component.md",  # Always include
]
```

---

### Problem: Coverage below 80% but can't reach it

**Cause**: Unreachable code or integration-only code

**Fix**:
```python
# Option 1: Exclude specific files
# Create .coveragerc
[run]
omit =
    tests/*
    src/utils/debug.py  # Exclude debug utilities

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError

# Option 2: Add more unit tests
# Focus on uncovered branches
pytest tests/unit/ --cov=src --cov-report=html
open htmlcov/index.html  # See what's uncovered
```

---

## Best Practices

### 1. Atomic Tasks

**Good**:
```markdown
- [ ] Create AuthManager class
- [ ] Write tests for AuthManager initialization
- [ ] Implement login() method
- [ ] Write tests for login() success case
- [ ] Write tests for login() failure cases
```

**Bad**:
```markdown
- [ ] Implement authentication system
- [ ] Write all authentication tests
```

**Principle**: Each checkbox = 5-15 minutes of work

---

### 2. Test-First Development

**Good**:
```markdown
- [ ] Write test_auth_login_success()
- [ ] Write test_auth_login_invalid_password()
- [ ] Implement login() method to pass tests
```

**Bad**:
```markdown
- [ ] Implement login() method
- [ ] Write tests for login()
```

**Principle**: Tests before implementation, always

---

### 3. Integration Test Placement

**Good**:
```markdown
## Phase 3 Integration Tests
- [ ] Create tests/integration/test_phase3_queue_workflow.py
- [ ] Test task submission + execution
- [ ] Test queue + context memory integration
```

**Bad**:
```markdown
## Phase 1: Core Infrastructure
- [ ] Create integration tests
```

**Principle**: Integration tests at end of each phase

---

### 4. Reference Specifications

**Good**:
```markdown
### OAuth Implementation
- [ ] Implement PKCE flow (see specs/020-authentication.md section 3.2)
- [ ] Test code_challenge generation (specs/020-authentication.md section 3.2.1)
```

**Bad**:
```markdown
### OAuth Implementation
- [ ] Implement OAuth
```

**Principle**: Link tasks to specific spec sections

---

## Completion Criteria

### When is Phase 1 Complete?

Phase 1 is complete when:

- [ ] All tasks in IMPLEMENTATION_PLAN.md marked [x]
- [ ] All must_pass tests passing
- [ ] Unit test coverage ≥ 80%
- [ ] Integration tests passing (no regressions)
- [ ] Real LLM tests passing (if applicable)
- [ ] Code committed to git
- [ ] Documentation updated (README, API docs)
- [ ] Ready for deployment/release

---

## Summary Checklist

**Before Starting Phase 1**:
- [ ] Phase 0 complete (all specs created)
- [ ] IMPLEMENTATION_PLAN.md created from specs
- [ ] Template files copied and customized
- [ ] test_expectations.json configured
- [ ] Python environment set up
- [ ] Initial commit made

**During Implementation Loop**:
- [ ] Monitor quality gates
- [ ] Investigate failures immediately
- [ ] Clear .implementation_flags after fixes
- [ ] Review context optimization metrics
- [ ] Check test coverage regularly

**After Phase 1 Completion**:
- [ ] All tasks [x] in IMPLEMENTATION_PLAN.md
- [ ] All quality gates passing
- [ ] Code coverage ≥ 80%
- [ ] Documentation complete
- [ ] Ready for release

---

## Files Reference

**Core Files**:
- `IMPLEMENTATION_PLAN.md` - Task checklist
- `CLAUDE.md` - Implementation guidelines
- `scripts/development/run-implementation-loop.sh` - Main loop
- `tests/conftest.py` - Test fixtures and mocking
- `tests/integration/test_expectations.json` - Quality criteria

**Generated Files** (gitignored):
- `.implementation_logs/` - Iteration logs
- `.implementation_flags` - Error state
- `.integration_test_state` - Test history
- `optimized_prompt.md` - Context-optimized prompt

**Optional Files**:
- `src/utils/context_relevance.py` - Context optimization
- `.context_optimization_metrics.log` - Optimization metrics

---

**You are now ready to run Phase 1!** Copy the template files, create your implementation plan, and start the loop.

For questions or issues, refer to the troubleshooting section or review the CogniscientAssistant project as a reference implementation.
