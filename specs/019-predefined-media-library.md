# Predefined Media Library - Gem-Flux MCP Server

**Type**: Media Library Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding media in metabolic modeling)
- Read: 002-data-formats.md (for media ID format and data structures)
- Read: 003-build-media-tool.md (for media creation and usage)

## Purpose

This specification defines the predefined media library included with the Gem-Flux MCP server. The library provides commonly-used growth media compositions that can be referenced by name without manual creation, enabling faster prototyping and standardized media conditions.

## Core Design Principles

**Common Use Cases First**:
- Focus on minimal media (glucose, pyruvate)
- Both aerobic and anaerobic conditions
- Based on standard microbiology protocols

**ModelSEED Compound IDs**:
- All compounds specified using ModelSEED IDs
- Human-readable names included for reference
- Uptake bounds follow FBA conventions

**Immutable and Versioned**:
- Predefined media cannot be modified by users
- Versions tracked if compositions change
- Users can create custom variants with build_media

## Predefined Media Library (MVP)

### 1. glucose_minimal_aerobic

**Description**: Minimal glucose medium with oxygen for aerobic growth

**Use Cases**:
- E. coli growth in aerobic conditions
- Standard aerobic bacterial cultivation
- Baseline growth conditions for model testing

**Composition** (18 compounds):

| Compound ID | Name | Bounds (mmol/gDW/h) | Role |
|-------------|------|---------------------|------|
| cpd00027 | D-Glucose | [-5.0, 100.0] | Carbon source |
| cpd00007 | O2 | [-10.0, 100.0] | Aerobic respiration |
| cpd00001 | H2O | [-100.0, 100.0] | Water |
| cpd00009 | Phosphate | [-100.0, 100.0] | Phosphorus source |
| cpd00011 | CO2 | [-100.0, 100.0] | Carbon dioxide |
| cpd00067 | H+ | [-100.0, 100.0] | Proton |
| cpd00013 | NH3 | [-100.0, 100.0] | Nitrogen source |
| cpd00048 | SO4 | [-100.0, 100.0] | Sulfur source |
| cpd00205 | K+ | [-100.0, 100.0] | Potassium |
| cpd00254 | Mg | [-100.0, 100.0] | Magnesium |
| cpd00971 | Na+ | [-100.0, 100.0] | Sodium |
| cpd00063 | Ca2+ | [-100.0, 100.0] | Calcium |
| cpd00099 | Cl- | [-100.0, 100.0] | Chloride |
| cpd10515 | Fe2+ | [-100.0, 100.0] | Iron(II) |
| cpd00030 | Mn2+ | [-100.0, 100.0] | Manganese |
| cpd00034 | Zn2+ | [-100.0, 100.0] | Zinc |
| cpd00058 | Cu2+ | [-100.0, 100.0] | Copper |
| cpd00149 | Co2+ | [-100.0, 100.0] | Cobalt |

**Media Type**: Minimal (< 50 compounds)

**Expected Growth**: E. coli ~0.8-1.0 hr⁻¹ (after gapfilling)

---

### 2. glucose_minimal_anaerobic

**Description**: Minimal glucose medium without oxygen for anaerobic growth

**Use Cases**:
- Fermentative growth
- Anaerobic bacterial cultivation
- Testing metabolic pathway shifts (respiration → fermentation)

**Composition** (17 compounds):

Same as `glucose_minimal_aerobic` **except**:
- ❌ **Removed**: cpd00007 (O2) - No oxygen
- All other compounds identical

**Media Type**: Minimal (< 50 compounds)

**Expected Growth**: E. coli ~0.3-0.5 hr⁻¹ (lower due to fermentation)

**Metabolic Differences**:
- Fermentation pathways active
- Lower ATP yield per glucose
- Accumulation of fermentation products (acetate, ethanol, formate)

---

### 3. pyruvate_minimal_aerobic

**Description**: Minimal pyruvate medium with oxygen for aerobic growth

**Use Cases**:
- Testing TCA cycle and respiration without glycolysis
- Pyruvate as alternative carbon source
- Metabolic pathway analysis

**Composition** (18 compounds):

Same as `glucose_minimal_aerobic` **except**:
- 🔄 **Replaced**: cpd00027 (D-Glucose) → cpd00020 (Pyruvate)
- Pyruvate bounds: [-5.0, 100.0] mmol/gDW/h

**Media Type**: Minimal (< 50 compounds)

**Expected Growth**: E. coli ~0.7-0.9 hr⁻¹ (slightly lower than glucose)

**Metabolic Differences**:
- Bypasses glycolysis
- Direct entry to TCA cycle
- Faster uptake kinetics

---

### 4. pyruvate_minimal_anaerobic

**Description**: Minimal pyruvate medium without oxygen for anaerobic growth

**Use Cases**:
- Anaerobic pyruvate metabolism
- Fermentation from pyruvate
- Comparing glucose vs pyruvate fermentation

**Composition** (17 compounds):

Same as `pyruvate_minimal_aerobic` **except**:
- ❌ **Removed**: cpd00007 (O2) - No oxygen
- Carbon source: cpd00020 (Pyruvate)

**Media Type**: Minimal (< 50 compounds)

**Expected Growth**: E. coli ~0.2-0.4 hr⁻¹ (fermentative)

---

## Media File Storage

### File Locations

```
data/
└── media/
    ├── glucose_minimal_aerobic.json
    ├── glucose_minimal_anaerobic.json
    ├── pyruvate_minimal_aerobic.json
    ├── pyruvate_minimal_anaerobic.json
    └── README.md
```

### File Format

Each media file is JSON with this structure:

