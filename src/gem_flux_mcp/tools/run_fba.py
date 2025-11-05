"""
run_fba tool for executing flux balance analysis on metabolic models.

This module implements the run_fba MCP tool according to specification
006-run-fba-tool.md. It executes FBA using COBRApy to predict growth rates
and metabolic fluxes under specified media conditions.

Tool Capabilities:
    - Execute flux balance analysis (FBA)
    - Apply media constraints to exchange reactions
    - Optimize objective function (default: biomass)
    - Return flux distributions with compound names
    - Handle infeasible and unbounded models

FBA Workflow:
    1. Load model and media from session
    2. Apply media constraints to exchange reactions
    3. Set objective function
    4. Execute FBA optimization
    5. Extract and filter fluxes by threshold
    6. Query database for compound/reaction names
    7. Return results with uptake/secretion summary

What this tool does NOT do (MVP):
    - Does not modify the model (read-only)
    - Does not perform iterative optimization
    - Does not validate biological feasibility
    - Does not analyze pathway essentiality
    - Does not compute flux variability (FVA)
    - Does not minimize total flux (pFBA)
"""

import copy
from typing import Any

from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.errors import (
    InfeasibilityError,
    NotFoundError,
    ValidationError,
    build_error_response,
    media_not_found_error,
    model_not_found_error,
)
from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.storage.media import (
    MEDIA_STORAGE,
    media_exists,
    retrieve_media,
)
from gem_flux_mcp.storage.models import (
    MODEL_STORAGE,
    model_exists,
    retrieve_model,
)
from gem_flux_mcp.utils.media import apply_media_to_model

logger = get_logger(__name__)


# =============================================================================
# Helper Functions for Prompts
# =============================================================================


def _get_next_steps_run_fba() -> list[str]:
    """Get next_steps from centralized prompt."""
    from gem_flux_mcp.prompts import render_prompt
    next_steps_text = render_prompt("next_steps/run_fba")
    return [
        line.strip()[2:].strip()
        for line in next_steps_text.split("\n")
        if line.strip().startswith("-")
    ]


# =============================================================================
# Validation Functions
# =============================================================================


