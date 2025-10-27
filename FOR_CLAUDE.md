# FOR CLAUDE: Critical Context About This Project

**READ THIS FIRST when you start working in this repository!**

---

## ⚠️ CURRENT STATUS: PHASE 1 IMPLEMENTATION IN PROGRESS

This is **NOT** a template repository. This is an **ACTIVE IMPLEMENTATION** of the Gem-Flux MCP Server.

### What Phase Are We In?

**✅ Phase 0 Complete**: All 20 specifications created and validated
**🔄 Phase 1 Active**: Implementation loop running (9/100 tasks complete)
**⏭️ Phase 2**: Not started

---

## 🚫 DO NOT CONFUSE WITH

This repository contains **TWO THINGS**:

### 1. **METHODOLOGY DOCUMENTATION** (in `/docs/`)
- Phase 0 guide (cleanroom spec generation)
- Phase 1 guide (implementation loop)
- Template files for NEW projects
- **Location**: `/docs/PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md`, `/docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md`
- **Purpose**: Teaching materials for applying methodology to OTHER projects

### 2. **ACTUAL GEM-FLUX IMPLEMENTATION** (everywhere else)
- 20 specifications in `/specs/`
- Implementation plan in `IMPLEMENTATION_PLAN.md` (100 tasks)
- Actual Python code in `/src/gem_flux_mcp/`
- Tests in `/tests/`
- **Purpose**: Building the actual Gem-Flux MCP Server

---

## 📍 WHERE ARE WE NOW?

Check `IMPLEMENTATION_PLAN.md` to see current progress:

```bash
# Count completed tasks
grep -c "^\- \[x\]" IMPLEMENTATION_PLAN.md

# Count remaining tasks
grep -c "^\- \[ \]" IMPLEMENTATION_PLAN.md

# Find current task
grep -A 3 "^\- \[ \]" IMPLEMENTATION_PLAN.md | head -5
```

**Current Status** (as of last update):
- ✅ Tasks 1-9: Complete (Foundation & Infrastructure)
- 🔄 Task 10: Next to implement
- ⏳ Tasks 11-100: Pending

---

## 🎯 WHAT TO DO WHEN ASKED TO WORK

### If User Says: "Continue implementation" or "Run the loop"

**DO THIS**:
1. Read `IMPLEMENTATION_PLAN.md`
2. Find FIRST unchecked `[ ]` task
3. Read relevant specifications in `/specs/`
4. Write tests FIRST
5. Implement code to pass tests
6. Mark task `[x]` in IMPLEMENTATION_PLAN.md
7. Commit changes

**DON'T DO THIS**:
- ❌ Create a new IMPLEMENTATION_PLAN.md
- ❌ Ask if they want to start Phase 0 (already done)
- ❌ Offer to generate specifications (already done)
- ❌ Confuse this with template documentation

### If User Says: "What's the status?"

**DO THIS**:
1. Check `IMPLEMENTATION_PLAN.md` for progress
2. Look at recent commits (`git log --oneline | head -10`)
3. Report: "You're on Task N of 100. Phase X in progress."

**DON'T DO THIS**:
- ❌ Say "You need to create IMPLEMENTATION_PLAN.md"
- ❌ Say "Phase 0 hasn't started yet"

---

## 🗂️ PROJECT STRUCTURE REFERENCE

```
gem-flux-mcp/
├── src/gem_flux_mcp/          # ACTUAL IMPLEMENTATION (work here)
│   ├── __init__.py
│   ├── server.py              # MCP server (Phase 8)
│   ├── logging.py             # ✅ Task 7 complete
│   ├── errors.py              # ✅ Task 8 complete
│   ├── types.py               # ✅ Task 9 complete
│   └── [more to come]
│
├── tests/                      # ACTUAL TESTS (work here)
│   ├── unit/
│   └── integration/
│
├── specs/                      # SPECIFICATIONS (read these)
│   ├── 001-system-overview.md
│   └── ... (20 total)
│
├── IMPLEMENTATION_PLAN.md      # TASK LIST (check progress here)
│
├── docs/                       # METHODOLOGY GUIDES (for reference only)
│   ├── PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md
│   ├── PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md
│   └── implementation-loop-development/
│       └── to-use-later/       # Template files for OTHER projects
│
├── CLAUDE.md                   # GUIDELINES (read during implementation)
└── FOR_CLAUDE.md               # THIS FILE (read first!)
```

---

## 🔍 HOW TO CHECK CURRENT STATE

### Quick Status Check

```bash
# Where are we in the plan?
echo "Completed: $(grep -c '^\- \[x\]' IMPLEMENTATION_PLAN.md)/100"
echo "Remaining: $(grep -c '^\- \[ \]' IMPLEMENTATION_PLAN.md)/100"

# What's the next task?
echo "Next task:"
grep -B 1 "^\- \[ \]" IMPLEMENTATION_PLAN.md | head -3

# Recent progress
git log --oneline --grep="^feat: complete Task" | head -5
```

### Phase Detection

