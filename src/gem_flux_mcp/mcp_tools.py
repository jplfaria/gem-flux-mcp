"""MCP tool wrappers for Gem-Flux FastMCP server.

This module provides MCP-compatible wrappers around the core Python library
functions. The wrappers remove DatabaseIndex and Request model parameters from
tool signatures, making them compatible with FastMCP's automatic JSON schema
generation.

Architecture:
    - Core library functions remain unchanged (tools/*.py)
    - These wrappers provide MCP layer (decorated with @mcp.tool())
    - Global state (db_index) accessed via server.get_db_index()
    - Request models created inside wrappers from raw parameters

Tools Provided:
    - build_media: Create growth media from ModelSEED compound IDs
    - build_model: Build metabolic models from protein sequences
    - gapfill_model: Add reactions to enable growth
    - run_fba: Execute flux balance analysis
    - get_compound_name: Lookup compound information by ID
    - search_compounds: Search compounds by name/formula/alias
    - get_reaction_name: Lookup reaction information by ID
    - search_reactions: Search reactions by name/EC/pathway
    - list_models: List all models in current session
    - delete_model: Delete a model from session
    - list_media: List all media in current session

Reference:
    - docs/PHASE_11_MCP_INTEGRATION_PLAN.md: Architecture and implementation plan
    - specs/021-mcp-tool-registration.md: MCP tool registration specification
"""

from typing import Any, Optional

from fastmcp import FastMCP

# Import global state accessors (will be defined in server.py)
from gem_flux_mcp.server import get_db_index

# Import core tool implementations
from gem_flux_mcp.tools.media_builder import (
    build_media as _build_media,
    BuildMediaRequest,
)
from gem_flux_mcp.tools.build_model import build_model as _build_model
from gem_flux_mcp.tools.gapfill_model import gapfill_model as _gapfill_model
from gem_flux_mcp.tools.run_fba import run_fba as _run_fba
from gem_flux_mcp.tools.compound_lookup import (
    get_compound_name as _get_compound_name,
    search_compounds as _search_compounds,
    GetCompoundNameRequest,
    SearchCompoundsRequest,
)
from gem_flux_mcp.tools.reaction_lookup import (
    get_reaction_name as _get_reaction_name,
    search_reactions as _search_reactions,
    GetReactionNameRequest,
    SearchReactionsRequest,
)
from gem_flux_mcp.tools.list_models import (
    list_models as _list_models,
    ListModelsRequest,
)
from gem_flux_mcp.tools.delete_model import (
    delete_model as _delete_model,
    DeleteModelRequest,
)
from gem_flux_mcp.tools.list_media import list_media as _list_media

# Create FastMCP server instance
# Note: Dependencies should be specified in fastmcp.json configuration file
# See: https://gofastmcp.com/docs/deployment/server-configuration
mcp = FastMCP(name="gem-flux-mcp")


# =============================================================================
# Media & Model Building Tools
# =============================================================================


@mcp.tool()
def build_media(
    compounds: list[str],
    default_uptake: float = 100.0,
    custom_bounds: Optional[dict[str, tuple[float, float]]] = None,
) -> dict:
    """Create a growth medium from ModelSEED compound IDs.

    This tool creates a media composition that can be used with gapfill_model and
    run_fba tools. Media specifies which nutrients are available for uptake and
    their maximum flux rates.

    Args:
        compounds: List of ModelSEED compound IDs to include in media.
                  Format: "cpd" followed by 5 digits (e.g., ["cpd00027", "cpd00007"]).
                  Each compound represents a nutrient available in the growth medium.
                  Common compounds:
                    - cpd00027: D-Glucose (carbon source)
                    - cpd00007: O2 (electron acceptor)
                    - cpd00001: H2O
                    - cpd00009: Phosphate
                    - cpd00013: NH3 (nitrogen source)

        default_uptake: Default maximum uptake rate for all compounds (mmol/gDW/h).
                       Default: 100.0 (generous limit allowing unrestricted uptake).
                       Applied to all compounds unless overridden in custom_bounds.
                       Typical values: 5-100 mmol/gDW/h.

        custom_bounds: Optional dictionary mapping specific compound IDs to custom
                      (lower, upper) flux bounds in mmol/gDW/h.
                      Format: {"cpd00027": (-5, 100)}
                      - lower bound: negative value = maximum uptake rate
                      - upper bound: positive value = maximum secretion rate
                      Example: {"cpd00027": (-5, 100)} means:
                        - Max glucose uptake: 5 mmol/gDW/h
                        - Max glucose secretion: 100 mmol/gDW/h

    Returns:
        dict: Media creation result containing:
            - success: True if media created successfully
            - media_id: Unique identifier for this media (e.g., "media_20251027_143052_x1y2z3")
            - compounds: List of compound metadata including:
                - id: ModelSEED compound ID
                - name: Human-readable compound name
                - formula: Molecular formula
                - bounds: Applied flux bounds (lower, upper)
            - num_compounds: Total number of compounds in media
            - media_type: Classification ("minimal" or "rich")
            - default_uptake_rate: Default uptake rate used
            - custom_bounds_applied: Number of compounds with custom bounds

    Raises:
        ValidationError: If compound IDs are invalid or not found in database

    Example:
        # Create glucose minimal media with oxygen
        result = build_media(
            compounds=["cpd00027", "cpd00007", "cpd00001", "cpd00009", "cpd00013"],
            default_uptake=100.0,
            custom_bounds={
                "cpd00027": (-5, 100),   # Limit glucose uptake to 5 mmol/gDW/h
                "cpd00007": (-10, 100)   # Aerobic conditions (10 mmol O2/gDW/h)
            }
        )
        print(result["media_id"])  # Use this ID with gapfill_model or run_fba

    Workflow:
        1. Build media composition → build_media()
        2. Build model from proteins → build_model()
        3. Gapfill model for media → gapfill_model(model_id, media_id)
        4. Analyze metabolism → run_fba(model_id, media_id)

    Reference:
        - Specification: specs/003-build-media-tool.md
        - Data formats: specs/002-data-formats.md
    """
    db_index = get_db_index()
    request = BuildMediaRequest(
        compounds=compounds,
        default_uptake=default_uptake,
        custom_bounds=custom_bounds or {},
    )
    return _build_media(request, db_index)


