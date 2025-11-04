"""MCP server for Gem-Flux metabolic modeling.

This module implements the FastMCP server initialization, resource loading,
tool registration, and lifecycle management according to specification
015-mcp-server-setup.md.
"""

import os
import sys
import signal
from typing import Optional

from fastmcp import FastMCP

from gem_flux_mcp.logging import get_logger
from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.templates import load_templates
from gem_flux_mcp.media import load_predefined_media
from gem_flux_mcp.storage.models import MODEL_STORAGE
from gem_flux_mcp.storage.media import MEDIA_STORAGE

# NOTE: MCP tools are imported INSIDE create_server() to avoid circular imports
# The mcp_tools module imports get_db_index() from this module, so we must
# import mcp_tools AFTER the global state (database_index, templates) is initialized

logger = get_logger(__name__)

# Global server instance
mcp: Optional[FastMCP] = None

# Global resource instances
database_index: Optional[DatabaseIndex] = None
templates: Optional[dict] = None


def get_db_index() -> DatabaseIndex:
    """Get globally loaded database index.

    Returns:
        DatabaseIndex: The loaded database index instance

    Raises:
        RuntimeError: If database not loaded (server not initialized)

    Note:
        This function is used by MCP tool wrappers to access the global
        database index without including it in tool signatures.
    """
    if database_index is None:
        raise RuntimeError(
            "Database not loaded - server not initialized. "
            "Call load_resources() first during server startup."
        )
    return database_index


def get_templates() -> dict:
    """Get globally loaded templates dictionary.

    Returns:
        dict: Dictionary of loaded MSTemplate objects (e.g., GramNegative, Core)

    Raises:
        RuntimeError: If templates not loaded (server not initialized)

    Note:
        This function is used by MCP tool wrappers to access the global
        templates dictionary without including it in tool signatures.
        Templates are used by build_model tool for genome-scale reconstruction.
    """
    if templates is None:
        raise RuntimeError(
            "Templates not loaded - server not initialized. "
            "Call load_resources() first during server startup."
        )
    return templates


def initialize_server() -> None:
    """Initialize server global state for testing.

    This is a convenience function for tests and scripts that need to
    initialize the server resources without running the full server.

    Equivalent to calling:
    1. get_config_from_env()
    2. load_resources(config)
    3. initialize_session_storage(config)
    """
    config = get_config_from_env()
    load_resources(config)
    initialize_session_storage(config)


def get_config_from_env() -> dict:
    """Load configuration from environment variables.

    Returns:
        dict: Configuration dictionary with server settings

    Environment Variables:
        GEM_FLUX_HOST: Host to bind (default: localhost)
        GEM_FLUX_PORT: Port to listen (default: 8080)
        GEM_FLUX_DATABASE_DIR: ModelSEED database location (default: ./data/database)
        GEM_FLUX_TEMPLATE_DIR: ModelSEED template location (default: ./data/templates)
        GEM_FLUX_MAX_MODELS: Max models in session (default: 100)
        GEM_FLUX_LOG_LEVEL: Logging level (default: INFO)
    """
    config = {
        "host": os.getenv("GEM_FLUX_HOST", "localhost"),
        "port": int(os.getenv("GEM_FLUX_PORT", "8080")),
        "database_dir": os.getenv("GEM_FLUX_DATABASE_DIR", "./data/database"),
        "template_dir": os.getenv("GEM_FLUX_TEMPLATE_DIR", "./data/templates"),
        "max_models": int(os.getenv("GEM_FLUX_MAX_MODELS", "100")),
        "log_level": os.getenv("GEM_FLUX_LOG_LEVEL", "INFO"),
    }

    logger.info(f"Configuration loaded from environment variables: {config}")
    return config


