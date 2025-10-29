# ModelSEED Template Object Reference

**Purpose**: Comprehensive reference for ModelSEED MSTemplate objects to prevent confusion between templates and models.

**Date**: 2025-10-29
**ModelSEEDpy Version**: 0.4.3
**Author**: Deep analysis session

---

## Critical Distinction: Templates vs Models

### MSTemplate (from ModelSEEDpy)
- **Source**: `modelseedpy.core.mstemplate.MSTemplate`
- **Purpose**: Template for building metabolic models
- **Key attribute**: `template.compounds` (NOT `template.metabolites`)

### COBRApy Model (from COBRApy)
- **Source**: `cobra.core.Model`
- **Purpose**: Actual metabolic model
- **Key attribute**: `model.metabolites` (NOT `model.compounds`)

**⚠️ CRITICAL**: Templates use `.compounds`, Models use `.metabolites`

---

## MSTemplate Object Structure

### Top-Level Attributes

Analyzed from GramNegModelTemplateV6.json:

| Attribute | Type | Count | Description |
|-----------|------|-------|-------------|
| `id` | str | - | Template identifier (e.g., "GramNegative.modeltemplate") |
| `name` | str | - | Template name |
| `domain` | str | - | Domain (e.g., "Bacteria") |
| `template_type` | str | - | Type (e.g., "Test") |
| `biochemistry_ref` | str | - | Reference to biochemistry database |
| `reactions` | DictList | 8,584 | Template reactions (MSTemplateReaction objects) |
| **`compounds`** | DictList | **6,573** | **Template compounds (MSTemplateMetabolite objects)** |
| `compcompounds` | DictList | 7,116 | Compartmentalized compounds |
| `compartments` | DictList | 2 | Compartments (e.g., c0, e0) |
| `biomasses` | DictList | 1 | Biomass reactions |
| `complexes` | DictList | 3,296 | Protein complexes |
| `roles` | DictList | 20,548 | Functional roles |
| `pathways` | DictList | 0 | Metabolic pathways (empty in GramNeg) |
| `subsystems` | DictList | 0 | Subsystems (empty in GramNeg) |
| `drains` | None/dict | - | Drain reactions |

**❌ `metabolites`**: Does NOT exist on MSTemplate objects
**✅ `compounds`**: Use this instead

---

## MSTemplateReaction Structure

**Type**: `modelseedpy.core.mstemplate.MSTemplateReaction`

**Sample**: `rxn00594_c` (Anthranilate,NADH:oxygen oxidoreductase)

### Attributes

| Attribute | Type | Example Value | Description |
|-----------|------|---------------|-------------|
| `id` | str | "rxn00594_c" | Reaction ID with compartment |
| `name` | str | "Anthranilate,NADH:oxygen..." | Full reaction name |
| `type` | str | "conditional" | Reaction type |
| `direction` | str | varies | Reaction direction |
| `reversibility` | bool | False | Whether reaction is reversible |
| `base_cost` | float | 4 | Base gapfilling cost |
| `forward_penalty` | float | 0 | Forward direction penalty |
| `reverse_penalty` | float | -8.22197 | Reverse direction penalty |

---

## MSTemplateMetabolite Structure

**Type**: `modelseedpy.core.mstemplate.MSTemplateMetabolite`

**⚠️ Important**: This is stored in `template.compounds`, NOT `template.metabolites`

**Sample**: `cpd14495`

### Attributes

| Attribute | Type | Example Value | Description |
|-----------|------|---------------|-------------|
| `id` | str | "cpd14495" | Compound ID |
| `name` | str | "beta-D-Glucuronosyl..." | Full compound name |
| `abbreviation` | str | "beta-D-Glucuronosyl..." | Short name/abbreviation |
| `formula` | str | "C20H28NO18R" | Chemical formula |
| `mass` | float | 571 | Molecular mass |
| `charge` | int | varies | Charge state |

---

## Compartments Structure

**Type**: `cobra.core.dictlist.DictList` of `MSTemplateCompartment`

**Count**: 2 (GramNegative template)

### Common Compartments

| ID | Name | Description |
|----|------|-------------|
| `c0` | Cytosol | Intracellular compartment |
| `e0` | Extracellular | External environment |
| `p0` | Periplasm | Periplasmic space (Gram-negative) |

---

## Biomass Structure

**Type**: `modelseedpy.core.mstemplate.MSTemplateBiomass`

**Count**: 1 (typically)

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | str | Biomass reaction ID (e.g., "bio1") |
| `name` | str | Biomass name (e.g., "GramNegativeBiomass") |
| `energy` | float | Energy requirement (e.g., 40 ATP) |
| `protein` | float | Protein fraction (e.g., 0.544) |
| `rna` | float | RNA fraction (e.g., 0.191) |
| `dna` | float | DNA fraction (e.g., 0.012) |
| `lipid` | float | Lipid fraction (e.g., 0.074) |
| `cellwall` | float | Cell wall fraction (e.g., 0.158) |
| `cofactor` | float | Cofactor fraction (e.g., 0.020) |