@mcp.tool()
async def build_model(
    protein_sequences: Optional[dict[str, str]] = None,
    fasta_file_path: Optional[str] = None,
    template: str = "GramNegative",
    model_name: Optional[str] = None,
    annotate_with_rast: bool = False,
) -> dict:
    """Build a draft genome-scale metabolic model from protein sequences.

    This tool creates a draft metabolic model using template-based reconstruction.
    The model typically requires gapfilling (via gapfill_model) to enable growth.

    Args:
        protein_sequences: Dictionary mapping protein IDs to amino acid sequences.
                          Format: {"protein_001": "MKLVINLV...", "protein_002": "MKQHKAMI..."}
                          Use this OR fasta_file_path, not both.
                          Sequences must contain only standard amino acids (ACDEFGHIKLMNPQRSTVWY).

        fasta_file_path: Path to FASTA file containing protein sequences.
                        Alternative to protein_sequences parameter.
                        File format:
                          >protein_001 description
                          MKLVINLVGNSGLGKSTFTQRLIN...
                          >protein_002 description
                          MKQHKAMIVALERFRKEKRDAALL...

        template: ModelSEED template name for reconstruction.
                 Options:
                   - "GramNegative": Gram-negative bacteria (E. coli, Salmonella, etc.)
                                    Default template, 2,138 reactions
                   - "GramPositive": Gram-positive bacteria (Bacillus, Staphylococcus)
                                    1,986 reactions
                   - "Core": Core metabolism only, 452 reactions
                 Default: "GramNegative"

        model_name: Optional user-provided name for the model.
                   If provided, model_id will be "{model_name}.draft"
                   If not provided, auto-generated: "model_YYYYMMDD_HHMMSS_random.draft"
                   Examples: "E_coli_K12", "B_subtilis_168"

        annotate_with_rast: Whether to use RAST annotation service for improved
                           reaction mapping. Default: False (not implemented in MVP)

    Returns:
        dict: Model build result containing:
            - success: True if model built successfully
            - model_id: Unique model identifier with .draft suffix
            - num_reactions: Total reactions in draft model
            - num_metabolites: Total metabolites in model
            - num_genes: Number of protein-coding sequences
            - num_exchange_reactions: Number of EX_ reactions
            - template_used: Template name used for reconstruction
            - has_biomass_reaction: True if biomass reaction exists
            - biomass_reaction_id: ID of biomass reaction (typically "bio1")
            - compartments: List of compartments in model (e.g., ["c0", "e0", "p0"])
            - statistics: Additional statistics (reactions by compartment, etc.)

    Raises:
        ValidationError: If protein sequences invalid or both/neither input provided
        LibraryError: If ModelSEEDpy model building fails

    Example:
        # Build E. coli model from protein sequences
        result = await build_model(
            protein_sequences={
                "prot_hexokinase": "MKLVINLVGNSGLGKSTFTQRLIN...",
                "prot_pgk": "MKQHKAMIVALERFRKEKRDAALL..."
            },
            template="GramNegative",
            model_name="E_coli_K12"
        )
        print(result["model_id"])  # "E_coli_K12.draft"
        print(result["num_reactions"])  # e.g., 856 reactions

        # Build from FASTA file
        result = await build_model(
            fasta_file_path="./ecoli_proteins.fasta",
            template="GramNegative"
        )

    Workflow:
        1. Build media → build_media()
        2. Build draft model → build_model()  ← YOU ARE HERE
        3. Gapfill for growth → gapfill_model(model_id, media_id)
        4. Analyze fluxes → run_fba(model_id, media_id)

    Note:
        Draft models typically cannot grow without gapfilling. Use gapfill_model
        to add missing reactions that enable growth in your target media.

    Reference:
        - Specification: specs/004-build-model-tool.md
        - Data formats: specs/002-data-formats.md
        - Template info: specs/017-template-management.md
    """
    # build_model doesn't use db_index
    return await _build_model(
        protein_sequences=protein_sequences,
        fasta_file_path=fasta_file_path,
        template=template,
        model_name=model_name,
        annotate_with_rast=annotate_with_rast,
    )


