# compound_lookup Tool

## Overview

The `compound_lookup` tool provides compound metadata queries from the ModelSEED database. It includes two functions: getting compound details by ID and searching compounds by name/formula.

**Location**: `src/gem_flux_mcp/tools/compound_lookup.py`

## Functions

### get_compound_name

Retrieve complete metadata for a single compound ID.

```python
def get_compound_name(
    request: GetCompoundNameRequest,
    db_index: DatabaseIndex
) -> dict
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `compound_id` | `str` | Yes | ModelSEED compound ID (format: `cpd#####`) |
| `db_index` | `DatabaseIndex` | Yes | Database index with loaded compounds |

#### Return Value

```python
{
    "success": bool,
    "id": str,
    "name": str,
    "abbreviation": str,
    "formula": str,
    "mass": float,
    "charge": int,
    "inchikey": str,
    "smiles": str,
    "aliases": dict[str, list[str]]  # {database: [ids]}
}
```

#### Example

```python
from gem_flux_mcp.tools.compound_lookup import get_compound_name, GetCompoundNameRequest

request = GetCompoundNameRequest(compound_id="cpd00027")
result = get_compound_name(request, db_index)

print(f"{result['name']}: {result['formula']}")  # D-Glucose: C6H12O6
print(f"Aliases: {result['aliases']}")  # {"KEGG": ["C00031"], "BiGG": ["glc__D"]}
```

### search_compounds

Search for compounds by name, formula, abbreviation, or alias.

```python
def search_compounds(
    request: SearchCompoundsRequest,
    db_index: DatabaseIndex
) -> dict
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | `str` | Yes | - | Text to search (name, formula, abbreviation, aliases) |
| `limit` | `int` | No | `10` | Maximum results to return (1-100) |
| `db_index` | `DatabaseIndex` | Yes | - | Database index with loaded compounds |

#### Return Value

```python
{
    "success": bool,
    "query": str,
    "num_results": int,
    "results": [
        {
            "id": str,
            "name": str,
            "abbreviation": str,
            "formula": str,
            "mass": float,
            "charge": int,
            "match_field": str,  # "name", "formula", "aliases", etc.
            "match_type": str    # "exact" or "partial"
        }
    ],
    "truncated": bool,
    "suggestions": list[str]  # Present if num_results == 0
}
```

#### Search Priority

1. **Exact ID match** - `cpd00027`
2. **Exact name match** - `d-glucose`
3. **Exact abbreviation match** - `glc-d`
4. **Partial name match** - `glucose` (matches D-Glucose, Glucose-6-phosphate, etc.)
5. **Formula match** - `c6h12o6`
6. **Alias match** - `kegg:c00031`

#### Example

```python
from gem_flux_mcp.tools.compound_lookup import search_compounds, SearchCompoundsRequest

# Search by name
request = SearchCompoundsRequest(query="glucose", limit=5)
result = search_compounds(request, db_index)

for compound in result['results']:
    print(f"{compound['id']}: {compound['name']} ({compound['formula']})")
```

## Common Use Cases

### Finding Compounds for Media

```python
# Find nitrogen sources
nitrogen_compounds = search_compounds(
    SearchCompoundsRequest(query="ammon", limit=10),
    db_index
)

# Find phosphate sources
phosphate_compounds = search_compounds(
    SearchCompoundsRequest(query="phosphate", limit=10),
    db_index
)
```

### Validating Compound IDs

```python
# Check if compound exists and get details
try:
    request = GetCompoundNameRequest(compound_id="cpd00027")
    result = get_compound_name(request, db_index)
    print(f"Valid compound: {result['name']}")
except NotFoundError:
    print("Compound not found")
```

### Cross-Database Lookup

```python
# Find ModelSEED ID from KEGG ID
kegg_results = search_compounds(
    SearchCompoundsRequest(query="C00031"),  # KEGG ID
    db_index
)

if kegg_results['num_results'] > 0:
    modelseed_id = kegg_results['results'][0]['id']
    print(f"KEGG C00031 = ModelSEED {modelseed_id}")
```

## Performance

- **get_compound_name**: <1ms (O(1) indexed lookup)
- **search_compounds**: 10-100ms (O(n) linear search)

## Error Handling

### COMPOUND_NOT_FOUND

```python
{
    "error_code": "COMPOUND_NOT_FOUND",
    "message": "Compound ID cpd99999 not found in ModelSEED database",
    "details": {
        "compound_id": "cpd99999",
        "searched_in": "compounds.tsv (32000 compounds)"
    },
    "suggestions": [
        "Check ID format: should be 'cpd' followed by exactly 5 digits",
        "Use search_compounds tool to find compounds by name",
        "Verify ID from ModelSEED database documentation"
    ]
}
```

## Related Tools

- **Used with**: `build_media` - Find compound IDs for media creation
- **Complementary**: `reaction_lookup` - Query reaction metadata
- Source code: `src/gem_flux_mcp/tools/compound_lookup.py`

## See Also

- [Build Media](build_media.md) - Create media from compound IDs
- [Reaction Lookup](reaction_lookup.md) - Query reaction information
- Database integration: `src/gem_flux_mcp/database/index.py`
