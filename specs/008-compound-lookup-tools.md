# Compound Lookup Tools Specification - Gem-Flux MCP Server

**Type**: Tool Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding ModelSEED identifiers)
- Read: 002-data-formats.md (for ModelSEED identifier conventions)
- Read: 007-database-integration.md (for database structure and loading)

## Purpose

The compound lookup tools provide AI assistants with the ability to translate between ModelSEED compound IDs and human-readable names, formulas, and metadata. These tools enable LLMs to reason about metabolic pathways, suggest media compositions, and explain FBA results by accessing the ModelSEED compounds database.

## Tools Overview

This specification covers two MCP tools:

1. **get_compound_name** - Retrieve metadata for a single compound ID
2. **search_compounds** - Find compounds by name, formula, or alias

These tools are essential for AI-assisted metabolic modeling workflows where the AI needs to understand what compounds like "cpd00027" represent or find compound IDs for substances like "glucose".

---

## Tool 1: get_compound_name

### Purpose

Retrieve human-readable name and metadata for a ModelSEED compound ID.

**What it does**:
- Looks up a single compound by its ModelSEED ID
- Returns name, formula, charge, mass, and aliases
- Validates compound ID format and existence
- Provides error messages with suggestions if compound not found

**What it does NOT do**:
- Does not search by name (use search_compounds instead)
- Does not validate chemical structure
- Does not calculate thermodynamic properties
- Does not suggest related compounds

### Input Specification

**Input Parameters**:
```json
{
  "compound_id": "cpd00027"
}
```

**Parameter Details**:

**compound_id** (required)
- Type: String
- Format: Must match pattern `cpd\d{5}` (cpd followed by exactly 5 digits)
- Examples: "cpd00001", "cpd00027", "cpd00007"
- Validation: Must exist in ModelSEED compounds database
- Case sensitivity: Case-insensitive (cpd00027 = CPD00027)

**Validation Rules**:
1. compound_id must not be empty or null
2. Must match format `cpd\d{5}` (regex pattern)
3. Must exist in compounds.tsv database
4. Whitespace trimmed before validation

### Output Specification

**Successful Response**:
```json
{
  "success": true,
  "id": "cpd00027",
  "name": "D-Glucose",
  "abbreviation": "glc__D",
  "formula": "C6H12O6",
  "mass": 180.0,
  "charge": 0,
  "inchikey": "WQZGKKKJIJFFOK-GASJEMHNSA-N",
  "smiles": "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
  "aliases": {
    "KEGG": ["C00031"],
    "BiGG": ["glc__D"],
    "MetaCyc": ["GLC"]
  }
}
```

**Output Fields**:

**success**
- Type: Boolean
- Value: `true` for successful lookup
- Always present

**id**
- Type: String
- Value: The compound ID as it appears in the database
- Purpose: Confirmation of lookup

**name**
- Type: String
- Value: Human-readable compound name from database
- Example: "D-Glucose", "H2O", "ATP"
- Purpose: Primary identifier for human/LLM understanding

**abbreviation**
- Type: String
- Value: Short code from database (often BiGG abbreviation)
- Example: "glc__D", "h2o", "atp"
- Purpose: Alternative identifier for compact display

**formula**
- Type: String
- Value: Molecular formula from database
- Example: "C6H12O6", "H2O", "C10H12N5O13P3"
- Format: Element symbols with subscript numbers
- Purpose: Chemical composition information

**mass**
- Type: Number (float)
- Value: Molecular mass in g/mol from database
- Example: 180.0, 18.0, 507.0
- Precision: Database precision (typically 1 decimal place)
- Purpose: Molecular weight information

**charge**
- Type: Integer
- Value: Ionic charge from database
- Examples: 0 (neutral), -1 (anion), +1 (cation)
- Purpose: Charge balance information for reactions

**inchikey**
- Type: String
- Value: Standard InChI key for structure identification
- Format: 27-character hash (14-10-1 pattern)
- Example: "WQZGKKKJIJFFOK-GASJEMHNSA-N"
- Purpose: Unique chemical structure identifier

**smiles**
- Type: String
- Value: SMILES notation for chemical structure
- Example: "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O"
- Purpose: Machine-readable structure representation
- May be empty if not available in database

**aliases**
- Type: Object (dictionary)
- Structure: `{"DatabaseName": ["ID1", "ID2", ...]}`
- Purpose: Cross-references to external databases
- Common databases: KEGG, BiGG, MetaCyc, PubChem, ChEBI
- Empty object `{}` if no aliases available
- Parsed from pipe-separated aliases column in database

