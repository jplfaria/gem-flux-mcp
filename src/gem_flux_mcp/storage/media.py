"""
Media storage module for session-based in-memory media storage.

This module implements media storage, retrieval, and ID generation
according to specification 010-model-storage.md.
"""

import random
import string
import time
from typing import Any

from gem_flux_mcp.errors import media_not_found_error
from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)

# In-memory media storage (session-scoped)
# Format: {"media_id": MSMedia object}
MEDIA_STORAGE: dict[str, Any] = {}


def generate_media_id() -> str:
    """Generate unique media ID.

    Returns:
        Media ID like "media_20251027_143052_x1y2z3"

    Format:
        media_{timestamp}_{random}
        - timestamp: YYYYMMDD_HHMMSS format
        - random: 6 alphanumeric characters (lowercase letters and digits)
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_suffix = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=6)
    )
    return f"media_{timestamp}_{random_suffix}"


def store_media(media_id: str, media: Any) -> None:
    """Store a media composition in session storage.

    Args:
        media_id: Unique media identifier
        media: MSMedia object

    Raises:
        ValueError: If media_id is empty or media is None
        RuntimeError: If media_id already exists (collision)
    """
    if not media_id:
        raise ValueError("media_id cannot be empty")
    if media is None:
        raise ValueError("media cannot be None")

    # Check for collision
    if media_id in MEDIA_STORAGE:
        logger.error(f"Media ID collision detected: {media_id}")
        raise RuntimeError(
            f"Media ID '{media_id}' already exists in storage. "
            f"This should not happen with proper ID generation."
        )

    MEDIA_STORAGE[media_id] = media
    logger.info(f"Stored media: {media_id}")


def retrieve_media(media_id: str) -> Any:
    """Retrieve a media composition from session storage.

    Args:
        media_id: Media identifier

    Returns:
        MSMedia object

    Raises:
        ValueError: If media_id is empty
        KeyError: If media_id not found (use media_exists to check first)
    """
    if not media_id:
        raise ValueError("media_id cannot be empty")

    if media_id not in MEDIA_STORAGE:
        available = list(MEDIA_STORAGE.keys())
        error = media_not_found_error(
            media_id=media_id,
            available_media=available,
        )
        raise KeyError(error.message)

    return MEDIA_STORAGE[media_id]


def media_exists(media_id: str) -> bool:
    """Check if a media composition exists in storage.

    Args:
        media_id: Media identifier

    Returns:
        True if media exists, False otherwise
    """
    return media_id in MEDIA_STORAGE


def list_media_ids() -> list[str]:
    """List all media IDs in storage.

    Returns:
        List of media IDs sorted alphabetically
    """
    return sorted(MEDIA_STORAGE.keys())


def delete_media(media_id: str) -> None:
    """Delete a media composition from storage.

    Args:
        media_id: Media identifier to delete

    Raises:
        ValueError: If media_id is empty
        KeyError: If media_id not found
    """
    if not media_id:
        raise ValueError("media_id cannot be empty")

    if media_id not in MEDIA_STORAGE:
        available = list(MEDIA_STORAGE.keys())
        error = media_not_found_error(
            media_id=media_id,
            available_media=available,
        )
        raise KeyError(error.message)

    del MEDIA_STORAGE[media_id]
    logger.info(f"Deleted media: {media_id}")


def clear_all_media() -> int:
    """Clear all media from storage.

    Returns:
        Number of media cleared
    """
    count = len(MEDIA_STORAGE)
    MEDIA_STORAGE.clear()
    logger.info(f"Cleared {count} media from storage")
    return count


def get_media_count() -> int:
    """Get the number of media in storage.

    Returns:
        Number of media currently stored
    """
    return len(MEDIA_STORAGE)
