"""
Storage initialization and configuration module.

This module handles initialization of session storage on server startup,
including configuration of storage limits and cleanup on shutdown.

According to specification 010-model-storage.md and 015-mcp-server-setup.md.
"""

import os
from typing import Optional

from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)

# Storage limits (configurable via environment variables)
DEFAULT_MAX_MODELS = 100
DEFAULT_MAX_MEDIA = 50

# Global storage configuration
_storage_config: Optional[dict] = None


class StorageConfig:
    """Storage configuration for session-based storage."""

    def __init__(
        self,
        max_models: int = DEFAULT_MAX_MODELS,
        max_media: int = DEFAULT_MAX_MEDIA,
    ):
        """Initialize storage configuration.

        Args:
            max_models: Maximum number of models in session storage (default: 100)
            max_media: Maximum number of media in session storage (default: 50)

        Raises:
            ValueError: If limits are not positive integers
        """
        if max_models <= 0:
            raise ValueError(f"max_models must be positive, got {max_models}")
        if max_media <= 0:
            raise ValueError(f"max_media must be positive, got {max_media}")

        self.max_models = max_models
        self.max_media = max_media

    def __repr__(self) -> str:
        return f"StorageConfig(max_models={self.max_models}, max_media={self.max_media})"


def load_config_from_env() -> StorageConfig:
    """Load storage configuration from environment variables.

    Environment variables:
        GEM_FLUX_MAX_MODELS: Maximum models in storage (default: 100)
        GEM_FLUX_MAX_MEDIA: Maximum media in storage (default: 50)

    Returns:
        StorageConfig instance with loaded or default values
    """
    max_models = DEFAULT_MAX_MODELS
    max_media = DEFAULT_MAX_MEDIA

    # Load from environment if set
    if "GEM_FLUX_MAX_MODELS" in os.environ:
        try:
            max_models = int(os.environ["GEM_FLUX_MAX_MODELS"])
        except ValueError:
            logger.warning(
                f"Invalid GEM_FLUX_MAX_MODELS value: {os.environ['GEM_FLUX_MAX_MODELS']}, "
                f"using default: {DEFAULT_MAX_MODELS}"
            )

    if "GEM_FLUX_MAX_MEDIA" in os.environ:
        try:
            max_media = int(os.environ["GEM_FLUX_MAX_MEDIA"])
        except ValueError:
            logger.warning(
                f"Invalid GEM_FLUX_MAX_MEDIA value: {os.environ['GEM_FLUX_MAX_MEDIA']}, "
                f"using default: {DEFAULT_MAX_MEDIA}"
            )

    return StorageConfig(max_models=max_models, max_media=max_media)


def initialize_storage(config: Optional[StorageConfig] = None) -> StorageConfig:
    """Initialize session storage on server startup.

    This function:
    1. Loads configuration from environment or uses provided config
    2. Verifies storage dictionaries are empty (fresh start)
    3. Logs initialization complete with configuration

    Args:
        config: Optional StorageConfig instance (loads from env if None)

    Returns:
        StorageConfig instance that was used for initialization

    Note:
        Storage dictionaries (MODEL_STORAGE, MEDIA_STORAGE) are module-level
        globals that are already initialized empty. This function configures
        limits and logs startup.
    """
    global _storage_config

    # Import here to avoid circular dependency
    from gem_flux_mcp.storage.models import MODEL_STORAGE, get_model_count
    from gem_flux_mcp.storage.media import MEDIA_STORAGE, get_media_count

    # Load or use provided config
    if config is None:
        config = load_config_from_env()

    # Verify storage is empty (should be on fresh startup)
    model_count = get_model_count()
    media_count = get_media_count()

    if model_count > 0 or media_count > 0:
        logger.warning(
            f"Storage not empty on initialization: {model_count} models, "
            f"{media_count} media (expected 0, 0)"
        )

    # Store global config
    _storage_config = {
        "max_models": config.max_models,
        "max_media": config.max_media,
    }

    logger.info("Initializing session storage")
    logger.info(f"Storage limits: {config.max_models} models, {config.max_media} media")
    logger.info(
        f"Storage initialized: {len(MODEL_STORAGE)} models, {len(MEDIA_STORAGE)} media"
    )

    return config


def get_storage_config() -> dict:
    """Get current storage configuration.

    Returns:
        Dictionary with max_models and max_media limits

    Raises:
        RuntimeError: If storage not initialized yet
    """
    if _storage_config is None:
        raise RuntimeError(
            "Storage not initialized. Call initialize_storage() first."
        )
    return _storage_config.copy()


def shutdown_storage() -> tuple[int, int]:
    """Clean up storage on server shutdown.

    This function:
    1. Clears all models from storage
    2. Clears all media from storage
    3. Logs shutdown statistics

    Returns:
        Tuple of (models_cleared, media_cleared)

    Note:
        This is called during graceful server shutdown to free memory
        and log final statistics. After shutdown, storage dictionaries
        are empty and can be re-initialized.
    """
    # Import here to avoid circular dependency
    from gem_flux_mcp.storage.models import clear_all_models
    from gem_flux_mcp.storage.media import clear_all_media

    logger.info("Shutting down session storage")

    models_cleared = clear_all_models()
    media_cleared = clear_all_media()

    logger.info(
        f"Storage cleared: {models_cleared} models, {media_cleared} media"
    )

    return models_cleared, media_cleared


def check_storage_limits() -> dict:
    """Check storage usage against configured limits.

    Returns:
        Dictionary with:
            - model_count: Current number of models
            - model_limit: Maximum models allowed
            - model_usage_pct: Percentage of model limit used
            - media_count: Current number of media
            - media_limit: Maximum media allowed
            - media_usage_pct: Percentage of media limit used
            - at_capacity: True if either storage ≥ 80% full

    Raises:
        RuntimeError: If storage not initialized
    """
    if _storage_config is None:
        raise RuntimeError(
            "Storage not initialized. Call initialize_storage() first."
        )

    # Import here to avoid circular dependency
    from gem_flux_mcp.storage.models import get_model_count
    from gem_flux_mcp.storage.media import get_media_count

    model_count = get_model_count()
    media_count = get_media_count()

    model_usage_pct = (model_count / _storage_config["max_models"]) * 100
    media_usage_pct = (media_count / _storage_config["max_media"]) * 100

    at_capacity = model_usage_pct >= 80.0 or media_usage_pct >= 80.0

    return {
        "model_count": model_count,
        "model_limit": _storage_config["max_models"],
        "model_usage_pct": model_usage_pct,
        "media_count": media_count,
        "media_limit": _storage_config["max_media"],
        "media_usage_pct": media_usage_pct,
        "at_capacity": at_capacity,
    }
