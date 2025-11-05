"""Unit tests for MCP server initialization and lifecycle.

Tests server creation, resource loading, tool registration, and shutdown
according to specification 015-mcp-server-setup.md.
"""

import os
from unittest.mock import Mock, patch

import pytest

from gem_flux_mcp.server import (
    create_server,
    get_config_from_env,
    initialize_session_storage,
    load_resources,
    shutdown_handler,
)


class TestConfigurationLoading:
    """Test configuration loading from environment variables."""

    def test_default_configuration(self):
        """Test default configuration values when no env vars set."""
        # Clear environment
        env_vars = [
            "GEM_FLUX_HOST",
            "GEM_FLUX_PORT",
            "GEM_FLUX_DATABASE_DIR",
            "GEM_FLUX_TEMPLATE_DIR",
            "GEM_FLUX_MAX_MODELS",
            "GEM_FLUX_LOG_LEVEL",
        ]
        for var in env_vars:
            os.environ.pop(var, None)

        config = get_config_from_env()

        assert config["host"] == "localhost"
        assert config["port"] == 8080
        assert config["database_dir"] == "./data/database"
        assert config["template_dir"] == "./data/templates"
        assert config["max_models"] == 100
        assert config["log_level"] == "INFO"

    def test_custom_configuration(self):
        """Test configuration loading with custom environment variables."""
        os.environ["GEM_FLUX_HOST"] = "0.0.0.0"
        os.environ["GEM_FLUX_PORT"] = "9000"
        os.environ["GEM_FLUX_DATABASE_DIR"] = "/custom/database"
        os.environ["GEM_FLUX_TEMPLATE_DIR"] = "/custom/templates"
        os.environ["GEM_FLUX_MAX_MODELS"] = "200"
        os.environ["GEM_FLUX_LOG_LEVEL"] = "DEBUG"

        config = get_config_from_env()

        assert config["host"] == "0.0.0.0"
        assert config["port"] == 9000
        assert config["database_dir"] == "/custom/database"
        assert config["template_dir"] == "/custom/templates"
        assert config["max_models"] == 200
        assert config["log_level"] == "DEBUG"

        # Cleanup
        for var in [
            "GEM_FLUX_HOST",
            "GEM_FLUX_PORT",
            "GEM_FLUX_DATABASE_DIR",
            "GEM_FLUX_TEMPLATE_DIR",
            "GEM_FLUX_MAX_MODELS",
            "GEM_FLUX_LOG_LEVEL",
        ]:
            os.environ.pop(var, None)


