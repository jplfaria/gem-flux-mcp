# Future Tools Roadmap - Gem-Flux MCP Server

**Type**: Roadmap Specification
**Status**: Phase 6 - Post-MVP Planning
**Version**: v0.2.0 through v0.5.0

## Purpose

This specification outlines the planned expansion of the Gem-Flux MCP Server beyond the MVP (v0.1.0). It defines 34 additional MCP tools organized into 8 functional categories, with a phased implementation strategy based on user value and technical dependencies.

## Core Philosophy

**Incremental Enhancement**: Each phase builds on previous capabilities while maintaining the core principle that Gem-Flux is a tool integration server, not an AI reasoning system.

**User-Driven Priorities**: Implementation order prioritizes tools that:
- Enable common metabolic engineering workflows
- Reduce friction in AI-assisted analysis
- Support batch operations for efficiency
- Provide data export for external visualization

## Post-MVP Tool Categories

### Category 1: Model I/O and Persistence (4 tools)

**Purpose**: Enable model portability, persistence, and integration with external tools.

#### import_model_json

Import a metabolic model from COBRApy JSON format.

**Input Parameters**:
```python
{
    "json_string": str,  # Complete model in COBRApy JSON format
    "validate": bool     # Optional, default True - validate model consistency
}
```

**Output Structure**:
```python
{
    "success": true,
    "model_id": "model_imported_001",
    "name": "iJO1366",
    "num_reactions": 2583,
    "num_metabolites": 1805,
    "num_genes": 1367,
    "objective": "BIOMASS_Ec_iJO1366_core_53p95M",
    "validation_results": {
        "mass_balanced": true,
        "charge_balanced": true,
        "dead_end_metabolites": 12,
        "orphan_reactions": 0
    }
}
```

**Behavior**:
1. Parse JSON string into COBRApy Model object
2. Validate model structure (reactions, metabolites, stoichiometry)
3. Check mass and charge balance if validate=True
4. Generate unique model_id and store in session
5. Return model metadata and validation summary

**Error Conditions**:
- Invalid JSON format → 400 error with parsing details
- Missing required fields → 400 error listing missing fields
- Stoichiometric inconsistencies → 422 error with validation failures

**Use Cases**:
- Import published models (BiGG, AGORA, etc.)
- Load previously exported models
- Integration with MATLAB COBRA models
- Testing gapfilling on known models

---

#### export_model_json

Export a metabolic model to COBRApy JSON format.

**Input Parameters**:
```python
{
    "model_id": str,              # ID of model to export
    "include_solutions": bool,    # Optional, include FBA results if available
    "pretty_print": bool          # Optional, format JSON for readability
}
```

**Output Structure**:
```python
{
    "success": true,
    "json_string": "{ ... }",     # Complete model in COBRApy JSON
    "size_kb": 423.5,
    "num_reactions": 2583,
    "num_metabolites": 1805,
    "format_version": "1.0"
}
```

**Behavior**:
1. Retrieve model from session by model_id
2. Serialize to COBRApy JSON format using model.to_json()
3. Optionally include FBA solution data
4. Format JSON (compact or pretty-printed)
5. Return JSON string with metadata

**Error Conditions**:
- Model not found → 404 error
- Serialization failure → 500 error

**Use Cases**:
- Export for visualization in Escher
- Save models for later import
- Share models with collaborators
- Integration with MATLAB COBRA Toolbox

---

#### save_model

Persist a model to server storage for future sessions.

**Input Parameters**:
```python
{
    "model_id": str,           # Session model ID to save
    "name": str,               # Human-readable name for saved model
    "description": str,        # Optional description
    "tags": list[str]          # Optional tags for organization
}
```

**Output Structure**:
```python
{
    "success": true,
    "saved_model_id": "saved_ecoli_glucose_001",
    "path": "/models/saved_ecoli_glucose_001.json",
    "timestamp": "2025-10-27T15:30:00Z",
    "size_kb": 423.5
}
```

**Behavior**:
1. Retrieve model from current session
2. Generate unique saved_model_id
3. Write model to persistent storage (JSON file)
4. Store metadata (name, description, tags, timestamp)
5. Return save confirmation with file path

**Error Conditions**:
- Model not found in session → 404 error
- Disk write failure → 500 error with details
- Duplicate name → 409 error suggesting alternative

**Use Cases**:
- Save gapfilled models for reuse
- Persist models between AI assistant sessions
- Build model library for comparative analysis

**Implementation Notes**:
- MVP uses file system storage (JSON files)
- Future: Database backend for metadata queries
- Consider storage quotas and cleanup policies

---

#### list_saved_models

List all saved models with metadata.

**Input Parameters**:
```python
{
    "limit": int,              # Optional, max results (default 50)
    "offset": int,             # Optional, for pagination (default 0)
    "tags": list[str],         # Optional, filter by tags
    "sort_by": str             # Optional, "name"|"date"|"size" (default "date")
}
```

