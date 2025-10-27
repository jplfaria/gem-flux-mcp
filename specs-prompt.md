# Gem-Flux MCP Server Specification Task

Read all materials in specs-source/ and any existing work in specs/.

Your task: Implement the FIRST UNCHECKED item from SPECS_PLAN.md by creating
CLEANROOM specifications (implementation-free behavioral specs).

## Requirements:
- Focus only on WHAT the system does, not HOW
- Define clear interfaces and capabilities
- Specify expected inputs/outputs
- Document behavioral contracts
- Follow the guidelines in SPECS_CLAUDE.md
- This is a **metabolic modeling tool server**, not a multi-agent AI system

## Process:
1. Read SPECS_PLAN.md
   - If it contains "Nothing here yet" or is empty:
     a. Study ALL materials in specs-source/ thoroughly
     b. CREATE a comprehensive specification plan with phases and checkboxes
     c. Save this plan to SPECS_PLAN.md
     d. Exit with message: "PLAN_CREATED - Please run again to start creating specs"
   - Otherwise, find the first unchecked [ ] item
2. Study all relevant materials in specs-source/, including:
   - build_metabolic_model/build_model.ipynb - ModelSEEDpy workflow example
   - references/cobrapy-reference.md - FBA operations
   - references/modelseed-database-guide.md - Database lookups
   - references/mcp-server-reference.md - MCP patterns (for reference only)
   - references/additional-mcp-tools.md - Future roadmap
   - SOURCE_MATERIALS_SUMMARY.md - Complete project overview
   - guidelines.md - Project-specific patterns
3. Review any existing specs in specs/ for context and consistency
4. Create a new specification file in specs/ with appropriate naming
   - Use numbered prefixes: 001-system-overview.md, 002-core-tools.md, etc.
   - Follow document organization from SPECS_CLAUDE.md
5. Update SPECS_PLAN.md to mark the item as complete [x]

## Completion Handling:
If you cannot find any incomplete tasks after checking SPECS_PLAN.md thoroughly:
- Output: "ALL_TASKS_COMPLETE"
- List all phases you checked
- Confirm all items show [x] instead of [ ]
- Exit without creating any new specifications

## Specification Format:
- Use clear section headers
- Add Prerequisites section when specs depend on others
- Include concrete examples from build_model.ipynb
- Document error handling behavior
- Show example usage from AI assistant perspective

## Key Elements to Specify (as relevant):

### MVP Tools (4 required)
1. **build_media** - Create growth media from ModelSEED compound IDs
2. **build_model** - Build metabolic model from protein sequences
3. **gapfill_model** - Add reactions to enable growth in specified media
4. **run_fba** - Execute flux balance analysis and return fluxes

### ModelSEED Database Tools (4 required)
1. **get_compound_name** - Get human-readable name for compound ID
2. **get_reaction_name** - Get human-readable name and equation for reaction ID
3. **search_compounds** - Find compounds by name/formula
4. **search_reactions** - Find reactions by name/enzyme

### Additional Considerations
- Model I/O (import/export JSON)
- Error handling patterns
- Data formats (JSON structures)
- Installation and deployment
- Future enhancements (batch operations, strain design)

## Examples of Good Specifications:

### Example 1: Tool Specification
```markdown
### build_media

Create a growth medium from a list of ModelSEED compound IDs.

**Input Parameters**:
```python
{
    "compounds": ["cpd00027", "cpd00007", "cpd00001", ...],  # ModelSEED IDs
    "default_uptake": 100.0,  # Default uptake bound (mmol/gDW/h)
    "custom_bounds": {  # Optional custom bounds
        "cpd00027": (-5, 100),  # Glucose: 5 mmol/gDW/h uptake
        "cpd00007": (-10, 100)  # O2: 10 mmol/gDW/h uptake
    }
}
```

**Output Structure**:
```python
{
    "success": true,
    "media_id": "media_12345",
    "compounds": [
        {"id": "cpd00027", "name": "D-Glucose", "bounds": (-5, 100)},
        {"id": "cpd00007", "name": "O2", "bounds": (-10, 100)},
        ...
    ],
    "num_compounds": 15
}
```

**Behavior**:
1. Validate all compound IDs exist in ModelSEED database
2. Create MSMedia object from compounds
3. Apply default uptake bounds to all compounds
4. Override with custom_bounds if provided
5. Store media with generated media_id
6. Return media metadata with human-readable compound names

**Error Conditions**:
- Invalid compound ID → 400 error listing invalid IDs
- Empty compounds list → 400 error
- Invalid bounds format → 400 error with details

**Example Usage**:
```
User: "Create a minimal glucose media for E. coli"

