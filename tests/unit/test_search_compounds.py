"""Unit tests for search_compounds tool.

Tests the compound search functionality as specified in 008-compound-lookup-tools.md.

Test Coverage:
    - Valid searches (exact ID, exact name, partial name, formula, alias)
    - Invalid searches (empty query, invalid limit)
    - Edge cases (no results, truncation, special characters)
    - Priority-based ranking
"""

import pandas as pd
import pytest

from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.errors import ValidationError
from gem_flux_mcp.tools.compound_lookup import (
    SearchCompoundsRequest,
    search_compounds,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_compounds_df():
    """Create mock compounds DataFrame for testing search.

    Contains variety of compounds for testing different search scenarios:
    - D-Glucose: Common compound for exact name matches
    - D-Glucose-6-phosphate: Test partial name matching
    - ATP: Test abbreviation matching
    - Compounds with formulas for formula search
    - Compounds with aliases for alias search
    """
    data = {
        "id": [
            "cpd00027",
            "cpd00079",
            "cpd00002",
            "cpd00001",
            "cpd00029",
            "cpd00007",
            "cpd00182",
            "cpd00221",
        ],
        "name": [
            "D-Glucose",
            "D-Glucose-6-phosphate",
            "ATP",
            "H2O",
            "Acetate",
            "O2",
            "alpha-D-Glucose",
            "D-Glucose-1-phosphate",
        ],
        "abbreviation": [
            "glc__D",
            "g6p_c",
            "atp_c",
            "h2o",
            "ac",
            "o2",
            "aglc__D",
            "g1p_c",
        ],
        "formula": [
            "C6H12O6",
            "C6H11O9P",
            "C10H12N5O13P3",
            "H2O",
            "C2H3O2",
            "O2",
            "C6H12O6",
            "C6H11O9P",
        ],
        "mass": [180.0, 258.0, 507.0, 18.0, 59.0, 32.0, 180.0, 258.0],
        "charge": [0, -2, -4, 0, -1, 0, 0, -2],
        "inchikey": ["KEY1", "KEY2", "KEY3", "KEY4", "KEY5", "KEY6", "KEY7", "KEY8"],
        "smiles": [
            "SMILES1",
            "SMILES2",
            "SMILES3",
            "O",
            "CC(=O)[O-]",
            "O=O",
            "SMILES7",
            "SMILES8",
        ],
        "aliases": [
            "KEGG: C00031|BiGG: glc__D",
            "KEGG: C00092|BiGG: g6p",
            "KEGG: C00002|BiGG: atp",
            "KEGG: C00001",
            "KEGG: C00033|BiGG: ac",
            "KEGG: C00007",
            "KEGG: C00221",
            "KEGG: C00103",
        ],
    }

    df = pd.DataFrame(data)
    df.set_index("id", inplace=True)
    return df


@pytest.fixture
def mock_reactions_df():
    """Create minimal mock reactions DataFrame (not used by search_compounds but required by DatabaseIndex)."""
    data = {
        "id": ["rxn00001"],
        "name": ["test_reaction"],
        "abbreviation": ["TEST"],
        "equation": ["test"],
        "reversibility": [">"],
        "ec_numbers": [""],
    }
    df = pd.DataFrame(data)
    df.set_index("id", inplace=True)
    return df


@pytest.fixture
def db_index(mock_compounds_df, mock_reactions_df):
    """Create DatabaseIndex with mock data."""
    return DatabaseIndex(mock_compounds_df, mock_reactions_df)


# =============================================================================
# Valid Search Tests
# =============================================================================


def test_search_exact_id_match(db_index):
    """Test exact ID match (highest priority)."""
    request = SearchCompoundsRequest(query="cpd00027", limit=10)
    response = search_compounds(request, db_index)

    assert response["success"] is True
    assert response["query"] == "cpd00027"
    assert response["num_results"] == 1
    assert len(response["results"]) == 1
    assert response["truncated"] is False

    result = response["results"][0]
    assert result["id"] == "cpd00027"
    assert result["name"] == "D-Glucose"
    assert result["match_field"] == "id"
    assert result["match_type"] == "exact"


def test_search_exact_name_match(db_index):
    """Test exact name match (case-insensitive).

    Note: Will also find partial matches (e.g., D-Glucose-6-phosphate contains D-Glucose).
    The first result should be the exact match with highest priority.
    """
    request = SearchCompoundsRequest(query="D-Glucose", limit=10)
    response = search_compounds(request, db_index)

    assert response["success"] is True
    assert response["num_results"] >= 1

    # First result should be the exact match (D-Glucose)
    result = response["results"][0]
    assert result["id"] == "cpd00027"
    assert result["name"] == "D-Glucose"
    assert result["match_field"] == "name"
    assert result["match_type"] == "exact"


def test_search_exact_name_case_insensitive(db_index):
    """Test exact name match is case-insensitive."""
    request = SearchCompoundsRequest(query="d-glucose", limit=10)
    response = search_compounds(request, db_index)

    assert response["success"] is True
    assert response["num_results"] >= 1
    # First result should be exact match
    assert response["results"][0]["id"] == "cpd00027"
    assert response["results"][0]["match_type"] == "exact"


def test_search_exact_abbreviation_match(db_index):
    """Test exact abbreviation match."""
    request = SearchCompoundsRequest(query="glc__D", limit=10)
    response = search_compounds(request, db_index)

    assert response["success"] is True
    assert response["num_results"] == 1

    result = response["results"][0]
    assert result["id"] == "cpd00027"
    assert result["abbreviation"] == "glc__D"
    assert result["match_field"] == "abbreviation"
    assert result["match_type"] == "exact"


def test_search_partial_name_match(db_index):
    """Test partial name matching (substring)."""
    request = SearchCompoundsRequest(query="glucose", limit=10)
    response = search_compounds(request, db_index)

    # Should find: D-Glucose, alpha-D-Glucose, D-Glucose-6-phosphate, D-Glucose-1-phosphate
    assert response["success"] is True
    assert response["num_results"] >= 3  # At least these compounds

    # Check that glucose-containing compounds are found
    found_ids = {result["id"] for result in response["results"]}
    assert "cpd00027" in found_ids  # D-Glucose
    assert "cpd00079" in found_ids  # D-Glucose-6-phosphate

    # All should match on name field (exact or partial)
    for result in response["results"]:
        assert result["match_field"] == "name"


def test_search_formula_match(db_index):
    """Test exact formula matching."""
    request = SearchCompoundsRequest(query="C6H12O6", limit=10)
    response = search_compounds(request, db_index)

    # Should find: D-Glucose and alpha-D-Glucose (both have same formula)
    assert response["success"] is True
    assert response["num_results"] >= 2

    found_ids = {result["id"] for result in response["results"]}
    assert "cpd00027" in found_ids
    assert "cpd00182" in found_ids

    # Check match field
    for result in response["results"]:
        assert result["formula"] == "C6H12O6"
        assert result["match_field"] == "formula"
        assert result["match_type"] == "exact"


def test_search_alias_match(db_index):
    """Test alias matching."""
    request = SearchCompoundsRequest(query="C00031", limit=10)
    response = search_compounds(request, db_index)

    # Should find D-Glucose (KEGG: C00031)
    assert response["success"] is True
    assert response["num_results"] >= 1

    result = response["results"][0]
    assert result["id"] == "cpd00027"
    assert result["match_field"] == "aliases"
    assert result["match_type"] == "partial"


def test_search_with_limit(db_index):
    """Test limit parameter restricts results."""
    request = SearchCompoundsRequest(query="glucose", limit=2)
    response = search_compounds(request, db_index)

    assert response["success"] is True
    assert response["num_results"] == 2
    assert len(response["results"]) == 2

    # Should be truncated (more than 2 glucose compounds exist)
    assert response["truncated"] is True


def test_search_priority_ordering(db_index):
    """Test that results are ordered by priority.

    Exact matches should come before partial matches.
    """
    request = SearchCompoundsRequest(query="glucose", limit=10)
    response = search_compounds(request, db_index)

    # First result should be exact match for "glucose" (if exists)
    # Or partial match with D-Glucose coming before others alphabetically
    results = response["results"]
    assert len(results) > 0

    # All name matches should be ordered alphabetically within priority
    name_matches = [r for r in results if r["match_field"] == "name"]
    if len(name_matches) > 1:
        names = [r["name"] for r in name_matches]
        assert names == sorted(names, key=str.lower)


def test_search_no_results(db_index):
    """Test search with no matches returns empty results with suggestions."""
    request = SearchCompoundsRequest(query="nonexistent_compound_xyz", limit=10)
    response = search_compounds(request, db_index)

    assert response["success"] is True
    assert response["num_results"] == 0
    assert len(response["results"]) == 0
    assert response["truncated"] is False

    # Should include suggestions
    assert response["suggestions"] is not None
    assert len(response["suggestions"]) > 0
    assert any("general" in s.lower() for s in response["suggestions"])


def test_search_default_limit(db_index):
    """Test default limit is 10."""
    request = SearchCompoundsRequest(query="glucose")
    response = search_compounds(request, db_index)

    # Should use default limit of 10
    assert response["num_results"] <= 10


# =============================================================================
# Invalid Input Tests
# =============================================================================


def test_search_empty_query_raises_error():
    """Test empty query raises ValidationError."""
    with pytest.raises(ValueError, match="non-empty string"):
        SearchCompoundsRequest(query="", limit=10)


def test_search_whitespace_query_raises_error():
    """Test whitespace-only query raises ValidationError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        SearchCompoundsRequest(query="   ", limit=10)


def test_search_limit_too_small_raises_error():
    """Test limit < 1 raises ValidationError."""
    with pytest.raises(ValueError):
        SearchCompoundsRequest(query="glucose", limit=0)


def test_search_limit_too_large_raises_error():
    """Test limit > 100 raises ValidationError."""
    with pytest.raises(ValueError):
        SearchCompoundsRequest(query="glucose", limit=101)


def test_search_negative_limit_raises_error():
    """Test negative limit raises ValidationError."""
    with pytest.raises(ValueError):
        SearchCompoundsRequest(query="glucose", limit=-1)


def test_search_non_string_query_raises_error():
    """Test non-string query raises ValidationError."""
    with pytest.raises(ValueError):
        SearchCompoundsRequest(query=123, limit=10)  # type: ignore


def test_search_none_query_raises_error():
    """Test None query raises ValidationError."""
    with pytest.raises(ValueError):
        SearchCompoundsRequest(query=None, limit=10)  # type: ignore


# =============================================================================
# Edge Cases
# =============================================================================


def test_search_single_character_query(db_index):
    """Test search with single character query."""
    request = SearchCompoundsRequest(query="O", limit=10)
    response = search_compounds(request, db_index)

    # Should find compounds with "O" in name (H2O, O2, etc.)
    assert response["success"] is True


def test_search_special_characters_in_query(db_index):
    """Test search with special characters."""
    request = SearchCompoundsRequest(query="6-phosphate", limit=10)
    response = search_compounds(request, db_index)

    # Should find glucose-6-phosphate compounds
    assert response["success"] is True
    if response["num_results"] > 0:
        assert any("phosphate" in r["name"].lower() for r in response["results"])


def test_search_removes_duplicates(db_index):
    """Test that search removes duplicate compounds (same ID matched in multiple fields)."""
    request = SearchCompoundsRequest(query="glc", limit=10)
    response = search_compounds(request, db_index)

    # Check no duplicate IDs
    found_ids = [r["id"] for r in response["results"]]
    assert len(found_ids) == len(set(found_ids))


def test_search_truncation_flag_correct(db_index):
    """Test truncated flag is set correctly."""
    # Search for "glucose" with very small limit
    request = SearchCompoundsRequest(query="glucose", limit=1)
    response = search_compounds(request, db_index)

    # Should have more than 1 glucose compound, so truncated=True
    if response["num_results"] == 1:
        # Only returned 1 due to limit, check if more exist
        request_all = SearchCompoundsRequest(query="glucose", limit=100)
        response_all = search_compounds(request_all, db_index)
        if response_all["num_results"] > 1:
            assert response["truncated"] is True


def test_search_query_trimmed(db_index):
    """Test query is trimmed of whitespace."""
    request = SearchCompoundsRequest(query="  glucose  ", limit=10)
    response = search_compounds(request, db_index)

    assert response["query"] == "glucose"  # Should be trimmed
    assert response["num_results"] >= 1


def test_search_response_includes_all_metadata(db_index):
    """Test search results include all required metadata fields."""
    request = SearchCompoundsRequest(query="cpd00027", limit=1)
    response = search_compounds(request, db_index)

    assert response["num_results"] == 1
    result = response["results"][0]

    # Check all required fields present
    assert "id" in result
    assert "name" in result
    assert "abbreviation" in result
    assert "formula" in result
    assert "mass" in result
    assert "charge" in result
    assert "match_field" in result
    assert "match_type" in result

    # Verify types
    assert isinstance(result["id"], str)
    assert isinstance(result["name"], str)
    assert isinstance(result["abbreviation"], str)
    assert isinstance(result["formula"], str)
    assert isinstance(result["mass"], (int, float))
    assert isinstance(result["charge"], int)
    assert isinstance(result["match_field"], str)
    assert isinstance(result["match_type"], str)


# =============================================================================
# Performance Tests (Logging/Validation)
# =============================================================================


def test_search_large_result_set_respects_limit(db_index):
    """Test that even with many matches, limit is respected."""
    request = SearchCompoundsRequest(query="c", limit=5)  # Common letter
    response = search_compounds(request, db_index)

    # Should respect limit
    assert response["num_results"] <= 5
    assert len(response["results"]) <= 5


def test_search_with_max_limit(db_index):
    """Test search with maximum allowed limit (100)."""
    request = SearchCompoundsRequest(query="c", limit=100)
    response = search_compounds(request, db_index)

    # Should not exceed 100
    assert response["num_results"] <= 100
    assert len(response["results"]) <= 100
