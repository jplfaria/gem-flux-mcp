# Template Management Specification - Gem-Flux MCP Server

**Type**: Template Management Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for understanding ModelSEED templates)
- Read: 004-build-model-tool.md (for template usage in model building)
- Read: 015-mcp-server-setup.md (for server initialization)

## Purpose

This specification defines how ModelSEED template files are loaded, cached, and accessed by the Gem-Flux MCP server. Templates define the reaction sets available for template-based metabolic model construction and are critical for the `build_model` tool.

## Core Design Principles

**Pre-loaded Templates**:
- Templates loaded at server startup
- Cached in memory for fast access
- No runtime template loading (MVP)
- Eliminates repeated file I/O during model building

**Fail-Fast on Missing Templates**:
- Server fails to start if templates missing
- Clear error messages guide installation/repair
- No degraded operation without templates

**Simple Template Access**:
- Templates accessed by name ("GramNegative", "GramPositive", "Core")
- O(1) lookup via dictionary
- Read-only access (templates never modified)

## Template File Locations

### Directory Structure

```
data/
└── templates/
    ├── GramNegModelTemplateV6.json
    ├── GramPosModelTemplateV6.json  (if available)
    ├── Core-V5.2.json
    └── README.md
```

### File Paths

**Absolute Paths** (from project root):
- GramNegative: `data/templates/GramNegModelTemplateV6.json`
- GramPositive: `data/templates/GramPosModelTemplateV6.json`
- Core: `data/templates/Core-V5.2.json`

**Template README**:
- Path: `data/templates/README.md`
- Purpose: Document template sources, versions, update procedures

## Template File Format

### JSON Structure

Templates are JSON files with the following top-level structure:

```json
{
  "id": "GramNegative",
  "name": "Gram-Negative Bacteria Template",
  "version": "6.0",
  "reactions": [...],  // Array of ~2000 reaction objects
  "metabolites": [...],  // Array of metabolite definitions (becomes .compounds attribute in MSTemplate)
  "biomass": {...},  // Biomass reaction composition
  "pathways": [...],  // Pathway organization
  "compartments": ["c0", "e0", "p0"],
  "complexes": [...]  // Protein complexes and gene associations
}
```

**Note**: In the raw JSON, metabolites are called "metabolites", but when parsed by `MSTemplateBuilder`, they become available as `template.compounds` (not `template.metabolites`). Always use `template.compounds` when accessing the MSTemplate object.

### File Characteristics

**GramNegModelTemplateV6.json**:
- Size: ~10-20 MB (JSON text)
- Reactions: ~2000
- Compartments: c0 (cytosol), e0 (extracellular), p0 (periplasm)
- Use for: E. coli, Salmonella, Pseudomonas, etc.

**GramPosModelTemplateV6.json**:
- Size: ~8-15 MB
- Reactions: ~1800
- Compartments: c0 (cytosol), e0 (extracellular)
- Use for: Bacillus, Staphylococcus, Streptococcus, etc.

**Core-V5.2.json**:
- Size: ~2-5 MB
- Reactions: ~200
- Compartments: c0 (cytosol), e0 (extracellular)
- Use for: Central metabolism, prototyping

## Template Loading Process

### Server Startup Sequence

**Step 1: Locate Template Files**
1. Check if `data/templates/` directory exists
2. If missing, fail startup with error message
3. List all JSON files in directory
4. Verify required templates present:
   - `GramNegModelTemplateV6.json` (required)
   - `Core-V5.2.json` (required)
   - `GramPosModelTemplateV6.json` (optional for MVP)

**Step 2: Load and Parse Templates**
1. For each template file:
   - Read JSON file
   - Parse JSON structure
   - Validate required fields present
   - Create MSTemplate object using ModelSEEDpy
2. If any parsing fails, fail startup with detailed error

**Step 3: Cache in Memory**
1. Store templates in memory cache (dictionary)
2. Key: Template name (e.g., "GramNegative")
3. Value: MSTemplate object
4. Templates remain cached for server lifetime

**Step 4: Log Template Status**
1. Log successfully loaded templates
2. Log template versions
3. Log template statistics (num reactions, compounds)
4. Confirm template cache ready

### Template Loading Algorithm

