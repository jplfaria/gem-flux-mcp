# build_model Tool Specification - Gem-Flux MCP Server

**Type**: Tool Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding ModelSEED templates and metabolic modeling workflow)
- Read: 002-data-formats.md (for protein sequence format and model output structure)

## Purpose

The `build_model` tool constructs a draft genome-scale metabolic model from a set of protein sequences using template-based reconstruction. It takes protein sequences and a template name as input, builds a base metabolic model with reactions from the template, adds an ATP maintenance (ATPM) reaction, and returns model metadata. The resulting model is a draft that typically requires gapfilling to enable growth in specific media conditions.

## Tool Overview

**What it does**:
- Creates a genome-scale metabolic model from protein sequences
- Uses template-based reconstruction (GramNegative, GramPositive, or Core templates)
- Maps protein sequences to reactions via template matching
- Adds ATP maintenance reaction for realistic energy requirements
- Returns model statistics and metadata
- Stores model in session for subsequent operations (gapfilling, FBA)

**What it does NOT do**:
- Does not gapfill the model (use gapfill_model for that)
- Does not validate if model can grow (draft models typically cannot)
- Does not optimize or refine the model

## Input Specification

### Input Parameters

**Option 1: From Dictionary (protein sequences)**:
```json
{
  "protein_sequences": {
    "protein_001": "MKLVINLVGNSGLGKSTFTQRLIN...",
    "protein_002": "MKQHKAMIVALERFRKEKRDAALL...",
    "protein_003": "MSVALERYGIDEVASIGGLVEVNN..."
  },
  "template": "GramNegative",
  "model_name": "E_coli_model",
  "annotate_with_rast": true
}
```

**Option 2: From FASTA File**:
```json
{
  "fasta_file_path": "/path/to/proteins.faa",
  "template": "GramNegative",
  "model_name": "E_coli_model",
  "annotate_with_rast": true
}
```

**Note**: Provide either `protein_sequences` OR `fasta_file_path`, not both.

### Parameter Descriptions

**protein_sequences** (conditionally required)
- Type: Object (dictionary) mapping protein IDs to amino acid sequences
- Format: Keys are protein identifiers (arbitrary strings), values are amino acid sequences
- Minimum: 1 protein sequence
- Typical: 50-5000 sequences for prokaryotes
- Amino acid alphabet: `ACDEFGHIKLMNPQRSTVWY` (standard 20 amino acids)
- Case: Uppercase recommended but case-insensitive
- Purpose: Protein sequences define the metabolic capabilities encoded by the genome
- Required: If `fasta_file_path` is not provided
- Mutually exclusive: Cannot be used with `fasta_file_path`
- Validation:
  - At least one sequence required
  - All sequences must contain only valid amino acids
  - Empty sequences are invalid
  - Duplicate protein IDs are invalid

**fasta_file_path** (conditionally required)
- Type: String (file path)
- Format: Path to FASTA file with protein sequences (.faa extension)
- Required: If `protein_sequences` is not provided
- Mutually exclusive: Cannot be used with `protein_sequences`
- Purpose: Load protein sequences from standard FASTA file
- FASTA format requirements:
  - Header lines start with `>`
  - Sequence lines contain only valid amino acids
  - Multiple sequences supported
- Example FASTA format:
  ```
  >protein_001 description here
  MKLVINLVGNSGLGKSTFTQRLIN
  VTAALERMGVKSTVFKQILKK
  >protein_002
  MKQHKAMIVALERFRKEKRDAALL
  ```
- Validation:
  - File must exist and be readable
  - File must be valid FASTA format
  - At least one sequence required
  - All sequences must contain only valid amino acids

**template** (required)
- Type: String
- Valid values:
  - `"GramNegative"` - Gram-negative bacteria (E. coli, Salmonella, etc.)
  - `"GramPositive"` - Gram-positive bacteria (Bacillus, Staphylococcus, etc.)
  - `"Core"` - Central metabolism only (smaller, faster)
- Default: No default (must be specified)
- Purpose: Template defines the reaction set available for model construction
- Template characteristics:
  - **GramNegative**: ~2000 reactions, includes periplasm (c0, e0, p0 compartments)
  - **GramPositive**: ~1800 reactions, no periplasm (c0, e0 compartments)
  - **Core**: ~200 reactions, central carbon metabolism only
- Selection guide:
  - Use GramNegative for: E. coli, Salmonella, Pseudomonas, etc.
  - Use GramPositive for: Bacillus, Staphylococcus, Streptococcus, etc.
  - Use Core for: Fast prototyping, central metabolism studies

