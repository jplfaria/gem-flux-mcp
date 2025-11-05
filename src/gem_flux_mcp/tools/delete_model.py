"""Delete model tool for session management.

This module implements the delete_model MCP tool for removing models
from the current session according to specification 018-session-management-tools.md.
"""

from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.storage.models import delete_model as storage_delete_model
from gem_flux_mcp.storage.models import model_exists
from gem_flux_mcp.types import (
    DeleteModelRequest,
    DeleteModelResponse,
    ErrorResponse,
)

# No error imports needed - we return simple error response dicts

logger = get_logger(__name__)


def delete_model(
    request: DeleteModelRequest,
) -> dict:
    """Delete a model from session storage.

    Args:
        request: Model ID to delete

    Returns:
        DeleteModelResponse on success or ErrorResponse on failure
    """
    try:
        model_id = request.model_id

        # Validate model_id not empty
        if not model_id or not model_id.strip():
            return ErrorResponse(
                success=False,
                error_type="ValidationError",
                message="Missing required parameter 'model_id'",
                details={"parameter": "model_id", "received": model_id},
                suggestion="Provide model_id to delete.",
            ).model_dump()

        # Check if model exists
        if not model_exists(model_id):
            from gem_flux_mcp.storage.models import list_model_ids

            available = list_model_ids()
            return ErrorResponse(
                success=False,
                error_type="ModelNotFound",
                message=f"Model '{model_id}' not found in session",
                details={
                    "model_id": model_id,
                    "available_models": available,
                },
                suggestion="Use list_models tool to see available models.",
            ).model_dump()

        # Delete the model
        storage_delete_model(model_id)

        logger.info(f"Deleted model: {model_id}")

        return DeleteModelResponse(
            success=True,
            deleted_model_id=model_id,
            message="Model deleted successfully",
        ).model_dump()

    except Exception as e:
        logger.error(f"Error in delete_model: {e}", exc_info=True)
        return ErrorResponse(
            success=False,
            error_type="ServerError",
            message=f"Failed to delete model: {str(e)}",
            details={"exception": str(e), "model_id": request.model_id},
            suggestion="Check server logs for details.",
        ).model_dump()
