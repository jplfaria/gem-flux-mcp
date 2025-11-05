"""
Unit tests for database loader module.

Tests database loading, validation, and alias parsing functions.
"""


import pandas as pd
import pytest

from gem_flux_mcp.database.loader import (
    COMPOUND_ID_PATTERN,
    MIN_COMPOUNDS_COUNT,
    MIN_REACTIONS_COUNT,
    REACTION_ID_PATTERN,
    REQUIRED_COMPOUND_COLUMNS,
    REQUIRED_REACTION_COLUMNS,
    load_compounds_database,
    load_reactions_database,
    parse_aliases,
    validate_compound_id,
    validate_reaction_id,
)
from gem_flux_mcp.errors import DatabaseError

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def valid_compounds_tsv(tmp_path):
    """Create a valid compounds TSV file for testing."""
    content = "\t".join(REQUIRED_COMPOUND_COLUMNS) + "\n"

    # Add enough test compounds to meet minimum count
    # Start from cpd00100 to avoid conflicts with well-known compounds below
    for i in range(100, 100 + MIN_COMPOUNDS_COUNT):
        compound_id = f"cpd{i:05d}"
        content += f"{compound_id}\ttest_abbr_{i}\tTest Compound {i}\tC6H12O6\t180.0\t0\tTEST-INCHIKEY\tTEST-SMILES\tKEGG: C{i:05d}\n"

    # Add some well-known compounds for specific tests (with IDs outside the loop range)
    content += "cpd00027\tglc__D\tD-Glucose\tC6H12O6\t180.0\t0\tWQZGKKKJIJFFOK-GASJEMHNSA-N\tOC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O\tKEGG: C00031|BiGG: glc__D|MetaCyc: GLC\n"
    content += "cpd00007\to2\tO2\tO2\t32.0\t0\tMYMFRHVKRCKBQM-UHFFFAOYSA-N\tO=O\tKEGG: C00007|BiGG: o2\n"
    content += "cpd00001\th2o\tH2O\tH2O\t18.0\t0\tXLYOFNOQVPJJNP-UHFFFAOYSA-N\tO\tKEGG: C00001|BiGG: h2o\n"

    file_path = tmp_path / "compounds.tsv"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def valid_reactions_tsv(tmp_path):
    """Create a valid reactions TSV file for testing."""
    content = "\t".join(REQUIRED_REACTION_COLUMNS) + "\n"

    # Add enough test reactions to meet minimum count
    # Start from rxn00500 to avoid conflicts with well-known reactions below
    for i in range(500, 500 + MIN_REACTIONS_COUNT):
        reaction_id = f"rxn{i:05d}"
        content += f"{reaction_id}\tR{i:05d}\tTest Reaction {i}\t(1) cpd00001[0] => (1) cpd00002[0]\t(1) H2O[0] => (1) ATP[0]\ttest_stoich\t>\t0\t1.1.1.1\tTest Pathway\tKEGG: R{i:05d}\n"

    # Add some well-known reactions for specific tests (with IDs outside the loop range)
    content += "rxn00148\tR00200\thexokinase\t(1) cpd00027[0] + (1) cpd00002[0] => (1) cpd00008[0] + (1) cpd00067[0] + (1) cpd00079[0]\t(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) H+[0] + (1) D-Glucose-6-phosphate[0]\ttest_stoich\t>\t0\t2.7.1.1\tGlycolysis\tKEGG: R00200|BiGG: HEX1\n"
    content += "rxn00225\tR00201\tacetate kinase\t(1) cpd00029[0] + (1) cpd00002[0] => (1) cpd00022[0] + (1) cpd00008[0]\t(1) Acetate[0] + (1) ATP[0] => (1) Acetyl-CoA[0] + (1) ADP[0]\ttest_stoich\t=\t0\t2.7.2.1\tFermentation\tKEGG: R00201\n"

    file_path = tmp_path / "reactions.tsv"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def minimal_compounds_tsv(tmp_path):
    """Create a minimal valid compounds TSV (below minimum count)."""
    content = "\t".join(REQUIRED_COMPOUND_COLUMNS) + "\n"
    content += "cpd00027\tglc__D\tD-Glucose\tC6H12O6\t180.0\t0\tTEST-KEY\tTEST-SMILES\tKEGG: C00031\n"
    content += "cpd00007\to2\tO2\tO2\t32.0\t0\tTEST-KEY\tTEST-SMILES\tKEGG: C00007\n"

    file_path = tmp_path / "compounds_minimal.tsv"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def invalid_id_compounds_tsv(tmp_path):
    """Create a compounds TSV with invalid IDs."""
    content = "\t".join(REQUIRED_COMPOUND_COLUMNS) + "\n"
    content += "compound00027\tglc__D\tD-Glucose\tC6H12O6\t180.0\t0\tTEST-KEY\tTEST-SMILES\tKEGG: C00031\n"  # Invalid ID
    content += "cpd1\to2\tO2\tO2\t32.0\t0\tTEST-KEY\tTEST-SMILES\tKEGG: C00007\n"  # Invalid ID

    file_path = tmp_path / "compounds_invalid.tsv"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def duplicate_id_compounds_tsv(tmp_path):
    """Create a compounds TSV with duplicate IDs."""
    content = "\t".join(REQUIRED_COMPOUND_COLUMNS) + "\n"
    content += "cpd00027\tglc__D\tD-Glucose\tC6H12O6\t180.0\t0\tTEST-KEY\tTEST-SMILES\tKEGG: C00031\n"
    content += "cpd00027\tglc__D2\tD-Glucose-Duplicate\tC6H12O6\t180.0\t0\tTEST-KEY\tTEST-SMILES\tKEGG: C00031\n"  # Duplicate

    file_path = tmp_path / "compounds_duplicates.tsv"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def missing_columns_compounds_tsv(tmp_path):
    """Create a compounds TSV missing required columns."""
    # Missing 'formula' and 'mass' columns
    columns = [c for c in REQUIRED_COMPOUND_COLUMNS if c not in ["formula", "mass"]]
    content = "\t".join(columns) + "\n"

    file_path = tmp_path / "compounds_missing_cols.tsv"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def corrupted_tsv(tmp_path):
    """Create a corrupted TSV file."""
    content = "This is not valid TSV content\nRandom text\n\x00\x01\x02"

    file_path = tmp_path / "corrupted.tsv"
    file_path.write_text(content, errors="ignore")
    return file_path


