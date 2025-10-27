# ModelSEED Database Guide for Gem-Flux MCP Server

**Purpose**: This guide explains the ModelSEED Database structure and how to use it for LLM-friendly compound and reaction lookups in metabolic modeling.

## Overview

The **ModelSEED Database** is a comprehensive biochemistry database containing:
- **33,978 compounds** with standardized IDs (cpd00001, cpd00002, etc.)
- **36,645 reactions** with standardized IDs (rxn00001, rxn00002, etc.)
- Cross-references to external databases (KEGG, MetaCyc, BiGG, etc.)
- Biochemical structures, thermodynamics data, and pathway information

### Why This Matters for LLMs

When working with metabolic models, reactions and compounds are represented by numerical IDs like `cpd00027` (glucose) or `rxn00148` (glycolysis reaction). For LLMs to:
- Reason about metabolic pathways
- Suggest model improvements
- Explain flux balance analysis results
- Make assertions about biochemical processes

They need tools to convert these IDs to human-readable names and vice versa.

## Database Location

The ModelSEED Database files are stored in this repository at:
```
specs-source/references/modelseed-database/
├── compounds.tsv       # Main compounds database (33,993 lines)
├── reactions.tsv       # Main reactions database (43,775 lines)
└── DATABASE_README.md  # Original ModelSEED documentation
```

**Source**: https://github.com/ModelSEED/ModelSEEDDatabase (master branch)
**Note**: For ModelSEEDpy we use the `dev` branch at https://github.com/Fxe/ModelSEEDpy/tree/dev

## Compounds Database Structure

### File: `compounds.tsv`

**Key Columns** (TSV format):

| Column | Description | Example |
|--------|-------------|---------|
| `id` | ModelSEED compound ID | `cpd00027` |
| `abbreviation` | Short code | `glc__D` |
| `name` | Human-readable name | `D-Glucose` |
| `formula` | Chemical formula | `C6H12O6` |
| `mass` | Molecular mass | `180.0` |
| `charge` | Ionic charge | `0` |
| `inchikey` | Standard structure key | `WQZGKKKJIJFFOK-GASJEMHNSA-N` |
| `aliases` | Names from other databases | `KEGG: C00031\|BiGG: glc__D\|MetaCyc: GLC` |
| `smiles` | Chemical structure notation | `OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O` |

###  Example Entries

```tsv
cpd00001	h2o	H2O	H2O	18.0	XLYOFNOQVPJJNP-UHFFFAOYSA-N	0
cpd00027	glc__D	D-Glucose	C6H12O6	180.0	WQZGKKKJIJFFOK-GASJEMHNSA-N	0
cpd00209	acetate	Acetate	C2H3O2	59.0	QTBSBXVTEAMEQO-UHFFFAOYSA-M	-1
```

### Common Compounds for Reference

| ID | Name | Role |
|----|------|------|
| `cpd00001` | H2O | Water |
| `cpd00002` | ATP | Energy currency |
| `cpd00003` | NAD | Redox cofactor |
| `cpd00004` | NADH | Reduced NAD |
| `cpd00007` | O2 | Oxygen |
| `cpd00008` | ADP | Adenosine diphosphate |
| `cpd00009` | Phosphate | Inorganic phosphate |
| `cpd00011` | CO2 | Carbon dioxide |
| `cpd00013` | NH3 | Ammonia |
| `cpd00027` | D-Glucose | Common sugar |
| `cpd00020` | Pyruvate | Central metabolism |
| `cpd00067` | H+ | Proton |

## Reactions Database Structure

### File: `reactions.tsv`

**Key Columns**:

| Column | Description | Example |
|--------|-------------|---------|
| `id` | ModelSEED reaction ID | `rxn00148` |
| `abbreviation` | Short code (often KEGG ID) | `R00200` |
| `name` | Human-readable name | `hexokinase` |
| `equation` | Reaction equation with compartments | `(1) cpd00027[0] + (1) cpd00002[0] => (1) cpd00008[0] + (1) cpd00067[0] + (1) cpd00079[0]` |
| `definition` | Equation with compound names | `(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) H+[0] + (1) D-Glucose-6-phosphate[0]` |
| `stoichiometry` | Detailed stoichiometry | `-1:cpd00027:0:0:"D-Glucose";-1:cpd00002:0:0:"ATP";1:cpd00008:0:0:"ADP"...` |
| `reversibility` | Direction symbol | `>`, `<`, `=` |
| `is_transport` | Transport reaction flag | `0` (no) or `1` (yes) |
| `ec_numbers` | Enzyme Commission numbers | `2.7.1.1` |
| `pathways` | Metabolic pathways | `Glycolysis; Central Metabolism` |
| `aliases` | External database IDs | `KEGG: R00200\|BiGG: HEX1\|MetaCyc: GLUCOKIN-RXN` |

