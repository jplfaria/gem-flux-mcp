# Additional MCP Tools for Metabolic Modeling

**Purpose**: Specification of additional MCP tools beyond the MVP for the Gem-Flux MCP server.

**MVP Tools** (must-have for v0.1.0):
1. `build_media` - Build media from compound list
2. `build_model` - Build model from protein sequences
3. `gapfill_model` - Gapfill model in specified media
4. `run_fba` - Run flux balance analysis

**Additional Tools** (future enhancements):
This document outlines tools to add after MVP is complete.

---

## Category 1: Model I/O and Persistence

### import_model_json
**Purpose**: Import a model from COBRApy JSON format

```python
@mcp.tool()
def import_model_json(json_string: str) -> dict:
    """Import a metabolic model from JSON format.

    Args:
        json_string: Model in COBRApy JSON format

    Returns:
        {
            "model_id": str,
            "name": str,
            "num_reactions": int,
            "num_metabolites": int,
            "num_genes": int,
            "objective": str
        }
    """
```

**Use case**: Users can import existing models from other tools

### export_model_json
**Purpose**: Export a model to COBRApy JSON format

```python
@mcp.tool()
def export_model_json(model_id: str) -> dict:
    """Export a metabolic model to JSON format.

    Args:
        model_id: ID of model to export

    Returns:
        {
            "json_string": str,  # Complete model in JSON format
            "size_kb": float,
            "reactions": int,
            "metabolites": int
        }
    """
```

**Use case**: Users can export models for use in other tools (Escher, MATLAB, etc.)

### save_model
**Purpose**: Persist a model to server storage

```python
@mcp.tool()
def save_model(model_id: str, name: str, description: str = None) -> dict:
    """Save a model to persistent storage.

    Args:
        model_id: ID of model in current session
        name: Human-readable name for saved model
        description: Optional description

    Returns:
        {
            "saved_model_id": str,
            "path": str,
            "timestamp": str
        }
    """
```

**Use case**: Users can save models between sessions

### list_saved_models
**Purpose**: List all saved models

```python
@mcp.tool()
def list_saved_models(limit: int = 50) -> list[dict]:
    """List all saved models.

    Args:
        limit: Maximum number of models to return

    Returns:
        List of saved models with metadata
    """
```

---

## Category 2: Batch Operations

### batch_build_models
**Purpose**: Build multiple models in parallel

```python
@mcp.tool()
def batch_build_models(
    genomes: list[dict],
    template: str = "GramNegative"
) -> list[dict]:
    """Build multiple metabolic models in batch.

    Args:
        genomes: List of genome dictionaries with protein_ids -> sequences
        template: ModelSEED template to use

    Returns:
        List of build results with model_ids
    """
```

**Use case**: Comparative genomics, building models for multiple strains

### batch_gapfill_models
**Purpose**: Gapfill multiple models with same media

```python
@mcp.tool()
def batch_gapfill_models(
    model_ids: list[str],
    media: dict
) -> list[dict]:
    """Gapfill multiple models with the same media.

    Args:
        model_ids: List of model IDs to gapfill
        media: Media composition (compound_id -> bounds)

    Returns:
        List of gapfilling results
    """
```

**Use case**: Preparing models for comparative analysis

### batch_run_fba
**Purpose**: Run FBA on multiple models

```python
@mcp.tool()
def batch_run_fba(
    model_ids: list[str],
    media: dict,
    objective: str = "bio1"
) -> list[dict]:
    """Run FBA on multiple models with same conditions.

    Args:
        model_ids: List of model IDs
        media: Media composition
        objective: Objective reaction ID

    Returns:
        List of FBA results
    """
```

**Use case**: Compare growth rates across strains/conditions

---

## Category 3: Model Comparison and Analysis

### compare_models
**Purpose**: Compare two metabolic models

