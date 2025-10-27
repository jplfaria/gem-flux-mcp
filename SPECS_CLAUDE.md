# Claude Gem-Flux MCP Server Specification Guidelines

**PLEASE FOLLOW THESE RULES EXACTLY - CLEANROOM SPECS REQUIRE DISCIPLINE**

**Core Philosophy: SPECS DESCRIBE BEHAVIOR, NOT IMPLEMENTATION. Keep it clean.**

## 🚨 THE COMPLETE READ RULE - THIS IS NOT OPTIONAL

### READ ALL SOURCE MATERIALS BEFORE WRITING ANY SPEC
Read the ENTIRE source materials and examine ALL provided references. Every AI that skims thinks they understand, then they INVENT FEATURES THAT DON'T EXIST or MISS CRITICAL BEHAVIORS.

**Source Materials to Read**:
1. **`build_model.ipynb`** - Complete ModelSEEDpy workflow example
2. **`cobrapy-reference.md`** - FBA operations and patterns
3. **`modelseed-database-guide.md`** - Compound/reaction lookup patterns
4. **`uv-package-manager.md`** - Deployment and dependencies
5. **`additional-mcp-tools.md`** - Future roadmap
6. **`mcp-server-reference.md`** - MCP server architecture
7. **`SOURCE_MATERIALS_SUMMARY.md`** - Complete project overview
8. **`guidelines.md`** - Project-specific patterns

**ONCE YOU'VE READ EVERYTHING, YOU UNDERSTAND THE SYSTEM.** Trust your complete read. Don't second-guess what you learned.

## 📋 YOUR SPEC-WRITING TODO LIST

**MAINTAIN THIS STRUCTURE FOR EACH SPEC:**

```markdown
## Current TODO List for [Spec Name]
1. [ ] Find first unchecked item in SPECS_PLAN.md
2. [ ] Read all source materials completely
3. [ ] Identify behaviors, inputs, outputs, interactions
4. [ ] Write the specification following guidelines
5. [ ] Update SPECS_PLAN.md and commit
```

## Project Context

**Gem-Flux MCP Server** is a Model Context Protocol server for metabolic modeling workflows:

**Purpose**: Enable AI assistants and metabolic engineers to:
- Build metabolic models from protein sequences
- Create growth media compositions
- Gapfill models for specific growth conditions
- Run flux balance analysis (FBA)
- Lookup human-readable compound/reaction names

**NOT a multi-agent research system** - This is a tool integration layer, not an AI reasoning system.

**Technology Stack**:
- **Python 3.11+** with type hints
- **FastMCP** - MCP server framework
- **ModelSEEDpy (dev)** - Model building and gapfilling
- **COBRApy ≥0.27.0** - Flux balance analysis
- **Pandas** - ModelSEED database queries
- **UV** - Package manager

## 🔄 THE SPEC WORKFLOW THAT WORKS

### Step 1: UNDERSTAND THE COMPLETE SYSTEM
- Read `build_model.ipynb` to see exact ModelSEEDpy workflow
- Read `cobrapy-reference.md` to understand FBA operations
- Read `modelseed-database-guide.md` for compound/reaction lookups
- Study MCP server patterns from `mcp-server-reference.md`
- Understand the 4 MVP tools: build_media, build_model, gapfill_model, run_fba