**model_name** (optional)
- Type: String
- Default: Auto-generated from model_id
- Format: Any valid string
- Purpose: Human-readable name for the model
- Examples: `"E_coli_K12"`, `"B_subtilis_168"`, `"my_organism"`
- Used in: Model metadata, logging, future export

**annotate_with_rast** (optional)
- Type: Boolean
- Default: `true` (RAST annotation enabled by default)
- Purpose: Enable functional annotation via RAST API for improved template matching
- When `true` (default):
  - Convert protein sequences to .faa file format
  - Submit to RAST API for functional annotation
  - Use annotation results to improve reaction mapping
  - Better gene-protein-reaction (GPR) associations
- When `false`:
  - Use offline template matching only
  - Faster but less accurate reaction mapping
  - Recommended only for offline/testing scenarios
- RAST requirements:
  - Requires internet connection
  - Accepts FASTA format (.faa files)
  - Returns functional annotations (EC numbers, GO terms, etc.)
- Implementation note:
  - When user provides `protein_sequences` dict, convert to temporary .faa file
  - When user provides `fasta_file_path`, use file directly
  - Submit .faa to RAST API as shown in source jupyter notebook

### Validation Rules

**Pre-validation** (before processing):
1. Either `protein_sequences` OR `fasta_file_path` must be provided (not both, not neither)
2. If `protein_sequences`:
   - Must be non-empty dictionary
   - All protein sequence values must contain only valid amino acids: `[ACDEFGHIKLMNPQRSTVWY]`
   - No empty sequences allowed
   - Duplicate protein IDs (keys) are invalid
3. If `fasta_file_path`:
   - File must exist and be readable
   - File must be valid FASTA format
   - Must contain at least one sequence
   - All sequences must contain only valid amino acids
4. `template` must be one of: "GramNegative", "GramPositive", "Core"
5. If `annotate_with_rast=true`, internet connection required (checked at runtime)

