"""
Session storage for models and media.

This module provides in-memory session-based storage for metabolic models
and media compositions. Storage is cleared when the server restarts.
"""

from gem_flux_mcp.storage.models import (
    store_model,
    retrieve_model,
    list_model_ids,
    model_exists,
    delete_model,
    clear_all_models,
    generate_model_id,
    generate_model_id_from_name,
    transform_state_suffix,
    get_model_count,
)

from gem_flux_mcp.storage.media import (
    store_media,
    retrieve_media,
    list_media_ids,
    media_exists,
    delete_media,
    clear_all_media,
    generate_media_id,
    get_media_count,
)

from gem_flux_mcp.storage.initialization import (
    StorageConfig,
    initialize_storage,
    shutdown_storage,
    get_storage_config,
    check_storage_limits,
    load_config_from_env,
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
