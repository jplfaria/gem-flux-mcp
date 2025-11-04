"""
Model storage module for session-based in-memory model storage.

This module implements model storage, retrieval, and ID generation
according to specification 010-model-storage.md.
"""

import time
import random
import string
from typing import Any, Optional

from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.errors import model_not_found_error, storage_collision_error

logger = get_logger(__name__)

# In-memory model storage (session-scoped)
# Format: {"model_id": cobra.Model object}
MODEL_STORAGE: dict[str, Any] = {}


def generate_model_id(state: str = "draft") -> str:
    """Generate unique auto-generated model ID.

    Args:
        state: Model state suffix ("draft", "gf", "draft.gf", etc.)

    Returns:
        Model ID like "model_20251027_143052_a3f9b2.draft"

    Raises:
        ValueError: If state is empty or None
    """
    if not state:
        raise ValueError("State parameter cannot be empty")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    random_suffix = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=6)
    )
    return f"model_{timestamp}_{random_suffix}.{state}"


def generate_model_id_from_name(
    model_name: str,
    state: str = "draft",
    existing_ids: Optional[set[str]] = None,
    max_retries: int = 10,
) -> str:
    """Generate model ID from user-provided name.

    Args:
        model_name: User's custom name (e.g., "E_coli_K12")
        state: Model state ("draft", "gf", "draft.gf", etc.)
        existing_ids: Set of existing model IDs to check collisions
        max_retries: Maximum retries to avoid collision (default: 10)

    Returns:
        Model ID with state suffix

    Raises:
        ValueError: If model_name or state is empty
        RuntimeError: If collision cannot be resolved after max_retries
    """
    if not model_name:
        raise ValueError("model_name cannot be empty")
    if not state:
        raise ValueError("State parameter cannot be empty")

    # Use MODEL_STORAGE if existing_ids not provided
    if existing_ids is None:
        existing_ids = set(MODEL_STORAGE.keys())

    base_id = f"{model_name}.{state}"

    # Check for collision
    if base_id not in existing_ids:
        return base_id

    # Collision detected - try appending timestamp
    for attempt in range(max_retries):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        # Add microseconds for uniqueness on fast retries
        microseconds = str(int(time.time() * 1000000) % 1000000).zfill(6)
        collision_id = f"{model_name}_{timestamp}_{microseconds}.{state}"

        if collision_id not in existing_ids:
            logger.warning(
                f"Model name collision for '{model_name}', using: {collision_id}"
            )
            return collision_id

        # Small delay to ensure timestamp changes
        time.sleep(0.001)

    # If we get here, we failed to resolve collision after max_retries
    raise RuntimeError(
        f"Failed to generate unique model ID for '{model_name}' after {max_retries} attempts"
    )


def transform_state_suffix(current_model_id: str) -> str:
    """Transform model ID state suffix for gapfilling.

    Args:
        current_model_id: Existing model ID with state suffix

    Returns:
        New model ID with updated state suffix

    Transformation rules:
        - .draft → .draft.gf
        - .gf → .gf.gf
        - .draft.gf → .draft.gf.gf
        - Any other .X → .X.gf

    Raises:
        ValueError: If model_id is invalid or has no state suffix

    Examples:
        >>> transform_state_suffix("model_abc.draft")
        'model_abc.draft.gf'
        >>> transform_state_suffix("model_abc.gf")
        'model_abc.gf.gf'
        >>> transform_state_suffix("model_abc.draft.gf")
        'model_abc.draft.gf.gf'
    """
    if not current_model_id:
        raise ValueError("model_id cannot be empty")

    # Find last dot to split base name and state
    if "." not in current_model_id:
        raise ValueError(f"Invalid model ID format (no state suffix): {current_model_id}")

    parts = current_model_id.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid model ID format: {current_model_id}")

    base_name, current_state = parts

    # Transform state based on current state
    if current_state == "draft":
        new_state = "draft.gf"
        # Keep same base name
        return f"{base_name}.{new_state}"
    else:
        # Append .gf for any other state
        return f"{current_model_id}.gf"


def store_model(model_id: str, model: Any, max_retries: int = 10) -> None:
    """Store a model in session storage.

    Args:
        model_id: Unique model identifier
        model: COBRApy Model object
        max_retries: Maximum collision retry attempts (default: 10)

    Raises:
        ValueError: If model_id is empty or model is None
        RuntimeError: If collision cannot be resolved after max_retries
    """
    if not model_id:
        raise ValueError("model_id cannot be empty")
    if model is None:
        raise ValueError("model cannot be None")

    # Check for collision
    if model_id in MODEL_STORAGE:
        # This should not happen if IDs are generated correctly
        # Try to resolve by regenerating ID
        logger.error(f"Model ID collision detected: {model_id}")
        raise RuntimeError(
            storage_collision_error(
                attempted_id=model_id,
                attempts=max_retries,
            )["message"]
        )

    MODEL_STORAGE[model_id] = model
    logger.info(f"Stored model: {model_id}")


def retrieve_model(model_id: str) -> Any:
    """Retrieve a model from session storage.

    Args:
        model_id: Model identifier

    Returns:
        COBRApy Model object

    Raises:
        ValueError: If model_id is empty
        KeyError: If model_id not found (use model_exists to check first)
    """
    if not model_id:
        raise ValueError("model_id cannot be empty")

    if model_id not in MODEL_STORAGE:
        available = list(MODEL_STORAGE.keys())
        error = model_not_found_error(
            model_id=model_id,
            available_models=available,
        )
        raise KeyError(error.message)

    return MODEL_STORAGE[model_id]


def model_exists(model_id: str) -> bool:
    """Check if a model exists in storage.

    Args:
        model_id: Model identifier

    Returns:
        True if model exists, False otherwise
    """
    return model_id in MODEL_STORAGE


def list_model_ids() -> list[str]:
    """List all model IDs in storage.

    Returns:
        List of model IDs sorted alphabetically
    """
    return sorted(MODEL_STORAGE.keys())


def delete_model(model_id: str) -> None:
    """Delete a model from storage.

    Args:
        model_id: Model identifier to delete

    Raises:
        ValueError: If model_id is empty
        KeyError: If model_id not found
    """
    if not model_id:
        raise ValueError("model_id cannot be empty")

    if model_id not in MODEL_STORAGE:
        available = list(MODEL_STORAGE.keys())
        error = model_not_found_error(
            model_id=model_id,
            available_models=available,
        )
        raise KeyError(error.message)

    del MODEL_STORAGE[model_id]
    logger.info(f"Deleted model: {model_id}")


def clear_all_models() -> int:
    """Clear all models from storage.

    Returns:
        Number of models cleared
    """
    count = len(MODEL_STORAGE)
    MODEL_STORAGE.clear()
    logger.info(f"Cleared {count} models from storage")
    return count


def get_model_count() -> int:
    """Get the number of models in storage.

    Returns:
        Number of models currently stored
    """
    return len(MODEL_STORAGE)