### Error Responses

**Compound Not Found**:
```json
{
  "success": false,
  "error_type": "CompoundNotFound",
  "message": "Compound ID cpd99999 not found in ModelSEED database",
  "details": {
    "compound_id": "cpd99999",
    "searched_in": "compounds.tsv (33,978 compounds)"
  },
  "suggestions": [
    "Check ID format: should be 'cpd' followed by exactly 5 digits",
    "Use search_compounds tool to find compounds by name",
    "Verify ID from ModelSEED database documentation"
  ]
}
```

**Invalid Format**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid compound ID format",
  "details": {
    "provided_id": "compound_001",
    "expected_format": "cpd followed by exactly 5 digits",
    "regex_pattern": "cpd\\d{5}",
    "examples": ["cpd00001", "cpd00027", "cpd00007"]
  },
  "suggestions": [
    "Correct format: cpd00001, cpd00027, etc.",
    "Use search_compounds to find the correct ModelSEED ID"
  ]
}
```

**Empty Input**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Compound ID cannot be empty",
  "details": {
    "parameter": "compound_id",
    "received": null
  },
  "suggestions": [
    "Provide a valid ModelSEED compound ID (e.g., cpd00027)"
  ]
}
```

### Behavioral Specification

**Lookup Process**:

**Step 1: Validate Input**
1. Check compound_id is not null/empty
2. Trim whitespace from compound_id
3. Convert to lowercase for case-insensitive matching
4. Validate format matches `cpd\d{5}` pattern
5. If validation fails, return format error

**Step 2: Query Database**
1. Look up compound_id in indexed compounds DataFrame
2. Use O(1) indexed lookup (not linear search)
3. If not found, return not-found error
4. If found, retrieve full database record

**Step 3: Parse Aliases**
1. Extract raw aliases string from database record
2. Parse pipe-separated format: "DB: ID|DB: ID|..."
3. Split on `|` to get individual database entries
4. For each entry, split on `:` to get database name and IDs
5. Handle semicolon-separated multiple IDs: "BiGG: id1;id2"
6. Build structured dictionary: `{"DB": ["id1", "id2"]}`

**Step 4: Format Response**
1. Extract all fields from database record
2. Convert mass to float
3. Convert charge to integer
4. Build response object with all fields
5. Return success response

**Alias Parsing Examples**:

Input: `"KEGG: C00031|BiGG: glc__D|MetaCyc: GLC"`
Output: `{"KEGG": ["C00031"], "BiGG": ["glc__D"], "MetaCyc": ["GLC"]}`

Input: `"BiGG: glc__D;glc_D|KEGG: C00031"`
Output: `{"BiGG": ["glc__D", "glc_D"], "KEGG": ["C00031"]}`

Input: `""`
Output: `{}`

**Performance**:
- Expected time: < 1 millisecond per lookup
- Database already loaded in memory at server startup
- Indexed access for O(1) performance

### Example Usage Scenarios

**Example 1: Basic Compound Lookup**

**User**: "What is cpd00027?"

**AI Assistant**:
1. Calls `get_compound_name({"compound_id": "cpd00027"})`
2. Receives response with name "D-Glucose", formula "C6H12O6"
3. Responds to user:

**AI Response**: "cpd00027 is D-Glucose (C6H12O6), a simple sugar with molecular weight 180.0 g/mol. It's also known as glucose or dextrose in other databases (KEGG: C00031)."

**Example 2: Understanding FBA Results**

**User**: "Why is cpd00029 being produced by my model?"

**AI Assistant**:
1. Calls `get_compound_name({"compound_id": "cpd00029"})`
2. Receives: name="Acetate", formula="C2H3O2", charge=-1
3. Responds to user:

**AI Response**: "cpd00029 is Acetate (C2H3O2), a common fermentation product. Your model is producing acetate, which typically happens during overflow metabolism when glucose is abundant but oxygen is limited."

**Example 3: Building Media**

**User**: "I need to add ATP to my media"

**AI Assistant**:
1. First uses `search_compounds({"query": "ATP"})` to find cpd00002
2. Then uses `get_compound_name({"compound_id": "cpd00002"})` to confirm
3. Receives: name="ATP", formula="C10H12N5O13P3"
4. Uses cpd00002 in build_media call

