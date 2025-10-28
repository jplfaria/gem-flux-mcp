"""
Unit tests for storage initialization module.

Tests storage initialization, configuration, limits, and shutdown behavior
according to specifications 010-model-storage.md and 015-mcp-server-setup.md.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from gem_flux_mcp.storage.initialization import (
    StorageConfig,
    initialize_storage,
    shutdown_storage,
    get_storage_config,
    check_storage_limits,
    load_config_from_env,
    DEFAULT_MAX_MODELS,
    DEFAULT_MAX_MEDIA,
)


class TestStorageConfig:
    """Test StorageConfig class."""

    def test_init_with_defaults(self):
        """Test StorageConfig initialization with default values."""
        config = StorageConfig()
        assert config.max_models == DEFAULT_MAX_MODELS
        assert config.max_media == DEFAULT_MAX_MEDIA

    def test_init_with_custom_values(self):
        """Test StorageConfig initialization with custom values."""
        config = StorageConfig(max_models=200, max_media=100)
        assert config.max_models == 200
        assert config.max_media == 100

    def test_init_with_zero_models_raises_error(self):
        """Test that zero max_models raises ValueError."""
        with pytest.raises(ValueError, match="max_models must be positive"):
            StorageConfig(max_models=0, max_media=50)

    def test_init_with_zero_media_raises_error(self):
        """Test that zero max_media raises ValueError."""
        with pytest.raises(ValueError, match="max_media must be positive"):
            StorageConfig(max_models=100, max_media=0)

    def test_init_with_negative_models_raises_error(self):
        """Test that negative max_models raises ValueError."""
        with pytest.raises(ValueError, match="max_models must be positive"):
            StorageConfig(max_models=-10, max_media=50)

    def test_init_with_negative_media_raises_error(self):
        """Test that negative max_media raises ValueError."""
        with pytest.raises(ValueError, match="max_media must be positive"):
            StorageConfig(max_models=100, max_media=-5)

    def test_repr(self):
        """Test string representation."""
        config = StorageConfig(max_models=150, max_media=75)
        assert repr(config) == "StorageConfig(max_models=150, max_media=75)"


class TestLoadConfigFromEnv:
    """Test loading configuration from environment variables."""

    def test_load_default_when_no_env_vars(self):
        """Test that defaults are used when no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            config = load_config_from_env()
            assert config.max_models == DEFAULT_MAX_MODELS
            assert config.max_media == DEFAULT_MAX_MEDIA

    def test_load_custom_max_models_from_env(self):
        """Test loading custom max_models from environment."""
        with patch.dict(os.environ, {"GEM_FLUX_MAX_MODELS": "200"}):
            config = load_config_from_env()
            assert config.max_models == 200
            assert config.max_media == DEFAULT_MAX_MEDIA

    def test_load_custom_max_media_from_env(self):
        """Test loading custom max_media from environment."""
        with patch.dict(os.environ, {"GEM_FLUX_MAX_MEDIA": "75"}):
            config = load_config_from_env()
            assert config.max_models == DEFAULT_MAX_MODELS
            assert config.max_media == 75

    def test_load_both_from_env(self):
        """Test loading both limits from environment."""
        with patch.dict(
            os.environ, {"GEM_FLUX_MAX_MODELS": "300", "GEM_FLUX_MAX_MEDIA": "150"}
        ):
            config = load_config_from_env()
            assert config.max_models == 300
            assert config.max_media == 150

    def test_invalid_max_models_uses_default(self, caplog):
        """Test that invalid max_models value uses default and logs warning."""
        with patch.dict(os.environ, {"GEM_FLUX_MAX_MODELS": "invalid"}):
            config = load_config_from_env()
            assert config.max_models == DEFAULT_MAX_MODELS
            assert "Invalid GEM_FLUX_MAX_MODELS value" in caplog.text

    def test_invalid_max_media_uses_default(self, caplog):
        """Test that invalid max_media value uses default and logs warning."""
        with patch.dict(os.environ, {"GEM_FLUX_MAX_MEDIA": "not_a_number"}):
            config = load_config_from_env()
            assert config.max_media == DEFAULT_MAX_MEDIA
            assert "Invalid GEM_FLUX_MAX_MEDIA value" in caplog.text


