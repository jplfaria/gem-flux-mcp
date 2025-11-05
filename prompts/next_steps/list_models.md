---
version: 1.0.0
tool: list_models
type: next_steps
updated: 2025-11-05
variables:
  - draft_count
  - gapfilled_count
  - has_models
description: Workflow-aware guidance based on model states
---

{% if draft_count > 0 and gapfilled_count == 0 %}
- Draft models need gapfilling: use gapfill_model with a media_id
{% elif draft_count > 0 and gapfilled_count > 0 %}
- Draft models (.draft suffix) need gapfilling for growth
- Gapfilled models (.gf suffix) are ready for run_fba
{% elif gapfilled_count > 0 %}
- Gapfilled models are ready: use run_fba to analyze metabolism
{% endif %}
{% if has_models %}
- Compare growth rates across models using run_fba with same media
- Use delete_model to remove models no longer needed
{% endif %}