**Validation Behavior**:
- If validation fails, return error before creating any model components
- List ALL invalid protein sequences in error response (don't stop at first)
- Provide clear guidance on fixing validation errors

## Output Specification

### Successful Response

```json
{
  "success": true,
  "model_id": "model_20251027_b4k8c1",
  "model_name": "E_coli_model",
  "num_reactions": 856,
  "num_metabolites": 742,
  "num_genes": 150,
  "num_exchange_reactions": 95,
  "template_used": "GramNegative",
  "has_biomass_reaction": true,
  "biomass_reaction_id": "bio1",
  "compartments": ["c0", "e0", "p0"],
  "has_atpm": true,
  "atpm_reaction_id": "ATPM_c0",
  "statistics": {
    "reactions_by_compartment": {
      "c0": 715,
      "e0": 95,
      "p0": 46
    },
    "metabolites_by_compartment": {
      "c0": 580,
      "e0": 95,
      "p0": 67
    },
    "reversible_reactions": 412,
    "irreversible_reactions": 444,
    "transport_reactions": 78
  },
  "model_properties": {
    "is_draft": true,
    "requires_gapfilling": true,
    "estimated_growth_without_gapfilling": 0.0
  }
}
```

### Output Fields

**success**
- Type: Boolean
- Value: `true` for successful model building
- Always present

**model_id**
- Type: String
- Format: `model_<timestamp>_<random_id>`
- Example: `"model_20251027_b4k8c1"`
- Purpose: Unique identifier for this model
- Used by: gapfill_model, run_fba, future export tools
- Scope: Valid within current server session only
- Lifecycle: Cleared when server restarts

**model_name**
- Type: String
- Value: User-provided name or auto-generated from model_id
- Purpose: Human-readable identifier for logging and display

**num_reactions**
- Type: Integer
- Value: Total count of reactions in the model
- Includes: Metabolic reactions, exchange reactions, biomass reaction, ATPM
- Typical range: 500-1500 for prokaryotic draft models
- Depends on: Template used and number of protein sequences

**num_metabolites**
- Type: Integer
- Value: Total count of unique metabolites across all compartments
- Typical range: 400-1000 for prokaryotes
- Includes: Internal metabolites and boundary metabolites

**num_genes**
- Type: Integer
- Value: Number of genes (protein-coding sequences) in the model
- Equals: Number of protein sequences provided in input
- Purpose: Track genome size

**num_exchange_reactions**
- Type: Integer
- Value: Count of exchange reactions (EX_ prefix)
- Purpose: Exchange reactions enable uptake/secretion of compounds
- Created automatically: For all boundary metabolites in extracellular compartment
- Typical range: 50-150 depending on model complexity

**template_used**
- Type: String
- Value: The template name used for model construction
- One of: "GramNegative", "GramPositive", "Core"
- Purpose: Document model provenance

**has_biomass_reaction**
- Type: Boolean
- Value: Should always be `true` for functional models
- Purpose: Indicates if biomass objective reaction exists
- Biomass reaction: Pseudo-reaction representing cellular growth

**biomass_reaction_id**
- Type: String
- Value: ID of the biomass reaction
- Default: `"bio1"`
- Purpose: Target for FBA optimization
- Used by: run_fba as default objective

**compartments**
- Type: Array of strings
- Values: List of compartment codes in the model
- GramNegative: `["c0", "e0", "p0"]` (cytosol, extracellular, periplasm)
- GramPositive: `["c0", "e0"]` (cytosol, extracellular)
- Core: `["c0", "e0"]`
- Purpose: Document model compartmentalization

**has_atpm**
- Type: Boolean
- Value: Should always be `true` (ATPM added by default)
- Purpose: Indicates ATP maintenance reaction was added

**atpm_reaction_id**
- Type: String
- Value: ID of ATP maintenance reaction
- Default: `"ATPM_c0"`
- Purpose: Models non-growth ATP consumption
- Typical flux: 8.39 mmol/gDW/h (from template)

**statistics**
- Type: Object with breakdown statistics
- **reactions_by_compartment**: Count of reactions per compartment
- **metabolites_by_compartment**: Count of metabolites per compartment
- **reversible_reactions**: Reactions that can run in either direction
- **irreversible_reactions**: Reactions with fixed direction
- **transport_reactions**: Reactions moving compounds between compartments
- Purpose: Provide detailed model composition summary

**model_properties**
- Type: Object with model status flags
- **is_draft**: Always `true` for newly built models
- **requires_gapfilling**: Always `true` (draft models rarely grow without gapfilling)
- **estimated_growth_without_gapfilling**: Typically `0.0` (infeasible)
- Purpose: Set expectations that gapfilling is needed

### Error Responses

**Empty Protein Sequences**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Protein sequences dictionary cannot be empty",
  "details": {
    "num_sequences_provided": 0,
    "minimum_required": 1
  },
  "suggestion": "Provide at least one protein sequence in the protein_sequences dictionary."
}
```

**Invalid Amino Acid Sequences**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid amino acid characters found in protein sequences",
  "details": {
    "invalid_sequences": {
      "protein_001": {
        "invalid_chars": ["X", "*"],
        "positions": [45, 123]
      },
      "protein_003": {
        "invalid_chars": ["B"],
        "positions": [67]
      }
    },
    "valid_alphabet": "ACDEFGHIKLMNPQRSTVWY",
    "num_invalid": 2,
    "num_valid": 1
  },
  "suggestion": "Remove invalid characters or ambiguous amino acid codes. Use standard 20 amino acids only. Stop codons (*) and unknown residues (X, B, Z) are not supported."
}
```

**Invalid Template Name**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid template name specified",
  "details": {
    "provided_template": "GramNegativ",
    "valid_templates": ["GramNegative", "GramPositive", "Core"],
    "did_you_mean": "GramNegative"
  },
  "suggestion": "Choose from valid templates: 'GramNegative' for E. coli-like organisms, 'GramPositive' for Bacillus-like organisms, or 'Core' for central metabolism only."
}
```

**RAST Annotation Failed (Network/API Error)**:
```json
{
  "success": false,
  "error_type": "RASTAnnotationError",
  "message": "RAST annotation request failed",
  "details": {
    "rast_status": "connection_timeout",
    "attempted_url": "https://rast.nmpdr.org/...",
    "error": "Connection timeout after 60 seconds"
  },
  "suggestion": "Check internet connection. Alternatively, retry with 'annotate_with_rast': false for offline mode."
}
```

**Both Inputs Provided**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Cannot provide both protein_sequences and fasta_file_path",
  "details": {
    "provided_inputs": ["protein_sequences", "fasta_file_path"]
  },
  "suggestion": "Choose ONE input method: either 'protein_sequences' (dict) OR 'fasta_file_path' (string path)."
}
```

**Neither Input Provided**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Must provide either protein_sequences or fasta_file_path",
  "details": {
    "provided_inputs": []
  },
  "suggestion": "Provide protein sequences via 'protein_sequences' dict OR 'fasta_file_path' string."
}
```

**Invalid FASTA File**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "FASTA file not found or invalid format",
  "details": {
    "fasta_file_path": "/path/to/missing.faa",
    "error": "File does not exist"
  },
  "suggestion": "Verify file path is correct and file exists. FASTA files should have .faa extension."
}
```

