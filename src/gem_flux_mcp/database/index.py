"""
Database indexing module for ModelSEED database.

This module provides secondary indexing functionality for efficient
lookups and searches beyond the primary ID index. According to spec 007,
we need to support:

- Compounds: Lookup by ID (O(1)), search by name/abbreviation (O(n) for MVP)
- Reactions: Lookup by ID (O(1)), search by name/abbreviation/EC (O(n) for MVP)

For MVP, we use pandas filtering which is acceptable performance (<100ms).
Future versions will implement full-text search indexes (SQLite FTS5).
"""

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseIndex:
    """
    Database index wrapper for ModelSEED compounds and reactions.

    Provides both O(1) lookup by ID (primary index) and search functionality
    by name, abbreviation, and other fields (secondary indexes).

    For MVP:
    - Primary index (by ID): O(1) via pandas DataFrame index
    - Secondary searches: O(n) via pandas filtering (acceptable for ~35k-40k rows)

    Future optimization:
    - Full-text search index (SQLite FTS5)
    - Pre-computed lowercase name index
    - Multi-field indexes
    """

    def __init__(self, compounds_df: pd.DataFrame, reactions_df: pd.DataFrame):
        """
        Initialize database indexes.

        Args:
            compounds_df: Compounds DataFrame indexed by ID
            reactions_df: Reactions DataFrame indexed by ID
        """
        self.compounds_df = compounds_df
        self.reactions_df = reactions_df

        # Create lowercase name columns for case-insensitive searching
        # (spec 007: Search Operations)
        if not compounds_df.empty:
            self.compounds_df["name_lower"] = self.compounds_df["name"].str.lower()
            self.compounds_df["abbreviation_lower"] = self.compounds_df["abbreviation"].str.lower()
        else:
            self.compounds_df["name_lower"] = pd.Series([], dtype=str)
            self.compounds_df["abbreviation_lower"] = pd.Series([], dtype=str)

        if not reactions_df.empty:
            self.reactions_df["name_lower"] = self.reactions_df["name"].str.lower()
            self.reactions_df["abbreviation_lower"] = self.reactions_df["abbreviation"].str.lower()
        else:
            self.reactions_df["name_lower"] = pd.Series([], dtype=str)
            self.reactions_df["abbreviation_lower"] = pd.Series([], dtype=str)

        logger.info(
            f"Initialized database index with {len(compounds_df)} compounds "
            f"and {len(reactions_df)} reactions"
        )

    def get_compound_by_id(self, compound_id: str) -> Optional[pd.Series]:
        """
        Get compound by ID (O(1) lookup).

        Args:
            compound_id: ModelSEED compound ID (e.g., 'cpd00027')

        Returns:
            Compound record as pandas Series, or None if not found

        Performance:
            O(1) - uses DataFrame index

        Example:
            >>> index = DatabaseIndex(compounds_df, reactions_df)
            >>> glucose = index.get_compound_by_id("cpd00027")
            >>> print(glucose["name"])
            'D-Glucose'
        """
        try:
            return self.compounds_df.loc[compound_id]
        except KeyError:
            return None

    def get_reaction_by_id(self, reaction_id: str) -> Optional[pd.Series]:
        """
        Get reaction by ID (O(1) lookup).

        Args:
            reaction_id: ModelSEED reaction ID (e.g., 'rxn00148')

        Returns:
            Reaction record as pandas Series, or None if not found

        Performance:
            O(1) - uses DataFrame index

        Example:
            >>> index = DatabaseIndex(compounds_df, reactions_df)
            >>> hexokinase = index.get_reaction_by_id("rxn00148")
            >>> print(hexokinase["name"])
            'hexokinase'
        """
        try:
            return self.reactions_df.loc[reaction_id]
        except KeyError:
            return None

    def search_compounds_by_name(self, query: str, limit: int = 10) -> list[pd.Series]:
        """
        Search compounds by name (case-insensitive, partial match).

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of compound records (pandas Series)

        Performance:
            O(n) - filters entire DataFrame (acceptable for MVP)

        Search Strategy:
            1. Exact name match (case-insensitive)
            2. Partial name match (case-insensitive)
            Sorted alphabetically by name

        Example:
            >>> results = index.search_compounds_by_name("glucose")
            >>> for compound in results:
            ...     print(f"{compound.name}: {compound['name']}")
            cpd00027: D-Glucose
            cpd00079: D-Glucose-6-phosphate
        """
        query_lower = query.lower()

        # Filter by name containing query (case-insensitive)
        matches = self.compounds_df[
            self.compounds_df["name_lower"].str.contains(query_lower, na=False)
        ]

        # Sort by name and limit results
        matches = matches.sort_values("name").head(limit)

        # Convert to list of Series
        return [row for _, row in matches.iterrows()]

    def search_compounds_by_abbreviation(self, query: str, limit: int = 10) -> list[pd.Series]:
        """
        Search compounds by abbreviation (case-insensitive, partial match).

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of compound records (pandas Series)

        Example:
            >>> results = index.search_compounds_by_abbreviation("glc")
            >>> for compound in results:
            ...     print(f"{compound.name}: {compound['abbreviation']}")
            cpd00027: glc__D
        """
        query_lower = query.lower()

        matches = self.compounds_df[
            self.compounds_df["abbreviation_lower"].str.contains(query_lower, na=False)
        ]

        matches = matches.sort_values("name").head(limit)
        return [row for _, row in matches.iterrows()]

    def search_reactions_by_name(self, query: str, limit: int = 10) -> list[pd.Series]:
        """
        Search reactions by name (case-insensitive, partial match).

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of reaction records (pandas Series)

        Performance:
            O(n) - filters entire DataFrame (acceptable for MVP)

        Example:
            >>> results = index.search_reactions_by_name("hexokinase")
            >>> for reaction in results:
            ...     print(f"{reaction.name}: {reaction['name']}")
            rxn00148: hexokinase
        """
        query_lower = query.lower()

        matches = self.reactions_df[
            self.reactions_df["name_lower"].str.contains(query_lower, na=False)
        ]

        matches = matches.sort_values("name").head(limit)
        return [row for _, row in matches.iterrows()]

    def search_reactions_by_abbreviation(self, query: str, limit: int = 10) -> list[pd.Series]:
        """
        Search reactions by abbreviation (case-insensitive, partial match).

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of reaction records (pandas Series)

        Example:
            >>> results = index.search_reactions_by_abbreviation("R00200")
            >>> for reaction in results:
            ...     print(f"{reaction.name}: {reaction['abbreviation']}")
            rxn00148: R00200
        """
        query_lower = query.lower()

        matches = self.reactions_df[
            self.reactions_df["abbreviation_lower"].str.contains(query_lower, na=False)
        ]

        matches = matches.sort_values("name").head(limit)
        return [row for _, row in matches.iterrows()]

    def search_reactions_by_ec_number(self, ec_number: str, limit: int = 10) -> list[pd.Series]:
        """
        Search reactions by EC number (exact or partial match).

        Args:
            ec_number: EC number to search for (e.g., "2.7.1.1" or "2.7.1")
            limit: Maximum number of results to return

        Returns:
            List of reaction records (pandas Series)

        Example:
            >>> results = index.search_reactions_by_ec_number("2.7.1.1")
            >>> for reaction in results:
            ...     print(f"{reaction.name}: {reaction['ec_numbers']}")
            rxn00148: 2.7.1.1
        """
        # EC numbers column contains strings like "2.7.1.1" or "2.7.1.1;1.1.1.1"
        matches = self.reactions_df[
            self.reactions_df["ec_numbers"].str.contains(ec_number, na=False)
        ]

        matches = matches.sort_values("name").head(limit)
        return [row for _, row in matches.iterrows()]

    def compound_exists(self, compound_id: str) -> bool:
        """
        Check if compound ID exists in database (O(1)).

        Args:
            compound_id: ModelSEED compound ID

        Returns:
            True if compound exists, False otherwise

        Example:
            >>> index.compound_exists("cpd00027")
            True
            >>> index.compound_exists("cpd99999")
            False
        """
        return compound_id in self.compounds_df.index

    def reaction_exists(self, reaction_id: str) -> bool:
        """
        Check if reaction ID exists in database (O(1)).

        Args:
            reaction_id: ModelSEED reaction ID

        Returns:
            True if reaction exists, False otherwise

        Example:
            >>> index.reaction_exists("rxn00148")
            True
            >>> index.reaction_exists("rxn99999")
            False
        """
        return reaction_id in self.reactions_df.index

    def get_compound_count(self) -> int:
        """Get total number of compounds in database."""
        return len(self.compounds_df)

    def get_reaction_count(self) -> int:
        """Get total number of reactions in database."""
        return len(self.reactions_df)