**Output Structure**:
```python
{
    "success": true,
    "models": [
        {
            "saved_model_id": "saved_ecoli_glucose_001",
            "name": "E. coli on glucose minimal media",
            "description": "Gapfilled for aerobic glucose growth",
            "tags": ["ecoli", "glucose", "gapfilled"],
            "timestamp": "2025-10-27T15:30:00Z",
            "size_kb": 423.5,
            "num_reactions": 2583,
            "num_metabolites": 1805
        }
    ],
    "total_count": 127,
    "has_more": true
}
```

**Behavior**:
1. Query saved model metadata storage
2. Apply filters (tags, date range)
3. Sort results by specified criteria
4. Paginate results based on limit/offset
5. Return model list with metadata

**Error Conditions**:
- Invalid sort criteria → 400 error
- Storage access failure → 500 error

**Use Cases**:
- Browse available models
- Find previously saved models by tag
- Manage model storage

---

### Category 2: Batch Operations (3 tools)

**Purpose**: Enable parallel analysis of multiple models or conditions for comparative studies.

#### batch_build_models

Build multiple metabolic models in parallel from different genomes.

**Input Parameters**:
```python
{
    "genomes": [
        {
            "genome_id": "strain_001",
            "protein_sequences": { "prot1": "MKLL...", ... },
            "template": "GramNegative"
        },
        {
            "genome_id": "strain_002",
            "protein_sequences": { "prot1": "MVAL...", ... },
            "template": "GramNegative"
        }
    ],
    "parallel": bool  # Optional, default True - build in parallel
}
```

**Output Structure**:
```python
{
    "success": true,
    "models": [
        {
            "genome_id": "strain_001",
            "model_id": "model_001",
            "num_reactions": 1247,
            "build_time_seconds": 23.4
        },
        {
            "genome_id": "strain_002",
            "model_id": "model_002",
            "num_reactions": 1198,
            "build_time_seconds": 22.1
        }
    ],
    "total_build_time": 23.4,  # Parallel execution
    "failures": []
}
```

**Behavior**:
1. Validate all genome inputs
2. Build models in parallel (if parallel=True) or sequentially
3. Track each model's build status
4. Return list of model_ids with build statistics
5. Report any failures with error details

**Error Conditions**:
- Any genome validation failure → partial success with failures list
- Too many genomes (>100) → 400 error suggesting smaller batches

**Use Cases**:
- Comparative genomics studies
- Build models for multiple strains
- Pan-genome analysis
- Outbreak investigation (multiple pathogen strains)

**Performance Notes**:
- Limit: 100 genomes per batch
- Parallel execution uses process pool
- Consider memory constraints for large batches

---

#### batch_gapfill_models

Gapfill multiple models with the same media conditions.

**Input Parameters**:
```python
{
    "model_ids": list[str],
    "media_id": str,
    "target_growth": float,     # Optional, default 0.1
    "parallel": bool            # Optional, default True
}
```

**Output Structure**:
```python
{
    "success": true,
    "results": [
        {
            "model_id": "model_001",
            "gapfilled_model_id": "model_001_gapfilled",
            "reactions_added": 23,
            "growth_rate_before": 0.0,
            "growth_rate_after": 0.874,
            "gapfill_time_seconds": 45.2
        },
        {
            "model_id": "model_002",
            "gapfilled_model_id": "model_002_gapfilled",
            "reactions_added": 31,
            "growth_rate_before": 0.0,
            "growth_rate_after": 0.821,
            "gapfill_time_seconds": 52.3
        }
    ],
    "total_time_seconds": 52.3,
    "failures": []
}
```

**Behavior**:
1. Validate all model_ids exist
2. Retrieve media conditions
3. Gapfill each model in parallel or sequentially
4. Return gapfilled model_ids with statistics
5. Report failures separately

**Error Conditions**:
- Media not found → 404 error
- Any model not found → 404 error listing missing IDs
- Infeasible gapfilling → partial success with failures

**Use Cases**:
- Prepare multiple strain models for comparison
- Test media compatibility across strains
- Standardize model capabilities

---

#### batch_run_fba

Run FBA on multiple models with the same conditions.

**Input Parameters**:
```python
{
    "model_ids": list[str],
    "media_id": str,
    "objective": str,           # Optional, default "bio1"
    "parallel": bool            # Optional, default True
}
```

**Output Structure**:
```python
{
    "success": true,
    "results": [
        {
            "model_id": "model_001",
            "objective_value": 0.874,
            "status": "optimal",
            "solve_time_seconds": 0.23
        },
        {
            "model_id": "model_002",
            "objective_value": 0.821,
            "status": "optimal",
            "solve_time_seconds": 0.19
        }
    ],
    "comparison": {
        "mean_growth_rate": 0.8475,
        "std_growth_rate": 0.0265,
        "range": [0.821, 0.874]
    },
    "failures": []
}
```

**Behavior**:
1. Validate all inputs
2. Run FBA on each model in parallel
3. Collect growth rates and solve statistics
4. Compute comparison statistics
5. Return results with summary