**AI Response**: "I'll add cpd00002 (ATP - Adenosine triphosphate) to your media composition."

**Example 4: Error Recovery**

**User**: "What is compound cpd99999?"

**AI Assistant**:
1. Calls `get_compound_name({"compound_id": "cpd99999"})`
2. Receives CompoundNotFound error
3. Responds to user:

**AI Response**: "I couldn't find cpd99999 in the ModelSEED database. This ID doesn't exist. Would you like me to search for a compound by name instead? I can use the search_compounds tool to help you find the correct ID."

---

## Tool 2: search_compounds

### Purpose

Search for compounds by name, formula, alias, or other text.

**What it does**:
- Searches compounds database by text query
- Returns ranked list of matching compounds
- Supports partial matching and case-insensitive search
- Limits results to prevent overwhelming responses

**What it does NOT do**:
- Does not perform structure-based searching
- Does not search by properties (e.g., "all sugars")
- Does not provide relevance scoring (simple match ranking)
- Does not learn from search history

### Input Specification

**Input Parameters**:
```json
{
  "query": "glucose",
  "limit": 10
}
```

**Parameter Details**:

**query** (required)
- Type: String
- Minimum length: 1 character
- Maximum length: 100 characters (practical limit)
- Case sensitivity: Case-insensitive matching
- Whitespace: Trimmed before search
- Examples: "glucose", "ATP", "C6H12O6", "2.7.1.1"
- Purpose: Text to search for in compound names, formulas, abbreviations, and aliases

**limit** (optional)
- Type: Integer
- Default: 10
- Minimum: 1
- Maximum: 100
- Purpose: Maximum number of results to return
- Behavior: Returns top N matches ranked by relevance

**Validation Rules**:
1. query must not be empty after trimming
2. query must be at least 1 character
3. limit must be positive integer if provided
4. limit must not exceed 100

### Output Specification

**Successful Response**:
```json
{
  "success": true,
  "query": "glucose",
  "num_results": 5,
  "results": [
    {
      "id": "cpd00027",
      "name": "D-Glucose",
      "abbreviation": "glc__D",
      "formula": "C6H12O6",
      "mass": 180.0,
      "charge": 0,
      "match_field": "name",
      "match_type": "exact"
    },
    {
      "id": "cpd00079",
      "name": "D-Glucose-6-phosphate",
      "abbreviation": "g6p_c",
      "formula": "C6H11O9P",
      "mass": 258.0,
      "charge": -2,
      "match_field": "name",
      "match_type": "partial"
    },
    {
      "id": "cpd00221",
      "name": "D-Glucose-1-phosphate",
      "abbreviation": "g1p_c",
      "formula": "C6H11O9P",
      "mass": 258.0,
      "charge": -2,
      "match_field": "name",
      "match_type": "partial"
    },
    {
      "id": "cpd00182",
      "name": "alpha-D-Glucose",
      "abbreviation": "aglc__D",
      "formula": "C6H12O6",
      "mass": 180.0,
      "charge": 0,
      "match_field": "name",
      "match_type": "partial"
    },
    {
      "id": "cpd00138",
      "name": "Lactose",
      "abbreviation": "lcts",
      "formula": "C12H22O11",
      "mass": 342.0,
      "charge": 0,
      "match_field": "aliases",
      "match_type": "partial"
    }
  ],
  "truncated": false
}
```

**Output Fields**:

**success**
- Type: Boolean
- Value: `true` for successful search (even if no results)
- Always present

**query**
- Type: String
- Value: The search query as processed (trimmed, lowercased)
- Purpose: Confirmation of what was searched

**num_results**
- Type: Integer
- Value: Number of results returned
- Range: 0 to limit
- Purpose: Quick count of matches

**results**
- Type: Array of compound objects
- Length: 0 to limit
- Order: Ranked by relevance (exact matches first, then partial)
- Each object contains:
  - **id**: ModelSEED compound ID
  - **name**: Human-readable name
  - **abbreviation**: Short code
  - **formula**: Molecular formula
  - **mass**: Molecular mass (g/mol)
  - **charge**: Ionic charge
  - **match_field**: Where match was found ("name", "abbreviation", "formula", "aliases", "id")
  - **match_type**: Type of match ("exact" or "partial")

**truncated**
- Type: Boolean
- Value: `true` if more results exist beyond limit, `false` otherwise
- Purpose: Indicate to AI that results were limited
- Example: If 50 matches found but limit=10, truncated=true

