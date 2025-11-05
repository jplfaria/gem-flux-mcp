---
version: 1.0.0
tool: list_media
type: next_steps
updated: 2025-11-05
variables:
  - predefined_count
  - user_created_count
  - has_media
description: Context-aware guidance for using media after listing
---

{% if predefined_count > 0 %}
- Use predefined media (like 'glucose_minimal_aerobic') with gapfill_model
{% endif %}
{% if user_created_count > 0 %}
- Your custom media compositions are ready for gapfilling
{% endif %}
{% if has_media %}
- Use media_id with gapfill_model to add reactions for growth
- Examine compounds_preview to see media composition
- Use build_media to create custom media compositions
{% endif %}