**Error Conditions**:
- Any model/media not found → 404 error
- Solver failures → partial success with failures list

**Use Cases**:
- Compare growth rates across strains
- Screen models for media compatibility
- Identify growth differences

---

### Category 3: Model Comparison and Analysis (2 tools)

**Purpose**: Understand differences between models and identify unique metabolic capabilities.

#### compare_models

Compare reaction and metabolite content between two models.

**Input Parameters**:
```python
{
    "model_id_1": str,
    "model_id_2": str,
    "include_genes": bool  # Optional, default False
}
```

**Output Structure**:
```python
{
    "success": true,
    "model_1_name": "E. coli K-12 MG1655",
    "model_2_name": "E. coli O157:H7",
    "reactions": {
        "shared": ["rxn00001", "rxn00002", ...],
        "unique_to_model_1": ["rxn12345", ...],
        "unique_to_model_2": ["rxn67890", ...],
        "overlap_percent": 87.3
    },
    "metabolites": {
        "shared": ["cpd00001", "cpd00027", ...],
        "unique_to_model_1": ["cpd12345", ...],
        "unique_to_model_2": ["cpd67890", ...],
        "overlap_percent": 91.2
    },
    "summary": {
        "total_reactions_1": 2583,
        "total_reactions_2": 2714,
        "total_metabolites_1": 1805,
        "total_metabolites_2": 1873,
        "similarity_score": 0.89
    }
}
```

**Behavior**:
1. Retrieve both models from session
2. Extract reaction and metabolite IDs
3. Compute set intersections and differences
4. Calculate overlap percentages
5. Optionally compare gene content
6. Return detailed comparison

**Error Conditions**:
- Either model not found → 404 error
- Models incompatible (different namespaces) → warning

**Use Cases**:
- Understand strain differences
- Compare gapfilling iterations
- Identify unique metabolic capabilities
- Validate model merges

---

#### compare_fba_results

Compare flux distributions across multiple FBA runs.

**Input Parameters**:
```python
{
    "fba_result_ids": list[str],  # Previously run FBA results
    "top_n": int                   # Optional, top N flux differences (default 20)
}
```

**Output Structure**:
```python
{
    "success": true,
    "growth_rates": [0.874, 0.821, 0.902],
    "correlations": {
        "result_1_vs_result_2": 0.87,
        "result_1_vs_result_3": 0.76,
        "result_2_vs_result_3": 0.82
    },
    "top_flux_differences": [
        {
            "reaction_id": "rxn00001",
            "reaction_name": "Glucose exchange",
            "fluxes": [-5.0, -3.2, -6.1],
            "variance": 2.1,
            "coefficient_of_variation": 0.43
        }
    ],
    "pathway_differences": [
        {
            "pathway": "Glycolysis",
            "mean_flux_change": 1.23,
            "affected_reactions": ["rxn00001", "rxn00002"]
        }
    ]
}
```

**Behavior**:
1. Retrieve all FBA result objects
2. Extract flux distributions for each
3. Compute pairwise correlations
4. Identify reactions with largest variance
5. Group by metabolic pathways
6. Return ranked differences

**Error Conditions**:
- Any result not found → 404 error
- Incompatible result formats → 400 error

**Use Cases**:
- Understand metabolic shifts across conditions
- Compare wild-type vs engineered strain fluxes
- Identify condition-specific pathway usage
- Validate model predictions

---

### Category 4: Constraint Modification (4 tools)

**Purpose**: Enable in silico genetic and regulatory manipulations.

#### set_reaction_bounds

Modify flux bounds on specific reactions.

**Input Parameters**:
```python
{
    "model_id": str,
    "reaction_bounds": {
        "rxn00001": (-10, 10),   # (lower_bound, upper_bound)
        "rxn00002": (0, 100),    # Force forward only
        "rxn00003": (0, 0)       # Knockout
    }
}
```

**Output Structure**:
```python
{
    "success": true,
    "model_id": "model_001_modified",  # New model with modified bounds
    "reactions_modified": 3,
    "modifications": [
        {
            "reaction_id": "rxn00001",
            "old_bounds": (-1000, 1000),
            "new_bounds": (-10, 10)
        }
    ],
    "invalid_reactions": []
}
```

**Behavior**:
1. Validate all reaction IDs exist in model
2. Create copy of model (preserve original)
3. Apply bound changes to reactions
4. Validate bounds (lower <= upper)
5. Return new model_id with modification summary

**Error Conditions**:
- Invalid reaction IDs → 400 error listing invalid IDs
- Invalid bounds (lower > upper) → 400 error
- Model not found → 404 error

**Use Cases**:
- Simulate gene knockouts (set bounds to 0)
- Limit uptake rates (constrain exchange reactions)
- Force pathway usage (set lower bound > 0)
- Simulate overexpression (increase upper bound)

---

#### knockout_reactions

Knockout specific reactions by setting bounds to zero.

**Input Parameters**:
```python
{
    "model_id": str,
    "reaction_ids": list[str],
    "test_growth": bool  # Optional, run FBA after knockout (default True)
}
```