```python
@mcp.tool()
def compare_models(model_id_1: str, model_id_2: str) -> dict:
    """Compare two metabolic models.

    Args:
        model_id_1: First model ID
        model_id_2: Second model ID

    Returns:
        {
            "shared_reactions": list[str],
            "unique_to_model_1": list[str],
            "unique_to_model_2": list[str],
            "shared_metabolites": list[str],
            "reaction_overlap_percent": float,
            "metabolite_overlap_percent": float
        }
    """
```

**Use case**: Understand differences between strains or gapfilling iterations

### compare_fba_results
**Purpose**: Compare FBA results between models or conditions

```python
@mcp.tool()
def compare_fba_results(
    fba_result_ids: list[str],
    top_n: int = 20
) -> dict:
    """Compare FBA results across multiple runs.

    Args:
        fba_result_ids: List of FBA result IDs to compare
        top_n: Number of top flux differences to report

    Returns:
        {
            "growth_rates": list[float],
            "flux_correlations": dict,
            "top_flux_differences": list[dict],
            "active_pathway_differences": list[str]
        }
    """
```

**Use case**: Understand metabolic shifts under different conditions

---

## Category 4: Constraint Modification

### set_reaction_bounds
**Purpose**: Modify bounds on specific reactions

```python
@mcp.tool()
def set_reaction_bounds(
    model_id: str,
    reaction_bounds: dict[str, tuple[float, float]]
) -> dict:
    """Set bounds on reactions.

    Args:
        model_id: Model ID
        reaction_bounds: Dict of reaction_id -> (lower_bound, upper_bound)

    Returns:
        {
            "model_id": str,
            "reactions_modified": int,
            "invalid_reactions": list[str]
        }
    """
```

**Use case**: Simulate knockouts, overexpression, or pathway constraints

### knockout_reactions
**Purpose**: Knockout (disable) specific reactions

```python
@mcp.tool()
def knockout_reactions(
    model_id: str,
    reaction_ids: list[str]
) -> dict:
    """Knockout (disable) reactions by setting bounds to zero.

    Args:
        model_id: Model ID
        reaction_ids: List of reaction IDs to knockout

    Returns:
        {
            "model_id": str,
            "reactions_knocked_out": list[str],
            "growth_rate_before": float,
            "growth_rate_after": float,
            "is_lethal": bool
        }
    """
```

**Use case**: Gene essentiality prediction, metabolic engineering

### knockout_genes
**Purpose**: Knockout genes and all associated reactions

```python
@mcp.tool()
def knockout_genes(
    model_id: str,
    gene_ids: list[str]
) -> dict:
    """Knockout genes and determine effect on growth.

    Args:
        model_id: Model ID
        gene_ids: List of gene IDs to knockout

    Returns:
        {
            "model_id": str,
            "genes_knocked_out": list[str],
            "reactions_disabled": list[str],
            "growth_rate_change": float,
            "is_lethal": bool,
            "compensatory_pathways": list[str]
        }
    """
```

**Use case**: Gene essentiality, synthetic lethality prediction

### simulate_overexpression
**Purpose**: Simulate gene/reaction overexpression

```python
@mcp.tool()
def simulate_overexpression(
    model_id: str,
    reaction_ids: list[str],
    fold_change: float = 2.0
) -> dict:
    """Simulate overexpression by increasing reaction bounds.

    Args:
        model_id: Model ID
        reaction_ids: Reactions to overexpress
        fold_change: Fold increase in upper bound

    Returns:
        {
            "model_id": str,
            "reactions_modified": list[str],
            "growth_rate_change": float,
            "flux_changes": dict[str, float]
        }
    """
```

**Use case**: Metabolic engineering, production optimization

---

## Category 5: Media Optimization

### optimize_media_minimal
**Purpose**: Find minimal media for growth

```python
@mcp.tool()
def optimize_media_minimal(
    model_id: str,
    target_growth_rate: float = 0.1
) -> dict:
    """Find minimal media composition for target growth rate.

    Args:
        model_id: Model ID
        target_growth_rate: Minimum acceptable growth rate

    Returns:
        {
            "minimal_media": dict[str, float],
            "num_compounds": int,
            "achieved_growth_rate": float,
            "essential_compounds": list[str],
            "optional_compounds": list[str]
        }
    """
```

