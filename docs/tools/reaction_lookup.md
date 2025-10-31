# reaction_lookup Tool

## Overview

The `reaction_lookup` tool provides reaction metadata queries from the ModelSEED database. It includes functions for getting reaction details and searching reactions by name/EC number.

**Location**: `src/gem_flux_mcp/tools/reaction_lookup.py`

## Functions

### get_reaction_name

Retrieve complete metadata for a single reaction ID.

```python
def get_reaction_name(
    request: GetReactionNameRequest,
    db_index: DatabaseIndex
) -> dict
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `reaction_id` | `str` | Yes | ModelSEED reaction ID (format: `rxn#####`) |
| `db_index` | `DatabaseIndex` | Yes | Database index with loaded reactions |

#### Return Value

```python
{
    "success": bool,
    "id": str,
    "name": str,
    "abbreviation": str,
    "equation": str,  # Human-readable with compound names
    "equation_with_ids": str,  # With compound IDs
    "reversibility": str,  # "reversible", "irreversible", "irreversible_reverse"
    "direction": str,  # "forward", "reverse", "bidirectional"
    "is_transport": bool,
    "ec_numbers": list[str],
    "pathways": list[str],
    "deltag": float | None,  # Standard Gibbs free energy (kJ/mol)
    "deltagerr": float | None,
    "aliases": dict[str, list[str]]
}
```

#### Example

```python
from gem_flux_mcp.tools.reaction_lookup import get_reaction_name, GetReactionNameRequest

request = GetReactionNameRequest(reaction_id="rxn00148")
result = get_reaction_name(request, db_index)

print(f"{result['name']}: {result['equation']}")
print(f"EC: {result['ec_numbers']}")
print(f"Pathways: {result['pathways']}")
```

### search_reactions

Search for reactions by name, EC number, pathway, or enzyme.

```python
def search_reactions(
    request: SearchReactionsRequest,
    db_index: DatabaseIndex
) -> dict
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | `str` | Yes | - | Text to search (name, EC number, pathway, etc.) |
| `limit` | `int` | No | `10` | Maximum results to return (1-100) |
| `db_index` | `DatabaseIndex` | Yes | - | Database index with loaded reactions |

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
            "equation": str,
            "ec_numbers": list[str],
            "match_field": str,  # "name", "ec_numbers", "pathways", etc.
            "match_type": str    # "exact" or "partial"
        }
    ],
    "truncated": bool,
    "suggestions": list[str]  # Present if num_results == 0
}
```

#### Search Priority

1. **Exact ID match** - `rxn00148`
2. **Exact name match** - `hexokinase`
3. **Exact abbreviation match** - `hk`
4. **EC number match** - `2.7.1.1`
5. **Partial name match** - `kinase`
6. **Alias match** - `kegg:r00299`
7. **Pathway match** - `glycolysis`

#### Example

```python
from gem_flux_mcp.tools.reaction_lookup import search_reactions, SearchReactionsRequest

# Search by enzyme name
request = SearchReactionsRequest(query="hexokinase", limit=5)
result = search_reactions(request, db_index)

for rxn in result['results']:
    print(f"{rxn['id']}: {rxn['name']}")
    print(f"  {rxn['equation']}")
    print(f"  EC: {rxn['ec_numbers']}")
```

## Common Use Cases

### Finding Reactions by Enzyme

```python
# Search for all kinases
kinases = search_reactions(
    SearchReactionsRequest(query="kinase", limit=20),
    db_index
)
```

### Finding Reactions by EC Number

```python
# Find all hexokinases (EC 2.7.1.1)
hexokinases = search_reactions(
    SearchReactionsRequest(query="2.7.1.1"),
    db_index
)
```

### Finding Reactions in Pathway

```python
# Find glycolysis reactions
glycolysis_rxns = search_reactions(
    SearchReactionsRequest(query="glycolysis", limit=50),
    db_index
)
```

### Cross-Database Lookup

```python
# Find ModelSEED ID from KEGG reaction ID
kegg_results = search_reactions(
    SearchReactionsRequest(query="R00299"),
    db_index
)
```

## Understanding Reaction Properties

### Reversibility

| Symbol | Reversibility | Direction | Meaning |
|--------|--------------|-----------|---------|
| `=` | reversible | bidirectional | Can proceed forward or reverse |
| `>` | irreversible | forward | Only proceeds left → right |
| `<` | irreversible_reverse | reverse | Only proceeds right → left |

### Transport Reactions

- `is_transport: true` - Reaction moves compounds between compartments
- Example: Glucose transport from extracellular to cytosol

### Thermodynamics

- `deltag`: Standard Gibbs free energy change (kJ/mol)
- `deltagerr`: Uncertainty in deltag estimate
- Negative deltag = thermodynamically favorable

## Performance

- **get_reaction_name**: <1ms (O(1) indexed lookup)
- **search_reactions**: 10-100ms (O(n) linear search)

## Error Handling

### REACTION_NOT_FOUND

```python
{
    "error_code": "REACTION_NOT_FOUND",
    "message": "Reaction ID rxn99999 not found in ModelSEED database",
    "details": {
        "reaction_id": "rxn99999",
        "searched_in": "reactions.tsv (38000 reactions)"
    },
    "suggestions": [
        "Check ID format: should be 'rxn' followed by exactly 5 digits",
        "Use search_reactions tool to find reactions by name or enzyme",
        "Verify ID from ModelSEED database documentation"
    ]
}
```

## Related Tools

- **Complementary**: `compound_lookup` - Query compound metadata
- **Used with**: Model analysis - Understanding model reactions
- Source code: `src/gem_flux_mcp/tools/reaction_lookup.py`

## See Also

- [Compound Lookup](compound_lookup.md) - Query compound information
- [Run FBA](run_fba.md) - Analyze reaction fluxes
- Database integration: `src/gem_flux_mcp/database/index.py`