**Output Structure**:
```python
{
    "success": true,
    "model_id": "model_001_knockout",
    "reactions_knocked_out": ["rxn00001", "rxn00002"],
    "growth_rate_before": 0.874,
    "growth_rate_after": 0.423,
    "is_lethal": false,
    "growth_impact": -0.451,
    "growth_impact_percent": -51.6
}
```

**Behavior**:
1. Create copy of model
2. Set specified reaction bounds to (0, 0)
3. If test_growth=True, run FBA before and after
4. Determine if knockout is lethal (growth < 0.01)
5. Return knockout results with growth impact

**Error Conditions**:
- Invalid reaction IDs → 400 error
- Model not found → 404 error
- FBA failure → include in result with status

**Use Cases**:
- Predict gene essentiality
- Test metabolic robustness
- Identify alternative pathways
- Metabolic engineering design

---

#### knockout_genes

Knockout genes and all associated reactions via GPR rules.

**Input Parameters**:
```python
{
    "model_id": str,
    "gene_ids": list[str],
    "test_growth": bool  # Optional, default True
}
```

**Output Structure**:
```python
{
    "success": true,
    "model_id": "model_001_gene_knockout",
    "genes_knocked_out": ["b0001", "b0002"],
    "reactions_disabled": ["rxn00001", "rxn00003"],
    "reactions_partial": ["rxn00005"],  # Still active via isozymes
    "growth_rate_before": 0.874,
    "growth_rate_after": 0.0,
    "is_lethal": true,
    "compensatory_pathways": []  # Identified if growth > 0
}
```

**Behavior**:
1. Create copy of model
2. For each gene, evaluate GPR rules for all reactions
3. Disable reactions where GPR evaluates to False
4. Identify partially affected reactions (isozymes)
5. Run FBA to test growth impact
6. Identify compensatory pathways if non-lethal

**Error Conditions**:
- Invalid gene IDs → 400 error listing invalid genes
- Model has no GPR rules → 422 error suggesting reaction knockout
- Model not found → 404 error

**Use Cases**:
- Gene essentiality prediction
- Synthetic lethality analysis
- Identify isozyme redundancy
- Metabolic engineering target identification

**Implementation Notes**:
- Requires models with gene-protein-reaction (GPR) associations
- Uses COBRApy's `knock_out_model_genes()` functionality
- Respects AND/OR logic in GPR rules

---

#### simulate_overexpression

Simulate gene/reaction overexpression by increasing flux capacity.

**Input Parameters**:
```python
{
    "model_id": str,
    "reaction_ids": list[str],
    "fold_change": float,  # Multiplier for upper bound (e.g., 2.0 = 2x)
    "test_growth": bool    # Optional, default True
}
```

**Output Structure**:
```python
{
    "success": true,
    "model_id": "model_001_overexpressed",
    "reactions_modified": ["rxn00001", "rxn00002"],
    "fold_change": 2.0,
    "growth_rate_before": 0.874,
    "growth_rate_after": 0.921,
    "growth_improvement": 0.047,
    "flux_changes": {
        "rxn00001": {"before": 5.2, "after": 8.3},
        "rxn00002": {"before": 3.1, "after": 3.8}
    }
}
```

**Behavior**:
1. Create copy of model
2. Multiply upper bounds of specified reactions by fold_change
3. If bidirectional, multiply lower bound by fold_change (maintaining sign)
4. Run FBA to measure impact on growth and fluxes
5. Return flux changes for overexpressed reactions

**Error Conditions**:
- Invalid reaction IDs → 400 error
- Invalid fold_change (≤ 0) → 400 error
- Model not found → 404 error

**Use Cases**:
- Metabolic engineering: predict overexpression benefit
- Identify rate-limiting steps
- Optimize production pathways
- Test pathway capacity

---

### Category 5: Media Optimization (2 tools)

**Purpose**: Design and optimize growth media for specific objectives.

#### optimize_media_minimal

Find the minimal set of nutrients required for growth.

**Input Parameters**:
```python
{
    "model_id": str,
    "target_growth_rate": float,  # Minimum acceptable growth
    "starting_media_id": str,     # Optional, start from existing media
    "max_compounds": int          # Optional, maximum media complexity
}
```

**Output Structure**:
```python
{
    "success": true,
    "minimal_media": {
        "cpd00027": (-5, 100),    # Glucose
        "cpd00007": (-10, 100),   # O2
        "cpd00001": (-10, 100),   # H2O
        "cpd00009": (-10, 100)    # Phosphate
        # ... 8 more compounds
    },
    "num_compounds": 12,
    "achieved_growth_rate": 0.102,
    "target_growth_rate": 0.1,
    "essential_compounds": ["cpd00027", "cpd00007", "cpd00009", ...],
    "optimization_method": "iterative_removal"
}
```

**Behavior**:
1. Start with complete or starting media
2. Iteratively remove compounds and test growth
3. Keep compounds where removal causes growth < target
4. Return minimal media composition
5. Identify strictly essential vs. growth-enhancing compounds