@mcp.tool()
def gapfill_model(
    model_id: str,
    media_id: str,
    target_growth_rate: float = 0.01,
    allow_all_non_grp_reactions: bool = True,
    gapfill_mode: str = "full",
) -> dict:
    """Add reactions to a metabolic model to enable growth in specified media.

    This tool performs gapfilling to find minimal sets of reactions that enable
    growth. It uses a two-stage approach: ATP correction followed by genome-scale
    gapfilling.

    Args:
        model_id: Model identifier from session storage.
                 Format: Must have .draft suffix (e.g., "E_coli_K12.draft")
                 Get from build_model() output or list_models() tool.

        media_id: Media identifier from session storage.
                 Format: "media_YYYYMMDD_HHMMSS_random" or predefined name
                 Get from build_media() output or predefined media library:
                   - "glucose_minimal_aerobic"
                   - "glucose_minimal_anaerobic"
                   - "pyruvate_minimal_aerobic"
                   - "pyruvate_minimal_anaerobic"

        target_growth_rate: Minimum growth rate target in hr⁻¹ (per hour).
                           Default: 0.01 hr⁻¹
                           Typical values: 0.001 - 0.1 hr⁻¹
                           Lower values make gapfilling easier (fewer reactions needed)
                           Higher values ensure more robust growth

        allow_all_non_grp_reactions: Allow all non-core reactions during gapfilling.
                                     Default: True
                                     If True: Can add any reaction from database
                                     If False: Restricted to template reactions only

        gapfill_mode: Gapfilling strategy to use.
                     Options:
                       - "full": ATP correction + genome-scale gapfilling (default)
                       - "genome": Skip ATP correction, only genome-scale gapfilling
                     Default: "full" (recommended)

    Returns:
        dict: Gapfilling result containing:
            - success: True if gapfilling succeeded
            - model_id: New model ID with .draft.gf suffix
            - original_model_id: Input model ID (preserved, not modified)
            - reactions_added: List of reactions added, each containing:
                - id: Reaction ID with compartment suffix
                - name: Human-readable reaction name
                - equation: Reaction equation with compound names
                - direction: "forward", "reverse", or "reversible"
                - bounds: Flux bounds (lower, upper)
            - num_reactions_added: Total number of reactions added
            - growth_rate_before: FBA objective value before gapfilling (typically 0)
            - growth_rate_after: FBA objective value after gapfilling (should be > 0)
            - media_id: Media ID used for gapfilling
            - gapfill_statistics: Breakdown of gapfilling stages:
                - atp_gapfill: ATP correction results
                - genome_gapfill: Genome-scale gapfilling results

    Raises:
        NotFoundError: If model_id or media_id not found in session
        InfeasibleGapfillError: If gapfilling cannot find solution
        ValidationError: If model_id doesn't have .draft suffix

    Example:
        # Gapfill model for glucose minimal media
        result = gapfill_model(
            model_id="E_coli_K12.draft",
            media_id="glucose_minimal_aerobic",
            target_growth_rate=0.01
        )
        print(result["model_id"])  # "E_coli_K12.draft.gf"
        print(result["num_reactions_added"])  # e.g., 5 reactions
        print(result["growth_rate_after"])  # e.g., 0.874 hr⁻¹

        # Reactions added during gapfilling
        for rxn in result["reactions_added"]:
            print(f"{rxn['name']}: {rxn['equation']}")

    Workflow:
        1. Build media → build_media()
        2. Build model → build_model()
        3. Gapfill model → gapfill_model()  ← YOU ARE HERE
        4. Analyze fluxes → run_fba(model_id, media_id)

    Notes:
        - Original model is preserved (not modified)
        - New model has .draft.gf suffix (gapfilled version)
        - Can gapfill same model multiple times for different media
        - Gapfilling can take 30 seconds to 5 minutes depending on model size

    Common Issues:
        - InfeasibleGapfillError: Media may be too restrictive, try richer media
        - Takes too long: Try lower target_growth_rate or different media

    Reference:
        - Specification: specs/005-gapfill-model-tool.md
        - Error handling: specs/013-error-handling.md
    """
    db_index = get_db_index()
    return _gapfill_model(
        model_id=model_id,
        media_id=media_id,
        db_index=db_index,
        target_growth_rate=target_growth_rate,
        allow_all_non_grp_reactions=allow_all_non_grp_reactions,
        gapfill_mode=gapfill_mode,
    )


