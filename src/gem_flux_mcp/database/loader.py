"""
Database loader module for ModelSEED database integration.

This module provides functions to load and validate the ModelSEED database
files (compounds.tsv and reactions.tsv) at server startup.

According to spec 007-database-integration.md:
- Loads TSV files into indexed pandas DataFrames
- Validates required columns and row counts
- Provides O(1) lookup by ID
- Handles missing/corrupted files with clear errors
"""

import logging
import re
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from gem_flux_mcp.errors import DatabaseError, build_error_response

logger = logging.getLogger(__name__)


# Required columns for compounds database (spec 007)
REQUIRED_COMPOUND_COLUMNS = [
    "id",
    "abbreviation",
    "name",
    "formula",
    "mass",
    "charge",
    "inchikey",
    "smiles",
    "aliases",
]

# Required columns for reactions database (spec 007)
REQUIRED_REACTION_COLUMNS = [
    "id",
    "abbreviation",
    "name",
    "equation",
    "definition",
    "stoichiometry",
    "reversibility",
    "is_transport",
    "ec_numbers",
    "pathways",
    "aliases",
]

# Validation patterns (spec 007)
COMPOUND_ID_PATTERN = re.compile(r"^cpd\d{5}$")
REACTION_ID_PATTERN = re.compile(r"^rxn\d{5}$")

# Minimum expected row counts (spec 007)
MIN_COMPOUNDS_COUNT = 30000
MIN_REACTIONS_COUNT = 35000


def load_compounds_database(file_path: str | Path) -> pd.DataFrame:
    """
    Load the ModelSEED compounds database from a TSV file.

    Args:
        file_path: Path to compounds.tsv file

    Returns:
        Pandas DataFrame with compounds indexed by ID

    Raises:
        DatabaseError: If file is missing, corrupted, or invalid

    Performance:
        - Load time: 1-3 seconds typical
        - Memory: ~50-80 MB
        - Lookup: O(1) by ID after indexing

    Example:
        >>> compounds_df = load_compounds_database("data/database/compounds.tsv")
        >>> glucose = compounds_df.loc["cpd00027"]
        >>> print(glucose["name"])
        'D-Glucose'
    """
    file_path = Path(file_path)

    # Check file exists (spec 007: Error Handling)
    if not file_path.exists():
        logger.error(f"Compounds database file not found: {file_path}")
        raise DatabaseError(
            message=f"Compounds database file not found at {file_path}",
            error_code="DATABASE_FILE_NOT_FOUND",
            details={
                "expected_path": str(file_path),
                "action": "Ensure compounds.tsv is present in the database directory",
            },
        )

    # Load TSV file
    try:
        logger.info(f"Loading compounds database from {file_path}")
        df = pd.read_csv(
            file_path,
            sep="\t",
            dtype=str,  # Load all as strings initially
            keep_default_na=False,  # Don't convert empty strings to NaN
        )
        logger.info(f"Loaded {len(df)} compounds from database")
    except Exception as e:
        logger.error(f"Failed to parse compounds database: {e}")
        raise DatabaseError(
            message=f"Failed to parse compounds database file",
            error_code="DATABASE_PARSE_ERROR",
            details={
                "file": str(file_path),
                "error": str(e),
                "action": "Verify file format is valid TSV and re-download if corrupted",
            },
        ) from e

    # Validate required columns (spec 007: Startup Validation)
    missing_columns = set(REQUIRED_COMPOUND_COLUMNS) - set(df.columns)
    if missing_columns:
        logger.error(f"Compounds database missing required columns: {missing_columns}")
        raise DatabaseError(
            message=f"Compounds database missing required columns: {', '.join(missing_columns)}",
            error_code="DATABASE_MISSING_COLUMNS",
            details={
                "file": str(file_path),
                "missing_columns": list(missing_columns),
                "found_columns": list(df.columns),
                "action": "Re-download database file from ModelSEED repository",
            },
        )

    # Validate row count (spec 007: minimum 30,000 compounds)
    if len(df) < MIN_COMPOUNDS_COUNT:
        logger.warning(
            f"Compounds database has fewer rows than expected: {len(df)} < {MIN_COMPOUNDS_COUNT}"
        )
        # Log warning but don't fail - could be a valid subset

    # Validate ID format (spec 007: compound IDs must be cpd\d{5})
    invalid_ids = df[~df["id"].str.match(COMPOUND_ID_PATTERN)]["id"].tolist()
    if invalid_ids:
        logger.error(f"Found {len(invalid_ids)} invalid compound IDs")
        raise DatabaseError(
            message=f"Compounds database contains invalid IDs",
            error_code="DATABASE_INVALID_IDS",
            details={
                "file": str(file_path),
                "invalid_ids": invalid_ids[:10],  # Show first 10
                "total_invalid": len(invalid_ids),
                "expected_format": "cpd followed by exactly 5 digits (e.g., cpd00027)",
                "action": "Re-download database file from ModelSEED repository",
            },
        )

    # Check for duplicate IDs
    duplicate_ids = df[df["id"].duplicated()]["id"].tolist()
    if duplicate_ids:
        logger.error(f"Found {len(duplicate_ids)} duplicate compound IDs")
        raise DatabaseError(
            message=f"Compounds database contains duplicate IDs",
            error_code="DATABASE_DUPLICATE_IDS",
            details={
                "file": str(file_path),
                "duplicate_ids": duplicate_ids[:10],
                "total_duplicates": len(duplicate_ids),
                "action": "Re-download database file from ModelSEED repository",
            },
        )

    # Set ID as index for O(1) lookup (spec 007: Indexing)
    df = df.set_index("id")

    # Convert numeric columns to appropriate types
    df["mass"] = pd.to_numeric(df["mass"], errors="coerce")
    df["charge"] = pd.to_numeric(df["charge"], errors="coerce").astype("Int64")

    logger.info(f"Successfully loaded and indexed {len(df)} compounds")
    return df