**Use case**: Design defined media, reduce media cost

### suggest_media_additions
**Purpose**: Suggest compounds to add to media for better growth

```python
@mcp.tool()
def suggest_media_additions(
    model_id: str,
    current_media: dict[str, float],
    max_suggestions: int = 10
) -> dict:
    """Suggest media additions to improve growth.

    Args:
        model_id: Model ID
        current_media: Current media composition
        max_suggestions: Max number of suggestions

    Returns:
        {
            "current_growth_rate": float,
            "suggestions": list[{
                "compound_id": str,
                "compound_name": str,
                "predicted_growth_improvement": float,
                "justification": str
            }]
        }
    """
```

**Use case**: Troubleshoot poor growth, optimize fermentation

---

## Category 6: Production Strain Design

### design_production_strain
**Purpose**: Suggest genetic modifications for metabolite production

```python
@mcp.tool()
def design_production_strain(
    model_id: str,
    target_metabolite: str,
    max_knockouts: int = 5
) -> dict:
    """Design strain for maximum metabolite production.

    Args:
        model_id: Model ID
        target_metabolite: Compound ID to produce
        max_knockouts: Maximum gene knockouts allowed

    Returns:
        {
            "target_metabolite": str,
            "target_name": str,
            "suggested_knockouts": list[str],
            "suggested_overexpressions": list[str],
            "predicted_yield": float,
            "growth_rate_impact": float,
            "required_media_changes": dict
        }
    """
```

**Use case**: Metabolic engineering, bioproduction optimization

### predict_product_envelope
**Purpose**: Calculate production envelope (growth vs production)

```python
@mcp.tool()
def predict_product_envelope(
    model_id: str,
    product_reaction: str,
    num_points: int = 20
) -> dict:
    """Calculate production envelope relating growth to production.

    Args:
        model_id: Model ID
        product_reaction: Reaction producing target metabolite
        num_points: Number of points on envelope

    Returns:
        {
            "envelope_points": list[{
                "growth_rate": float,
                "production_rate": float
            }],
            "max_theoretical_yield": float,
            "growth_coupled_production": bool
        }
    """
```

**Use case**: Evaluate production potential, design coupled systems

---

## Category 7: Pathway Analysis

### find_pathways
**Purpose**: Find metabolic pathways between compounds

```python
@mcp.tool()
def find_pathways(
    model_id: str,
    source_metabolite: str,
    target_metabolite: str,
    max_length: int = 10
) -> dict:
    """Find metabolic pathways connecting two metabolites.

    Args:
        model_id: Model ID
        source_metabolite: Starting compound ID
        target_metabolite: Target compound ID
        max_length: Maximum pathway length

    Returns:
        {
            "pathways": list[{
                "reactions": list[str],
                "length": int,
                "is_active": bool,
                "flux_capacity": float
            }],
            "shortest_pathway": dict,
            "highest_flux_pathway": dict
        }
    """
```

**Use case**: Pathway engineering, understanding metabolism

### identify_bottlenecks
**Purpose**: Identify flux bottlenecks in active pathways

```python
@mcp.tool()
def identify_bottlenecks(
    model_id: str,
    pathway_reactions: list[str]
) -> dict:
    """Identify flux bottlenecks in a pathway.

    Args:
        model_id: Model ID
        pathway_reactions: List of reactions in pathway

    Returns:
        {
            "bottleneck_reactions": list[{
                "reaction_id": str,
                "current_flux": float,
                "max_possible_flux": float,
                "improvement_potential": float
            }],
            "suggested_modifications": list[str]
        }
    """
```

**Use case**: Optimize engineered pathways, increase production

---

## Category 8: Visualization Data Preparation

**Note**: Actual visualization will be deferred, but we can provide data for external viz tools.

### get_escher_map_data
**Purpose**: Prepare data for Escher visualization

