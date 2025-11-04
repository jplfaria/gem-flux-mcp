# Document Deep Dive Review Changes

**PURPOSE**: Use this prompt after making changes based on a deep dive review and before restarting the implementation loop.

**WHEN TO USE**:
1. After running `.prompts/deep-review.md` and reviewing iteration
2. After making changes based on review findings
3. Before restarting the implementation loop

---

## Instructions for Claude

You need to document the deep dive review session according to the structure in `docs/deep-dive-reviews/`.

### Step 1: Gather Information

Ask the user these questions:

1. **Which iteration was reviewed?**
   - Example: "Iteration 10"

2. **What files were changed during the review?**
   - Example: "tests/unit/test_run_fba.py, tests/unit/test_atp_media_loader.py"
   - Tip: User can provide `git diff --name-only HEAD~2..HEAD` output

3. **What was the nature of the changes?**
   - Bug fixes
   - Quality improvements
   - Pattern implementation
   - Systematic fix for recurring issue
   - Architecture validation

4. **Approximately how much time was invested?**
   - Example: "About 60 minutes"

5. **Were any new patterns discovered or were existing patterns applied?**
   - New pattern (needs new pattern file)
   - Applied existing pattern (link to pattern)
   - No patterns (just changes)

### Step 2: Determine Session Number

Read `docs/deep-dive-reviews/README.md` to find the next session number.

### Step 3: Create Session Document

Using the template at `docs/deep-dive-reviews/sessions/template.md`, create a new session file:

**Filename**: `docs/deep-dive-reviews/sessions/session-XX-iteration-YY.md`

**Content should include**:
- Full before/after code examples for each change
- Clear explanation of why each change matters
- "Loop vs Manual" analysis
- Summary statistics
- Key lessons learned
- ROI analysis (high/medium/low with justification)

### Step 4: Update README.md

Update `docs/deep-dive-reviews/README.md`:

1. **Quick Stats table**: Increment totals
2. **Review Sessions section**: Add new session to tables
3. **Patterns Discovered section**: Add new pattern if applicable
4. **Next Review section**: Update recommendation

### Step 5: Update ROI Analysis

Update `docs/deep-dive-reviews/metrics/roi-analysis.md`:

1. **Aggregate Statistics table**: Update totals
2. **Per-Session Breakdown**: Add new session entry
3. **Cost-Benefit Analysis**: Recalculate ROI ratio
4. **Last Updated**: Update date

### Step 6: Create Pattern Document (if needed)

If a new pattern was discovered, create:

**Filename**: `docs/deep-dive-reviews/patterns/pattern-name.md`

**Content should include**:
- Problem description
- Root cause (if applicable)
- Solution/template
- Examples (before/after)
- Benefits
- Loop improvement opportunities
- Related files and sessions
- Impact analysis

### Step 7: Commit Everything

Create a single commit with all documentation:

```bash
git add docs/deep-dive-reviews/
git commit -m "docs: add Review Session X for Iteration Y

[Brief summary of what was reviewed and key findings]

Files changed: N
Time invested: N minutes
ROI: [High/Medium/Low]
Key impact: [One sentence summary]

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 8: Confirm Completion

Provide a summary to the user:

```
✅ Review documentation complete!

Created:
- docs/deep-dive-reviews/sessions/session-XX-iteration-YY.md
- [docs/deep-dive-reviews/patterns/pattern-name.md] (if applicable)

Updated:
- docs/deep-dive-reviews/README.md
- docs/deep-dive-reviews/metrics/roi-analysis.md

Committed: [commit hash]

You can now restart the implementation loop with confidence that this review is properly documented.
```

---

## Example Usage

**User prompt**:
```
I just finished making changes from the deep dive review of iteration 10.
I want to document everything before restarting the loop.

[Paste this file content, or just: cat .prompts/document-review.md]
```

**Claude response**:
```
I'll help you document the deep dive review. Let me ask a few questions:

1. Which iteration was reviewed?
2. What files were changed during the review?
3. What was the nature of the changes?
4. How much time was invested?
5. Were any new patterns discovered?
```

---

## Tips for Users

### Get Changed Files Quickly
```bash
# Show files changed in last 2 commits
git diff --name-only HEAD~2..HEAD

# Show files changed since last tag
git diff --name-only v1.0..HEAD

# Show files changed in specific commits
git diff --name-only abc123..def456
```

### Get Change Summary
```bash
# Show commit messages for context
git log --oneline -5

# Show detailed changes
git diff HEAD~2..HEAD
```

### Quick Time Estimate
- Small changes (1-2 files): ~20-30 minutes
- Medium changes (3-5 files): ~45-60 minutes
- Large systematic fixes: ~60-90 minutes

---

## What This Achieves

✅ **Structured Documentation**: Consistent format across all reviews
✅ **Pattern Extraction**: Reusable patterns documented separately
✅ **ROI Tracking**: Clear visibility into review value
✅ **Knowledge Preservation**: Future developers can learn from reviews
✅ **Loop Improvement**: Identifies opportunities for loop enhancement

---

**Last Updated**: 2025-10-28
**Version**: 2.0 (restructured documentation)