@mcp.tool()
def run_fba(
    model_id: str,
    media_id: str,
    objective: str = "bio1",
    maximize: bool = True,
    flux_threshold: float = 1e-6,
) -> dict:
    """Execute flux balance analysis (FBA) on a metabolic model.

    FBA computes optimal flux distributions through metabolic reactions by
    solving a linear programming problem. It predicts growth rate and metabolic
    fluxes under specified media conditions.

    Args:
        model_id: Model identifier from session storage.
                 Format: Can be .draft, .gf, or .draft.gf suffix
                 Examples: "E_coli_K12.draft.gf", "model_20251027_143052_abc123.gf"
                 Get from build_model(), gapfill_model(), or list_models()
                 Note: Draft models (.draft) typically cannot grow without gapfilling

        media_id: Media identifier from session storage.
                 Format: "media_YYYYMMDD_HHMMSS_random" or predefined name
                 Get from build_media() or use predefined media:
                   - "glucose_minimal_aerobic"
                   - "glucose_minimal_anaerobic"
                   - "pyruvate_minimal_aerobic"
                   - "pyruvate_minimal_anaerobic"

        objective: Objective reaction to optimize.
                  Default: "bio1" (biomass/growth objective)
                  Can be any reaction ID in the model
                  Typically maximize biomass, but can optimize other objectives

        maximize: Whether to maximize (True) or minimize (False) the objective.
                 Default: True (maximize growth)
                 Use False to minimize objectives like ATP maintenance

        flux_threshold: Minimum absolute flux to report in results (mmol/gDW/h).
                       Default: 1e-6 (0.000001)
                       Fluxes below this threshold are considered zero
                       Reduces output size by filtering negligible fluxes

    Returns:
        dict: FBA result containing:
            - success: True if FBA solved successfully
            - model_id: Model ID used for FBA
            - media_id: Media ID used for FBA
            - objective_value: Optimal objective value (growth rate in hr⁻¹ for bio1)
            - objective_reaction: Objective reaction ID
            - status: Solver status ("optimal", "infeasible", or "unbounded")
            - active_reactions: Number of reactions with non-zero flux
            - total_flux: Sum of absolute fluxes (metabolic activity measure)
            - fluxes: Dictionary mapping reaction IDs to flux values
                     Only includes fluxes above flux_threshold
            - uptake_fluxes: Human-readable uptake summary:
                - compound ID, name, flux, reaction ID for each uptake
            - secretion_fluxes: Human-readable secretion summary:
                - compound ID, name, flux, reaction ID for each secretion
            - summary: Breakdown of reaction counts:
                - uptake_reactions: Number of uptake reactions
                - secretion_reactions: Number of secretion reactions
                - internal_reactions: Number of internal reactions with flux

    Raises:
        NotFoundError: If model_id or media_id not found in session
        InfeasibleModelError: If model has no feasible solution (cannot grow)
        UnboundedModelError: If objective can grow infinitely (model error)

    Example:
        # Run FBA on gapfilled model
        result = run_fba(
            model_id="E_coli_K12.draft.gf",
            media_id="glucose_minimal_aerobic"
        )

        print(result["objective_value"])  # e.g., 0.874 hr⁻¹ (growth rate)
        print(result["status"])  # "optimal"
        print(result["active_reactions"])  # e.g., 423 reactions

        # Uptake fluxes (what the cell is consuming)
        for cpd_id, data in result["uptake_fluxes"].items():
            print(f"Consuming {data['name']}: {-data['flux']:.2f} mmol/gDW/h")
        # Output: "Consuming D-Glucose: 5.00 mmol/gDW/h"

        # Secretion fluxes (what the cell is producing)
        for cpd_id, data in result["secretion_fluxes"].items():
            print(f"Producing {data['name']}: {data['flux']:.2f} mmol/gDW/h")
        # Output: "Producing CO2: 8.46 mmol/gDW/h"

    Workflow:
        1. Build media → build_media()
        2. Build model → build_model()
        3. Gapfill model → gapfill_model()
        4. Analyze fluxes → run_fba()  ← YOU ARE HERE

    Common Issues:
        - status="infeasible": Model cannot grow in media, needs gapfilling
        - status="unbounded": Model error, check exchange reaction bounds
        - objective_value=0: Draft model needs gapfilling first

    Interpretation:
        - Objective value (bio1): Predicted growth rate in doublings per hour
        - Negative flux: Compound is consumed (uptake)
        - Positive flux: Compound is produced (secretion)
        - Larger absolute flux: Higher metabolic activity through that reaction

    Reference:
        - Specification: specs/006-run-fba-tool.md
        - Data formats: specs/002-data-formats.md
        - Error handling: specs/013-error-handling.md
    """
    db_index = get_db_index()
    return _run_fba(
        model_id=model_id,
        media_id=media_id,
        db_index=db_index,
        objective=objective,
        maximize=maximize,
        flux_threshold=flux_threshold,
    )


# =============================================================================
# Database Lookup Tools
# =============================================================================


