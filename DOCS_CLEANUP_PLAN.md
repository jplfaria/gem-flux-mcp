# Documentation Cleanup Plan

**Created**: 2025-10-29
**Status**: Ready to execute after Phase 11 completion
**Goal**: Simplify root directory and improve AI/developer navigation

---

## Current State Analysis

### Issues Identified

1. **Root directory clutter**: 19 .md files with unclear hierarchy
2. **Phase 11 context spread across 4 files** (redundancy)
3. **Historical Phase 0 files mixed with active docs** (confusion)
4. **Git shows deleted files** (uncommitted moves)
5. **No directory-level README files** to guide navigation

### Documentation Structure is SOUND ✅

The core hierarchy is clear:
```
specs/ → IMPLEMENTATION_PLAN.md → NEXT_TASK.md → docs/PHASE_11_*.md
```

**Problem is presentation**, not organization.

---

## Priority 1: Immediate (Execute Before Next Loop)

### A. Commit Git File Moves

**Issue**: Files moved but deletion not committed

```bash
# Files exist but git shows as deleted:
# docs/PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md
# docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md

# They're actually at:
# docs/spec-development/PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md
# docs/implementation-loop-development/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md

# Fix:
git add docs/spec-development/
git add docs/implementation-loop-development/
git rm docs/PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md
git rm docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md
git commit -m "docs: finalize methodology guide reorganization into subdirectories"
```

**Impact**: Prevents broken references and git confusion

---

## Priority 2: After Phase 11 Complete

### A. Archive Historical Files

Create `docs/archive/` structure:

```bash
# Create archive directories
mkdir -p docs/archive/phase-0/
mkdir -p docs/archive/phase-11/
mkdir -p docs/archive/sessions/

# Archive Phase 0 files (historical, no longer needed)
mv SPECS_PLAN.md docs/archive/phase-0/
mv SPECS_CLAUDE.md docs/archive/phase-0/
mv specs-prompt.md docs/archive/phase-0/
mv CONFLICT_RESOLUTION_PLAN.md docs/archive/phase-0/
mv PHASE_1_PREPARATION_PLAN.md docs/archive/phase-0/
mv SOURCE_MATERIALS_SUMMARY.md docs/archive/phase-0/

# Archive session summaries
mv CONVERSATION_SUMMARY_*.md docs/archive/sessions/
mv REVIEW_SUMMARY.md docs/archive/sessions/

git add docs/archive/
git commit -m "docs: archive Phase 0 and session files (historical reference)"
```

### B. Consolidate Phase 11 Context

**Issue**: Phase 11 rationale explained in 4 places

**Files**:
- `MCP_INTEGRATION_STATUS.md` (executive summary)
- `IMPLEMENTATION_PLAN_AUDIT.md` (why Phase 8 incomplete)
- `YOUR_QUESTIONS_ANSWERED.md` (Q&A format)
- `IMPLEMENTATION_PLAN_UPDATED.md` (update log)

**Solution**: Create single comprehensive document

```bash
# Create consolidated doc
cat > docs/PHASE_11_COMPLETE_CONTEXT.md << 'EOF'
# Phase 11 MCP Integration - Complete Context

**Why Phase 11 Was Created**

Phase 8 MCP Server Setup was attempted but incomplete (40% done).
Server skeleton exists but crashes on startup due to Pydantic
schema errors when DatabaseIndex is in tool signatures.

**The Problem (Phase 8)**

FastMCP cannot serialize non-JSON types (DatabaseIndex, MSMedia).
Attempted to pass these directly in tool signatures → schema error.

**The Solution (Phase 11)**

Use global state pattern:
- Store DatabaseIndex/templates as global variables in server.py
- Access via get_db_index() and get_templates() functions
- MCP tool signatures only contain JSON-serializable types
- Wrappers call core functions with injected dependencies

**Implementation Status**

- Task 11.1: ✅ COMPLETE (mcp_tools.py created)
- Task 11.2: 🔄 IN PROGRESS (refactor server.py)
- Task 11.3: ⏸️ PENDING (integration tests)
- Task 11.4: ⏸️ PENDING (documentation)
- Task 11.5: ⏸️ PENDING (test client)

**Key Documents**

- Implementation Guide: docs/PHASE_11_MCP_INTEGRATION_PLAN.md
- Technical Spec: specs/021-mcp-tool-registration.md
- Current Task: NEXT_TASK.md

**Critical Lessons**

1. FastMCP requires JSON-serializable signatures
2. Global state pattern solves Pydantic serialization
3. Import mcp_tools INSIDE create_server() (avoid circular import)
4. Verify server starts after each change
5. Test with real MCP client before marking complete

---

*This document consolidates:*
- MCP_INTEGRATION_STATUS.md
- IMPLEMENTATION_PLAN_AUDIT.md
- YOUR_QUESTIONS_ANSWERED.md
- IMPLEMENTATION_PLAN_UPDATED.md
EOF

# Move originals to archive
mv MCP_INTEGRATION_STATUS.md docs/archive/phase-11/
mv IMPLEMENTATION_PLAN_AUDIT.md docs/archive/phase-11/
mv YOUR_QUESTIONS_ANSWERED.md docs/archive/phase-11/
mv IMPLEMENTATION_PLAN_UPDATED.md docs/archive/phase-11/

git add docs/PHASE_11_COMPLETE_CONTEXT.md docs/archive/phase-11/
git commit -m "docs: consolidate Phase 11 context into single comprehensive document"
```

