# Data Formats and Structures - Gem-Flux MCP Server

**Type**: Data Format Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding overall architecture and terminology)

## Purpose

This specification defines all data formats and structures used by the Gem-Flux MCP Server. It covers input formats for MCP tools, output formats for responses, internal data representations, and the structure of metabolic models, media, and analysis results.

## Core Design Principles

**JSON as Primary Format**:
- All MCP tool inputs and outputs use JSON
- JSON is human-readable and parseable by LLMs
- Structured data enables validation and type checking
- Compatible with modern tooling and visualization

**ModelSEED Identifier System**:
- Compounds identified by `cpd` prefix: `cpd00001`, `cpd00027`, etc.
- Reactions identified by `rxn` prefix: `rxn00001`, `rxn00148`, etc.
- Compartment suffixes: `_c0` (cytosol), `_e0` (extracellular), `_p0` (periplasm)
- Exchange reactions: `EX_` prefix for uptake/secretion

**Units and Conventions**:
- Flux units: mmol/gDW/h (millimoles per gram dry weight per hour)
- Negative flux = uptake/consumption
- Positive flux = secretion/production
- Growth rate: 1/h (per hour, reciprocal hours)

---

## Protein Sequence Format

### Input Option 1: Dictionary Format

Used by `build_model` tool to provide protein sequences as a JSON dictionary.

```json
{
  "protein_sequences": {
    "protein_001": "MKLVINLVGNSGLGKSTFTQRLIN...",
    "protein_002": "MKQHKAMIVALERFRKEKRDAALL...",
    "protein_003": "MSVALERYGIDEVASIGGLVEVNN..."
  }
}
```

**Field Specifications**:

- **Keys**: Protein identifiers
  - Type: String
  - Format: Any valid JSON string (arbitrary, user-defined)
  - Examples: `"protein_001"`, `"gene_lacZ"`, `"NP_414542.1"`
  - No restrictions on naming convention

- **Values**: Amino acid sequences
  - Type: String
  - Format: Single-letter amino acid code
  - Valid characters: `ACDEFGHIKLMNPQRSTVWY`
  - Invalid characters: `*` (stop codon), `X` (unknown), `B` (Asx), `Z` (Glx), `J` (Xle)
  - Case: Uppercase recommended, but case-insensitive
  - Minimum length: 1 amino acid
  - Maximum length: No hard limit (practical limit ~10,000 for typical proteins)

**Validation Rules**:

1. At least one protein sequence required
2. All sequences must contain only valid amino acids
3. Empty sequences are invalid
4. Duplicate protein IDs are invalid (keys must be unique)

**Example Valid Input**:
```json
{
  "protein_sequences": {
    "prot_hexokinase": "MKLVINLVGNSGLGKSTFTQRLINSLQIDEDVRKQLAELSALQRGVKVVLTGSKGVTT",
    "prot_pgk": "MKQHKAMIVALERFRKEKRDAALLNLVRNPVADAGVIHYVDAKK"
  }
}
```

**Example Invalid Input**:
```json
{
  "protein_sequences": {
    "prot_001": "MKXLINVAL*",  // Invalid: contains 'X' and '*'
    "prot_002": ""             // Invalid: empty sequence
  }
}
```

### Input Option 2: FASTA File Format

Used by `build_model` tool when providing protein sequences as a FASTA file.

```json
{
  "fasta_file_path": "/path/to/proteins.faa"
}
```

**FASTA File Structure**:

```
>protein_001 hexokinase
MKLVINLVGNSGLGKSTFTQRLINSLQIDEDVRKQLAELSALQRGVKVVLTGSKGVTT
SHIAPERDVDLLAKLGVEVTTSGKMTSFVSRAKEKYNEKASQIAKELFPQYLGGVKD
>protein_002 phosphoglycerate kinase
MKQHKAMIVALERFRKEKRDAALLNLVRNPVADAGVIHYVDAKK
>protein_003
MSVALERYGIDEVASIGGLVEVNNQYLNSSNGIIKQLLKKLKEK
```

**FASTA Format Rules**:

- **Header Line**:
  - Starts with `>` character
  - Followed by protein identifier (no spaces)
  - Optional description after first space
  - Example: `>protein_001 hexokinase EC:2.7.1.1`

- **Sequence Lines**:
  - Amino acid sequence (standard 20 amino acids)
  - Can be single line or multi-line
  - Uppercase recommended but case-insensitive
  - No line length requirement (typically 60-80 characters per line)

- **File Extension**:
  - `.faa` - FASTA Amino Acid (recommended)
  - `.fasta` - Generic FASTA (also accepted)

**Validation Rules**:

1. File must exist and be readable
2. File must contain at least one sequence
3. All sequences must have valid amino acid characters: `ACDEFGHIKLMNPQRSTVWY`
4. Header lines must start with `>`
5. No empty sequences allowed
6. Protein IDs (first word after `>`) must be unique

**Example Valid FASTA**:
```
>NP_414542.1 galactose-1-phosphate uridylyltransferase
MKKISAVDDIILKATRQAQKTLKTLGVEVFDDSEVKKLTQLGLRVQFVGP
KLAELIQYQDPTIVHRDIKPSNMLANDGDVAFVLGDGTTTVDVAKQGKVG
>NP_414543.1 UDP-glucose-4-epimerase
MKILVTGGAGYIGSHTVVELLEAGYLPVVIDNFHNAFRGGGAAKLSELQK
KYQVTVGDQRSRDIVKELNIEEEPVTVDYLGKFYPFILKAADDKLDYVNK
```

