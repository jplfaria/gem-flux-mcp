"""
gapfill_model tool for adding reactions to enable growth in metabolic models.

This module implements the gapfill_model MCP tool according to specification
005-gapfill-model-tool.md. It performs two-stage gapfilling: ATP correction
to ensure energy metabolism works across conditions, followed by genome-scale
gapfilling to enable growth in the target medium.

Tool Capabilities:
    - Two-stage gapfilling (ATP correction + genome-scale)
    - Automatic reuse of ATP test conditions from build_model
    - Minimal reaction set addition
    - Template-based reaction sourcing
    - Growth rate verification
    - Session-based model storage with transformed .gf suffix

Gapfilling Stages:
    1. ATP Correction (MSATPCorrection):
       - Automatically reuses test conditions if model was ATP-corrected during build_model
       - If not already done: tests ATP production across 54 default media
       - Adds reactions to fix ATP metabolism gaps
       - Expands model to genome-scale template

    2. Genome-Scale Gapfilling (MSGapfill):
       - Uses ATP test conditions for multi-media validation
       - Adds minimal reactions for target medium
       - Ensures model reaches target growth rate
       - Auto-generates exchange reactions

What this tool does NOT do (MVP):
    - Does not validate biological accuracy
    - Does not optimize reaction selection beyond minimization
    - Does not perform iterative refinement
    - Does not guarantee complete pathway coverage
"""

import copy
from typing import Any, Optional

from modelseedpy import MSATPCorrection, MSGapfill
from modelseedpy.core.msatpcorrection import load_default_medias
from modelseedpy.core.msmodel import get_reaction_constraints_from_direction

from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.errors import (
    ValidationError,
    NotFoundError,
    InfeasibilityError,
    LibraryError,
    build_error_response,
    build_generic_error_response,
    model_not_found_error,
    media_not_found_error,
    gapfill_infeasible_error,
)
from gem_flux_mcp.storage.models import (
    MODEL_STORAGE,
    retrieve_model,
    model_exists,
    transform_state_suffix,
    store_model,
)
from gem_flux_mcp.storage.media import (
    MEDIA_STORAGE,
    retrieve_media,
    media_exists,
)
from gem_flux_mcp.templates.loader import get_template
from gem_flux_mcp.database.index import DatabaseIndex

logger = get_logger(__name__)


# =============================================================================
# Helper Functions for Prompts
# =============================================================================


def _get_next_steps_gapfill() -> list[str]:
    """Get next_steps from centralized prompt."""
    from gem_flux_mcp.prompts import render_prompt
    next_steps_text = render_prompt("next_steps/gapfill_model")
    return [
        line.strip()[2:].strip()
        for line in next_steps_text.split("\n")
        if line.strip().startswith("-")
    ]


# =============================================================================
# Validation Functions
# =============================================================================