# ============================================================================
# Tests for load_compounds_database
# ============================================================================


def test_load_compounds_success(valid_compounds_tsv):
    """Test successful loading of valid compounds database."""
    df = load_compounds_database(valid_compounds_tsv)

    # Verify DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert df.index.name == "id"
    assert len(df) >= MIN_COMPOUNDS_COUNT

    # Verify specific compounds
    assert "cpd00027" in df.index
    glucose = df.loc["cpd00027"]
    assert glucose["name"] == "D-Glucose"
    assert glucose["formula"] == "C6H12O6"
    assert glucose["mass"] == 180.0
    assert glucose["charge"] == 0


def test_load_compounds_file_not_found(tmp_path):
    """Test error when compounds file doesn't exist."""
    non_existent_path = tmp_path / "nonexistent.tsv"

    with pytest.raises(DatabaseError) as exc_info:
        load_compounds_database(non_existent_path)

    error = exc_info.value
    assert "not found" in str(error).lower()
    assert "compounds" in str(error).lower()


def test_load_compounds_corrupted_file(corrupted_tsv):
    """Test error when compounds file is corrupted."""
    with pytest.raises(DatabaseError) as exc_info:
        load_compounds_database(corrupted_tsv)

    error = exc_info.value
    # Corrupted file may be detected as missing columns or parse error
    assert "missing" in str(error).lower() or "parse" in str(error).lower() or "failed" in str(error).lower()


def test_load_compounds_missing_columns(missing_columns_compounds_tsv):
    """Test error when required columns are missing."""
    with pytest.raises(DatabaseError) as exc_info:
        load_compounds_database(missing_columns_compounds_tsv)

    error = exc_info.value
    assert "missing" in str(error).lower()
    assert "column" in str(error).lower()


def test_load_compounds_below_minimum_count(minimal_compounds_tsv):
    """Test warning (but not failure) when compound count is below minimum."""
    # Should load successfully but log a warning
    df = load_compounds_database(minimal_compounds_tsv)
    assert len(df) == 2  # Only 2 compounds
    assert "cpd00027" in df.index


def test_load_compounds_invalid_ids(invalid_id_compounds_tsv):
    """Test error when compound IDs have invalid format."""
    with pytest.raises(DatabaseError) as exc_info:
        load_compounds_database(invalid_id_compounds_tsv)

    error = exc_info.value
    assert "invalid" in str(error).lower()


def test_load_compounds_duplicate_ids(duplicate_id_compounds_tsv):
    """Test error when compound IDs are duplicated."""
    with pytest.raises(DatabaseError) as exc_info:
        load_compounds_database(duplicate_id_compounds_tsv)

    error = exc_info.value
    assert "duplicate" in str(error).lower()


def test_load_compounds_indexing(valid_compounds_tsv):
    """Test that compounds are indexed by ID for O(1) lookup."""
    df = load_compounds_database(valid_compounds_tsv)

    # Verify index is set to 'id'
    assert df.index.name == "id"

    # Verify O(1) lookup works
    assert "cpd00027" in df.index
    glucose = df.loc["cpd00027"]
    assert glucose["name"] == "D-Glucose"


