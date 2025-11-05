---
version: 1.0.0
tool: build_model
type: interpretation
updated: 2025-11-05
variables:
  - model_quality
  - annotation_note
  - atp_note
description: Biological interpretation of draft model
---

**Model Quality**: {{ model_quality }}

**Annotation**: {{ annotation_note }}

**ATP Correction**: {{ atp_note }}

**Model State**: Draft model created - requires gapfilling to enable growth

**Expected Growth**: 0.0 (draft models cannot grow)

**Readiness**: Ready for gapfilling with gapfill_model tool
