# Deep Implementation Review Prompt

**IMPORTANT**: When using this prompt, also provide the log file path like:
```
Log file: .implementation_logs/iteration_X_success_YYYY-MM-DD_HH-MM-SS.log
```

Review the most recent implementation log and perform a comprehensive code quality analysis:

**TASK:** Perform Option D analysis (Phase Boundary Reviews + Spot Checks for critical tools)

## INSTRUCTIONS

1. Identify which iteration this is and detect if it's a phase boundary
2. Read the actual implementation code (not just the log summary)
3. Compare implementation against relevant specifications
4. Check integration with existing code
5. Evaluate if setup is appropriate for future work
6. **Check if any suggested changes require loop restart**
7. Provide FINDINGS ONLY - no immediate changes

## ANALYSIS CHECKLIST

### Code Quality
- Does implementation follow established patterns?
- Are functions well-designed and maintainable?
- Is error handling comprehensive?
- Are edge cases covered?

### Specification Compliance
- Read the relevant spec(s) mentioned in the log
- Compare spec requirements against actual implementation
- Identify any missing features or deviations
- Verify data formats match specifications

### Integration & Compatibility
- Does new code integrate cleanly with existing modules?
- Are APIs consistent with previous tools?
- Will this work with upcoming phases?
- Any architectural concerns?

### Test Coverage Analysis
- Are tests truly comprehensive or just hitting coverage numbers?
- Are important edge cases tested?
- Mock usage appropriate?
- Any test smells or anti-patterns?

### Future-Proofing
- Will this design support Phase 6+ requirements?
- Any technical debt being introduced?
- Extensibility considerations?

### Loop Restart Detection
**Check if any suggested changes affect these files:**
- ❌ `scripts/development/run-implementation-loop.sh` → RESTART REQUIRED
- ❌ `scripts/development/run-quality-gates.sh` → RESTART REQUIRED
- ❌ `scripts/development/context-optimizer.py` → RESTART REQUIRED
- ❌ Any `.py` files imported by loop scripts → RESTART REQUIRED
- ✅ `src/**/*.py` (application code) → Safe while paused
- ✅ `tests/**/*.py` (test code) → Safe while paused
- ✅ `docs/**/*.md` (documentation) → Safe while paused
- ✅ `specs/**/*.md` (specifications) → Safe while paused
- ✅ `.prompts/**/*.md` (prompts) → Safe while paused

**Rule**: If ANY suggested change is ❌, mark "Loop Restart Required: YES"

## DETECTION RULES

- **If phase just completed:** THOROUGH analysis of entire phase
- **If critical tool (build_model, gapfill_model, run_fba):** DEEP analysis
- **Otherwise:** SPOT CHECK one new module

## OUTPUT FORMAT

### Review Summary
- Iteration: [number]
- Phase Status: [in progress / boundary detected]
- Analysis Depth: [thorough / deep / spot check]
- **Loop Restart Required**: [YES / NO - only YES if changes affect loop scripts]

### ⚠️ Loop Restart Notice (if applicable)

**IF any suggested changes modify loop infrastructure files, include this section:**

```
🔄 LOOP RESTART REQUIRED

The suggested changes modify loop infrastructure. After applying changes:

1. Ctrl+C to stop the current loop
2. Apply the suggested changes
3. Commit the changes
4. Restart loop: ./scripts/development/run-implementation-loop.sh

Files that require restart if modified:
- scripts/development/run-implementation-loop.sh
- scripts/development/run-quality-gates.sh
- scripts/development/context-optimizer.py
- Any Python files imported by loop scripts

All other changes (src/, tests/, docs/, specs/) can be applied while loop is paused.
```

**IF no changes require restart (most common), simply state:**
```
✅ NO LOOP RESTART REQUIRED

All suggested changes are to application code (src/tests/docs) and can be
applied while the loop is paused between iterations.
```

### Findings

#### ✅ Strengths
[List what's done well]

#### ⚠️ Concerns
[Precise issues found, with file:line references]

#### 🔧 Suggested Changes
[Very specific, actionable suggestions with exact locations]
[NO immediate implementation - just documented recommendations]

**For each suggestion, indicate:**
- File path and line numbers
- Exact change needed
- ⚠️ **If file is in scripts/development/**: Mark as "REQUIRES LOOP RESTART"
- ✅ **If file is in src/tests/docs/specs/**: Mark as "Safe to apply while paused"

#### 📊 Spec Compliance
[Comparison against specifications]

#### 🔮 Future Considerations
[Architectural notes for upcoming phases]

---

## Usage Instructions

**How to use this prompt:**

1. After iteration completes, you'll see:
   ```
   Log saved to: .implementation_logs/iteration_X_success_YYYY-MM-DD_HH-MM-SS.log
   ```

2. Run these commands together:
   ```bash
   cat .prompts/deep-review.md
   echo ""
   echo "Log file: .implementation_logs/iteration_X_success_YYYY-MM-DD_HH-MM-SS.log"
   ```

3. Paste the output to Claude

**Alternative (even better):**
```bash
cat .prompts/deep-review.md && echo -e "\n---\nLog file: $(ls -t .implementation_logs/iteration_*_success_*.log | head -1)"
```
This automatically finds the most recent success log!

**What happens:**
- Claude reads the prompt instructions
- Claude automatically finds and reads the specified log file
- Auto-detects phase boundaries and adjusts depth accordingly
- Provides findings without disrupting implementation loop
- Save findings to decide when/if to apply changes

## When to Use

- ✅ After every iteration for continuous validation
- ✅ At phase boundaries (auto-detected for thorough review)
- ✅ Before major tools (build_model, gapfill_model, run_fba)