**Template Loading Failure**:
```json
{
  "success": false,
  "error_type": "TemplateLoadError",
  "message": "Failed to load ModelSEED template",
  "details": {
    "template": "GramNegative",
    "template_file": "GramNegModelTemplateV6.json",
    "error": "File not found or corrupted"
  },
  "suggestion": "Ensure ModelSEEDpy is correctly installed. Try reinstalling with 'uv sync'."
}
```

**Model Building Failed**:
```json
{
  "success": false,
  "error_type": "ModelBuildError",
  "message": "Model building process failed",
  "details": {
    "stage": "base_model_construction",
    "error": "MSBuilder.build_base_model() raised exception",
    "exception_type": "ValueError"
  },
  "suggestion": "Check protein sequences for validity. If problem persists, this may be a ModelSEEDpy library issue."
}
```

## Behavioral Specification

### Model Building Process

The model building process follows the ModelSEEDpy workflow from build_model.ipynb:

**Step 1: Validate Input**
1. Verify exactly ONE of `protein_sequences` OR `fasta_file_path` is provided
2. If `protein_sequences`:
   - Verify non-empty dictionary
   - Validate all amino acid sequences contain only valid characters
3. If `fasta_file_path`:
   - Verify file exists and is readable
   - Verify file is valid FASTA format
   - Validate all sequences contain only valid amino acids
4. Verify template name is valid
5. If any validation fails, return error with all issues

**Step 2: Load Template**
1. Load specified template from data/templates/ directory
2. Templates are JSON files:
   - GramNegative: data/templates/GramNegModelTemplateV6.json
   - GramPositive: data/templates/GramPosModelTemplateV6.json
   - Core: data/templates/Core-V5.2.json
3. Parse template into MSTemplate object
4. If template loading fails, return error

**Step 3: Prepare Protein Sequences for RAST (if annotate_with_rast=true)**
1. If `protein_sequences` dict provided:
   - Convert dict to temporary .faa file
   - Format: Standard FASTA with `>protein_id` headers
   - Save to temporary location
2. If `fasta_file_path` provided:
   - Use file directly (already in .faa format)
3. File path is now ready for RAST submission

**Step 4: Create Genome Object**
1. If `annotate_with_rast=true` (default):
   - Submit .faa file to RAST API for functional annotation
   - Wait for RAST annotation results
   - Create MSGenome from RAST-annotated results
   - Use `MSGenome.from_fasta()` with RAST output
   - If RAST fails, return error with suggestion to use offline mode
2. If `annotate_with_rast=false`:
   - Create MSGenome directly from sequences
   - If `protein_sequences`: Use `MSGenome.from_dict()`
   - If `fasta_file_path`: Use `MSGenome.from_fasta()`
   - No annotation, template matching only
3. Protein IDs become gene IDs in the model

**Step 5: Initialize Model Builder**
1. Create MSBuilder instance with:
   - Genome: MSGenome object from step 4
   - Template: MSTemplate object from step 2
   - Model ID: Generated model_id or user-provided model_name
2. MSBuilder will map genome to template reactions

**Step 6: Build Base Model**
1. Call `MSBuilder.build_base_model(model_name, annotate_with_rast=<user_value>)`
2. Template matching process:
   - If RAST annotation used: Map functional annotations to template reactions
   - If offline mode: Basic sequence-based template matching
   - For each protein, find matching reactions in template
   - Add reactions to model based on protein presence
   - Create gene-protein-reaction (GPR) associations
   - Add biomass reaction from template
3. Result: COBRApy Model object with draft network
4. RAST annotation typically results in more accurate reaction mapping

**Step 7: Add ATP Maintenance**
1. Call `MSBuilder.add_atpm(model)`
2. Adds ATPM_c0 reaction: `ATP + H2O → ADP + H+ + Phosphate`
3. Purpose: Model non-growth ATP consumption (maintenance energy)
4. Typical lower bound: 8.39 mmol/gDW/h (from template)

**Step 8: Generate Model ID and Store**
1. Generate unique model_id with state suffix: `model_<timestamp>_<random>.draft`
2. State: `.draft` indicates model is built but not gapfilled
3. Store COBRApy Model object in session: `session.models[model_id] = model`
4. Model available for gapfill_model and run_fba

**Step 9: Collect Statistics**
1. Count reactions, metabolites, genes
2. Break down by compartment
3. Identify exchange reactions (EX_ prefix)
4. Count reversible vs irreversible reactions
5. Identify transport reactions

**Step 10: Cleanup Temporary Files**
1. If dict→.faa conversion was performed, delete temporary file
2. Keep RAST annotation results cached (if applicable)

**Step 11: Return Response**
1. Return success response with model metadata
2. Include all statistics and properties
3. Set flags: is_draft=true, requires_gapfilling=true
4. Include annotation method used (RAST vs offline)