@mcp.tool()
def get_compound_name(compound_id: str) -> dict:
    """Get human-readable information for a ModelSEED compound ID.

    This tool looks up detailed metadata for a compound from the ModelSEED database,
    including name, formula, molecular mass, charge, structure identifiers, and
    cross-references to external databases.

    Args:
        compound_id: ModelSEED compound ID to look up.
                    Format: "cpd" followed by exactly 5 digits
                    Examples: "cpd00027" (D-Glucose), "cpd00007" (O2), "cpd00001" (H2O)
                    Case-insensitive: "CPD00027" is equivalent to "cpd00027"

    Returns:
        dict: Compound information containing:
            - success: True if compound found
            - id: ModelSEED compound ID
            - name: Human-readable compound name
            - abbreviation: Short compound code (often BiGG abbreviation)
            - formula: Molecular formula (e.g., "C6H12O6")
            - mass: Molecular mass in g/mol
            - charge: Ionic charge (0 for neutral, -1 for anions, +1 for cations)
            - inchikey: Standard InChI key for structure identification
            - smiles: SMILES notation for chemical structure
            - aliases: Cross-references to external databases:
                - KEGG: KEGG compound IDs
                - BiGG: BiGG compound IDs
                - MetaCyc: MetaCyc compound IDs
                - PubChem: PubChem compound IDs
                - ChEBI: ChEBI compound IDs

    Raises:
        NotFoundError: If compound_id not found in ModelSEED database
        ValidationError: If compound_id format is invalid

    Example:
        # Look up glucose
        result = get_compound_name("cpd00027")
        print(result["name"])  # "D-Glucose"
        print(result["formula"])  # "C6H12O6"
        print(result["mass"])  # 180.0 g/mol
        print(result["aliases"]["KEGG"])  # ["C00031"]

        # Look up oxygen
        result = get_compound_name("cpd00007")
        print(result["name"])  # "O2"
        print(result["formula"])  # "O2"

    Use Cases:
        - Understanding FBA results: Convert compound IDs to names
        - Building media: Find compound IDs for desired nutrients
        - Interpreting reactions: Understand what compounds are involved
        - Cross-referencing: Map ModelSEED IDs to other databases

    Common Compounds:
        - cpd00001: H2O (water)
        - cpd00002: ATP (energy currency)
        - cpd00007: O2 (oxygen)
        - cpd00009: Phosphate
        - cpd00011: CO2 (carbon dioxide)
        - cpd00013: NH3 (ammonia)
        - cpd00027: D-Glucose
        - cpd00029: Acetate

    Reference:
        - Specification: specs/008-compound-lookup-tools.md
        - Database info: specs/007-database-integration.md
    """
    db_index = get_db_index()
    request = GetCompoundNameRequest(compound_id=compound_id)
    return _get_compound_name(request, db_index)


@mcp.tool()
def search_compounds(query: str, limit: int = 10) -> dict:
    """Search for compounds by name, formula, abbreviation, or alias.

    This tool searches the ModelSEED database for compounds matching a query string.
    It performs case-insensitive matching across multiple fields and returns ranked
    results with match metadata.

    Args:
        query: Text to search for in compound names, formulas, abbreviations, and aliases.
              Can be:
                - Compound name: "glucose", "ATP", "phosphate"
                - Chemical formula: "C6H12O6", "H2O"
                - Abbreviation: "glc__D", "atp"
                - External database ID: "C00031" (KEGG), "CHEBI:17634" (ChEBI)
              Matching is case-insensitive and supports partial matches
              Minimum length: 1 character

        limit: Maximum number of results to return.
              Default: 10
              Range: 1-100
              Use higher limits for broad searches, lower for specific queries

    Returns:
        dict: Search results containing:
            - success: True for successful search (even if 0 results)
            - query: The search query as processed (trimmed, lowercased)
            - num_results: Number of results returned
            - results: List of matching compounds, each containing:
                - id: ModelSEED compound ID
                - name: Human-readable compound name
                - abbreviation: Short compound code
                - formula: Molecular formula
                - mass: Molecular mass in g/mol
                - charge: Ionic charge
                - match_field: Field where match found ("name", "abbreviation", "formula", "aliases", "id")
                - match_type: Type of match ("exact" or "partial")
            - truncated: True if more results exist beyond limit, False otherwise
            - suggestions: Suggestions when no results found (only present if num_results=0)

    Search Priority (results ordered by):
        1. Exact ID match (highest priority)
        2. Exact name match
        3. Exact abbreviation match
        4. Partial name match
        5. Formula match (exact)
        6. Alias match

    Example:
        # Search for glucose
        result = search_compounds("glucose", limit=5)
        print(result["num_results"])  # 5
        for compound in result["results"]:
            print(f"{compound['id']}: {compound['name']} ({compound['formula']})")
        # Output:
        # cpd00027: D-Glucose (C6H12O6)
        # cpd00079: D-Glucose-6-phosphate (C6H11O9P)
        # cpd00221: D-Glucose-1-phosphate (C6H11O9P)
        # ...

        # Search by formula
        result = search_compounds("C6H12O6", limit=10)
        # Returns all hexoses (glucose, fructose, galactose, etc.)

        # Search by external ID
        result = search_compounds("C00031", limit=5)
        # Returns cpd00027 (D-Glucose) with KEGG alias match

    Use Cases:
        - Find compound IDs: "I need glucose" → search → cpd00027
        - Discover related compounds: "phosphate" → find all phosphorylated compounds
        - Cross-reference databases: "C00031" (KEGG) → cpd00027 (ModelSEED)
        - Explore isomers: "C6H12O6" → all hexoses

    Tips:
        - Use specific terms for precise results: "D-glucose" instead of "sugar"
        - Search by formula to find isomers: "C6H12O6"
        - Check truncated flag to see if more results exist
        - Use higher limits (50-100) for exploratory searches

    Empty Results:
        If no compounds match, suggestions will be provided:
        - Try a more general search term
        - Check spelling of compound name
        - Search by formula (e.g., C6H12O6)
        - Search by database ID from other sources (KEGG, BiGG)

    Reference:
        - Specification: specs/008-compound-lookup-tools.md
        - Database info: specs/007-database-integration.md
    """
    db_index = get_db_index()
    request = SearchCompoundsRequest(query=query, limit=limit)
    return _search_compounds(request, db_index)