### C. Update Root README Navigation

Add explicit documentation structure section:

```markdown
## 📚 Documentation Structure

### Active Implementation
- **[README.md](README.md)** - You are here (installation & usage)
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - 100-task master plan (Phases 1-11)
- **[NEXT_TASK.md](NEXT_TASK.md)** - Current task for implementation loop
- **[specs/](specs/)** - 21 authoritative behavioral specifications
- **[docs/](docs/)** - Implementation guides, patterns, reviews

### For AI Implementation Loop
- **[CLAUDE.md](CLAUDE.md)** - Implementation guidelines and patterns
- **[FOR_CLAUDE.md](FOR_CLAUDE.md)** - Phase clarifications

### Methodology (Reusable Process)
- **[docs/spec-development/](docs/spec-development/)** - Phase 0: Cleanroom Specifications
- **[docs/implementation-loop-development/](docs/implementation-loop-development/)** - Phase 1: Implementation Loop

### Archive
- **[docs/archive/](docs/archive/)** - Historical files (Phase 0, sessions)
```

---

## Priority 3: Long-term Improvements

### A. Create Directory README Files

**docs/README.md**:
```markdown
# Documentation Index

## 🎯 Current Work
- [Phase 11 MCP Integration Plan](PHASE_11_MCP_INTEGRATION_PLAN.md)
- [Phase 11 Complete Context](PHASE_11_COMPLETE_CONTEXT.md)

## 📖 Methodology Guides
- [Phase 0: Cleanroom Specifications](spec-development/)
- [Phase 1: Implementation Loop](implementation-loop-development/)

## 🔍 Technical References
- [ModelSEEDpy API Reference](MODELSEEDPY_API_REFERENCE.md)
- [COBRApy API Reference](COBRAPY_API_REFERENCE.md)
- [Testing Guidelines](testing-guidelines.md)

## 🎨 Architectural Patterns
- [Deep Dive Reviews](deep-dive-reviews/) - 10 sessions, 7 extracted patterns
- [MSMedia DictList Handling](deep-dive-reviews/patterns/msmedia-dictlist-handling.md)
- [Global State MCP Wrappers](deep-dive-reviews/patterns/global-state-mcp-wrappers.md)
- [Mandatory Verification Gates](deep-dive-reviews/patterns/mandatory-verification-gates.md)

## 🗄️ Archive
- [Phase 0 Historical Files](archive/phase-0/)
- [Phase 11 Context Evolution](archive/phase-11/)
- [Session Summaries](archive/sessions/)
```

**specs/README.md**:
```markdown
# Specifications Index

Authoritative behavioral specifications generated via Phase 0 cleanroom methodology.
These define **WHAT** the system does (not HOW to implement).

## 🏗️ Core System (7 specs)
- [001: System Overview](001-system-overview.md) - Architecture and design
- [002: Data Formats](002-data-formats.md) - Types, schemas, model IDs
- [007: Database Integration](007-database-integration.md) - ModelSEED loading
- [010: Model Storage](010-model-storage.md) - Session-based storage
- [013: Error Handling](013-error-handling.md) - JSON-RPC error codes
- [014: Installation](014-installation.md) - Setup and dependencies
- [015: MCP Server Setup](015-mcp-server-setup.md) - MCP protocol

## 🛠️ Core Tools (4 specs)
- [003: Build Media](003-build-media-tool.md)
- [004: Build Model](004-build-model-tool.md)
- [005: Gapfill Model](005-gapfill-model-tool.md)
- [006: Run FBA](006-run-fba-tool.md)

## 🔎 Database Tools (2 specs)
- [008: Compound Lookup](008-compound-lookup-tools.md)
- [009: Reaction Lookup](009-reaction-lookup-tools.md)

## 💾 Session Tools (3 specs)
- [018: Session Management](018-session-management-tools.md) - list_models, list_media, delete_model

## 🧪 Supporting Features (5 specs)
- [012: Complete Workflow](012-complete-workflow.md) - End-to-end examples
- [017: Template Management](017-template-management.md) - ModelSEED templates
- [019: Predefined Media Library](019-predefined-media-library.md) - 4 standard media
- [020: Documentation Requirements](020-documentation-requirements.md)
- [021: MCP Tool Registration](021-mcp-tool-registration.md) - Phase 11 global state

## 🚀 Future (2 specs)
- [011: Model Import/Export](011-model-import-export.md) - Not MVP (future)
- [016: Future Tools Roadmap](016-future-tools-roadmap.md) - Post-MVP features

---

**Total**: 21 specifications covering complete MVP + Phase 11 MCP integration
```

