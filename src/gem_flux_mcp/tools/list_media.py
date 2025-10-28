"""List media tool for session management.

This module implements the list_media MCP tool for querying all media
in the current session according to specification 018-session-management-tools.md.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.media.predefined import PREDEFINED_MEDIA_IDS, PREDEFINED_MEDIA_TIMESTAMP
from gem_flux_mcp.storage.media import MEDIA_STORAGE
from gem_flux_mcp.types import (
    ListMediaResponse,
    MediaInfo,
    ErrorResponse,
)
# No error imports needed - we return simple error response dicts

logger = get_logger(__name__)


def extract_media_name(media_id: str) -> Optional[str]:
    """Extract user-provided or predefined name from media_id.

    Args:
        media_id: Media identifier

    Returns:
        Name if predefined or None if auto-generated

    Examples:
        >>> extract_media_name("media_20251027_143052_x1y2z3")
        None
        >>> extract_media_name("glucose_minimal_aerobic")
        'glucose_minimal_aerobic'
    """
    # Auto-generated format: media_{timestamp}_{random}
    if media_id.startswith("media_"):
        return None

    # Predefined media use fixed names
    if media_id in PREDEFINED_MEDIA_IDS:
        return media_id

    # Unknown format - return None
    return None


def extract_media_metadata(media_id: str, media: Any, db_index=None) -> MediaInfo:
    """Extract metadata from MSMedia object.

    Args:
        media_id: Media identifier
        media: MSMedia object (dict format for MVP)
        db_index: Optional database index for compound name lookup

    Returns:
        MediaInfo with all metadata fields
    """
    # Extract media name
    media_name = extract_media_name(media_id)

    # Get number of compounds
    # Media is stored as dict: {"cpd00027_e0": (lower, upper), ...}
    if isinstance(media, dict):
        num_compounds = len(media)
    else:
        # Handle MSMedia object (if used in future)
        num_compounds = len(getattr(media, "mediacompounds", {}))

    # Classify as minimal vs rich
    media_type = "minimal" if num_compounds < 50 else "rich"

    # Get first 3 compounds for preview
    compounds_preview: List[Dict[str, str]] = []
    if isinstance(media, dict):
        compound_ids = sorted(media.keys())[:3]
        for cpd_full_id in compound_ids:
            # Strip compartment suffix (_e0) to get base compound ID
            cpd_id = cpd_full_id.replace("_e0", "")

            # Get name from database if available
            cpd_name = "Unknown"
            if db_index:
                try:
                    cpd_info = db_index.get_compound(cpd_id)
                    if cpd_info:
                        cpd_name = cpd_info.get("name", "Unknown")
                except Exception:
                    pass

            compounds_preview.append({"id": cpd_id, "name": cpd_name})

    # Get creation timestamp (fallback to current time if not stored)
    # For predefined media, use a fixed timestamp
    if media_id in PREDEFINED_MEDIA_IDS:
        created_at_str = PREDEFINED_MEDIA_TIMESTAMP
    else:
        created_at_str = datetime.utcnow().isoformat() + "Z"

    return MediaInfo(
        media_id=media_id,
        media_name=media_name,
        num_compounds=num_compounds,
        media_type=media_type,
        compounds_preview=compounds_preview,
        created_at=created_at_str,
        is_predefined=(media_id in PREDEFINED_MEDIA_IDS),
    )


def list_media(db_index=None) -> Union[ListMediaResponse, ErrorResponse]:
    """List all media in current session.

    Args:
        db_index: Optional database index for enriching compound names

    Returns:
        ListMediaResponse with media metadata or ErrorResponse
    """
    try:
        # Query all media from storage
        all_media_ids = sorted(MEDIA_STORAGE.keys())

        # Extract metadata
        media_list: List[MediaInfo] = []
        predefined_count = 0
        user_created_count = 0

        for media_id in all_media_ids:
            media = MEDIA_STORAGE[media_id]
            metadata = extract_media_metadata(media_id, media, db_index)
            media_list.append(metadata)

            # Count predefined vs user-created
            if media_id in PREDEFINED_MEDIA_IDS:
                predefined_count += 1
            else:
                user_created_count += 1

        # Sort by created_at (oldest first)
        media_list.sort(key=lambda m: m.created_at)

        # Build response
        response = ListMediaResponse(
            success=True,
            media=media_list,
            total_media=len(media_list),
            predefined_media=predefined_count,
            user_created_media=user_created_count,
        )

        logger.info(
            f"Listed {len(media_list)} media "
            f"(predefined: {predefined_count}, user-created: {user_created_count})"
        )

        return response

    except Exception as e:
        logger.error(f"Error in list_media: {e}", exc_info=True)
        return ErrorResponse(
            success=False,
            error_type="ServerError",
            message=f"Failed to list media: {str(e)}",
            details={"exception": str(e)},
            suggestion="Check server logs for details.",
        )
