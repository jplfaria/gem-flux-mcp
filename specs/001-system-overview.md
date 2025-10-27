# System Overview - Gem-Flux MCP Server

**Type**: Architecture Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Purpose

The Gem-Flux MCP Server is a Model Context Protocol (MCP) server that provides AI assistants and metabolic engineers with tools for building, gapfilling, and analyzing genome-scale metabolic models. It serves as an integration layer between powerful metabolic modeling libraries (ModelSEEDpy and COBRApy) and AI-assisted workflows.

## Core Philosophy

**This is a tool integration server, not an AI reasoning system.**

The server exposes metabolic modeling capabilities through well-defined MCP tools that:
- Accept structured inputs (protein sequences, compound IDs, model configurations)
- Invoke ModelSEEDpy and COBRApy library functions
- Return structured outputs (model metadata, flux distributions, database lookups)
- Enable AI assistants to reason about metabolic pathways using human-readable names

**What this IS:**
- ✅ MCP server exposing metabolic modeling tools
- ✅ Integration layer for ModelSEEDpy and COBRApy
- ✅ ModelSEED database interface for compound/reaction lookups
- ✅ Tool server for AI-assisted metabolic engineering

**What this is NOT:**
- ❌ A multi-agent AI research system
- ❌ A hypothesis generation system
- ❌ An LLM-based reasoning engine
- ❌ A workflow orchestration system

## System Scope

### MVP Capabilities (v0.1.0)

The minimum viable product provides 8 core MCP tools:

**Model Building & Analysis Tools (4)**:
1. **build_media** - Create growth media from ModelSEED compound IDs
2. **build_model** - Build metabolic model from protein sequences
3. **gapfill_model** - Add reactions to enable growth in specified media
4. **run_fba** - Execute flux balance analysis and return fluxes

**ModelSEED Database Tools (4)**:
5. **get_compound_name** - Get human-readable name for compound ID
6. **get_reaction_name** - Get human-readable name and equation for reaction ID
7. **search_compounds** - Find compounds by name/formula
8. **search_reactions** - Find reactions by name/enzyme

### Out of Scope for MVP

**Deferred to Future Phases:**
- Model persistence (file-based import/export) → v0.2.0
- Authentication and authorization → v0.2.0
- Batch operations (multiple models) → v0.2.0
- Knockout analysis and constraint modification → v0.3.0
- Media optimization → v0.3.0
- Production strain design → v0.4.0
- Advanced analysis (FVA, pFBA) → v0.5.0
- Visualization data export → v0.5.0

**Explicitly Not Included:**
- Cloud deployment (local/remote servers only)
- Web UI (MCP tool interface only)
- Multi-user collaboration features
- Real-time notifications
- Database persistence (session-based storage only for MVP)

## Technology Stack

### Core Dependencies

**ModelSEEDpy (dev branch)**
- Source: https://github.com/Fxe/ModelSEEDpy/tree/dev
- Purpose: Model building, gapfilling, media creation
- Key modules:
  - `MSGenome` - Genome representation from protein sequences
  - `MSBuilder` - Draft model construction from templates
  - `MSGapfill` - Genome-scale gapfilling
  - `MSATPCorrection` - ATP metabolism gapfilling
  - `MSMedia` - Growth media specification
  - `MSTemplate` - Template reaction sets

**COBRApy (≥0.27.0)**
- Source: https://pypi.org/project/cobra/
- Purpose: Flux balance analysis, model I/O
- Key functions:
  - `model.optimize()` - FBA execution
  - `load_json_model()` / `save_json_model()` - Model persistence
  - `model.medium` - Media constraints

**FastMCP (latest)**
- Purpose: MCP server framework
- Features: Tool definitions, OAuth 2.1 support (future), JSON-RPC transport

**Pandas (≥2.0.0)**
- Purpose: ModelSEED database queries
- Usage: Load compounds.tsv and reactions.tsv at startup

### Development Tools

**UV** - Modern Python package manager and virtual environment
**Python 3.11+** - Required for type hints and modern syntax
**pytest** - Testing framework (≥80% coverage requirement)
**mypy** - Type checker for static analysis
**ruff** - Linter and formatter

### Deployment Model

