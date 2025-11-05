"""
Unit tests for database indexing module.

Tests O(1) lookups, search operations, and existence checks.
"""

import pandas as pd
import pytest

from gem_flux_mcp.database.index import DatabaseIndex

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_compounds_df():
    """Create a sample compounds DataFrame for testing."""
    data = {
        "id": ["cpd00027", "cpd00007", "cpd00001", "cpd00079", "cpd00221"],
        "abbreviation": ["glc__D", "o2", "h2o", "g6p_c", "g1p_c"],
        "name": [
            "D-Glucose",
            "O2",
            "H2O",
            "D-Glucose-6-phosphate",
            "D-Glucose-1-phosphate",
        ],
        "formula": ["C6H12O6", "O2", "H2O", "C6H11O9P", "C6H11O9P"],
        "mass": [180.0, 32.0, 18.0, 260.0, 260.0],
        "charge": [0, 0, 0, -2, -2],
        "inchikey": ["KEY1", "KEY2", "KEY3", "KEY4", "KEY5"],
        "smiles": ["SMILES1", "SMILES2", "SMILES3", "SMILES4", "SMILES5"],
        "aliases": [
            "KEGG: C00031|BiGG: glc__D",
            "KEGG: C00007",
            "KEGG: C00001",
            "KEGG: C00092",
            "KEGG: C00103",
        ],
    }
    df = pd.DataFrame(data)
    df = df.set_index("id")
    return df


@pytest.fixture
def sample_reactions_df():
    """Create a sample reactions DataFrame for testing."""
    data = {
        "id": ["rxn00148", "rxn00225", "rxn00558", "rxn01100"],
        "abbreviation": ["R00200", "R00201", "R00558", "R01100"],
        "name": ["hexokinase", "acetate kinase", "malate dehydrogenase", "glucokinase"],
        "equation": [
            "(1) cpd00027[0] => (1) cpd00079[0]",
            "(1) cpd00029[0] => (1) cpd00022[0]",
            "(1) cpd00020[0] => (1) cpd00036[0]",
            "(1) cpd00027[0] => (1) cpd00079[0]",
        ],
        "definition": [
            "(1) D-Glucose => (1) G6P",
            "(1) Acetate => (1) Acetyl-CoA",
            "(1) Malate => (1) Oxaloacetate",
            "(1) D-Glucose => (1) G6P",
        ],
        "stoichiometry": ["stoich1", "stoich2", "stoich3", "stoich4"],
        "reversibility": [">", "=", ">", ">"],
        "is_transport": [0, 0, 0, 0],
        "ec_numbers": ["2.7.1.1", "2.7.2.1", "1.1.1.37", "2.7.1.2"],
        "pathways": [
            "Glycolysis",
            "Fermentation",
            "TCA Cycle",
            "Glycolysis",
        ],
        "aliases": [
            "KEGG: R00200|BiGG: HEX1",
            "KEGG: R00201",
            "KEGG: R00558",
            "KEGG: R01100",
        ],
    }
    df = pd.DataFrame(data)
    df = df.set_index("id")
    return df


@pytest.fixture
def db_index(sample_compounds_df, sample_reactions_df):
    """Create a DatabaseIndex instance for testing."""
    return DatabaseIndex(sample_compounds_df, sample_reactions_df)


# ============================================================================
# Test O(1) Lookups
# ============================================================================


def test_get_compound_by_id_found(db_index):
    """Test successful compound lookup by ID."""
    compound = db_index.get_compound_by_id("cpd00027")
    assert compound is not None
    assert compound["name"] == "D-Glucose"
    assert compound["abbreviation"] == "glc__D"
    assert compound["formula"] == "C6H12O6"


def test_get_compound_by_id_not_found(db_index):
    """Test compound lookup with non-existent ID."""
    compound = db_index.get_compound_by_id("cpd99999")
    assert compound is None


def test_get_reaction_by_id_found(db_index):
    """Test successful reaction lookup by ID."""
    reaction = db_index.get_reaction_by_id("rxn00148")
    assert reaction is not None
    assert reaction["name"] == "hexokinase"
    assert reaction["abbreviation"] == "R00200"
    assert reaction["ec_numbers"] == "2.7.1.1"


def test_get_reaction_by_id_not_found(db_index):
    """Test reaction lookup with non-existent ID."""
    reaction = db_index.get_reaction_by_id("rxn99999")
    assert reaction is None


# ============================================================================
# Test Existence Checks
# ============================================================================


def test_compound_exists_true(db_index):
    """Test compound_exists returns True for valid ID."""
    assert db_index.compound_exists("cpd00027") is True
    assert db_index.compound_exists("cpd00007") is True


def test_compound_exists_false(db_index):
    """Test compound_exists returns False for invalid ID."""
    assert db_index.compound_exists("cpd99999") is False
    assert db_index.compound_exists("invalid") is False