**Example Invalid FASTA**:
```
>protein_001
MKXLINVAL*   # Invalid: contains 'X' and '*'

>protein_002
                # Invalid: empty sequence
```

### Input Mutually Exclusive

The `build_model` tool accepts **either** `protein_sequences` (dict) **OR** `fasta_file_path` (string), but not both.

**Valid:**
```json
{"protein_sequences": {...}}
```

**Valid:**
```json
{"fasta_file_path": "/path/to/file.faa"}
```

**Invalid:**
```json
{
  "protein_sequences": {...},
  "fasta_file_path": "/path/to/file.faa"
}
```

---

## Media Specification Format

### Input Format (build_media tool)

```json
{
  "compounds": ["cpd00027", "cpd00007", "cpd00001", "cpd00009", "cpd00067"],
  "default_uptake": 100.0,
  "custom_bounds": {
    "cpd00027": (-5, 100),
    "cpd00007": (-10, 100)
  }
}
```

**Field Specifications**:

- **compounds**: List of ModelSEED compound IDs
  - Type: Array of strings
  - Format: Each string matches `cpd\d{5}` pattern
  - Minimum: 1 compound
  - Typical: 10-30 compounds for minimal media, 100+ for rich media
  - Must exist in ModelSEED database

- **default_uptake**: Default uptake bound for all compounds
  - Type: Number (float)
  - Units: mmol/gDW/h
  - Typical value: 100.0 (generous default)
  - Applied to all compounds not in `custom_bounds`
  - Creates bounds: `(-default_uptake, 100.0)` for each compound

- **custom_bounds**: Custom bounds for specific compounds (optional)
  - Type: Object mapping compound IDs to `(lower, upper)` tuples
  - Lower bound: Negative value representing maximum uptake rate
  - Upper bound: Positive value representing maximum secretion rate
  - Example: `"cpd00027": (-5, 100)` means:
    - Maximum glucose uptake: 5 mmol/gDW/h
    - Maximum glucose secretion: 100 mmol/gDW/h

**Bound Conventions**:

```
(-5, 100)  →  Uptake limited to 5 mmol/gDW/h, secretion allowed up to 100
(-10, 0)   →  Uptake only, no secretion allowed
(0, 100)   →  Secretion only, no uptake allowed
(-100, 100)→  Unrestricted bidirectional exchange
```

**Example: Glucose Minimal Media**

```json
{
  "compounds": [
    "cpd00027",  // D-Glucose (carbon source)
    "cpd00007",  // O2 (electron acceptor)
    "cpd00001",  // H2O
    "cpd00009",  // Phosphate
    "cpd00011",  // CO2
    "cpd00013",  // NH3 (nitrogen source)
    "cpd00067",  // H+
    "cpd00099",  // Cl-
    "cpd00149",  // Cobalt
    "cpd00205",  // K+
    "cpd00254",  // Mg2+
    "cpd00971",  // Na+
    "cpd10515",  // Fe2+
    "cpd10516",  // Fe3+
    "cpd00063",  // Ca2+
    "cpd00030",  // Mn2+
    "cpd00034",  // Zn2+
    "cpd00048",  // Sulfate
    "cpd00058",  // Cu2+
    "cpd00244"   // Ni2+
  ],
  "default_uptake": 100.0,
  "custom_bounds": {
    "cpd00027": (-5, 100),   // Limit glucose uptake
    "cpd00007": (-10, 100)   // Aerobic conditions
  }
}
```

### Internal Media Representation (MSMedia)

After processing by `build_media`, media is stored internally with compartment suffixes:

```json
{
  "cpd00027_e0": (-5, 100),
  "cpd00007_e0": (-10, 100),
  "cpd00001_e0": (-100, 100),
  "cpd00009_e0": (-100, 100)
  // ... all compounds with _e0 suffix
}
```

**Compartment Suffixes**:
- `_e0`: Extracellular compartment (all media compounds)
- `_c0`: Cytosolic compartment (intracellular)
- `_p0`: Periplasmic compartment (Gram-negative bacteria only)

### Media Output Format (build_media response)

```json
{
  "success": true,
  "media_id": "media_20251027_a3f9b2",
  "compounds": [
    {
      "id": "cpd00027",
      "name": "D-Glucose",
      "formula": "C6H12O6",
      "bounds": [-5, 100]
    },
    {
      "id": "cpd00007",
      "name": "O2",
      "formula": "O2",
      "bounds": [-10, 100]
    }
    // ... all compounds with names
  ],
  "num_compounds": 20,
  "media_type": "minimal"  // or "rich" (heuristic: <50 compounds = minimal)
}
```

**Field Descriptions**:

- **media_id**: Unique identifier for this media composition
  - Format: `media_<timestamp>_<random>`
  - Used by `gapfill_model` and `run_fba` tools
  - Valid only for current server session

- **compounds**: Array of compound objects with metadata
  - Each entry includes ID, human-readable name, formula, and bounds
  - Names retrieved from ModelSEED database
  - Enables LLM to understand media composition