**Empty Results Response**:
```json
{
  "success": true,
  "query": "nonexistentcompound",
  "num_results": 0,
  "results": [],
  "truncated": false,
  "suggestions": [
    "Try a more general search term",
    "Check spelling of compound name",
    "Search by formula (e.g., C6H12O6)",
    "Search by database ID from other sources (KEGG, BiGG)"
  ]
}
```

### Error Responses

**Empty Query**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Search query cannot be empty",
  "details": {
    "parameter": "query",
    "received": ""
  },
  "suggestions": [
    "Provide a search term (compound name, formula, or alias)"
  ]
}
```

**Invalid Limit**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid limit parameter",
  "details": {
    "parameter": "limit",
    "received": 500,
    "minimum": 1,
    "maximum": 100
  },
  "suggestions": [
    "Set limit between 1 and 100",
    "Default limit is 10 if not specified"
  ]
}
```

### Behavioral Specification

**Search Process**:

**Step 1: Validate Input**
1. Trim whitespace from query
2. Check query is not empty
3. Convert query to lowercase for case-insensitive matching
4. Validate limit is in range [1, 100]
5. If validation fails, return error

**Step 2: Execute Search**

**Priority-Based Matching** (search in order):

1. **Exact ID match**:
   - Check if query matches compound ID exactly
   - If yes, return that compound with match_type="exact"

2. **Exact name match** (case-insensitive):
   - Search name column for exact match
   - Add all exact matches to results with match_type="exact"

3. **Exact abbreviation match** (case-insensitive):
   - Search abbreviation column for exact match
   - Add to results with match_type="exact"

4. **Partial name match** (case-insensitive):
   - Search name column for substring match
   - Example: "gluc" matches "D-Glucose"
   - Add to results with match_type="partial"

5. **Formula match** (exact):
   - Search formula column for exact match
   - Example: "C6H12O6" matches glucose
   - Add to results with match_type="exact"

6. **Alias match** (case-insensitive):
   - Search parsed aliases for query
   - Example: "C00031" matches glucose (KEGG alias)
   - Add to results with match_type="partial"

**Step 3: Rank Results**
1. Exact matches before partial matches
2. Within each group, alphabetical by name
3. Limit to top N results (parameter: limit)
4. Set truncated=true if more results exist

**Step 4: Format Response**
1. Build results array with all match metadata
2. Include match_field and match_type for each result
3. Return success response

**Search Algorithm** (for MVP):
- Linear search through all compounds
- O(n) performance where n = 33,978 compounds
- Acceptable for MVP (< 100ms typical search time)
- Future: Full-text search index or SQLite FTS5

**Performance**:
- Expected time: 10-100 milliseconds per search
- Depends on: query complexity, number of matches
- No optimization required for MVP

### Example Usage Scenarios

**Example 1: Finding Compound by Name**

**User**: "Add glucose to my media"

**AI Assistant**:
1. Calls `search_compounds({"query": "glucose", "limit": 5})`
2. Receives results with cpd00027 (D-Glucose) as top match
3. Verifies with `get_compound_name({"compound_id": "cpd00027"})`
4. Uses cpd00027 in build_media call

**AI Response**: "I found D-Glucose (cpd00027) and added it to your media composition."

**Example 2: Searching by Formula**

**User**: "What compounds have formula C6H12O6?"

**AI Assistant**:
1. Calls `search_compounds({"query": "C6H12O6", "limit": 10})`
2. Receives multiple results: D-Glucose, alpha-D-Glucose, beta-D-Glucose, etc.
3. Responds to user:

**AI Response**: "I found several compounds with formula C6H12O6:
- cpd00027: D-Glucose
- cpd00182: alpha-D-Glucose
- cpd00224: beta-D-Glucose
- cpd00137: D-Fructose
- cpd00142: D-Galactose

These are all hexose sugars (6-carbon monosaccharides). Which one would you like to use?"

**Example 3: Ambiguous Search**

**User**: "Add phosphate"

**AI Assistant**:
1. Calls `search_compounds({"query": "phosphate", "limit": 10})`
2. Receives many results: Phosphate, Glucose-6-phosphate, ATP, etc.
3. Recognizes ambiguity, asks user:

**AI Response**: "I found several compounds with 'phosphate':
- cpd00009: Phosphate (inorganic phosphate)
- cpd00079: D-Glucose-6-phosphate
- cpd00002: ATP (adenosine triphosphate)
- cpd00008: ADP (adenosine diphosphate)
- ... and 25 more