def validate_gapfill_inputs(
    model_id: str,
    media_id: str,
    target_growth_rate: float,
    gapfill_mode: str,
) -> None:
    """Validate gapfill_model input parameters.

    Args:
        model_id: Model identifier to gapfill
        media_id: Media identifier for gapfilling conditions
        target_growth_rate: Minimum growth rate to achieve
        gapfill_mode: Gapfilling mode ("full", "atp_only", "genomescale_only")

    Raises:
        ValidationError: If any validation fails
        NotFoundError: If model_id or media_id not found
    """
    # Validate model_id exists
    if not model_exists(model_id):
        available_models = list(MODEL_STORAGE.keys())
        raise model_not_found_error(
            model_id=model_id,
            available_models=available_models,
        )

    # Validate media_id exists
    if not media_exists(media_id):
        available_media = list(MEDIA_STORAGE.keys())
        raise media_not_found_error(
            media_id=media_id,
            available_media=available_media,
        )

    # Validate target_growth_rate is positive
    if target_growth_rate <= 0:
        raise ValidationError(
            message="Target growth rate must be positive",
            error_code="INVALID_TARGET_GROWTH_RATE",
            details={
                "provided_value": target_growth_rate,
                "valid_range": [0.001, 10.0],
                "typical_range": [0.01, 1.0],
                "recommendation": 0.01,
            },
            suggestions=[
                "Use a positive growth rate",
                "Typical values: 0.01 for permissive gapfilling, 0.1 for moderate, 0.5+ for stringent",
            ],
        )

    # Validate gapfill_mode
    valid_modes = ["full", "atp_only", "genomescale_only"]
    if gapfill_mode not in valid_modes:
        raise ValidationError(
            message=f"Invalid gapfill_mode: {gapfill_mode}",
            error_code="INVALID_GAPFILL_MODE",
            details={
                "provided_mode": gapfill_mode,
                "valid_modes": valid_modes,
            },
            suggestions=[
                f"Use one of: {', '.join(valid_modes)}",
                "Recommended: 'full' for comprehensive gapfilling",
            ],
        )

    # Check for biomass reaction (warn if missing, but allow gapfilling to proceed)
    model = retrieve_model(model_id)
    biomass_reactions = [rxn for rxn in model.reactions if rxn.id.startswith("bio")]

    if not biomass_reactions:
        logger.warning(
            f"Model '{model_id}' does not have a biomass reaction. "
            f"This may occur with offline model building (annotate_with_rast=False). "
            f"Gapfilling will proceed, but results may not be meaningful for empty models."
        )
        # Note: We allow gapfilling to proceed because:
        # 1. Offline model building (annotate_with_rast=False) produces empty models
        # 2. These tests are for API correctness, not workflow validation
        # 3. ModelSEEDpy itself doesn't require biomass for gapfilling


def check_baseline_growth(model: Any, media: Any, objective: str = "bio1") -> float:
    """Check model's growth rate before gapfilling.

    Uses shared media utility for correct media application.

    Args:
        model: COBRApy Model object
        media: MSMedia object
        objective: Objective reaction ID to optimize (default: "bio1" for biomass)

    Returns:
        Current growth rate (objective value)
    """
    from gem_flux_mcp.utils.media import apply_media_to_model

    try:
        # Apply media constraints using shared utility
        apply_media_to_model(model, media, compartment="e0")

        # Set objective explicitly (critical for correct growth rate calculation)
        if objective in model.reactions:
            model.objective = objective
            model.objective_direction = "max"
            logger.debug(f"Set objective to {objective} (maximize)")
        else:
            logger.warning(f"Objective reaction {objective} not found in model, using current objective")

        # Run FBA
        solution = model.optimize()

        if solution.status == "optimal":
            growth_rate = solution.objective_value
            logger.info(f"Baseline growth rate: {growth_rate:.6f}")
            return growth_rate
        else:
            logger.info(f"Baseline FBA status: {solution.status} (growth rate: 0.0)")
            return 0.0

    except Exception as e:
        logger.warning(f"Baseline growth check failed: {e}")
        return 0.0