- **num_compounds**: Total number of compounds in media
  - Useful for quick assessment of media complexity

- **media_type**: Classification heuristic
  - "minimal": < 50 compounds (defined media)
  - "rich": ≥ 50 compounds (complex media like LB)

---

## Model ID Format and States

### Model ID Structure

All models are identified by a unique ID with the following format:

```
<base_name>.<state_suffix>
```

Where:
- **base_name**: Either auto-generated (`model_<timestamp>_<random>`) or user-provided
- **state_suffix**: Indicates the model's processing state

### State Suffixes

**`.draft`** - Draft Model (Not Gapfilled)
- Model built from template matching
- Has not undergone gapfilling
- Typically cannot predict growth (infeasible)
- Created by: `build_model` tool
- Example: `model_20251027_a1b2c3.draft`

**`.gf`** - Gapfilled Model
- Model has been gapfilled
- Source model was already gapfilled
- Created by gapfilling an already-gapfilled model
- Created by: `gapfill_model` when input has `.gf` or `.draft.gf` suffix
- Example: `model_20251027_a1b2c3.gf`

**`.draft.gf`** - Draft → Gapfilled Model
- Model was initially built as draft
- Then underwent gapfilling
- Most common workflow path
- Created by: `gapfill_model` when input has `.draft` suffix
- Example: `model_20251027_a1b2c3.draft.gf`

### State Transitions

```
build_model → model.draft
              ↓
          gapfill_model
              ↓
          model.draft.gf
              ↓
          gapfill_model (again)
              ↓
          model.draft.gf.gf (appends .gf)
```

### ID Generation Algorithm

**Auto-Generated IDs**:
```python
import time
import random
import string

def generate_model_id(state: str = "draft") -> str:
    """Generate unique model ID.

    Args:
        state: Model state ("draft", "gf", "draft.gf")

    Returns:
        Model ID like "model_20251027_123456_a1b2c3.draft"
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"model_{timestamp}_{random_id}.{state}"

# Examples:
# "model_20251027_143052_x7k9m2.draft"
# "model_20251027_150312_b4n8p1.draft.gf"
```

**User-Provided Names**:
```python
def generate_model_id_from_name(model_name: str, state: str = "draft", existing_ids: set = None) -> str:
    """Generate model ID from user-provided name.

    Args:
        model_name: User-provided name (e.g., "E_coli_K12")
        state: Model state ("draft", "gf", "draft.gf")
        existing_ids: Set of existing model IDs to check for collisions

    Returns:
        Model ID with state suffix
    """
    base_id = f"{model_name}.{state}"

    # Check for collision
    if existing_ids and base_id in existing_ids:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base_id = f"{model_name}_{timestamp}.{state}"

    return base_id

# Examples:
# "E_coli_K12.draft"
# "E_coli_K12_20251027_143052.draft"  # (collision avoided)
# "B_subtilis_168.draft.gf"
```

### State Suffix Updates During Gapfilling

When `gapfill_model` creates a new model:

1. **Input has `.draft` suffix**:
   - Output: Replace `.draft` with `.draft.gf`
   - Example: `model_abc.draft` → `model_abc.draft.gf`

2. **Input has `.gf` suffix**:
   - Output: Append `.gf` (becomes `.gf.gf`)
   - Example: `model_abc.gf` → `model_abc.gf.gf`

3. **Input has `.draft.gf` suffix**:
   - Output: Append `.gf` (becomes `.draft.gf.gf`)
   - Example: `model_abc.draft.gf` → `model_abc.draft.gf.gf`

This allows tracking the full history of gapfilling operations.

### Model ID Examples

**Typical Workflow**:
```json
{
  "step": "build_model",
  "output_model_id": "model_20251027_143052_x7k9m2.draft"
}

{
  "step": "gapfill_model",
  "input_model_id": "model_20251027_143052_x7k9m2.draft",
  "output_model_id": "model_20251027_143052_x7k9m2.draft.gf"
}

{
  "step": "run_fba",
  "model_id": "model_20251027_143052_x7k9m2.draft.gf",
  "growth_rate": 0.874
}
```

**User-Named Workflow**:
```json
{
  "step": "build_model",
  "model_name": "E_coli_MG1655",
  "output_model_id": "E_coli_MG1655.draft"
}

{
  "step": "gapfill_model",
  "input_model_id": "E_coli_MG1655.draft",
  "output_model_id": "E_coli_MG1655.draft.gf"
}
```

---

## Media ID Format

### Media ID Structure

All media (growth media compositions) are identified by a unique ID with the following format:

```
media_<timestamp>_<random>
```

Where:
- **Prefix**: `media_` (identifies as media, not model)
- **Timestamp**: `YYYYMMDD_HHMMSS` format using server local time
- **Random suffix**: 6 alphanumeric characters (lowercase letters and digits)

### Media ID Examples

**Auto-Generated Media IDs**:
```
media_20251027_143052_x1y2z3  # Created at 2025-10-27 14:30:52
media_20251027_150312_p9q8r7  # Created at 2025-10-27 15:03:12
media_20251027_161045_a4b8c2  # Created at 2025-10-27 16:10:45
```