def load_reactions_database(file_path: str | Path) -> pd.DataFrame:
    """
    Load the ModelSEED reactions database from a TSV file.

    Args:
        file_path: Path to reactions.tsv file

    Returns:
        Pandas DataFrame with reactions indexed by ID

    Raises:
        DatabaseError: If file is missing, corrupted, or invalid

    Performance:
        - Load time: 2-4 seconds typical
        - Memory: ~100-150 MB
        - Lookup: O(1) by ID after indexing

    Example:
        >>> reactions_df = load_reactions_database("data/database/reactions.tsv")
        >>> hexokinase = reactions_df.loc["rxn00148"]
        >>> print(hexokinase["name"])
        'hexokinase'
    """
    file_path = Path(file_path)

    # Check file exists (spec 007: Error Handling)
    if not file_path.exists():
        logger.error(f"Reactions database file not found: {file_path}")
        raise DatabaseError(
            message=f"Reactions database file not found at {file_path}",
            error_code="DATABASE_FILE_NOT_FOUND",
            details={
                "expected_path": str(file_path),
                "action": "Ensure reactions.tsv is present in the database directory",
            },
        )

    # Load TSV file
    try:
        logger.info(f"Loading reactions database from {file_path}")
        df = pd.read_csv(
            file_path,
            sep="\t",
            dtype=str,  # Load all as strings initially
            keep_default_na=False,  # Don't convert empty strings to NaN
        )
        logger.info(f"Loaded {len(df)} reactions from database")
    except Exception as e:
        logger.error(f"Failed to parse reactions database: {e}")
        raise DatabaseError(
            message=f"Failed to parse reactions database file",
            error_code="DATABASE_PARSE_ERROR",
            details={
                "file": str(file_path),
                "error": str(e),
                "action": "Verify file format is valid TSV and re-download if corrupted",
            },
        ) from e

    # Validate required columns (spec 007: Startup Validation)
    missing_columns = set(REQUIRED_REACTION_COLUMNS) - set(df.columns)
    if missing_columns:
        logger.error(f"Reactions database missing required columns: {missing_columns}")
        raise DatabaseError(
            message=f"Reactions database missing required columns: {', '.join(missing_columns)}",
            error_code="DATABASE_MISSING_COLUMNS",
            details={
                "file": str(file_path),
                "missing_columns": list(missing_columns),
                "found_columns": list(df.columns),
                "action": "Re-download database file from ModelSEED repository",
            },
        )

    # Validate row count (spec 007: minimum 35,000 reactions)
    if len(df) < MIN_REACTIONS_COUNT:
        logger.warning(
            f"Reactions database has fewer rows than expected: {len(df)} < {MIN_REACTIONS_COUNT}"
        )
        # Log warning but don't fail - could be a valid subset

    # Validate ID format (spec 007: reaction IDs must be rxn\d{5})
    invalid_ids = df[~df["id"].str.match(REACTION_ID_PATTERN)]["id"].tolist()
    if invalid_ids:
        logger.error(f"Found {len(invalid_ids)} invalid reaction IDs")
        raise DatabaseError(
            message=f"Reactions database contains invalid IDs",
            error_code="DATABASE_INVALID_IDS",
            details={
                "file": str(file_path),
                "invalid_ids": invalid_ids[:10],  # Show first 10
                "total_invalid": len(invalid_ids),
                "expected_format": "rxn followed by exactly 5 digits (e.g., rxn00148)",
                "action": "Re-download database file from ModelSEED repository",
            },
        )

    # Check for duplicate IDs
    duplicate_ids = df[df["id"].duplicated()]["id"].tolist()
    if duplicate_ids:
        logger.error(f"Found {len(duplicate_ids)} duplicate reaction IDs")
        raise DatabaseError(
            message=f"Reactions database contains duplicate IDs",
            error_code="DATABASE_DUPLICATE_IDS",
            details={
                "file": str(file_path),
                "duplicate_ids": duplicate_ids[:10],
                "total_duplicates": len(duplicate_ids),
                "action": "Re-download database file from ModelSEED repository",
            },
        )

    # Set ID as index for O(1) lookup (spec 007: Indexing)
    df = df.set_index("id")

    # Convert is_transport to int
    df["is_transport"] = pd.to_numeric(df["is_transport"], errors="coerce").astype(
        "Int64"
    )

    logger.info(f"Successfully loaded and indexed {len(df)} reactions")
    return df


