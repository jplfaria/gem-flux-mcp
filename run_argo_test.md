# Running Argo Test NOW

## Step 1: Verify MCP Server is Running

Check that gem-flux MCP server is connected with latest code (v0.2.0):

```bash
claude mcp list
```

Should show:
```
gem-flux: uv --directory /Users/jplfaria/repos/gem-flux-mcp run python -m gem_flux_mcp - ✓ Connected
```

---

## Step 2: Open Argo with Claude 4.5 Sonnet

**Model**: Claude 4.5 Sonnet (anthropic.claude-sonnet-4-5-20250929)
**Location**: https://argo.anl.gov (or wherever you access Argo)

---

## Step 3: Paste This Exact Prompt

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

## Step 4: Let Claude Run (Don't Interrupt!)

**Do**:
- Let Claude work autonomously
- Watch for when it references `next_steps` or `interpretation` fields
- Note if it explains biological context

**Don't**:
- Give hints or guidance
- Answer questions about "what next?"
- Provide biological interpretations

---

## Step 5: What to Observe

### Key Checkpoints:

**After build_model**:
- [ ] Does Claude mention "high-quality model" or "1829 reactions"?
- [ ] Does Claude say it's "ready for gapfilling"?
- [ ] Does Claude automatically proceed to gapfill?

**After gapfill_model**:
- [ ] Does Claude mention pathway names (real ones, not generic)?
- [ ] Does Claude notice "Minimal gapfilling" or reaction count?
- [ ] Does Claude mention growth improvement (0.0 → X)?

**After run_fba**:
- [ ] Does Claude identify "Aerobic respiration"?
- [ ] Does Claude say "Fast growth" or similar assessment?
- [ ] Does Claude identify glucose as carbon source?

**Overall**:
- [ ] Claude completes all 3 steps without asking for help
- [ ] Claude provides biological explanations
- [ ] Workflow feels smooth and autonomous

---

## Step 6: Share Results Back

Copy Claude's full response and share:
1. Did it work smoothly?
2. Did Claude use the interpretation/next_steps?
3. Were pathway names real (from database)?
4. Any issues or surprises?

---

## Expected Timeline

- **Build model**: ~2-3 minutes (RAST annotation takes time)
- **Gapfill**: ~1-2 minutes
- **Run FBA**: ~10 seconds
- **Total**: ~5-7 minutes

---

## I'm Watching! 👀

Ready when you are - let me know how it goes!