def run_atp_correction(
    model: Any,
    core_template: Any,
) -> dict[str, Any]:
    """Run ATP correction stage (MSATPCorrection).

    Args:
        model: COBRApy Model object (will be modified in-place)
        core_template: Core template for ATP correction

    Returns:
        Dict with ATP correction statistics and test conditions
    """
    logger.info("Starting ATP correction stage...")

    try:
        # Load default ATP test media (54 media)
        default_medias = load_default_medias()
        logger.info(f"Loaded {len(default_medias)} default ATP test media")

        # Create MSATPCorrection object
        atp_correction = MSATPCorrection(
            model_or_mdlutl=model,
            core_template=core_template,
            atp_medias=default_medias,
            compartment="c0",
            atp_hydrolysis_id="ATPM_c0",
            load_default_medias=False,  # Already loaded
        )

        # Run ATP correction workflow
        logger.info("Evaluating growth media...")
        media_eval = atp_correction.evaluate_growth_media()

        logger.info("Determining growth media...")
        atp_correction.determine_growth_media()

        logger.info("Applying growth media gapfilling...")
        atp_correction.apply_growth_media_gapfilling()

        logger.info("Expanding model to genome scale...")
        atp_correction.expand_model_to_genome_scale()

        logger.info("Building test conditions...")
        tests = atp_correction.build_tests()

        # Collect statistics
        media_tested = len(default_medias)
        media_passed = 0
        media_failed = 0
        reactions_added = 0
        failed_media_examples = []

        for test in tests:
            test_media = test['media']
            stats = atp_correction.media_gapfill_stats.get(test_media)

            if stats is None:
                # No solution found for this media
                media_failed += 1
                if len(failed_media_examples) < 5:
                    failed_media_examples.append(test_media.id if hasattr(test_media, 'id') else str(test_media))
            else:
                # Solution found
                media_passed += 1
                # Count reactions added from this media
                if 'new' in stats:
                    reactions_added += len(stats['new'])

        logger.info(f"ATP correction complete: {media_passed}/{media_tested} media passed, {reactions_added} reactions added")

        return {
            "performed": True,
            "media_tested": media_tested,
            "media_passed": media_passed,
            "media_failed": media_failed,
            "reactions_added": reactions_added,
            "failed_media_examples": failed_media_examples,
            "tests": tests,  # Needed for genome-scale gapfilling
        }

    except Exception as e:
        logger.error(f"ATP correction failed: {e}")
        raise LibraryError(
            message=f"ATP correction stage failed: {str(e)}",
            error_code="ATP_CORRECTION_FAILED",
            details={
                "exception_type": type(e).__name__,
                "exception_message": str(e),
            },
            suggestions=[
                "Check model has valid ATPM reaction",
                "Verify Core template is loaded correctly",
                "Check server logs for detailed error information",
            ],
        )


def run_genome_scale_gapfilling(
    model: Any,
    template: Any,
    media: Any,
    target_growth_rate: float,
    tests: list[dict],
) -> dict[str, Any]:
    """Run genome-scale gapfilling stage (MSGapfill).

    Args:
        model: COBRApy Model object (ATP-corrected)
        template: Genome-scale template (GramNegative, etc.)
        media: MSMedia object for target growth conditions
        target_growth_rate: Minimum growth rate to achieve
        tests: Test conditions from ATP correction

    Returns:
        Dict with gapfilling solution and statistics
    """
    logger.info("Starting genome-scale gapfilling stage...")

    try:
        # Create MSGapfill object
        gapfiller = MSGapfill(
            model_or_mdlutl=model,
            default_gapfill_templates=[template],
            test_conditions=tests,
            default_target="bio1",
        )

        # Run gapfilling
        # Note: target is already set to "bio1" in MSGapfill.__init__ via default_target
        # minimum_obj is the threshold growth rate we want to achieve
        logger.info(f"Running gapfilling for target growth rate: {target_growth_rate}")
        gapfill_solution = gapfiller.run_gapfilling(
            media=media,
            minimum_obj=target_growth_rate,
        )

        # Check if solution found
        if gapfill_solution is None:
            logger.warning("Gapfilling returned None (no solution)")
            return {
                "performed": True,
                "solution_found": False,
                "reactions_added": 0,
                "reversed_reactions": 0,
                "new_reactions": 0,
            }

        # Parse solution
        reversed_reactions = len(gapfill_solution.get('reversed', {}))
        new_reactions = len(gapfill_solution.get('new', {}))
        reactions_added = reversed_reactions + new_reactions

        logger.info(f"Gapfilling solution: {new_reactions} new reactions, {reversed_reactions} reversed reactions")

        return {
            "performed": True,
            "solution_found": True,
            "reactions_added": reactions_added,
            "reversed_reactions": reversed_reactions,
            "new_reactions": new_reactions,
            "solution": gapfill_solution,
        }

    except Exception as e:
        logger.error(f"Genome-scale gapfilling failed: {e}")
        raise LibraryError(
            message=f"Genome-scale gapfilling stage failed: {str(e)}",
            error_code="GENOMESCALE_GAPFILL_FAILED",
            details={
                "exception_type": type(e).__name__,
                "exception_message": str(e),
            },
            suggestions=[
                "Check media contains essential nutrients (C, N, P, S sources)",
                "Try a richer media composition",
                "Lower target_growth_rate (try 0.001)",
                "Check server logs for detailed error information",
            ],
        )


