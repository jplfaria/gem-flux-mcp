# Centralized Prompt Management Proposal

**Date**: 2025-11-05
**Status**: 📋 Proposal
**Branch**: `prompts-central` (to be created)

---

## Problem Statement

Currently, all prompts in our MCP tools are **hardcoded in Python code**:
- `interpretation` messages embedded in tool files
- `next_steps` arrays scattered across 11 tools
- Difficult for non-developers to review and improve
- Hard to A/B test prompt variations
- No version control specifically for prompts
- Can't iterate on prompts without code changes

**Example**: To improve the gapfill_model interpretation message, someone needs to:
1. Find the Python file
2. Understand Python code
3. Edit strings in code
4. Test the entire tool
5. Commit code changes

---

## Research Findings

### MCP Best Practices (2024)

Based on research of MCP specification and existing implementations:

1. **MCP Native Prompts Feature** ✅
   - MCP has built-in support for prompts as first-class resources
   - Prompts are user-controlled, explicitly selected
   - Servers expose prompts; clients present them

2. **Markdown + YAML Frontmatter** ✅ (Industry Standard)
   - Markdown for human-readable prompt content
   - YAML frontmatter for metadata
   - Used by: LangChain Hub, Langfuse, multiple MCP servers

3. **Centralization Benefits**
   - Single source of truth for prompts
   - Team collaboration without code knowledge
   - Version control for prompts
   - A/B testing and optimization
   - Separation of concerns (prompts vs logic)

4. **Versioning** ✅
   - Semantic versioning (X.Y.Z)
   - Git-based version control
   - Rollback capabilities

### Examples from the Wild

**mcp-prompts server**:
- Stores prompts as markdown files
- Uses YAML frontmatter for metadata
- Centralized directory structure

**LangChain Hub**:
- Prompt templates with versioning
- Tag-based deployment (dev/prod)
- Collaborative editing

**Langfuse**:
- Version control for prompts
- Commit-based history
- UI for non-technical editing

---

## Proposed Solution

### Architecture

```
gem-flux-mcp/
├── prompts/                      # NEW: Centralized prompts directory
│   ├── interpretations/          # Interpretation messages
│   │   ├── build_model.md
│   │   ├── gapfill_model.md
│   │   └── run_fba.md
│   ├── next_steps/               # Next steps guidance
│   │   ├── build_model.md
│   │   ├── gapfill_model.md
│   │   ├── run_fba.md
│   │   ├── compound_lookup.md
│   │   └── ... (all 11 tools)
│   ├── system/                   # System-level prompts
│   │   ├── phase2_enhanced.md    # From production_config.py
│   │   └── default.md
│   └── README.md                 # Prompt authoring guide
├── src/gem_flux_mcp/
│   ├── prompts/                  # NEW: Prompt loader module
│   │   ├── __init__.py
│   │   ├── loader.py             # Load prompts from markdown
│   │   ├── renderer.py           # Template rendering (Jinja2)
│   │   └── cache.py              # Prompt caching
│   └── tools/
│       ├── build_model.py        # Uses prompt loader
│       └── ...
```

### File Format: Markdown + YAML Frontmatter

**Example: `prompts/interpretations/gapfill_model.md`**

```markdown
---
version: 1.0.0
tool: gapfill_model
type: interpretation
updated: 2025-11-05
variables:
  - num_reactions
  - num_pathways
  - growth_rate_after
  - target_growth_rate
  - gapfilling_successful
---

# Gapfilling Interpretation

## Overview

{% if gapfilling_successful %}
Added {{ num_reactions }} reactions across {{ num_pathways }} metabolic pathways. Model can now grow.
{% else %}
Added {{ num_reactions }} reactions across {{ num_pathways }} metabolic pathways. Model still cannot grow.
{% endif %}

## Growth Improvement

- **Before**: 0.0 hr⁻¹
- **After**: {{ growth_rate_after }} hr⁻¹
- **Target**: {{ target_growth_rate }} hr⁻¹
- **Met Target**: {{ "Yes" if gapfilling_successful else "No" }}

## Assessment

{% if num_reactions < 10 %}
Minimal gapfilling ({{ num_reactions }} reactions) - indicates high-quality annotation
{% elif num_reactions < 50 %}
Moderate gapfilling ({{ num_reactions }} reactions) - typical for draft models
{% else %}
Extensive gapfilling ({{ num_reactions }} reactions) - may indicate poor annotation quality
{% endif %}
```

### Benefits

1. **Team Collaboration** 👥
   - Biologists can review and improve prompts directly
   - No Python knowledge required
   - Markdown is familiar to everyone
   - Easy to track changes in Git

