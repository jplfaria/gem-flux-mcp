# Documentation Requirements - Gem-Flux MCP Server

**Type**: Documentation Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding overall system architecture)
- Read: All tool specifications (003-006, 008-009, 018)

## Purpose

This specification defines the documentation requirements for the Gem-Flux MCP server project. It ensures that all phases of development maintain comprehensive, accurate, and useful documentation for developers, users, and AI assistants interacting with the system.

## Core Design Principles

**Documentation as Code**:
- Documentation lives alongside code
- Updated in the same commits as code changes
- Versioned with the codebase

**Multi-Audience Approach**:
- **Developers**: Implementation guides, API docs, architecture
- **Users**: User guides, tutorials, examples
- **AI Assistants**: Tool descriptions, usage patterns, error recovery

**Keep It Current**:
- Documentation updated before PR merge
- Review checklist includes documentation verification
- Automated checks for missing docs

## Documentation Structure

### Project Root Documentation

```
gem-flux-mcp/
├── README.md                    # Project overview, quick start
├── CHANGELOG.md                 # Version history, breaking changes
├── CONTRIBUTING.md              # How to contribute
├── LICENSE                      # MIT License
├── docs/
│   ├── installation.md          # Detailed installation guide
│   ├── quick-start.md           # 5-minute getting started
│   ├── architecture.md          # System architecture overview
│   ├── api-reference.md         # Complete API documentation
│   ├── tutorials/               # Step-by-step guides
│   ├── examples/                # Code examples
│   └── troubleshooting.md       # Common issues and solutions
├── specs/                       # Phase 0 specifications (this directory)
└── tests/
    └── README.md                # Testing guide
```

## Required Documentation Files

### 1. README.md (Project Root)

**Purpose**: First point of contact for anyone discovering the project

**Required Sections**:
- **Project Title and Description**: What is Gem-Flux MCP Server?
- **Key Features**: Bullet list of main capabilities
- **Quick Start**: Installation and first command (< 5 minutes)
- **Example Usage**: One complete workflow example
- **Documentation Links**: Links to detailed docs
- **License**: MIT License badge and link
- **Contributing**: Link to CONTRIBUTING.md
- **Status Badge**: Development status (Alpha/Beta/Stable)

**Length**: 200-400 lines

**Update Frequency**: Every minor version release

---

### 2. docs/installation.md

**Purpose**: Complete installation guide for all platforms

**Required Sections**:
- **Prerequisites**: Python 3.11+, UV package manager
- **Installation Methods**:
  - From PyPI (future)
  - From source (current)
  - Development setup
- **Platform-Specific Instructions**:
  - macOS
  - Linux
  - Windows (WSL)
- **Dependency Installation**: ModelSEEDpy (dev), COBRApy
- **Template Setup**: Downloading and placing template files
- **Database Setup**: ModelSEED database files
- **Verification**: Test commands to verify installation
- **Troubleshooting**: Common installation issues

**Length**: 300-500 lines

**Update Frequency**: When dependencies change

---

### 3. docs/quick-start.md

**Purpose**: Get users productive in 5 minutes

**Required Sections**:
- **Goal**: What you'll accomplish in 5 minutes
- **Installation** (brief): Link to full installation guide
- **First Model**: Build a simple model from protein sequences
- **First Gapfill**: Gapfill model for growth
- **First FBA**: Run flux balance analysis
- **Next Steps**: Links to tutorials and examples

**Example Workflow**:
```bash
# 1. Start server
uv run fastmcp dev server.py

# 2. Build model (via AI assistant or direct)
# 3. Gapfill model
# 4. Run FBA
# 5. Interpret results
```

**Length**: 100-200 lines

**Update Frequency**: Every major version

---

### 4. docs/architecture.md

**Purpose**: Explain system design and component interactions

**Required Sections**:
- **System Overview**: High-level architecture diagram
- **Components**:
  - MCP Server (FastMCP)
  - ModelSEEDpy integration
  - COBRApy integration
  - Database layer
  - Session management
- **Data Flow**: How data moves through the system
- **Tool Specifications**: Link to individual tool specs
- **Design Decisions**: Why certain approaches were chosen
- **Extensibility**: How to add new tools

**Length**: 500-800 lines

**Update Frequency**: When architecture changes

---

