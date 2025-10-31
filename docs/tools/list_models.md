# list_models Tool

## Overview

The `list_models` tool lists all models in the current session with metadata and filtering options.

**Location**: `src/gem_flux_mcp/tools/list_models.py`

## Function Signature

```python
def list_models(
    request: ListModelsRequest
) -> dict
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filter_state` | `str` | No | `"all"` | Filter by model state: `"all"`, `"draft"`, or `"gapfilled"` |

## Return Value

```python
{
    "success": bool,
    "models": [
        {
            "model_id": str,
            "model_name": str | None,  # User-provided name or None if auto-generated
            "state": str,  # "draft" or "gapfilled"
            "num_reactions": int,
            "num_metabolites": int,
            "num_genes": int,
            "template_used": str,  # "GramNegative", "GramPositive", "Core"
            "created_at": str,  # ISO 8601 timestamp
            "derived_from": str | None  # Parent model ID if gapfilled
        }
    ],
    "total_models": int,
    "models_by_state": {
        "draft": int,
        "gapfilled": int
    }
}
```

## Usage Examples

### List All Models

```python
from gem_flux_mcp.tools.list_models import list_models, ListModelsRequest

request = ListModelsRequest(filter_state="all")
result = list_models(request)

print(f"Total models: {result['total_models']}")
for model in result['models']:
    print(f"  {model['model_id']}: {model['num_reactions']} reactions ({model['state']})")
```

### List Only Draft Models

```python
request = ListModelsRequest(filter_state="draft")
result = list_models(request)

print(f"Draft models: {result['total_models']}")
for model in result['models']:
    print(f"  {model['model_id']}")
```

### List Only Gapfilled Models

```python
request = ListModelsRequest(filter_state="gapfilled")
result = list_models(request)

for model in result['models']:
    print(f"{model['model_id']}:")
    print(f"  Derived from: {model['derived_from']}")
    print(f"  Reactions: {model['num_reactions']}")
```

## Model State Classification

Models are classified by their ID suffix:

| Suffix | State | Description |
|--------|-------|-------------|
| `.draft` | draft | Built but not gapfilled |
| `.gf` or `.draft.gf` | gapfilled | Has been gapfilled |
| `.draft.gf.gf` | gapfilled | Re-gapfilled on additional media |

## Model Naming

### Auto-Generated Names

Format: `model_YYYYMMDD_HHMMSS_RANDOM.state`

Example: `model_20251027_143052_abc123.draft`

- `model_name` field will be `None`

### User-Provided Names

Format: `user_name.state`

Example: `ecoli_K12.draft`

- `model_name` field will contain the user's name: `ecoli_K12`

## Common Use Cases

### Check Model Lineage

```python
# Find all models derived from a base model
all_models = list_models(ListModelsRequest())['models']

base_model_id = "ecoli.draft"
lineage = [m for m in all_models if m.get('derived_from') == base_model_id]

for model in lineage:
    print(f"  → {model['model_id']}")
```

### Model Statistics

```python
result = list_models(ListModelsRequest())

print(f"Total models: {result['total_models']}")
print(f"Draft models: {result['models_by_state']['draft']}")
print(f"Gapfilled models: {result['models_by_state']['gapfilled']}")

# Average model size
if result['total_models'] > 0:
    avg_reactions = sum(m['num_reactions'] for m in result['models']) / result['total_models']
    print(f"Average reactions per model: {avg_reactions:.0f}")
```

### Find Models by Template

```python
all_models = list_models(ListModelsRequest())['models']

gram_neg_models = [m for m in all_models if m['template_used'] == 'GramNegative']
gram_pos_models = [m for m in all_models if m['template_used'] == 'GramPositive']

print(f"GramNegative models: {len(gram_neg_models)}")
print(f"GramPositive models: {len(gram_pos_models)}")
```

## Sort Order

Models are returned **sorted by creation time** (oldest first).

## Performance

- **Typical time**: <100ms for up to 100 models
- **Memory**: Minimal (metadata only, not full models)

## Error Handling

### INVALID_FILTER_STATE

```python
{
    "error_type": "ValidationError",
    "message": "Invalid filter_state: unknown",
    "details": {
        "provided": "unknown",
        "valid_values": ["all", "draft", "gapfilled"]
    },
    "suggestion": "Use 'all', 'draft', or 'gapfilled' for filter_state parameter."
}
```

## Related Tools

- **Create models**: `build_model`, `gapfill_model`
- **Delete models**: `delete_model`
- **Complementary**: `list_media` - List media in session
- Source code: `src/gem_flux_mcp/tools/list_models.py`

## See Also

- [Build Model](build_model.md) - Create new models
- [Gapfill Model](gapfill_model.md) - Gapfill existing models
- [Delete Model](delete_model.md) - Remove models from session
- Storage: `src/gem_flux_mcp/storage/models.py`