2. **Rapid Iteration** 🚀
   - Change prompts without touching code
   - Test prompt variations quickly
   - A/B test different phrasings
   - Hot reload in development

3. **Version Control** 📊
   - Git tracks every prompt change
   - Semantic versioning for prompts
   - Rollback to previous versions
   - Compare prompt performance over time

4. **Maintainability** 🛠️
   - Clear separation: logic vs presentation
   - Easier to review prompt quality
   - Reduced code complexity
   - Centralized documentation

5. **MCP Native** ✅
   - Follows MCP best practices
   - Compatible with MCP prompt specification
   - Could expose as MCP prompts resource later
   - Industry-standard approach

---

## Implementation Plan

### Phase 1: Setup & Infrastructure (Day 1)

1. **Create Branch**
   ```bash
   git checkout -b prompts-central
   ```

2. **Create Directory Structure**
   ```
   prompts/
   ├── interpretations/
   ├── next_steps/
   ├── system/
   └── README.md
   ```

3. **Implement Prompt Loader**
   - `src/gem_flux_mcp/prompts/loader.py` - Load markdown files
   - `src/gem_flux_mcp/prompts/renderer.py` - Jinja2 template rendering
   - `src/gem_flux_mcp/prompts/cache.py` - Cache loaded prompts

4. **Add Dependencies**
   ```toml
   # pyproject.toml
   dependencies = [
       "jinja2>=3.1.0",
       "pyyaml>=6.0",
       # ... existing deps
   ]
   ```

### Phase 2: Extract Current Prompts (Day 1-2)

5. **Extract Interpretations**
   - `prompts/interpretations/build_model.md`
   - `prompts/interpretations/gapfill_model.md`
   - `prompts/interpretations/run_fba.md`

6. **Extract Next Steps**
   - One file per tool (11 total)
   - Convert Python lists to markdown lists
   - Add YAML frontmatter with metadata

7. **Extract System Prompts**
   - `prompts/system/phase2_enhanced.md`
   - `prompts/system/default.md`
   - From `examples/argo_llm/production_config.py`

### Phase 3: Refactor Tools (Day 2-3)

8. **Update Tool Imports**
   ```python
   from gem_flux_mcp.prompts.loader import load_prompt, render_prompt
   ```

9. **Replace Hardcoded Prompts**
   ```python
   # Before:
   interpretation = {
       "overview": f"Added {num_reactions} reactions..."
   }

   # After:
   interpretation = render_prompt(
       "interpretations/gapfill_model",
       num_reactions=num_reactions,
       num_pathways=num_pathways,
       ...
   )
   ```

10. **Update All 11 Tools**
    - build_model
    - gapfill_model
    - run_fba
    - compound_lookup (search + get)
    - reaction_lookup (search + get)
    - media_builder
    - list_models
    - list_media
    - delete_model

### Phase 4: Testing (Day 3-4)

11. **Baseline Testing (BEFORE changes)**
    - Run comprehensive test suite
    - Document current behavior
    - Record test results
    - Save as `BASELINE_TESTS.md`

12. **Implementation Testing (AFTER changes)**
    - Run same comprehensive test suite
    - Verify identical behavior
    - Compare tool outputs character-by-character
    - Document any differences

13. **Claude Code Integration Test**
    - Test MCP server with Claude Code
    - Run E. coli workflow
    - Verify Phase 2 features still work
    - Compare to baseline

14. **Argo Client Test**
    - Run `test_phase2_argo.py`
    - Verify 83% score maintained
    - No regression in functionality

### Phase 5: Documentation (Day 4)

15. **Prompt Authoring Guide**
    - `prompts/README.md` - How to write prompts
    - Template examples
    - Variable conventions
    - Best practices

16. **Developer Guide**
    - How to use prompt loader in code
    - How to add new prompts
    - Caching behavior
    - Testing prompts

17. **Migration Guide**
    - Document changes for contributors
    - How to update custom forks
    - Backward compatibility notes

---

## Testing Strategy

### Pre-Implementation: Baseline Recording

**Goal**: Document exact current behavior

1. **Unit Tests**
   ```bash
   pytest tests/ -v --tb=short > BASELINE_UNIT_TESTS.txt
   ```

2. **Integration Tests**
   ```bash
   uv run python test_phase2_improvements.py > BASELINE_INTEGRATION.txt
   ```

3. **Argo Tests**
   ```bash
   uv run python examples/argo_llm/test_phase2_argo.py > BASELINE_ARGO.txt
   ```

