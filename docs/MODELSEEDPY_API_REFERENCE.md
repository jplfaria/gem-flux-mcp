# ModelSEEDpy API Reference for Gem-Flux MCP

**Generated**: 2025-10-29
**Purpose**: Verified API signatures for all ModelSEEDpy classes used in Gem-Flux MCP

This document provides the **actual** API signatures from ModelSEEDpy v0.4.3 to prevent API assumption errors.

---

## MSGenome - Genome Representation

### Factory Methods (Class Methods)

```python
MSGenome.from_dna_fasta(filename)
MSGenome.from_fasta(filename, split=' ', h_func=None)
MSGenome.from_gbff_features(filename, feature_id_qualifier='protein_id', description_qualifier='product')
MSGenome.from_gbff_sequence(filename)
MSGenome.from_protein_sequences_hash(sequences)  # ✅ CORRECT - Not from_dict()
```

### Instance Attributes

- `.id` - Genome identifier
- `.features` - List of genomic features
- `.name` - Genome name

---

## MSBuilder - Model Building

### Constructor

```python
MSBuilder(
    genome,              # MSGenome object
    template=None,       # MSTemplate object
    name=None,           # Model name
    ontology_term='RAST',
    index='0'
)
```

### Key Methods

```python
.build_base_model(
    model_or_id,                           # Model ID string
    index='0',
    allow_all_non_grp_reactions=False,
    annotate_with_rast=True,
    biomass_classic=False,
    biomass_gc=0.5,
    add_reaction_from_rast_annotation=True
) -> COBRApy Model

.add_atpm(model)  # Static method - adds ATPM reaction
```

---

## MSMedia - Media Composition

### Constructor

```python
MSMedia(
    media_id,     # Media identifier
    name=''       # Optional media name
)
```

### Factory Methods

```python
MSMedia.from_dict(media_dict)
# ✅ Expects: {'cpd00027_e0': (-5, 100), 'cpd00007_e0': (-10, 100), ...}
# Returns: MSMedia object
```

### Instance Methods

```python
.get_media_constraints(cmp='e0')
# ✅ Returns: dict of {reaction_id: (lower_bound, upper_bound)}
# Example: {'cpd00027_e0': (-5.0, 100.0), ...}

.merge(media, overwrite_overlap=False)
# Merge another MSMedia into this one
```

### Instance Attributes

- `.id` - Media identifier
- `.mediacompounds` - List of MediaCompound objects
- `.name` - Media name

### ❌ DOES NOT EXIST

- `.apply_to_model()` - **This method does not exist!**
- Must manually apply constraints via `get_media_constraints()`

---

## MSGapfill - Gapfilling

### Constructor

```python
MSGapfill(
    model_or_mdlutl,                # ✅ CORRECT - Not 'model'
    default_gapfill_templates=[],
    default_gapfill_models=[],
    test_conditions=[],
    reaction_scores={},
    blacklist=[],
    atp_gapfilling=False,
    minimum_obj=0.01,
    default_excretion=100,
    default_uptake=100,
    default_target=None            # Reaction ID like 'bio1'
)
```

### Key Methods

```python
.run_gapfilling(
    media=None,           # MSMedia object
    target=None,          # ✅ Reaction ID string (e.g., 'bio1'), NOT growth rate!
    minimum_obj=None,     # ✅ Growth rate threshold (e.g., 0.01)
    binary_check=False,
    prefilter=True,
    check_for_growth=True
) -> dict
# Returns: {'reversed': {...}, 'new': {...}, 'media': MSMedia, ...}
```

### Critical Notes

- `target` expects a **reaction ID string** (like `"bio1"`), NOT a float
- `minimum_obj` is for the **growth rate threshold** (like `0.01`)
- ❌ **WRONG**: `run_gapfilling(target=0.01)` → KeyError: 0.01
- ✅ **CORRECT**: `run_gapfilling(minimum_obj=0.01)`

---

## MSATPCorrection - ATP Correction

### Constructor

