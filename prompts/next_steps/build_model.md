---
version: 1.0.0
tool: build_model
type: next_steps
updated: 2025-11-05
description: Workflow guidance after building draft model
---

- Use gapfill_model to add reactions needed for growth in target media
- Specify media_id (e.g., 'glucose_minimal_aerobic') when gapfilling
- After gapfilling, use run_fba to analyze growth and metabolism
- Compare growth rates across different media conditions
- Use list_models to see both draft and gapfilled versions