def test_reaction_exists_true(db_index):
    """Test reaction_exists returns True for valid ID."""
    assert db_index.reaction_exists("rxn00148") is True
    assert db_index.reaction_exists("rxn00225") is True


def test_reaction_exists_false(db_index):
    """Test reaction_exists returns False for invalid ID."""
    assert db_index.reaction_exists("rxn99999") is False
    assert db_index.reaction_exists("invalid") is False


# ============================================================================
# Test Compound Searches
# ============================================================================


def test_search_compounds_by_name_exact_match(db_index):
    """Test exact name match (case-insensitive)."""
    results = db_index.search_compounds_by_name("D-Glucose")
    assert len(results) >= 1
    # Should include cpd00027 (D-Glucose)
    glucose = next((r for r in results if r.name == "cpd00027"), None)
    assert glucose is not None
    assert glucose["name"] == "D-Glucose"


def test_search_compounds_by_name_partial_match(db_index):
    """Test partial name match."""
    results = db_index.search_compounds_by_name("glucose")
    # Should find D-Glucose, D-Glucose-6-phosphate, D-Glucose-1-phosphate
    assert len(results) == 3
    names = [r["name"] for r in results]
    assert "D-Glucose" in names
    assert "D-Glucose-6-phosphate" in names
    assert "D-Glucose-1-phosphate" in names


def test_search_compounds_by_name_case_insensitive(db_index):
    """Test case-insensitive search."""
    results_lower = db_index.search_compounds_by_name("glucose")
    results_upper = db_index.search_compounds_by_name("GLUCOSE")
    results_mixed = db_index.search_compounds_by_name("GlUcOsE")

    # All should return same results
    assert len(results_lower) == len(results_upper) == len(results_mixed)


def test_search_compounds_by_name_no_match(db_index):
    """Test search with no matches."""
    results = db_index.search_compounds_by_name("nonexistent")
    assert len(results) == 0


def test_search_compounds_by_name_limit(db_index):
    """Test search result limit."""
    results = db_index.search_compounds_by_name("glucose", limit=2)
    assert len(results) <= 2


def test_search_compounds_by_abbreviation_found(db_index):
    """Test search by abbreviation."""
    results = db_index.search_compounds_by_abbreviation("glc")
    assert len(results) >= 1
    # Should find cpd00027 (glc__D)
    glucose = next((r for r in results if r.name == "cpd00027"), None)
    assert glucose is not None


def test_search_compounds_by_abbreviation_no_match(db_index):
    """Test search by abbreviation with no matches."""
    results = db_index.search_compounds_by_abbreviation("xyz")
    assert len(results) == 0


# ============================================================================
# Test Reaction Searches
# ============================================================================


def test_search_reactions_by_name_exact_match(db_index):
    """Test exact reaction name match."""
    results = db_index.search_reactions_by_name("hexokinase")
    assert len(results) >= 1
    hexokinase = next((r for r in results if r.name == "rxn00148"), None)
    assert hexokinase is not None
    assert hexokinase["name"] == "hexokinase"


def test_search_reactions_by_name_partial_match(db_index):
    """Test partial reaction name match."""
    results = db_index.search_reactions_by_name("kinase")
    # Should find hexokinase, acetate kinase, glucokinase
    assert len(results) == 3
    names = [r["name"] for r in results]
    assert "hexokinase" in names
    assert "acetate kinase" in names
    assert "glucokinase" in names


def test_search_reactions_by_name_case_insensitive(db_index):
    """Test case-insensitive reaction search."""
    results_lower = db_index.search_reactions_by_name("hexokinase")
    results_upper = db_index.search_reactions_by_name("HEXOKINASE")
    assert len(results_lower) == len(results_upper)


def test_search_reactions_by_name_no_match(db_index):
    """Test reaction search with no matches."""
    results = db_index.search_reactions_by_name("nonexistent")
    assert len(results) == 0


def test_search_reactions_by_abbreviation_found(db_index):
    """Test search by reaction abbreviation."""
    results = db_index.search_reactions_by_abbreviation("R00200")
    assert len(results) >= 1
    hexokinase = next((r for r in results if r.name == "rxn00148"), None)
    assert hexokinase is not None


def test_search_reactions_by_abbreviation_partial(db_index):
    """Test partial match on abbreviation."""
    results = db_index.search_reactions_by_abbreviation("R00")
    # Should find multiple reactions with R00xxx abbreviations
    assert len(results) >= 1


def test_search_reactions_by_ec_number_exact(db_index):
    """Test search by exact EC number."""
    results = db_index.search_reactions_by_ec_number("2.7.1.1")
    assert len(results) >= 1
    hexokinase = next((r for r in results if r.name == "rxn00148"), None)
    assert hexokinase is not None
    assert hexokinase["ec_numbers"] == "2.7.1.1"