### Example Entry

```tsv
rxn00148	R00200	hexokinase
(1) cpd00027[0] + (1) cpd00002[0] => (1) cpd00008[0] + (1) cpd00067[0] + (1) cpd00079[0]
(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) H+[0] + (1) D-Glucose-6-phosphate[0]
2.7.1.1
Glycolysis
KEGG: R00200|BiGG: HEX1
```

### Direction Symbols

- `>` = Irreversible forward (left → right)
- `<` = Irreversible reverse (right → left)
- `=` = Reversible (can go both ways)

## Required MCP Tools for LLM Support

Based on this database structure, the Gem-Flux MCP server needs these tools:

### 1. Compound Lookup Tools

```python
@mcp.tool()
def get_compound_name(compound_id: str) -> dict:
    """Get human-readable name for a ModelSEED compound ID.

    Args:
        compound_id: ModelSEED compound ID (e.g., "cpd00027")

    Returns:
        {
            "id": "cpd00027",
            "name": "D-Glucose",
            "abbreviation": "glc__D",
            "formula": "C6H12O6",
            "aliases": ["glucose", "Glc", "dextrose"]
        }
    """

@mcp.tool()
def search_compounds(query: str, limit: int = 10) -> list[dict]:
    """Search compounds by name, formula, or alias.

    Args:
        query: Search term (e.g., "glucose", "C6H12O6", "glc")
        limit: Max results to return

    Returns:
        List of matching compounds with id, name, formula
    """
```

### 2. Reaction Lookup Tools

```python
@mcp.tool()
def get_reaction_name(reaction_id: str) -> dict:
    """Get human-readable name and equation for a reaction.

    Args:
        reaction_id: ModelSEED reaction ID (e.g., "rxn00148")

    Returns:
        {
            "id": "rxn00148",
            "name": "hexokinase",
            "equation": "D-Glucose + ATP => ADP + H+ + D-Glucose-6-phosphate",
            "reversibility": "irreversible forward",
            "ec_number": "2.7.1.1"
        }
    """

@mcp.tool()
def search_reactions(query: str, limit: int = 10) -> list[dict]:
    """Search reactions by name, enzyme, or EC number.

    Args:
        query: Search term (e.g., "hexokinase", "2.7.1.1")
        limit: Max results to return

    Returns:
        List of matching reactions with id, name, equation
    """
```

### 3. Batch Lookup Tools

```python
@mcp.tool()
def get_pathway_compounds(compound_ids: list[str]) -> dict:
    """Convert list of compound IDs to names for pathway visualization.

    Args:
        compound_ids: List of ModelSEED compound IDs

    Returns:
        Dict mapping IDs to names
    """

@mcp.tool()
def get_model_reactions_readable(reaction_ids: list[str]) -> list[dict]:
    """Get readable equations for all reactions in a model.

    Args:
        reaction_ids: List of ModelSEED reaction IDs

    Returns:
        List of reactions with human-readable equations
    """
```

## Implementation Approach

### Option 1: In-Memory Database (Recommended for MVP)

Load TSV files into pandas DataFrames at server startup:

```python
import pandas as pd

# Load once at startup
compounds_df = pd.read_csv('modelseed-database/compounds.tsv', sep='\t',
                          low_memory=False)
reactions_df = pd.read_csv('modelseed-database/reactions.tsv', sep='\t',
                          low_memory=False)

# Index by ID for O(1) lookup
compounds_df.set_index('id', inplace=True)
reactions_df.set_index('id', inplace=True)

def get_compound_name(compound_id):
    row = compounds_df.loc[compound_id]
    return {
        'id': compound_id,
        'name': row['name'],
        'formula': row['formula']
    }
```

**Pros**: Fast, simple, works offline
**Cons**: ~100-200MB RAM usage

### Option 2: SQLite Database (For Future)

Convert TSV to SQLite for efficient searching:

```sql
CREATE INDEX idx_compound_name ON compounds(name);
CREATE INDEX idx_reaction_name ON reactions(name);
CREATE VIRTUAL TABLE compound_fts USING fts5(id, name, aliases);
```

**Pros**: Full-text search, lower memory
**Cons**: More complexity, requires migration script

## Database Maintenance

### Updating the Database

The ModelSEED Database is actively maintained. To update:

```bash
cd specs-source/references/modelseed-database
curl -sL "https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compounds.tsv" -o compounds.tsv
curl -sL "https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv" -o reactions.tsv
```

### Validation

After updating, validate the files:

```bash
# Check line counts
wc -l compounds.tsv reactions.tsv

# Check for required columns
head -1 compounds.tsv
head -1 reactions.tsv

# Test loading
python -c "import pandas as pd; df = pd.read_csv('compounds.tsv', sep='\t'); print(f'Loaded {len(df)} compounds')"
```