**specs-source/README.md**:
```markdown
# Source Materials (Phase 0 Input)

⚠️ **READ-ONLY**: These files were used to generate `specs/` during Phase 0.

## Purpose

External knowledge sources (API docs, frameworks, research) that informed
specification generation. Not authoritative - see `specs/` for final specs.

## Structure

- **guidelines.md** - Specification writing standards
- **references/** - External documentation (ModelSEED, COBRApy, FastMCP, MCP)
- **argo_llm_documentation/** - Argo LLM API docs (RAST annotation)
- **MODELSEED_TEMPLATE_OBJECT_REFERENCE.md** - Technical reference

## Usage

Phase 0 cleanroom process: AI reads these → generates `specs/`
Phase 1 implementation: AI reads `specs/` (not specs-source/)

Do not modify during implementation.
```

### B. Add Quick Reference Comment to Key Files

At top of `IMPLEMENTATION_PLAN.md`:
```markdown
<!--
📍 YOU ARE HERE: Master implementation task list (100 tasks, Phases 1-11)
📖 CURRENT TASK: See NEXT_TASK.md for current work
📋 SPECIFICATIONS: See specs/ for authoritative requirements
📚 GUIDES: See docs/ for implementation guides and patterns
-->
```

At top of `NEXT_TASK.md`:
```markdown
<!--
📍 YOU ARE HERE: Current task for implementation loop
📋 MASTER PLAN: IMPLEMENTATION_PLAN.md (100 tasks)
📖 IMPLEMENTATION GUIDE: docs/PHASE_11_MCP_INTEGRATION_PLAN.md
📄 TECHNICAL SPEC: specs/021-mcp-tool-registration.md
-->
```

---

## Execution Timeline

### Immediate (Before Next Loop Run)
- [x] Fix notebook syntax error ✅ DONE (commit e586ca5)
- [ ] Commit git file moves (Priority 1.A)

### After Phase 11 Complete
- [ ] Archive historical files (Priority 2.A)
- [ ] Consolidate Phase 11 context (Priority 2.B)
- [ ] Update root README navigation (Priority 2.C)

### When Time Permits
- [ ] Create directory README files (Priority 3.A)
- [ ] Add quick reference comments (Priority 3.B)

---

## Success Metrics

### Before Cleanup
- Root directory: 19 .md files (unclear purpose)
- Phase 11 context: 4 separate files
- No directory READMEs

### After Cleanup
- Root directory: ~8-10 .md files (clear active docs)
- Phase 11 context: 1 comprehensive file
- Directory READMEs: 3 navigation guides (docs/, specs/, specs-source/)
- Archive: ~15 historical files properly organized

### AI Navigation Improvement
- ✅ Specifications easy to find (specs/)
- ✅ Current task explicit (NEXT_TASK.md)
- ✅ Implementation guides clear (docs/PHASE_11_*.md)
- ✅ Supporting context discoverable (directory READMEs)
- ✅ Historical files separated (docs/archive/)

---

## Notes

**Don't break the loop**: All cleanup should happen AFTER Phase 11 completion.
The current structure works - we're just improving clarity.

**Keep it simple**: Archive old files, consolidate duplicates, add READMEs.
Don't restructure fundamentally - the hierarchy is sound.

**Test after changes**: Verify implementation loop can still find:
- specs/021-mcp-tool-registration.md
- docs/PHASE_11_MCP_INTEGRATION_PLAN.md
- NEXT_TASK.md
- IMPLEMENTATION_PLAN.md