**Local Installation:**
```bash
# Clone repository
git clone https://github.com/user/gem-flux-mcp.git
cd gem-flux-mcp

# Install with UV
uv sync

# Start server
uv run python -m gem_flux_mcp
```

**Remote Server:**
- Same installation process
- Accessible to team via network
- No cloud deployment for MVP

**Not Supported:**
- Docker containers (future)
- Kubernetes orchestration (future)
- Cloud hosting (future)

## System Architecture

### High-Level Data Flow

```
User (via AI Assistant)
    ↓
MCP Tool Call (JSON-RPC)
    ↓
Gem-Flux MCP Server
    ↓
┌─────────────────────────────────────┐
│  Tool Router                        │
│  • Input validation                 │
│  • Session management               │
│  • Error handling                   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Library Integration Layer          │
│                                     │
│  ModelSEEDpy         COBRApy        │
│  • MSGenome          • FBA          │
│  • MSBuilder         • Model I/O    │
│  • MSGapfill         • Constraints  │
│  • MSMedia                          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  ModelSEED Database (Pandas)        │
│  • compounds.tsv (33,978 compounds) │
│  • reactions.tsv (36,645 reactions) │
└─────────────────────────────────────┘
    ↓
Structured Response (JSON)
    ↓
AI Assistant
    ↓
User
```

### Complete Workflow Example

**Goal**: Build and analyze an E. coli metabolic model

**Step 1: Create Media**
```
User → AI Assistant: "Create a glucose minimal media"
AI → build_media:
  input: {compounds: ["cpd00027", "cpd00007", ...], custom_bounds: {...}}
  output: {media_id: "media_001", compounds: [...]}
```

**Step 2: Build Model**
```
User → AI Assistant: "Build a model from my E. coli protein sequences"
AI → build_model:
  input: {protein_sequences: {...}, template: "GramNegative"}
  output: {model_id: "model_001", num_reactions: 856, ...}
```

**Step 3: Gapfill Model**
```
User → AI Assistant: "Gapfill this model for growth in glucose media"
AI → gapfill_model:
  input: {model_id: "model_001", media_id: "media_001"}
  output: {model_id: "model_001.gf", reactions_added: [...], growth_rate_after: 0.874}
```

**Step 4: Run FBA**
```
User → AI Assistant: "Run FBA and show me the top fluxes"
AI → run_fba:
  input: {model_id: "model_001.gf", media_id: "media_001"}
  output: {objective_value: 0.874, status: "optimal", fluxes: {...}}
```

**Step 5: Interpret Results**
```
AI → get_reaction_name(reaction_id: "rxn00148")
  output: {name: "hexokinase", equation: "D-Glucose + ATP => ..."}
AI → User: "The model predicts a growth rate of 0.874 hr⁻¹. Key active
             pathways include glycolysis (rxn00148: hexokinase) and ..."
```

## Key Concepts

### Metabolic Modeling Workflow

**Draft Model Building**
- Input: Protein sequences (FASTA format)
- Process: Template-based reconstruction
  1. Load template (GramNegative, GramPositive, Core)
  2. Create genome from sequences
  3. Optional: Annotate with RAST (offline for MVP)
  4. Build base model with template reactions
  5. Add ATPM (ATP maintenance) reaction
- Output: Draft model (may not grow without gapfilling)

**Gapfilling**
- Purpose: Add minimal reactions to enable growth
- Process: Two-stage gapfilling
  1. ATP correction: Ensure ATP production works across test media
  2. Genome-scale: Add reactions for target media and growth rate
- Input: Draft model, target media, growth threshold
- Output: Gapfilled model with added reactions documented

**Flux Balance Analysis (FBA)**
- Purpose: Predict metabolic fluxes and growth rate
- Process: Linear programming optimization
  - Maximize biomass objective (typically "bio1")
  - Subject to stoichiometric and thermodynamic constraints
  - Bounded by media availability (exchange reactions)
- Output: Optimal flux distribution, growth rate, solver status

### ModelSEED Identifiers

**Compound IDs**: `cpd00001`, `cpd00027`, etc.
- Example: `cpd00027` = D-Glucose
- Format: `cpd` + 5-digit number
- Compartment suffix: `cpd00027_c0` (cytosol), `cpd00027_e0` (extracellular)