### Template-Based Reconstruction

**How Template Matching Works**:
1. Template contains ~2000 reactions with associated functional annotations
2. Each reaction has optional gene associations (complex rules)
3. MSBuilder compares protein sequences to template annotations
4. When match found, reaction is added to model
5. Gene-protein-reaction (GPR) associations created

**Result of Template Matching**:
- Draft model with 500-1500 reactions (depends on genome size)
- Many biosynthetic pathways may be incomplete
- Model typically cannot grow without gapfilling
- Exchange reactions created automatically for boundary metabolites

**Why Gapfilling is Needed**:
- Template matching is conservative (avoids false positives)
- Some pathways may have missing reactions
- Biomass precursor synthesis may be incomplete
- ATP production pathways may need completion

### ATPM (ATP Maintenance) Reaction

**Purpose**: Model ATP consumption for non-growth processes:
- Protein turnover
- Futile cycles
- Maintaining ion gradients
- General cellular maintenance

**Reaction**: `ATP[c0] + H2O[c0] → ADP[c0] + H+[c0] + Phosphate[c0]`

**Typical Bounds**:
- Lower bound: 8.39 mmol/gDW/h (maintenance requirement)
- Upper bound: 1000.0 mmol/gDW/h (effectively unlimited)

**Impact on FBA**:
- Forces model to produce ATP even at zero growth
- More realistic energy requirements
- Affects growth rate predictions

## Example Usage Scenarios

### Example 1: Build E. coli Model

**User Intent**: "Build a metabolic model for E. coli from my protein sequences"

**AI Assistant Approach**:
1. User has protein sequences file (50-500 sequences typical for draft)
2. E. coli is Gram-negative → use GramNegative template
3. Call build_model:

```json
{
  "protein_sequences": {
    "prot_001": "MKLVINLVGNSGLGKSTFTQRLIN...",
    "prot_002": "MKQHKAMIVALERFRKEKRDAALL...",
    ... // 150 sequences
  },
  "template": "GramNegative",
  "model_name": "E_coli_K12"
}
```

**Response**:
```json
{
  "success": true,
  "model_id": "model_001",
  "model_name": "E_coli_K12",
  "num_reactions": 856,
  "num_metabolites": 742,
  "num_genes": 150,
  "template_used": "GramNegative",
  "has_biomass_reaction": true,
  "biomass_reaction_id": "bio1",
  "compartments": ["c0", "e0", "p0"],
  "model_properties": {
    "is_draft": true,
    "requires_gapfilling": true,
    "estimated_growth_without_gapfilling": 0.0
  }
}
```

**AI Response to User**:
"I've built a draft metabolic model (model_001) for E. coli using the GramNegative template. The model has 856 reactions across 3 compartments (cytosol, extracellular, periplasm) and includes 150 genes from your sequences. This is a draft model that will need gapfilling before it can predict growth. Would you like me to gapfill it for a specific growth medium?"

### Example 2: Build Bacillus Model (Gram-positive)

**User Intent**: "Build a model for Bacillus subtilis"

**AI Assistant Approach**:
1. Bacillus is Gram-positive (no periplasm)
2. Use GramPositive template
3. Call build_model:

```json
{
  "protein_sequences": {
    "BSU_001": "MKKFARMVIGAV...",
    "BSU_002": "MKKLVVVGATGL...",
    ... // 200 sequences
  },
  "template": "GramPositive",
  "model_name": "B_subtilis_168"
}
```

**Response**:
```json
{
  "success": true,
  "model_id": "model_002",
  "model_name": "B_subtilis_168",
  "num_reactions": 723,
  "compartments": ["c0", "e0"],
  "template_used": "GramPositive"
}
```

**AI Response to User**:
"I've built a draft model (model_002) for Bacillus subtilis using the GramPositive template. The model has 723 reactions across 2 compartments (no periplasm for Gram-positive bacteria)."

### Example 3: Build Small Core Model

**User Intent**: "I want to quickly prototype with central metabolism only"

**AI Assistant Approach**:
1. User wants fast model building for prototyping
2. Core template includes only central metabolism (~200 reactions)
3. Much faster than full genome-scale
4. Call build_model:

```json
{
  "protein_sequences": {
    "prot_pfk": "MKLVINLV...",
    "prot_eno": "MKQHKAMI...",
    ... // 20-30 core metabolism proteins
  },
  "template": "Core",
  "model_name": "core_metabolism_test"
}
```

**Response**:
```json
{
  "success": true,
  "model_id": "model_003",
  "model_name": "core_metabolism_test",
  "num_reactions": 95,
  "num_metabolites": 72,
  "template_used": "Core"
}
```