@mcp.tool()
def get_reaction_name(reaction_id: str) -> dict:
    """Get human-readable information for a ModelSEED reaction ID.

    This tool looks up detailed metadata for a reaction from the ModelSEED database,
    including name, equation, EC numbers, reversibility, pathways, and cross-references
    to external databases.

    Args:
        reaction_id: ModelSEED reaction ID to look up.
                    Format: "rxn" followed by exactly 5 digits
                    Examples: "rxn00148" (hexokinase), "rxn00200" (glycolysis)
                    Case-insensitive: "RXN00148" is equivalent to "rxn00148"

    Returns:
        dict: Reaction information containing:
            - success: True if reaction found
            - id: ModelSEED reaction ID
            - name: Human-readable reaction name
            - abbreviation: Short reaction code
            - equation: Reaction equation with compound names
            - equation_with_ids: Reaction equation with ModelSEED compound IDs
            - reversibility: "irreversible_forward", "irreversible_reverse", or "reversible"
            - direction_symbol: Direction symbol (">", "<", or "=")
            - ec_numbers: List of EC numbers (enzyme classification)
            - pathways: List of metabolic pathways this reaction belongs to
            - is_transport: True if reaction transports compounds between compartments
            - external_ids: Cross-references to external databases:
                - KEGG: KEGG reaction IDs
                - BiGG: BiGG reaction IDs
                - MetaCyc: MetaCyc reaction IDs

    Raises:
        NotFoundError: If reaction_id not found in ModelSEED database
        ValidationError: If reaction_id format is invalid

    Example:
        # Look up hexokinase
        result = get_reaction_name("rxn00148")
        print(result["name"])  # "hexokinase"
        print(result["equation"])  # "D-Glucose + ATP => ADP + H+ + D-Glucose 6-phosphate"
        print(result["ec_numbers"])  # ["2.7.1.1"]
        print(result["reversibility"])  # "irreversible_forward"
        print(result["direction_symbol"])  # ">"

        # Look up reversible reaction
        result = get_reaction_name("rxn00200")
        print(result["direction_symbol"])  # "=" (reversible)

    Use Cases:
        - Understanding gapfilling results: What reactions were added?
        - Interpreting FBA results: What reactions have high flux?
        - Pathway analysis: What pathways is this reaction part of?
        - Enzyme identification: What enzymes catalyze this reaction?

    Direction Symbols:
        - ">": Irreversible forward (left to right only)
        - "<": Irreversible reverse (right to left only)
        - "=": Reversible (bidirectional)

    Common Reactions:
        - rxn00148: hexokinase (glucose phosphorylation)
        - rxn00200: phosphoglucose isomerase
        - rxn00216: phosphofructokinase
        - rxn01100: glucokinase

    Reference:
        - Specification: specs/009-reaction-lookup-tools.md
        - Database info: specs/007-database-integration.md
    """
    db_index = get_db_index()
    request = GetReactionNameRequest(reaction_id=reaction_id)
    return _get_reaction_name(request, db_index)


