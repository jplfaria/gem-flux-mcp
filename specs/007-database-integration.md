# ModelSEED Database Integration - Gem-Flux MCP Server

**Type**: System Integration Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding ModelSEED identifiers and terminology)
- Read: 002-data-formats.md (for ModelSEED identifier conventions)

## Purpose

This specification defines how the Gem-Flux MCP Server integrates with the ModelSEED Database to provide human-readable compound and reaction information. The database enables LLMs to reason about metabolic pathways, explain FBA results, and assist users with model construction by translating between numerical IDs (cpd00027) and human-readable names (D-Glucose).

## Overview

### What the Database Integration Provides

**For LLMs**:
- Translation from ModelSEED IDs to human-readable names
- Search capability to find compounds/reactions by name
- Access to biochemical properties (formulas, charges, EC numbers)
- Understanding of metabolic pathway context

**For Users**:
- Interpretable flux analysis results
- Searchable compound/reaction databases
- Cross-references to external databases (KEGG, BiGG, MetaCyc)
- Chemical formulas and structures

**For the System**:
- Validation of compound/reaction IDs
- Enrichment of model data with metadata
- Support for database lookups in all MCP tools

### What the Database Integration Does NOT Provide

- Biochemical reaction predictions (ModelSEEDpy handles this)
- Pathway analysis algorithms (use dedicated tools)
- Model building logic (MSBuilder handles this)
- Thermodynamic calculations
- Real-time database updates from external sources

---

## Database Structure

### Database Files

The ModelSEED Database consists of two primary TSV (tab-separated values) files:

**compounds.tsv**:
- **Size**: 33,993 lines (including header)
- **Format**: TSV with 19 columns
- **Primary key**: `id` column (cpd00001, cpd00027, etc.)
- **Source**: https://github.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compounds.tsv

**reactions.tsv**:
- **Size**: 43,775 lines (including header)
- **Format**: TSV with 20+ columns
- **Primary key**: `id` column (rxn00001, rxn00148, etc.)
- **Source**: https://github.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv

### Compounds Database Schema

**Key Columns**:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | String | ModelSEED compound ID (primary key) | `cpd00027` |
| `abbreviation` | String | Short code (often from BiGG) | `glc__D` |
| `name` | String | Human-readable name | `D-Glucose` |
| `formula` | String | Chemical formula | `C6H12O6` |
| `mass` | Float | Molecular mass (g/mol) | `180.0` |
| `charge` | Integer | Ionic charge | `0` |
| `inchikey` | String | Standard structure identifier | `WQZGKKKJIJFFOK-GASJEMHNSA-N` |
| `smiles` | String | Chemical structure notation | `OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O` |
| `aliases` | String | Pipe-separated external DB IDs | `KEGG: C00031\|BiGG: glc__D` |

**Example Entry**:
```
cpd00027	glc__D	D-Glucose	C6H12O6	180.0	0	WQZGKKKJIJFFOK-GASJEMHNSA-N	OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O	KEGG: C00031|BiGG: glc__D|MetaCyc: GLC
```

### Reactions Database Schema

**Key Columns**:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | String | ModelSEED reaction ID (primary key) | `rxn00148` |
| `abbreviation` | String | Short code (often KEGG ID) | `R00200` |
| `name` | String | Human-readable name | `hexokinase` |
| `equation` | String | Reaction equation with compartments | `(1) cpd00027[0] + (1) cpd00002[0] => ...` |
| `definition` | String | Equation with compound names | `(1) D-Glucose[0] + (1) ATP[0] => ...` |
| `stoichiometry` | String | Detailed stoichiometry encoding | `-1:cpd00027:0:0:"D-Glucose";...` |
| `reversibility` | String | Direction symbol (`>`, `<`, `=`) | `>` |
| `is_transport` | Integer | Transport reaction flag (0 or 1) | `0` |
| `ec_numbers` | String | Enzyme Commission numbers | `2.7.1.1` |
| `pathways` | String | Metabolic pathway names | `Glycolysis; Central Metabolism` |
| `aliases` | String | Pipe-separated external DB IDs | `KEGG: R00200\|BiGG: HEX1` |