4. **Manual Claude Code Test**
   - Run E. coli workflow in Claude Code
   - Copy entire conversation
   - Save as `BASELINE_CLAUDE_CODE.md`

5. **Tool Output Snapshots**
   - Run each tool with known inputs
   - Save JSON outputs
   - Save as `BASELINE_TOOL_OUTPUTS.json`

### Post-Implementation: Validation

**Goal**: Verify zero functional changes

1. **Run All Baseline Tests Again**
   - Compare outputs line-by-line
   - Tool outputs must be identical (except timing)
   - Phase 2 scores must match

2. **Diff Analysis**
   ```bash
   diff BASELINE_UNIT_TESTS.txt AFTER_UNIT_TESTS.txt
   diff BASELINE_INTEGRATION.txt AFTER_INTEGRATION.txt
   diff BASELINE_ARGO.txt AFTER_ARGO.txt
   ```

3. **Manual Verification**
   - Claude Code E. coli workflow
   - Compare conversation quality
   - Verify Phase 2 features work

4. **Acceptance Criteria** ✅
   - All tests pass
   - Tool outputs identical
   - No functional regressions
   - Prompts load correctly
   - Performance acceptable (<10ms per prompt load)

---

## File Format Specification

### Markdown Structure

```markdown
---
version: X.Y.Z
tool: tool_name
type: interpretation | next_steps | system
updated: YYYY-MM-DD
author: optional
variables:
  - var1
  - var2
tags:
  - optional_tag
---

# Prompt Title

Prompt content with {{ variable }} placeholders.

## Sections

Use markdown formatting:
- Lists
- **Bold**
- *Italic*
- Code blocks

{% if conditional %}
Conditional content
{% endif %}
```

### YAML Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `version` | Yes | Semantic version (X.Y.Z) |
| `tool` | Yes | Tool name this prompt belongs to |
| `type` | Yes | interpretation, next_steps, or system |
| `updated` | Yes | Last update date (YYYY-MM-DD) |
| `author` | No | Who last updated |
| `variables` | No | List of template variables |
| `tags` | No | Tags for organization |

### Template Variables

Use Jinja2 syntax:
- `{{ variable }}` - Simple substitution
- `{% if condition %}...{% endif %}` - Conditionals
- `{% for item in items %}...{% endfor %}` - Loops
- `{{ value|round(2) }}` - Filters

---

## Example Migration

### Before (Hardcoded in Python)

**File**: `src/gem_flux_mcp/tools/gapfill_model.py`

```python
# Lines 844-852
interpretation = {
    "overview": overview,
    "growth_improvement": growth_improvement,
    "gapfilling_assessment": gapfill_assessment,
}

if unknown_count > 0:
    interpretation["pathway_coverage_note"] = f"{unknown_count} of {num_reactions} reactions ({unknown_pct}%) lack pathway annotations in database"
```

### After (Centralized Prompts)

**File**: `prompts/interpretations/gapfill_model.md`

```markdown
---
version: 1.0.0
tool: gapfill_model
type: interpretation
updated: 2025-11-05
variables:
  - overview
  - growth_improvement
  - gapfill_assessment
  - unknown_count
  - num_reactions
  - unknown_pct
---

# Gapfilling Interpretation

{{ overview }}

## Growth Improvement

- Before: {{ growth_improvement.before }} hr⁻¹
- After: {{ growth_improvement.after }} hr⁻¹
- Target: {{ growth_improvement.target }} hr⁻¹
- Met Target: {{ "Yes" if growth_improvement.met_target else "No" }}

## Assessment

{{ gapfill_assessment }}

{% if unknown_count > 0 %}
**Note**: {{ unknown_count }} of {{ num_reactions }} reactions ({{ unknown_pct }}%) lack pathway annotations in database
{% endif %}
```

**File**: `src/gem_flux_mcp/tools/gapfill_model.py`

```python
from gem_flux_mcp.prompts.loader import render_prompt

# Lines 844-852
interpretation = render_prompt(
    "interpretations/gapfill_model",
    overview=overview,
    growth_improvement=growth_improvement,
    gapfill_assessment=gapfill_assessment,
    unknown_count=unknown_count,
    num_reactions=num_reactions,
    unknown_pct=unknown_pct,
)
```

**Benefits**:
- ✅ Prompt visible in markdown (easy to review)
- ✅ Non-developers can edit
- ✅ Version controlled
- ✅ Can A/B test variations
- ✅ Cleaner code

---

## Risk Analysis

### Risks

1. **Template Rendering Errors**
   - **Risk**: Syntax errors in Jinja2 templates
   - **Mitigation**: Prompt validation on load, comprehensive tests