```python
from modelseedpy.core.mstemplate import MSTemplateBuilder
import json
from pathlib import Path

def load_templates() -> dict:
    """Load all ModelSEED templates at server startup.

    Returns:
        Dict mapping template names to MSTemplate objects

    Raises:
        FileNotFoundError: If template directory or files missing
        ValueError: If template parsing fails
    """
    template_dir = Path("data/templates")

    # Verify directory exists
    if not template_dir.exists():
        raise FileNotFoundError(
            f"Template directory not found: {template_dir}\n"
            "Please ensure data/templates/ directory exists with template files."
        )

    # Define template files
    template_files = {
        "GramNegative": "GramNegModelTemplateV6.json",
        "GramPositive": "GramPosModelTemplateV6.json",
        "Core": "Core-V5.2.json"
    }

    templates = {}
    required = ["GramNegative", "Core"]

    for name, filename in template_files.items():
        filepath = template_dir / filename

        # Check if file exists
        if not filepath.exists():
            if name in required:
                raise FileNotFoundError(
                    f"Required template missing: {filepath}\n"
                    f"Template '{name}' is required for server operation."
                )
            else:
                print(f"Warning: Optional template '{name}' not found at {filepath}")
                continue

        # Load and parse template
        try:
            with open(filepath, 'r') as fh:
                template_dict = json.load(fh)

            # Build MSTemplate object
            template = MSTemplateBuilder.from_dict(template_dict).build()

            templates[name] = template
            print(f"✓ Loaded template '{name}': {len(template.reactions)} reactions")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to build template '{name}': {e}")

    # Verify at least one template loaded
    if not templates:
        raise ValueError("No templates successfully loaded. Cannot start server.")

    return templates

# Usage at server startup:
TEMPLATE_CACHE = load_templates()
```

## Template Access Pattern

### Getting Templates by Name

```python
def get_template(template_name: str) -> MSTemplate:
    """Get cached template by name.

    Args:
        template_name: One of "GramNegative", "GramPositive", "Core"

    Returns:
        MSTemplate object

    Raises:
        ValueError: If template name unknown
    """
    if template_name not in TEMPLATE_CACHE:
        valid_names = list(TEMPLATE_CACHE.keys())
        raise ValueError(
            f"Unknown template '{template_name}'. "
            f"Valid templates: {valid_names}"
        )

    return TEMPLATE_CACHE[template_name]

# Usage in build_model tool:
template = get_template("GramNegative")
builder = MSBuilder(genome, template, model_name)
```

### Template Name Validation

```python
def validate_template_name(template_name: str) -> bool:
    """Check if template name is valid and available.

    Args:
        template_name: Template name to validate

    Returns:
        True if valid and available, False otherwise
    """
    return template_name in TEMPLATE_CACHE

# Usage:
if not validate_template_name(user_input):
    return error_response(f"Invalid template: {user_input}")
```

### List Available Templates

```python
def list_available_templates() -> list[dict]:
    """List all available templates with metadata.

    Returns:
        List of dicts with template info
    """
    templates_info = []

    for name, template in TEMPLATE_CACHE.items():
        templates_info.append({
            "name": name,
            "num_reactions": len(template.reactions),
            "num_compounds": len(template.compounds),  # Templates use .compounds, not .metabolites
            "compartments": template.compartments,
            "version": getattr(template, 'version', 'unknown')
        })

    return templates_info

# Example output:
# [
#   {
#     "name": "GramNegative",
#     "num_reactions": 2035,
#     "num_compounds": 1542,  # Templates use .compounds, not .metabolites
#     "compartments": ["c0", "e0", "p0"],
#     "version": "6.0"
#   },
#   ...
# ]
```

## Error Handling

### Missing Template Directory

**Error Condition**: `data/templates/` directory does not exist

**Server Behavior**:
- Fail to start
- Display clear error message
- Provide instructions for fixing

**Error Message**:
```
ERROR: Template directory not found: data/templates/

The server requires ModelSEED template files to operate.

To fix:
1. Create directory: mkdir -p data/templates
2. Download required templates:
   - GramNegModelTemplateV6.json
   - Core-V5.2.json
3. Place templates in data/templates/
4. Restart server

See docs/template-installation.md for detailed instructions.
```

### Missing Required Template

**Error Condition**: Required template file missing (GramNegative or Core)

**Server Behavior**:
- Fail to start
- Identify which template is missing
- Provide download/installation instructions

**Error Message**:
```
ERROR: Required template missing: data/templates/GramNegModelTemplateV6.json

Template 'GramNegative' is required for server operation.

To fix:
1. Download GramNegModelTemplateV6.json from ModelSEED
2. Place in data/templates/
3. Verify file integrity (valid JSON)
4. Restart server

Template source: https://github.com/ModelSEED/ModelSEEDDatabase
```

### Invalid Template JSON

**Error Condition**: Template file is corrupted or invalid JSON

**Server Behavior**:
- Fail to start
- Identify which template has invalid JSON
- Show JSON parsing error

