"""Predefined media library loader.

This module loads predefined growth media from JSON files at server startup
according to specification 019-predefined-media-library.md.
"""

import json
from pathlib import Path
from typing import Any, Dict

from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.media.predefined import PREDEFINED_MEDIA_IDS, PREDEFINED_MEDIA_TIMESTAMP

logger = get_logger(__name__)

# Cache for predefined media (loaded once at startup)
PREDEFINED_MEDIA_CACHE: Dict[str, Any] = {}


def load_predefined_media(media_dir: str = "data/media") -> Dict[str, Any]:
    """Load predefined media library from JSON files.

    Loads all JSON files from the media directory and converts them to
    MSMedia objects. Media are stored with their name as the media_id
    (e.g., "glucose_minimal_aerobic") for easy reference.

    Args:
        media_dir: Directory containing media JSON files (default: "data/media")

    Returns:
        Dictionary mapping media names to MSMedia-compatible dictionaries

    Raises:
        DatabaseError: If media directory is missing or JSON files are invalid

    Example:
        >>> predefined = load_predefined_media()
        >>> len(predefined)
        4
        >>> "glucose_minimal_aerobic" in predefined
        True
    """
    media_path = Path(media_dir)

    # Validate media directory exists
    if not media_path.exists():
        logger.error(f"Media directory not found: {media_dir}")
        raise RuntimeError(f"Predefined media directory not found: {media_dir}")

    if not media_path.is_dir():
        logger.error(f"Media path is not a directory: {media_dir}")
        raise RuntimeError(f"Media path is not a directory: {media_dir}")

    # Load each JSON file
    predefined_media = {}
    json_files = list(media_path.glob("*.json"))

    if not json_files:
        logger.warning(f"No JSON files found in media directory: {media_dir}")
        return predefined_media

    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                media_def = json.load(f)

            # Validate media definition structure
            if "name" not in media_def:
                logger.error(f"Media definition missing 'name' field: {json_file}")
                continue

            if "compounds" not in media_def:
                logger.error(f"Media definition missing 'compounds' field: {json_file}")
                continue

            media_name = media_def["name"]

            # Convert to MSMedia-compatible format
            # MSMedia.from_dict() expects compound IDs WITHOUT compartment suffix
            # It will add _e0 internally when creating exchange reactions
            compounds_dict = {}
            for cpd_id, cpd_data in media_def["compounds"].items():
                # Do NOT add _e0 suffix - MSMedia.from_dict() adds it
                bounds = tuple(cpd_data["bounds"])  # Convert to tuple
                compounds_dict[cpd_id] = bounds

            # Store as dictionary (MSMedia object will be created when used)
            predefined_media[media_name] = {
                "name": media_name,
                "description": media_def.get("description", ""),
                "compounds": compounds_dict,
                "created_at": PREDEFINED_MEDIA_TIMESTAMP,
                "is_predefined": True,
            }

            logger.info(
                f"✓ Loaded predefined media: {media_name} ({len(compounds_dict)} compounds)"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON file {json_file}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error loading predefined media {json_file}: {e}")
            continue

    # Store in cache
    PREDEFINED_MEDIA_CACHE.clear()
    PREDEFINED_MEDIA_CACHE.update(predefined_media)

    logger.info(f"Loaded {len(predefined_media)} predefined media compositions")

    # Verify all expected media were loaded
    loaded_names = set(predefined_media.keys())
    missing = PREDEFINED_MEDIA_IDS - loaded_names
    if missing:
        logger.warning(f"Some expected predefined media were not loaded: {missing}")

    return predefined_media


def get_predefined_media(media_name: str) -> dict | None:
    """Get predefined media by name.

    Args:
        media_name: Name of predefined media (e.g., "glucose_minimal_aerobic")

    Returns:
        Media dictionary if found, None otherwise
    """
    return PREDEFINED_MEDIA_CACHE.get(media_name)


def has_predefined_media(media_name: str) -> bool:
    """Check if predefined media exists.

    Args:
        media_name: Name of predefined media

    Returns:
        True if media exists, False otherwise
    """
    return media_name in PREDEFINED_MEDIA_CACHE


def list_predefined_media_names() -> list[str]:
    """Get list of all predefined media names.

    Returns:
        List of media names (sorted alphabetically)
    """
    return sorted(PREDEFINED_MEDIA_CACHE.keys())


def get_predefined_media_count() -> int:
    """Get count of predefined media.

    Returns:
        Number of predefined media loaded
    """
    return len(PREDEFINED_MEDIA_CACHE)
