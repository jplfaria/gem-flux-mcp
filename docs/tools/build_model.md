# build_model Tool

## Overview

The `build_model` tool creates draft genome-scale metabolic models from protein sequences using template-based reconstruction. It's the first step in the ModelSEED workflow for building genome-scale metabolic models.

**Location**: `src/gem_flux_mcp/tools/build_model.py`

## What It Does

- Builds draft metabolic models from protein sequences
- Uses template-based reconstruction (GramNegative, GramPositive, Core)
- Optionally annotates sequences with RAST for improved reaction mapping
- Applies ATP maintenance correction by default (biologically realistic models)
- Stores models with `.draft` suffix for tracking

## What It Does NOT Do (MVP Scope)

- Does not gapfill models (use `gapfill_model` for that)
- Does not validate if model can grow
- Does not optimize or refine models beyond ATP correction
- Does not guarantee biological accuracy without gapfilling

## Function Signature

```python
async def build_model(
    protein_sequences: Optional[dict[str, str]] = None,
    fasta_file_path: Optional[str] = None,
    template: str = "GramNegative",
    model_name: Optional[str] = None,
    annotate_with_rast: bool = False,
    apply_atp_correction: bool = True,
) -> dict[str, Any]
```

## Parameters

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `protein_sequences` | `dict[str, str]` | Conditional | `None` | Dict mapping protein IDs to amino acid sequences. Mutually exclusive with `fasta_file_path`. |
| `fasta_file_path` | `str` | Conditional | `None` | Path to FASTA file (.faa) containing protein sequences. Mutually exclusive with `protein_sequences`. |
| `template` | `str` | No | `"GramNegative"` | Template name for reconstruction. Valid: "GramNegative", "GramPositive", "Core". |
| `model_name` | `str` | No | `None` | Custom model name. If not provided, auto-generated UUID is used. |
| `annotate_with_rast` | `bool` | No | `False` | Use RAST annotation service for improved functional predictions. Requires internet. Takes ~3-5 minutes. |
| `apply_atp_correction` | `bool` | No | `True` | Apply ATP correction for biologically realistic models. Tests ATP across 54 media conditions. Takes ~3-5 minutes. |

**Note**: You must provide EITHER `protein_sequences` OR `fasta_file_path`, but not both.

### Return Value

Returns a dictionary with the following structure:

```python
{
    "success": bool,
    "model_id": str,  # Model ID with .draft suffix
    "model_name": str,  # Custom name or None
    "annotated_with_rast": bool,
    "num_reactions": int,
    "num_metabolites": int,
    "num_genes": int,
    "num_exchange_reactions": int,
    "template_used": str,
    "has_biomass_reaction": bool,
    "biomass_reaction_id": str,
    "compartments": list[str],
    "has_atpm": bool,
    "atpm_reaction_id": str,
    "statistics": {
        "reactions_by_compartment": dict,
        "metabolites_by_compartment": dict,
        "reversible_reactions": int,
        "irreversible_reactions": int,
        "transport_reactions": int,
    },
    "model_properties": {
        "is_draft": bool,
        "requires_gapfilling": bool,
        "estimated_growth_without_gapfilling": float,
    },
    "atp_correction": {
        "atp_correction_applied": bool,
        "num_test_conditions": int,  # 54 if applied
        "reactions_before_correction": int,
        "reactions_after_correction": int,
        "reactions_added_by_correction": int,
        "media_tested": list[str],
    }
}
```

## Usage Examples

### Example 1: Build from FASTA File (Default Settings)

```python
from gem_flux_mcp.tools.build_model import build_model

# Build E. coli model with ATP correction (default)
result = await build_model(
    fasta_file_path="path/to/ecoli_proteins.faa",
    template="GramNegative",
    model_name="ecoli_demo"
)

print(f"Model ID: {result['model_id']}")  # ecoli_demo.draft
print(f"Reactions: {result['num_reactions']}")
print(f"ATP correction: {result['atp_correction']['atp_correction_applied']}")
```

### Example 2: Build from Protein Dict (Fast Mode)