Did you mean inorganic phosphate (cpd00009) for your media?"

**Example 4: No Results**

**User**: "Find compound XYZ123"

**AI Assistant**:
1. Calls `search_compounds({"query": "XYZ123", "limit": 10})`
2. Receives empty results
3. Responds to user:

**AI Response**: "I couldn't find any compounds matching 'XYZ123' in the ModelSEED database. Could you provide more details about the compound? I can search by:
- Common name (e.g., 'glucose', 'ATP')
- Chemical formula (e.g., 'C6H12O6')
- Database IDs from KEGG, BiGG, or MetaCyc"

**Example 5: Searching by External ID**

**User**: "Find KEGG compound C00031"

**AI Assistant**:
1. Calls `search_compounds({"query": "C00031", "limit": 10})`
2. Receives cpd00027 (D-Glucose) which has KEGG alias C00031
3. Responds to user:

**AI Response**: "KEGG C00031 corresponds to cpd00027 (D-Glucose) in ModelSEED."

---

## Integration with Other Tools

### Used By: build_media

When AI needs to convert compound names to IDs:

1. User says: "Create media with glucose and oxygen"
2. AI calls `search_compounds({"query": "glucose"})` → cpd00027
3. AI calls `search_compounds({"query": "oxygen"})` → cpd00007
4. AI calls `build_media({"compounds": ["cpd00027", "cpd00007", ...]})`

### Used By: run_fba

When explaining FBA results to user:

1. FBA returns fluxes for exchange reactions with compound IDs
2. AI calls `get_compound_name` for each compound to translate IDs
3. AI explains results in human terms:
   - "Your model is consuming 5 mmol/gDW/h of D-Glucose (cpd00027)"
   - "Your model is producing 10 mmol/gDW/h of CO2 (cpd00011)"

### Used By: gapfill_model

When explaining which compounds are involved in gapfilled reactions:

1. Gapfilling adds reaction: "cpd00027 + cpd00002 → cpd00079 + cpd00008"
2. AI calls `get_compound_name` for each compound
3. AI explains: "Added hexokinase reaction that converts D-Glucose (cpd00027) and ATP (cpd00002) to Glucose-6-phosphate (cpd00079) and ADP (cpd00008)"

---

## Common Compounds Reference

For AI assistant quick reference:

| ID | Name | Formula | Role |
|----|------|---------|------|
| cpd00001 | H2O | H2O | Water |
| cpd00002 | ATP | C10H12N5O13P3 | Energy currency |
| cpd00003 | NAD | C21H26N7O14P2 | Oxidized cofactor |
| cpd00004 | NADH | C21H27N7O14P2 | Reduced cofactor |
| cpd00007 | O2 | O2 | Electron acceptor |
| cpd00008 | ADP | C10H12N5O10P2 | Energy intermediate |
| cpd00009 | Phosphate | HO4P | Inorganic phosphate |
| cpd00011 | CO2 | CO2 | Carbon dioxide |
| cpd00013 | NH3 | H3N | Nitrogen source |
| cpd00020 | Pyruvate | C3H3O3 | Central metabolism |
| cpd00027 | D-Glucose | C6H12O6 | Carbon source |
| cpd00029 | Acetate | C2H3O2 | Fermentation product |
| cpd00067 | H+ | H | Proton |

---

## Performance Considerations

### Expected Performance

**get_compound_name**:
- Time: < 1 ms per lookup
- Throughput: > 10,000 lookups/second
- Memory: Negligible (database already loaded)

**search_compounds**:
- Time: 10-100 ms per search (linear scan)
- Throughput: 10-100 searches/second
- Memory: Negligible (uses existing database)

**Optimization Strategy**:
- MVP: Linear search (adequate performance)
- Future v0.3.0: Full-text search index
- Future v0.4.0: SQLite FTS5 for advanced queries

### Caching Opportunities

**Frequently Accessed Compounds**:
- Cache top 100 most common compounds (glucose, ATP, water, etc.)
- LRU cache for recent lookups
- Cache size: ~1MB maximum

**Search Results**:
- Cache recent search queries and results
- LRU cache with max 1000 entries
- Cache invalidation: On database update only

---

## Data Flow Diagrams

### get_compound_name Flow

```
Input: {"compound_id": "cpd00027"}
  ↓
Validate format (cpd\d{5})
  ↓
Lookup in indexed DataFrame (O(1))
  ↓ (if found)
Retrieve database record
  ↓
Parse aliases column
  ↓
Format response with all fields
  ↓
Return: {"success": true, "name": "D-Glucose", ...}
```

