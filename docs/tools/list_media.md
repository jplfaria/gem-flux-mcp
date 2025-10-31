# list_media Tool

## Overview

The `list_media` tool lists all media in the current session with metadata and preview information.

**Location**: `src/gem_flux_mcp/tools/list_media.py`

## Function Signature

```python
def list_media(
    db_index: DatabaseIndex = None
) -> dict
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `db_index` | `DatabaseIndex` | No | Database index for enriching compound names in preview |

## Return Value

```python
{
    "success": bool,
    "media": [
        {
            "media_id": str,
            "media_name": str | None,  # Name if predefined, None if auto-generated
            "num_compounds": int,
            "media_type": str,  # "minimal" (<50 compounds) or "rich" (>=50)
            "compounds_preview": [
                {
                    "id": str,
                    "name": str
                }
            ],  # First 3 compounds
            "created_at": str,  # ISO 8601 timestamp
            "is_predefined": bool
        }
    ],
    "total_media": int,
    "predefined_media": int,
    "user_created_media": int
}
```

## Usage Examples

### List All Media

```python
from gem_flux_mcp.tools.list_media import list_media

result = list_media(db_index)

print(f"Total media: {result['total_media']}")
for media in result['media']:
    print(f"  {media['media_id']}: {media['num_compounds']} compounds ({media['media_type']})")

    # Show preview
    preview = [f"{c['id']} ({c['name']})" for c in media['compounds_preview']]
    print(f"    Preview: {', '.join(preview)}")
```

### Filter Predefined vs User-Created

```python
result = list_media(db_index)

predefined = [m for m in result['media'] if m['is_predefined']]
user_created = [m for m in result['media'] if not m['is_predefined']]

print(f"Predefined media: {len(predefined)}")
for media in predefined:
    print(f"  {media['media_id']}")

print(f"\nUser-created media: {len(user_created)}")
for media in user_created:
    print(f"  {media['media_id']}")
```

### Media Type Distribution

```python
result = list_media(db_index)

minimal = [m for m in result['media'] if m['media_type'] == 'minimal']
rich = [m for m in result['media'] if m['media_type'] == 'rich']

print(f"Minimal media (<50 compounds): {len(minimal)}")
print(f"Rich media (>=50 compounds): {len(rich)}")
```

## Media Naming

### Auto-Generated IDs

Format: `media_YYYYMMDD_HHMMSS_RANDOM`

Example: `media_20251027_143052_x1y2z3`

- `media_name` field will be `None`
- `is_predefined` will be `False`

### Predefined Media

Format: Descriptive name

Examples:
- `glucose_minimal_aerobic`
- `pyruvate_minimal_aerobic`
- `complete_rich`

- `media_name` field will contain the name
- `is_predefined` will be `True`

## Media Type Classification

| Type | Threshold | Typical Examples |
|------|-----------|-----------------|
| `minimal` | <50 compounds | Glucose minimal, defined media |
| `rich` | >=50 compounds | Complete media, complex media |

## Compounds Preview

The `compounds_preview` field contains the **first 3 compounds** in the media with their names:

```python
"compounds_preview": [
    {"id": "cpd00027", "name": "D-Glucose"},
    {"id": "cpd00007", "name": "O2"},
    {"id": "cpd00009", "name": "Phosphate"}
]
```

## Common Use Cases

### Find Media by Compound

```python
result = list_media(db_index)

# Find all media containing glucose
glucose_media = []
for media in result['media']:
    # Check if glucose is in preview (note: only shows first 3)
    has_glucose = any(c['id'] == 'cpd00027' for c in media['compounds_preview'])
    if has_glucose:
        glucose_media.append(media['media_id'])

print(f"Media with glucose in preview: {glucose_media}")
```

### Media Creation Timeline

```python
result = list_media(db_index)

print("Media creation timeline:")
for media in result['media']:
    print(f"  {media['created_at']}: {media['media_id']} ({media['num_compounds']} compounds)")
```

### Media Statistics

```python
result = list_media(db_index)

print(f"Total media: {result['total_media']}")
print(f"Predefined: {result['predefined_media']}")
print(f"User-created: {result['user_created_media']}")

if result['total_media'] > 0:
    avg_compounds = sum(m['num_compounds'] for m in result['media']) / result['total_media']
    print(f"Average compounds per media: {avg_compounds:.1f}")
```

## Sort Order

Media are returned **sorted by creation time** (oldest first).

Predefined media use a fixed early timestamp, so they appear first.

## Performance

- **Typical time**: <100ms for up to 100 media
- **Memory**: Minimal (metadata only, not full media objects)

## Related Tools

- **Create media**: `build_media`
- **Use media**: `gapfill_model`, `run_fba`
- **Complementary**: `list_models` - List models in session
- Source code: `src/gem_flux_mcp/tools/list_media.py`

## See Also

- [Build Media](build_media.md) - Create new media
- [Gapfill Model](gapfill_model.md) - Use media for gapfilling
- [Run FBA](run_fba.md) - Analyze models in media conditions
- [List Models](list_models.md) - List models in session
- Storage: `src/gem_flux_mcp/storage/media.py`