class TestInitializeStorage:
    """Test storage initialization."""

    def setup_method(self):
        """Clear storage before each test."""
        from gem_flux_mcp.storage.models import clear_all_models
        from gem_flux_mcp.storage.media import clear_all_media
        from gem_flux_mcp.storage import initialization

        clear_all_models()
        clear_all_media()
        initialization._storage_config = None

    def test_initialize_with_default_config(self, caplog):
        """Test initialization with default configuration."""
        import logging
        caplog.set_level(logging.INFO)

        config = initialize_storage()

        assert config.max_models == DEFAULT_MAX_MODELS
        assert config.max_media == DEFAULT_MAX_MEDIA
        assert "Initializing session storage" in caplog.text
        assert f"Storage limits: {DEFAULT_MAX_MODELS} models, {DEFAULT_MAX_MEDIA} media" in caplog.text

    def test_initialize_with_custom_config(self, caplog):
        """Test initialization with custom configuration."""
        import logging
        caplog.set_level(logging.INFO)

        custom_config = StorageConfig(max_models=200, max_media=100)
        config = initialize_storage(custom_config)

        assert config.max_models == 200
        assert config.max_media == 100
        assert "Storage limits: 200 models, 100 media" in caplog.text

    def test_initialize_from_env_vars(self, caplog):
        """Test initialization loads from environment variables."""
        import logging
        caplog.set_level(logging.INFO)

        with patch.dict(
            os.environ, {"GEM_FLUX_MAX_MODELS": "250", "GEM_FLUX_MAX_MEDIA": "125"}
        ):
            config = initialize_storage()

            assert config.max_models == 250
            assert config.max_media == 125
            assert "Storage limits: 250 models, 125 media" in caplog.text

    def test_initialize_logs_empty_storage(self, caplog):
        """Test initialization logs that storage is empty."""
        import logging
        caplog.set_level(logging.INFO)

        initialize_storage()
        assert "Storage initialized: 0 models, 0 media" in caplog.text

    def test_initialize_warns_if_storage_not_empty(self, caplog):
        """Test warning logged if storage not empty on initialization."""
        from gem_flux_mcp.storage.models import store_model

        # Create a mock model
        mock_model = MagicMock()
        store_model("model_test.draft", mock_model)

        initialize_storage()

        assert "Storage not empty on initialization" in caplog.text
        assert "1 models, 0 media (expected 0, 0)" in caplog.text

    def test_get_storage_config_after_init(self):
        """Test retrieving storage config after initialization."""
        custom_config = StorageConfig(max_models=175, max_media=90)
        initialize_storage(custom_config)

        config_dict = get_storage_config()
        assert config_dict["max_models"] == 175
        assert config_dict["max_media"] == 90

    def test_get_storage_config_before_init_raises_error(self):
        """Test that getting config before initialization raises error."""
        with pytest.raises(RuntimeError, match="Storage not initialized"):
            get_storage_config()


class TestShutdownStorage:
    """Test storage shutdown."""

    def setup_method(self):
        """Initialize storage and clear before each test."""
        from gem_flux_mcp.storage.models import clear_all_models
        from gem_flux_mcp.storage.media import clear_all_media
        from gem_flux_mcp.storage import initialization

        clear_all_models()
        clear_all_media()
        initialization._storage_config = None
        initialize_storage()

    def test_shutdown_empty_storage(self, caplog):
        """Test shutdown with empty storage."""
        import logging
        caplog.set_level(logging.INFO)

        models_cleared, media_cleared = shutdown_storage()

        assert models_cleared == 0
        assert media_cleared == 0
        assert "Shutting down session storage" in caplog.text
        assert "Storage cleared: 0 models, 0 media" in caplog.text

    def test_shutdown_with_models_and_media(self, caplog):
        """Test shutdown clears models and media."""
        import logging
        caplog.set_level(logging.INFO)

        from gem_flux_mcp.storage.models import store_model
        from gem_flux_mcp.storage.media import store_media

        # Add mock models and media
        mock_model = MagicMock()
        mock_media = MagicMock()

        store_model("model_1.draft", mock_model)
        store_model("model_2.draft", mock_model)
        store_media("media_1", mock_media)

        models_cleared, media_cleared = shutdown_storage()

        assert models_cleared == 2
        assert media_cleared == 1
        assert "Storage cleared: 2 models, 1 media" in caplog.text

    def test_shutdown_actually_clears_storage(self):
        """Test that shutdown actually clears storage dictionaries."""
        from gem_flux_mcp.storage.models import store_model, get_model_count
        from gem_flux_mcp.storage.media import store_media, get_media_count

        # Add items
        mock_model = MagicMock()
        mock_media = MagicMock()
        store_model("model_test.draft", mock_model)
        store_media("media_test", mock_media)

        assert get_model_count() == 1
        assert get_media_count() == 1

        # Shutdown
        shutdown_storage()

        # Verify cleared
        assert get_model_count() == 0
        assert get_media_count() == 0