**Error Conditions**:
- Model cannot achieve target growth → 422 error with max achievable
- Model not found → 404 error
- Infeasible optimization → 500 error

**Use Cases**:
- Design defined minimal media
- Reduce media cost for fermentation
- Identify auxotrophies
- Experimental media design

**Implementation Notes**:
- Uses iterative deletion or MILP optimization
- Can start from rich media and simplify
- Reports both essential and beneficial compounds

---

#### suggest_media_additions

Suggest nutrients to add for improved growth.

**Input Parameters**:
```python
{
    "model_id": str,
    "current_media_id": str,
    "max_suggestions": int  # Optional, default 10
}
```

**Output Structure**:
```python
{
    "success": true,
    "current_growth_rate": 0.234,
    "suggestions": [
        {
            "compound_id": "cpd00048",
            "compound_name": "Sulfate",
            "predicted_growth_improvement": 0.145,
            "predicted_growth_rate": 0.379,
            "justification": "Enables sulfur assimilation pathway",
            "priority": "high"
        },
        {
            "compound_id": "cpd00063",
            "compound_name": "L-Cysteine",
            "predicted_growth_improvement": 0.087,
            "predicted_growth_rate": 0.321,
            "justification": "Bypasses blocked sulfate reduction",
            "priority": "medium"
        }
    ],
    "blocked_pathways": ["Sulfate reduction", "Cysteine biosynthesis"]
}
```

**Behavior**:
1. Run FBA with current media to get baseline growth
2. Test addition of each missing nutrient individually
3. Rank by predicted growth improvement
4. Identify blocked pathways that would be enabled
5. Return top suggestions with justifications

**Error Conditions**:
- Model or media not found → 404 error
- Model already at maximum growth → 200 with empty suggestions

**Use Cases**:
- Troubleshoot poor growth predictions
- Identify limiting nutrients
- Optimize fermentation media
- Understand auxotrophies

---

### Category 6: Production Strain Design (2 tools)

**Purpose**: Design engineered strains for metabolite production.

#### design_production_strain

Suggest genetic modifications to maximize metabolite production.

**Input Parameters**:
```python
{
    "model_id": str,
    "target_metabolite": str,      # Compound ID to produce
    "media_id": str,
    "max_knockouts": int,          # Optional, default 5
    "min_growth_rate": float,      # Optional, minimum viable growth (default 0.05)
    "algorithm": str               # Optional, "optknock"|"robustknock" (default "optknock")
}
```

**Output Structure**:
```python
{
    "success": true,
    "target_metabolite": "cpd00020",
    "target_name": "Pyruvate",
    "design": {
        "knockouts": ["b0001", "b0002", "b0003"],
        "overexpressions": ["b1234"],
        "reaction_bounds": {
            "rxn00001": (0, 5)  # Limit glucose uptake
        }
    },
    "predictions": {
        "production_rate": 12.3,      # mmol/gDW/h
        "yield": 0.45,                # mol product / mol substrate
        "growth_rate": 0.08,          # hr^-1
        "growth_coupled": true        # Production requires growth
    },
    "required_media_changes": {
        "cpd00027": (-5, 100)  # Limit glucose to force efficiency
    },
    "algorithm_details": {
        "method": "OptKnock",
        "iterations": 453,
        "solve_time_seconds": 123.4
    }
}
```

**Behavior**:
1. Validate target metabolite exists in model
2. Ensure exchange reaction exists or create it
3. Run strain design algorithm (OptKnock, RobustKnock, etc.)
4. Identify gene knockout combinations
5. Test growth-coupling of production
6. Suggest complementary modifications (overexpression, media)
7. Return design with predictions

**Error Conditions**:
- Target metabolite not in model → 404 error
- No viable design found → 422 error with analysis
- Model or media not found → 404 error
- Algorithm timeout → 408 error with partial results

**Use Cases**:
- Design strains for bioproduction
- Identify metabolic engineering targets
- Optimize yield and productivity
- Create growth-coupled production systems

**Implementation Notes**:
- OptKnock: Bi-level optimization (computationally expensive)
- May require external solver (Gurobi, CPLEX)
- Consider timeout limits (5-10 minutes)
- Provide simplified heuristic fallback

---

#### predict_product_envelope

Calculate production envelope relating growth rate to production rate.

**Input Parameters**:
```python
{
    "model_id": str,
    "product_reaction": str,  # Exchange or sink reaction for product
    "media_id": str,
    "num_points": int         # Optional, envelope resolution (default 20)
}
```

**Output Structure**:
```python
{
    "success": true,
    "product_name": "Pyruvate",
    "envelope_points": [
        {"growth_rate": 0.0, "production_rate": 15.3},
        {"growth_rate": 0.1, "production_rate": 14.2},
        {"growth_rate": 0.2, "production_rate": 12.8},
        # ... 17 more points
        {"growth_rate": 0.87, "production_rate": 0.0}
    ],
    "max_theoretical_yield": 15.3,      # At zero growth
    "max_growth_rate": 0.874,           # Zero production
    "growth_coupled_production": false,  # Production possible at zero growth
    "optimal_operating_point": {
        "growth_rate": 0.4,
        "production_rate": 8.7,
        "yield": 0.32
    }
}
```

