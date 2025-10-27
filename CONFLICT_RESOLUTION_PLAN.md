# Specification Conflict Resolution Plan

**Date**: October 27, 2025
**Status**: Ready for Approval
**Total Conflicts Found**: 14
**Total Text Replacements Needed**: 91 occurrences across 11 files

---

## Critical Decisions Required

### DECISION 1: Model ID State Suffix Format ✅ RESOLVED
**Decision**: Use **DOT notation** (`.draft`, `.gf`, `.draft.gf`)
**Rationale**:
- More readable and clear separation from base name
- Aligns with file extension conventions
- Already implemented in 002, 004, 010, 017, 018 specs

**Action Required**: Fix 91 occurrences of underscore format (`_gf`) → dot format (`.gf`)

### DECISION 2: RAST Annotation Default ✅ RESOLVED
**Decision**: RAST annotation **enabled by default** (`annotate_with_rast=true`)
**Rationale**:
- User explicitly requested RAST as default
- Provides better annotation quality
- Offline mode available via `annotate_with_rast=false`

**Action Required**: Already implemented in 004-build-model-tool.md, no changes needed

### DECISION 3: Error Response Format ✅ RESOLVED
**Decision**: Use **013-error-handling.md** format as canonical
**Rationale**:
- Most comprehensive and structured
- Includes error_code, tool_name, timestamp
- Uses snake_case for error_type
- Uses suggestions array (not singular)

**Action Required**: Update all tool specs (003-006) to use 013 format

---

## Batch Fix Plan

### Phase 1: Critical Fixes (91 occurrences)

**Model ID Format Change: `_gf` → `.gf`**

Files requiring batch replacement:
1. `001-system-overview.md` - 3 occurrences
2. `002-data-formats.md` - 6 occurrences
3. `003-build-media-tool.md` - 1 occurrence
4. `004-build-model-tool.md` - 1 occurrence
5. `005-gapfill-model-tool.md` - 16 occurrences ⚠️ HIGH
6. `006-run-fba-tool.md` - 14 occurrences ⚠️ HIGH
7. `010-model-storage.md` - 12 occurrences
8. `011-model-import-export.md` - 12 occurrences
9. `012-complete-workflow.md` - 11 occurrences
10. `013-error-handling.md` - 2 occurrences
11. `018-session-management-tools.md` - 0 occurrences (already fixed)

**Replacement Strategy**:
```bash
# Global search and replace patterns:
"_gf" → ".gf"
"_draft" → ".draft"
"_gf suffix" → ".gf suffix"
"{model_id}_gf" → "{model_id}.gf"
```

**Validation**:
- No occurrences of `_gf` should remain except in comments about "old format"
- All model_id examples should use dot notation
- State transformation algorithms should use dot format

### Phase 2: Error Format Standardization

**Update to 013-error-handling.md format:**

Required changes for each tool spec (003-006):
1. Change `error_type`: PascalCase → snake_case
   - `"ValidationError"` → `"validation_error"`
   - `"ModelNotFoundError"` → `"model_not_found_error"`
   - `"TemplateLoadError"` → `"template_load_error"`

2. Change `suggestion` → `suggestions` (array)
   - `"suggestion": "text"` → `"suggestions": ["text"]`

3. Add required fields:
   - `"error_code": "INVALID_INPUT"`
   - `"tool_name": "build_model"`
   - `"timestamp": "2025-10-27T14:32:15Z"`

**Files to update**:
- `003-build-media-tool.md`
- `004-build-model-tool.md`
- `005-gapfill-model-tool.md`
- `006-run-fba-tool.md`

### Phase 3: Documentation Improvements

**Add Missing Sections:**

1. **002-data-formats.md**: Add Media ID Format section
   - Currently in 010-model-storage.md
   - Should be in 002 as canonical data format reference

2. **004-build-model-tool.md**: Add FASTA example
   - Add "Example 4: Build Model from FASTA File"
   - Show complete FASTA workflow
   - Include FASTA validation error example

3. **002-data-formats.md**: Fix bounds notation
   - Change tuple `(-5, 100)` → array `[-5, 100]`
   - Add note about Python tuples vs JSON arrays

