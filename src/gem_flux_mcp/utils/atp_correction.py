"""
ATP correction utilities for metabolic model building.

This module implements ATP correction workflow using ModelSEEDpy's MSATPCorrection class.
ATP correction improves model accuracy by:
1. Testing ATP production across multiple media conditions
2. Expanding models to genome scale with additional reactions
3. Creating test conditions for multi-media validation during gapfilling
4. Ensuring biologically realistic ATP metabolism constraints

This results in more constrained, biologically realistic growth predictions.
"""

from typing import Any, Optional
from modelseedpy import MSATPCorrection
from modelseedpy.core.msatpcorrection import load_default_medias

from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.errors import LibraryError

logger = get_logger(__name__)


def apply_atp_correction(
    model: Any,
    core_template: Any,
    compartment: str = "c0",
    atp_hydrolysis_id: str = "ATPM_c0",
) -> tuple[Any, list[dict[str, Any]]]:
    """Apply ATP correction to a metabolic model.

    This performs the full ATP correction workflow:
    1. Loads default media for ATP testing
    2. Evaluates model growth on different media
    3. Applies media-specific gapfilling to enable ATP production
    4. Expands model to genome scale
    5. Builds test conditions for subsequent gapfilling

    Args:
        model: COBRApy Model object (will be modified in-place)
        core_template: MSTemplate object for core metabolism (typically Core template)
        compartment: Compartment ID for ATP hydrolysis reaction (default: "c0")
        atp_hydrolysis_id: ATP maintenance reaction ID (default: "ATPM_c0")

    Returns:
        Tuple of (modified_model, test_conditions)
        - modified_model: Model expanded to genome scale with ATP corrections
        - test_conditions: List of test condition dicts for gapfilling

    Raises:
        LibraryError: If ATP correction workflow fails

    Example:
        >>> from modelseedpy import MSBuilder
        >>> from gem_flux_mcp.templates.loader import get_template
        >>> from gem_flux_mcp.utils.atp_correction import apply_atp_correction
        >>>
        >>> # Build base model
        >>> template = get_template("GramNegative")
        >>> builder = MSBuilder(genome, template, "model_id")
        >>> model = builder.build_base_model("model_id")
        >>> builder.add_atpm(model)
        >>>
        >>> # Apply ATP correction
        >>> core_template = get_template("Core")
        >>> model, test_conditions = apply_atp_correction(model, core_template)
        >>>
        >>> # Now use test_conditions in gapfilling
        >>> gapfill = MSGapfill(model, test_conditions=test_conditions, ...)
    """
    try:
        logger.info("Starting ATP correction workflow...")

        # Load default media for ATP testing
        default_medias = load_default_medias()
        logger.info(f"Loaded {len(default_medias)} default media for ATP testing")

        # Initialize ATP correction
        atp_correction = MSATPCorrection(
            model,
            core_template,
            default_medias,
            compartment=compartment,
            atp_hydrolysis_id=atp_hydrolysis_id,
            load_default_medias=False,  # We already loaded them
        )

        # Run ATP correction workflow
        logger.info("Evaluating growth media...")
        media_eval = atp_correction.evaluate_growth_media()

        logger.info("Determining growth media...")
        atp_correction.determine_growth_media()

        logger.info("Applying growth media gapfilling...")
        atp_correction.apply_growth_media_gapfilling()

        # Critical step: expand model to genome scale
        logger.info("Expanding model to genome scale...")
        atp_correction.expand_model_to_genome_scale()

        # Build test conditions for subsequent gapfilling
        logger.info("Building test conditions...")
        test_conditions = atp_correction.build_tests()

        logger.info(f"ATP correction completed: model has {len(model.reactions)} reactions, {len(test_conditions)} test conditions")

        return model, test_conditions

    except Exception as e:
        raise LibraryError(
            message=f"ATP correction workflow failed: {e}",
            error_code="ATP_CORRECTION_ERROR",
            details={
                "stage": "atp_correction_workflow",
                "error": str(e),
                "compartment": compartment,
                "atp_hydrolysis_id": atp_hydrolysis_id,
            },
            suggestions=[
                "Ensure Core template is available.",
                "Check that ATPM reaction exists in model.",
                "If problem persists, try setting apply_atp_correction=False.",
            ],
        )


def get_atp_correction_statistics(
    original_num_reactions: int,
    corrected_num_reactions: int,
    test_conditions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Get statistics about ATP correction results.

    Args:
        original_num_reactions: Number of reactions before ATP correction
        corrected_num_reactions: Number of reactions after ATP correction
        test_conditions: Test conditions created by ATP correction

    Returns:
        Dict with ATP correction statistics
    """
    reactions_added = corrected_num_reactions - original_num_reactions

    # Extract media names from test conditions
    media_names = [tc.get("media", {}).id if hasattr(tc.get("media", {}), "id") else "unknown" for tc in test_conditions]

    return {
        "atp_correction_applied": True,
        "reactions_before_correction": original_num_reactions,
        "reactions_after_correction": corrected_num_reactions,
        "reactions_added_by_correction": reactions_added,
        "num_test_conditions": len(test_conditions),
        "test_media": media_names[:10] if len(media_names) > 10 else media_names,  # Limit for readability
        "biological_realism": "enhanced",
        "expected_growth_impact": "More constrained, biologically realistic growth rates",
    }