```python
# Build without ATP correction for faster testing
protein_sequences = {
    "gene1": "MTKPTQVLVGASGAGKSTLLNQLAGEHRDWREGEILITGGQRVRELNAVAKALARSHGVEVCDVFSFDRGTLRDARQGVEPDVLLLDMSNQYAQQGVDRLLEAFK",
    "gene2": "MDTLQAADLQLKQSLAAVDTRLREAAERLGVSQQQAIESRAQELRQSVSRISDQLPQADTAVQQAALDRLHSGWQRLVQSAQRTADQAQQLNQKLAQLQQRLNTLEQRQLQLQQQE"
}

result = await build_model(
    protein_sequences=protein_sequences,
    template="GramNegative",
    model_name="test_model",
    apply_atp_correction=False  # Faster for testing
)

print(f"Model built in ~30 seconds: {result['model_id']}")
```

### Example 3: Build with RAST Annotation

```python
# Use RAST for better gene-to-reaction mapping
# Requires internet connection, takes ~5-7 minutes total
result = await build_model(
    fasta_file_path="path/to/genome.faa",
    template="GramPositive",
    model_name="bacillus_model",
    annotate_with_rast=True,  # Enable RAST
    apply_atp_correction=True  # Also apply ATP correction
)

print(f"Genes identified: {result['num_genes']}")
print(f"Reactions mapped: {result['num_reactions']}")
```

## ATP Correction Feature

### Why ATP Correction is ON by Default

ATP correction is enabled by default (`apply_atp_correction=True`) because it produces biologically realistic models that match the published ModelSEED workflow. Without ATP correction:

- Models may have unrealistic growth rates (too high or too low)
- ATP metabolism may not work correctly across different media
- Gapfilling results may be suboptimal

### What ATP Correction Does

1. **Tests ATP Production**: Evaluates model across 54 default media conditions
2. **Adds Missing Reactions**: Fills gaps in energy metabolism
3. **Expands to Genome Scale**: Ensures template reactions are available
4. **Creates Test Conditions**: Generates multi-media validation conditions for later gapfilling

### Performance Impact

- **With ATP correction**: ~3-5 minutes (first time)
- **Without ATP correction**: ~30 seconds
- **With RAST + ATP**: ~5-7 minutes total

### When to Disable ATP Correction

You can disable ATP correction (`apply_atp_correction=False`) for:

- Rapid prototyping and testing
- When you'll apply it later during `gapfill_model`
- Exploratory analysis where speed matters more than accuracy

## Model ID Conventions

Models are stored with state suffixes to track their lifecycle:

- **`.draft`**: Built but not gapfilled
- **`.draft.gf`**: Gapfilled once (after `gapfill_model`)
- **`.draft.gf.gf`**: Re-gapfilled (after second `gapfill_model`)

Example progression:
```
ecoli_demo.draft → ecoli_demo.draft.gf → ecoli_demo.draft.gf.gf
```

## Templates

### GramNegative (Default)

**Use for:**
- E. coli and related organisms
- Gram-negative bacteria
- Most common template

**Includes:**
- Core metabolism
- Gram-negative cell wall synthesis
- Periplasmic space (compartment "p0")

### GramPositive

**Use for:**
- Bacillus, Streptococcus, etc.
- Gram-positive bacteria

**Includes:**
- Core metabolism
- Gram-positive cell wall synthesis
- No periplasm

### Core

**Use for:**
- Minimal metabolism testing
- ATP correction only
- Specialized analyses

**Includes:**
- Central carbon metabolism
- Energy metabolism
- Minimal reactions

## Input Validation

### FASTA File Requirements

- Must exist and be readable
- Must have `.faa` extension
- Must start with header line (`>protein_id`)
- Sequences must contain valid amino acids

### Protein Sequence Requirements

- Dictionary must be non-empty
- Protein IDs must be unique
- Sequences must be non-empty
- Valid amino acids: `ACDEFGHIKLMNPQRSTVWY` (standard 20)
- Invalid: Stop codons (`*`), unknowns (`X`, `B`, `Z`), gaps (`-`)

### Template Validation

Must be one of: `"GramNegative"`, `"GramPositive"`, `"Core"`

## Error Handling

### Common Errors