**Reaction IDs**: `rxn00001`, `rxn00148`, etc.
- Example: `rxn00148` = hexokinase
- Format: `rxn` + 5-digit number
- Compartment suffix: `rxn00148_c0` (cytosolic reaction)

**Exchange Reactions**: `EX_cpd00027_e0`
- Represent uptake/secretion of compounds
- Prefix: `EX_`
- Negative flux = uptake, Positive flux = secretion

**Biomass Objective**: `bio1`
- Pseudo-reaction representing cellular growth
- Consumes metabolic precursors in proportion to biomass composition
- Maximized during FBA

### Templates

**Template Purpose**: Pre-defined reaction sets for organism types

**Available Templates**:
- **GramNegative** (GramNegModelTemplateV6): E. coli, Salmonella, etc.
- **GramPositive**: Bacillus, Staphylococcus, etc.
- **Core** (Core-V5.2): Central metabolism only
- **Archaea**: Archaeal metabolism (future)

**Template Loading**:
- Templates are JSON files distributed with ModelSEEDpy
- Loaded at server startup via `MSTemplateBuilder.from_dict()`
- Contain reaction stoichiometry, directionality, gene associations

## Data Formats

### Media Specification Format

**Input Format** (used by build_media):
```json
{
  "compounds": ["cpd00027", "cpd00007", "cpd00001", "cpd00009", ...],
  "default_uptake": 100.0,
  "custom_bounds": {
    "cpd00027": (-5, 100),    // D-Glucose: -5 mmol/gDW/h uptake
    "cpd00007": (-10, 100)    // O2: -10 mmol/gDW/h uptake
  }
}
```

**Internal Representation** (MSMedia):
```python
{
  "cpd00027_e0": (-5, 100),
  "cpd00007_e0": (-10, 100),
  "cpd00001_e0": (-100, 100),
  // ... other compounds
}
```

**Notes**:
- Negative lower bound = uptake allowed
- Positive upper bound = secretion allowed
- Units: mmol/gDW/h (millimoles per gram dry weight per hour)

### Model Representation

**Session Storage** (MVP):
- Models stored in memory as COBRApy `Model` objects
- Keyed by generated model_id: `model_12345`, `model_12345.gf`
- Cleared when server restarts

**JSON Export Format** (future):
```json
{
  "id": "model_ecoli_001",
  "name": "E. coli K-12 MG1655",
  "reactions": [...],
  "metabolites": [...],
  "genes": [...]
}
```
- Standard COBRApy JSON format
- Compatible with Escher visualization
- Human-readable, version-control friendly

### FBA Results Format

```json
{
  "success": true,
  "objective_value": 0.874,
  "status": "optimal",
  "active_reactions": 423,
  "fluxes": {
    "bio1": 0.874,
    "EX_glc__D_e": -5.0,
    "EX_o2_e": -10.2,
    "rxn00148_c0": 5.0,
    // ... significant fluxes only (|flux| > 1e-6)
  }
}
```

**Status Values**:
- `"optimal"` - Solution found
- `"infeasible"` - No solution exists (model cannot grow)
- `"unbounded"` - Objective can grow infinitely (model error)

### Protein Sequence Format

```json
{
  "protein_sequences": {
    "prot_001": "MKLVINLVGNSGLGKSTFTQRLIN...",
    "prot_002": "MKQHKAMIVALERFRKEKRDAALL...",
    "prot_003": "MSVALERYGIDEVASIGGLVEVNN..."
  }
}
```

**Requirements**:
- Keys: Protein identifiers (arbitrary strings)
- Values: Amino acid sequences (single-letter code)
- Valid amino acids: ACDEFGHIKLMNPQRSTVWY
- No stop codons (*) or ambiguous codes (X, B, Z)

## Session Management

### Model Lifecycle

**Create** → **Modify** → **Analyze** → **Discard**

1. **Create**: `build_model()` generates a model_id
2. **Modify**: `gapfill_model()` creates new model_id (original preserved)
3. **Analyze**: `run_fba()` reads model, doesn't modify
4. **Discard**: Models cleared on server restart