4. **Template path clarification**:
   - Confirm GramPositive is optional for MVP
   - Update 004 to note which templates are required

---

## Conflict Resolution by Priority

### Immediate (Before Implementation Start):
- [x] ~~CONFLICT 1: Model ID format (dot vs underscore)~~ - DECIDED: Use dot
- [x] ~~CONFLICT 2: RAST annotation default~~ - DECIDED: Default true
- [x] ~~CONFLICT 8: Error response format~~ - DECIDED: Use 013 format

### Phase 0 Cleanup (Next):
- [ ] CONFLICT 3: Add FASTA examples to 004 - **30 min**
- [ ] CONFLICT 5: Add media_id format to 002 - **15 min**
- [ ] CONFLICT 6: Fix state transformation algorithm - **15 min** (part of batch fix)
- [ ] CONFLICT 9: Audit and fix all model_id examples - **2 hours** (91 occurrences)

### Before MVP Release:
- [ ] CONFLICT 4: Template path clarification - **15 min**
- [ ] CONFLICT 7: Timestamp format documentation - **30 min**
- [ ] CONFLICT 11: Template loading error handling - **30 min**
- [ ] CONFLICT 13: Bounds format notation - **10 min**

### Post-MVP:
- [ ] CONFLICT 10: Predefined media library spec - **CREATE 019 spec**
- [ ] CONFLICT 14: Model state classification edge cases - **15 min**

---

## Estimated Time

**Batch Fix (91 occurrences)**: 2-3 hours
- Automated search/replace: 30 min
- Manual verification: 1-2 hours
- Testing examples: 30 min

**Error Format Updates**: 2 hours
- 4 tool specs × 30 min each

**Documentation Improvements**: 1.5 hours
- Media ID format: 30 min
- FASTA example: 45 min
- Minor fixes: 15 min

**Total Estimated Time**: 5.5-6.5 hours

---

## Testing Checklist

After fixes, verify:
- [ ] No `_gf` or `_draft` occurrences remain (except in "old format" notes)
- [ ] All model_id examples use dot notation: `.draft`, `.gf`, `.draft.gf`
- [ ] All error responses match 013-error-handling.md format
- [ ] State transformation algorithms use dot format
- [ ] Template paths are consistent across specs
- [ ] Media ID format documented in 002
- [ ] FASTA example added to 004

---

## Approval Required

**User**: Please review and approve:
1. ✅ Model ID format: Dot notation (`.draft`, `.gf`, `.draft.gf`)
2. ✅ RAST annotation: Default enabled (`annotate_with_rast=true`)
3. ✅ Error format: Use 013-error-handling.md as canonical

**Proceed with batch fix?**
- [ ] Yes - Execute all 91 replacements + error format updates
- [ ] No - Review conflicts first and decide individually
- [ ] Defer - Complete remaining tasks from original 12-step plan first

---

## Original Task Progress

**Completed (6/12)**:
1. ✅ Create new data directory structure
2. ✅ Update 004-build-model-tool.md (RAST, FASTA, dict→faa)
3. ✅ Update 002-data-formats.md (FASTA, model ID states)
4. ✅ Update 010-model-storage.md (ID generation algorithm)
5. ✅ Create 017-template-management.md
6. ✅ Create 018-session-management-tools.md

**Remaining (6/12)**:
7. ⏳ Create 019-predefined-media-library.md
8. ⏳ Create 020-documentation-requirements.md
9. ⏳ Update 005-gapfill-model-tool.md (failure handling)
10. ⏳ Update 013-error-handling.md (JSON-RPC codes)
11. ⏳ Update 015-mcp-server-setup.md (MCP version)
12. ⏳ Update all file path references

**Recommendation**:
- Option A: Complete remaining 6 tasks first, then batch fix conflicts
- Option B: Fix critical conflicts now (91 occurrences), then continue tasks
- Option C: Create remaining specs (019, 020), then batch fix everything together

---

**Next Steps**: Awaiting user decision on batch fix approach and priority.
