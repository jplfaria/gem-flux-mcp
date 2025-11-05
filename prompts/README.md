# Centralized Prompts

This directory contains all prompts for the gem-flux-mcp tools, extracted from hardcoded Python strings to centralized markdown files.

## Structure

```
prompts/
├── next_steps/          # Workflow guidance prompts
│   ├── build_media.md
│   ├── build_model.md
│   ├── gapfill_model.md
│   ├── list_media.md
│   ├── list_models.md
│   ├── run_fba.md
│   ├── search_compounds.md
│   └── search_reactions.md
├── interpretations/     # Biological interpretation prompts
│   └── build_model.md
└── test/               # Test prompts
    └── simple.md
```

## Format

All prompts use **Markdown with YAML frontmatter**:

```markdown
---
version: 1.0.0
tool: tool_name
type: next_steps | interpretation
updated: YYYY-MM-DD
variables:
  - var1
  - var2
description: What this prompt does
---

# Prompt Content

Use {{ variable }} for substitution.

{% if conditional %}
Conditional content
{% endif %}

- List items
- Another item
```

## Editing Prompts

### For Non-Developers

1. Find the tool's prompt in `prompts/next_steps/` or `prompts/interpretations/`
2. Edit the markdown content (below the `---` section)
3. Use variables like `{{ num_reactions }}` where needed
4. Save and test with the MCP server

### For Developers

Prompts are loaded using `gem_flux_mcp.prompts.render_prompt()`:

```python
from gem_flux_mcp.prompts import render_prompt

# Render prompt with variables
next_steps_text = render_prompt(
    "next_steps/list_media",
    predefined_count=4,
    user_created_count=0,
    has_media=True,
)

# Convert to list
next_steps = [
    line.strip()[2:].strip()  # Remove "- " prefix
    for line in next_steps_text.split("\n")
    if line.strip().startswith("-")
]
```

## Template Syntax

Using **Jinja2** syntax:

### Variables
```markdown
{{ variable_name }}
```

### Conditionals
```markdown
{% if condition %}
Text when true
{% else %}
Text when false
{% endif %}
```

### Loops
```markdown
{% for item in items %}
- {{ item }}
{% endfor %}
```

### Filters
```markdown
{{ value|round(2) }}
{{ text|upper }}
```

## Benefits

✅ **Team Collaboration** - Non-developers can edit prompts directly
✅ **Version Control** - Git tracks every prompt change
✅ **Rapid Iteration** - Change prompts without touching code
✅ **A/B Testing** - Easy to test prompt variations
✅ **Clear Separation** - Logic vs presentation
✅ **MCP Best Practice** - Industry standard approach

## Testing Prompts

Test individual prompts:

```bash
uv run python -c "
from gem_flux_mcp.prompts import render_prompt

result = render_prompt(
    'next_steps/list_media',
    predefined_count=4,
    user_created_count=0,
    has_media=True
)
print(result)
"
```

Test with MCP server:

```bash
# Restart MCP server to reload prompts
claude mcp restart gem-flux

# Test in Claude Code conversation
# Use any tool and check next_steps in response
```

## Versioning

Follow **semantic versioning** in YAML frontmatter:

- `1.0.0` - Initial version
- `1.0.1` - Minor text improvements
- `1.1.0` - New conditional logic added
- `2.0.0` - Breaking changes (new variables required)

## Examples

### Simple Prompt (build_media)

```markdown
---
version: 1.0.0
tool: build_media
type: next_steps
updated: 2025-11-05
---

- Use this media_id with gapfill_model to add reactions for growth
- Use list_media to see all available media compositions
- Compare model growth on different media by gapfilling with different media_ids
```

### Conditional Prompt (list_models)

```markdown
---
version: 1.0.0
tool: list_models
type: next_steps
variables:
  - draft_count
  - gapfilled_count
  - has_models
---

{% if draft_count > 0 and gapfilled_count == 0 %}
- Draft models need gapfilling: use gapfill_model with a media_id
{% elif draft_count > 0 and gapfilled_count > 0 %}
- Draft models (.draft suffix) need gapfilling for growth
- Gapfilled models (.gf suffix) are ready for run_fba
{% endif %}
```

### Truncation Logic (search_compounds)

```markdown
---
version: 1.0.0
tool: search_compounds
variables:
  - truncated
  - limit
  - total_matches
---

{% if truncated %}
- More results available: increase limit parameter (currently {{ limit }}) to see all {{ total_matches }} matches
{% endif %}
- Use get_compound_name with compound 'id' to get detailed information
- Use compound IDs in build_media to create growth media
```

## Troubleshooting

### Prompt not loading

1. Check file exists: `prompts/next_steps/tool_name.md`
2. Check YAML frontmatter is valid
3. Restart MCP server: `claude mcp restart gem-flux`

### Template error

1. Check variable names match code
2. Check Jinja2 syntax is correct
3. Test prompt in isolation (see Testing section)

### Unexpected output

1. Check conditional logic
2. Verify variable values being passed
3. Compare to previous version in Git

## Contributing

When adding new prompts:

1. Create markdown file in appropriate directory
2. Add YAML frontmatter with metadata
3. Write prompt content with variables
4. Update tool code to use `render_prompt()`
5. Test with MCP server
6. Commit with descriptive message

---

**Created**: 2025-11-05
**Proposal**: See PROMPTS_CENTRALIZATION_PROPOSAL.md
**Baseline**: See baseline_tests/BASELINE_SUMMARY.md