AI Assistant calls build_media:
{
    "compounds": ["cpd00027", "cpd00007", "cpd00001", "cpd00009", ...],
    "custom_bounds": {
        "cpd00027": (-5, 100),  # Limit glucose
        "cpd00007": (-10, 100)  # Aerobic conditions
    }
}

Response: { "success": true, "media_id": "media_001", ... }

AI: "I've created a minimal glucose medium with 15 compounds.
Glucose uptake is limited to 5 mmol/gDW/h. Media ID: media_001"
```
```

### Example 2: ModelSEED Database Tool
```markdown
### get_compound_name

Get human-readable name and metadata for a ModelSEED compound ID.

**Input Parameters**:
```python
{
    "compound_id": "cpd00027"
}
```

**Output Structure**:
```python
{
    "success": true,
    "id": "cpd00027",
    "name": "D-Glucose",
    "abbreviation": "glc__D",
    "formula": "C6H12O6",
    "charge": 0,
    "aliases": ["glucose", "Glc", "dextrose"]
}
```

**Behavior**:
1. Query ModelSEED compounds database (compounds.tsv)
2. Lookup compound by ID
3. Parse aliases column for alternative names
4. Return compound metadata

**Error Conditions**:
- Compound ID not found → 404 error with suggestion
- Invalid ID format → 400 error

**Example Usage**:
```
User: "What is cpd00027?"

AI Assistant calls get_compound_name:
{ "compound_id": "cpd00027" }

Response: { "name": "D-Glucose", "formula": "C6H12O6", ... }

AI: "cpd00027 is D-Glucose (C6H12O6), also known as glucose or dextrose."
```
```

### Example 3: Workflow Specification
```markdown
## Complete Model Building Workflow

This workflow shows how the MVP tools work together.

**Steps**:
1. **Create Media**: Use `build_media` to define growth conditions
2. **Build Model**: Use `build_model` to create draft model from proteins
3. **Gapfill**: Use `gapfill_model` to add missing reactions
4. **Analyze**: Use `run_fba` to predict growth and fluxes

**Example**:
```python
# Step 1: Create glucose minimal media
media_result = build_media({
    "compounds": ["cpd00027", "cpd00007", "cpd00001", ...],
    "custom_bounds": {"cpd00027": (-5, 100)}
})
media_id = media_result["media_id"]

# Step 2: Build model from protein sequences
model_result = build_model({
    "protein_sequences": {"prot1": "MKLL...", "prot2": "MVAL..."},
    "template": "GramNegative"
})
model_id = model_result["model_id"]

# Step 3: Gapfill for growth in media
gapfill_result = gapfill_model({
    "model_id": model_id,
    "media_id": media_id,
    "target_growth": 0.1
})
gapfilled_model_id = gapfill_result["model_id"]

# Step 4: Run FBA
fba_result = run_fba({
    "model_id": gapfilled_model_id,
    "media_id": media_id
})
growth_rate = fba_result["objective_value"]  # 0.874 hr^-1
```

**Data Flow**:
1. Media definition → MSMedia object → media_id
2. Protein sequences → MSBuilder → draft model → model_id
3. Draft model + media → MSGapfill → gapfilled model → gapfilled_model_id
4. Gapfilled model + media → COBRApy FBA → fluxes + growth rate
```
```

## Critical Reminders:

**This is NOT**:
- ❌ A multi-agent AI research system
- ❌ A hypothesis generation system
- ❌ An LLM-based reasoning system

**This IS**:
- ✅ An MCP server exposing metabolic modeling tools
- ✅ Integration layer for ModelSEEDpy and COBRApy
- ✅ Database interface for LLM-friendly compound/reaction names
- ✅ Tool server for AI-assisted metabolic engineering

**Focus on**:
- Tool inputs and outputs
- ModelSEEDpy/COBRApy library interfaces
- Data formats and validation
- Error handling
- Example usage from AI assistant perspective

**Don't specify**:
- Internal algorithms (defer to ModelSEEDpy/COBRApy)
- Python class implementations
- Performance optimizations
- Database internals

Write your output to specs/ folder.