def test_load_compounds_numeric_conversion(valid_compounds_tsv):
    """Test that numeric columns are converted to appropriate types."""
    import numpy as np

    df = load_compounds_database(valid_compounds_tsv)

    glucose = df.loc["cpd00027"]
    assert isinstance(glucose["mass"], (float, int, np.floating, np.integer))
    # charge can be int, pandas Int64, or numpy int64
    assert isinstance(glucose["charge"], (int, np.integer)) or pd.isna(glucose["charge"])


# ============================================================================
# Tests for load_reactions_database
# ============================================================================


def test_load_reactions_success(valid_reactions_tsv):
    """Test successful loading of valid reactions database."""
    df = load_reactions_database(valid_reactions_tsv)

    # Verify DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert df.index.name == "id"
    assert len(df) >= MIN_REACTIONS_COUNT

    # Verify specific reactions
    assert "rxn00148" in df.index
    hexokinase = df.loc["rxn00148"]
    assert hexokinase["name"] == "hexokinase"
    assert hexokinase["reversibility"] == ">"
    assert hexokinase["ec_numbers"] == "2.7.1.1"


def test_load_reactions_file_not_found(tmp_path):
    """Test error when reactions file doesn't exist."""
    non_existent_path = tmp_path / "nonexistent.tsv"

    with pytest.raises(DatabaseError) as exc_info:
        load_reactions_database(non_existent_path)

    error = exc_info.value
    assert "not found" in str(error).lower()
    assert "reactions" in str(error).lower()


def test_load_reactions_indexing(valid_reactions_tsv):
    """Test that reactions are indexed by ID for O(1) lookup."""
    df = load_reactions_database(valid_reactions_tsv)

    # Verify index is set to 'id'
    assert df.index.name == "id"

    # Verify O(1) lookup works
    assert "rxn00148" in df.index
    hexokinase = df.loc["rxn00148"]
    assert hexokinase["name"] == "hexokinase"


def test_load_reactions_is_transport_conversion(valid_reactions_tsv):
    """Test that is_transport column is converted to int."""
    import numpy as np

    df = load_reactions_database(valid_reactions_tsv)

    hexokinase = df.loc["rxn00148"]
    # is_transport can be int, pandas Int64, or numpy int64
    assert isinstance(hexokinase["is_transport"], (int, np.integer)) or pd.isna(hexokinase["is_transport"])


# ============================================================================
# Tests for parse_aliases
# ============================================================================


def test_parse_aliases_basic():
    """Test basic alias parsing."""
    aliases = "KEGG: C00031|BiGG: glc__D"
    result = parse_aliases(aliases)

    assert result == {
        "KEGG": ["C00031"],
        "BiGG": ["glc__D"],
    }


def test_parse_aliases_multiple_ids():
    """Test parsing multiple IDs from same database."""
    aliases = "BiGG: glc__D;glc_D|KEGG: C00031"
    result = parse_aliases(aliases)

    assert result == {
        "BiGG": ["glc__D", "glc_D"],
        "KEGG": ["C00031"],
    }


def test_parse_aliases_three_databases():
    """Test parsing aliases with three databases."""
    aliases = "KEGG: C00031|BiGG: glc__D|MetaCyc: GLC"
    result = parse_aliases(aliases)

    assert result == {
        "KEGG": ["C00031"],
        "BiGG": ["glc__D"],
        "MetaCyc": ["GLC"],
    }


def test_parse_aliases_empty_string():
    """Test parsing empty alias string."""
    result = parse_aliases("")
    assert result == {}


def test_parse_aliases_whitespace_only():
    """Test parsing whitespace-only string."""
    result = parse_aliases("   \t\n  ")
    assert result == {}


def test_parse_aliases_malformed_no_colon():
    """Test parsing malformed entry without colon (should skip)."""
    aliases = "KEGG: C00031|MALFORMED_ENTRY|BiGG: glc__D"
    result = parse_aliases(aliases)

    # Should skip malformed entry
    assert result == {
        "KEGG": ["C00031"],
        "BiGG": ["glc__D"],
    }


def test_parse_aliases_whitespace_trimming():
    """Test that whitespace around IDs is stripped."""
    aliases = "KEGG:  C00031  |  BiGG:  glc__D ; glc_D  "
    result = parse_aliases(aliases)

    assert result == {
        "KEGG": ["C00031"],
        "BiGG": ["glc__D", "glc_D"],
    }


def test_parse_aliases_empty_database_name():
    """Test parsing with empty database name (should skip)."""
    aliases = ": C00031|KEGG: C00007"
    result = parse_aliases(aliases)

    # Should skip entry with empty database name
    assert result == {
        "KEGG": ["C00007"],
    }