**Example Entry**:
```
rxn00148	R00200	hexokinase	(1) cpd00027[0] + (1) cpd00002[0] => (1) cpd00008[0] + (1) cpd00067[0] + (1) cpd00079[0]	(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) H+[0] + (1) D-Glucose-6-phosphate[0]	>	2.7.1.1	Glycolysis	KEGG: R00200|BiGG: HEX1
```

### Reversibility Symbols

The `reversibility` column uses these symbols:

- `>` = **Irreversible forward** (left → right)
- `<` = **Irreversible reverse** (right → left)
- `=` = **Reversible** (can proceed both directions)

---

## Database Loading and Initialization

### Loading Behavior

**When**: Database files loaded at server startup

**How**:
1. Load TSV files into in-memory data structures
2. Index by primary key (id column) for O(1) lookup
3. Pre-process aliases column for searchability
4. Create secondary indexes for name-based searching

**Where**: Database files located in project at:
```
specs-source/references/modelseed-database/
├── compounds.tsv
└── reactions.tsv
```

For deployment, copy to:
```
src/gem_flux_mcp/data/
├── compounds.tsv
└── reactions.tsv
```

### Loading Requirements

**Memory Footprint**:
- Compounds database: ~50-80 MB in memory
- Reactions database: ~100-150 MB in memory
- Total: ~150-230 MB for both databases
- Acceptable for modern systems (minimal overhead)

**Load Time**:
- Initial load: 1-3 seconds on typical hardware
- Subsequent queries: O(1) for ID lookups, O(n) for searches
- No external network calls required (offline-first)

**Startup Validation**:
1. Verify both TSV files exist
2. Verify minimum row counts (compounds ≥ 30,000, reactions ≥ 35,000)
3. Verify required columns present
4. Log database statistics (counts, load time)

**Error Handling on Load Failure**:
- If files missing → Log error, server fails to start with clear message
- If files corrupted → Log error, server fails to start with diagnostic info
- If files outdated → Log warning, continue (backward compatible)

---

## Database Query Operations

### Lookup by ID

**Operation**: Retrieve compound or reaction by ModelSEED ID

**Input**: Single ID string (e.g., "cpd00027" or "rxn00148")

**Output**: Complete database record for that entity

**Performance**: O(1) lookup via indexed data structure

**Behavior**:
1. Normalize ID (trim whitespace, lowercase)
2. Check if ID exists in index
3. If found → Return full record
4. If not found → Return null or raise not-found error

**Example Compound Lookup**:
```
Input: "cpd00027"
Output: {
  "id": "cpd00027",
  "abbreviation": "glc__D",
  "name": "D-Glucose",
  "formula": "C6H12O6",
  "mass": 180.0,
  "charge": 0,
  "inchikey": "WQZGKKKJIJFFOK-GASJEMHNSA-N",
  "aliases": {
    "KEGG": ["C00031"],
    "BiGG": ["glc__D"],
    "MetaCyc": ["GLC"]
  }
}
```

**Example Reaction Lookup**:
```
Input: "rxn00148"
Output: {
  "id": "rxn00148",
  "abbreviation": "R00200",
  "name": "hexokinase",
  "equation": "(1) cpd00027[0] + (1) cpd00002[0] => (1) cpd00008[0] + (1) cpd00067[0] + (1) cpd00079[0]",
  "definition": "(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) H+[0] + (1) D-Glucose-6-phosphate[0]",
  "reversibility": ">",
  "is_transport": 0,
  "ec_numbers": "2.7.1.1",
  "pathways": "Glycolysis",
  "aliases": {
    "KEGG": ["R00200"],
    "BiGG": ["HEX1"]
  }
}
```

### Search by Name or Alias

**Operation**: Find compounds/reactions matching a text query

**Input**: Search string (e.g., "glucose", "hexokinase", "2.7.1.1")

**Output**: List of matching entities, ranked by relevance

**Performance**: O(n) linear search for MVP (full-text search in future)