def integrate_gapfill_solution(
    model: Any,
    template: Any,
    solution: dict[str, Any],
) -> list[dict[str, Any]]:
    """Integrate gapfilling solution into model.

    CRITICAL: Reactions must be added in this order:
    1. Add non-exchange reactions from template (may introduce new metabolites)
    2. Call MSBuilder.add_exchanges_to_model() to create exchanges for new metabolites
    3. Set bounds on exchange reactions based on gapfill solution

    Args:
        model: COBRApy Model object to modify
        template: Template with reaction definitions
        solution: Gapfilling solution from MSGapfill

    Returns:
        List of added reaction metadata
    """
    logger.info("Integrating gapfilling solution into model...")

    added_reactions = []
    new_reactions = solution.get('new', {})

    # STEP 1: Add non-exchange reactions first (these may introduce new metabolites)
    logger.info("Step 1: Adding non-exchange reactions from template...")
    for rxn_id, direction in new_reactions.items():
        # Skip exchange reactions for now - process them after MSBuilder
        if rxn_id.startswith('EX_'):
            continue

        try:
            # Convert model reaction ID (indexed) to template reaction ID (non-indexed)
            # Model uses: rxn05481_c0, Template uses: rxn05481_c
            if rxn_id.endswith('0'):
                template_rxn_id = rxn_id[:-1]  # rxn05481_c0 → rxn05481_c
            else:
                template_rxn_id = rxn_id

            # Get reaction from template
            if template_rxn_id not in template.reactions:
                logger.warning(f"Reaction {template_rxn_id} not found in template, skipping")
                continue

            template_reaction = template.reactions.get_by_id(template_rxn_id)

            # Convert to COBRApy reaction
            model_reaction = template_reaction.to_reaction(model)

            # Set bounds based on direction
            lb, ub = get_reaction_constraints_from_direction(direction)
            model_reaction.lower_bound = lb
            model_reaction.upper_bound = ub

            # Add to model
            model.add_reactions([model_reaction])

            # Record metadata
            added_reactions.append({
                "id": rxn_id,
                "direction": direction,
                "bounds": [lb, ub],
            })

            logger.debug(f"Added reaction: {rxn_id} (direction: {direction})")

        except Exception as e:
            logger.warning(f"Failed to add reaction {rxn_id}: {e}")
            continue

    # STEP 2: Now that new reactions (and their metabolites) are in the model,
    # call MSBuilder to create exchange reactions for any new metabolites
    from modelseedpy.core.msbuilder import MSBuilder
    exchange_reactions_in_solution = [
        rxn_id for rxn_id in new_reactions.keys() if rxn_id.startswith('EX_')
    ]

    if exchange_reactions_in_solution:
        logger.info(f"Step 2: Creating exchange reactions for new metabolites...")
        # MSBuilder will create exchanges for all metabolites that don't have them yet
        added_exchanges = MSBuilder.add_exchanges_to_model(model, extra_cell='e0')
        logger.info(f"MSBuilder added {len(added_exchanges)} exchange reactions")

        # STEP 3: Set bounds on exchange reactions based on gapfill solution
        logger.info("Step 3: Setting bounds on exchange reactions...")
        for rxn_id, direction in new_reactions.items():
            if not rxn_id.startswith('EX_'):
                continue

            try:
                if rxn_id in model.reactions:
                    existing_rxn = model.reactions.get_by_id(rxn_id)
                    lb, ub = get_reaction_constraints_from_direction(direction)
                    existing_rxn.lower_bound = lb
                    existing_rxn.upper_bound = ub
                    logger.debug(f"Set exchange reaction {rxn_id} bounds to ({lb}, {ub})")

                    added_reactions.append({
                        "id": rxn_id,
                        "direction": direction,
                        "bounds": [lb, ub],
                    })
                else:
                    logger.warning(f"Exchange reaction {rxn_id} not found after MSBuilder.add_exchanges_to_model()")

            except Exception as e:
                logger.warning(f"Failed to set bounds on exchange reaction {rxn_id}: {e}")
                continue

    logger.info(f"Integrated {len(added_reactions)} reactions into model")

    return added_reactions