**AI Response to User**:
"I've built a small core metabolism model (model_003) with only 95 reactions. This is much faster for prototyping and focuses on central carbon metabolism (glycolysis, TCA cycle, etc.)."

### Example 4: Build Model from FASTA File

**User Intent**: "Build a model from my FASTA file of protein sequences"

**AI Assistant Approach**:
1. User provides path to FASTA file
2. Use `fasta_file_path` parameter instead of `protein_sequences`
3. RAST annotation enabled by default

**Call build_model**:
```json
{
  "fasta_file_path": "/Users/data/ecoli_proteins.faa",
  "template": "GramNegative",
  "model_name": "E_coli_from_fasta",
  "annotate_with_rast": true
}
```

**Response**:
```json
{
  "success": true,
  "model_id": "E_coli_from_fasta.draft",
  "model_name": "E_coli_from_fasta",
  "num_reactions": 892,
  "num_metabolites": 758,
  "num_genes": 187,
  "template_used": "GramNegative",
  "annotation_method": "RAST",
  "rast_job_id": "12345678",
  "has_biomass_reaction": true
}
```

**AI Response to User**:
"I've built a metabolic model (E_coli_from_fasta.draft) from your FASTA file. The model contains 892 reactions and 758 metabolites based on 187 protein sequences. I used RAST annotation (job ID: 12345678) to improve reaction mapping accuracy. The model is ready for gapfilling."

**FASTA File Example**:
```
>protein_001 putative hexokinase
MKLVINLVGNSGLGKSTFTQRLINSLQIDEDVRKQLAELSALQRGVKVVLTGSKGVTT
SHIAPERDVDLLAKLGVEVTTSGKMTSFVSRAKEKYNEKASQIAKELFPQYLGGVKD
>protein_002 phosphoglycerate kinase
MKQHKAMIVALERFRKEKRDAALLNLVRNPVADAGVIHYVDAKK
>protein_003 pyruvate kinase
MSVALERYGIDEVASIGGLVEVNNQYLNSSNGIIKQLLKKLKEK
```

**Validation**: The tool validates:
1. File exists and is readable
2. Valid FASTA format (headers start with `>`)
3. At least one sequence present
4. All sequences contain only valid amino acids

### Example 5: Handling Invalid Input

**User Attempt** (with invalid amino acids):
```json
{
  "protein_sequences": {
    "prot_001": "MKLVINLX*VGNS",  // Contains X and *
    "prot_002": "MKQHKAMI"
  },
  "template": "GramNegative"
}
```

**Error Response**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid amino acid characters found in protein sequences",
  "details": {
    "invalid_sequences": {
      "prot_001": {
        "invalid_chars": ["X", "*"],
        "positions": [8, 9]
      }
    },
    "valid_alphabet": "ACDEFGHIKLMNPQRSTVWY"
  },
  "suggestion": "Remove invalid characters. Stop codons (*) and unknown residues (X) are not supported."
}
```

**AI Recovery**:
1. Identify the issue: Invalid characters in sequence
2. Ask user to check sequence quality
3. AI: "I found invalid characters (X and * at positions 8-9) in protein_001. These represent unknown amino acids and stop codons. Please provide clean protein sequences with only the 20 standard amino acids."

## Integration with Other Tools

### Used by: gapfill_model

The gapfill_model tool requires a model_id from build_model:

```json
{
  "model_id": "model_001",
  "media_id": "media_001"
}
```

**Workflow**:
1. build_model creates draft model
2. gapfill_model adds missing reactions to enable growth
3. Result: Gapfilled model that can grow in specified media

### Used by: run_fba

The run_fba tool can analyze models (though draft models typically show zero growth):

```json
{
  "model_id": "model_001",
  "media_id": "media_001"
}
```

**Expected Result for Draft Model**:
- Status: "infeasible" (cannot grow)
- Objective value: 0.0
- Suggestion: Use gapfill_model first

### Session Storage

**Storage Pattern**:
```python
# After building model
session.models[model_id] = cobra_model

# Later retrieval
model = session.models.get(model_id)
if model is None:
    return ModelNotFoundError
```

**Memory Considerations**:
- Each COBRApy Model object: ~1-5 MB
- Typical session: 1-10 models
- Total memory: 10-50 MB (acceptable)

**Lifecycle**:
- Created by: build_model
- Modified by: gapfill_model (creates new model_id with .gf suffix)
- Read by: run_fba, future export tools
- Cleared on: Server restart

## Data Flow Diagram

```
Input (protein_sequences, template)
  ↓
Validate amino acid sequences
  ↓