**Behavior**:
1. Fix objective to maximize product exchange reaction
2. Iteratively constrain growth rate from 0 to maximum
3. At each growth rate, maximize production
4. Collect (growth, production) points
5. Determine if production is growth-coupled
6. Identify Pareto-optimal operating points
7. Return envelope with recommendations

**Error Conditions**:
- Product reaction not found → 404 error
- Model or media not found → 404 error
- Infeasible envelope → 422 error

**Use Cases**:
- Evaluate production potential
- Determine growth-coupling
- Identify optimal operating conditions
- Compare wild-type vs engineered strain envelopes

**Implementation Notes**:
- Uses COBRApy's production envelope functionality
- Computationally fast (20 FBA solves)
- Visualize externally (plot growth vs production)

---

### Category 7: Pathway Analysis (2 tools)

**Purpose**: Understand and optimize metabolic pathways.

#### find_pathways

Find metabolic pathways connecting two metabolites.

**Input Parameters**:
```python
{
    "model_id": str,
    "source_metabolite": str,  # Starting compound ID
    "target_metabolite": str,  # Ending compound ID
    "max_length": int,         # Optional, max reactions in path (default 10)
    "max_paths": int           # Optional, max paths to return (default 10)
}
```

**Output Structure**:
```python
{
    "success": true,
    "source_name": "D-Glucose",
    "target_name": "Pyruvate",
    "pathways": [
        {
            "pathway_id": "path_001",
            "reactions": ["rxn00001", "rxn00002", "rxn00003"],
            "reaction_names": ["Glucose exchange", "Hexokinase", "Phosphoglucose isomerase"],
            "length": 3,
            "is_active": true,           # Active in current FBA solution
            "flux_capacity": 10.5,       # Maximum flux through pathway
            "intermediates": ["cpd00027", "cpd00031", "cpd00236"]
        }
    ],
    "shortest_pathway": "path_001",
    "highest_flux_pathway": "path_003",
    "num_pathways_found": 7
}
```

**Behavior**:
1. Use graph search (BFS/DFS) to find reaction paths
2. Filter paths by maximum length
3. Test flux capacity of each pathway using FBA
4. Identify which pathways are active in baseline FBA
5. Rank by length and flux capacity
6. Return top pathways with annotations

**Error Conditions**:
- Metabolites not found → 404 error
- No pathways exist → 200 with empty pathways list
- Max_length too large (>20) → 400 error suggesting smaller value
- Model not found → 404 error

**Use Cases**:
- Identify production pathways
- Find alternative routes
- Understand flux distribution
- Pathway engineering design

**Implementation Notes**:
- Computationally expensive for large networks
- Consider caching results
- May need timeout for complex graphs

---

#### identify_bottlenecks

Identify flux bottlenecks in metabolic pathways.

**Input Parameters**:
```python
{
    "model_id": str,
    "pathway_reactions": list[str],  # Reactions in pathway of interest
    "media_id": str,
    "fba_result_id": str             # Optional, use specific FBA solution
}
```

**Output Structure**:
```python
{
    "success": true,
    "pathway_name": "Glycolysis",  # If recognizable
    "total_pathway_flux": 8.3,
    "bottleneck_reactions": [
        {
            "reaction_id": "rxn00002",
            "reaction_name": "Phosphofructokinase",
            "current_flux": 8.3,
            "max_possible_flux": 12.7,      # From flux variability analysis
            "min_possible_flux": 5.1,
            "improvement_potential": 4.4,   # mmol/gDW/h
            "is_constrained_by": "Upper bound",
            "suggestions": [
                "Increase reaction upper bound",
                "Overexpress associated genes"
            ]
        }
    ],
    "limiting_factor": "Enzyme capacity",
    "suggested_modifications": [
        "Overexpress pfkA gene",
        "Increase phosphofructokinase upper bound to 15"
    ]
}
```

**Behavior**:
1. Run FBA to get baseline fluxes
2. Run flux variability analysis (FVA) for pathway reactions
3. Identify reactions operating near bounds
4. Identify reactions with low flux variability
5. Calculate improvement potential for each reaction
6. Suggest genetic or constraint modifications
7. Return ranked bottleneck list

**Error Conditions**:
- Invalid reaction IDs → 400 error
- Model or media not found → 404 error
- FVA computation failure → 500 error

**Use Cases**:
- Optimize engineered pathways
- Increase production rates
- Identify rate-limiting steps
- Target metabolic engineering efforts

**Implementation Notes**:
- Uses COBRApy's flux_variability_analysis()
- FVA can be slow for large models
- Consider caching FVA results

---

### Category 8: Visualization Data Preparation (2 tools)

**Purpose**: Export data for external visualization tools (Escher, Cytoscape).

