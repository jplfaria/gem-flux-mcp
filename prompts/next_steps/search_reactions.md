---
version: 1.0.0
tool: search_reactions
type: next_steps
updated: 2025-11-05
variables:
  - truncated
  - limit
  - total_matches
description: Guidance for using reaction search results
---

{% if truncated %}
- More results available: increase limit parameter (currently {{ limit }}) to see all {{ total_matches }} matches
{% endif %}
- Use get_reaction_name with reaction 'id' to get detailed information and equation
- Examine EC numbers to understand enzyme classification
- Look at pathways to see metabolic context of reactions
