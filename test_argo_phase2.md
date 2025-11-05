# Argo Test Prompt - Phase 2 Improvements

**Purpose**: Test if Phase 2 improvements (next_steps, interpretation, real pathway data) help Claude 4.5 Sonnet understand and execute the workflow better.

**Model**: Claude 4.5 Sonnet (same as Claude Code)

---

## Test Prompt for Argo

```
I want to build a genome-scale metabolic model for E. coli and analyze its growth on glucose.

The protein sequences are in: examples/ecoli_proteins.fasta

Please:
1. Build a draft model using the GramNegative template with RAST annotation
2. Gapfill it for growth on glucose minimal aerobic media
3. Run FBA to predict the growth rate
4. Explain what you learned about the model's metabolism

Important: Pay attention to the tool outputs - they include guidance on next steps and biological interpretation. Use this information to guide your workflow.
```

---

## What to Look For

### Before Phase 2 (Expected Issues):
- Claude might not know what to do after build_model
- Pathway information was keyword-based ("Pentose phosphate", "TCA cycle")
- No context about whether gapfilling was successful
- FBA results were just numbers with no biological meaning
- Claude might ask "what should I do next?" after each step

### After Phase 2 (Expected Improvements):
- **next_steps** should guide Claude through the workflow automatically
- **interpretation** should help Claude understand:
  - Model quality (reactions count → quality assessment)
  - Gapfilling success (growth improvement context)
  - Metabolism type (aerobic vs anaerobic from FBA)
  - Real pathway names from ModelSEED database
- Claude should provide better explanations without needing to ask for guidance

---

## Specific Things to Check

### 1. build_model Output
**Look for**:
```json
"interpretation": {
  "model_quality": "High-quality draft model with extensive reaction coverage",
  "annotation_status": "RAST annotation enabled: 1333 genes annotated...",
  "atp_correction_status": "ATP correction applied: added X reactions...",
  "model_state": "Draft model created - requires gapfilling to enable growth",
  "readiness": "Ready for gapfilling with gapfill_model tool"
},
"next_steps": [
  "Use gapfill_model to add reactions needed for growth in target media",
  "Specify media_id (e.g., 'glucose_minimal_aerobic') when gapfilling",
  ...
]
```

**Question**: Does Claude automatically proceed to gapfilling without asking?

---

### 2. gapfill_model Output
**Look for**:
```json
"interpretation": {
  "overview": "Added 5 reactions across 3 metabolic pathways. Model can now grow.",
  "growth_improvement": {
    "before": 0.0,
    "after": 0.554,
    "target": 0.01,
    "met_target": true
  },
  "gapfilling_assessment": "Minimal gapfilling (5 reactions)",
  "pathway_coverage_note": "..."
},
"pathway_summary": {
  "pathways": [
    {"pathway": "Glycolysis / Gluconeogenesis", ...},  // REAL pathway name!
    {"pathway": "Pentose Phosphate Pathway", ...}      // Not "Pentose phosphate"!
  ],
  "reactions_without_pathways": 0,
  "reactions_without_pathways_percentage": 0.0
}
```

**Questions**:
- Does Claude understand the growth improvement (0.0 → 0.554)?
- Does Claude mention the real pathway names in its explanation?
- Does Claude understand "Minimal gapfilling" means good annotation quality?

---

### 3. run_fba Output
**Look for**:
```json
"interpretation": {
  "growth_rate_per_hour": 0.554,
  "metabolism_type": "Aerobic respiration",
  "carbon_source": "cpd00027",
  "growth_assessment": "Fast growth",
  "model_status": "Model is viable and can grow in specified media"
},
"next_steps": [
  "Analyze uptake_fluxes to understand nutrient consumption",
  "Analyze secretion_fluxes to identify metabolic byproducts",
  ...
]
```

**Questions**:
- Does Claude explain the metabolism type in its summary?
- Does Claude mention that it's "Fast growth" vs just giving the number?
- Does Claude identify the carbon source (glucose)?

---

## Success Criteria

### Workflow Understanding:
- [ ] Claude completes all 3 steps without asking "what next?"
- [ ] Claude uses the next_steps to guide its actions
- [ ] Claude references the interpretation fields in its explanations

### Biological Context:
- [ ] Claude explains model quality (not just reaction count)
- [ ] Claude explains gapfilling results (what pathways were added)
- [ ] Claude explains metabolism type and growth assessment
- [ ] Claude uses real pathway names (not generic categories)

### Transparency:
- [ ] Claude mentions growth improvement (0.0 → 0.554)
- [ ] Claude explains gapfilling assessment (Minimal/Moderate/Extensive)
- [ ] Claude notices if reactions lack pathway annotations

---

## Comparison Test (Optional)

If you want to see the difference, you could run the same prompt on:
1. **v0.1.2** (before Phase 2) - keyword pathways, no next_steps
2. **v0.2.0** (after Phase 2) - real pathways, next_steps, interpretation

Compare:
- How many times Claude asks "what should I do next?"
- Quality of biological explanations
- Whether pathway names are real or generic
- Overall workflow smoothness

---

## Notes for Running in Argo

1. Make sure gem-flux MCP server is connected and using v0.2.0
2. Use Claude 4.5 Sonnet (same model as Claude Code)
3. Let Claude run autonomously - don't provide hints
4. Watch for when Claude references the interpretation/next_steps fields
5. Check if Claude's final explanation includes biological context

---

## Expected Claude Response Pattern

**Good (Phase 2 working)**:
```
I'll build an E. coli metabolic model using the workflow.

1. Building draft model...
   ✓ Created high-quality model with 1829 reactions
   ✓ RAST annotation added functional roles to 1333 genes
   ✓ Model is ready for gapfilling

2. Gapfilling for glucose aerobic growth...
   ✓ Minimal gapfilling needed (only 5 reactions added)
   ✓ Added reactions to Glycolysis / Gluconeogenesis and Pentose Phosphate Pathway
   ✓ Growth improved from 0.0 to 0.554 hr⁻¹

3. Analyzing metabolism with FBA...
   ✓ Fast growth rate (0.554 hr⁻¹)
   ✓ Aerobic respiration detected (oxygen uptake)
   ✓ Using glucose as carbon source

The model shows typical E. coli aerobic metabolism with fast growth...
```

**Bad (Phase 2 not working)**:
```
I built a model with 1829 reactions.
What should I do next?

[User provides hint]

I gapfilled and added 5 reactions.
The growth rate is 0.554. Is that good?

[User provides context]

I ran FBA. Here are the fluxes. What do they mean?
```

---

## Ready to Test!

Copy the test prompt above and paste it into Argo with Claude 4.5 Sonnet.

Let me know what you observe!
