# ModelSEED Database Files

This directory contains the ModelSEED biochemistry database files required for compound and reaction lookups.

## Files

- **compounds.tsv** (12 MB) - 33,993 compounds with IDs, names, formulas, aliases
- **reactions.tsv** (37 MB) - 43,775 reactions with IDs, names, equations, EC numbers

## Source

Downloaded from: https://github.com/ModelSEED/ModelSEEDDatabase
Version: Latest as of October 2025

## Loading

These files are loaded at server startup by `src/gem_flux_mcp/database/loader.py`.
See specification: `specs/007-database-integration.md`

## Format

Tab-separated values (TSV) with columns documented in:
`specs-source/references/modelseed-database/DATABASE_README.md`

## Usage

```python
# Loaded automatically at server startup
# Available via database module
from gem_flux_mcp.database import get_compound_name, get_reaction_name

compound = get_compound_name("cpd00027")  # Returns "D-Glucose"
reaction = get_reaction_name("rxn00148")  # Returns reaction details
```