**Predefined Media IDs** (from media library):
```
glucose_minimal_aerobic       # Named media (no timestamp)
glucose_minimal_anaerobic     # Named media (no timestamp)
pyruvate_minimal_aerobic      # Named media (no timestamp)
pyruvate_minimal_anaerobic    # Named media (no timestamp)
```

### Media ID Generation Algorithm

**Auto-Generated Media**:
```python
import time
import random
import string

def generate_media_id() -> str:
    """Generate unique media ID.

    Returns:
        Media ID like "media_20251027_143052_x7k9m2"
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")  # Local time
    random_suffix = ''.join(
        random.choices(string.ascii_lowercase + string.digits, k=6)
    )
    return f"media_{timestamp}_{random_suffix}"

# Examples:
# generate_media_id() → "media_20251027_143052_x7k9m2"
# generate_media_id() → "media_20251027_150312_b4n8p1"
```

**Predefined Media**:
- Media from library use human-readable names
- No timestamp or random suffix
- Examples: `glucose_minimal_aerobic`, `pyruvate_minimal_anaerobic`
- See 019-predefined-media-library.md for complete list

### Media ID Characteristics

**Format Properties**:
- Length: 29-35 characters (auto-generated), varies (predefined)
- Characters: Alphanumeric with underscores
- Sortable: Timestamp prefix enables chronological sorting (auto-generated)
- Unique: Random suffix prevents collisions
- No state suffixes: Media doesn't have states (unlike models)

**Lifecycle**:
- Created by: `build_media` tool (auto-generated)
- Loaded from: Media library (predefined)
- Used by: `gapfill_model`, `run_fba` tools
- Session scope: Cleared on server restart (MVP)
- Future: Persistent storage (v0.2.0+)

### Media ID vs Model ID Comparison

| Aspect | Model ID | Media ID |
|--------|----------|----------|
| **Format** | `model_<timestamp>_<random>.<state>` | `media_<timestamp>_<random>` |
| **State suffixes** | Yes (`.draft`, `.gf`, `.draft.gf`) | No |
| **Predefined** | No | Yes (4 predefined media) |
| **Naming** | User can provide custom names | Predefined have fixed names |
| **Lifecycle** | Created → Modified (gapfilled) | Created once, immutable |

---

## Model Data Format

### Model Build Output (build_model response)

```json
{
  "success": true,
  "model_id": "model_20251027_b4k8c1.draft",
  "num_reactions": 856,
  "num_metabolites": 742,
  "num_genes": 150,
  "num_exchange_reactions": 95,
  "template_used": "GramNegative",
  "has_biomass_reaction": true,
  "biomass_reaction_id": "bio1",
  "compartments": ["c0", "e0", "p0"],
  "statistics": {
    "reactions_by_compartment": {
      "c0": 715,
      "e0": 95,
      "p0": 46
    },
    "reversible_reactions": 412,
    "irreversible_reactions": 444
  }
}
```

**Field Descriptions**:

- **model_id**: Unique identifier for the model with state suffix
  - Format: `model_<timestamp>_<random>.<state>`
  - State suffixes:
    - `.draft` - Model built but not gapfilled
    - `.gf` - Model gapfilled from existing gapfilled model
    - `.draft.gf` - Model built as draft then gapfilled
  - Examples:
    - `model_20251027_b4k8c1.draft` - Newly built draft model
    - `model_20251027_b4k8c1.draft.gf` - Draft model after gapfilling
    - `model_20251027_x7z9a2.gf` - Gapfilled model (source was already gapfilled)
  - Used by subsequent operations (gapfill, FBA)
  - Session-scoped (cleared on server restart)
  - User naming: If user provides custom `model_name`, use as base instead of timestamp
  - Collision handling: If name exists, append `_<timestamp>` before state suffix

- **num_reactions**: Total number of reactions in model
  - Includes metabolic reactions, exchange reactions, biomass
  - Typical range: 500-1500 for prokaryotes

- **num_metabolites**: Total number of unique metabolites
  - Across all compartments
  - Typical range: 400-1000 for prokaryotes

- **num_genes**: Number of genes (protein-coding sequences)
  - Equals number of protein sequences provided
  - Typical range: 50-5000

- **num_exchange_reactions**: Count of EX_ reactions
  - Enable uptake/secretion of compounds
  - Created automatically for boundary metabolites

- **template_used**: Which template was used for model construction
  - Values: "GramNegative", "GramPositive", "Core"
  - Determines reaction set and compartment structure

- **has_biomass_reaction**: Whether biomass reaction exists
  - Should always be `true` for functional models
  - Biomass reaction is the growth objective

- **biomass_reaction_id**: ID of the biomass reaction
  - Default: "bio1"
  - Target for FBA optimization

- **compartments**: List of compartments in model
  - GramNegative: ["c0", "e0", "p0"]
  - GramPositive: ["c0", "e0"]
  - Core: ["c0", "e0"]

### Model Gapfill Output (gapfill_model response)