def test_search_reactions_by_ec_number_partial(db_index):
    """Test search by partial EC number (e.g., '2.7.1')."""
    results = db_index.search_reactions_by_ec_number("2.7.1")
    # Should find hexokinase (2.7.1.1) and glucokinase (2.7.1.2)
    assert len(results) == 2


def test_search_reactions_by_ec_number_no_match(db_index):
    """Test EC number search with no matches."""
    results = db_index.search_reactions_by_ec_number("9.9.9.9")
    assert len(results) == 0


# ============================================================================
# Test Statistics
# ============================================================================


def test_get_compound_count(db_index):
    """Test get_compound_count returns correct count."""
    assert db_index.get_compound_count() == 5


def test_get_reaction_count(db_index):
    """Test get_reaction_count returns correct count."""
    assert db_index.get_reaction_count() == 4


# ============================================================================
# Test Index Initialization
# ============================================================================


def test_index_creates_lowercase_columns(sample_compounds_df, sample_reactions_df):
    """Test that index initialization creates lowercase columns."""
    index = DatabaseIndex(sample_compounds_df, sample_reactions_df)

    # Check compounds have lowercase columns
    assert "name_lower" in index.compounds_df.columns
    assert "abbreviation_lower" in index.compounds_df.columns

    # Check reactions have lowercase columns
    assert "name_lower" in index.reactions_df.columns
    assert "abbreviation_lower" in index.reactions_df.columns


def test_lowercase_columns_content(db_index):
    """Test that lowercase columns contain correct data."""
    # Check compound name_lower
    glucose = db_index.get_compound_by_id("cpd00027")
    assert glucose["name_lower"] == "d-glucose"
    assert glucose["abbreviation_lower"] == "glc__d"

    # Check reaction name_lower
    hexokinase = db_index.get_reaction_by_id("rxn00148")
    assert hexokinase["name_lower"] == "hexokinase"
    assert hexokinase["abbreviation_lower"] == "r00200"


# ============================================================================
# Test Performance Characteristics (Spec 007 requirement: <1ms lookup)
# ============================================================================


def test_lookup_performance(db_index):
    """Test that ID lookup is fast (<1ms).

    This test verifies that lookups work correctly.
    For actual performance benchmarking, use pytest-benchmark separately.
    """
    import time

    # Perform multiple lookups and measure time
    start = time.perf_counter()
    for _ in range(1000):
        result = db_index.get_compound_by_id("cpd00027")
    elapsed = time.perf_counter() - start

    # 1000 lookups should complete in less than 1 second (avg <1ms each)
    assert elapsed < 1.0
    assert result is not None


def test_existence_check_performance(db_index):
    """Test that existence check is fast (<1ms)."""
    import time

    # Perform multiple existence checks
    start = time.perf_counter()
    for _ in range(1000):
        result = db_index.compound_exists("cpd00027")
    elapsed = time.perf_counter() - start

    # 1000 checks should complete in less than 1 second (avg <1ms each)
    assert elapsed < 1.0
    assert result is True


# ============================================================================
# Test Edge Cases
# ============================================================================


def test_empty_query_string(db_index):
    """Test search with empty query string."""
    results = db_index.search_compounds_by_name("")
    # Empty string matches everything, limited by default limit
    assert len(results) <= 10


def test_special_characters_in_query(db_index):
    """Test search with special characters."""
    # Should not crash, may return no results
    results = db_index.search_compounds_by_name("D-Glucose")
    assert isinstance(results, list)


def test_very_long_query(db_index):
    """Test search with very long query string."""
    long_query = "a" * 1000
    results = db_index.search_compounds_by_name(long_query)
    assert isinstance(results, list)
    # Likely no matches for such a long string


def test_unicode_in_query(db_index):
    """Test search with Unicode characters."""
    results = db_index.search_compounds_by_name("α-glucose")
    assert isinstance(results, list)


def test_limit_zero(db_index):
    """Test search with limit=0."""
    results = db_index.search_compounds_by_name("glucose", limit=0)
    assert len(results) == 0


def test_limit_negative(db_index):
    """Test search with negative limit (pandas should handle gracefully)."""
    results = db_index.search_compounds_by_name("glucose", limit=-1)
    # pandas .head(-1) returns all but the last row, so we get results
    # This is expected pandas behavior
    assert isinstance(results, list)


def test_search_with_none_values(sample_compounds_df, sample_reactions_df):
    """Test search when DataFrame has None/NaN values."""
    # Add a compound with missing name
    sample_compounds_df.loc["cpd99999", "name"] = None
    sample_compounds_df.loc["cpd99999", "abbreviation"] = "test"

    index = DatabaseIndex(sample_compounds_df, sample_reactions_df)

    # Should not crash when searching
    results = index.search_compounds_by_name("glucose")
    assert isinstance(results, list)
