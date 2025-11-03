"""Delete media from session storage.

This tool removes a media composition from the active session. It provides
structured error handling and validation to ensure safe media deletion.

Usage:
    from gem_flux_mcp.tools.delete_media import delete_media
    from gem_flux_mcp.types import DeleteMediaRequest

    request = DeleteMediaRequest(media_id="glucose_minimal_aerobic")
    response = delete_media(request)

    if response['success']:
        print(f"Deleted: {response['deleted_media_id']}")
"""

import logging

from gem_flux_mcp.storage.media import delete_media as storage_delete_media
from gem_flux_mcp.storage.media import media_exists
from gem_flux_mcp.types import DeleteMediaRequest, DeleteMediaResponse, ErrorResponse

logger = logging.getLogger(__name__)


def delete_media(request: DeleteMediaRequest) -> dict:
    """Delete a media composition from session storage.

    Args:
        request: DeleteMediaRequest with media_id

    Returns:
        DeleteMediaResponse on success, ErrorResponse on failure

    Error cases:
        - ValidationError: Empty media_id
        - MediaNotFound: media_id doesn't exist in session
        - ServerError: Unexpected deletion failure
    """
    try:
        media_id = request.media_id

        # Validate media_id not empty
        if not media_id or not media_id.strip():
            return ErrorResponse(
                success=False,
                error_type="ValidationError",
                message="Missing required parameter 'media_id'",
                details={"parameter": "media_id", "received": media_id},
                suggestion="Provide media_id to delete.",
            ).model_dump()

        # Check if media exists
        if not media_exists(media_id):
            from gem_flux_mcp.storage.media import list_media_ids
            available = list_media_ids()
            return ErrorResponse(
                success=False,
                error_type="MediaNotFound",
                message=f"Media '{media_id}' not found in session",
                details={"media_id": media_id, "available_media": available},
                suggestion="Use list_media tool to see available media.",
            ).model_dump()

        # Delete the media
        storage_delete_media(media_id)
        logger.info(f"Deleted media: {media_id}")

        return DeleteMediaResponse(
            success=True,
            deleted_media_id=media_id,
            message="Media deleted successfully",
        ).model_dump()

    except Exception as e:
        logger.error(f"Error in delete_media: {e}", exc_info=True)
        return ErrorResponse(
            success=False,
            error_type="ServerError",
            message=f"Failed to delete media: {str(e)}",
            details={"exception": str(e), "media_id": request.media_id},
            suggestion="Check server logs for details.",
        ).model_dump()
