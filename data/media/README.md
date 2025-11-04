# Predefined Media Library

This directory contains predefined growth media compositions for the Gem-Flux MCP server.

## Available Media

### Glucose-Based Media

1. **glucose_minimal_aerobic** - 18 compounds
   - Carbon source: D-Glucose (5 mmol/gDW/h)
   - Oxygen: Available (10 mmol/gDW/h)
   - Use case: Standard aerobic bacterial growth
   - Expected E. coli growth rate: 0.8-1.0 hr⁻¹

2. **glucose_minimal_anaerobic** - 17 compounds
   - Carbon source: D-Glucose (5 mmol/gDW/h)
   - Oxygen: Not available
   - Use case: Fermentative growth
   - Expected E. coli growth rate: 0.3-0.5 hr⁻¹

### Pyruvate-Based Media

3. **pyruvate_minimal_aerobic** - 18 compounds
   - Carbon source: Pyruvate (5 mmol/gDW/h)
   - Oxygen: Available (10 mmol/gDW/h)
   - Use case: TCA cycle and aerobic respiration testing
   - Expected E. coli growth rate: 0.7-0.9 hr⁻¹

4. **pyruvate_minimal_anaerobic** - 17 compounds
   - Carbon source: Pyruvate (5 mmol/gDW/h)
   - Oxygen: Not available
   - Use case: Pyruvate fermentation
   - Expected E. coli growth rate: 0.2-0.4 hr⁻¹

## Media Composition

All media include the following minimal components:

### Essential Nutrients
- **Water** (cpd00001): Solvent
- **Phosphate** (cpd00009): Phosphorus source
- **CO2** (cpd00011): Carbon dioxide
- **H+** (cpd00067): Proton
- **NH3** (cpd00013): Nitrogen source
- **SO4** (cpd00048): Sulfur source

### Trace Minerals
- **K+** (cpd00205): Potassium
- **Mg** (cpd00254): Magnesium
- **Na+** (cpd00971): Sodium
- **Ca2+** (cpd00063): Calcium
- **Cl-** (cpd00099): Chloride
- **Fe2+** (cpd10515): Iron
- **Mn2+** (cpd00030): Manganese
- **Zn2+** (cpd00034): Zinc
- **Cu2+** (cpd00058): Copper
- **Co2+** (cpd00149): Cobalt

## File Format

Each media file is a JSON document with the following structure:

```json
{
  "name": "media_name",
  "description": "Human-readable description",
  "compounds": {
    "cpd00027": {
      "name": "D-Glucose",
      "bounds": [-5.0, 100.0],
      "comment": "Carbon source, uptake limited to 5 mmol/gDW/h"
    }
    // ... more compounds
  }
}
```

### Bounds Interpretation
- Bounds are specified as `[lower, upper]` in mmol/gDW/h
- Negative lower bound: Maximum uptake rate
- Positive upper bound: Maximum secretion rate
- Example: `[-5.0, 100.0]` means up to 5 mmol/gDW/h uptake, 100 mmol/gDW/h secretion

## Usage

### Using Predefined Media in Tools

**Gapfilling:**
```json
{
  "model_id": "model_abc.draft",
  "media_id": "glucose_minimal_aerobic"
}
```

**FBA:**
```json
{
  "model_id": "model_abc.draft.gf",
  "media_id": "pyruvate_minimal_anaerobic"
}
```

### Creating Custom Variants

To create a custom variant based on predefined media:

1. Use `build_media` tool with modified compound list
2. Adjust bounds for specific compounds
3. Add or remove compounds as needed

Example: Lower oxygen availability
```json
{
  "compounds": ["cpd00027", "cpd00007", ...],
  "custom_bounds": {
    "cpd00027": [-5.0, 100.0],
    "cpd00007": [-2.0, 100.0]  // Reduced from -10.0
  }
}
```

## Loading

Predefined media are loaded automatically when the Gem-Flux server starts. They are stored in `MEDIA_STORAGE` with their name as the media_id and are immediately available for use in all tools.

## Future Extensions

Future versions may include:

- **Rich media** (e.g., LB complex medium)
- **Specialty media** (e.g., high glucose, limited nitrogen, microaerobic)
- **User media library** (save and share custom media)
- **Media composition tools** (compare, export, import)

## References

- Specification: `specs/019-predefined-media-library.md`
- ModelSEED Database: Compound IDs from ModelSEED biochemistry database
- Media Builder Tool: `specs/003-build-media-tool.md`
