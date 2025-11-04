# Tool Documentation

This directory contains comprehensive documentation for all 9 tools in the gem-flux-mcp library.

## Core Workflow Tools

These are the primary tools for building, gapfilling, and analyzing metabolic models:

1. **[build_model](build_model.md)** - Build draft genome-scale metabolic models from protein sequences
2. **[gapfill_model](gapfill_model.md)** - Add reactions to enable growth in specific media
3. **[run_fba](run_fba.md)** - Execute flux balance analysis to predict growth and fluxes

## Support Tools

### Media Management

4. **build_media** - Create media definitions from compound lists with custom bounds
5. **list_media** - List all media stored in current session

### Model Management

6. **list_models** - List all models stored in current session with statistics
7. **delete_model** - Remove models from session storage

### Database Queries

8. **compound_lookup** - Query compound metadata (names, formulas, aliases)
9. **reaction_lookup** - Query reaction metadata (equations, EC numbers, pathways)

## Quick Reference

### Typical Workflow

```python
from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.tools.run_fba import run_fba
from gem_flux_mcp.tools.media_builder import build_media, BuildMediaRequest

# Load database
db_index = DatabaseIndex(
    load_compounds_database("data/database/compounds.tsv"),
    load_reactions_database("data/database/reactions.tsv")
)

# Step 1: Build model
build_result = await build_model(
    fasta_file_path="genome.faa",
    template="GramNegative",
    model_name="my_organism",
    apply_atp_correction=True
)

# Step 2: Create media
media_request = BuildMediaRequest(
    compounds=["cpd00027", "cpd00007", "cpd00009"],  # Glucose, O2, Phosphate
    default_uptake=100.0
)
media_result = build_media(media_request, db_index)

# Step 3: Gapfill model
gapfill_result = gapfill_model(
    model_id=build_result["model_id"],
    media_id=media_result["media_id"],
    db_index=db_index,
    target_growth_rate=0.01
)

# Step 4: Run FBA
fba_result = run_fba(
    model_id=gapfill_result["model_id"],
    media_id=media_result["media_id"],
    db_index=db_index
)

print(f"Growth rate: {fba_result['objective_value']:.4f}")
```

## Tool Categories

### Model Building & Refinement
- `build_model` - Initial draft model construction
- `gapfill_model` - Enable growth through reaction addition

### Analysis
- `run_fba` - Flux balance analysis for growth prediction

### Session Management
- `list_models` - View available models
- `list_media` - View available media
- `delete_model` - Clean up storage

### Data Queries
- `compound_lookup` - Metabolite information
- `reaction_lookup` - Reaction information
- `build_media` - Media construction

## Documentation Status

| Tool | Documentation | Examples | Tests |
|------|--------------|----------|-------|
| build_model | ✓ Complete | ✓ | ✓ 13 tests |
| gapfill_model | ✓ Complete | ✓ | ✓ Workflow tests |
| run_fba | ✓ Complete | ✓ | ✓ Workflow tests |
| build_media | Basic | ✓ | ✓ 11 tests |
| list_models | Basic | ✓ | ✓ |
| list_media | Basic | ✓ | ✓ |
| delete_model | Basic | ✓ | ✓ |
| compound_lookup | Basic | ✓ | ✓ 15 tests |
| reaction_lookup | Basic | ✓ | ✓ 15 tests |

## Support Tool Usage

### build_media
```python
from gem_flux_mcp.tools.media_builder import build_media, BuildMediaRequest

media_request = BuildMediaRequest(
    compounds=["cpd00027", "cpd00007", "cpd00009", "cpd00013"],
    default_uptake=100.0,
    custom_bounds={
        "cpd00007": (-20.0, 1000.0),  # Limit oxygen
    }
)
result = build_media(media_request, db_index)
```

### list_models
```python
from gem_flux_mcp.tools.list_models import list_models

models = list_models()
for model in models:
    print(f"{model['id']}: {model['reactions']} reactions")
```

### compound_lookup
```python
from gem_flux_mcp.tools.compound_lookup import compound_lookup

result = compound_lookup(
    compound_id="cpd00027",
    db_index=db_index
)
print(f"{result['name']}: {result['formula']}")
```

## See Also

- [ATP Correction Guide](../ATP_CORRECTION.md)
- [Testing Guide](../TESTING.md)
- [Example Notebooks](../../examples/)
- [Integration Tests](../../tests/integration/)

## Getting Help

For detailed documentation on each tool, see the individual markdown files in this directory.