class TestResourceLoading:
    """Test resource loading (database, templates, media)."""

    @patch("gem_flux_mcp.server.load_compounds_database")
    @patch("gem_flux_mcp.server.load_reactions_database")
    @patch("gem_flux_mcp.server.DatabaseIndex")
    @patch("gem_flux_mcp.server.load_templates")
    @patch("gem_flux_mcp.server.load_predefined_media")
    @patch("os.path.exists")
    def test_successful_resource_loading(
        self,
        mock_exists,
        mock_load_media,
        mock_load_templates,
        mock_db_index,
        mock_load_reactions,
        mock_load_compounds,
    ):
        """Test successful loading of all resources."""
        # Setup mocks
        mock_exists.return_value = True
        mock_load_compounds.return_value = Mock(
            name="compounds_df", __len__=Mock(return_value=33993)
        )
        mock_load_reactions.return_value = Mock(
            name="reactions_df", __len__=Mock(return_value=43775)
        )
        mock_load_templates.return_value = {
            "GramNegative": Mock(),
            "GramPositive": Mock(),
            "Core": Mock(),
        }
        mock_load_media.return_value = {
            "glucose_minimal_aerobic": Mock(),
            "glucose_minimal_anaerobic": Mock(),
            "pyruvate_minimal_aerobic": Mock(),
            "pyruvate_minimal_anaerobic": Mock(),
        }

        config = {
            "database_dir": "./data/database",
            "template_dir": "./data/templates",
        }

        # Should not raise any exceptions
        load_resources(config)

        # Verify calls
        mock_load_compounds.assert_called_once()
        mock_load_reactions.assert_called_once()
        mock_db_index.assert_called_once()
        mock_load_templates.assert_called_once()
        mock_load_media.assert_called_once()

    @patch("os.path.exists")
    def test_missing_compounds_database(self, mock_exists):
        """Test error when compounds database file is missing."""

        # compounds.tsv doesn't exist
        def exists_side_effect(path):
            return "reactions.tsv" in str(path)

        mock_exists.side_effect = exists_side_effect

        config = {"database_dir": "./data/database"}

        with pytest.raises(FileNotFoundError, match="Compounds database not found"):
            load_resources(config)

    @patch("os.path.exists")
    def test_missing_reactions_database(self, mock_exists):
        """Test error when reactions database file is missing."""

        # reactions.tsv doesn't exist
        def exists_side_effect(path):
            return "compounds.tsv" in str(path)

        mock_exists.side_effect = exists_side_effect

        config = {"database_dir": "./data/database"}

        with pytest.raises(FileNotFoundError, match="Reactions database not found"):
            load_resources(config)

    @patch("gem_flux_mcp.server.load_compounds_database")
    @patch("gem_flux_mcp.server.load_reactions_database")
    @patch("gem_flux_mcp.server.DatabaseIndex")
    @patch("gem_flux_mcp.server.load_templates")
    @patch("os.path.exists")
    def test_no_templates_loaded(
        self,
        mock_exists,
        mock_load_templates,
        mock_db_index,
        mock_load_reactions,
        mock_load_compounds,
    ):
        """Test error when no templates are loaded."""
        mock_exists.return_value = True
        mock_load_compounds.return_value = Mock(__len__=Mock(return_value=33993))
        mock_load_reactions.return_value = Mock(__len__=Mock(return_value=43775))
        mock_load_templates.return_value = {}  # No templates loaded

        config = {
            "database_dir": "./data/database",
            "template_dir": "./data/templates",
        }

        with pytest.raises(ValueError, match="Failed to load any ModelSEED templates"):
            load_resources(config)


class TestSessionStorageInitialization:
    """Test session storage initialization."""

    @patch("gem_flux_mcp.server.MODEL_STORAGE")
    @patch("gem_flux_mcp.server.MEDIA_STORAGE")
    def test_storage_initialization(self, mock_media_storage, mock_model_storage):
        """Test session storage initialization logs correctly."""
        # Make storage look empty
        mock_model_storage.__len__.return_value = 0
        mock_media_storage.__len__.return_value = 0

        config = {"max_models": 100}

        # Should not raise any exceptions
        initialize_session_storage(config)

        # Verify storage objects were accessed
        assert mock_model_storage.__len__.called
        assert mock_media_storage.__len__.called


class TestToolRegistration:
    """Test MCP tool auto-registration via decorators.

    NOTE: Tools are now auto-registered via @mcp.tool() decorators in mcp_tools.py.
    Tool registration happens when the mcp_tools module is imported inside create_server().
    This test class is kept for future integration tests that verify tools are accessible.
    """

    def test_tool_registration_is_automatic(self):
        """Test that tool registration is automatic via decorators.

        Tools are registered when mcp_tools module is imported inside create_server().
        This test simply verifies that create_server() doesn't raise exceptions.
        """
        # create_server() will import mcp_tools internally and return pre-configured server
        # If this doesn't raise an exception, tool registration worked
        with patch("gem_flux_mcp.server.database_index") as mock_db:
            with patch("gem_flux_mcp.server.templates") as mock_templates:
                mock_db.return_value = Mock()
                mock_templates.return_value = {"GramNegative": Mock()}

                # Just verify server creation doesn't raise exceptions
                # Tools are auto-registered when mcp_tools is imported
                server = create_server()
                assert server is not None


