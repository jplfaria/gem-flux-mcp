---
version: 1.0.0
tool: search_compounds
type: next_steps
updated: 2025-11-05
variables:
  - truncated
  - limit
  - total_matches
description: Guidance for using compound search results
---

{% if truncated %}
- More results available: increase limit parameter (currently {{ limit }}) to see all {{ total_matches }} matches
{% endif %}
- Use get_compound_name with compound 'id' to get detailed information
- Use compound IDs in build_media to create growth media