def parse_aliases(aliases_str: str) -> dict[str, list[str]]:
    """
    Parse the aliases column into a structured dictionary.

    The aliases column contains pipe-separated database references:
    "KEGG: C00031|BiGG: glc__D|MetaCyc: GLC"

    Multiple IDs from the same database are semicolon-separated:
    "BiGG: glc__D;glc_D|KEGG: C00031"

    Args:
        aliases_str: Raw aliases string from TSV

    Returns:
        Dictionary mapping database names to lists of IDs

    Examples:
        >>> parse_aliases("KEGG: C00031|BiGG: glc__D")
        {'KEGG': ['C00031'], 'BiGG': ['glc__D']}

        >>> parse_aliases("BiGG: glc__D;glc_D|KEGG: C00031")
        {'BiGG': ['glc__D', 'glc_D'], 'KEGG': ['C00031']}

        >>> parse_aliases("")
        {}

    Edge Cases:
        - Empty string → empty dict
        - Malformed entry (no ':') → skip that entry
        - Whitespace around IDs → stripped automatically
    """
    if not aliases_str or aliases_str.strip() == "":
        return {}

    aliases_dict: dict[str, list[str]] = {}

    # Split by pipe to get individual database entries
    entries = aliases_str.split("|")

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        # Split on ':' to get database name and IDs
        if ":" not in entry:
            # Malformed entry - skip (spec 007: Edge Cases)
            logger.debug(f"Skipping malformed alias entry (no ':'): {entry}")
            continue

        parts = entry.split(":", 1)
        if len(parts) != 2:
            continue

        db_name = parts[0].strip()
        ids_str = parts[1].strip()

        # Split IDs on semicolon if multiple IDs present
        ids = [id.strip() for id in ids_str.split(";") if id.strip()]

        if db_name and ids:
            aliases_dict[db_name] = ids

    return aliases_dict


def validate_compound_id(compound_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate a compound ID format.

    Args:
        compound_id: Compound ID to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, error_message) if invalid

    Examples:
        >>> validate_compound_id("cpd00027")
        (True, None)

        >>> validate_compound_id("cpd1")
        (False, "Invalid compound ID format: expected 'cpd' followed by exactly 5 digits")

        >>> validate_compound_id("compound00027")
        (False, "Invalid compound ID format: expected 'cpd' followed by exactly 5 digits")
    """
    if not COMPOUND_ID_PATTERN.match(compound_id):
        return (
            False,
            "Invalid compound ID format: expected 'cpd' followed by exactly 5 digits (e.g., cpd00027)",
        )
    return (True, None)


def validate_reaction_id(reaction_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate a reaction ID format.

    Args:
        reaction_id: Reaction ID to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, error_message) if invalid

    Examples:
        >>> validate_reaction_id("rxn00148")
        (True, None)

        >>> validate_reaction_id("rxn1")
        (False, "Invalid reaction ID format: expected 'rxn' followed by exactly 5 digits")

        >>> validate_reaction_id("reaction00148")
        (False, "Invalid reaction ID format: expected 'rxn' followed by exactly 5 digits")
    """
    if not REACTION_ID_PATTERN.match(reaction_id):
        return (
            False,
            "Invalid reaction ID format: expected 'rxn' followed by exactly 5 digits (e.g., rxn00148)",
        )
    return (True, None)