def load_resources(config: dict) -> None:
    """Load ModelSEED database, templates, and predefined media.

    Args:
        config: Configuration dictionary

    Raises:
        FileNotFoundError: If required database files not found
        ValueError: If database loading fails
    """
    global database_index, templates

    logger.info("=" * 60)
    logger.info("Loading ModelSEED Resources")
    logger.info("=" * 60)

    # Phase 1: Load ModelSEED Database
    logger.info(f"Loading ModelSEED database from {config['database_dir']}")

    compounds_path = os.path.join(config["database_dir"], "compounds.tsv")
    reactions_path = os.path.join(config["database_dir"], "reactions.tsv")

    if not os.path.exists(compounds_path):
        raise FileNotFoundError(
            f"Compounds database not found: {compounds_path}\n"
            "Please download from ModelSEED database repository."
        )

    if not os.path.exists(reactions_path):
        raise FileNotFoundError(
            f"Reactions database not found: {reactions_path}\n"
            "Please download from ModelSEED database repository."
        )

    compounds_df = load_compounds_database(compounds_path)
    reactions_df = load_reactions_database(reactions_path)

    logger.info(f"Loaded {len(compounds_df)} compounds from compounds.tsv")
    logger.info(f"Loaded {len(reactions_df)} reactions from reactions.tsv")

    # Create database index
    database_index = DatabaseIndex(compounds_df, reactions_df)
    logger.info("Database indexing complete")

    # Phase 2: Load ModelSEED Templates
    logger.info(f"Loading ModelSEED templates from {config['template_dir']}")

    templates = load_templates(config["template_dir"])
    if not templates:
        logger.warning(
            "No templates loaded! At least one template is required for model building."
        )
        raise ValueError("Failed to load any ModelSEED templates")

    logger.info(f"Loaded {len(templates)} templates: {list(templates.keys())}")

    # Phase 3: Load Predefined Media
    logger.info("Loading predefined media library")
    loaded_media = load_predefined_media()
    logger.info(f"Loaded {len(loaded_media)} predefined media compositions")

    # Store predefined media in session storage so tools can access them
    from gem_flux_mcp.storage.media import store_media
    from modelseedpy.core.msmedia import MSMedia

    for media_name, media_data in loaded_media.items():
        try:
            # Convert dict to MSMedia object
            # media_data["compounds"] is a dict of {cpd_id: (lower, upper)}
            compounds_dict = media_data["compounds"]
            media_obj = MSMedia.from_dict(compounds_dict)
            media_obj.id = media_name  # Set the ID to the media name

            # Store MSMedia object using the media name as ID
            store_media(media_name, media_obj)
            logger.info(f"  ✓ Stored predefined media in session: {media_name} ({len(compounds_dict)} compounds)")
        except Exception as e:
            logger.error(f"  ✗ Failed to store predefined media {media_name}: {e}")
            import traceback
            logger.error(f"    Traceback: {traceback.format_exc()}")

    logger.info(f"Predefined media available in session: {len(loaded_media)}")

    logger.info("=" * 60)
    logger.info("Resource loading complete")
    logger.info("=" * 60)


def initialize_session_storage(config: dict) -> None:
    """Initialize in-memory session storage for models and media.

    Args:
        config: Configuration dictionary

    Note:
        For MVP, storage is in-memory only. Models and media are lost on restart.
    """
    logger.info("Initializing session storage")

    # Storage is already initialized via module-level globals:
    # - MODEL_STORAGE in storage/models.py
    # - MEDIA_STORAGE in storage/media.py

    # Just log the configuration
    max_models = config.get("max_models", 100)
    logger.info(f"Session storage initialized (max_models: {max_models})")
    logger.info(f"Models in storage: {len(MODEL_STORAGE)}")
    logger.info(f"Media in storage: {len(MEDIA_STORAGE)}")


def create_server() -> FastMCP:
    """Create and configure FastMCP server instance.

    CRITICAL: This function imports mcp_tools INSIDE the function to avoid
    circular import issues. The mcp_tools module imports get_db_index() and
    get_templates() from this module, so we must import mcp_tools AFTER the
    global state (database_index, templates) is initialized.

    Returns:
        FastMCP: Configured server instance with all tools registered

    Server Metadata:
        - name: gem-flux-mcp
        - version: 0.1.0
        - description: MCP server for metabolic modeling
        - Tools: Auto-registered via @mcp.tool() decorators in mcp_tools.py
    """
    logger.info("Creating FastMCP server instance")

    # CRITICAL: Import mcp_tools INSIDE this function to avoid circular import
    # This import happens AFTER load_resources() has set database_index and templates
    from gem_flux_mcp import mcp_tools

    # Return the pre-configured server from mcp_tools
    # All tools are already registered via @mcp.tool() decorators
    logger.info("MCP server with registered tools returned from mcp_tools")
    return mcp_tools.mcp


def shutdown_handler(signum, frame):
    """Handle graceful shutdown on SIGINT/SIGTERM.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info(f"Shutdown signal received (signal {signum})")
    logger.info("Stopping MCP server (waiting for active requests)")

    # Clear session storage
    model_count = len(MODEL_STORAGE)
    media_count = len(MEDIA_STORAGE)

    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()

    logger.info(f"Cleared session storage ({model_count} models, {media_count} media)")
    logger.info("Shutdown complete")

    sys.exit(0)


def main():
    """Main entry point for Gem-Flux MCP Server.

    Startup Sequence:
        1. Load configuration from environment
        2. Load ModelSEED database
        3. Load ModelSEED templates
        4. Load predefined media
        5. Initialize session storage
        6. Create FastMCP server
        7. Register MCP tools
        8. Start server

    Exits:
        0: Clean shutdown
        1: Startup error
    """
    global mcp

    try:
        logger.info("=" * 60)
        logger.info("Gem-Flux MCP Server v0.1.0 starting...")
        logger.info("=" * 60)

        # Phase 1: Configuration
        config = get_config_from_env()

        # Phase 2: Resource Loading
        load_resources(config)

        # Phase 3: Session Storage Initialization
        initialize_session_storage(config)

        # Phase 4: Server Creation (tools auto-registered via @mcp.tool() decorators)
        mcp = create_server()

        # Phase 5: Setup shutdown handlers
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        # Phase 7: Server Ready
        logger.info("=" * 60)
        logger.info(f"Server ready on {config['host']}:{config['port']}")
        logger.info("Accepting MCP requests")
        logger.info("=" * 60)

        # Start server (blocking call)
        mcp.run()

    except FileNotFoundError as e:
        logger.error(f"Startup failed - missing resource: {e}")
        sys.exit(1)

    except ValueError as e:
        logger.error(f"Startup failed - configuration error: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Startup failed - unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