**Search Strategy**:
1. Normalize query (lowercase, trim)
2. Search in order of priority:
   - Exact match on ID
   - Exact match on name (case-insensitive)
   - Exact match on abbreviation
   - Partial match on name
   - Match in aliases
3. Return top N results (default: 10, max: 100)

**Matching Rules**:
- Case-insensitive
- Partial matches allowed (e.g., "gluc" matches "D-Glucose")
- Matches in name field prioritized over aliases
- Multiple word queries treated as AND (all words must match)

**Example Search**:
```
Input: "glucose"
Output: [
  {
    "id": "cpd00027",
    "name": "D-Glucose",
    "formula": "C6H12O6",
    "match_field": "name",
    "relevance": 1.0
  },
  {
    "id": "cpd00079",
    "name": "D-Glucose-6-phosphate",
    "formula": "C6H11O9P",
    "match_field": "name",
    "relevance": 0.8
  },
  ...
]
```

### Batch Lookup

**Operation**: Retrieve multiple compounds/reactions in single request

**Input**: List of IDs

**Output**: Dictionary mapping IDs to records

**Performance**: O(k) where k = number of IDs

**Behavior**:
1. Process all IDs in input list
2. For each ID, perform O(1) lookup
3. Collect results into dictionary
4. Handle missing IDs gracefully (include in "not_found" list)

**Example Batch Lookup**:
```
Input: ["cpd00027", "cpd00007", "cpd99999"]
Output: {
  "found": {
    "cpd00027": {"id": "cpd00027", "name": "D-Glucose", ...},
    "cpd00007": {"id": "cpd00007", "name": "O2", ...}
  },
  "not_found": ["cpd99999"]
}
```

---

## Alias Parsing

### Aliases Column Format

The `aliases` column contains pipe-separated database references:

```
KEGG: C00031|BiGG: glc__D|MetaCyc: GLC
```

Multiple IDs from same database separated by semicolons:

```
BiGG: glc__D;glc_D|KEGG: C00031
```

### Parsing Behavior

**Input**: Raw aliases string from TSV

**Output**: Structured dictionary of external database IDs

**Algorithm**:
1. Split on `|` to get individual database entries
2. For each entry, split on `:` to get database name and IDs
3. Split IDs on `;` if multiple IDs present
4. Return dictionary: `{"DatabaseName": ["ID1", "ID2", ...]}`

**Example Parsing**:
```
Input: "KEGG: C00031|BiGG: glc__D;glc_D|MetaCyc: GLC"

Output: {
  "KEGG": ["C00031"],
  "BiGG": ["glc__D", "glc_D"],
  "MetaCyc": ["GLC"]
}
```

