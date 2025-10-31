# build_media Tool

## Overview

The `build_media` tool creates growth media definitions from ModelSEED compound IDs with configurable uptake/secretion bounds.

**Location**: `src/gem_flux_mcp/tools/media_builder.py`

## Function Signature

```python
def build_media(
    request: BuildMediaRequest,
    db_index: DatabaseIndex
) -> dict
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `compounds` | `list[str]` | Yes | - | List of ModelSEED compound IDs (e.g., `["cpd00027", "cpd00007"]`) |
| `default_uptake` | `float` | No | `100.0` | Default maximum uptake rate (mmol/gDW/h) for all compounds |
| `custom_bounds` | `dict[str, tuple[float, float]]` | No | `{}` | Custom bounds for specific compounds |
| `db_index` | `DatabaseIndex` | Yes | - | Database index for compound validation |

## Return Value

```python
{
    "success": bool,
    "media_id": str,  # Generated media identifier
    "compounds": [
        {
            "id": str,
            "name": str,
            "formula": str,
            "bounds": [float, float]
        }
    ],
    "num_compounds": int,
    "media_type": str,  # "minimal" (<50 compounds) or "rich" (>=50)
    "default_uptake_rate": float,
    "custom_bounds_applied": int
}
```

## Usage Example

```python
from gem_flux_mcp.tools.media_builder import build_media, BuildMediaRequest

# Create glucose minimal media
request = BuildMediaRequest(
    compounds=["cpd00027", "cpd00007", "cpd00009", "cpd00013"],  # Glucose, O2, Phosphate, NH3
    default_uptake=100.0,
    custom_bounds={
        "cpd00007": (-20.0, 1000.0),  # Limit oxygen uptake
    }
)

result = build_media(request, db_index)
print(f"Media ID: {result['media_id']}")
print(f"Type: {result['media_type']}")
```

## How It Works

1. **Validates** compound IDs against database
2. **Applies bounds** from default_uptake and custom_bounds
3. **Creates MSMedia object** using ModelSEEDpy
4. **Generates unique ID** with timestamp
5. **Stores** in session storage
6. **Enriches** with compound names and metadata

## Common Bounds Patterns

### Standard Uptake Bounds

```python
# Default: allows unlimited uptake and secretion
(-100.0, 100.0)

# Uptake only: no secretion allowed
(-100.0, 0.0)

# Limited uptake: controlled nutrient availability
(-5.0, 0.0)
```

### Common Compound Bounds

| Compound | ID | Typical Bounds | Notes |
|----------|-----|----------------|-------|
| Glucose | cpd00027 | (-10, 0) | Limited carbon source |
| Oxygen | cpd00007 | (-20, 1000) | Aerobic respiration |
| CO2 | cpd00011 | (-1000, 1000) | Free exchange |
| H2O | cpd00001 | (-1000, 1000) | Free exchange |
| Phosphate | cpd00009 | (-100, 100) | Essential nutrient |
| Ammonium | cpd00013 | (-100, 100) | Nitrogen source |

## Input Validation

### Compound ID Format

- Must match pattern: `cpd#####` (e.g., `cpd00027`)
- Case-insensitive (converted to lowercase)
- Must exist in database
- No duplicates allowed

### Bounds Validation

- Custom bounds must be `[lower, upper]` tuples
- Lower bound must be ≤ upper bound
- Bounds must be numeric
- Compound ID in custom_bounds must be in compounds list

## Error Handling

### INVALID_COMPOUND_IDS

```python
{
    "error_code": "INVALID_COMPOUND_IDS",
    "message": "Some compound IDs were not found in database",
    "details": {
        "invalid_ids": ["cpd99999"],
        "valid_ids": ["cpd00027", "cpd00007"],
        "total_provided": 3
    },
    "suggestions": [
        "Use search_compounds tool to find valid compound IDs",
        "Check spelling of compound IDs",
        "Verify IDs from ModelSEED database"
    ]
}
```

## Performance

- **Typical time**: <500ms for 20-100 compounds
- **Memory**: Minimal (~10MB for media object)

## Related Tools

- **Prerequisite**: None (can be created independently)
- **Used by**: `gapfill_model`, `run_fba` - Apply media constraints
- **Query**: `compound_lookup` - Find compound IDs
- **Inspect**: `list_media` - View all media in session

## See Also

- [Compound Lookup](compound_lookup.md) - Find compound IDs by name
- [Gapfill Model](gapfill_model.md) - Use media for gapfilling
- [Run FBA](run_fba.md) - Analyze model in media
- Source code: `src/gem_flux_mcp/tools/media_builder.py`
