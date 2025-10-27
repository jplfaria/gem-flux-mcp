# Gem-Flux MCP Server Specification Guidelines

## Key Lessons from Previous Specification Exercises

### 1. **Start Complex, Then Simplify**
- First version can be comprehensive/complex
- Look for actual simplicity in source materials
- Don't add complexity that isn't there
- ModelSEEDpy and COBRApy are already complex - capture their interfaces simply

### 2. **Multi-Agent Research Pattern**
*Note: This refers to using AI assistants to research and create specs, not to the Gem-Flux architecture*
- Use parallel agents for different aspects:
  - ModelSEEDpy integration agent
  - COBRApy integration agent
  - MCP interface agent
  - ModelSEED database agent
- Synthesize findings AFTER all complete
- Wait for ALL agents before proceeding
- Example: Use Claude's Task tool to spawn parallel research agents
- Each agent should have a clear, focused prompt
- Gather all results before synthesizing into specs

### 3. **CLEANROOM Principles**
- NO implementation details
- Focus on WHAT, not HOW
- Define interfaces and contracts
- Specify inputs/outputs/behaviors
- Keep implementation choices open
- See SPECS_CLAUDE.md for detailed CLEANROOM guidance

### 4. **Specification Structure**
Each spec should include:
- Prerequisites section (when the spec depends on understanding other specs)
- Input/Output specifications
- Behavioral contracts
- Error handling behavior
- Quality requirements
- Natural language examples

**Prerequisites Section**:
When a specification depends on concepts from other specs, add a Prerequisites section near the top:
```markdown
## Prerequisites
- Read: [Required spec name] (for understanding X concept)
- Understand: [Key concept] from [Source spec]
```
This helps readers know what context they need before diving into the spec.

### 5. **Technology Decisions**
For Gem-Flux MCP Server:
- **Python 3.11+** with type hints
- **FastMCP** for MCP server framework
- **ModelSEEDpy (dev branch)** from https://github.com/Fxe/ModelSEEDpy
  - Model building: MSBuilder, MSGenome, MSTemplate
  - Gapfilling: MSGapfill, MSATPCorrection
  - Media creation: MSMedia
- **COBRApy (≥0.27.0)** for flux balance analysis
  - Model I/O: load_json_model, save_json_model
  - FBA: model.optimize(), model.slim_optimize()
  - Constraints: model.medium, reaction bounds
- **Pandas** for ModelSEED database queries (compounds.tsv, reactions.tsv)
- **UV package manager** for dependency management
- Simple local file-based storage (no database for MVP)
- Modern development environment:
  - Use `uv` for fast package management and virtual environments
  - `pytest` for testing with ≥80% coverage requirement
  - `mypy` for type checking
  - `ruff` for linting

### 6. **Document Organization**
Create separate specs for:
1. System overview and architecture
2. Core MCP tools (build_media, build_model, gapfill_model, run_fba)
3. ModelSEED database integration (compound/reaction lookups)
4. Model I/O and persistence (import/export JSON)
5. Authentication and security (future: OAuth 2.1)
6. Deployment and installation
7. Error handling and validation
8. Future enhancements (batch operations, strain design, etc.)

**File Naming Convention**:
- Use numbered prefixes for ordering: `001-system-overview.md`, `002-core-tools.md`
- Numbers help maintain logical reading order
- Use descriptive names after the number

### 7. **Key Questions to Answer**
- What are the 4 MVP tools and what do they do?
- How does ModelSEEDpy model building work?
- How does gapfilling work?
- How does COBRApy FBA work?
- How do LLMs get human-readable compound/reaction names?
- What data formats are used (input/output)?
- How are models persisted between operations?
- What constitutes a successful model build?
- What are common failure modes?
- How do users install and run the server?

### 8. **Avoid Common Pitfalls**
- Don't invent features not in source materials
- Don't overcomplicate the ModelSEEDpy/COBRApy interfaces
- Don't mix implementation with specification
- Don't forget this is for AI assistants, not just human users
- Don't create unnecessary abstractions
- Don't specify authentication for MVP (defer to future)

### 9. **Follow Established Patterns**
- Study `build_model.ipynb` for exact ModelSEEDpy workflow
- Use ModelSEED Database guide for compound/reaction lookup patterns
- Apply COBRApy reference for FBA patterns
- Keep implementations minimal and focused
- Follow MCP server patterns from `mcp-server-reference.md`

### 10. **Gem-Flux Specific Patterns**

#### ModelSEEDpy Workflow
1. Load templates (GramNegative, Core, etc.)
2. Create genome from protein sequences
3. Optionally annotate with RAST (offline mode for MVP)
4. Build base model with MSBuilder
5. Run ATP gapfilling with MSATPCorrection
6. Run genome-scale gapfilling with MSGapfill
7. Export to COBRApy model for FBA

#### COBRApy FBA Workflow
1. Load model (from ModelSEEDpy or import JSON)
2. Set medium (exchange reaction bounds)
3. Run FBA with model.optimize()
4. Return fluxes, growth rate, status

#### ModelSEED Database Integration
1. Load compounds.tsv and reactions.tsv at server startup
2. Index by ID for O(1) lookup
3. Provide tools: get_compound_name, get_reaction_name, search_compounds, search_reactions
4. Enable LLMs to reason about metabolic pathways