```json
{
  "success": true,
  "model_id": "model_20251027_b4k8c1.gf",
  "original_model_id": "model_20251027_b4k8c1",
  "reactions_added": [
    {
      "id": "rxn05459_c0",
      "name": "fumarate reductase",
      "equation": "(1) Fumarate[c0] + (1) NADH[c0] => (1) Succinate[c0] + (1) NAD[c0]",
      "direction": "forward",
      "bounds": [0, 1000]
    },
    {
      "id": "rxn05481_c0",
      "name": "malate dehydrogenase",
      "equation": "(1) Malate[c0] + (1) NAD[c0] => (1) Oxaloacetate[c0] + (1) NADH[c0]",
      "direction": "reverse",
      "bounds": [-1000, 0]
    }
  ],
  "num_reactions_added": 5,
  "growth_rate_before": 0.0,
  "growth_rate_after": 0.874,
  "media_id": "media_20251027_a3f9b2",
  "gapfill_statistics": {
    "atp_gapfill": {
      "media_tested": 27,
      "media_feasible": 27,
      "reactions_added": 0
    },
    "genome_gapfill": {
      "reactions_added": 5,
      "reactions_reversed": 0
    }
  }
}
```

**Field Descriptions**:

- **model_id**: New model ID for gapfilled model
  - Format: `<original_model_id>.gf`
  - Original model preserved (not modified)

- **original_model_id**: Reference to pre-gapfill model
  - Allows comparison before/after gapfilling

- **reactions_added**: Array of reactions added during gapfilling
  - Each entry includes ID, name, equation, direction, bounds
  - Names and equations from ModelSEED database
  - Direction: "forward" (>), "reverse" (<), "reversible" (=)

- **growth_rate_before**: FBA objective before gapfilling
  - Typically 0.0 (infeasible) for draft models
  - Units: 1/h (per hour)

- **growth_rate_after**: FBA objective after gapfilling
  - Should be > 0 if gapfilling succeeded
  - Typical values: 0.1 - 2.0 hr⁻¹ for bacteria

- **gapfill_statistics**: Breakdown of gapfilling stages
  - **atp_gapfill**: ATP metabolism correction phase
    - Tests model against multiple media conditions
    - Ensures ATP production pathways are functional
  - **genome_gapfill**: Genome-scale gapfilling phase
    - Adds reactions for target media and growth rate
    - Minimizes number of reactions added

**Gapfilling Failure Response**:

```json
{
  "success": false,
  "error_type": "InfeasibleGapfillError",
  "message": "Cannot find reactions to enable growth in specified media",
  "details": {
    "model_id": "model_001",
    "media_id": "media_001",
    "target_growth": 0.01,
    "attempts": 1
  },
  "suggestion": "Try a richer media composition or lower the target growth rate"
}
```

---

## FBA Results Format

### Successful FBA Response (run_fba)

```json
{
  "success": true,
  "model_id": "model_20251027_b4k8c1.gf",
  "media_id": "media_20251027_a3f9b2",
  "objective_value": 0.874,
  "objective_reaction": "bio1",
  "status": "optimal",
  "active_reactions": 423,
  "total_flux": 2841.5,
  "fluxes": {
    "bio1": 0.874,
    "EX_cpd00027_e0": -5.0,
    "EX_cpd00007_e0": -10.234,
    "EX_cpd00011_e0": 8.456,
    "rxn00148_c0": 5.0,
    "rxn00200_c0": 4.123
    // ... only reactions with |flux| > 1e-6
  },
  "uptake_fluxes": {
    "cpd00027": {
      "name": "D-Glucose",
      "flux": -5.0,
      "reaction": "EX_cpd00027_e0"
    },
    "cpd00007": {
      "name": "O2",
      "flux": -10.234,
      "reaction": "EX_cpd00007_e0"
    }
  },
  "secretion_fluxes": {
    "cpd00011": {
      "name": "CO2",
      "flux": 8.456,
      "reaction": "EX_cpd00011_e0"
    }
  },
  "summary": {
    "uptake_reactions": 15,
    "secretion_reactions": 8,
    "internal_reactions": 400
  }
}
```

**Field Descriptions**:

- **objective_value**: Value of objective function at optimum
  - Units: 1/h for biomass objective
  - Represents predicted growth rate
  - Typical values: 0.1 - 2.0 hr⁻¹ for prokaryotes

- **status**: Solver status
  - `"optimal"`: Solution found successfully
  - `"infeasible"`: No feasible solution (model cannot grow)
  - `"unbounded"`: Objective can grow infinitely (model error)

- **active_reactions**: Count of reactions with non-zero flux
  - Reactions with |flux| > 1e-6 threshold
  - Typical: 30-50% of total reactions

- **total_flux**: Sum of absolute values of all fluxes
  - Measure of total metabolic activity
  - Units: mmol/gDW/h

- **fluxes**: Dictionary of reaction IDs to flux values
  - Only includes significant fluxes (|flux| > 1e-6)
  - Negative = reverse direction
  - Positive = forward direction

- **uptake_fluxes**: Human-readable uptake summary
  - Only exchange reactions with negative flux
  - Includes compound names from database

- **secretion_fluxes**: Human-readable secretion summary
  - Only exchange reactions with positive flux
  - Includes compound names from database

### Infeasible FBA Response

```json
{
  "success": false,
  "model_id": "model_001",
  "media_id": "media_001",
  "objective_value": null,
  "status": "infeasible",
  "error_type": "InfeasibleModelError",
  "message": "Model has no feasible solution in the specified media",
  "suggestion": "Model may need gapfilling. Use gapfill_model tool first.",
  "diagnostics": {
    "biomass_reaction": "bio1",
    "num_constraints": 1598,
    "num_variables": 1712
  }
}
```