def validate_fba_inputs(
    model_id: str,
    media_id: str,
    objective: str,
    flux_threshold: float,
) -> None:
    """Validate run_fba input parameters.

    Args:
        model_id: Model identifier to analyze
        media_id: Media identifier for growth conditions
        objective: Objective reaction ID to optimize
        flux_threshold: Minimum flux value to report

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

    # Validate flux_threshold is positive
    if flux_threshold < 0:
        raise ValidationError(
            message="flux_threshold must be a positive number",
            error_code="INVALID_FLUX_THRESHOLD",
            details={
                "provided_threshold": flux_threshold,
                "minimum": 0,
            },
            suggestions=[
                "Use a positive threshold value (e.g., 1e-6)",
                "Default threshold is 1e-6 if not specified",
            ],
        )


def get_compound_name_safe(db_index: DatabaseIndex, compound_id: str) -> str:
    """Get compound name from database, return ID if not found.

    Args:
        db_index: Database index for lookups
        compound_id: ModelSEED compound ID (without compartment)

    Returns:
        Compound name or original ID if not found
    """
    try:
        compound = db_index.get_compound(compound_id)
        return compound.name
    except Exception:
        return compound_id


def get_reaction_name_safe(db_index: DatabaseIndex, reaction_id: str) -> str:
    """Get reaction name from database, return ID if not found.

    Args:
        db_index: Database index for lookups
        reaction_id: Reaction ID (may include compartment suffix)

    Returns:
        Reaction name or original ID if not found
    """
    try:
        # Remove compartment suffix if present
        base_rxn_id = reaction_id.split("_")[0]
        reaction = db_index.get_reaction(base_rxn_id)
        return reaction.name
    except Exception:
        return reaction_id


def extract_fluxes(
    solution: Any,
    flux_threshold: float,
    db_index: DatabaseIndex,
) -> dict[str, Any]:
    """Extract and organize fluxes from FBA solution.

    Args:
        solution: COBRApy optimization solution
        flux_threshold: Minimum absolute flux to include
        db_index: Database index for compound/reaction lookups

    Returns:
        Dictionary with organized flux data:
        - fluxes: All significant fluxes
        - uptake_fluxes: Exchange reactions with negative flux
        - secretion_fluxes: Exchange reactions with positive flux
        - active_reactions: Count of reactions with flux
        - total_flux: Sum of absolute flux values
    """
    # Get flux distribution from solution
    all_fluxes = solution.fluxes.to_dict()

    # Filter by threshold
    significant_fluxes = {
        rxn_id: flux
        for rxn_id, flux in all_fluxes.items()
        if abs(flux) > flux_threshold
    }

    # Separate exchange reactions
    uptake_fluxes = []
    secretion_fluxes = []

    for rxn_id, flux in significant_fluxes.items():
        if rxn_id.startswith("EX_"):
            # Extract compound ID from exchange reaction
            # Format: EX_cpd00027_e0 -> cpd00027
            cpd_id_with_comp = rxn_id[3:]  # Remove "EX_"
            cpd_id = cpd_id_with_comp.rsplit("_", 1)[0]  # Remove compartment

            # Get compound metadata
            compound_name = get_compound_name_safe(db_index, cpd_id)

            flux_entry = {
                "compound_id": cpd_id,
                "compound_name": compound_name,
                "flux": round(flux, 6),
                "reaction_id": rxn_id,
            }

            if flux < 0:
                # Negative flux = uptake
                uptake_fluxes.append(flux_entry)
            else:
                # Positive flux = secretion
                secretion_fluxes.append(flux_entry)

    # Sort uptake by absolute flux (largest first)
    uptake_fluxes.sort(key=lambda x: abs(x["flux"]), reverse=True)

    # Sort secretion by flux (largest first)
    secretion_fluxes.sort(key=lambda x: x["flux"], reverse=True)

    # Calculate statistics
    active_reactions = len(significant_fluxes)
    total_flux = sum(abs(f) for f in significant_fluxes.values())

    # Get top fluxes for highlighting
    top_fluxes = []
    sorted_fluxes = sorted(
        significant_fluxes.items(),
        key=lambda x: abs(x[1]),
        reverse=True,
    )[:10]

    for rxn_id, flux in sorted_fluxes:
        reaction_name = get_reaction_name_safe(db_index, rxn_id)
        direction = "forward" if flux > 0 else "reverse"

        top_fluxes.append({
            "reaction_id": rxn_id,
            "reaction_name": reaction_name,
            "flux": round(flux, 6),
            "direction": direction,
        })

    return {
        "fluxes": {k: round(v, 6) for k, v in significant_fluxes.items()},
        "uptake_fluxes": uptake_fluxes,
        "secretion_fluxes": secretion_fluxes,
        "active_reactions": active_reactions,
        "total_flux": round(total_flux, 6),
        "top_fluxes": top_fluxes,
    }


def run_fba(
    model_id: str,
    media_id: str,
    db_index: DatabaseIndex,
    objective: str = "bio1",
    maximize: bool = True,
    flux_threshold: float = 1e-6,
) -> dict[str, Any]:
    """Execute flux balance analysis on a metabolic model.

    Args:
        model_id: Model identifier from session storage
        media_id: Media identifier from session storage
        db_index: Database index for compound/reaction name lookups
        objective: Objective reaction to optimize (default: "bio1")
        maximize: Whether to maximize (True) or minimize (False) objective
        flux_threshold: Minimum absolute flux to report (default: 1e-6)

    Returns:
        Dictionary with FBA results:
        - success: True if optimal solution found
        - objective_value: Optimized objective value
        - status: Solver status ("optimal", "infeasible", "unbounded")
        - fluxes: Significant reaction fluxes
        - uptake_fluxes: Uptake reactions with compound names
        - secretion_fluxes: Secretion reactions with compound names
        - summary: High-level statistics

    Raises:
        ValidationError: If inputs are invalid
        NotFoundError: If model_id or media_id not found
        InfeasibilityError: If FBA is infeasible or unbounded
    """
    try:
        # Step 1: Validate inputs
        logger.info(f"Starting FBA: model={model_id}, media={media_id}")
        validate_fba_inputs(model_id, media_id, objective, flux_threshold)

        # Step 2: Load model and media from storage
        original_model = retrieve_model(model_id)
        media = retrieve_media(media_id)

        # Create a copy to avoid modifying stored model
        model = copy.deepcopy(original_model)

        # Step 3: Apply media constraints
        # Use reset_exchange_bounds=False to preserve gapfilled exchanges
        apply_media_to_model(model, media, compartment="e0", reset_exchange_bounds=False)

        # Step 4: Verify objective reaction exists
        if objective not in model.reactions:
            available_objectives = ["bio1", "ATPM_c0"]
            raise ValidationError(
                message=f"Objective reaction '{objective}' not found in model",
                error_code="INVALID_OBJECTIVE",
                details={
                    "requested_objective": objective,
                    "model_id": model_id,
                    "suggested_objectives": available_objectives,
                    "total_reactions": len(model.reactions),
                },
                suggestions=[
                    "Use 'bio1' for growth optimization",
                    "Use 'ATPM_c0' for ATP maintenance",
                    "Specify a valid reaction ID from the model",
                ],
            )

        # Step 5: Set objective
        model.objective = objective

        # Step 5b: Set optimization direction explicitly
        # CRITICAL: COBRApy has two separate concepts:
        # - model.objective: which reaction(s) to optimize
        # - model.objective_direction: whether to maximize or minimize
        # Setting model.objective alone doesn't change the direction!
        if maximize:
            model.objective_direction = "max"
        else:
            model.objective_direction = "min"

        # Step 6: Execute FBA
        logger.info(f"Running FBA with objective={objective}, maximize={maximize}")
        solution = model.optimize()

        # Step 7: Check solution status
        status = solution.status

        if status == "infeasible":
            # Model cannot grow in this medium
            raise InfeasibilityError(
                message="Model has no feasible solution in the specified media",
                error_code="MODEL_INFEASIBLE",
                details={
                    "model_id": model_id,
                    "media_id": media_id,
                    "objective": objective,
                    "num_constraints": len(model.metabolites),
                    "num_variables": len(model.reactions),
                },
                suggestions=[
                    "Model may need gapfilling. Use gapfill_model tool first.",
                    "Check that media contains essential nutrients (C, N, P, S sources)",
                    "Verify exchange reactions exist for media compounds",
                ],
            )

        if status == "unbounded":
            # Objective can grow infinitely (model error)
            # Find unbounded exchange reactions
            unbounded_exchanges = []
            for rxn in model.reactions:
                if rxn.id.startswith("EX_"):
                    if rxn.lower_bound == float("-inf") or rxn.upper_bound == float("inf"):
                        unbounded_exchanges.append(rxn.id)

            raise InfeasibilityError(
                message="Model objective is unbounded (can grow infinitely)",
                error_code="MODEL_UNBOUNDED",
                details={
                    "model_id": model_id,
                    "media_id": media_id,
                    "objective": objective,
                    "unbounded_exchanges": unbounded_exchanges[:10],  # Limit to 10
                    "unbounded_count": len(unbounded_exchanges),
                },
                suggestions=[
                    "Check that all exchange reactions have finite bounds",
                    "Verify media was applied correctly",
                    "This indicates a model error - rebuild the model",
                ],
            )

        if status != "optimal":
            # Unknown solver status
            raise InfeasibilityError(
                message=f"FBA solver returned unexpected status: {status}",
                error_code="SOLVER_ERROR",
                details={
                    "model_id": model_id,
                    "media_id": media_id,
                    "solver_status": status,
                },
                suggestions=[
                    "This is a rare solver issue",
                    "Try rebuilding the model",
                    "Check model for numerical issues",
                ],
            )

        # Step 8: Extract fluxes and build response
        logger.info(f"FBA optimal: objective_value={solution.objective_value:.6f}")

        # Extract and organize fluxes (using db_index parameter)
        flux_data = extract_fluxes(solution, flux_threshold, db_index)

        # Build summary statistics
        summary = {
            "uptake_reactions": len(flux_data["uptake_fluxes"]),
            "secretion_reactions": len(flux_data["secretion_fluxes"]),
            "internal_reactions": (
                flux_data["active_reactions"]
                - len(flux_data["uptake_fluxes"])
                - len(flux_data["secretion_fluxes"])
            ),
        }

        # Calculate biological interpretations
        growth_rate = solution.objective_value

        # Identify metabolism type based on uptake
        has_oxygen = any(f["compound_id"] == "cpd00007" for f in flux_data["uptake_fluxes"])
        metabolism_type = "Aerobic respiration" if has_oxygen else "Anaerobic/fermentation"

        # Main carbon source
        carbon_sources = ["cpd00027", "cpd00029", "cpd00020"]  # glucose, acetate, pyruvate
        main_carbon = None
        for f in flux_data["uptake_fluxes"]:
            if f["compound_id"] in carbon_sources:
                main_carbon = f["compound_id"]
                break

        # Build success response with interpretation
        response = {
            "success": True,
            "model_id": model_id,
            "media_id": media_id,
            "objective_reaction": objective,
            "objective_value": round(growth_rate, 6),
            "status": "optimal",
            "solver_status": status,
            "interpretation": {
                "growth_rate_per_hour": round(growth_rate, 3),
                "metabolism_type": metabolism_type,
                "carbon_source": main_carbon if main_carbon else "Unknown",
                "growth_assessment": (
                    "Fast growth" if growth_rate > 0.5 else
                    "Moderate growth" if growth_rate > 0.1 else
                    "Slow growth" if growth_rate > 0.01 else
                    "Very slow growth"
                ),
                "model_status": "Model is viable and can grow in specified media"
            },
            "next_steps": _get_next_steps_run_fba(),
            "active_reactions": flux_data["active_reactions"],
            "total_reactions": len(model.reactions),
            "total_flux": flux_data["total_flux"],
            "fluxes": flux_data["fluxes"],
            "uptake_fluxes": flux_data["uptake_fluxes"],
            "secretion_fluxes": flux_data["secretion_fluxes"],
            "summary": summary,
            "top_fluxes": flux_data["top_fluxes"],
        }

        logger.info(
            f"FBA completed: {flux_data['active_reactions']} active reactions, "
            f"{summary['uptake_reactions']} uptake, "
            f"{summary['secretion_reactions']} secretion"
        )

        return response

    except (ValidationError, NotFoundError, InfeasibilityError) as e:
        # Known errors - build error response
        logger.error(f"FBA failed: {e.message}")
        return build_error_response(e, "run_fba")

    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error in run_fba: {e}")
        return {
            "success": False,
            "error_type": "ServerError",
            "message": f"Internal server error during FBA: {str(e)}",
            "details": {
                "model_id": model_id,
                "media_id": media_id,
            },
            "suggestion": "This is an unexpected error. Please report this issue.",
        }
