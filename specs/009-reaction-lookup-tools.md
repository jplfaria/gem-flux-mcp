# Reaction Lookup Tools Specification - Gem-Flux MCP Server

**Type**: Tool Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding ModelSEED identifiers)
- Read: 002-data-formats.md (for ModelSEED identifier conventions)
- Read: 007-database-integration.md (for database structure and loading)
- Read: 008-compound-lookup-tools.md (for consistent patterns)

## Purpose

The reaction lookup tools provide AI assistants with the ability to translate between ModelSEED reaction IDs and human-readable names, equations, and metadata. These tools enable LLMs to reason about metabolic pathways, explain gapfilling results, interpret FBA fluxes, and understand what biochemical reactions are occurring in models.

## Tools Overview

This specification covers two MCP tools:

1. **get_reaction_name** - Retrieve metadata for a single reaction ID
2. **search_reactions** - Find reactions by name, enzyme, or EC number

These tools are essential for AI-assisted metabolic modeling workflows where the AI needs to understand what reactions like "rxn00148" represent or find reaction IDs for enzymes like "hexokinase".

---

## Tool 1: get_reaction_name

### Purpose

Retrieve human-readable name, equation, and metadata for a ModelSEED reaction ID.

**What it does**:
- Looks up a single reaction by its ModelSEED ID
- Returns name, equation, EC number, reversibility, and pathways
- Converts compound IDs in equation to human-readable names
- Validates reaction ID format and existence
- Provides error messages with suggestions if reaction not found

**What it does NOT do**:
- Does not search by name (use search_reactions instead)
- Does not calculate thermodynamic properties
- Does not suggest related reactions
- Does not perform stoichiometric balancing

### Input Specification

**Input Parameters**:
```json
{
  "reaction_id": "rxn00148"
}
```

**Parameter Details**:

**reaction_id** (required)
- Type: String
- Format: Must match pattern `rxn\d{5}` (rxn followed by exactly 5 digits)
- Examples: "rxn00001", "rxn00148", "rxn00200"
- Validation: Must exist in ModelSEED reactions database
- Case sensitivity: Case-insensitive (rxn00148 = RXN00148)

**Validation Rules**:
1. reaction_id must not be empty or null
2. Must match format `rxn\d{5}` (regex pattern)
3. Must exist in reactions.tsv database
4. Whitespace trimmed before validation

### Output Specification