@mcp.tool()
def search_reactions(query: str, limit: int = 10) -> dict:
    """Search for reactions by name, EC number, abbreviation, or pathway.

    This tool searches the ModelSEED database for reactions matching a query string.
    It performs case-insensitive matching across multiple fields and returns ranked
    results with match metadata.

    Args:
        query: Text to search for in reaction names, EC numbers, abbreviations, and pathways.
              Can be:
                - Reaction name: "hexokinase", "ATP synthase", "glycolysis"
                - EC number: "2.7.1.1", "1.1.1.1"
                - Abbreviation: "HEX1", "PGI"
                - Pathway: "Glycolysis", "TCA cycle", "Central Metabolism"
                - External database ID: "R00200" (KEGG)
              Matching is case-insensitive and supports partial matches
              Minimum length: 1 character

        limit: Maximum number of results to return.
              Default: 10
              Range: 1-100

    Returns:
        dict: Search results containing:
            - success: True for successful search (even if 0 results)
            - query: The search query as processed
            - num_results: Number of results returned
            - results: List of matching reactions, each containing:
                - id: ModelSEED reaction ID
                - name: Human-readable reaction name
                - equation: Reaction equation with compound names
                - ec_numbers: List of EC numbers
                - match_field: Field where match found
                - match_type: Type of match ("exact" or "partial")
            - truncated: True if more results exist beyond limit
            - suggestions: Suggestions when no results found

    Search Priority (results ordered by):
        1. Exact ID match
        2. Exact name match
        3. Exact abbreviation match
        4. Partial name match
        5. EC number match
        6. Pathway match
        7. Alias match

    Example:
        # Search for hexokinase
        result = search_reactions("hexokinase", limit=5)
        for reaction in result["results"]:
            print(f"{reaction['id']}: {reaction['name']}")
            print(f"  {reaction['equation']}")
            print(f"  EC: {', '.join(reaction['ec_numbers'])}")
        # Output:
        # rxn00148: hexokinase
        #   D-Glucose + ATP => ADP + H+ + D-Glucose 6-phosphate
        #   EC: 2.7.1.1

        # Search by EC number
        result = search_reactions("2.7.1.1", limit=10)
        # Returns all reactions with EC 2.7.1.1 (hexokinases)

        # Search by pathway
        result = search_reactions("glycolysis", limit=20)
        # Returns all reactions in glycolysis pathway

    Use Cases:
        - Find reaction IDs: "I need hexokinase" → search → rxn00148
        - Explore pathways: "TCA cycle" → find all TCA reactions
        - Enzyme lookup: "2.7.1.1" (EC) → find all hexokinases
        - Cross-reference: "R00200" (KEGG) → rxn00148 (ModelSEED)

    Reference:
        - Specification: specs/009-reaction-lookup-tools.md
        - Database info: specs/007-database-integration.md
    """
    db_index = get_db_index()
    request = SearchReactionsRequest(query=query, limit=limit)
    return _search_reactions(request, db_index)


# =============================================================================
# Session Management Tools
# =============================================================================


@mcp.tool()
def list_models(filter_state: str = "all") -> dict:
    """List all metabolic models in the current server session.

    This tool returns metadata for all models stored in session, with optional
    filtering by processing state (draft vs gapfilled). Use this to discover
    available models before running gapfill_model or run_fba.

    Args:
        filter_state: Filter models by processing state.
                     Options:
                       - "all": Return all models regardless of state (default)
                       - "draft": Return only draft models (.draft suffix)
                       - "gapfilled": Return only gapfilled models (.gf or .draft.gf suffixes)
                     Case-insensitive

    Returns:
        dict: Model listing containing:
            - success: True for successful listing
            - models: List of model metadata, each containing:
                - model_id: Unique model identifier with state suffix
                - model_name: User-provided name or None if auto-generated
                - state: Processing state ("draft" or "gapfilled")
                - num_reactions: Total reactions in model
                - num_metabolites: Total metabolites in model
                - num_genes: Number of protein-coding sequences
                - template_used: Template name used for model building
                - created_at: ISO 8601 timestamp of model creation
                - derived_from: Model ID this was derived from, or None if original
            - total_models: Total number of models returned (after filtering)
            - models_by_state: Breakdown of models by state:
                - draft: Count of draft models
                - gapfilled: Count of gapfilled models

    State Classification:
        - "draft": Model has .draft suffix (not gapfilled)
        - "gapfilled": Model has .gf or .draft.gf suffix (gapfilled)

    Example:
        # List all models
        result = list_models()
        print(f"Total models: {result['total_models']}")
        for model in result["models"]:
            print(f"{model['model_id']}: {model['state']}, {model['num_reactions']} reactions")
        # Output:
        # E_coli_K12.draft: draft, 856 reactions
        # E_coli_K12.draft.gf: gapfilled, 892 reactions

        # List only draft models
        result = list_models(filter_state="draft")
        print(f"Draft models needing gapfilling: {result['total_models']}")

        # List only gapfilled models
        result = list_models(filter_state="gapfilled")
        print(f"Gapfilled models ready for FBA: {result['total_models']}")

    Use Cases:
        - Discover available models: What models exist in session?
        - Find draft models: Which models need gapfilling?
        - Find gapfilled models: Which models are ready for FBA?
        - Track model lineage: What models were derived from what?
        - Session management: How many models am I storing?

    Model Lifecycle:
        1. build_model() → model.draft (draft model)
        2. gapfill_model() → model.draft.gf (gapfilled model)
        3. Both versions coexist in session
        4. Use list_models() to see all versions

    Empty Results:
        If no models exist in session, returns:
        - models: []
        - total_models: 0
        - models_by_state: {"draft": 0, "gapfilled": 0}

    Reference:
        - Specification: specs/018-session-management-tools.md
        - Model storage: specs/010-model-storage.md
    """
    request = ListModelsRequest(filter_state=filter_state)
    return _list_models(request)


