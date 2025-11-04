"""Shared media application utilities.

This module provides common functions for applying media constraints to
COBRApy models using the canonical .medium property pattern.
"""

import logging
import math
from typing import Any, Union

import cobra

logger = logging.getLogger(__name__)


def apply_media_to_model(
    model: cobra.Model,
    media: Any,
    compartment: str = "e0",
    reset_exchange_bounds: bool = False
) -> None:
    """Apply media constraints using COBRApy's model.medium property.

    This function uses COBRApy's canonical model.medium property to apply media
    constraints. This ensures compatibility with COBRApy's constraint management
    and matches the reference notebook implementation.

    IMPORTANT: COBRApy's model.medium property:
    1. Closes ALL exchange reactions first (sets bounds to 0)
    2. Then opens only exchanges present in the medium dict
    3. Sets lower_bound = -uptake_rate (from medium dict)
    4. Sets upper_bound = 1000 (COBRApy default for secretion)

    The reset_exchange_bounds parameter is kept for API compatibility but has no
    effect since model.medium always resets exchanges.

    Args:
        model: COBRApy Model object (modified in place)
        media: MSMedia object or dict with media constraints
        compartment: Extracellular compartment ID (default: "e0")
        reset_exchange_bounds: Deprecated - has no effect (kept for compatibility)

    Example with MSMedia:
        ```python
        from modelseedpy import MSMedia
        media = MSMedia.from_dict({"cpd00027": (-5, 100), "cpd00007": (-10, 100)})
        apply_media_to_model(model, media)
        ```

    Example with dict:
        ```python
        media_dict = {
            "compounds": {
                "cpd00027": (-5, 100),
                "cpd00007": (-10, 100)
            }
        }
        apply_media_to_model(model, media_dict)
        ```

    Notes:
        - Uses math.fabs(lower_bound) to convert negative bounds to positive uptake rates
        - model.medium dict format: {exchange_id: uptake_rate} where uptake_rate > 0
        - Matches reference notebook implementation (build_model.ipynb)
    """
    media_constraints = {}

    if hasattr(media, "get_media_constraints"):
        # MSMedia object - use get_media_constraints() method
        logger.debug("Applying MSMedia constraints using .get_media_constraints()")
        media_constraints = media.get_media_constraints(cmp=compartment)
        logger.debug(f"Media constraints returned {len(media_constraints)} compounds")

    elif isinstance(media, dict):
        # Dict format - check for "compounds" or "bounds" keys
        logger.debug("Applying dict-based media constraints")

        # Try "compounds" key first (predefined media format)
        bounds_dict = media.get("compounds", media.get("bounds", {}))

        # Convert to media_constraints format
        for compound_id, bounds in bounds_dict.items():
            # Ensure compound has compartment suffix
            if not compound_id.endswith(f"_{compartment}"):
                compound_id = f"{compound_id}_{compartment}"

            # bounds can be tuple (lb, ub) or dict with "bounds" key
            if isinstance(bounds, tuple):
                media_constraints[compound_id] = bounds
            elif isinstance(bounds, dict) and "bounds" in bounds:
                media_constraints[compound_id] = tuple(bounds["bounds"])
            else:
                logger.warning(f"Skipping {compound_id}: invalid bounds format {bounds}")

    else:
        raise TypeError(
            f"media must be MSMedia object or dict, got {type(media).__name__}"
        )

    if len(media_constraints) == 0:
        logger.error(f"NO media constraints found!")
        raise ValueError(
            f"Failed to parse media: no compound constraints found. "
            f"Check media format."
        )

    # Convert to COBRApy medium dict format: {exchange_id: uptake_rate}
    # This matches the reference notebook implementation (build_model.ipynb)
    medium = {}
    missing_exchanges = []

    # DEBUG: Count exchanges BEFORE applying media
    exchanges_before = [r.id for r in model.reactions if r.id.startswith("EX_")]
    open_before = [r.id for r in model.reactions if r.id.startswith("EX_") and (r.lower_bound < 0 or r.upper_bound > 0)]
    logger.info(f"BEFORE applying media: {len(exchanges_before)} total exchanges, {len(open_before)} open")

    for compound_id, (lower_bound, upper_bound) in media_constraints.items():
        # Convert compound ID to exchange reaction ID
        # cpd00027_e0 → EX_cpd00027_e0
        exchange_rxn_id = f"EX_{compound_id}"

        if exchange_rxn_id in model.reactions:
            # Use math.fabs(lb) to convert negative bound to positive uptake rate
            # This matches the notebook's integrate_to_model_medium() function
            uptake_rate = math.fabs(lower_bound)
            medium[exchange_rxn_id] = uptake_rate
            logger.debug(f"Adding {exchange_rxn_id} to medium: uptake_rate={uptake_rate}")
        else:
            missing_exchanges.append(exchange_rxn_id)
            logger.warning(f"Exchange reaction {exchange_rxn_id} not found in model (compound: {compound_id})")

    if len(medium) == 0:
        logger.error(f"NO exchange reactions matched! This will prevent growth.")
        logger.error(f"Media had {len(media_constraints)} constraints")
        logger.error(f"Model has {len([r for r in model.reactions if r.id.startswith('EX_')])} exchange reactions")
        logger.error(f"Missing exchanges: {missing_exchanges[:10]}")
        raise ValueError(
            f"Failed to apply media: no exchange reactions matched media constraints. "
            f"This would result in zero growth. Check exchange reaction naming."
        )

    # Apply using COBRApy's model.medium property
    # This closes ALL exchanges, then opens only those in medium dict
    # Sets lower_bound = -uptake_rate, upper_bound = 1000 (default)
    logger.info(f"Applying medium with {len(medium)} compounds using model.medium property")
    model.medium = medium

    # DEBUG: Count exchanges AFTER applying media
    open_after = [r.id for r in model.reactions if r.id.startswith("EX_") and (r.lower_bound < 0 or r.upper_bound > 0)]
    logger.info(f"AFTER applying media: {len(open_after)} open exchanges (was {len(open_before)})")