### 5. docs/api-reference.md

**Purpose**: Complete reference for all MCP tools

**Required Sections**:

For **each tool** (8 MVP tools + 3 session management):
- **Tool Name**: build_model, gapfill_model, etc.
- **Description**: One-line summary
- **Input Parameters**: Complete parameter documentation
- **Output Format**: Response structure with examples
- **Error Responses**: All possible errors
- **Usage Examples**: At least 2 examples per tool
- **Related Tools**: Links to tools used before/after

**Generation**: Auto-generated from tool docstrings (future)

**Length**: 2000-3000 lines (all tools)

**Update Frequency**: When tool interfaces change

---

### 6. docs/tutorials/

**Purpose**: Step-by-step guides for common workflows

**Required Tutorials** (MVP):

**Tutorial 1: Building Your First Model** (`building-first-model.md`)
- Choose organism (E. coli example)
- Obtain protein sequences
- Select appropriate template
- Build model
- Interpret results
- Save model (future)

**Tutorial 2: Gapfilling for Growth** (`gapfilling-guide.md`)
- Why gapfilling is needed
- Create or select media
- Run gapfilling
- Understand reactions added
- Verify growth

**Tutorial 3: Flux Balance Analysis** (`fba-guide.md`)
- What is FBA?
- Run FBA on gapfilled model
- Interpret fluxes
- Analyze metabolic pathways
- Export results (future)

**Tutorial 4: Complete Workflow** (`complete-workflow.md`)
- End-to-end: sequences → model → gapfill → FBA
- Real-world example
- Troubleshooting common issues

**Length**: 200-400 lines each

**Update Frequency**: When workflows change

---

### 7. docs/examples/

**Purpose**: Copy-paste code examples

**Required Examples**:

```
examples/
├── basic_model_building.py       # Build model from dict
├── build_from_fasta.py           # Build model from FASTA file
├── gapfill_workflow.py           # Complete gapfilling workflow
├── fba_analysis.py               # Run FBA and analyze results
├── custom_media.py               # Create custom growth media
├── database_queries.py           # Query compound/reaction database
├── session_management.py         # List, delete models
└── README.md                     # Example index
```

**Example Format**:
- **File header**: Purpose, prerequisites
- **Complete code**: Runnable example
- **Comments**: Explain each step
- **Expected output**: What to expect

**Length**: 50-150 lines per example

**Update Frequency**: With each new tool

---

### 8. docs/troubleshooting.md

**Purpose**: Solutions to common problems

**Required Sections**:
- **Installation Issues**
- **Server Startup Problems**
- **Template Loading Errors**
- **RAST Annotation Failures**
- **Model Building Errors**
- **Gapfilling Failures**
- **FBA Infeasible Solutions**
- **Performance Issues**

**Format for Each Issue**:
```markdown
### Issue: [Short description]

**Symptoms**: What the user sees

**Cause**: Why it happens

**Solution**: Step-by-step fix

**Prevention**: How to avoid in future
```

**Length**: 400-600 lines

**Update Frequency**: As new issues discovered

---

## Tool Documentation Requirements

### MCP Tool Docstrings

Every MCP tool must have:

```python
@mcp.tool()
async def build_model(
    protein_sequences: dict[str, str] | None = None,
    fasta_file_path: str | None = None,
    template: str = "GramNegative",
    model_name: str | None = None,
    annotate_with_rast: bool = True
) -> dict:
    """Build draft metabolic model from protein sequences.

    Constructs a genome-scale metabolic model using template-based
    reconstruction. By default, uses RAST API for functional annotation
    to improve reaction mapping accuracy.

    Args:
        protein_sequences: Dict mapping protein IDs to amino acid sequences.
            Mutually exclusive with fasta_file_path.
        fasta_file_path: Path to FASTA file with protein sequences (.faa).
            Mutually exclusive with protein_sequences.
        template: ModelSEED template name. One of: "GramNegative",
            "GramPositive", "Core". Default: "GramNegative".
        model_name: Optional custom model name. If not provided,
            auto-generates timestamped ID.
        annotate_with_rast: Enable RAST annotation (requires internet).
            Default: True. Set to False for offline mode.

    Returns:
        Dict with:
            - success: bool
            - model_id: str (with .draft suffix)
            - model_name: str
            - num_reactions: int
            - num_metabolites: int
            - num_genes: int
            - template_used: str
            - annotation_method: str ("RAST" or "offline")

    Raises:
        ValidationError: Invalid amino acid sequences or template name
        FileNotFoundError: FASTA file not found
        RASTAnnotationError: RAST API failure (if annotate_with_rast=True)

    Example:
        >>> result = await build_model(
        ...     protein_sequences={"prot1": "MKLVIN...", "prot2": "MKQHKA..."},
        ...     template="GramNegative"
        ... )
        >>> print(result["model_id"])
        'model_20251027_143052_abc123.draft'
    """
```

