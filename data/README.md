# Gem-Flux MCP Server Data Directory

This directory contains all source data files used by the Gem-Flux MCP server.

## Directory Structure

```
data/
├── media/          # Predefined growth media definitions
├── templates/      # ModelSEED template files (GramNegative, Core, etc.)
└── database/       # ModelSEED compound and reaction database files
```

## Media Library

The `media/` directory contains JSON files for commonly-used growth media:

- **glucose_minimal_aerobic.json** - Minimal glucose medium with O2 (cpd00007)
- **glucose_minimal_anaerobic.json** - Minimal glucose medium without O2
- **pyruvate_minimal_aerobic.json** - Minimal pyruvate medium with O2
- **pyruvate_minimal_anaerobic.json** - Minimal pyruvate medium without O2

Each media file follows this structure:
```json
{
  "name": "media_name",
  "description": "Human-readable description",
  "compounds": {
    "cpd00027": {
      "name": "D-Glucose",
      "bounds": [-5.0, 100.0],
      "comment": "Explanation"
    }
  }
}
```

## Templates

The `templates/` directory will contain ModelSEED template JSON files:
- GramNegative templates
- GramPositive templates
- Core metabolic templates
- Archaeal templates (future)

Templates define the reaction sets available for model building based on organism type.

## Database Files

The `database/` directory contains ModelSEED database TSV files:
- `compounds.tsv` - Compound definitions (cpd00001 format)
- `reactions.tsv` - Reaction definitions (rxn00001 format)

These files are loaded at server startup for compound/reaction lookups.

## Usage in MCP Tools

### Loading Predefined Media
```python
import json
with open('data/media/glucose_minimal_aerobic.json') as f:
    media_def = json.load(f)
```

### Loading Templates
```python
from modelseedpy import MSModelUtilities
template = MSModelUtilities.get_template("GramNegative")
```

### Loading Database
```python
import pandas as pd
compounds_df = pd.read_csv('data/database/compounds.tsv', sep='\t')
reactions_df = pd.read_csv('data/database/reactions.tsv', sep='\t')
```

## File Maintenance

- Media files: Add new predefined media as needed
- Templates: Updated when ModelSEEDpy templates change
- Database: Updated when ModelSEED database is refreshed

All file paths in specifications reference this unified `data/` directory.
