"""MCP tools module for Gem-Flux server.

This module contains all MCP tool implementations for metabolic modeling.
"""

from gem_flux_mcp.tools.build_model import build_model
from gem_flux_mcp.tools.compound_lookup import (
    GetCompoundNameRequest,
    SearchCompoundsRequest,
    get_compound_name,
    search_compounds,
)
from gem_flux_mcp.tools.delete_model import delete_model
from gem_flux_mcp.tools.gapfill_model import gapfill_model
from gem_flux_mcp.tools.list_media import list_media
from gem_flux_mcp.tools.list_models import list_models
from gem_flux_mcp.tools.media_builder import build_media
from gem_flux_mcp.tools.reaction_lookup import (
    GetReactionNameRequest,
    SearchReactionsRequest,
    get_reaction_name,
    search_reactions,
)
from gem_flux_mcp.tools.run_fba import run_fba

__all__ = [
    # Tool functions
    "build_media",
    "build_model",
    "gapfill_model",
    "run_fba",
    "get_compound_name",
    "search_compounds",
    "get_reaction_name",
    "search_reactions",
    "list_models",
    "delete_model",
    "list_media",
    # Request types (for tool modules defined in tool files)
    "GetCompoundNameRequest",
    "SearchCompoundsRequest",
    "GetReactionNameRequest",
    "SearchReactionsRequest",
]