#### get_escher_map_data

Prepare model and flux data for Escher visualization.

**Input Parameters**:
```python
{
    "model_id": str,
    "fba_result_id": str,  # Optional, overlay flux data
    "pathway": str         # Optional, suggest map (e.g., "Glycolysis")
}
```

**Output Structure**:
```python
{
    "success": true,
    "model_json": "{ ... }",           # COBRApy JSON for Escher
    "reaction_data": {                  # Flux values to overlay
        "rxn00001": 8.3,
        "rxn00002": 7.2,
        # ...
    },
    "metabolite_data": {},              # Future: metabolite levels
    "suggested_map": "iJO1366.Central metabolism",
    "escher_url": "https://escher.github.io/builder/",
    "usage_instructions": "Load model JSON and select map '{}'"
}
```

**Behavior**:
1. Export model to COBRApy JSON format
2. If FBA provided, extract flux values
3. Format flux data for Escher overlay
4. Suggest Escher map based on pathway or organism
5. Return data bundle with instructions

**Error Conditions**:
- Model not found → 404 error
- FBA result not found → 404 warning, proceed without fluxes
- Export failure → 500 error

**Use Cases**:
- Visualize flux distributions
- Explore metabolic maps interactively
- Present FBA results
- Validate model predictions

**Implementation Notes**:
- Escher is web-based: provide URL and instructions
- Users load data in browser
- No server-side rendering (client-side visualization)

---

#### export_cytoscape_network

Export metabolic network for Cytoscape visualization.

**Input Parameters**:
```python
{
    "model_id": str,
    "include_genes": bool,     # Optional, default True
    "subsystem": str           # Optional, filter by subsystem/pathway
}
```

**Output Structure**:
```python
{
    "success": true,
    "format": "cytoscape_json",
    "nodes": [
        {
            "data": {
                "id": "cpd00027",
                "name": "D-Glucose",
                "type": "metabolite",
                "compartment": "c0"
            }
        },
        {
            "data": {
                "id": "rxn00001",
                "name": "Glucose exchange",
                "type": "reaction",
                "subsystem": "Transport"
            }
        }
    ],
    "edges": [
        {
            "data": {
                "source": "cpd00027",
                "target": "rxn00001",
                "stoichiometry": -1,
                "role": "substrate"
            }
        }
    ],
    "num_nodes": 3388,
    "num_edges": 7234,
    "cytoscape_version": "3.9+"
}
```

**Behavior**:
1. Extract model network structure
2. Create nodes for metabolites and reactions
3. Create edges for stoichiometric connections
4. Optionally include gene nodes with GPR edges
5. Filter by subsystem if specified
6. Format as Cytoscape JSON
7. Return network data

**Error Conditions**:
- Model not found → 404 error
- Invalid subsystem filter → 400 warning, return full network
- Export failure → 500 error

**Use Cases**:
- Network analysis (centrality, clustering)
- Visualize metabolic topology
- Identify hub metabolites
- Explore pathway connectivity

**Implementation Notes**:
- Large networks (>1000 nodes) may be slow to visualize
- Consider subsystem filtering for focused analysis
- Users import JSON into Cytoscape desktop app

---

## Implementation Phases

### Phase 2: Core Expansion (v0.2.0)

**Target**: Enable model persistence and basic manipulations

**Tools** (9):
1. ✅ import_model_json - Already in specs (011)
2. ✅ export_model_json - Already in specs (011)
3. save_model - New
4. list_saved_models - New
5. ✅ get_compound_name - Already in specs (008)
6. ✅ get_reaction_name - Already in specs (009)
7. ✅ search_compounds - Already in specs (008)
8. ✅ search_reactions - Already in specs (009)
9. set_reaction_bounds - New
10. knockout_reactions - New

**Rationale**: Basic I/O and constraint modification enable iterative workflows.

**Estimated Time**: 1-2 weeks

---

### Phase 3: Analysis Tools (v0.3.0)

**Target**: Enable comparative and batch analysis

**Tools** (5):
1. batch_run_fba
2. compare_models
3. knockout_genes
4. optimize_media_minimal
5. find_pathways

**Rationale**: Support multi-model and multi-condition analysis.

**Estimated Time**: 2-3 weeks

---

### Phase 4: Production Optimization (v0.4.0)

**Target**: Enable metabolic engineering design

**Tools** (5):
1. design_production_strain
2. predict_product_envelope
3. simulate_overexpression
4. identify_bottlenecks
5. suggest_media_additions

**Rationale**: Core metabolic engineering workflows.

**Estimated Time**: 3-4 weeks (complex algorithms)

---

### Phase 5: Advanced Features (v0.5.0)

**Target**: Scale and integrate with external tools

**Tools** (5):
1. batch_build_models
2. batch_gapfill_models
3. compare_fba_results
4. get_escher_map_data
5. export_cytoscape_network

**Rationale**: Enable large-scale studies and visualization.

**Estimated Time**: 2-3 weeks

---

## Design Considerations