```bash
# What phase are we in?
if [ $(grep -c "^\- \[ \]" IMPLEMENTATION_PLAN.md) -eq 0 ]; then
    echo "✅ ALL TASKS COMPLETE"
elif grep -B 5 "^\- \[ \]" IMPLEMENTATION_PLAN.md | grep -q "Phase 1:"; then
    echo "🔄 Phase 1: Foundation & Infrastructure"
elif grep -B 5 "^\- \[ \]" IMPLEMENTATION_PLAN.md | grep -q "Phase 2:"; then
    echo "🔄 Phase 2: Database & Templates"
# ... etc
fi
```

---

## ❓ COMMON CONFUSION SCENARIOS

### Scenario 1: "Do you have an implementation plan?"

**WRONG ANSWER**: "No, you need to create one first"

**RIGHT ANSWER**: "Yes, IMPLEMENTATION_PLAN.md exists with 100 tasks. You're currently at task N."

---

### Scenario 2: "What's been happening in the iterations?"

**WRONG ANSWER**: "The loop creates specifications"

**RIGHT ANSWER**: "The implementation loop has completed tasks 1-9, implementing logging, errors, and types modules with full test coverage."

---

### Scenario 3: "Should we run the spec loop?"

**WRONG ANSWER**: "Yes, let's generate specifications"

**RIGHT ANSWER**: "Specifications are already complete (20 specs in /specs/). You're in Phase 1 implementation. The implementation loop should continue."

---

### Scenario 4: "Are we ready for Phase 1?"

**WRONG ANSWER**: "Yes, let me help you set up Phase 1"

**RIGHT ANSWER**: "You're already IN Phase 1. Task 9 is complete, Task 10 is next."

---

## 📋 QUICK DECISION TREE

```
User asks to work on project
    │
    ├─ Mentions "spec" or "specification"
    │   └─> They're asking about Phase 0 (ALREADY DONE)
    │       └─> Check /specs/ directory (20 files exist)
    │           └─> Answer: "Specs complete, implementation in progress"
    │
    ├─ Mentions "implement" or "code" or "loop"
    │   └─> They're asking about Phase 1 (IN PROGRESS)
    │       └─> Check IMPLEMENTATION_PLAN.md
    │           └─> Find next [ ] task
    │               └─> Implement that task
    │
    ├─ Asks "status" or "progress"
    │   └─> Count [x] vs [ ] in IMPLEMENTATION_PLAN.md
    │       └─> Report progress (X/100 tasks complete)
    │
    └─ Asks "what's happening"
        └─> Check git log for recent commits
            └─> Report recent task completions
```

---

## 💾 FILES TO CHECK FIRST

When you start working, check these files IN ORDER:

1. **THIS FILE** (`FOR_CLAUDE.md`) - Read this first!
2. **IMPLEMENTATION_PLAN.md** - See what tasks are done/pending
3. **git log --oneline | head -10** - See recent work
4. **CLAUDE.md** - Read implementation guidelines
5. **specs/** - Read relevant specifications for current task

---

## 🚨 CRITICAL REMINDERS

1. **This is NOT a template** - It's an active implementation
2. **Phase 0 is DONE** - All 20 specs exist in /specs/
3. **Phase 1 is IN PROGRESS** - Check IMPLEMENTATION_PLAN.md for current task
4. **Documentation in /docs/ is for OTHER projects** - Not for this one
5. **IMPLEMENTATION_PLAN.md is the source of truth** - Check it first

---

## 🎯 WHEN IN DOUBT

**Ask yourself**: "Am I being asked to implement code, or to teach someone methodology?"

- **Implement code**: Work on tasks in IMPLEMENTATION_PLAN.md
- **Teach methodology**: Reference docs in /docs/ (but this project is past that phase)

**If still confused**: Check IMPLEMENTATION_PLAN.md first. It will tell you exactly what to do next.

---

## 📊 PROJECT METRICS (Updated Regularly)

**Phase 0 (Specification)**:
- Status: ✅ Complete
- Deliverables: 20 specifications
- Location: /specs/

**Phase 1 (Implementation)**:
- Status: 🔄 In Progress
- Progress: 9/100 tasks (9%)
- Current: Task 10 - Write unit tests for infrastructure
- Location: src/gem_flux_mcp/, tests/

**Test Coverage**:
- Current: >80% (meeting threshold)
- Target: ≥80% at all times
- Recent: 100% (logging), 100% (errors), 99.18% (types)

---

## 🔄 LAST UPDATED

This file should be updated whenever:
- Phase changes (e.g., Phase 1 → Phase 2)
- Major milestone reached (e.g., 50/100 tasks complete)
- Confusion detected (add to Common Confusion Scenarios)

**Last Update**: 2025-10-27
**Current Phase**: Phase 1 - Foundation & Infrastructure
**Current Task**: Task 10 of 100
**Next Phase**: Phase 2 starts at Task 11

---

**Remember**: When in doubt, `grep "^\- \[" IMPLEMENTATION_PLAN.md` shows the truth!