class TestCheckStorageLimits:
    """Test storage limit checking."""

    def setup_method(self):
        """Initialize storage before each test."""
        from gem_flux_mcp.storage.models import clear_all_models
        from gem_flux_mcp.storage.media import clear_all_media
        from gem_flux_mcp.storage import initialization

        clear_all_models()
        clear_all_media()
        initialization._storage_config = None
        initialize_storage(StorageConfig(max_models=10, max_media=5))

    def test_check_limits_empty_storage(self):
        """Test checking limits with empty storage."""
        limits = check_storage_limits()

        assert limits["model_count"] == 0
        assert limits["model_limit"] == 10
        assert limits["model_usage_pct"] == 0.0
        assert limits["media_count"] == 0
        assert limits["media_limit"] == 5
        assert limits["media_usage_pct"] == 0.0
        assert limits["at_capacity"] is False

    def test_check_limits_with_some_storage(self):
        """Test checking limits with some items in storage."""
        from gem_flux_mcp.storage.models import store_model
        from gem_flux_mcp.storage.media import store_media

        mock_model = MagicMock()
        mock_media = MagicMock()

        # Add 5 models (50% of 10)
        for i in range(5):
            store_model(f"model_{i}.draft", mock_model)

        # Add 2 media (40% of 5)
        for i in range(2):
            store_media(f"media_{i}", mock_media)

        limits = check_storage_limits()

        assert limits["model_count"] == 5
        assert limits["model_usage_pct"] == 50.0
        assert limits["media_count"] == 2
        assert limits["media_usage_pct"] == 40.0
        assert limits["at_capacity"] is False

    def test_check_limits_at_80_percent_models(self):
        """Test at_capacity flag when models reach 80%."""
        from gem_flux_mcp.storage.models import store_model

        mock_model = MagicMock()

        # Add 8 models (80% of 10)
        for i in range(8):
            store_model(f"model_{i}.draft", mock_model)

        limits = check_storage_limits()

        assert limits["model_usage_pct"] == 80.0
        assert limits["at_capacity"] is True

    def test_check_limits_at_80_percent_media(self):
        """Test at_capacity flag when media reach 80%."""
        from gem_flux_mcp.storage.media import store_media

        mock_media = MagicMock()

        # Add 4 media (80% of 5)
        for i in range(4):
            store_media(f"media_{i}", mock_media)

        limits = check_storage_limits()

        assert limits["media_usage_pct"] == 80.0
        assert limits["at_capacity"] is True

    def test_check_limits_over_capacity(self):
        """Test at_capacity flag when exceeding 80%."""
        from gem_flux_mcp.storage.models import store_model

        mock_model = MagicMock()

        # Add 9 models (90% of 10)
        for i in range(9):
            store_model(f"model_{i}.draft", mock_model)

        limits = check_storage_limits()

        assert limits["model_usage_pct"] == 90.0
        assert limits["at_capacity"] is True

    def test_check_limits_before_init_raises_error(self):
        """Test that checking limits before initialization raises error."""
        from gem_flux_mcp.storage import initialization

        initialization._storage_config = None

        with pytest.raises(RuntimeError, match="Storage not initialized"):
            check_storage_limits()


class TestIntegrationScenarios:
    """Test complete initialization/shutdown scenarios."""

    def setup_method(self):
        """Clear storage before each test."""
        from gem_flux_mcp.storage.models import clear_all_models
        from gem_flux_mcp.storage.media import clear_all_media
        from gem_flux_mcp.storage import initialization

        clear_all_models()
        clear_all_media()
        initialization._storage_config = None

    def test_full_lifecycle(self, caplog):
        """Test complete storage lifecycle: init → use → shutdown."""
        import logging
        caplog.set_level(logging.INFO)

        from gem_flux_mcp.storage.models import store_model, get_model_count
        from gem_flux_mcp.storage.media import store_media, get_media_count

        # Step 1: Initialize
        config = initialize_storage(StorageConfig(max_models=50, max_media=25))
        assert "Initializing session storage" in caplog.text

        # Step 2: Use storage
        mock_model = MagicMock()
        mock_media = MagicMock()

        store_model("model_1.draft", mock_model)
        store_media("media_1", mock_media)

        assert get_model_count() == 1
        assert get_media_count() == 1

        # Step 3: Check limits
        limits = check_storage_limits()
        assert limits["model_count"] == 1
        assert limits["media_count"] == 1
        assert limits["at_capacity"] is False

        # Step 4: Shutdown
        models_cleared, media_cleared = shutdown_storage()
        assert models_cleared == 1
        assert media_cleared == 1
        assert "Shutting down session storage" in caplog.text

        # Step 5: Verify cleared
        assert get_model_count() == 0
        assert get_media_count() == 0

    def test_re_initialization_after_shutdown(self):
        """Test that storage can be re-initialized after shutdown."""
        # First initialization
        config1 = initialize_storage(StorageConfig(max_models=100, max_media=50))
        assert config1.max_models == 100

        # Shutdown
        shutdown_storage()

        # Re-initialize with different config
        config2 = initialize_storage(StorageConfig(max_models=200, max_media=100))
        assert config2.max_models == 200

        # Config should be updated
        new_config = get_storage_config()
        assert new_config["max_models"] == 200
        assert new_config["max_media"] == 100