### 11. **Data Flow Specifications**

**Model Building Flow**:
```
Protein Sequences (dict)
  → MSGenome.from_dict()
  → (optional) RastClient.annotate_genome()
  → MSBuilder.build_base_model()
  → MSBuilder.add_atpm()
  → MSATPCorrection (ATP gapfilling)
  → MSGapfill (genome-scale gapfilling)
  → COBRApy Model (JSON export)
```

**FBA Flow**:
```
Model ID + Media (dict)
  → Load COBRApy model
  → Set model.medium
  → model.optimize()
  → Solution (fluxes, objective_value, status)
  → JSON response
```

### 12. **Error Handling Patterns**
Specify behaviors for:
- Invalid protein sequences
- RAST annotation failures (offline mode)
- Gapfilling infeasibility
- FBA infeasibility
- Invalid ModelSEED compound/reaction IDs
- Missing media components
- Model loading failures
- JSON parsing errors

### 13. **MCP Tool Interface Patterns**
For each tool, specify:
- Tool name and description
- Input parameters (types, constraints, examples)
- Output structure (JSON schema)
- Error responses
- Example usage from AI assistant perspective
- Required permissions/scopes (for future auth)

### 14. **Development Environment Setup**
When implementing Gem-Flux:
1. **Project Setup Phase** should include:
   - Install `uv` for package management: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Create `pyproject.toml` with dependencies
   - Use `uv sync` for dependency installation
   - Configure Python 3.11 in `.python-version`

2. **Testing Infrastructure**:
   - Unit tests for each MCP tool
   - Integration tests with ModelSEEDpy
   - Integration tests with COBRApy
   - ModelSEED database query tests
   - Use pytest with ≥80% coverage requirement

3. **Implementation Loop** (Phase 1):
   - After specs complete, create IMPLEMENTATION_PLAN.md
   - Break specs into atomic coding tasks
   - Test-driven development
   - Quality gates: tests pass, coverage ≥80%, mypy clean, ruff clean

### 15. **Validation Framework**
For Gem-Flux, validation means:

**Functional Validation** (Can it work?):
- Build a model from protein sequences
- Gapfill the model for glucose minimal media
- Run FBA and get positive growth rate
- Lookup compound names from ModelSEED IDs

**Behavioral Validation** (Does it work correctly?):
- Gapfilled models grow in specified media
- FBA returns biologically reasonable fluxes
- ModelSEED lookups return correct names
- Errors are handled gracefully

**Test Cases**:
1. **E. coli model building**: Use example from `build_model.ipynb`
2. **Minimal media**: Glucose + salts → positive growth
3. **Rich media**: LB media → high growth
4. **Compound lookup**: cpd00027 → "D-Glucose"
5. **Reaction lookup**: rxn00148 → "hexokinase"

**Success Criteria**:
- All 4 MVP tools execute without errors
- Models can be built, gapfilled, and analyzed
- LLMs can get human-readable metabolic information
- System is installable by users via GitHub

### 16. **Metabolic Modeling Domain Knowledge**

**Key Concepts to Capture in Specs**:
- **Templates**: Pre-defined reaction sets for organism types (GramNegative, GramPositive, Archaea, etc.)
- **Gapfilling**: Adding reactions to enable growth (minimize additions while achieving target growth rate)
- **ATP Gapfilling**: Ensuring ATP production pathways work across different media
- **Exchange Reactions**: Reactions representing uptake/secretion (prefix: EX_)
- **Biomass Reaction**: Objective function representing cellular growth (typically bio1)
- **Flux Balance Analysis**: Linear programming to find optimal flux distribution
- **Media**: Set of available compounds with uptake bounds
- **ModelSEED IDs**: Standardized compound (cpd*) and reaction (rxn*) identifiers

**Don't Over-Specify**:
- We're building an interface, not re-implementing ModelSEEDpy/COBRApy
- Defer to source libraries for complex metabolic logic
- Focus on: inputs → library call → outputs

### 17. **Future Phases Roadmap**
Document but don't over-specify:
- **Phase 2** (v0.2.0): Model persistence, import/export, basic auth
- **Phase 3** (v0.3.0): Batch operations, knockout analysis
- **Phase 4** (v0.4.0): Production strain design, media optimization
- **Phase 5** (v0.5.0): Advanced analysis, visualization data export

Keep future specs lightweight - just enough to guide architecture decisions.

---

## Summary

**This is a metabolic modeling MCP server, not a research hypothesis system.**

Key differences from AI Co-Scientist example:
- ❌ No multi-agent system (no supervisor, no tournaments)
- ❌ No LLM-based reasoning (ModelSEEDpy/COBRApy do the work)
- ❌ No BAML (direct Python library calls)
- ❌ No hypothesis evolution or ranking
- ✅ MCP server exposing metabolic modeling tools
- ✅ FastMCP framework with tool definitions
- ✅ Integration with ModelSEEDpy and COBRApy
- ✅ ModelSEED database for LLM-friendly lookups
- ✅ Simple, focused on 4 core operations

**When specifying, ask**: "What does this tool DO?" not "How is it implemented?"

**Follow the source materials**:
- `build_model.ipynb` shows exact workflow
- COBRApy reference shows FBA patterns
- ModelSEED database guide shows lookup patterns
- MCP reference shows server patterns

**Trust your complete read of the source materials.**
