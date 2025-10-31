# delete_model Tool

## Overview

The `delete_model` tool removes a model from the current session storage.

**Location**: `src/gem_flux_mcp/tools/delete_model.py`

## Function Signature

```python
def delete_model(
    request: DeleteModelRequest
) -> dict
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | `str` | Yes | Model identifier to delete |

## Return Value

### Success Response

```python
{
    "success": true,
    "deleted_model_id": str,
    "message": "Model deleted successfully"
}
```

### Error Response

```python
{
    "success": false,
    "error_type": str,  # "ValidationError", "ModelNotFound", "ServerError"
    "message": str,
    "details": dict,
    "suggestion": str
}
```

## Usage Examples

### Basic Deletion

```python
from gem_flux_mcp.tools.delete_model import delete_model, DeleteModelRequest

request = DeleteModelRequest(model_id="ecoli_test.draft")
result = delete_model(request)

if result['success']:
    print(f"Deleted: {result['deleted_model_id']}")
else:
    print(f"Error: {result['message']}")
```

### Safe Deletion with Verification

```python
from gem_flux_mcp.tools.list_models import list_models, ListModelsRequest
from gem_flux_mcp.tools.delete_model import delete_model, DeleteModelRequest

# List models first
models = list_models(ListModelsRequest())['models']
model_ids = [m['model_id'] for m in models]

model_to_delete = "ecoli_test.draft"

if model_to_delete in model_ids:
    result = delete_model(DeleteModelRequest(model_id=model_to_delete))
    print(f"Deleted: {result['deleted_model_id']}")
else:
    print(f"Model {model_to_delete} not found")
```

### Batch Deletion

```python
# Delete all draft models
all_models = list_models(ListModelsRequest())['models']
draft_models = [m['model_id'] for m in all_models if m['state'] == 'draft']

for model_id in draft_models:
    result = delete_model(DeleteModelRequest(model_id=model_id))
    if result['success']:
        print(f"  Deleted: {model_id}")
    else:
        print(f"  Failed: {model_id} - {result['message']}")
```

### Delete Model and Derivatives

```python
# Delete a model and all models derived from it
base_model_id = "ecoli.draft"

# Find all derivatives
all_models = list_models(ListModelsRequest())['models']
to_delete = [m['model_id'] for m in all_models
             if m['model_id'] == base_model_id or m.get('derived_from') == base_model_id]

print(f"Deleting {len(to_delete)} models:")
for model_id in to_delete:
    result = delete_model(DeleteModelRequest(model_id=model_id))
    print(f"  {model_id}: {'✓' if result['success'] else '✗'}")
```

## Important Notes

### Deletion is Permanent

- Models are removed from session storage immediately
- **No undo/recovery** - ensure you want to delete before calling
- Consider saving models to disk before deletion if needed

### Dependent Models

- Deleting a model **does not delete** models derived from it
- If you delete `model.draft`, `model.draft.gf` will remain
- Use `derived_from` field to find dependent models

### Test Conditions

- If model has ATP correction test conditions, they are also deleted
- Stored as `{model_id}.test_conditions` in MODEL_STORAGE
- Automatically cleaned up with model deletion

## Error Handling

### MODEL_NOT_FOUND

```python
{
    "success": false,
    "error_type": "ModelNotFound",
    "message": "Model 'unknown_model.draft' not found in session",
    "details": {
        "model_id": "unknown_model.draft",
        "available_models": ["ecoli.draft", "bacillus.draft.gf"]
    },
    "suggestion": "Use list_models tool to see available models."
}
```

### VALIDATION_ERROR

```python
{
    "success": false,
    "error_type": "ValidationError",
    "message": "Missing required parameter 'model_id'",
    "details": {
        "parameter": "model_id",
        "received": ""
    },
    "suggestion": "Provide model_id to delete."
}
```

## Common Use Cases

### Clean Up Test Models

```python
# Delete all test models
all_models = list_models(ListModelsRequest())['models']
test_models = [m['model_id'] for m in all_models if 'test' in m['model_id'].lower()]

for model_id in test_models:
    delete_model(DeleteModelRequest(model_id=model_id))
```

### Keep Only Final Models

```python
# Delete all draft versions, keep only gapfilled
all_models = list_models(ListModelsRequest())['models']

# Group by base name
from collections import defaultdict
by_base = defaultdict(list)

for model in all_models:
    base = model['model_id'].split('.')[0]
    by_base[base].append(model)

# For each base, delete draft if gapfilled exists
for base, models in by_base.items():
    has_gapfilled = any(m['state'] == 'gapfilled' for m in models)
    if has_gapfilled:
        drafts = [m for m in models if m['state'] == 'draft']
        for draft in drafts:
            delete_model(DeleteModelRequest(model_id=draft['model_id']))
            print(f"Deleted draft: {draft['model_id']}")
```

### Session Cleanup

```python
# Clear all models from session
all_models = list_models(ListModelsRequest())['models']

print(f"Deleting {len(all_models)} models...")
for model in all_models:
    delete_model(DeleteModelRequest(model_id=model['model_id']))

print("Session cleared")
```

## Performance

- **Typical time**: <10ms per deletion
- **Memory**: Frees memory used by deleted model

## Related Tools

- **List models**: `list_models` - See available models before deletion
- **Create models**: `build_model`, `gapfill_model`
- Source code: `src/gem_flux_mcp/tools/delete_model.py`

## See Also

- [List Models](list_models.md) - View available models
- [Build Model](build_model.md) - Create new models
- [Gapfill Model](gapfill_model.md) - Gapfill models
- Storage: `src/gem_flux_mcp/storage/models.py`
