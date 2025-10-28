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

# Import all MCP tools
from gem_flux_mcp.tools.media_builder import build_media
from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.tools.run_fba import run_fba
from gem_flux_mcp.tools.compound_lookup import (
    get_compound_name,
    search_compounds,
)
from gem_flux_mcp.tools.reaction_lookup import (
    get_reaction_name,
    search_reactions,
)
from gem_flux_mcp.tools.list_models import list_models
from gem_flux_mcp.tools.delete_model import delete_model
from gem_flux_mcp.tools.list_media import list_media

logger = get_logger(__name__)

# Global server instance
mcp: Optional[FastMCP] = None

# Global resource instances
database_index: Optional[DatabaseIndex] = None


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
    global database_index

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


def register_tools(mcp_server: FastMCP) -> None:
    """Register all MCP tools with FastMCP server.

    Args:
        mcp_server: FastMCP server instance

    Registers:
        - build_media: Create growth medium
        - build_model: Build metabolic model from proteins
        - gapfill_model: Gapfill model for growth
        - run_fba: Execute flux balance analysis
        - get_compound_name: Lookup compound name by ID
        - get_reaction_name: Lookup reaction name by ID
        - search_compounds: Search compounds by query
        - search_reactions: Search reactions by query
        - list_models: List all models in session
        - delete_model: Delete a model from session
        - list_media: List all media in session
    """
    logger.info("Registering MCP tools")

    tools = [
        ("build_media", build_media),
        ("build_model", build_model),
        ("gapfill_model", gapfill_model),
        ("run_fba", run_fba),
        ("get_compound_name", get_compound_name),
        ("get_reaction_name", get_reaction_name),
        ("search_compounds", search_compounds),
        ("search_reactions", search_reactions),
        ("list_models", list_models),
        ("delete_model", delete_model),
        ("list_media", list_media),
    ]

    for tool_name, tool_func in tools:
        mcp_server.tool()(tool_func)
        logger.info(f"Registered tool: {tool_name}")

    logger.info(f"Tool registration complete ({len(tools)} tools)")


def create_server() -> FastMCP:
    """Create and configure FastMCP server instance.

    Returns:
        FastMCP: Configured server instance

    Server Metadata:
        - name: gem-flux-mcp
        - version: 0.1.0
        - description: MCP server for metabolic modeling
        - protocol_version: 2025-06-18 (latest stable MCP)
    """
    logger.info("Creating FastMCP server instance")

    server = FastMCP(
        name="gem-flux-mcp",
        dependencies=["fastmcp>=0.2.0", "cobra>=0.27.0", "modelseedpy", "pandas>=2.0.0"],
    )

    # FastMCP automatically handles protocol version and capabilities
    logger.info("FastMCP server instance created")
    return server


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

        # Phase 4: Server Creation
        mcp = create_server()

        # Phase 5: Tool Registration
        register_tools(mcp)

        # Phase 6: Setup shutdown handlers
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