Load ModelSEED template
  ↓
Create MSGenome from sequences
  ↓
Initialize MSBuilder
  ↓
Build base model (template matching)
  ↓
Add ATPM reaction
  ↓
Generate model_id
  ↓
Store COBRApy Model in session
  ↓
Collect statistics
  ↓
Return response (JSON)
```

## ModelSEEDpy Integration

### Library Functions Used

**Option 1: From Dictionary with RAST (default)**:
```python
from modelseedpy import MSGenome, MSBuilder
from modelseedpy.core.mstemplate import MSTemplateBuilder
from modelseedpy.core.rast_client import RastClient
import json
import tempfile

# Step 1: Load template
with open('data/templates/GramNegModelTemplateV6.json') as fh:
    template_dict = json.load(fh)
    template = MSTemplateBuilder.from_dict(template_dict).build()

# Step 2: Convert dict to .faa file if needed
temp_faa = tempfile.NamedTemporaryFile(mode='w', suffix='.faa', delete=False)
for protein_id, sequence in protein_sequences.items():
    temp_faa.write(f'>{protein_id}\n{sequence}\n')
temp_faa.close()

# Step 3: Submit to RAST for annotation
rast_client = RastClient()
annotated_genome = rast_client.annotate(temp_faa.name)

# Step 4: Create genome from RAST results
genome = MSGenome.from_fasta(annotated_genome)

# Step 5: Initialize builder
builder = MSBuilder(genome, template, 'model_name')

# Step 6: Build base model with RAST annotation
model = builder.build_base_model('model_name', annotate_with_rast=True)

# Step 7: Add ATPM
builder.add_atpm(model)

# Result: model is a COBRApy Model object
```

**Option 2: From FASTA File with RAST (default)**:
```python
from modelseedpy import MSGenome, MSBuilder
from modelseedpy.core.mstemplate import MSTemplateBuilder
from modelseedpy.core.rast_client import RastClient
import json

# Step 1: Load template
with open('data/templates/GramNegModelTemplateV6.json') as fh:
    template_dict = json.load(fh)
    template = MSTemplateBuilder.from_dict(template_dict).build()

# Step 2: Submit FASTA to RAST for annotation
rast_client = RastClient()
annotated_genome = rast_client.annotate(fasta_file_path)

# Step 3: Create genome from RAST results
genome = MSGenome.from_fasta(annotated_genome)

# Step 4: Build model with RAST annotation
builder = MSBuilder(genome, template, 'model_name')
model = builder.build_base_model('model_name', annotate_with_rast=True)
builder.add_atpm(model)
```

**Option 3: Offline Mode (annotate_with_rast=false)**:
```python
from modelseedpy import MSGenome, MSBuilder
from modelseedpy.core.mstemplate import MSTemplateBuilder
import json

# Step 1: Load template
with open('data/templates/GramNegModelTemplateV6.json') as fh:
    template_dict = json.load(fh)
    template = MSTemplateBuilder.from_dict(template_dict).build()

# Step 2: Create genome directly (no RAST)
if protein_sequences:
    genome = MSGenome.from_dict(protein_sequences)
elif fasta_file_path:
    genome = MSGenome.from_fasta(fasta_file_path)

# Step 3: Build model without RAST annotation
builder = MSBuilder(genome, template, 'model_name')
model = builder.build_base_model('model_name', annotate_with_rast=False)
builder.add_atpm(model)
```

### Dict to FASTA Conversion Pattern

When user provides `protein_sequences` dict and RAST annotation is requested, convert to .faa file:

```python
import tempfile

def dict_to_faa(protein_sequences: dict[str, str]) -> str:
    """Convert protein sequences dict to FASTA format file.

    Args:
        protein_sequences: Dict mapping protein IDs to sequences

    Returns:
        Path to temporary .faa file
    """
    temp_faa = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.faa',
        delete=False,
        prefix='proteins_'
    )

    for protein_id, sequence in protein_sequences.items():
        # Write FASTA header
        temp_faa.write(f'>{protein_id}\n')

        # Write sequence (can optionally wrap at 80 chars)
        temp_faa.write(f'{sequence}\n')

    temp_faa.close()
    return temp_faa.name

