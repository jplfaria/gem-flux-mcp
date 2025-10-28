"""
ATP gapfill media loader module.

This module provides functions to load default ATP gapfilling media at server startup.
These media are used by MSATPCorrection for ATP metabolism validation during gapfilling.

According to spec 015-mcp-server-setup.md:
- Load default ATP gapfilling media (54 media compositions)
- Used by MSATPCorrection for ATP metabolism validation
- Returns list of tuples: [(media, min_objective), ...]
- If loading fails, log warning and continue (ATP correction can be skipped)
"""

import logging
from typing import Any

from modelseedpy.core.msatpcorrection import load_default_medias
from modelseedpy.core.msmedia import MSMedia

logger = logging.getLogger(__name__)

# Global cache for ATP media (populated at startup)
ATP_MEDIA_CACHE: list[tuple[MSMedia, float]] = []


def load_atp_media(media_path: str | None = None) -> list[tuple[MSMedia, float]]:
    """Load default ATP gapfilling media at server startup.

    This function loads the 54 default media compositions used by MSATPCorrection
    to validate ATP production pathways across different growth conditions.

    Args:
        media_path: Optional path to custom ATP media file (default: use ModelSEEDpy default)

    Returns:
        List of tuples (MSMedia, min_objective) where:
        - MSMedia: Media composition object
        - min_objective: Minimum objective value for that media (typically 0.01)

    Raises:
        Warning logged if loading fails (non-fatal, ATP correction can be skipped)
    """
    try:
        # Call ModelSEEDpy's load_default_medias function
        # Returns: [(MSMedia, min_obj), (MSMedia, min_obj), ...]
        atp_medias = load_default_medias(default_media_path=media_path)

        # Log success
        num_media = len(atp_medias)
        logger.info(f"✓ Loaded {num_media} ATP test media conditions")

        # Update global cache
        global ATP_MEDIA_CACHE
        ATP_MEDIA_CACHE.clear()
        ATP_MEDIA_CACHE.extend(atp_medias)

        return atp_medias

    except FileNotFoundError as e:
        logger.warning(
            f"ATP media file not found: {e}. "
            "ATP correction will be unavailable during gapfilling. "
            "This is non-fatal, but gapfilling may be less robust."
        )
        return []

    except Exception as e:
        logger.warning(
            f"Failed to load ATP gapfilling media: {e}. "
            "ATP correction will be unavailable during gapfilling. "
            "Server will continue without ATP media."
        )
        return []


def get_atp_media() -> list[tuple[MSMedia, float]]:
    """Get cached ATP media.

    Returns:
        List of (MSMedia, min_objective) tuples from cache

    Note:
        Returns empty list if ATP media failed to load during startup.
        This is non-fatal; gapfilling can proceed without ATP correction.
    """
    return ATP_MEDIA_CACHE.copy()


def has_atp_media() -> bool:
    """Check if ATP media are available.

    Returns:
        True if ATP media loaded successfully, False otherwise
    """
    return len(ATP_MEDIA_CACHE) > 0


def get_atp_media_info() -> list[dict[str, Any]]:
    """Get metadata about available ATP media.

    Returns:
        List of dicts with media info (id, name, num_compounds, min_objective)
    """
    media_info = []

    for media, min_obj in ATP_MEDIA_CACHE:
        # Count compounds in media (media is dict-like with compound IDs as keys)
        num_compounds = len(media.mediacompounds) if hasattr(media, 'mediacompounds') else 0

        media_info.append({
            "id": media.id,
            "name": media.name,
            "num_compounds": num_compounds,
            "min_objective": min_obj
        })

    return media_info