```python
MSATPCorrection(
    model_or_mdlutl,          # ✅ CORRECT - Not 'model'
    core_template=None,
    atp_medias=[],            # ✅ CORRECT - Not 'tests'
    compartment='c0',
    max_gapfilling=10,
    gapfilling_delta=0,
    atp_hydrolysis_id=None,
    load_default_medias=True,
    forced_media=[],
    default_media_path=None
)
```

### Key Methods

```python
.evaluate_growth_media()
# Evaluate which media support growth

.determine_growth_media(max_gapfilling=None)
# Determine viable growth media

.apply_growth_media_gapfilling()
# Apply gapfilling for growth media

.expand_model_to_genome_scale()
# Expand model to full template

.build_tests(multiplier_hash_override={})
# Build test conditions for subsequent gapfilling
# Returns: list of test dicts for MSGapfill
```

### Helper Function

```python
from modelseedpy.core.msatpcorrection import load_default_medias

load_default_medias(default_media_path=None, default_min_obj=0.01)
# Returns: list of (MSMedia, minimum_objective) tuples
# Example: [(MSMedia('Glc.O2'), 0.01), ...]
```

---

## RastClient - RAST Annotation

### Constructor

```python
RastClient()
```

### Key Methods

```python
.annotate_genome(genome, split_terms=True)
# ✅ Annotate an MSGenome object in-place
# Does NOT return a new genome - modifies the genome parameter

.annotate_genome_from_fasta(filepath, split='|')
# Annotate directly from FASTA file
```

### ❌ DOES NOT EXIST

- `.annotate()` - **This method does not exist!**

### Correct Workflow

```python
# ✅ CORRECT
genome = MSGenome.from_fasta('path/to/file.fasta')
rast = RastClient()
rast.annotate_genome(genome)  # Modifies genome in-place

# ❌ WRONG
rast.annotate('path/to/file.fasta')  # AttributeError
```

---

## MSTemplate - Template Representation

### Factory

```python
from modelseedpy.core.mstemplate import MSTemplateBuilder

MSTemplateBuilder.from_dict(d, info=None, args=None)
# Returns: MSTemplateBuilder instance

builder.build() -> MSTemplate
# Returns: MSTemplate object
```

### Instance Attributes

- `.id` - Template identifier
- `.reactions` - DictList of template reactions
- `.compounds` - DictList of template compounds (not `.metabolites`)
- `.compartments` - Dict of compartments

---

## Common Mistakes to Avoid

### ❌ WRONG → ✅ CORRECT

```python
# MSGenome
MSGenome.from_dict(sequences)              # ❌
MSGenome.from_protein_sequences_hash(sequences)  # ✅

# MSGapfill initialization
MSGapfill(model=model, tests=tests)        # ❌
MSGapfill(model_or_mdlutl=model, test_conditions=tests)  # ✅

# MSGapfill.run_gapfilling
gapfiller.run_gapfilling(target=0.01)      # ❌ KeyError: 0.01
gapfiller.run_gapfilling(minimum_obj=0.01) # ✅

# MSATPCorrection initialization
MSATPCorrection(model=model, tests=medias) # ❌
MSATPCorrection(model_or_mdlutl=model, atp_medias=medias)  # ✅

# RastClient
rast.annotate(fasta_path)                  # ❌
genome = MSGenome.from_fasta(fasta_path)
rast.annotate_genome(genome)               # ✅

# MSMedia
media.apply_to_model(model)                # ❌ Method doesn't exist
constraints = media.get_media_constraints()
for rxn_id, (lb, ub) in constraints.items():
    model.reactions.get_by_id(rxn_id).bounds = (lb, ub)  # ✅
```

---

## API Verification Script

To verify any API before using it:

```bash
# Check available methods
uv run python -c "from modelseedpy import ClassName; print(dir(ClassName))"

# Check method signature
uv run python -c "import inspect; from modelseedpy import ClassName; print(inspect.signature(ClassName.method))"

# Read method source
uv run python -c "import inspect; from modelseedpy import ClassName; print(inspect.getsource(ClassName.method))"
```

---

**Rule**: Always check this reference before implementing ModelSEEDpy calls. Never assume an API exists.