**Model ID Format**: `model_<timestamp>_<random>`
- Example: `model_20251027_a3f9b2`
- Unique per session
- No persistence across server restarts (MVP)

### Media Lifecycle

Similar to models:
1. **Create**: `build_media()` generates media_id
2. **Use**: Referenced by `gapfill_model()` and `run_fba()`
3. **Discard**: Cleared on server restart

**Media ID Format**: `media_<timestamp>_<random>`

## Error Handling Philosophy

### Input Validation

**Validate Early**:
- Check all inputs before calling library functions
- Provide specific error messages with suggestions
- Return structured error responses

**Example Error Response**:
```json
{
  "success": false,
  "error_type": "ValidationError",
  "message": "Invalid compound IDs: cpd99999, cpd88888",
  "details": {
    "invalid_ids": ["cpd99999", "cpd88888"],
    "valid_example": "cpd00027"
  },
  "suggestion": "Check compound IDs against ModelSEED database using search_compounds()"
}
```

### Library Error Handling

**Wrap Library Exceptions**:
- Catch ModelSEEDpy and COBRApy exceptions
- Translate to user-friendly messages
- Include recovery suggestions when possible

**Common Failure Modes**:
- **Gapfilling infeasible**: No reactions can enable growth
  - Suggest: Check media composition, try richer media
- **FBA infeasible**: Model cannot grow in media
  - Suggest: Gapfill model first, check media bounds
- **Template loading failure**: Template file missing/corrupt
  - Suggest: Reinstall ModelSEEDpy, check template names

### Error Response Format

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

## Quality Requirements

### Performance

**Response Times** (target):
- `get_compound_name()`: < 10ms (database lookup)
- `search_compounds()`: < 100ms (database query)
- `build_media()`: < 500ms (MSMedia creation)
- `build_model()`: < 30s (depends on genome size)
- `gapfill_model()`: < 5min (depends on model size)
- `run_fba()`: < 5s (depends on model size)

**Notes**:
- Times are estimates for typical models (~1000 reactions)
- Actual performance depends on hardware and model complexity
- No hard timeouts for MVP (implement in v0.2.0)

### Reliability

**Validation Coverage**:
- ✅ All inputs validated before library calls
- ✅ All library exceptions caught and translated
- ✅ All ModelSEED IDs verified against database
- ✅ All protein sequences validated (amino acid alphabet)

**Testing Requirements**:
- ≥80% code coverage
- Unit tests for each MCP tool
- Integration tests with ModelSEEDpy/COBRApy
- Database query tests

### Usability

**For AI Assistants**:
- Clear, descriptive tool names and descriptions
- Structured JSON inputs/outputs
- Human-readable error messages with suggestions
- Database tools for converting IDs to names

**For Human Users**:
- Natural language interaction via AI assistant
- No need to know ModelSEED IDs
- AI uses `search_compounds()` to find IDs from names
- Results explained in biological terms

## Security & Authentication

### MVP Security Model

**Local-Only Deployment**:
- No authentication required for MVP
- Server listens on localhost only
- Single-user, single-session
- No rate limiting

### Future Security (v0.2.0+)

**OAuth 2.1 with PKCE**:
- No client secrets (PKCE flow)
- JWT tokens for authentication
- Hierarchical scopes:
  - `model:read` - View models
  - `model:write` - Build/modify models
  - `analysis:run` - Execute FBA
  - `database:read` - Query compound/reaction names

**Rate Limiting**:
- Per-client token bucket
- Protect expensive operations (gapfilling, FBA)

**Audit Logging**:
- Log all tool calls with timestamps
- Track model creation and modification
- Enable debugging and usage analysis

## Observability

### Logging

**Log Levels**:
- **INFO**: Tool calls, model creation, FBA execution
- **WARNING**: Validation failures, recoverable errors
- **ERROR**: Library exceptions, system failures
- **DEBUG**: Detailed execution traces (development only)

**Log Format**:
```
[2025-10-27 12:34:56] INFO: build_model called with template=GramNegative, num_proteins=150
[2025-10-27 12:35:23] INFO: build_model completed: model_id=model_001, num_reactions=856
[2025-10-27 12:35:45] ERROR: gapfill_model failed: InfeasibleGapfillError for model_001
```