**Successful Response**:
```json
{
  "success": true,
  "id": "rxn00148",
  "name": "hexokinase",
  "abbreviation": "R00200",
  "equation": "(1) D-Glucose + (1) ATP => (1) ADP + (1) H+ + (1) D-Glucose-6-phosphate",
  "equation_with_ids": "(1) cpd00027[c0] + (1) cpd00002[c0] => (1) cpd00008[c0] + (1) cpd00067[c0] + (1) cpd00079[c0]",
  "reversibility": "irreversible",
  "direction": "forward",
  "is_transport": false,
  "ec_numbers": ["2.7.1.1"],
  "pathways": [
    "Glycolysis",
    "Central Metabolism"
  ],
  "deltag": -16.7,
  "deltagerr": 1.5,
  "aliases": {
    "KEGG": ["R00200"],
    "BiGG": ["HEX1"],
    "MetaCyc": ["GLUCOKIN-RXN"]
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
- Value: The reaction ID as it appears in the database
- Purpose: Confirmation of lookup

**name**
- Type: String
- Value: Human-readable reaction name from database
- Example: "hexokinase", "pyruvate dehydrogenase", "ATP synthase"
- Purpose: Primary identifier for human/LLM understanding

**abbreviation**
- Type: String
- Value: Short code from database (often KEGG reaction ID)
- Example: "R00200", "R01196", "HEX1"
- Purpose: Alternative identifier for compact display

**equation**
- Type: String
- Value: Reaction equation with human-readable compound names
- Format: Stoichiometry in parentheses, compound names, arrow indicating direction
- Example: "(1) D-Glucose + (1) ATP => (1) ADP + (1) H+ + (1) D-Glucose-6-phosphate"
- Purpose: Human-readable reaction representation
- Generated from: `definition` column in database, simplified for readability

**equation_with_ids**
- Type: String
- Value: Reaction equation with ModelSEED compound IDs
- Format: Includes compartment notation [c0], [e0], etc.
- Example: "(1) cpd00027[c0] + (1) cpd00002[c0] => (1) cpd00008[c0] + (1) cpd00067[c0] + (1) cpd00079[c0]"
- Purpose: Technical reference for model building
- Taken from: `equation` column in database

**reversibility**
- Type: String
- Value: One of "reversible", "irreversible", "irreversible_reverse"
- Mapping:
  - `=` → "reversible"
  - `>` → "irreversible"
  - `<` → "irreversible_reverse"
- Purpose: Indicates if reaction can proceed in both directions

**direction**
- Type: String
- Value: One of "forward", "reverse", "bidirectional"
- Mapping:
  - `>` → "forward"
  - `<` → "reverse"
  - `=` → "bidirectional"
- Purpose: Preferred direction of reaction

**is_transport**
- Type: Boolean
- Value: `true` if reaction moves compounds between compartments, `false` otherwise
- Taken from: `is_transport` column (0 = false, 1 = true)
- Purpose: Identify transport reactions for analysis

**ec_numbers**
- Type: Array of Strings
- Value: Enzyme Commission numbers for this reaction
- Example: ["2.7.1.1"], ["1.1.1.1", "1.1.1.2"]
- Format: Standard EC notation (e.g., "2.7.1.1")
- Purpose: Enzyme classification and cross-referencing
- Empty array `[]` if no EC numbers available

**pathways**
- Type: Array of Strings
- Value: Metabolic pathways containing this reaction
- Example: ["Glycolysis", "Central Metabolism"]
- Parsed from: `pathways` column (pipe-separated)
- Purpose: Biological context and pathway membership
- Empty array `[]` if no pathways assigned

**deltag**
- Type: Number (float)
- Value: Standard Gibbs free energy change (kJ/mol)
- Example: -16.7, 0.0, 25.3
- Purpose: Thermodynamic favorability information
- May be null if not calculated

**deltagerr**
- Type: Number (float)
- Value: Error estimate for deltag (kJ/mol)
- Example: 1.5, 2.0
- Purpose: Uncertainty in thermodynamic calculation
- May be null if not calculated

**aliases**
- Type: Object (dictionary)
- Structure: `{"DatabaseName": ["ID1", "ID2", ...]}`
- Purpose: Cross-references to external databases
- Common databases: KEGG, BiGG, MetaCyc, AraCyc
- Empty object `{}` if no aliases available
- Parsed from pipe-separated aliases column in database

### Error Responses

**Reaction Not Found**:
```json
{
  "success": false,
  "error_type": "ReactionNotFound",
  "message": "Reaction ID rxn99999 not found in ModelSEED database",
  "details": {
    "reaction_id": "rxn99999",
    "searched_in": "reactions.tsv (36,645 reactions)"
  },
  "suggestions": [
    "Check ID format: should be 'rxn' followed by exactly 5 digits",
    "Use search_reactions tool to find reactions by name or enzyme",
    "Verify ID from ModelSEED database documentation"
  ]
}
```

**Invalid Format**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid reaction ID format",
  "details": {
    "provided_id": "reaction_001",
    "expected_format": "rxn followed by exactly 5 digits",
    "regex_pattern": "rxn\\d{5}",
    "examples": ["rxn00001", "rxn00148", "rxn00200"]
  },
  "suggestions": [
    "Correct format: rxn00001, rxn00148, etc.",
    "Use search_reactions to find the correct ModelSEED ID"
  ]
}
```