# Usage
faa_path = dict_to_faa(protein_sequences)
# Submit faa_path to RAST...
# Clean up after use:
os.unlink(faa_path)
```

**FASTA Format Details**:
- Header line: `>protein_id optional_description`
- Sequence lines: Amino acid sequence (can be multi-line)
- Standard FASTA conventions (recognized by RAST API)

### Template Structure

Templates are JSON files with:
- **reactions**: List of ~2000 reactions with stoichiometry
- **metabolites**: Compound definitions
- **biomass**: Biomass reaction composition
- **pathways**: Reaction organization
- **complexes**: Protein complexes and gene associations

### Genome Representation

MSGenome stores:
- **features**: List of protein-coding genes
- **id**: Genome identifier
- **name**: Organism name
- **sequences**: Protein sequences

## Template Characteristics

### GramNegative Template
- **Source**: GramNegModelTemplateV6.json
- **Reactions**: ~2000
- **Compartments**: c0 (cytosol), e0 (extracellular), p0 (periplasm)
- **Use for**: E. coli, Salmonella, Shigella, Pseudomonas, etc.
- **Special features**: Periplasmic space, LPS biosynthesis

### GramPositive Template
- **Source**: GramPosModelTemplateV6.json (if available)
- **Reactions**: ~1800
- **Compartments**: c0 (cytosol), e0 (extracellular)
- **Use for**: Bacillus, Staphylococcus, Streptococcus, etc.
- **Special features**: Thick cell wall, no periplasm

### Core Template
- **Source**: Core-V5.2.json
- **Reactions**: ~200
- **Compartments**: c0 (cytosol), e0 (extracellular)
- **Use for**: Fast prototyping, teaching, central metabolism studies
- **Coverage**: Glycolysis, TCA cycle, pentose phosphate pathway, basic biosynthesis

## Performance Considerations

### Expected Performance

**Typical Execution Time**:
- Small genome (50 sequences, Core template): 1-5 seconds
- Medium genome (150 sequences, GramNegative): 10-30 seconds
- Large genome (500+ sequences, GramNegative): 1-2 minutes

**Performance Factors**:
1. Number of protein sequences (linear scaling)
2. Template size (GramNegative > GramPositive > Core)
3. Template matching complexity
4. MSBuilder algorithm performance

**Performance is Acceptable**: Most models build in < 30 seconds, which is reasonable for a one-time operation per organism.

## Quality Requirements

### Correctness
- ✅ All valid protein sequences result in model creation
- ✅ Template reactions correctly added based on sequence matching
- ✅ ATPM reaction always added
- ✅ Biomass reaction present in all models
- ✅ Model stored correctly in session

### Reliability
- ✅ Invalid sequences detected before model building starts
- ✅ Template loading failures handled gracefully
- ✅ MSBuilder exceptions caught and translated to user-friendly errors
- ✅ Partial models never stored (all-or-nothing)

### Usability
- ✅ Clear error messages for validation failures
- ✅ Template selection guidance in errors
- ✅ Model statistics help user understand model composition
- ✅ Draft model warnings set proper expectations

### Performance
- ✅ Small models (< 100 sequences): < 10 seconds
- ✅ Medium models (100-500 sequences): < 30 seconds
- ✅ Large models (> 500 sequences): < 2 minutes

## Testing Considerations

### Test Cases

**Valid Inputs**:
1. Small model (10 sequences, Core template)
2. Medium model (150 sequences, GramNegative)
3. Large model (500 sequences, GramNegative)
4. GramPositive template
5. Custom model name
6. Auto-generated model name

**Invalid Inputs**:
1. Empty protein_sequences
2. Invalid amino acid characters (X, *, B, Z, J)
3. Empty sequences
4. Invalid template name
5. annotate_with_rast=true (not supported)
6. Duplicate protein IDs

**Edge Cases**:
1. Single protein sequence
2. Very long sequences (>5000 amino acids)
3. Very short sequences (< 50 amino acids)
4. Many identical sequences
5. Template loading failure

### Integration Tests

1. Build model → use in gapfill_model
2. Build model → use in run_fba
3. Build multiple models in same session
4. Server restart clears models
5. Build with each template type

## Future Enhancements

### Post-MVP Features (Not in Specification)

**v0.3.0 - RAST Integration**:
- `annotate_with_rast=true` - Submit genome to RAST for annotation
- Better functional predictions
- Improved template matching

**v0.3.0 - Custom Templates**:
- `custom_template_path` - Use user-provided template
- Template creation tools
- Template merging

**v0.4.0 - Model Refinement**:
- `refine_model()` - Improve draft model quality
- Remove dead-end metabolites
- Check mass balance
- Validate stoichiometry

## Related Specifications

- **001-system-overview.md**: Overall architecture and ModelSEED workflow
- **002-data-formats.md**: Protein sequence format and model output format
- **005-gapfill-model-tool.md**: Uses model_id to gapfill draft models
- **006-run-fba-tool.md**: Uses model_id to run flux balance analysis
- **007-database-integration.md**: Template loading and database queries

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 005-gapfill-model-tool.md
