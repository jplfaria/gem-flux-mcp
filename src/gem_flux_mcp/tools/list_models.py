"""List models tool for session management.

This module implements the list_models MCP tool for querying all models
in the current session according to specification 018-session-management-tools.md.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.storage.models import MODEL_STORAGE
from gem_flux_mcp.types import (
    ListModelsRequest,
    ListModelsResponse,
    ModelInfo,
    ErrorResponse,
)
# No error imports needed - we return simple error response dicts

logger = get_logger(__name__)


def classify_model_state(model_id: str) -> str:
    """Determine model state from model_id suffix.

    Args:
        model_id: Model identifier with state suffix

    Returns:
        "draft" or "gapfilled"

    Rules:
        - .draft → "draft"
        - .gf or .draft.gf or any suffix containing .gf → "gapfilled"
    """
    if ".gf" in model_id:
        return "gapfilled"
    elif model_id.endswith(".draft"):
        return "draft"
    else:
        # Fallback: assume draft if no clear indicator
        return "draft"


def extract_model_name(model_id: str) -> Optional[str]:
    """Extract user-provided name from model_id.

    Args:
        model_id: Model identifier

    Returns:
        User name if model uses custom naming, None if auto-generated

    Examples:
        >>> extract_model_name("model_20251027_143052_abc123.draft")
        None
        >>> extract_model_name("E_coli_K12.draft")
        'E_coli_K12'
    """
    # Auto-generated format: model_{timestamp}_{random}.{state}
    if model_id.startswith("model_"):
        return None

    # User-provided: extract base name before first dot
    base_name = model_id.split(".")[0]
    return base_name


def extract_model_metadata(model_id: str, model: Any) -> ModelInfo:
    """Extract metadata from COBRApy Model object.

    Args:
        model_id: Model identifier
        model: COBRApy Model object

    Returns:
        ModelInfo with all metadata fields
    """
    # Determine state from ID
    state = classify_model_state(model_id)

    # Extract user name if present
    model_name = extract_model_name(model_id)

    # Get basic statistics
    num_reactions = len(model.reactions)
    num_metabolites = len(model.metabolites)
    num_genes = len(model.genes)

    # Get template from model notes (if available)
    template_used = getattr(model, "notes", {}).get("template_used", "Unknown")

    # Get creation timestamp from model notes (if available)
    # Fallback to current time if not stored
    created_at_str = getattr(model, "notes", {}).get("created_at")
    if not created_at_str:
        created_at_str = datetime.utcnow().isoformat() + "Z"
        logger.warning(
            f"Model '{model_id}' missing created_at timestamp, using current time. "
            "This may affect chronological sorting."
        )

    # Get parent model ID from notes (if available)
    derived_from = getattr(model, "notes", {}).get("derived_from", None)

    return ModelInfo(
        model_id=model_id,
        model_name=model_name,
        state=state,
        num_reactions=num_reactions,
        num_metabolites=num_metabolites,
        num_genes=num_genes,
        template_used=template_used,
        created_at=created_at_str,
        derived_from=derived_from,
    )


def list_models(
    request: ListModelsRequest,
) -> Union[ListModelsResponse, ErrorResponse]:
    """List all models in current session with filtering.

    Args:
        request: Filter parameters

    Returns:
        ListModelsResponse with model metadata or ErrorResponse

    Raises:
        ValueError: If filter_state is invalid
    """
    try:
        filter_state = request.filter_state.lower()

        # Validate filter_state
        valid_states = ["all", "draft", "gapfilled"]
        if filter_state not in valid_states:
            return ErrorResponse(
                success=False,
                error_type="ValidationError",
                message=f"Invalid filter_state: {filter_state}",
                details={
                    "provided": filter_state,
                    "valid_values": valid_states,
                },
                suggestion="Use 'all', 'draft', or 'gapfilled' for filter_state parameter.",
            )

        # Query all models from storage
        all_model_ids = sorted(MODEL_STORAGE.keys())

        # Extract metadata and apply filtering
        models: List[ModelInfo] = []
        state_counts = {"draft": 0, "gapfilled": 0}

        for model_id in all_model_ids:
            model = MODEL_STORAGE[model_id]
            metadata = extract_model_metadata(model_id, model)

            # Count by state
            state_counts[metadata.state] += 1

            # Apply filter
            if filter_state == "all":
                models.append(metadata)
            elif filter_state == "draft" and metadata.state == "draft":
                models.append(metadata)
            elif filter_state == "gapfilled" and metadata.state == "gapfilled":
                models.append(metadata)

        # Sort by created_at (oldest first)
        models.sort(key=lambda m: m.created_at)

        # Build response
        response = ListModelsResponse(
            success=True,
            models=models,
            total_models=len(models),
            models_by_state=state_counts,
        )

        logger.info(
            f"Listed {len(models)} models (filter: {filter_state}, "
            f"draft: {state_counts['draft']}, gapfilled: {state_counts['gapfilled']})"
        )

        return response

    except Exception as e:
        logger.error(f"Error in list_models: {e}", exc_info=True)
        return ErrorResponse(
            success=False,
            error_type="ServerError",
            message=f"Failed to list models: {str(e)}",
            details={"exception": str(e)},
            suggestion="Check server logs for details.",
        )