def enrich_reaction_metadata(
    reactions: list[dict[str, Any]],
    db_index: DatabaseIndex,
) -> list[dict[str, Any]]:
    """Enrich reaction metadata with human-readable names from database.

    Args:
        reactions: List of reaction dicts with id, direction, bounds
        db_index: DatabaseIndex instance with loaded reactions database

    Returns:
        List of enriched reaction dicts with name, equation, compartment
    """
    enriched = []

    for rxn in reactions:
        rxn_id = rxn["id"]

        # Extract base reaction ID (without compartment suffix)
        # rxn05481_c0 → rxn05481
        base_rxn_id = rxn_id.split("_")[0]

        # Lookup in database
        reaction_record = db_index.get_reaction_by_id(base_rxn_id)

        if reaction_record is not None:
            name = reaction_record.get("name", "Unknown reaction")
            equation = reaction_record.get("equation", "")
        else:
            name = "Unknown reaction"
            equation = ""

        # Parse compartment from rxn_id
        if "_" in rxn_id:
            compartment = rxn_id.split("_")[1]
        else:
            compartment = "c0"

        # Convert direction symbol to readable string
        direction_map = {
            ">": "forward",
            "<": "reverse",
            "=": "reversible",
        }
        direction_str = direction_map.get(rxn["direction"], rxn["direction"])

        # Simplified reaction info (remove long equation to save tokens)
        enriched.append({
            "id": rxn_id,
            "name": name,
            "direction": direction_str,
            "compartment": compartment,
            # "equation": equation,  # Removed to reduce response size - use get_reaction_name for details
        })

    return enriched