def test_parse_aliases_empty_ids():
    """Test parsing with empty IDs (should skip)."""
    aliases = "KEGG: |BiGG: glc__D"
    result = parse_aliases(aliases)

    # Should skip entry with empty IDs
    assert result == {
        "BiGG": ["glc__D"],
    }


def test_parse_aliases_complex_example():
    """Test parsing a complex real-world example."""
    aliases = "KEGG: C00031|BiGG: glc__D;glc_D;glc_alpha_D|MetaCyc: GLC|ChEBI: 4167"
    result = parse_aliases(aliases)

    assert result == {
        "KEGG": ["C00031"],
        "BiGG": ["glc__D", "glc_D", "glc_alpha_D"],
        "MetaCyc": ["GLC"],
        "ChEBI": ["4167"],
    }


# ============================================================================
# Tests for validate_compound_id
# ============================================================================


def test_validate_compound_id_valid():
    """Test validation of valid compound IDs."""
    assert validate_compound_id("cpd00001") == (True, None)
    assert validate_compound_id("cpd00027") == (True, None)
    assert validate_compound_id("cpd99999") == (True, None)


def test_validate_compound_id_invalid_format():
    """Test validation of invalid compound ID formats."""
    # Too few digits
    is_valid, error = validate_compound_id("cpd1")
    assert not is_valid
    assert "format" in error.lower()

    # Too many digits
    is_valid, error = validate_compound_id("cpd000001")
    assert not is_valid
    assert "format" in error.lower()

    # Wrong prefix
    is_valid, error = validate_compound_id("compound00027")
    assert not is_valid
    assert "format" in error.lower()

    # Missing prefix
    is_valid, error = validate_compound_id("00027")
    assert not is_valid
    assert "format" in error.lower()


def test_validate_compound_id_pattern():
    """Test compound ID regex pattern directly."""
    assert COMPOUND_ID_PATTERN.match("cpd00001")
    assert COMPOUND_ID_PATTERN.match("cpd99999")
    assert not COMPOUND_ID_PATTERN.match("cpd1")
    assert not COMPOUND_ID_PATTERN.match("cpd000001")
    assert not COMPOUND_ID_PATTERN.match("compound00001")


# ============================================================================
# Tests for validate_reaction_id
# ============================================================================


def test_validate_reaction_id_valid():
    """Test validation of valid reaction IDs."""
    assert validate_reaction_id("rxn00001") == (True, None)
    assert validate_reaction_id("rxn00148") == (True, None)
    assert validate_reaction_id("rxn99999") == (True, None)


def test_validate_reaction_id_invalid_format():
    """Test validation of invalid reaction ID formats."""
    # Too few digits
    is_valid, error = validate_reaction_id("rxn1")
    assert not is_valid
    assert "format" in error.lower()

    # Too many digits
    is_valid, error = validate_reaction_id("rxn000001")
    assert not is_valid
    assert "format" in error.lower()

    # Wrong prefix
    is_valid, error = validate_reaction_id("reaction00148")
    assert not is_valid
    assert "format" in error.lower()

    # Missing prefix
    is_valid, error = validate_reaction_id("00148")
    assert not is_valid
    assert "format" in error.lower()


def test_validate_reaction_id_pattern():
    """Test reaction ID regex pattern directly."""
    assert REACTION_ID_PATTERN.match("rxn00001")
    assert REACTION_ID_PATTERN.match("rxn99999")
    assert not REACTION_ID_PATTERN.match("rxn1")
    assert not REACTION_ID_PATTERN.match("rxn000001")
    assert not REACTION_ID_PATTERN.match("reaction00001")


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_pathlib_compatibility(valid_compounds_tsv):
    """Test that loader accepts both str and Path objects."""
    # Test with Path object
    df1 = load_compounds_database(valid_compounds_tsv)

    # Test with str
    df2 = load_compounds_database(str(valid_compounds_tsv))

    # Results should be identical
    assert len(df1) == len(df2)
    assert list(df1.columns) == list(df2.columns)


def test_case_sensitivity_aliases():
    """Test that alias parsing preserves case."""
    aliases = "KEGG: C00031|BiGG: Glc__D|MetaCyc: glc"
    result = parse_aliases(aliases)

    # Should preserve case exactly as provided
    assert result["BiGG"] == ["Glc__D"]
    assert result["MetaCyc"] == ["glc"]


def test_special_characters_in_aliases():
    """Test that special characters in aliases are preserved."""
    aliases = "BiGG: glc__D|Custom: id-with-dashes_and_underscores.and.dots"
    result = parse_aliases(aliases)

    assert result["Custom"] == ["id-with-dashes_and_underscores.and.dots"]
