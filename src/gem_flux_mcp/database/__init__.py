"""
Database module for ModelSEED database integration.

Provides database loading, indexing, and query functionality.
"""

from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.database.loader import (
    load_compounds_database,
    load_reactions_database,
    parse_aliases,
    validate_compound_id,
    validate_reaction_id,
)

__all__ = [
    "DatabaseIndex",
    "load_compounds_database",
    "load_reactions_database",
    "parse_aliases",
    "validate_compound_id",
    "validate_reaction_id",
]