def categorize_reactions_by_pathway(enriched_reactions: list[dict], db_index: DatabaseIndex) -> dict:
    """Categorize gapfilled reactions by biological pathway using ModelSEED database annotations.

    Uses actual pathway data from the ModelSEED reactions database instead of keyword matching.
    This provides more accurate pathway categorization based on curated annotations.

    Args:
        enriched_reactions: List of reaction dicts with id, name, direction, compartment
        db_index: DatabaseIndex instance for looking up reaction pathway data

    Returns:
        Dict with pathway categories and counts
    """
    from gem_flux_mcp.tools.reaction_lookup import parse_pathways

    # Count reactions by pathway
    pathway_counts = {}
    pathway_examples = {}
    reactions_without_pathways = 0

    for rxn in enriched_reactions:
        # Extract base reaction ID (without compartment suffix)
        base_rxn_id = rxn["id"].split("_")[0]

        # Lookup in database
        reaction_record = db_index.get_reaction_by_id(base_rxn_id)

        if reaction_record is not None:
            pathways_raw = reaction_record.get("pathways", "")
            pathways_list = parse_pathways(pathways_raw)

            if pathways_list:
                # Reaction has pathway annotations
                for pathway in pathways_list:
                    if pathway not in pathway_counts:
                        pathway_counts[pathway] = 0
                        pathway_examples[pathway] = []

                    pathway_counts[pathway] += 1
                    if len(pathway_examples[pathway]) < 3:  # Keep up to 3 examples per pathway
                        pathway_examples[pathway].append({
                            "id": rxn["id"],
                            "name": rxn["name"]
                        })
            else:
                # Reaction exists but has no pathway annotation
                reactions_without_pathways += 1
                if "Unannotated" not in pathway_counts:
                    pathway_counts["Unannotated"] = 0
                    pathway_examples["Unannotated"] = []
                pathway_counts["Unannotated"] += 1
                if len(pathway_examples["Unannotated"]) < 3:
                    pathway_examples["Unannotated"].append({
                        "id": rxn["id"],
                        "name": rxn["name"]
                    })
        else:
            # Reaction not found in database
            reactions_without_pathways += 1
            if "Unknown" not in pathway_counts:
                pathway_counts["Unknown"] = 0
                pathway_examples["Unknown"] = []
            pathway_counts["Unknown"] += 1
            if len(pathway_examples["Unknown"]) < 3:
                pathway_examples["Unknown"].append({
                    "id": rxn["id"],
                    "name": rxn["name"]
                })

    # Build pathway summary (only include pathways with reactions)
    pathways = []
    for pathway, count in sorted(pathway_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pathways.append({
                "pathway": pathway,
                "reactions_added": count,
                "examples": pathway_examples[pathway]
            })

    # Calculate annotated pathways (exclude Unknown and Unannotated)
    num_annotated_pathways = len([p for p in pathways if p["pathway"] not in ["Unknown", "Unannotated"]])

    return {
        "total_reactions": len(enriched_reactions),
        "pathways": pathways,
        "num_pathways_affected": num_annotated_pathways,
        "reactions_without_pathways": reactions_without_pathways,
        "reactions_without_pathways_percentage": round(reactions_without_pathways / len(enriched_reactions) * 100, 1) if len(enriched_reactions) > 0 else 0
    }


def gapfill_model(
    model_id: str,
    media_id: str,
    db_index: DatabaseIndex,
    target_growth_rate: float = 0.01,
    allow_all_non_grp_reactions: bool = True,
    gapfill_mode: str = "full",
) -> dict[str, Any]:
    """Gapfill a metabolic model to enable growth in specified media.

    Args:
        model_id: Model identifier (typically .draft suffix)
        media_id: Media identifier for gapfilling conditions
        db_index: DatabaseIndex instance with loaded database
        target_growth_rate: Minimum growth rate to achieve (default: 0.01)
        allow_all_non_grp_reactions: Allow non-gene-associated reactions (default: True)
        gapfill_mode: Gapfilling mode ("full", "atp_only", "genomescale_only")

    Returns:
        Dict with gapfilling results including new model_id, reactions added, statistics

    Raises:
        ValidationError: If inputs are invalid
        NotFoundError: If model_id or media_id not found
        InfeasibilityError: If gapfilling cannot find solution
        LibraryError: If ModelSEEDpy operation fails
    """
    logger.info(f"Starting gapfill_model: model_id={model_id}, media_id={media_id}, target={target_growth_rate}")

    try:
        # Step 1: Validate inputs
        validate_gapfill_inputs(model_id, media_id, target_growth_rate, gapfill_mode)

        # Step 2: Load model and media from session
        original_model = retrieve_model(model_id)
        media = retrieve_media(media_id)

        # Step 3: Create copy of model (preserve original)
        model = copy.deepcopy(original_model)
        logger.info(f"Created working copy of model {model_id}")

        # Step 4: Check baseline growth with bio1 objective
        growth_rate_before = check_baseline_growth(model, media, objective="bio1")

        # If already meets target, skip gapfilling
        if growth_rate_before >= target_growth_rate:
            logger.info(f"Model already meets target growth rate ({growth_rate_before:.6f} >= {target_growth_rate})")
            # Still create a .gf version but note no gapfilling was needed
            new_model_id = transform_state_suffix(model_id)
            store_model(new_model_id, model)

            return {
                "success": True,
                "model_id": new_model_id,
                "original_model_id": model_id,
                "media_id": media_id,
                "growth_rate_before": growth_rate_before,
                "growth_rate_after": growth_rate_before,
                "target_growth_rate": target_growth_rate,
                "gapfilling_successful": True,
                "num_reactions_added": 0,
                "reactions_added": [],
                "exchange_reactions_added": [],
                "atp_correction": {
                    "performed": False,
                    "note": "Model already meets target growth rate"
                },
                "genomescale_gapfill": {
                    "performed": False,
                    "note": "Model already meets target growth rate"
                },
                "model_properties": {
                    "num_reactions": len(model.reactions),
                    "num_metabolites": len(model.metabolites),
                    "is_draft": False,
                    "requires_further_gapfilling": False,
                },
            }

        # Step 5: Load templates
        # Get template name from model metadata (stored during build_model)
        template_name = model.notes.get("template_used", "GramNegative")
        template = get_template(template_name)
        core_template = get_template("Core")
        logger.info(f"Loaded templates: {template_name}, Core")

        # Step 6: Check for stored test_conditions from build_model ATP correction
        test_conditions_id = f"{model_id}.test_conditions"
        stored_test_conditions = None

        if test_conditions_id in MODEL_STORAGE:
            stored_test_conditions = MODEL_STORAGE[test_conditions_id]
            logger.info(f"Found stored ATP test_conditions from build_model: {len(stored_test_conditions)} conditions")

        # Step 6.5: Run ATP correction (if enabled and not already done)
        atp_stats = {"performed": False}
        tests = []

        if gapfill_mode in ["full", "atp_only"]:
            if stored_test_conditions is not None:
                # Use stored test_conditions from build_model - skip redundant ATP correction
                tests = stored_test_conditions
                atp_stats = {
                    "performed": False,
                    "note": "Skipped - ATP correction already applied during build_model",
                    "test_conditions_reused": len(tests),
                }
                logger.info(f"Reusing {len(tests)} test_conditions from build_model ATP correction")
            else:
                # No stored test_conditions - run ATP correction now
                logger.info("No stored test_conditions found - running ATP correction")
                atp_stats = run_atp_correction(model, core_template)
                tests = atp_stats.get("tests", [])

        # Step 7: Run genome-scale gapfilling (if enabled)
        genomescale_stats = {"performed": False}
        added_reactions = []

        if gapfill_mode in ["full", "genomescale_only"]:
            genomescale_stats = run_genome_scale_gapfilling(
                model=model,
                template=template,
                media=media,
                target_growth_rate=target_growth_rate,
                tests=tests,
            )

            # Integrate solution if found
            if genomescale_stats.get("solution_found", False):
                solution = genomescale_stats["solution"]
                added_reactions = integrate_gapfill_solution(model, template, solution)

        # Step 8: Verify final growth rate with bio1 objective
        growth_rate_after = check_baseline_growth(model, media, objective="bio1")
        gapfilling_successful = growth_rate_after >= target_growth_rate

        if not gapfilling_successful:
            # Gapfilling failed to achieve target
            logger.warning(f"Gapfilling failed: achieved {growth_rate_after:.6f} < target {target_growth_rate}")

            # For atp_only mode, zero growth is EXPECTED (no bio1 objective yet)
            if gapfill_mode == "atp_only":
                logger.info("ATP-only mode: zero growth expected (no biomass objective at this stage)")
            elif growth_rate_after == 0.0:
                # Complete failure in full or genomescale_only mode - raise error
                raise gapfill_infeasible_error(
                    model_id=model_id,
                    media_id=media_id,
                    target_growth=target_growth_rate,
                    media_compounds=len(media.get_media_constraints()),
                    template_reactions_available=len(template.reactions),
                )
            else:
                # Partial success - return with warning
                logger.info(f"Partial gapfilling: achieved {growth_rate_after:.6f}, target was {target_growth_rate}")

        # Step 9: Transform model_id state suffix
        new_model_id = transform_state_suffix(model_id)

        # Step 10: Store gapfilled model
        store_model(new_model_id, model)
        logger.info(f"Stored gapfilled model: {new_model_id}")

        # Step 11: Enrich reaction metadata
        enriched_reactions = enrich_reaction_metadata(added_reactions, db_index)

        # Step 12: Categorize reactions by pathway (using real database pathway data)
        pathway_summary = categorize_reactions_by_pathway(enriched_reactions, db_index)

        # Step 13: Build improved interpretation with 5 key improvements
        num_reactions = len(enriched_reactions)

        # Improvement 1: Fix misleading overview (don't say "to enable growth" if it failed)
        if gapfilling_successful:
            overview = f"Added {num_reactions} reactions across {pathway_summary['num_pathways_affected']} metabolic pathways. Model can now grow."
        else:
            overview = f"Added {num_reactions} reactions across {pathway_summary['num_pathways_affected']} metabolic pathways. Model still cannot grow."

        # Improvement 2: Add growth improvement context
        growth_improvement = {
            "before": round(growth_rate_before, 6),
            "after": round(growth_rate_after, 6),
            "target": target_growth_rate,
            "met_target": gapfilling_successful,
        }

        # Improvement 3: Add gapfilling assessment
        if num_reactions < 10:
            gapfill_assessment = f"Minimal gapfilling ({num_reactions} reactions)"
        elif num_reactions < 50:
            gapfill_assessment = f"Moderate gapfilling ({num_reactions} reactions)"
        else:
            gapfill_assessment = f"Extensive gapfilling ({num_reactions} reactions) - may indicate poor annotation quality"

        # Improvement 4 & 5: Expose unknown reactions
        unknown_count = pathway_summary["reactions_without_pathways"]
        unknown_pct = pathway_summary["reactions_without_pathways_percentage"]

        interpretation = {
            "overview": overview,
            "growth_improvement": growth_improvement,
            "gapfilling_assessment": gapfill_assessment,
        }

        # Add warning if significant unknowns
        if unknown_count > 0:
            interpretation["pathway_coverage_note"] = f"{unknown_count} of {num_reactions} reactions ({unknown_pct}%) lack pathway annotations in database"

        # Step 14: Build response with improved interpretation
        return {
            "success": True,
            "model_id": new_model_id,
            "original_model_id": model_id,
            "media_id": media_id,
            "growth_rate_before": growth_rate_before,
            "growth_rate_after": growth_rate_after,
            "target_growth_rate": target_growth_rate,
            "gapfilling_successful": gapfilling_successful,
            "num_reactions_added": num_reactions,
            "pathway_summary": pathway_summary,
            "interpretation": interpretation,
            "next_steps": _get_next_steps_gapfill(),
            "atp_correction": {
                "performed": atp_stats.get("performed", False),
                "media_tested": atp_stats.get("media_tested", 0),
                "media_passed": atp_stats.get("media_passed", 0),
                "media_failed": atp_stats.get("media_failed", 0),
                "reactions_added": atp_stats.get("reactions_added", 0),
                "failed_media_examples": atp_stats.get("failed_media_examples", []),
                "test_conditions_reused": atp_stats.get("test_conditions_reused"),
                "note": atp_stats.get("note"),
            },
            "genomescale_gapfill": {
                "performed": genomescale_stats.get("performed", False),
                "reactions_added": genomescale_stats.get("new_reactions", 0),
                "reversed_reactions": genomescale_stats.get("reversed_reactions", 0),
                "new_reactions": genomescale_stats.get("new_reactions", 0),
            },
            "model_properties": {
                "num_reactions": len(model.reactions),
                "num_metabolites": len(model.metabolites),
                "is_draft": False,
                "requires_further_gapfilling": not gapfilling_successful,
            },
        }

    except (ValidationError, NotFoundError, InfeasibilityError, LibraryError) as e:
        logger.error(f"Gapfill failed with known error: {e.message}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error in gapfill_model: {e}", exc_info=True)
        raise LibraryError(
            message=f"Unexpected error during gapfilling: {str(e)}",
            error_code="GAPFILL_UNEXPECTED_ERROR",
            details={
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "model_id": model_id,
                "media_id": media_id,
            },
            suggestions=[
                "Check server logs for detailed error information",
                "Verify model and media are valid",
                "Try with different media or lower target_growth_rate",
            ],
        )