---

## COBRApy Model Structure (for comparison)

**Type**: `cobra.core.Model`

**⚠️ Different from MSTemplate!**

### Key Differences

| MSTemplate | COBRApy Model |
|------------|---------------|
| `template.compounds` | `model.metabolites` |
| `template.reactions` | `model.reactions` |
| `template.compartments` | `model.compartments` |
| Template for building | Actual metabolic model |

---

## Code Usage Patterns

### ✅ CORRECT Usage

```python
# Template (MSTemplate)
template = load_template("GramNegative")
num_compounds = len(template.compounds)  # ✅ Correct
num_reactions = len(template.reactions)  # ✅ Correct

# Model (COBRApy Model)
model = build_model(template)
num_metabolites = len(model.metabolites)  # ✅ Correct
num_reactions = len(model.reactions)      # ✅ Correct
```

### ❌ INCORRECT Usage

```python
# Template (MSTemplate)
template = load_template("GramNegative")
num_metabolites = len(template.metabolites)  # ❌ WRONG! Attribute doesn't exist

# Model (COBRApy Model)
model = build_model(template)
num_compounds = len(model.compounds)  # ❌ WRONG! Use model.metabolites
```

---

## Where Confusion Occurs

### 1. ModelSEEDpy Naming
- `MSTemplateMetabolite` class name suggests "metabolite"
- But stored in `template.compounds` attribute
- This is ModelSEEDpy's internal naming convention

### 2. COBRApy vs ModelSEEDpy
- COBRApy uses `model.metabolites`
- ModelSEEDpy templates use `template.compounds`
- Both refer to chemical compounds, just different naming

### 3. Documentation Gaps
- ModelSEEDpy documentation doesn't clearly distinguish
- Easy to assume `template.metabolites` exists
- Must inspect actual object to discover truth

---

## Template Loading Statistics

### GramNegative Template (v6.0)
- **Reactions**: 8,584
- **Compounds**: 6,573
- **Compcompounds**: 7,116 (compartmentalized)
- **Compartments**: 2 (c0, e0)
- **Complexes**: 3,296
- **Roles**: 20,548
- **Biomasses**: 1

### Core Template (v5.2)
- **Reactions**: 252
- **Compounds**: 197
- **Compartments**: 2 (c0, e0)
- **Biomasses**: 1

---

## Bug Prevention Checklist

When working with templates:

- [ ] Use `template.compounds`, NOT `template.metabolites`
- [ ] Use `template.reactions` (same as models)
- [ ] Use `template.compartments` (same as models)
- [ ] Remember: templates BUILD models, they aren't models
- [ ] Check object type before accessing attributes
- [ ] Models use `.metabolites`, templates use `.compounds`

---

## Related Files

### Our Implementation
- `src/gem_flux_mcp/templates/loader.py` - Template loading and validation
- `src/gem_flux_mcp/tools/build_model.py` - Uses templates to build models
- `src/gem_flux_mcp/tools/gapfill_model.py` - Works with models (not templates)

### ModelSEEDpy Source
- `modelseedpy.core.mstemplate.MSTemplate` - Template class
- `modelseedpy.core.mstemplate.MSTemplateReaction` - Reaction class
- `modelseedpy.core.mstemplate.MSTemplateMetabolite` - Compound/metabolite class

---

## Known Issues Found

### Issue 1: Incorrect metabolites access (templates/loader.py:293)
```python
# WRONG
"num_metabolites": len(template.metabolites),  # ❌ Doesn't exist

# CORRECT
"num_compounds": len(template.compounds),  # ✅ Exists
```

**Status**: Need to fix this in loader.py

---

## Testing Template Access

```python
# Test script to verify template structure
from modelseedpy.core.mstemplate import MSTemplateBuilder
import json

with open('data/templates/GramNegModelTemplateV6.json', 'r') as f:
    template_dict = json.load(f)

template = MSTemplateBuilder.from_dict(template_dict).build()

# Verify attributes
assert hasattr(template, 'compounds'), "Missing compounds attribute"
assert hasattr(template, 'reactions'), "Missing reactions attribute"
assert hasattr(template, 'compartments'), "Missing compartments attribute"
assert not hasattr(template, 'metabolites'), "Should NOT have metabolites attribute"

print(f"✓ Template validated: {len(template.compounds)} compounds")
```

---

## References

1. **ModelSEEDpy GitHub**: https://github.com/Fxe/ModelSEEDpy
2. **ModelSEED Templates**: https://github.com/ModelSEED/ModelSEEDTemplates
3. **COBRApy Documentation**: https://cobrapy.readthedocs.io/
4. **This Analysis**: Based on GramNegModelTemplateV6.json (v6.0)

---

**Last Updated**: 2025-10-29
**Verified Against**: ModelSEEDpy 0.4.3, GramNegative v6.0, Core v5.2