### Metrics (Future)

**Track**:
- Tool call counts per endpoint
- Average response times
- Success/failure rates
- Model sizes (reactions, metabolites)
- Gapfilling statistics (reactions added)

## Installation & Deployment

### Prerequisites

- Python 3.11 or higher
- UV package manager (https://docs.astral.sh/uv/)
- Git

### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/user/gem-flux-mcp.git
cd gem-flux-mcp

# 2. Install dependencies with UV
uv sync

# 3. Verify installation
uv run pytest

# 4. Start server
uv run python -m gem_flux_mcp
```

### Configuration

**Server Settings** (future: config.yaml):
```yaml
server:
  host: localhost
  port: 8080
  log_level: INFO

database:
  compounds: data/compounds.tsv
  reactions: data/reactions.tsv

templates:
  path: data/templates/
  preload:
    - GramNegative
    - Core

session:
  max_models: 100
  max_media: 50
```

### Distribution

**GitHub Repository**:
- Public repository (recommended)
- Include documentation, examples, tests
- Tag releases (v0.1.0, v0.2.0, etc.)

**Package Distribution** (future):
- PyPI package for `pip install gem-flux-mcp`
- Docker images for containerized deployment

## Future Roadmap

### Phase 2 (v0.2.0): Persistence & Auth
- Model import/export (JSON, SBML)
- File-based persistence
- OAuth 2.1 authentication
- Rate limiting
- Audit logging

### Phase 3 (v0.3.0): Advanced Analysis
- Batch operations (multiple models)
- Knockout analysis (`delete_gene`, `knock_out_reaction`)
- Constraint modification (`set_bounds`, `set_objective`)
- Media optimization (`optimize_media`)

### Phase 4 (v0.4.0): Strain Design
- Production strain design (`design_strain`)
- Pathway analysis (`find_pathways`)
- Flux variability analysis (`run_fva`)
- Parsimonious FBA (`run_pfba`)

### Phase 5 (v0.5.0): Visualization & Integration
- Escher visualization data export
- Cytoscape network export
- KEGG pathway mapping
- Multi-model comparison

### Phase 6 (v1.0.0): Enterprise Features
- Multi-user collaboration
- Project management
- Model versioning
- Result caching
- Distributed gapfilling

## Success Criteria

### MVP Complete When:
- ✅ All 8 core tools implemented and tested
- ✅ ModelSEEDpy integration working (build, gapfill)
- ✅ COBRApy integration working (FBA)
- ✅ ModelSEED database queries functional
- ✅ Complete workflow: build → gapfill → FBA → interpret
- ✅ Documentation complete with examples
- ✅ Test coverage ≥80%
- ✅ GitHub repository ready for distribution

### Quality Gates:
- ✅ All tests pass
- ✅ Type checking passes (mypy)
- ✅ Linting passes (ruff)
- ✅ Example notebooks run successfully
- ✅ AI assistants can use tools without confusion

## References

**Source Materials**:
- `build_model.ipynb` - Complete ModelSEEDpy workflow
- `cobrapy-reference.md` - FBA operations and patterns
- `modelseed-database-guide.md` - Database structure and queries
- `uv-package-manager.md` - Package management and deployment
- `additional-mcp-tools.md` - Future roadmap (34 additional tools)

**External Documentation**:
- ModelSEEDpy: https://github.com/Fxe/ModelSEEDpy/tree/dev
- COBRApy: https://cobrapy.readthedocs.io/
- ModelSEED Database: https://github.com/ModelSEED/ModelSEEDDatabase
- FastMCP: https://github.com/jlowin/fastmcp
- UV: https://docs.astral.sh/uv/

**Related Specifications**:
- 002-data-formats.md - Detailed data structure specifications
- 003-build-media-tool.md - build_media tool specification
- 004-build-model-tool.md - build_model tool specification
- 005-gapfill-model-tool.md - gapfill_model tool specification
- 006-run-fba-tool.md - run_fba tool specification
- 007-database-integration.md - ModelSEED database architecture
- 008-compound-lookup-tools.md - Compound lookup specifications
- 009-reaction-lookup-tools.md - Reaction lookup specifications

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 002-data-formats.md