### Unbounded FBA Response

```json
{
  "success": false,
  "model_id": "model_001",
  "media_id": "media_001",
  "objective_value": null,
  "status": "unbounded",
  "error_type": "UnboundedModelError",
  "message": "Model objective is unbounded (can grow infinitely)",
  "suggestion": "Check for missing bounds on exchange reactions or model error",
  "diagnostics": {
    "unbounded_reactions": ["EX_cpd00001_e0", "EX_cpd00067_e0"]
  }
}
```

---

## ModelSEED Database Formats

### Compound Lookup Response (get_compound_name)

```json
{
  "success": true,
  "id": "cpd00027",
  "name": "D-Glucose",
  "abbreviation": "glc__D",
  "formula": "C6H12O6",
  "mass": 180.156,
  "charge": 0,
  "inchikey": "WQZGKKKJIJFFOK-GASJEMHNSA-N",
  "aliases": [
    "glucose",
    "Glc",
    "dextrose",
    "grape sugar",
    "D-glucose"
  ],
  "external_ids": {
    "KEGG": ["C00031"],
    "BiGG": ["glc__D"],
    "MetaCyc": ["GLC"],
    "ChEBI": ["CHEBI:17634"]
  }
}
```

**Field Descriptions**:

- **name**: Primary human-readable name
- **abbreviation**: Short code used in models
- **formula**: Molecular formula
- **mass**: Molecular mass in g/mol
- **charge**: Net ionic charge
- **inchikey**: Standard structure identifier
- **aliases**: Alternative names and synonyms
- **external_ids**: Cross-references to other databases

### Compound Not Found Response

```json
{
  "success": false,
  "error_type": "CompoundNotFoundError",
  "message": "Compound 'cpd99999' not found in ModelSEED database",
  "compound_id": "cpd99999",
  "suggestion": "Use search_compounds tool to find valid compound IDs"
}
```

### Compound Search Response (search_compounds)

```json
{
  "success": true,
  "query": "glucose",
  "num_results": 15,
  "results": [
    {
      "id": "cpd00027",
      "name": "D-Glucose",
      "formula": "C6H12O6",
      "match_type": "name",
      "relevance_score": 1.0
    },
    {
      "id": "cpd00221",
      "name": "D-Glucose 6-phosphate",
      "formula": "C6H13O9P",
      "match_type": "name",
      "relevance_score": 0.85
    },
    {
      "id": "cpd00094",
      "name": "D-Glucose 1-phosphate",
      "formula": "C6H13O9P",
      "match_type": "alias",
      "relevance_score": 0.75
    }
    // ... up to limit (default 10)
  ]
}
```

**Search Behavior**:
- Case-insensitive matching
- Searches name, abbreviation, and aliases fields
- Partial matching allowed (e.g., "gluc" matches "glucose")
- Results sorted by relevance score
- Default limit: 10 results, max: 100

### Reaction Lookup Response (get_reaction_name)

```json
{
  "success": true,
  "id": "rxn00148",
  "name": "hexokinase",
  "abbreviation": "HEX1",
  "equation": "D-Glucose + ATP => ADP + H+ + D-Glucose 6-phosphate",
  "equation_with_ids": "(1) cpd00027[c0] + (1) cpd00002[c0] => (1) cpd00008[c0] + (1) cpd00067[c0] + (1) cpd00079[c0]",
  "reversibility": "irreversible_forward",
  "direction_symbol": ">",
  "ec_numbers": ["2.7.1.1"],
  "pathways": ["Glycolysis", "Central Metabolism"],
  "is_transport": false,
  "external_ids": {
    "KEGG": ["R00200"],
    "BiGG": ["HEX1"],
    "MetaCyc": ["GLUCOKIN-RXN"]
  }
}
```

**Reversibility Values**:
- `"irreversible_forward"`: Direction symbol `>` (left to right only)
- `"irreversible_reverse"`: Direction symbol `<` (right to left only)
- `"reversible"`: Direction symbol `=` (bidirectional)

### Reaction Search Response (search_reactions)

```json
{
  "success": true,
  "query": "hexokinase",
  "num_results": 3,
  "results": [
    {
      "id": "rxn00148",
      "name": "hexokinase",
      "equation": "D-Glucose + ATP => ADP + H+ + D-Glucose 6-phosphate",
      "ec_numbers": ["2.7.1.1"],
      "match_type": "name",
      "relevance_score": 1.0
    },
    {
      "id": "rxn01100",
      "name": "glucokinase",
      "equation": "D-Glucose + ATP => ADP + D-Glucose 6-phosphate",
      "ec_numbers": ["2.7.1.2"],
      "match_type": "alias",
      "relevance_score": 0.7
    }
  ]
}
```

---

## Model Representation Formats

### COBRApy JSON Format (Internal/Export)

The Gem-Flux server uses COBRApy's native JSON format for model storage and future import/export.

**Structure Overview**:
```json
{
  "id": "model_ecoli_001",
  "name": "Escherichia coli K-12 MG1655",
  "version": "1.0",
  "reactions": [ ... ],
  "metabolites": [ ... ],
  "genes": [ ... ],
  "compartments": { ... }
}
```