### Step 2: FOCUS ON YOUR ASSIGNED COMPONENT
- What does it DO? (not how it's built)
- What does it RECEIVE? (inputs)
- What does it PRODUCE? (outputs)
- How does it INTERACT? (with ModelSEEDpy/COBRApy/database)

### Step 3: WRITE BEHAVIORAL SPECS
```markdown
# build_model Tool Specification

**Type**: MCP Tool
**Dependencies**: ModelSEEDpy, MSBuilder, MSTemplate

## Behavior
The build_model tool constructs a draft metabolic model from protein sequences...

## Inputs
- protein_sequences: dict[str, str]  # protein_id -> amino acid sequence
- template: str  # "GramNegative", "GramPositive", etc.
- annotate_rast: bool = False  # Offline mode for MVP

## Outputs
- model_id: str  # Unique identifier for created model
- num_reactions: int  # Reactions added from template
- num_metabolites: int  # Metabolites in model
- status: str  # "success" or error description
```

## 🎯 CLEANROOM PRINCIPLES - NEVER VIOLATE

### WHAT TO INCLUDE:
- Tool behaviors and responsibilities
- Input/output specifications
- ModelSEEDpy/COBRApy library call patterns (interface only)
- ModelSEED database query patterns
- Error conditions and handling
- Data formats (JSON structures)
- Example usage from AI assistant perspective

### WHAT TO EXCLUDE:
- Python class implementations
- Internal data structures
- Algorithm details (defer to ModelSEEDpy/COBRApy)
- Performance optimizations
- Database schema details

## 📊 UNDERSTANDING GEM-FLUX ARCHITECTURE

From your complete read, you know:

### MVP Tools (4 required)
1. **build_media**: Create media from ModelSEED compound IDs
2. **build_model**: Build model from protein sequences
3. **gapfill_model**: Add reactions to enable growth
4. **run_fba**: Execute flux balance analysis

### ModelSEED Database Tools (4 required)
1. **get_compound_name**: cpd00027 → "D-Glucose"
2. **get_reaction_name**: rxn00148 → "hexokinase"
3. **search_compounds**: Find compounds by name
4. **search_reactions**: Find reactions by name

### Data Flow
```
1. Build Media → MSMedia object
2. Build Model → MSBuilder → Draft model
3. Gapfill Model → MSGapfill → Gapfilled model
4. Run FBA → COBRApy → Fluxes + growth rate
```

### Key Concepts
- **Templates**: GramNegative, GramPositive, Core (reaction sets)
- **Gapfilling**: Add minimal reactions for growth
- **Exchange Reactions**: Uptake/secretion (prefix: EX_)
- **Biomass**: Growth objective (bio1)
- **ModelSEED IDs**: cpd00001 (compounds), rxn00001 (reactions)

## ✅ SPEC QUALITY CHECKLIST

**Before committing any spec:**
- [ ] Describes WHAT, not HOW
- [ ] All tool behaviors documented
- [ ] Inputs/outputs clearly defined with types
- [ ] Error conditions specified
- [ ] Example usage from AI assistant perspective
- [ ] Consistent with source materials (build_model.ipynb, etc.)
- [ ] No implementation details (no classes, algorithms)
- [ ] Follows MCP tool definition patterns
- [ ] Specifies ModelSEEDpy/COBRApy interfaces (not internals)

## 🚨 REMEMBER: YOU'VE READ THE SOURCES

**Once you've done the complete read, YOU KNOW THE SYSTEM.**

You know:
- How ModelSEEDpy builds models (from `build_model.ipynb`)
- How COBRApy runs FBA (from `cobrapy-reference.md`)
- How to query ModelSEED database (from `modelseed-database-guide.md`)
- How MCP servers work (from `mcp-server-reference.md`)

Other AIs skim and guess. You read completely and specify precisely.

**When you follow these rules, you write specs that are: Clear. Complete. CLEANROOM.**

## 🔄 COMMIT EACH SPEC INDIVIDUALLY

```bash
git add specs/[new-spec].md SPECS_PLAN.md
git commit -m "spec: add [component] specification"
```

One spec per commit - maintain clear history.

## 🔧 MCP TOOL DEFINITION PATTERN

Use this pattern for each tool specification:

```markdown
### build_model

Build a draft metabolic model from protein sequences.

**Input Parameters**:
```python
{
    "protein_sequences": {
        "protein_001": "MKLVINLVGNSGLG...",  # Amino acid sequence
        "protein_002": "MKQHKAMIVAL..."
    },
    "template": "GramNegative",  # or "GramPositive", "Core", etc.
    "model_name": "my_model",  # Optional human-readable name
    "annotate_rast": false  # Offline mode for MVP
}
```

**Output Structure**:
```python
{
    "success": true,
    "model_id": "model_12345",
    "model_name": "my_model",
    "template_used": "GramNegative",
    "num_reactions": 842,
    "num_metabolites": 761,
    "num_genes": 150,
    "objective": "bio1",
    "timestamp": "2025-10-26T12:34:56Z"
}
```

**Behavior**:
1. Validate protein sequences (must be valid amino acids)
2. Load specified template (GramNegative, etc.)
3. Create MSGenome from protein sequences
4. If annotate_rast=true, call RastClient (skip for MVP offline mode)
5. Build base model with MSBuilder
6. Add ATPM reaction for ATP maintenance
7. Store model with generated model_id
8. Return model metadata

**Error Conditions**:
- Invalid protein sequences → 400 error with details
- Unknown template name → 400 error listing valid templates
- RAST unavailable (when requested) → Fallback to no annotation
- Template loading failure → 500 error

**Example Usage** (from AI assistant):
```
User: "Build me a model for E. coli strain K-12"

AI Assistant calls build_model:
{
    "protein_sequences": {...},  # E. coli protein sequences
    "template": "GramNegative",
    "model_name": "ecoli_k12"
}

Response:
{
    "success": true,
    "model_id": "model_ecoli_12345",
    "num_reactions": 856,
    ...
}

AI: "I've built a metabolic model for E. coli K-12 using the GramNegative template.
The model contains 856 reactions and 761 metabolites. Model ID: model_ecoli_12345"
```

**MCP Tool Signature** (interface definition only):
```python
@mcp.tool()
async def build_model(
    protein_sequences: dict[str, str],
    template: str = "GramNegative",
    model_name: str | None = None,
    annotate_rast: bool = False
) -> dict:
    """Build draft metabolic model from protein sequences.

    This tool uses ModelSEEDpy to construct a genome-scale metabolic
    model from a set of protein sequences and a template.

    Args:
        protein_sequences: Dict mapping protein IDs to amino acid sequences
        template: ModelSEED template name (GramNegative, GramPositive, etc.)
        model_name: Optional human-readable name
        annotate_rast: Whether to annotate with RAST (requires connection)

    Returns:
        Dict with model_id, statistics, and metadata
    """
```
```

## 🔬 METABOLIC MODELING PATTERNS

### Media Specification Pattern
```python
# Media as dict of compound_id -> (lower_bound, upper_bound)
{
    "cpd00027": (-5, 100),    # D-Glucose uptake: -5 mmol/gDW/h
    "cpd00007": (-10, 100),   # O2 uptake: -10 mmol/gDW/h
    "cpd00001": (-100, 100),  # H2O
    "cpd00009": (-100, 100),  # Phosphate
    # ... other compounds
}
```

### FBA Result Pattern
```python
{
    "success": true,
    "objective_value": 0.874,  # Growth rate (1/h)
    "status": "optimal",  # or "infeasible", "unbounded"
    "active_reactions": 423,  # Reactions with non-zero flux
    "fluxes": {
        "bio1": 0.874,  # Biomass production
        "EX_glc__D_e": -5.0,  # Glucose uptake
        "EX_o2_e": -10.2,  # O2 uptake
        # ... other significant fluxes
    }
}
```

### Gapfilling Result Pattern
```python
{
    "success": true,
    "model_id": "model_12345_gapfilled",
    "reactions_added": [
        {"id": "rxn00148", "name": "hexokinase", "direction": "forward"},
        {"id": "rxn00200", "name": "pyruvate dehydrogenase", "direction": "forward"}
    ],
    "growth_rate_before": 0.0,
    "growth_rate_after": 0.874,
    "media_tested": {...}  # Media used for gapfilling
}
```

## 🚫 WHAT NOT TO SPECIFY

**Don't specify** (defer to libraries):
- How gapfilling LP is solved
- How FBA linear programming works
- Template reaction selection logic
- ATP gapfilling algorithm
- Internal ModelSEEDpy classes

**Do specify** (interfaces):
- What inputs each tool accepts
- What outputs each tool produces
- What errors can occur
- How tools interact
- What ModelSEED database queries return

---

**CRITICAL**: This is a tool integration server, not an AI reasoning system. Focus on:
- What each MCP tool does
- What ModelSEEDpy/COBRApy operations it calls
- What data it accepts and returns
- How LLMs use these tools

**Trust the source materials. They show you exactly what to specify.**