**Empty Input**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Reaction ID cannot be empty",
  "details": {
    "parameter": "reaction_id",
    "received": null
  },
  "suggestions": [
    "Provide a valid ModelSEED reaction ID (e.g., rxn00148)"
  ]
}
```

### Behavioral Specification

**Lookup Process**:

**Step 1: Validate Input**
1. Check reaction_id is not null/empty
2. Trim whitespace from reaction_id
3. Convert to lowercase for case-insensitive matching
4. Validate format matches `rxn\d{5}` pattern
5. If validation fails, return format error

**Step 2: Query Database**
1. Look up reaction_id in indexed reactions DataFrame
2. Use O(1) indexed lookup (not linear search)
3. If not found, return not-found error
4. If found, retrieve full database record

**Step 3: Parse Equation**
1. Extract raw equation from `equation` column (with compound IDs)
2. Extract definition from `definition` column (with compound names)
3. Simplify definition for readability:
   - Remove compartment suffixes from compound names (e.g., "[0]")
   - Keep stoichiometric coefficients in parentheses
   - Use `=>` for forward, `<=` for reverse, `<=>` for bidirectional
4. Store both equation_with_ids and equation (readable)

**Step 4: Parse Reversibility and Direction**
1. Extract reversibility symbol from database
2. Map symbols to readable values:
   - `>` → reversibility="irreversible", direction="forward"
   - `<` → reversibility="irreversible_reverse", direction="reverse"
   - `=` → reversibility="reversible", direction="bidirectional"

**Step 5: Parse EC Numbers**
1. Extract raw ec_numbers string from database
2. Split on semicolon or pipe if multiple EC numbers
3. Trim whitespace from each EC number
4. Return as array of strings
5. If empty or null, return empty array `[]`

**Step 6: Parse Pathways**
1. Extract raw pathways string from database
2. Split on pipe character `|` for multiple pathways
3. Each pathway may have format "Database: Pathway Name (Description)"
4. Extract just the pathway name, removing database prefix
5. Return as array of strings
6. If empty or null, return empty array `[]`

**Step 7: Parse Aliases**
1. Extract raw aliases string from database record
2. Parse pipe-separated format: "DB: ID|DB: ID|..."
3. Split on `|` to get individual database entries
4. For each entry, split on `:` to get database name and IDs
5. Handle semicolon-separated multiple IDs
6. Build structured dictionary: `{"DB": ["id1", "id2"]}`

**Step 8: Parse Thermodynamic Data**
1. Extract deltag and deltagerr from database
2. Convert to float if present
3. Set to null if missing or invalid

**Step 9: Format Response**
1. Extract all fields from database record
2. Convert is_transport to boolean (0→false, 1→true)
3. Build response object with all fields
4. Return success response

**Equation Formatting Examples**:

Database `equation`: `(1) cpd00027[0] + (1) cpd00002[0] => (1) cpd00008[0] + (1) cpd00067[0] + (1) cpd00079[0]`
Database `definition`: `(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) H+[0] + (1) D-Glucose-6-phosphate[0]`

Output:
- `equation`: "(1) D-Glucose + (1) ATP => (1) ADP + (1) H+ + (1) D-Glucose-6-phosphate"
- `equation_with_ids`: "(1) cpd00027[c0] + (1) cpd00002[c0] => (1) cpd00008[c0] + (1) cpd00067[c0] + (1) cpd00079[c0]"

**Pathway Parsing Examples**:

Input: `"MetaCyc: Glycolysis (Glucose Degradation)|KEGG: rn00010 (Glycolysis / Gluconeogenesis)"`
Output: `["Glycolysis", "Glycolysis / Gluconeogenesis"]`

Input: `"Glycolysis; Central Metabolism"`
Output: `["Glycolysis", "Central Metabolism"]`

Input: `""`
Output: `[]`

**Performance**:
- Expected time: < 1 millisecond per lookup
- Database already loaded in memory at server startup
- Indexed access for O(1) performance

### Example Usage Scenarios

**Example 1: Basic Reaction Lookup**

**User**: "What is rxn00148?"

**AI Assistant**:
1. Calls `get_reaction_name({"reaction_id": "rxn00148"})`
2. Receives response with name "hexokinase", equation with glucose→G6P
3. Responds to user:

**AI Response**: "rxn00148 is hexokinase (EC 2.7.1.1), which catalyzes the conversion of D-Glucose and ATP to D-Glucose-6-phosphate and ADP. This is the first committed step of glycolysis with ΔG° = -16.7 kJ/mol (thermodynamically favorable)."

**Example 2: Understanding FBA Results**

**User**: "Why does my model have high flux through rxn00200?"

**AI Assistant**:
1. Calls `get_reaction_name({"reaction_id": "rxn00200"})`
2. Receives: name="pyruvate dehydrogenase", equation showing pyruvate→acetyl-CoA
3. Responds to user:

**AI Response**: "rxn00200 is pyruvate dehydrogenase, which converts pyruvate to acetyl-CoA. High flux through this reaction indicates your model is routing carbon from glycolysis into the TCA cycle for aerobic respiration. This is expected under aerobic conditions with glucose as the carbon source."

**Example 3: Interpreting Gapfilling Results**

**User**: "What reactions did gapfilling add?"

**AI Assistant**:
1. Receives gapfill result with added reactions: ["rxn00148", "rxn00200", "rxn00216"]
2. Calls `get_reaction_name` for each reaction ID
3. Receives names and equations
4. Responds to user:

**AI Response**: "Gapfilling added 3 reactions to enable growth:

1. rxn00148 (hexokinase): D-Glucose + ATP → G6P + ADP
   - First step of glucose utilization
2. rxn00200 (pyruvate dehydrogenase): Pyruvate → Acetyl-CoA
   - Links glycolysis to TCA cycle
3. rxn00216 (citrate synthase): Acetyl-CoA + Oxaloacetate → Citrate
   - First step of TCA cycle

These reactions form a core pathway for aerobic glucose metabolism."

**Example 4: Transport Reaction Identification**

**User**: "Which reactions move glucose across the membrane?"

**AI Assistant**:
1. First uses `search_reactions({"query": "glucose transport"})`
2. Then uses `get_reaction_name` on each result to check `is_transport` field
3. Filters for is_transport=true
4. Responds to user:

**AI Response**: "I found these glucose transport reactions:
- rxn05211: D-Glucose transport via proton symport (extracellular → cytoplasm)
- rxn08161: Glucose facilitator transporter (passive diffusion)

The is_transport flag confirms these move glucose between compartments."

**Example 5: Error Recovery**

**User**: "What is reaction rxn99999?"

**AI Assistant**:
1. Calls `get_reaction_name({"reaction_id": "rxn99999"})`
2. Receives ReactionNotFound error
3. Responds to user:

**AI Response**: "I couldn't find rxn99999 in the ModelSEED database. This ID doesn't exist. Would you like me to search for a reaction by name or enzyme instead? I can use the search_reactions tool to help you find the correct ID."

---

## Tool 2: search_reactions

### Purpose

Search for reactions by name, enzyme name, EC number, or other text.

**What it does**:
- Searches reactions database by text query
- Returns ranked list of matching reactions
- Supports partial matching and case-insensitive search
- Searches in name, EC numbers, aliases, and pathways
- Limits results to prevent overwhelming responses

**What it does NOT do**:
- Does not search by compound participation
- Does not perform stoichiometric queries
- Does not search by thermodynamic properties
- Does not learn from search history

### Input Specification

**Input Parameters**:
```json
{
  "query": "hexokinase",
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
- Examples: "hexokinase", "2.7.1.1", "glycolysis", "R00200"
- Purpose: Text to search for in reaction names, EC numbers, abbreviations, and aliases

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
  "query": "hexokinase",
  "num_results": 3,
  "results": [
    {
      "id": "rxn00148",
      "name": "hexokinase",
      "abbreviation": "R00200",
      "equation": "(1) D-Glucose + (1) ATP => (1) ADP + (1) H+ + (1) D-Glucose-6-phosphate",
      "reversibility": "irreversible",
      "ec_numbers": ["2.7.1.1"],
      "is_transport": false,
      "match_field": "name",
      "match_type": "exact"
    },
    {
      "id": "rxn01100",
      "name": "glucokinase",
      "abbreviation": "R01100",
      "equation": "(1) D-Glucose + (1) ATP => (1) ADP + (1) H+ + (1) D-Glucose-6-phosphate",
      "reversibility": "irreversible",
      "ec_numbers": ["2.7.1.2"],
      "is_transport": false,
      "match_field": "name",
      "match_type": "partial"
    },
    {
      "id": "rxn00351",
      "name": "fructokinase",
      "abbreviation": "R00760",
      "equation": "(1) D-Fructose + (1) ATP => (1) ADP + (1) H+ + (1) D-Fructose-6-phosphate",
      "reversibility": "irreversible",
      "ec_numbers": ["2.7.1.4"],
      "is_transport": false,
      "match_field": "name",
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
- Type: Array of reaction objects
- Length: 0 to limit
- Order: Ranked by relevance (exact matches first, then partial)
- Each object contains:
  - **id**: ModelSEED reaction ID
  - **name**: Human-readable reaction name
  - **abbreviation**: Short code (often KEGG ID)
  - **equation**: Human-readable reaction equation
  - **reversibility**: "reversible", "irreversible", or "irreversible_reverse"
  - **ec_numbers**: Array of EC numbers
  - **is_transport**: Boolean indicating transport reaction
  - **match_field**: Where match was found ("name", "abbreviation", "ec_numbers", "aliases", "pathways", "id")
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
  "query": "nonexistentreaction",
  "num_results": 0,
  "results": [],
  "truncated": false,
  "suggestions": [
    "Try a more general search term",
    "Check spelling of reaction or enzyme name",
    "Search by EC number (e.g., 2.7.1.1)",
    "Search by database ID from other sources (KEGG, BiGG, MetaCyc)"
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
    "Provide a search term (reaction name, enzyme, EC number, or alias)"
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
   - Check if query matches reaction ID exactly
   - If yes, return that reaction with match_type="exact"

2. **Exact name match** (case-insensitive):
   - Search name column for exact match
   - Add all exact matches to results with match_type="exact"

3. **Exact abbreviation match** (case-insensitive):
   - Search abbreviation column for exact match
   - Add to results with match_type="exact"

4. **EC number match** (exact):
   - Search ec_numbers column for exact match
   - Example: "2.7.1.1" matches hexokinase
   - Add to results with match_type="exact"

5. **Partial name match** (case-insensitive):
   - Search name column for substring match
   - Example: "kinase" matches "hexokinase"
   - Add to results with match_type="partial"

6. **Alias match** (case-insensitive):
   - Search parsed aliases for query
   - Example: "R00200" matches hexokinase (KEGG alias)
   - Add to results with match_type="partial"

7. **Pathway match** (case-insensitive):
   - Search pathway names for query
   - Example: "glycolysis" matches all glycolysis reactions
   - Add to results with match_type="partial"

**Step 3: Rank Results**
1. Exact matches before partial matches
2. Within each group, alphabetical by name
3. Limit to top N results (parameter: limit)
4. Set truncated=true if more results exist

**Step 4: Format Response**
1. For each result, retrieve full metadata
2. Format equation using definition column (human-readable)
3. Parse reversibility symbol to readable string
4. Include match_field and match_type for each result
5. Return success response

**Search Algorithm** (for MVP):
- Linear search through all reactions
- O(n) performance where n = 36,645 reactions
- Acceptable for MVP (< 100ms typical search time)
- Future: Full-text search index or SQLite FTS5

**Performance**:
- Expected time: 10-100 milliseconds per search
- Depends on: query complexity, number of matches
- No optimization required for MVP

### Example Usage Scenarios

**Example 1: Finding Reaction by Enzyme Name**

**User**: "Find the hexokinase reaction"

**AI Assistant**:
1. Calls `search_reactions({"query": "hexokinase", "limit": 5})`
2. Receives results with rxn00148 as top match
3. Responds to user:

**AI Response**: "I found the hexokinase reaction (rxn00148), which phosphorylates glucose: D-Glucose + ATP → G6P + ADP. This is EC 2.7.1.1."

**Example 2: Searching by EC Number**

**User**: "What reactions have EC number 2.7.1.1?"

**AI Assistant**:
1. Calls `search_reactions({"query": "2.7.1.1", "limit": 10})`
2. Receives multiple hexokinase variants
3. Responds to user:

**AI Response**: "I found 3 reactions with EC 2.7.1.1 (hexokinase):
- rxn00148: hexokinase (D-Glucose → G6P)
- rxn00351: fructokinase (D-Fructose → F6P)
- rxn01100: glucokinase (D-Glucose → G6P, liver-specific)

All are ATP-dependent kinases that phosphorylate hexose sugars."

**Example 3: Pathway-Based Search**

**User**: "What reactions are in glycolysis?"

**AI Assistant**:
1. Calls `search_reactions({"query": "glycolysis", "limit": 20})`
2. Receives all reactions with "glycolysis" in pathways field
3. Responds to user:

**AI Response**: "I found 15 reactions in glycolysis pathways:
1. rxn00148: hexokinase (Glucose → G6P)
2. rxn00558: phosphoglucose isomerase (G6P → F6P)
3. rxn00206: phosphofructokinase (F6P → F1,6BP)
... [continues with pathway steps]

Would you like details on any specific reaction?"

**Example 4: Ambiguous Search**

**User**: "Find ATP synthase"

**AI Assistant**:
1. Calls `search_reactions({"query": "ATP synthase", "limit": 10})`
2. Receives multiple ATP synthase complexes
3. Recognizes ambiguity, asks user:

**AI Response**: "I found several ATP synthase reactions:
- rxn00062: ATP synthase (mitochondrial)
- rxn08173: ATP synthase (bacterial)
- rxn10534: ATP synthase (chloroplast)

These differ in compartment localization and proton stoichiometry. Which one are you interested in?"

**Example 5: No Results**

**User**: "Find reaction ABC123"

**AI Assistant**:
1. Calls `search_reactions({"query": "ABC123", "limit": 10})`
2. Receives empty results
3. Responds to user:

**AI Response**: "I couldn't find any reactions matching 'ABC123' in the ModelSEED database. Could you provide more details? I can search by:
- Enzyme name (e.g., 'hexokinase', 'ATP synthase')
- EC number (e.g., '2.7.1.1')
- Database IDs from KEGG, BiGG, or MetaCyc
- Pathway name (e.g., 'glycolysis')"

**Example 6: Searching by External Database ID**

**User**: "Find KEGG reaction R00200"

**AI Assistant**:
1. Calls `search_reactions({"query": "R00200", "limit": 10})`
2. Receives rxn00148 (hexokinase) which has KEGG alias R00200
3. Responds to user:

**AI Response**: "KEGG R00200 corresponds to rxn00148 (hexokinase) in ModelSEED."

---

## Integration with Other Tools

### Used By: gapfill_model

When explaining gapfilling results to user:

1. Gapfilling returns list of added reaction IDs
2. AI calls `get_reaction_name` for each reaction to translate IDs
3. AI explains results in human terms:
   - "Added hexokinase (rxn00148) to enable glucose phosphorylation"
   - "Added pyruvate dehydrogenase (rxn00200) to connect glycolysis to TCA cycle"

### Used By: run_fba

When explaining FBA fluxes to user:

1. FBA returns fluxes for reactions with ModelSEED IDs
2. AI calls `get_reaction_name` for reactions with high flux
3. AI explains metabolic activity:
   - "High flux through rxn00148 (hexokinase) indicates active glucose consumption"
   - "Flux through rxn00216 (citrate synthase) shows TCA cycle activity"

### Used By: build_model

When describing model contents:

1. Model contains list of reaction IDs from template
2. AI calls `search_reactions` to find specific pathways
3. AI describes model capabilities:
   - "Your model contains 15 glycolysis reactions"
   - "ATP synthase is present (rxn00062) for energy production"

---

## Common Reactions Reference

For AI assistant quick reference:

| ID | Name | EC | Equation (simplified) | Pathway |
|----|------|----|-----------------------|---------|
| rxn00148 | hexokinase | 2.7.1.1 | Glucose + ATP → G6P + ADP | Glycolysis |
| rxn00558 | glucose-6-phosphate isomerase | 5.3.1.9 | G6P ↔ F6P | Glycolysis |
| rxn00200 | pyruvate dehydrogenase | 1.2.4.1 | Pyruvate → Acetyl-CoA + CO2 | TCA link |
| rxn00216 | citrate synthase | 2.3.3.1 | Acetyl-CoA + Oxaloacetate → Citrate | TCA cycle |
| rxn00062 | ATP synthase | 3.6.3.14 | ADP + Pi → ATP | Energy production |
| rxn05064 | glucose transport | - | Glucose[e] → Glucose[c] | Transport |
| rxn08173 | F0F1-ATPase | 3.6.3.14 | ADP + Pi + H+ → ATP | Respiration |

---

## Performance Considerations

### Expected Performance

**get_reaction_name**:
- Time: < 1 ms per lookup
- Throughput: > 10,000 lookups/second
- Memory: Negligible (database already loaded)

**search_reactions**:
- Time: 10-100 ms per search (linear scan)
- Throughput: 10-100 searches/second
- Memory: Negligible (uses existing database)

**Optimization Strategy**:
- MVP: Linear search (adequate performance)
- Future v0.3.0: Full-text search index
- Future v0.4.0: SQLite FTS5 for advanced queries

### Caching Opportunities

**Frequently Accessed Reactions**:
- Cache top 100 most common reactions (hexokinase, ATP synthase, etc.)
- LRU cache for recent lookups
- Cache size: ~2MB maximum

**Search Results**:
- Cache recent search queries and results
- LRU cache with max 1000 entries
- Cache invalidation: On database update only

---

## Data Flow Diagrams

### get_reaction_name Flow

```
Input: {"reaction_id": "rxn00148"}
  ↓
Validate format (rxn\d{5})
  ↓
Lookup in indexed DataFrame (O(1))
  ↓ (if found)
Retrieve database record
  ↓
Parse equation and definition
  ↓
Parse reversibility and direction
  ↓
Parse EC numbers and pathways
  ↓
Parse aliases column
  ↓
Format response with all fields
  ↓
Return: {"success": true, "name": "hexokinase", ...}
```

### search_reactions Flow

```
Input: {"query": "hexokinase", "limit": 10}
  ↓
Validate query not empty
  ↓
Normalize query (lowercase, trim)
  ↓
Search database (priority-based):
  1. Exact ID match
  2. Exact name match
  3. Exact abbreviation match
  4. EC number match
  5. Partial name match
  6. Alias match
  7. Pathway match
  ↓
Collect matches with metadata
  ↓
Rank and limit results
  ↓
Return: {"success": true, "results": [...]}
```

---

## Testing Requirements

### Test Cases for get_reaction_name

**Valid Lookups**:
1. Common reaction (rxn00148 → hexokinase)
2. Transport reaction (rxn05064 → glucose transport, is_transport=true)
3. Reversible reaction (rxn00216 → citrate synthase, reversibility="reversible")
4. Reaction with multiple EC numbers
5. Case insensitive (RXN00148 → hexokinase)

**Invalid Lookups**:
1. Non-existent ID (rxn99999 → ReactionNotFound)
2. Invalid format (reaction001 → ValidationError)
3. Empty input (→ ValidationError)
4. Wrong prefix (cpd00001 → ValidationError)

**Edge Cases**:
1. Reaction with no EC numbers
2. Reaction with no pathways
3. Reaction with no aliases
4. Reaction with very long equation
5. Reaction with special characters in name

### Test Cases for search_reactions

**Valid Searches**:
1. Exact name match ("hexokinase" → rxn00148)
2. Partial name match ("kinase" → multiple kinases)
3. Case insensitive ("HEXOKINASE" → rxn00148)
4. EC number search ("2.7.1.1" → hexokinase)
5. Pathway search ("glycolysis" → glycolysis reactions)
6. Alias search ("R00200" → rxn00148)
7. Limit parameter (limit=5 → max 5 results)

**Invalid Searches**:
1. Empty query (→ ValidationError)
2. Invalid limit (limit=500 → ValidationError)
3. Negative limit (limit=-1 → ValidationError)

**Edge Cases**:
1. No results ("nonexistentreaction" → empty results)
2. Very common term ("synthase" → many results)
3. Single character search ("A" → multiple matches)
4. Special characters in query
5. Truncation (more than limit results exist)

### Integration Tests

1. search_reactions → get_reaction_name (verify IDs)
2. gapfill_model → get_reaction_name (explain additions)
3. run_fba → get_reaction_name (explain fluxes)
4. Multiple searches in sequence (session handling)
5. Database not loaded (error handling)

---

## Quality Requirements

### Correctness
- ✅ All reaction IDs resolve to correct names
- ✅ All searches return relevant results
- ✅ Exact matches prioritized over partial matches
- ✅ Equations formatted correctly (human-readable)
- ✅ Reversibility parsed correctly
- ✅ EC numbers and pathways parsed correctly

### Reliability
- ✅ Invalid inputs produce clear error messages
- ✅ Empty results handled gracefully
- ✅ Database errors caught and reported
- ✅ No crashes on malformed queries

### Usability
- ✅ Human-readable error messages
- ✅ Helpful suggestions in errors
- ✅ Results include match context (field, type)
- ✅ Equations formatted for readability
- ✅ AI can understand and use results effectively

### Performance
- ✅ get_reaction_name: < 1ms per lookup
- ✅ search_reactions: < 100ms per search
- ✅ No memory leaks
- ✅ Acceptable performance for 36,645 reactions

---

## Future Enhancements

### Post-MVP Features

**v0.2.0 - Enhanced Search**:
- Multi-word queries with AND logic
- Compound-based search (find reactions involving glucose)
- Wildcard matching (* for any characters)
- Regular expression search
- Search result ranking by relevance score

**v0.3.0 - Advanced Lookups**:
- Batch reaction lookup (multiple IDs at once)
- Reaction filtering by properties (transport, reversible, etc.)
- Pathway enumeration (all reactions in pathway)
- Enzyme classification queries

**v0.4.0 - Database Extensions**:
- Full-text search with SQLite FTS5
- Cross-reference resolution (KEGG → ModelSEED)
- Custom reaction additions
- Reaction synonym management
- Stoichiometric queries

**v0.5.0 - Analytics**:
- Most frequently accessed reactions
- Search analytics and suggestions
- Reaction usage statistics in models
- Database coverage reports
- Pathway completion analysis

---

## Related Specifications

- **001-system-overview.md**: Overall architecture and ModelSEED identifiers
- **002-data-formats.md**: ModelSEED reaction ID format
- **004-build-model-tool.md**: Uses reactions from templates
- **005-gapfill-model-tool.md**: Adds reactions, needs explanation via lookup
- **006-run-fba-tool.md**: Returns fluxes, needs reaction names for interpretation
- **007-database-integration.md**: Database loading and structure
- **008-compound-lookup-tools.md**: Companion tools for compounds
- **013-error-handling.md**: Error response patterns

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 010-model-storage.md