**Reaction Entry**:
```json
{
  "id": "rxn00148_c0",
  "name": "hexokinase",
  "metabolites": {
    "cpd00027_c0": -1.0,
    "cpd00002_c0": -1.0,
    "cpd00008_c0": 1.0,
    "cpd00067_c0": 1.0,
    "cpd00079_c0": 1.0
  },
  "lower_bound": 0.0,
  "upper_bound": 1000.0,
  "gene_reaction_rule": "protein_001",
  "subsystem": "Glycolysis"
}
```

**Metabolite Entry**:
```json
{
  "id": "cpd00027_c0",
  "name": "D-Glucose",
  "compartment": "c0",
  "formula": "C6H12O6",
  "charge": 0
}
```

**Gene Entry**:
```json
{
  "id": "protein_001",
  "name": "Hexokinase protein"
}
```

**Format Characteristics**:
- ✅ Human-readable text format
- ✅ Version control friendly (line-by-line diffs)
- ✅ Compatible with Escher visualization
- ✅ Native COBRApy format (no conversion needed)
- ✅ Preserves all model metadata
- ⚠️ Larger file sizes than SBML
- ⚠️ COBRApy-specific (not universal standard)

---

## Exchange Reaction Format

### Naming Convention

```
EX_<compound_id>_<compartment>
```

**Examples**:
- `EX_cpd00027_e0` - Glucose exchange
- `EX_cpd00007_e0` - Oxygen exchange
- `EX_cpd00011_e0` - CO2 exchange

### Exchange Reaction Bounds

```json
{
  "id": "EX_cpd00027_e0",
  "name": "D-Glucose exchange",
  "metabolites": {
    "cpd00027_e0": -1.0
  },
  "lower_bound": -5.0,    // Maximum uptake: 5 mmol/gDW/h
  "upper_bound": 100.0    // Maximum secretion: 100 mmol/gDW/h
}
```

**Interpretation**:
- Negative flux → Compound is consumed (uptake)
- Positive flux → Compound is produced (secretion)
- Lower bound controls maximum uptake
- Upper bound controls maximum secretion

**Common Patterns**:

```python
# Glucose uptake only (no secretion)
"lower_bound": -5.0,
"upper_bound": 0.0

# CO2 secretion only (no uptake)
"lower_bound": 0.0,
"upper_bound": 100.0

# Bidirectional (both uptake and secretion allowed)
"lower_bound": -10.0,
"upper_bound": 100.0

# Blocked (no exchange)
"lower_bound": 0.0,
"upper_bound": 0.0
```

---

## Compartment Notation

### Standard Compartments

| Code | Name | Description |
|------|------|-------------|
| `c0` | Cytosol | Intracellular fluid |
| `e0` | Extracellular | Outside the cell |
| `p0` | Periplasm | Gram-negative space between membranes |

### Compartment Suffix Format

All metabolites and reactions have compartment suffixes:

**Metabolites**:
- `cpd00027_c0` - D-Glucose in cytosol
- `cpd00027_e0` - D-Glucose in extracellular space
- `cpd00027_p0` - D-Glucose in periplasm

**Reactions**:
- `rxn00148_c0` - Hexokinase in cytosol
- `rxn05305_p0` - Periplasmic reaction

**Transport Reactions**:
- Move compounds between compartments
- Example: `cpd00027_e0 → cpd00027_c0` (glucose transport into cell)

---

## Error Response Format

### Standard Error Structure

All tools return errors in a consistent format:

```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Human-readable error description",
  "details": {
    // Context-specific error details
  },
  "suggestion": "Actionable suggestion for recovery"
}
```

### Error Types

