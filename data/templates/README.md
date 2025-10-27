# ModelSEED Templates

This directory contains ModelSEED template files used for genome-scale metabolic model reconstruction.

## Files

- **Core-V5.2.json** (891 KB) - Core metabolic template (452 reactions)
  - Used for ATP correction gapfilling phase
  - Minimal core metabolism pathways

- **GramNegModelTemplateV6.json** (23 MB) - Gram-negative bacteria template (2,138 reactions)
  - Default template for most bacteria (E. coli, etc.)
  - Comprehensive genome-scale reconstruction

## Source

Templates from ModelSEEDpy package:
https://github.com/Fxe/ModelSEEDpy (dev branch)

## Usage

Templates are loaded at server startup by `src/gem_flux_mcp/templates/manager.py`.
See specification: `specs/017-template-management.md`

## Template Selection

- **GramNegative**: Default for Gram-negative bacteria
  - E. coli, Salmonella, Pseudomonas
  - 2,138 reactions from template

- **Core**: Used for ATP correction phase
  - 452 core metabolic reactions
  - Tests ATP production across 54 standard media

- **GramPositive**: (Future) For Gram-positive bacteria
  - B. subtilis, S. aureus
  - To be added in v0.2.0

## Loading

```python
# Loaded automatically at server startup
from gem_flux_mcp.templates import load_template

template = load_template("GramNegative")
# Returns MSTemplate object with 2,138 reactions
```