```json
{
  "name": "glucose_minimal_aerobic",
  "description": "Minimal glucose medium with oxygen (aerobic conditions)",
  "compounds": {
    "cpd00027": {
      "name": "D-Glucose",
      "bounds": [-5.0, 100.0],
      "comment": "Carbon source, uptake limited to 5 mmol/gDW/h"
    },
    "cpd00007": {
      "name": "O2",
      "bounds": [-10.0, 100.0],
      "comment": "Oxygen for aerobic respiration"
    },
    "cpd00001": {
      "name": "H2O",
      "bounds": [-100.0, 100.0],
      "comment": "Water"
    }
    // ... additional compounds
  }
}
```

## Loading Predefined Media

### Server Startup

**Behavior**:
1. Server loads all JSON files from `data/media/` at startup
2. Predefined media added to MEDIA_STORAGE with their name as media_id
3. Available immediately without calling `build_media`

**Loading Algorithm**:

```python
import json
from pathlib import Path

def load_predefined_media() -> dict:
    """Load predefined media library at server startup.

    Returns:
        Dict mapping media names to MSMedia objects
    """
    media_dir = Path("data/media")
    predefined_media = {}

    # Load each JSON file
    for json_file in media_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            media_def = json.load(f)

        media_name = media_def["name"]

        # Convert to MSMedia object
        compounds = {}
        for cpd_id, cpd_data in media_def["compounds"].items():
            # Add _e0 suffix for extracellular compartment
            compounds[f"{cpd_id}_e0"] = tuple(cpd_data["bounds"])

        # Create MSMedia
        ms_media = MSMedia.from_dict(compounds)

        predefined_media[media_name] = ms_media
        print(f"✓ Loaded predefined media: {media_name}")

    return predefined_media

# Usage at startup:
PREDEFINED_MEDIA = load_predefined_media()
MEDIA_STORAGE.update(PREDEFINED_MEDIA)
```

## Using Predefined Media

### Example 1: Gapfill with Predefined Media

**User Intent**: "Gapfill my model for glucose minimal aerobic conditions"

**AI Assistant**:
```json
{
  "model_id": "model_abc.draft",
  "media_id": "glucose_minimal_aerobic"
}
```

**Advantages**:
- No need to manually specify 18 compounds
- Standardized media composition
- Faster workflow

### Example 2: Run FBA with Predefined Media

**User Intent**: "Run FBA on my model with pyruvate anaerobic medium"

**AI Assistant**:
```json
{
  "model_id": "model_abc.draft.gf",
  "media_id": "pyruvate_minimal_anaerobic"
}
```

### Example 3: List Available Media

**User Intent**: "What predefined media do you have?"

**AI Assistant calls `list_media`**:

Response includes:
```json
{
  "media": [
    {
      "media_id": "glucose_minimal_aerobic",
      "media_name": "glucose_minimal_aerobic",
      "num_compounds": 18,
      "media_type": "minimal",
      "is_predefined": true
    },
    {
      "media_id": "glucose_minimal_anaerobic",
      "num_compounds": 17,
      "is_predefined": true
    },
    // ... other predefined media
  ],
  "predefined_media": 4
}
```

## Media Comparison Table

| Media Name | Carbon Source | O2 | Compounds | Growth Rate* | Use Case |
|------------|---------------|-------|-----------|--------------|----------|
| glucose_minimal_aerobic | Glucose | Yes | 18 | 0.8-1.0 | Standard aerobic |
| glucose_minimal_anaerobic | Glucose | No | 17 | 0.3-0.5 | Fermentation |
| pyruvate_minimal_aerobic | Pyruvate | Yes | 18 | 0.7-0.9 | TCA cycle focus |
| pyruvate_minimal_anaerobic | Pyruvate | No | 17 | 0.2-0.4 | Pyruvate fermentation |

*Expected growth rates for E. coli after gapfilling (hr⁻¹)

## Customizing Predefined Media

### Creating Variants

Users can create custom variants based on predefined media:

**Example**: "Create glucose medium with less oxygen"

**Approach**:
1. Start with predefined media composition
2. Modify specific bounds
3. Use `build_media` to create custom variant

```python
# Conceptual workflow (not implementation)
base_media = get_predefined_media("glucose_minimal_aerobic")
custom_compounds = base_media.compounds.copy()
custom_compounds["cpd00007"] = (-2.0, 100.0)  # Reduce O2 uptake

create_media(compounds=custom_compounds)
```

**Result**: New custom media with modified oxygen availability

## Future Enhancements (Post-MVP)

### v0.2.0 - Additional Predefined Media

**Rich Media**:
- `lb_complex` - Luria-Bertani medium (>50 compounds)
- `m9_minimal` - M9 minimal medium variant

**Specialty Media**:
- `high_glucose` - 20 mmol/gDW/h glucose uptake
- `limited_nitrogen` - Reduced NH3 availability
- `microaerobic` - Limited O2 (2 mmol/gDW/h)

### v0.3.0 - Media Composition Tools

**Features**:
- `get_media_composition(media_id)` - Retrieve compound list
- `compare_media(media_id_1, media_id_2)` - Show differences
- `export_media(media_id, format="json")` - Export to file

### v0.4.0 - User Media Library

**Features**:
- Save custom media with names
- Organize media into collections
- Share media between sessions
- Import media from files

## Related Specifications

- **002-data-formats.md**: Media ID format and data structures
- **003-build-media-tool.md**: Creating custom media
- **005-gapfill-model-tool.md**: Using media for gapfilling
- **006-run-fba-tool.md**: Using media for FBA
- **018-session-management-tools.md**: list_media tool

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 020-documentation-requirements.md