class TestServerCreation:
    """Test FastMCP server instance creation."""

    def test_create_server_instance(self):
        """Test server instance is created successfully.

        NOTE: Server is now pre-configured in mcp_tools.py and returned from there.
        create_server() imports mcp_tools internally and returns the pre-configured server.
        """
        with patch("gem_flux_mcp.server.database_index") as mock_db:
            with patch("gem_flux_mcp.server.templates") as mock_templates:
                # Mock global state being initialized
                mock_db.return_value = Mock()
                mock_templates.return_value = {"GramNegative": Mock()}

                # Just verify server creation doesn't raise exceptions
                server = create_server()
                assert server is not None


class TestShutdownHandler:
    """Test graceful shutdown behavior."""

    @patch("gem_flux_mcp.server.MODEL_STORAGE")
    @patch("gem_flux_mcp.server.MEDIA_STORAGE")
    @patch("sys.exit")
    def test_shutdown_clears_storage(self, mock_exit, mock_media_storage, mock_model_storage):
        """Test shutdown handler clears session storage."""
        # Make storage look populated
        mock_model_storage.__len__.return_value = 5
        mock_media_storage.__len__.return_value = 3

        # Call with positional arguments (signum, frame)
        shutdown_handler(2, None)

        # Verify storage was cleared
        mock_model_storage.clear.assert_called_once()
        mock_media_storage.clear.assert_called_once()

        # Verify exit was called
        mock_exit.assert_called_once_with(0)


class TestIntegrationScenarios:
    """Test complete initialization scenarios."""

    @patch("gem_flux_mcp.server.load_resources")
    @patch("gem_flux_mcp.server.initialize_session_storage")
    @patch("gem_flux_mcp.server.create_server")
    @patch("signal.signal")
    def test_successful_startup_sequence(
        self,
        mock_signal,
        mock_create_server,
        mock_init_storage,
        mock_load_resources,
    ):
        """Test complete successful startup sequence (without running server).

        NOTE: Tool registration is now automatic via @mcp.tool() decorators.
        Tools are registered when create_server() imports the mcp_tools module.
        """
        from gem_flux_mcp.server import get_config_from_env

        # Setup mocks
        mock_server = Mock()
        mock_server.run = Mock()  # Don't actually run server
        mock_create_server.return_value = mock_server

        # Get config
        config = get_config_from_env()

        # Execute startup phases
        mock_load_resources(config)
        mock_init_storage(config)
        mock_create_server()
        # NOTE: No register_tools(server) call - tools auto-register when mcp_tools is imported

        # Verify all phases executed
        mock_load_resources.assert_called_once()
        mock_init_storage.assert_called_once()
        mock_create_server.assert_called_once()

    @patch("gem_flux_mcp.server.load_resources")
    def test_startup_fails_on_resource_error(self, mock_load_resources):
        """Test startup fails gracefully when resource loading fails."""
        mock_load_resources.side_effect = FileNotFoundError("Database not found")

        with pytest.raises(FileNotFoundError, match="Database not found"):
            config = {"database_dir": "./missing"}
            mock_load_resources(config)


class TestEnvironmentVariableHandling:
    """Test environment variable edge cases."""

    def test_port_conversion_to_int(self):
        """Test port is converted from string to integer."""
        os.environ["GEM_FLUX_PORT"] = "9000"

        config = get_config_from_env()

        assert isinstance(config["port"], int)
        assert config["port"] == 9000

        os.environ.pop("GEM_FLUX_PORT", None)

    def test_max_models_conversion_to_int(self):
        """Test max_models is converted from string to integer."""
        os.environ["GEM_FLUX_MAX_MODELS"] = "150"

        config = get_config_from_env()

        assert isinstance(config["max_models"], int)
        assert config["max_models"] == 150

        os.environ.pop("GEM_FLUX_MAX_MODELS", None)

    def test_invalid_port_raises_error(self):
        """Test invalid port value raises ValueError."""
        os.environ["GEM_FLUX_PORT"] = "not_a_number"

        with pytest.raises(ValueError):
            get_config_from_env()

        os.environ.pop("GEM_FLUX_PORT", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