## Integration with ModelSEEDpy

ModelSEEDpy (dev branch) uses this same database internally. When building models:

```python
from modelseedpy import MSBuilder, MSMedia

# ModelSEEDpy automatically maps compound/reaction IDs to database entries
media = MSMedia.from_dict({
    'cpd00027': (-5, 100),   # D-Glucose
    'cpd00007': (-10, 100),  # O2
    # ModelSEEDpy knows these IDs from the database
})
```

Our MCP tools should provide the same ID→name mapping that ModelSEEDpy uses internally.

## Common Use Cases for MCP Tools

### Use Case 1: Explain FBA Results

**LLM needs**: Interpret flux values for reactions

```
User: "Why is my model producing so much acetate?"

LLM (via MCP):
1. get_reaction_name("rxn00225") → "acetate kinase"
2. get_compound_name("cpd00029") → "Acetate"
3. Explain: "Your model is producing acetate through the acetate kinase
   reaction (rxn00225), which converts acetyl-P to acetate..."
```

### Use Case 2: Suggest Media Compositions

**LLM needs**: Recommend compounds for growth media

```
User: "What should I add to grow E. coli?"

LLM (via MCP):
1. search_compounds("nitrogen") → Find nitrogen sources
2. get_compound_name("cpd00013") → "NH3 (ammonia)"
3. Recommend: "For nitrogen, add cpd00013 (ammonia) or cpd00209 (nitrate)..."
```

### Use Case 3: Gapfilling Analysis

**LLM needs**: Explain which reactions were added

```
User: "What reactions did gapfilling add?"

LLM (via MCP):
1. get_model_reactions_readable(["rxn00148", "rxn00200", ...])
2. Explain: "Gapfilling added hexokinase (rxn00148) to convert glucose to G6P,
   and pyruvate dehydrogenase (rxn00200) to connect glycolysis to TCA cycle..."
```

## File Formats and Parsing

### TSV Format Notes

- **Delimiter**: Tab character (`\t`)
- **Header**: First line contains column names
- **Quoting**: Not consistently used, beware of embedded tabs
- **Encoding**: UTF-8
- **Line endings**: Unix-style (`\n`)

### Safe Parsing with Pandas

```python
df = pd.read_csv('compounds.tsv',
                 sep='\t',
                 dtype=str,           # Read all as strings initially
                 na_values=['null'],  # Treat 'null' as NaN
                 keep_default_na=False,  # Don't treat other strings as NA
                 low_memory=False)    # Don't guess dtypes
```

### Handling Aliases Column

The `aliases` column contains pipe-separated database references:

```python
def parse_aliases(aliases_str):
    """Parse aliases column to dict of external IDs."""
    if pd.isna(aliases_str):
        return {}

    result = {}
    for part in aliases_str.split('|'):
        if ':' in part:
            db, id_list = part.split(':', 1)
            result[db.strip()] = id_list.split(';')
    return result

# Example: "KEGG: C00031|BiGG: glc__D|MetaCyc: GLC"
# Returns: {'KEGG': ['C00031'], 'BiGG': ['glc__D'], 'MetaCyc': ['GLC']}
```

## Testing Recommendations

### Test Data

Create test cases using well-known metabolites:

```python
TEST_COMPOUNDS = {
    'cpd00001': 'H2O',
    'cpd00027': 'D-Glucose',
    'cpd00209': 'Acetate',
}

TEST_REACTIONS = {
    'rxn00148': 'hexokinase',
    'rxn00225': 'acetate kinase',
}

def test_compound_lookup():
    result = get_compound_name('cpd00027')
    assert result['name'] == 'D-Glucose'
    assert 'C6H12O6' in result['formula']
```

### Edge Cases to Test

1. **Invalid IDs**: `get_compound_name('cpd99999')` → Should return error
2. **Case sensitivity**: `search_compounds('GLUCOSE')` → Should work
3. **Partial matches**: `search_compounds('gluc')` → Should find glucose
4. **Empty results**: `search_reactions('nonexistent')` → Return empty list
5. **Special characters**: Compounds with brackets, primes, Greek letters

## Summary

The ModelSEED Database provides the foundation for human-readable metabolic modeling. Key points:

✅ **33,978 compounds** and **36,645 reactions** with standardized IDs
✅ **TSV files** stored locally in `specs-source/references/modelseed-database/`
✅ **Required MCP tools**: `get_compound_name`, `get_reaction_name`, `search_compounds`, `search_reactions`
✅ **Implementation**: Load TSV into pandas DataFrames for fast lookup
✅ **Purpose**: Enable LLMs to reason about metabolic models using human-readable names

This database is essential for the Gem-Flux MCP server to provide intelligent assistance for metabolic modeling workflows.