**ValidationError**: Invalid input data
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid compound IDs: cpd99999, cpd88888",
  "details": {
    "invalid_ids": ["cpd99999", "cpd88888"],
    "field": "compounds"
  },
  "suggestion": "Check compound IDs against ModelSEED database using search_compounds()"
}
```

**InfeasibleGapfillError**: Gapfilling cannot find solution
```json
{
  "success": false,
  "error_type": "InfeasibleGapfillError",
  "message": "Cannot find reactions to enable growth in specified media",
  "details": {
    "model_id": "model_001",
    "media_id": "media_001",
    "target_growth": 0.01
  },
  "suggestion": "Try a richer media or lower target growth rate"
}
```

**InfeasibleModelError**: FBA has no solution
```json
{
  "success": false,
  "error_type": "InfeasibleModelError",
  "message": "Model has no feasible solution in the specified media",
  "details": {
    "model_id": "model_001",
    "media_id": "media_001"
  },
  "suggestion": "Model may need gapfilling. Use gapfill_model tool first."
}
```

**CompoundNotFoundError**: Compound ID not in database
```json
{
  "success": false,
  "error_type": "CompoundNotFoundError",
  "message": "Compound 'cpd99999' not found in ModelSEED database",
  "details": {
    "compound_id": "cpd99999"
  },
  "suggestion": "Use search_compounds tool to find valid compound IDs"
}
```

**ReactionNotFoundError**: Reaction ID not in database
```json
{
  "success": false,
  "error_type": "ReactionNotFoundError",
  "message": "Reaction 'rxn99999' not found in ModelSEED database",
  "details": {
    "reaction_id": "rxn99999"
  },
  "suggestion": "Use search_reactions tool to find valid reaction IDs"
}
```

**ModelNotFoundError**: Model ID not in session
```json
{
  "success": false,
  "error_type": "ModelNotFoundError",
  "message": "Model 'model_001' not found in current session",
  "details": {
    "model_id": "model_001",
    "available_models": ["model_002", "model_003"]
  },
  "suggestion": "Use build_model to create a new model or check model_id"
}
```

---

## Data Validation Rules

### Compound ID Validation

**Format**: `cpd\d{5}`
**Examples**: `cpd00001`, `cpd00027`, `cpd11574`

**Validation Steps**:
1. Check format matches regex: `^cpd\d{5}$`
2. Check ID exists in ModelSEED database
3. Return error with suggestions if invalid

### Reaction ID Validation

**Format**: `rxn\d{5}`
**Examples**: `rxn00001`, `rxn00148`, `rxn05459`

**Validation Steps**:
1. Check format matches regex: `^rxn\d{5}$`
2. Check ID exists in ModelSEED database
3. Return error with suggestions if invalid

### Model ID Validation

**Format**: `model_<timestamp>_<random>`
**Examples**: `model_20251027_a3f9b2`, `model_20251027_b4k8c1.gf`

**Validation Steps**:
1. Check ID exists in current session storage
2. Return error with list of available models if not found

### Media ID Validation

**Format**: `media_<timestamp>_<random>`
**Examples**: `media_20251027_a3f9b2`

**Validation Steps**:
1. Check ID exists in current session storage
2. Return error with list of available media if not found

### Bounds Validation

**Format**: `(lower, upper)` where `lower < upper`
**Units**: mmol/gDW/h

**Rules**:
1. Lower bound must be ≤ 0 (uptake)
2. Upper bound must be ≥ 0 (secretion)
3. Lower bound < Upper bound
4. Typical ranges: -1000 to +1000

**Invalid Examples**:
```json
(5, -10)     // Lower > Upper
(10, 5)      // Both positive but lower > upper
```

**Valid Examples**:
```json
(-10, 100)   // Standard bidirectional
(0, 100)     // Secretion only
(-10, 0)     // Uptake only
```

---

## Units and Conventions Summary

### Flux Units
- **Standard**: mmol/gDW/h (millimoles per gram dry weight per hour)
- **Direction**: Negative = uptake/consumption, Positive = secretion/production

### Growth Rate Units
- **Standard**: hr⁻¹ (per hour, reciprocal hours)
- **Typical Range**: 0.1 - 2.0 hr⁻¹ for bacteria

### Mass Units
- **Molecular mass**: g/mol or Da (Daltons)

### Concentration Units
- **Not used in FBA**: FBA uses flux rates, not concentrations

### Time Convention
- **Standard**: hours (hr or h)

---

## Future Format Extensions

### SBML Export (v0.2.0)

COBRApy can export to SBML (Systems Biology Markup Language):
- Standard format for metabolic models
- Compatible with MATLAB COBRA, KBase, etc.
- XML-based format
- Larger files than JSON

### YAML Format (Future)

Alternative human-readable format:
- More compact than JSON
- Better for version control
- Native COBRApy support

### MATLAB MAT Format (Future)

For compatibility with MATLAB COBRA Toolbox:
- Binary format
- Requires scipy
- Used by legacy tools

---

## Example Complete Workflow Data Flow

### Step 1: Build Media

**Input**:
```json
{
  "compounds": ["cpd00027", "cpd00007", "cpd00001"],
  "default_uptake": 100.0,
  "custom_bounds": {"cpd00027": (-5, 100)}
}
```

**Output**:
```json
{
  "success": true,
  "media_id": "media_001",
  "num_compounds": 3
}
```

### Step 2: Build Model

**Input**:
```json
{
  "protein_sequences": {
    "prot1": "MKLVINLV...",
    "prot2": "MKQHKAMI..."
  },
  "template": "GramNegative"
}
```

**Output**:
```json
{
  "success": true,
  "model_id": "model_001",
  "num_reactions": 856
}
```

### Step 3: Gapfill Model

**Input**:
```json
{
  "model_id": "model_001",
  "media_id": "media_001"
}
```

**Output**:
```json
{
  "success": true,
  "model_id": "model_001.gf",
  "num_reactions_added": 5,
  "growth_rate_after": 0.874
}
```

### Step 4: Run FBA

**Input**:
```json
{
  "model_id": "model_001.gf",
  "media_id": "media_001"
}
```

**Output**:
```json
{
  "success": true,
  "objective_value": 0.874,
  "status": "optimal",
  "fluxes": { ... }
}
```

---

## Related Specifications

- **001-system-overview.md**: Overall architecture and terminology
- **003-build-media-tool.md**: Detailed build_media tool specification
- **004-build-model-tool.md**: Detailed build_model tool specification
- **005-gapfill-model-tool.md**: Detailed gapfill_model tool specification
- **006-run-fba-tool.md**: Detailed run_fba tool specification
- **007-database-integration.md**: ModelSEED database loading and indexing
- **008-compound-lookup-tools.md**: Compound name lookup specifications
- **009-reaction-lookup-tools.md**: Reaction name lookup specifications

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 003-build-media-tool.md