@mcp.tool()
def delete_model(model_id: str) -> dict:
    """Delete a metabolic model from the current server session.

    This tool permanently removes a model from session storage. Use this to free
    memory and clean up models that are no longer needed.

    Args:
        model_id: Model identifier to delete.
                 Format: Must match exact model_id including state suffix
                 Examples: "E_coli_K12.draft", "E_coli_K12.draft.gf"
                 Get from list_models() output
                 Case-sensitive

    Returns:
        dict: Deletion result containing:
            - success: True if model deleted successfully
            - deleted_model_id: The model_id that was deleted (confirmation)
            - message: Human-readable confirmation message

    Raises:
        NotFoundError: If model_id not found in session storage

    Example:
        # Delete a draft model (keep only gapfilled version)
        result = delete_model("E_coli_K12.draft")
        print(result["message"])  # "Model deleted successfully"

        # Delete a gapfilled model
        result = delete_model("E_coli_K12.draft.gf")

    Use Cases:
        - Clean up drafts: Delete draft models after gapfilling
        - Free memory: Remove models from long-running sessions
        - Session management: Keep storage organized
        - Failed attempts: Delete models from failed workflows

    Common Workflow:
        # Build and gapfill model
        build_result = await build_model(...)
        draft_id = build_result["model_id"]  # "model_123.draft"

        gapfill_result = gapfill_model(draft_id, media_id)
        gf_id = gapfill_result["model_id"]  # "model_123.draft.gf"

        # Keep only gapfilled version
        delete_model(draft_id)

    Warning:
        - Deletion is permanent (cannot be undone)
        - Models are session-scoped (lost on server restart anyway)
        - Be careful not to delete models still needed for analysis

    Tip:
        Use list_models() before deleting to see what models exist and their relationships.

    Reference:
        - Specification: specs/018-session-management-tools.md
        - Model storage: specs/010-model-storage.md
    """
    request = DeleteModelRequest(model_id=model_id)
    return _delete_model(request)


@mcp.tool()
def list_media() -> dict:
    """List all growth media compositions in the current server session.

    This tool returns metadata for all media stored in session, including both
    predefined media from the library and user-created media from build_media().

    Returns:
        dict: Media listing containing:
            - success: True for successful listing
            - media: List of media metadata, each containing:
                - media_id: Unique media identifier
                - media_name: User-provided or predefined name, or None
                - num_compounds: Number of compounds in media
                - media_type: Classification ("minimal" or "rich")
                - compounds_preview: First 3 compounds with IDs and names
                - created_at: ISO 8601 timestamp of media creation
            - total_media: Total number of media (predefined + user-created)
            - predefined_media: Count of predefined media from library
            - user_created_media: Count of media created via build_media

    Media Types:
        - "minimal": < 50 compounds (defined media)
        - "rich": ≥ 50 compounds (complex media like LB)

    Predefined Media:
        - glucose_minimal_aerobic: Glucose + O2 (18 compounds)
        - glucose_minimal_anaerobic: Glucose without O2 (17 compounds)
        - pyruvate_minimal_aerobic: Pyruvate + O2 (18 compounds)
        - pyruvate_minimal_anaerobic: Pyruvate without O2 (17 compounds)

    Example:
        # List all media
        result = list_media()
        print(f"Total media: {result['total_media']}")
        for media in result["media"]:
            print(f"{media['media_id']}: {media['num_compounds']} compounds ({media['media_type']})")
        # Output:
        # glucose_minimal_aerobic: 18 compounds (minimal)
        # media_20251027_143052_x1y2z3: 20 compounds (minimal)

        # Preview compounds in first media
        for compound in result["media"][0]["compounds_preview"]:
            print(f"  - {compound['id']}: {compound['name']}")
        # Output:
        #   - cpd00027: D-Glucose
        #   - cpd00007: O2
        #   - cpd00001: H2O

    Use Cases:
        - Discover available media: What media can I use for gapfilling?
        - Check media composition: What compounds are in this media?
        - Session overview: How many media compositions exist?
        - Before gapfilling: Which media should I use?

    Common Workflow:
        # List available media
        result = list_media()

        # Use predefined media for gapfilling
        gapfill_model(
            model_id="E_coli_K12.draft",
            media_id="glucose_minimal_aerobic"  # From list_media output
        )

        # Or create custom media
        build_result = build_media(...)
        custom_media_id = build_result["media_id"]

        # Verify it was created
        result = list_media()
        print(result["user_created_media"])  # 1

    Empty Results:
        If no media exist in session (should not happen - predefined media always loaded):
        - media: []
        - total_media: 0
        - predefined_media: 0
        - user_created_media: 0

    Reference:
        - Specification: specs/018-session-management-tools.md
        - Predefined media: specs/019-predefined-media-library.md
        - Media format: specs/002-data-formats.md
    """
    return _list_media(db_index=get_db_index())


# =============================================================================
# Tool Count Verification
# =============================================================================

# Verify 11 tools are registered
__all__ = [
    "mcp",
    "build_media",
    "build_model",
    "gapfill_model",
    "run_fba",
    "get_compound_name",
    "search_compounds",
    "get_reaction_name",
    "search_reactions",
    "list_models",
    "delete_model",
    "list_media",
]

# Expected tool count: 11
# 1. build_media
# 2. build_model
# 3. gapfill_model
# 4. run_fba
# 5. get_compound_name
# 6. search_compounds
# 7. get_reaction_name
# 8. search_reactions
# 9. list_models
# 10. delete_model
# 11. list_media