**Requirements**:
- One-line summary (< 80 chars)
- Detailed description (2-4 sentences)
- All parameters documented with types
- Return value fully documented
- All exceptions listed
- At least one example

---

## Documentation Workflow

### Phase-Based Documentation

**Phase 0 (Specification)**:
- ✅ All specifications written (specs/ directory)
- ✅ CLEANROOM specifications (behavioral, not implementation)
- ✅ Complete tool specifications
- ✅ Data format specifications

**Phase 1 (Implementation)**:
- Write implementation docs alongside code
- Update API reference as tools implemented
- Create examples for each tool
- Write docstrings for all functions

**Phase 2 (Testing)**:
- Document test procedures
- Create testing guides
- Add troubleshooting entries

**Phase 3 (Release)**:
- Finalize README.md
- Complete all tutorials
- Review all documentation for accuracy
- Generate API docs from docstrings

### Documentation Review Checklist

Before merging any PR:

- [ ] Code changes reflected in relevant docs
- [ ] New tools have complete API documentation
- [ ] Examples updated if API changed
- [ ] Docstrings complete and accurate
- [ ] No broken internal links
- [ ] CHANGELOG.md updated
- [ ] Version numbers consistent

### Documentation Quality Standards

**Clarity**:
- Write for target audience (don't assume knowledge)
- Use clear, concise language
- Provide context before details

**Completeness**:
- Cover all features
- Document all parameters and return values
- Include error handling

**Accuracy**:
- Test all code examples
- Verify commands work as shown
- Update when code changes

**Consistency**:
- Use same terminology throughout
- Follow style guide
- Consistent formatting

## Style Guide

### Terminology

**Use Consistently**:
- "Model" not "network" or "reconstruction"
- "Tool" not "function" or "method" (for MCP tools)
- "Media" not "medium" or "growth conditions" (singular: use "medium")
- "Gapfill" not "gap-fill" or "gap fill"
- "Model ID" not "model identifier" or "model_id"

### Code Examples

**Format**:
```python
# Good: Complete, runnable example
from modelseedpy import MSGenome

protein_sequences = {
    "protein_001": "MKLVIN...",
    "protein_002": "MKQHKA..."
}

result = build_model(
    protein_sequences=protein_sequences,
    template="GramNegative"
)
print(result["model_id"])
```

**Avoid**:
```python
# Bad: Incomplete, not runnable
result = build_model(...)  # Don't use ... without context
```

### Diagrams

**Use Mermaid for Diagrams**:
```mermaid
graph LR
    A[Protein Sequences] --> B[build_model]
    B --> C[Draft Model]
    C --> D[gapfill_model]
    D --> E[Gapfilled Model]
    E --> F[run_fba]
    F --> G[Growth Rate + Fluxes]
```

**Include in Markdown**:
- Architecture diagrams
- Data flow diagrams
- Workflow visualizations

## Automated Documentation

### Future: Auto-Generated API Docs

**Tools**:
- Sphinx for Python API docs
- mkdocs for user-facing docs
- pdoc3 for quick reference

**Process**:
1. Write docstrings (Google style)
2. Run documentation generator
3. Review generated docs
4. Publish to docs site

**Configuration**:
```yaml
# mkdocs.yml
site_name: Gem-Flux MCP Server
theme: material
nav:
  - Home: index.md
  - Installation: installation.md
  - Quick Start: quick-start.md
  - API Reference: api-reference.md
  - Tutorials: tutorials/
```

## Related Specifications

- **001-system-overview.md**: Overall system architecture
- **All tool specs**: Source material for API reference
- **SPECS_PLAN.md**: Documentation requirements per phase

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Completion**: All new specs created!