**Edge Cases**:
- Empty aliases field → Return empty dict `{}`
- Malformed entry (no `:`) → Skip that entry, continue parsing
- Unknown database name → Include in output (don't filter)
- Whitespace around IDs → Strip whitespace

---

## Database Validation

### ID Validation

**Compound ID Validation**:
- Format: `cpd\d{5}` (cpd followed by exactly 5 digits)
- Valid examples: `cpd00001`, `cpd00027`, `cpd99999`
- Invalid examples: `cpd1`, `cpd0001`, `cpd000001`, `compound00027`

**Reaction ID Validation**:
- Format: `rxn\d{5}` (rxn followed by exactly 5 digits)
- Valid examples: `rxn00001`, `rxn00148`, `rxn99999`
- Invalid examples: `rxn1`, `rxn0001`, `rxn000001`, `reaction00148`

**Validation Behavior**:
1. Check format using regex pattern
2. If format valid → Check existence in database
3. If exists → Return true
4. If not exists → Return false with "not found" message
5. If format invalid → Return false with "invalid format" message

### Existence Checking

Used by all MCP tools to validate compound/reaction IDs before processing.

**validate_compound_id(compound_id)**:
- Returns: `{"valid": true}` or `{"valid": false, "error": "reason"}`

**validate_reaction_id(reaction_id)**:
- Returns: `{"valid": true}` or `{"valid": false, "error": "reason"}`

**validate_compound_ids(compound_ids)**:
- Returns: `{"valid": ["cpd00027"], "invalid": ["cpd99999"]}`

**Example Usage in build_media**:
```
Input: ["cpd00027", "cpd00007", "cpd99999"]

Validation Result: {
  "valid": ["cpd00027", "cpd00007"],
  "invalid": ["cpd99999"]
}

Action: Reject request, return error listing invalid IDs
```

---

## Common Compounds Reference

For quick reference during model building and analysis:

| ID | Name | Role | Formula |
|----|------|------|---------|
| `cpd00001` | H2O | Water | H2O |
| `cpd00002` | ATP | Energy currency | C10H12N5O13P3 |
| `cpd00003` | NAD | Oxidized cofactor | C21H26N7O14P2 |
| `cpd00004` | NADH | Reduced cofactor | C21H27N7O14P2 |
| `cpd00005` | NADP | Oxidized cofactor | C21H25N7O17P3 |
| `cpd00006` | NADPH | Reduced cofactor | C21H26N7O17P3 |
| `cpd00007` | O2 | Oxygen | O2 |
| `cpd00008` | ADP | Energy intermediate | C10H12N5O10P2 |
| `cpd00009` | Phosphate | Inorganic phosphate | HO4P |
| `cpd00011` | CO2 | Carbon dioxide | CO2 |
| `cpd00013` | NH3 | Ammonia (nitrogen source) | H3N |
| `cpd00020` | Pyruvate | Central metabolism | C3H3O3 |
| `cpd00027` | D-Glucose | Common carbon source | C6H12O6 |
| `cpd00067` | H+ | Proton | H |
| `cpd00079` | D-Glucose-6-phosphate | Glycolysis intermediate | C6H11O9P |

---

## Common Reactions Reference

For quick reference during flux analysis:

| ID | Name | EC Number | Pathway |
|----|------|-----------|---------|
| `rxn00148` | hexokinase | 2.7.1.1 | Glycolysis |
| `rxn00200` | pyruvate dehydrogenase | 1.2.4.1 | Central metabolism |
| `rxn00225` | acetate kinase | 2.7.2.1 | Fermentation |
| `rxn00350` | phosphoglycerate kinase | 2.7.2.3 | Glycolysis |
| `rxn00558` | malate dehydrogenase | 1.1.1.37 | TCA cycle |
| `rxn00782` | ATP synthase | 3.6.3.14 | Energy production |

---

## Database Update Procedures

### When to Update

- **Major ModelSEED releases**: Quarterly or as needed
- **Bug fixes in database**: As issues discovered
- **New compound/reaction additions**: When needed for new templates

### How to Update

**Download Latest Database**:
```bash
cd specs-source/references/modelseed-database/
curl -sL "https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compounds.tsv" -o compounds.tsv
curl -sL "https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/reactions.tsv" -o reactions.tsv
```

**Validate Updated Files**:
1. Check line counts: `wc -l *.tsv`
2. Verify header: `head -1 compounds.tsv`
3. Test loading: Run server with `--validate-database` flag
4. Run database test suite: `pytest tests/test_database_integration.py`

**Deployment**:
1. Copy validated files to `src/gem_flux_mcp/data/`
2. Update version in database metadata
3. Document changes in CHANGELOG.md
4. Restart server to load new database

### Backward Compatibility

**Handling Removed IDs**:
- Log warning if model references removed compound/reaction
- Provide alternative suggestions if available
- Maintain deprecated ID mapping for grace period

**Handling New Columns**:
- Ignore unknown columns during parsing
- Log new columns for future integration
- Don't break on unexpected fields

---

## Integration with MCP Tools

### Tool: build_media

**Integration Points**:
1. Validate all compound IDs in `compounds` parameter
2. Enrich output with compound names and formulas
3. Provide helpful error messages for invalid IDs

**Example**:
```
Input: {"compounds": ["cpd00027", "cpd99999"]}

Validation: Query database for both IDs
Result: cpd00027 found, cpd99999 not found

Error Response: {
  "success": false,
  "error": "invalid_compounds",
  "message": "The following compound IDs are not found in the ModelSEED database: cpd99999",
  "invalid_ids": ["cpd99999"],
  "suggestions": ["Did you mean cpd00029 (Acetate)?"]
}
```

### Tool: build_model

**Integration Points**:
1. No direct database queries (ModelSEEDpy handles internal lookups)
2. Enrich output with reaction names for added reactions
3. Provide compound/reaction details in model statistics

### Tool: gapfill_model

**Integration Points**:
1. Enrich output with names of added reactions
2. Translate reaction IDs to human-readable equations
3. Provide pathway information for gapfilled reactions

**Example**:
```
Output Enhancement:
{
  "reactions_added": [
    {
      "id": "rxn00148",
      "name": "hexokinase",
      "equation": "D-Glucose + ATP => ADP + H+ + D-Glucose-6-phosphate",
      "pathway": "Glycolysis",
      "ec_number": "2.7.1.1"
    }
  ]
}
```

### Tool: run_fba

**Integration Points**:
1. Translate reaction IDs to names in flux output
2. Group fluxes by pathway (using pathway field)
3. Provide human-readable flux interpretation

**Example Flux Output Enhancement**:
```
{
  "fluxes": [
    {
      "reaction_id": "rxn00148",
      "reaction_name": "hexokinase",
      "equation": "D-Glucose + ATP => ADP + H+ + D-Glucose-6-phosphate",
      "flux": 5.0,
      "units": "mmol/gDW/h",
      "pathway": "Glycolysis"
    }
  ]
}
```

---

## Error Handling

### Database Load Errors

**Missing Database Files**:
```
{
  "error": "database_not_found",
  "message": "ModelSEED database files not found at expected location",
  "expected_path": "src/gem_flux_mcp/data/",
  "missing_files": ["compounds.tsv", "reactions.tsv"],
  "action": "Please ensure database files are present before starting server"
}
```

**Corrupted Database Files**:
```
{
  "error": "database_corrupted",
  "message": "Failed to parse ModelSEED database files",
  "file": "compounds.tsv",
  "line": 1523,
  "details": "Unexpected number of columns (expected 19, found 15)",
  "action": "Re-download database files or restore from backup"
}
```

### Query Errors

**ID Not Found**:
```
{
  "error": "compound_not_found",
  "compound_id": "cpd99999",
  "message": "Compound ID cpd99999 not found in ModelSEED database",
  "suggestions": [
    "Check ID format (should be cpd followed by 5 digits)",
    "Search by name using search_compounds tool",
    "Verify ID from ModelSEED database documentation"
  ]
}
```

**Invalid ID Format**:
```
{
  "error": "invalid_compound_id",
  "compound_id": "compound00027",
  "message": "Invalid compound ID format",
  "expected_format": "cpd followed by exactly 5 digits (e.g., cpd00027)",
  "action": "Correct the ID format and try again"
}
```

**Search No Results**:
```
{
  "success": true,
  "query": "nonexistent compound",
  "results": [],
  "suggestions": [
    "Try a more general search term",
    "Check spelling",
    "Search in external databases (KEGG, BiGG) and find ModelSEED equivalent"
  ]
}
```

---

## Performance Considerations

### Optimization Strategies

**Indexing**:
- Primary index: Dictionary/HashMap on ID column (O(1) lookup)
- Secondary index: Lowercase name to ID mapping for fast exact matches
- Alias index: Flatten aliases for searchability

**Caching**:
- Cache frequently accessed compounds (glucose, ATP, water, etc.)
- Cache recent search queries and results (LRU cache, max 1000 entries)
- Pre-compute common compound sets (minimal media ingredients)

**Search Optimization**:
- For MVP: Simple linear search (acceptable for 30k-40k entries)
- For future: Full-text search index or SQLite FTS5
- Limit search results to top N (default 10, max 100)

### Expected Performance

**Lookup by ID**:
- Time: < 1 ms per lookup
- Throughput: > 10,000 lookups/second

**Search by Name**:
- Time: 10-50 ms per search (linear scan)
- Throughput: 20-100 searches/second

**Batch Lookup (100 IDs)**:
- Time: < 10 ms total
- Throughput: > 10,000 IDs/second

**Memory Usage**:
- Baseline: 150-230 MB for both databases
- With indexes: 200-300 MB total
- With caching: +10-50 MB depending on cache size

---

## Testing Requirements

### Unit Tests

**Database Loading**:
- Test successful load of valid TSV files
- Test handling of missing files
- Test handling of corrupted files
- Test validation of row counts and columns

**ID Validation**:
- Test valid compound IDs
- Test invalid compound IDs (wrong format)
- Test non-existent compound IDs
- Test batch validation with mixed valid/invalid IDs

**Lookup Operations**:
- Test lookup by ID (found)
- Test lookup by ID (not found)
- Test batch lookup with partial results
- Test alias parsing for various formats

**Search Operations**:
- Test exact match search
- Test partial match search
- Test case-insensitive search
- Test multi-word search
- Test search with no results

### Integration Tests

**With build_media Tool**:
- Test compound validation during media creation
- Test error messages for invalid compound IDs
- Test enrichment of media output with compound names

**With gapfill_model Tool**:
- Test enrichment of gapfilling results with reaction names
- Test pathway information inclusion

**With run_fba Tool**:
- Test flux output enrichment with reaction names
- Test human-readable flux interpretation

### Test Data

**Use Well-Known Compounds**:
```python
TEST_COMPOUNDS = {
    'cpd00001': 'H2O',
    'cpd00027': 'D-Glucose',
    'cpd00007': 'O2',
    'cpd00013': 'NH3'
}
```

**Use Well-Known Reactions**:
```python
TEST_REACTIONS = {
    'rxn00148': 'hexokinase',
    'rxn00225': 'acetate kinase',
    'rxn00558': 'malate dehydrogenase'
}
```

---

## Success Criteria

### Functional Requirements

✅ **Database loads successfully at server startup**
✅ **All compound IDs can be validated**
✅ **All reaction IDs can be validated**
✅ **Compound names can be retrieved by ID**
✅ **Reaction names and equations can be retrieved by ID**
✅ **Compounds can be searched by name**
✅ **Reactions can be searched by name**
✅ **Aliases are parsed correctly**
✅ **Batch lookups work for multiple IDs**
✅ **Invalid IDs return clear error messages**

### Performance Requirements

✅ **Database loads in < 5 seconds**
✅ **ID lookups complete in < 1 ms**
✅ **Searches return results in < 100 ms**
✅ **Memory footprint < 500 MB**
✅ **Server remains responsive during queries**

### Quality Requirements

✅ **All database operations are tested**
✅ **Error handling covers all failure modes**
✅ **Documentation includes examples**
✅ **Database can be updated without code changes**
✅ **Backward compatible with older database versions**

---

## Future Enhancements

### Post-MVP Improvements

**Full-Text Search** (v0.2.0):
- SQLite database with FTS5 virtual tables
- Multi-field search (name, aliases, formula)
- Ranking by relevance
- Faster search performance

**Expanded Metadata** (v0.3.0):
- SMILES structure validation
- InChI/InChIKey verification
- Cross-references to PubChem, ChEBI
- Thermodynamic data integration

**Database Statistics** (v0.4.0):
- Most commonly used compounds/reactions
- Coverage analysis for templates
- Database completeness metrics
- Query performance analytics

**Custom Database Extensions** (v0.5.0):
- User-defined compounds/reactions
- Private compound libraries
- Organization-specific databases
- Database merging and versioning

---

## Summary

The ModelSEED Database Integration provides the foundation for human-readable metabolic modeling in the Gem-Flux MCP Server. By loading the 33,978 compounds and 36,645 reactions at startup, the server can:

1. **Validate** all compound and reaction IDs used in models
2. **Translate** numerical IDs to human-readable names for LLMs
3. **Search** compounds and reactions by name or properties
4. **Enrich** tool outputs with biochemical context
5. **Enable** LLMs to reason about metabolic pathways

This integration is essential for all MVP tools and enables the AI-assisted metabolic modeling workflows that are the core purpose of the Gem-Flux MCP Server.