### search_compounds Flow

```
Input: {"query": "glucose", "limit": 10}
  ↓
Validate query not empty
  ↓
Normalize query (lowercase, trim)
  ↓
Search database (priority-based):
  1. Exact ID match
  2. Exact name match
  3. Exact abbreviation match
  4. Partial name match
  5. Formula match
  6. Alias match
  ↓
Collect matches with metadata
  ↓
Rank and limit results
  ↓
Return: {"success": true, "results": [...]}
```

---

## Testing Requirements

### Test Cases for get_compound_name

**Valid Lookups**:
1. Common compound (cpd00027 → D-Glucose)
2. Water (cpd00001 → H2O)
3. Compound with complex aliases (cpd00002 → ATP)
4. Compound with charge (cpd00029 → Acetate, charge=-1)
5. Case insensitive (CPD00027 → D-Glucose)

**Invalid Lookups**:
1. Non-existent ID (cpd99999 → CompoundNotFound)
2. Invalid format (compound001 → ValidationError)
3. Empty input (→ ValidationError)
4. Wrong prefix (rxn00001 → ValidationError)

**Edge Cases**:
1. Compound with no aliases
2. Compound with empty SMILES
3. Compound with very long name
4. Compound with special characters in name

### Test Cases for search_compounds

**Valid Searches**:
1. Exact name match ("D-Glucose" → cpd00027)
2. Partial name match ("gluc" → glucose compounds)
3. Case insensitive ("GLUCOSE" → glucose compounds)
4. Formula search ("C6H12O6" → hexoses)
5. Alias search ("C00031" → cpd00027)
6. Limit parameter (limit=5 → max 5 results)

**Invalid Searches**:
1. Empty query (→ ValidationError)
2. Invalid limit (limit=500 → ValidationError)
3. Negative limit (limit=-1 → ValidationError)

**Edge Cases**:
1. No results ("nonexistentcompound" → empty results)
2. Very common term ("phosphate" → many results)
3. Single character search ("A" → multiple matches)
4. Special characters in query
5. Truncation (more than limit results exist)

### Integration Tests

1. search_compounds → get_compound_name (verify IDs)
2. search_compounds → build_media (use found IDs)
3. Multiple searches in sequence (session handling)
4. Database not loaded (error handling)

---

## Quality Requirements

### Correctness
- ✅ All compound IDs resolve to correct names
- ✅ All searches return relevant results
- ✅ Exact matches prioritized over partial matches
- ✅ Aliases parsed correctly from database

### Reliability
- ✅ Invalid inputs produce clear error messages
- ✅ Empty results handled gracefully
- ✅ Database errors caught and reported
- ✅ No crashes on malformed queries

### Usability
- ✅ Human-readable error messages
- ✅ Helpful suggestions in errors
- ✅ Results include match context (field, type)
- ✅ AI can understand and use results effectively

### Performance
- ✅ get_compound_name: < 1ms per lookup
- ✅ search_compounds: < 100ms per search
- ✅ No memory leaks
- ✅ Acceptable performance for 33,978 compounds

---

## Future Enhancements

### Post-MVP Features

**v0.2.0 - Enhanced Search**:
- Multi-word queries with AND logic
- Wildcard matching (* for any characters)
- Regular expression search
- Search result ranking by relevance score

**v0.3.0 - Advanced Lookups**:
- Batch compound lookup (multiple IDs at once)
- Compound properties filtering (e.g., "all sugars")
- Structure-based similarity search
- Pathway membership queries

**v0.4.0 - Database Extensions**:
- Full-text search with SQLite FTS5
- Cross-reference resolution (KEGG → ModelSEED)
- Custom compound additions
- Compound synonym management

**v0.5.0 - Analytics**:
- Most frequently accessed compounds
- Search analytics and suggestions
- Compound usage statistics in models
- Database coverage reports

---

## Related Specifications

- **001-system-overview.md**: Overall architecture and ModelSEED identifiers
- **002-data-formats.md**: ModelSEED compound ID format
- **003-build-media-tool.md**: Uses compound lookup for validation
- **007-database-integration.md**: Database loading and structure
- **009-reaction-lookup-tools.md**: Similar tools for reactions
- **013-error-handling.md**: Error response patterns

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 009-reaction-lookup-tools.md