### Rate Limiting and Resource Management

**Batch Operation Limits**:
- Maximum 100 models per batch operation
- Maximum 10,000 pathways in pathway enumeration
- Timeout limits: 5 minutes for strain design, 2 minutes for FVA

**Rationale**: Prevent resource exhaustion, ensure responsive service

---

### Caching Strategy

**Cache Expensive Operations**:
- FBA results (keyed by model_id + media_id + objective)
- Gapfilling solutions (keyed by model_id + media_id)
- Pathway enumeration (keyed by model_id + source + target)
- Model comparisons (keyed by sorted model_ids)

**Cache Invalidation**:
- Model modification clears dependent caches
- Time-based expiration (24 hours)
- LRU eviction for memory management

**Rationale**: Improve performance for repeated queries

---

### Asynchronous Operations

**Async Candidates**:
- Batch model building (>10 models)
- Long gapfilling runs (>2 minutes predicted)
- Strain design algorithms (OptKnock)
- Extensive knockout screens (>100 knockouts)
- Production envelope calculation (>50 points)

**Implementation**:
- Return job_id immediately
- Provide status endpoint: `get_job_status(job_id)`
- Notify when complete via polling or webhook

**Rationale**: Maintain responsiveness for long-running operations

---

### Error Handling Patterns

**Structured Error Responses**:
```python
{
    "success": false,
    "error_type": "InfeasibleModel|NotFound|ValidationError|TimeoutError",
    "message": "Human-readable error description",
    "details": {
        "model_id": "model_001",
        "media_id": "media_001",
        "objective_value": 0.0
    },
    "suggestions": [
        "Check media composition",
        "Run gapfilling",
        "Verify reaction bounds"
    ],
    "documentation_url": "https://docs.gem-flux.ai/errors/infeasible-model"
}
```

**Error Types**:
- **NotFound** (404): Model, media, or resource not found
- **ValidationError** (400): Invalid input parameters
- **InfeasibleModel** (422): Model cannot satisfy constraints
- **TimeoutError** (408): Operation exceeded time limit
- **ComputeError** (500): Solver or computation failure

**Rationale**: Help AI assistants and users diagnose issues

---

## Success Metrics

### Phase 2 Success Criteria:
- [ ] Users can import/export models from BiGG database
- [ ] Users can save and reload models between sessions
- [ ] Users can perform basic knockouts and test growth

### Phase 3 Success Criteria:
- [ ] Users can compare multiple strain models
- [ ] Users can run batch FBA on 50+ models in <5 minutes
- [ ] Users can find minimal media compositions

### Phase 4 Success Criteria:
- [ ] Users can design production strains with OptKnock
- [ ] Users can calculate production envelopes
- [ ] Users can identify pathway bottlenecks

### Phase 5 Success Criteria:
- [ ] Users can build 100 models in batch in <10 minutes
- [ ] Users can export data for Escher visualization
- [ ] Users can export networks for Cytoscape analysis

---

## Future Considerations (Beyond v0.5.0)

### Authentication and Multi-User Support
- User accounts and authentication
- Model ownership and sharing
- Rate limiting per user
- Usage quotas

### Advanced Algorithms
- Flux sampling (ACHR, OptGP)
- FSEOF (Flux Scanning based on Enforced Objective Flux)
- MOMA (Minimization of Metabolic Adjustment)
- ROOM (Regulatory On/Off Minimization)

### Machine Learning Integration
- Predict gapfilling solutions
- Suggest engineering targets
- Learn from historical designs

### Collaboration Features
- Shared model repositories
- Annotation and comments
- Version control for models

---

## Tool Implementation Checklist

For each new tool, ensure:
- [ ] Input/output schemas defined
- [ ] Error conditions documented
- [ ] Example usage provided
- [ ] Performance characteristics noted
- [ ] Dependencies identified (library functions)
- [ ] Test cases specified
- [ ] Documentation written
- [ ] Integrated into MCP server

---

## Summary

This roadmap defines **34 additional MCP tools** beyond the MVP, organized into 8 functional categories and 4 implementation phases (v0.2.0 through v0.5.0).

**Key Principles**:
1. **Incremental Value**: Each phase delivers user-facing capabilities
2. **Performance Aware**: Rate limits, caching, async operations
3. **Integration Focus**: Enable external tools (Escher, Cytoscape)
4. **Error Resilience**: Structured errors with helpful suggestions

**Total Estimated Development Time**: 10-15 weeks beyond MVP

**Note**: Implementation order should be adjusted based on user feedback and actual usage patterns after MVP release.

---

## Prerequisites

This specification depends on:
- **001-system-overview.md** - Overall architecture
- **002-data-formats.md** - Data structure definitions
- **003-006** - MVP tool specifications (build_media, build_model, gapfill_model, run_fba)
- **007-009** - Database integration and lookup tools
- **010-011** - Model storage and I/O (import/export already specified)
- **013** - Error handling patterns

All future tools must conform to the data formats and error handling patterns established in these foundational specifications.