**Error Message**:
```
ERROR: Invalid JSON in data/templates/GramNegModelTemplateV6.json
Line 42, Column 18: Unexpected token '}'

The template file appears to be corrupted.

To fix:
1. Delete corrupted file
2. Re-download template from source
3. Verify file size and integrity
4. Restart server
```

### Template Parsing Error

**Error Condition**: JSON is valid but MSTemplateBuilder fails to parse

**Server Behavior**:
- Fail to start
- Show ModelSEEDpy error message
- Suggest template version mismatch

**Error Message**:
```
ERROR: Failed to build template 'GramNegative'
ModelSEEDpy error: Missing required field 'reactions' in template

This may indicate a template version mismatch.

To fix:
1. Verify you have the correct template version
2. Check ModelSEEDpy is up to date (pip install -U modelseedpy)
3. Re-download templates if needed
4. Restart server
```

## Template Characteristics Reference

### GramNegative Template

**Organism Types**: Gram-negative bacteria
- *Escherichia coli*
- *Salmonella* spp.
- *Pseudomonas* spp.
- *Shigella* spp.

**Features**:
- Reactions: ~2000
- Compartments: c0 (cytosol), e0 (extracellular), p0 (periplasm)
- Special pathways: LPS biosynthesis, flagellar assembly
- Periplasmic space: Unique to Gram-negatives

**Use When**:
- Organism is Gram-negative
- Thin peptidoglycan layer
- Outer membrane present
- Periplasmic space present

### GramPositive Template

**Organism Types**: Gram-positive bacteria
- *Bacillus* spp.
- *Staphylococcus* spp.
- *Streptococcus* spp.
- *Lactobacillus* spp.

**Features**:
- Reactions: ~1800
- Compartments: c0 (cytosol), e0 (extracellular)
- Special pathways: Thick cell wall biosynthesis
- No periplasm: Different from Gram-negatives

**Use When**:
- Organism is Gram-positive
- Thick peptidoglycan layer
- No outer membrane
- No periplasmic space

### Core Template

**Organism Types**: Any (central metabolism only)

**Features**:
- Reactions: ~200
- Compartments: c0 (cytosol), e0 (extracellular)
- Pathways: Glycolysis, TCA cycle, pentose phosphate, basic biosynthesis
- Fast: Much smaller than full genome-scale

**Use When**:
- Prototyping
- Teaching/learning metabolic modeling
- Only central metabolism needed
- Fast model building desired
- Testing workflows

## Template Update Procedures

### When to Update Templates

**Triggers for updating**:
1. ModelSEED database releases new template version
2. Bug fixes in template reactions
3. New organism-specific templates available
4. Template improvements published

**Update Frequency**:
- MVP: Manual updates as needed
- Future: Automated update checks

### Update Process

**Steps**:
1. Download new template JSON files
2. Verify file integrity (checksums if provided)
3. Test templates in development environment
4. Replace old templates in `data/templates/`
5. Update template README with version info
6. Restart server to load new templates
7. Verify models build successfully with new templates

**Validation**:
- Run test suite after template update
- Build sample models (E. coli, B. subtilis)
- Compare model statistics (reaction count, etc.)
- Ensure backward compatibility where possible

## Performance Considerations

### Memory Usage

**Template Cache Size**:
- GramNegative template: ~50-100 MB in memory
- GramPositive template: ~40-80 MB in memory
- Core template: ~10-20 MB in memory
- Total: ~100-200 MB for all templates

**Acceptability**: Negligible for modern servers

### Loading Time

**Startup Impact**:
- GramNegative: 2-5 seconds to load and parse
- GramPositive: 2-5 seconds
- Core: < 1 second
- Total startup delay: 5-10 seconds

**Acceptability**: One-time cost at server startup, not per-request

### Access Performance

**Template Lookup**: O(1) dictionary lookup (< 1 ms)
**Template Usage**: Zero overhead (already in memory)

## Future Enhancements

### Post-MVP Features (Not in Specification)

**v0.3.0 - Custom Templates**:
- User-provided template files
- `custom_template_path` parameter in `build_model`
- Template validation and caching

**v0.4.0 - Template Merging**:
- Combine multiple templates
- Custom template creation tools
- Template subset extraction

**v0.5.0 - Dynamic Template Updates**:
- Hot-reload templates without server restart
- Template version management
- Automatic template downloads

## Related Specifications

- **001-system-overview.md**: Overall architecture
- **004-build-model-tool.md**: Template usage in model building
- **015-mcp-server-setup.md**: Server startup procedures
- **002-data-formats.md**: Model data format created from templates

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 018-session-management-tools.md