2. **Performance Impact**
   - **Risk**: Slower tool execution due to template rendering
   - **Mitigation**: Prompt caching, benchmark before/after

3. **Complexity Increase**
   - **Risk**: New abstraction layer to maintain
   - **Mitigation**: Simple API, good documentation

4. **Backward Compatibility**
   - **Risk**: Breaking changes for contributors
   - **Mitigation**: Clear migration guide, maintain old interface initially

5. **File Not Found Errors**
   - **Risk**: Missing prompt files break tools
   - **Mitigation**: Fallback to hardcoded defaults, validation on startup

### Mitigation Strategy

1. **Gradual Rollout**
   - Start with 1-2 tools (gapfill_model, run_fba)
   - Test thoroughly
   - Expand to remaining tools

2. **Backward Compatibility**
   - Keep hardcoded prompts as fallback
   - Deprecate gradually
   - Clear migration timeline

3. **Comprehensive Testing**
   - Baseline before changes
   - Line-by-line output comparison
   - Performance benchmarks

4. **Validation on Startup**
   - Check all prompt files exist
   - Validate YAML frontmatter
   - Fail fast if issues detected

---

## Success Criteria

### Technical

- ✅ All tests pass (unit + integration)
- ✅ Tool outputs identical to baseline
- ✅ Performance impact <10ms per tool call
- ✅ Zero regressions in functionality
- ✅ Prompts load correctly from markdown
- ✅ Template rendering works with all variables

### Quality

- ✅ Code cleaner (less string formatting in tools)
- ✅ Prompts easier to read (markdown vs Python strings)
- ✅ Version control works (can see prompt history in Git)
- ✅ Documentation clear and complete

### Team

- ✅ Non-developers can edit prompts
- ✅ Team can review prompts without code knowledge
- ✅ Prompt changes tracked independently of code
- ✅ A/B testing prompts is feasible

---

## Timeline

**Estimated**: 4-5 days

| Phase | Tasks | Duration |
|-------|-------|----------|
| Phase 1 | Setup & Infrastructure | 1 day |
| Phase 2 | Extract Current Prompts | 1-2 days |
| Phase 3 | Refactor Tools | 1-2 days |
| Phase 4 | Testing & Validation | 1 day |
| Phase 5 | Documentation | 0.5 day |

**Total**: 4.5-5.5 days

---

## Alternatives Considered

### Alternative 1: JSON Files

**Pros**: Native Python support, structured data
**Cons**: Not human-friendly, hard to edit multi-line text
**Decision**: ❌ Rejected - Markdown more readable

### Alternative 2: YAML Only

**Pros**: Structured, widely used
**Cons**: Multi-line text awkward, less readable than markdown
**Decision**: ❌ Rejected - Use YAML only for metadata

### Alternative 3: Python .py Files

**Pros**: Native, no new dependencies
**Cons**: Requires Python knowledge, defeats purpose of centralization
**Decision**: ❌ Rejected - Not accessible to non-developers

### Alternative 4: Database Storage

**Pros**: Query capabilities, versioning built-in
**Cons**: Overkill, adds complexity, harder to edit
**Decision**: ❌ Rejected - Git versioning sufficient

### Alternative 5: Keep Current Approach

**Pros**: No change, works currently
**Cons**: Team can't collaborate on prompts, hard to iterate
**Decision**: ❌ Rejected - Improvement needed

---

## Recommendation

**✅ PROCEED with Markdown + YAML Frontmatter approach**

**Reasoning**:
1. Industry standard (LangChain, Langfuse, MCP servers)
2. Human-readable and editable by non-developers
3. Git-based version control works perfectly
4. Follows MCP best practices
5. Clear separation of concerns
6. Enables rapid iteration and A/B testing

**Next Steps**:
1. Review this proposal with team
2. Get approval to proceed
3. Create `prompts-central` branch
4. Record baseline tests
5. Begin Phase 1 implementation

---

## Questions for Discussion

1. **Scope**: Start with all tools or pilot with 2-3 tools first?
2. **Timeline**: 4-5 days acceptable or need faster?
3. **Versioning**: Semantic versioning for prompts or Git SHA only?
4. **Fallbacks**: Keep hardcoded prompts as fallback indefinitely or remove after X months?
5. **Hot Reload**: Support hot-reloading prompts in development?
6. **MCP Prompts**: Expose as MCP prompts resource in future?

---

**Prepared by**: Claude (AI Assistant)
**Date**: 2025-11-05
**Status**: 📋 Awaiting Review & Approval