```python
@mcp.tool()
def get_escher_map_data(
    model_id: str,
    fba_result_id: str = None,
    pathway: str = None
) -> dict:
    """Get data formatted for Escher map visualization.

    Args:
        model_id: Model ID
        fba_result_id: Optional FBA result to overlay fluxes
        pathway: Optional pathway to highlight (e.g., "Glycolysis")

    Returns:
        {
            "model_json": str,  # For Escher
            "reaction_data": dict[str, float],  # Fluxes to display
            "metabolite_data": dict[str, float],  # Concentrations
            "suggested_map": str  # Escher map name
        }
    """
```

**Use case**: Users can visualize in Escher web app

### export_cytoscape_network
**Purpose**: Export network for Cytoscape visualization

```python
@mcp.tool()
def export_cytoscape_network(
    model_id: str,
    include_genes: bool = True
) -> dict:
    """Export metabolic network for Cytoscape.

    Args:
        model_id: Model ID
        include_genes: Include gene-reaction associations

    Returns:
        {
            "nodes": list[dict],  # Metabolites and reactions
            "edges": list[dict],  # Connections
            "format": "cytoscape_json"
        }
    """
```

**Use case**: Network analysis in Cytoscape

---

## Implementation Priority

### Phase 1 (MVP) - v0.1.0
- ✅ build_media
- ✅ build_model
- ✅ gapfill_model
- ✅ run_fba

### Phase 2 (Core Expansion) - v0.2.0
1. import_model_json / export_model_json
2. save_model / list_saved_models
3. set_reaction_bounds
4. knockout_reactions
5. get_compound_name / get_reaction_name (from ModelSEED DB)

### Phase 3 (Analysis) - v0.3.0
1. compare_models
2. batch_run_fba
3. optimize_media_minimal
4. find_pathways
5. knockout_genes

### Phase 4 (Production Optimization) - v0.4.0
1. design_production_strain
2. predict_product_envelope
3. simulate_overexpression
4. identify_bottlenecks
5. suggest_media_additions

### Phase 5 (Advanced Features) - v0.5.0
1. batch_build_models
2. batch_gapfill_models
3. compare_fba_results
4. get_escher_map_data
5. export_cytoscape_network

---

## Design Considerations

### Rate Limiting

Some operations are computationally expensive:
- Batch operations: Limit to 100 models
- Pathway finding: Limit to 10,000 paths
- FVA: Can be slow, consider async

### Caching

Cache expensive computations:
- FBA results
- Gapfilling solutions
- Pathway enumeration
- Model comparisons

### Async Operations

Consider async for:
- Batch model building
- Long gapfilling runs
- Extensive knockout screens
- Production envelope calculation

### Error Handling

All tools should return structured errors:
```python
{
    "success": False,
    "error_type": "InfeasibleModel",
    "message": "Model cannot grow in specified media",
    "suggestions": [
        "Check media composition",
        "Run gapfilling",
        "Verify reaction bounds"
    ]
}
```

---

## Summary

This document outlines **34 additional MCP tools** beyond the MVP, organized into 8 categories:

1. **Model I/O** (4 tools) - Import, export, save, list
2. **Batch Operations** (3 tools) - Build, gapfill, FBA in batch
3. **Model Comparison** (2 tools) - Compare models and results
4. **Constraint Modification** (4 tools) - Knockouts, bounds, overexpression
5. **Media Optimization** (2 tools) - Minimal media, suggestions
6. **Production Strain Design** (2 tools) - Strain design, envelopes
7. **Pathway Analysis** (2 tools) - Find pathways, identify bottlenecks
8. **Visualization Data** (2 tools) - Escher, Cytoscape export

**Implementation Strategy**:
- Start with MVP (4 tools)
- Add tools incrementally based on user feedback
- Prioritize most requested features
- Consider async/batch operations for scalability

These additional tools will make Gem-Flux MCP a comprehensive platform for metabolic modeling and strain design.