**FASTA_FILE_NOT_FOUND**
```python
{
    "error_code": "FASTA_FILE_NOT_FOUND",
    "message": "FASTA file not found or invalid format",
    "suggestions": [
        "Verify file path is correct and file exists",
        "FASTA files should have .faa extension"
    ]
}
```

**INVALID_AMINO_ACIDS**
```python
{
    "error_code": "INVALID_AMINO_ACIDS",
    "message": "Invalid amino acid characters found in protein sequences",
    "details": {
        "invalid_sequences": {
            "protein_id": {
                "invalid_chars": ["*", "X"],
                "positions": [150, 275]
            }
        }
    },
    "suggestions": [
        "Remove invalid characters or ambiguous amino acid codes",
        "Use standard 20 amino acids only: ACDEFGHIKLMNPQRSTVWY"
    ]
}
```

**RAST_ANNOTATION_ERROR**
```python
{
    "error_code": "RAST_ANNOTATION_ERROR",
    "message": "RAST annotation request failed",
    "suggestions": [
        "Check internet connection",
        "Retry with 'annotate_with_rast': false for offline mode"
    ]
}
```

**BOTH_INPUTS_PROVIDED**
```python
{
    "error_code": "BOTH_INPUTS_PROVIDED",
    "message": "Cannot provide both protein_sequences and fasta_file_path",
    "suggestions": [
        "Choose ONE input method: either 'protein_sequences' (dict) OR 'fasta_file_path' (string path)"
    ]
}
```

## Implementation Details

### Workflow Steps

1. **Validate inputs**: Check mutually exclusive inputs, template name
2. **Load protein sequences**: From dict or FASTA file
3. **Validate sequences**: Check amino acid alphabet
4. **Load template**: Get ModelSEED template object
5. **Create genome**: MSGenome object (with or without RAST)
6. **Build base model**: MSBuilder.build_base_model()
7. **Add ATPM**: ATP maintenance reaction
8. **Apply ATP correction** (if enabled): MSATPCorrection workflow
9. **Generate model ID**: With `.draft` suffix
10. **Store model**: In session storage
11. **Collect statistics**: Reactions, metabolites, compartments
12. **Return response**: With comprehensive metadata

### Key Dependencies

- **ModelSEEDpy**: Core model building library
- **MSGenome**: Genome representation
- **MSBuilder**: Model construction
- **RastClient**: RAST annotation service
- **MSATPCorrection**: ATP correction workflow (see `utils/atp_correction.py`)

### Storage

Models are stored in session storage with their test conditions:
- Model: `MODEL_STORAGE[model_id]`
- Test conditions: `MODEL_STORAGE[f"{model_id}.test_conditions"]`

Test conditions are reused by `gapfill_model` to avoid redundant ATP correction.

## Typical Workflow

```python
# Step 1: Build model
build_result = await build_model(
    fasta_file_path="genome.faa",
    template="GramNegative",
    model_name="my_organism",
    annotate_with_rast=True,
    apply_atp_correction=True
)

model_id = build_result["model_id"]  # my_organism.draft

# Step 2: Gapfill model (next tool)
from gem_flux_mcp.tools.gapfill_model import gapfill_model

gapfill_result = gapfill_model(
    model_id=model_id,
    media_id="glucose_minimal",
    target_growth_rate=0.01
)

# Step 3: Run FBA (analyze growth)
from gem_flux_mcp.tools.run_fba import run_fba

fba_result = run_fba(
    model_id=gapfill_result["model_id"],  # my_organism.draft.gf
    media_id="glucose_minimal"
)

print(f"Growth rate: {fba_result['objective_value']}")
```

## Testing

See test coverage in:
- `tests/integration/test_build_model_integration.py` (13 tests)
- `tests/integration/test_full_workflow_notebook_replication.py` (end-to-end)

Demo notebook:
- `examples/tool_demos/build_model_demo.ipynb`

## Related Tools

- **Next**: `gapfill_model` - Enable growth in specific media
- **After**: `run_fba` - Analyze flux distributions and growth rates
- **Support**: `build_media` - Create media conditions for gapfilling

## References

- ModelSEED paper: [Henry et al. 2010](https://www.nature.com/articles/nbt.1672)
- ATP correction: See `docs/ATP_CORRECTION.md`
- Source code: `src/gem_flux_mcp/tools/build_model.py`
