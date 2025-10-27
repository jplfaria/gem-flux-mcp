# Gem-Flux MCP Server Implementation Task

Read all specifications in specs/ and implement the Gem-Flux MCP Server system according to IMPLEMENTATION_PLAN.md.

## Your Task

1. **Check IMPLEMENTATION_PLAN.md**
   - If it contains "Nothing here yet" or is empty:
     - Study ALL 20 specifications in specs/ thoroughly
     - CREATE a comprehensive implementation plan with phases and tasks
     - Save this plan to IMPLEMENTATION_PLAN.md using checkbox format: `- [ ] Task description`
     - Each task should be atomic (5-15 minutes of work)
     - Exit with message: "PLAN_CREATED - Please run loop again to start implementation"
   - Otherwise:
     - Find the FIRST unchecked `- [ ]` item in the plan
     - This is your task for this iteration

2. **Study all 20 specifications** in specs/:
   - 001-system-overview.md - Overall architecture
   - 002-data-formats.md - Data structures and model ID notation (.gf)
   - 003-build-media-tool.md - Growth media creation
   - 004-build-model-tool.md - Model building (RAST, FASTA, dict)
   - 005-gapfill-model-tool.md - Gapfilling with failure handling
   - 006-run-fba-tool.md - Flux balance analysis
   - 007-database-integration.md - ModelSEED database loading
   - 008-compound-lookup-tools.md - Compound search/retrieval
   - 009-reaction-lookup-tools.md - Reaction search/retrieval
   - 010-model-storage.md - Session-based model storage
   - 011-model-import-export.md - Model I/O (future)
   - 012-complete-workflow.md - End-to-end workflows
   - 013-error-handling.md - JSON-RPC 2.0 error compliance
   - 014-installation.md - Setup and dependencies
   - 015-mcp-server-setup.md - MCP protocol configuration
   - 016-future-tools-roadmap.md - Post-MVP features
   - 017-template-management.md - ModelSEED template loading
   - 018-session-management-tools.md - list_models, list_media, delete_model
   - 019-predefined-media-library.md - Standard growth media
   - 020-documentation-requirements.md - Documentation plan

3. **Review existing implementation** in src/:
   - Understand what's already been built
   - Maintain consistency with existing code
   - Don't duplicate existing functionality

4. **Implement the selected task**:
   - **Write tests FIRST** (test-driven development)
   - Implement code to make tests pass
   - Follow specifications EXACTLY (no deviations)
   - Use .gf notation for model IDs (NOT underscore)
   - Ensure JSON-RPC 2.0 compliant errors
   - Maintain ≥80% test coverage

5. **Run quality checks** (if tools and code exist):
   - `pytest tests/` - All tests must pass
   - `pytest --cov=src --cov-report=term-missing` - Check coverage
   - Fix any failures before continuing

6. **Update IMPLEMENTATION_PLAN.md**:
   - Mark completed item as `- [x]`
   - Add sub-tasks if you discovered additional work needed
   - Keep plan organized and up-to-date

7. **Commit changes**:
   - Use descriptive commit message
   - Format: "feat: add [feature]" or "fix: resolve [issue]"
   - Include: 🤖 Generated with [Claude Code](https://claude.com/claude-code)
   - Include: Co-Authored-By: Claude <noreply@anthropic.com>

## Exit Conditions

Output "IMPLEMENTATION_COMPLETE" when:
- All items in IMPLEMENTATION_PLAN.md are marked `- [x]`
- All tests pass
- Coverage ≥ 80%
- No pending tasks remain

## Implementation Order (Suggested)

**Phase 1: Infrastructure Setup**
- Project structure, pyproject.toml, dependencies
- Package initialization (__init__.py files)

**Phase 2: Database & Templates**
- Database loading (specs 007, 017)
- Template management
- Storage infrastructure (spec 010)

**Phase 3: Core MCP Tools**
- build_media (spec 003)
- build_model (spec 004)
- gapfill_model (spec 005)
- run_fba (spec 006)

**Phase 4: Database Tools**
- Compound lookup (spec 008)
- Reaction lookup (spec 009)

**Phase 5: Session Management**
- Session tools (spec 018)
- list_models, list_media, delete_model

**Phase 6: Integration & Testing**
- Complete workflows (spec 012)
- Error handling validation (spec 013)
- End-to-end testing

## Critical Requirements

- **Python 3.11 ONLY**: Python 3.12+ removed distutils (ModelSEEDpy dependency)
- **ModelSEEDpy Fxe Fork**: Must use https://github.com/Fxe/ModelSEEDpy.git dev branch
- **Model ID Format**: Use .gf notation (e.g., "ecoli.gf") NOT underscore
- **JSON-RPC 2.0**: All errors must be compliant
- **FastMCP**: Use for all MCP tool implementations
- **Test Coverage**: Maintain ≥80% always

## Remember

- **One task per iteration** - Don't try to do everything at once
- **Specifications are canonical** - Implement exactly what they describe
- **Tests guide implementation** - Write tests first, then code
- **Commit working code only** - Each iteration should have passing tests
- **Incremental progress** - Small, tested steps are better than big leaps

---

*This is a metabolic modeling MCP server, not a multi-agent AI system.*
