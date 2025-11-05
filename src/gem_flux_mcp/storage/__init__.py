"""
Session storage for models and media.

This module provides in-memory session-based storage for metabolic models
and media compositions. Storage is cleared when the server restarts.
"""

from gem_flux_mcp.storage.initialization import (
    StorageConfig,
    check_storage_limits,
    get_storage_config,
    initialize_storage,
    load_config_from_env,
    shutdown_storage,
)
from gem_flux_mcp.storage.media import (
    clear_all_media,
    delete_media,
    generate_media_id,
    get_media_count,
    list_media_ids,
    media_exists,
    retrieve_media,
    store_media,
)
from gem_flux_mcp.storage.models import (
    clear_all_models,
    delete_model,
    generate_model_id,
    generate_model_id_from_name,
    get_model_count,
    list_model_ids,
    model_exists,
    retrieve_model,
    store_model,
    transform_state_suffix,
)

__all__ = [
    # Model storage
    "store_model",
    "retrieve_model",
    "list_model_ids",
    "model_exists",
    "delete_model",
    "clear_all_models",
    "generate_model_id",
    "generate_model_id_from_name",
    "transform_state_suffix",
    "get_model_count",
    # Media storage
    "store_media",
    "retrieve_media",
    "list_media_ids",
    "media_exists",
    "delete_media",
    "clear_all_media",
    "generate_media_id",
    "get_media_count",
    # Storage initialization
    "StorageConfig",
    "initialize_storage",
    "shutdown_storage",
    "get_storage_config",
    "check_storage_limits",
    "load_config_from_env",
]
