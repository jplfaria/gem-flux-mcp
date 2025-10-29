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
    compartment: str = "e0"
) -> None:
    """Apply media constraints to model using COBRApy's .medium property.

    This is the canonical pattern for media application in COBRApy. It converts
    ModelSEEDpy MSMedia constraints or dict-based constraints to the COBRApy
    .medium format.

    The .medium property in COBRApy modifies exchange reactions to allow/prevent
    metabolite uptake and secretion.

    Args:
        model: COBRApy Model object (modified in place)
        media: MSMedia object or dict with media constraints
        compartment: Extracellular compartment ID (default: "e0")

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
        - MSMedia.get_media_constraints() returns compound IDs as keys
        - We must convert compound IDs to exchange reaction IDs (add "EX_" prefix)
        - COBRApy .medium property expects positive uptake rates
        - Use math.fabs() to convert negative lower bounds to positive uptake rates
    """
    medium = {}

    if hasattr(media, "get_media_constraints"):
        # MSMedia object - use get_media_constraints() method
        logger.debug("Applying MSMedia constraints using .get_media_constraints()")
        media_constraints = media.get_media_constraints(cmp=compartment)

        for compound_id, (lower_bound, upper_bound) in media_constraints.items():
            # Convert compound ID to exchange reaction ID
            # cpd00027_e0 → EX_cpd00027_e0
            exchange_rxn_id = f"EX_{compound_id}"

            if exchange_rxn_id in model.reactions:
                # COBRApy .medium expects positive values for max uptake rate
                # Negative lower_bound (-5) becomes positive uptake (5)
                medium[exchange_rxn_id] = math.fabs(lower_bound)
            else:
                logger.debug(f"Exchange reaction {exchange_rxn_id} not in model")

    elif isinstance(media, dict):
        # Dict format - check for "compounds" or "bounds" keys
        logger.debug("Applying dict-based media constraints")

        # Try "compounds" key first (predefined media format)
        bounds_dict = media.get("compounds", media.get("bounds", {}))

        for compound_id, (lower_bound, upper_bound) in bounds_dict.items():
            # Ensure compound has compartment suffix
            if not compound_id.endswith(f"_{compartment}"):
                compound_id = f"{compound_id}_{compartment}"

            # Convert to exchange reaction ID
            exchange_rxn_id = f"EX_{compound_id}"

            if exchange_rxn_id in model.reactions:
                medium[exchange_rxn_id] = math.fabs(lower_bound)
            else:
                logger.debug(f"Exchange reaction {exchange_rxn_id} not in model")

    else:
        raise TypeError(
            f"media must be MSMedia object or dict, got {type(media).__name__}"
        )

    # Apply medium using COBRApy's .medium property
    # This sets exchange reaction bounds according to COBRApy conventions
    model.medium = medium
    logger.info(f"Applied media to {len(medium)} exchange reactions")
