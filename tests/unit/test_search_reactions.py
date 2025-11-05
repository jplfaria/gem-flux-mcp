"""Unit tests for search_reactions tool.

Tests the search_reactions functionality from spec 009-reaction-lookup-tools.md.
"""

import pandas as pd
import pytest
from pydantic import ValidationError as PydanticValidationError

from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.tools.reaction_lookup import (
    SearchReactionsRequest,
    search_reactions,
)


@pytest.fixture
def sample_reactions_db():
    """Create sample reactions database for testing."""
    # Create empty compounds dataframe with required columns
    compounds_data = {
        "id": [],
        "name": [],
        "abbreviation": [],
        "formula": [],
        "mass": [],
        "charge": [],
        "inchikey": [],
        "smiles": [],
        "aliases": [],
    }
    compounds_df = pd.DataFrame(compounds_data)
    if not compounds_df.empty:
        compounds_df.set_index("id", inplace=True)

    # Create reactions dataframe
    data = {
        "id": [
            "rxn00001",
            "rxn00148",
            "rxn00200",
            "rxn00225",
            "rxn00350",
            "rxn00558",
            "rxn00782",
            "rxn01100",
        ],
        "name": [
            "malate dehydrogenase",
            "hexokinase",
            "pyruvate dehydrogenase",
            "acetate kinase",
            "phosphoglycerate kinase",
            "malate dehydrogenase (NAD)",
            "ATP synthase",
            "glucokinase",
        ],
        "abbreviation": [
            "MDH",
            "HEX1",
            "PDH",
            "ACK",
            "PGK",
            "MDH2",
            "ATPS",
            "GCK",
        ],
        "equation": [
            "(1) cpd00001[0] + (1) cpd00002[0] => (1) cpd00008[0]",
            "(1) cpd00027[0] + (1) cpd00002[0] => (1) cpd00008[0] + (1) cpd00079[0]",
            "(1) cpd00020[0] + (1) cpd00010[0] => (1) cpd00011[0] + (1) cpd00022[0]",
            "(1) cpd00029[0] + (1) cpd00002[0] => (1) cpd00008[0] + (1) cpd00023[0]",
            "(1) cpd00091[0] + (1) cpd00008[0] => (1) cpd00002[0] + (1) cpd00236[0]",
            "(1) cpd00036[0] + (1) cpd00003[0] => (1) cpd00004[0] + (1) cpd00036[0]",
            "(1) cpd00008[0] + (1) cpd00009[0] => (1) cpd00002[0] + (1) cpd00001[0]",
            "(1) cpd00027[0] + (1) cpd00002[0] => (1) cpd00008[0] + (1) cpd00079[0]",
        ],
        "definition": [
            "(1) H2O[0] + (1) ATP[0] => (1) ADP[0]",
            "(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) D-Glucose-6-phosphate[0]",
            "(1) Pyruvate[0] + (1) CoA[0] => (1) CO2[0] + (1) Acetyl-CoA[0]",
            "(1) Acetate[0] + (1) ATP[0] => (1) ADP[0] + (1) Acetyl-phosphate[0]",
            "(1) 3-Phosphoglycerate[0] + (1) ADP[0] => (1) ATP[0] + (1) 1,3-Bisphosphoglycerate[0]",
            "(1) Oxaloacetate[0] + (1) NAD[0] => (1) NADH[0] + (1) Oxaloacetate[0]",
            "(1) ADP[0] + (1) Phosphate[0] => (1) ATP[0] + (1) H2O[0]",
            "(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) D-Glucose-6-phosphate[0]",
        ],
        "reversibility": [">", ">", ">", ">", "=", "=", ">", ">"],
        "is_transport": [0, 0, 0, 0, 0, 0, 0, 0],
        "ec_numbers": [
            "1.1.1.37",
            "2.7.1.1",
            "1.2.4.1",
            "2.7.2.1",
            "2.7.2.3",
            "1.1.1.37",
            "3.6.3.14",
            "2.7.1.2",
        ],
        "pathways": [
            "TCA cycle",
            "Glycolysis",
            "Central metabolism",
            "Fermentation",
            "Glycolysis",
            "TCA cycle",
            "Energy production",
            "Glycolysis",
        ],
        "aliases": [
            "BiGG: MDH|KEGG: R00342",
            "BiGG: HEX1|KEGG: R00200",
            "BiGG: PDH|KEGG: R00209",
            "BiGG: ACK|KEGG: R00315",
            "BiGG: PGK|KEGG: R01512",
            "BiGG: MDH2|KEGG: R00343",
            "BiGG: ATPS|KEGG: R00086",
            "BiGG: GCK|KEGG: R00700",
        ],
    }

    df = pd.DataFrame(data)
    df.set_index("id", inplace=True)

    # Add lowercase columns for case-insensitive searching
    df["name_lower"] = df["name"].str.lower()
    df["abbreviation_lower"] = df["abbreviation"].str.lower()

    # Create DatabaseIndex
    db_index = DatabaseIndex(compounds_df=compounds_df, reactions_df=df)

    return db_index


# =============================================================================
# Request Validation Tests
# =============================================================================


def test_search_reactions_request_valid():
    """Test valid SearchReactionsRequest creation."""
    request = SearchReactionsRequest(query="hexokinase", limit=10)
    assert request.query == "hexokinase"
    assert request.limit == 10


def test_search_reactions_request_default_limit():
    """Test SearchReactionsRequest uses default limit of 10."""
    request = SearchReactionsRequest(query="hexokinase")
    assert request.limit == 10


def test_search_reactions_request_empty_query():
    """Test SearchReactionsRequest rejects empty query."""
    with pytest.raises(PydanticValidationError) as exc_info:
        SearchReactionsRequest(query="")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert "query" in errors[0]["loc"]
    assert "empty" in str(errors[0]["msg"]).lower()


def test_search_reactions_request_whitespace_query():
    """Test SearchReactionsRequest rejects whitespace-only query."""
    with pytest.raises(PydanticValidationError) as exc_info:
        SearchReactionsRequest(query="   ")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert "query" in errors[0]["loc"]


def test_search_reactions_request_limit_too_low():
    """Test SearchReactionsRequest rejects limit < 1."""
    with pytest.raises(PydanticValidationError) as exc_info:
        SearchReactionsRequest(query="hexokinase", limit=0)

    errors = exc_info.value.errors()
    assert any("limit" in str(e["loc"]) for e in errors)


def test_search_reactions_request_limit_too_high():
    """Test SearchReactionsRequest rejects limit > 100."""
    with pytest.raises(PydanticValidationError) as exc_info:
        SearchReactionsRequest(query="hexokinase", limit=101)

    errors = exc_info.value.errors()
    assert any("limit" in str(e["loc"]) for e in errors)


def test_search_reactions_request_query_trimming():
    """Test SearchReactionsRequest trims query whitespace."""
    request = SearchReactionsRequest(query="  hexokinase  ")
    assert request.query == "hexokinase"


# =============================================================================
# Search Functionality Tests
# =============================================================================


def test_search_reactions_exact_id_match(sample_reactions_db):
    """Test search finds reaction by exact ID match."""
    request = SearchReactionsRequest(query="rxn00148", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    assert result["num_results"] == 1
    assert result["results"][0]["id"] == "rxn00148"
    assert result["results"][0]["name"] == "hexokinase"
    assert result["results"][0]["match_field"] == "id"
    assert result["results"][0]["match_type"] == "exact"


def test_search_reactions_exact_name_match(sample_reactions_db):
    """Test search finds reaction by exact name match (case-insensitive)."""
    request = SearchReactionsRequest(query="hexokinase", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    assert result["num_results"] == 1
    assert result["results"][0]["id"] == "rxn00148"
    assert result["results"][0]["name"] == "hexokinase"
    assert result["results"][0]["match_field"] == "name"
    assert result["results"][0]["match_type"] == "exact"


def test_search_reactions_case_insensitive(sample_reactions_db):
    """Test search is case-insensitive."""
    request = SearchReactionsRequest(query="HEXOKINASE", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    assert result["num_results"] == 1
    assert result["results"][0]["name"] == "hexokinase"


def test_search_reactions_exact_abbreviation_match(sample_reactions_db):
    """Test search finds reaction by exact abbreviation match."""
    request = SearchReactionsRequest(query="hex1", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    assert result["num_results"] == 1
    assert result["results"][0]["id"] == "rxn00148"
    assert result["results"][0]["match_field"] == "abbreviation"
    assert result["results"][0]["match_type"] == "exact"


def test_search_reactions_ec_number_match(sample_reactions_db):
    """Test search finds reaction by EC number."""
    request = SearchReactionsRequest(query="2.7.1.1", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    assert result["num_results"] == 1
    assert result["results"][0]["id"] == "rxn00148"
    assert result["results"][0]["match_field"] == "ec_numbers"
    assert result["results"][0]["match_type"] == "exact"
    assert "2.7.1.1" in result["results"][0]["ec_numbers"]


def test_search_reactions_partial_name_match(sample_reactions_db):
    """Test search finds reactions by partial name match."""
    request = SearchReactionsRequest(query="kinase", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    # Should find: hexokinase, acetate kinase, phosphoglycerate kinase, glucokinase
    assert result["num_results"] >= 4

    # Check that all results contain "kinase" in name
    for reaction in result["results"]:
        assert "kinase" in reaction["name"].lower()


def test_search_reactions_alias_match(sample_reactions_db):
    """Test search finds reaction by alias."""
    request = SearchReactionsRequest(query="R00200", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    assert result["num_results"] >= 1
    # Find the hexokinase result
    hexokinase_result = next((r for r in result["results"] if r["id"] == "rxn00148"), None)
    assert hexokinase_result is not None
    assert hexokinase_result["match_field"] == "aliases"


def test_search_reactions_pathway_match(sample_reactions_db):
    """Test search finds reactions by pathway."""
    request = SearchReactionsRequest(query="glycolysis", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    # Should find: hexokinase, phosphoglycerate kinase, glucokinase
    assert result["num_results"] >= 3


def test_search_reactions_limit_parameter(sample_reactions_db):
    """Test search respects limit parameter."""
    request = SearchReactionsRequest(query="kinase", limit=2)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    assert result["num_results"] == 2
    assert len(result["results"]) == 2


def test_search_reactions_truncation_flag(sample_reactions_db):
    """Test truncated flag is set when more results exist."""
    request = SearchReactionsRequest(query="kinase", limit=2)
    result = search_reactions(request, sample_reactions_db)

    # Should have more than 2 kinase reactions, so truncated should be True
    assert result["truncated"] is True


def test_search_reactions_no_truncation(sample_reactions_db):
    """Test truncated flag is false when all results returned."""
    request = SearchReactionsRequest(query="hexokinase", limit=10)
    result = search_reactions(request, sample_reactions_db)

    # Only 1 exact match, so truncated should be False
    assert result["truncated"] is False


def test_search_reactions_empty_results(sample_reactions_db):
    """Test search returns empty results with suggestions for no matches."""
    request = SearchReactionsRequest(query="nonexistent_reaction_xyz", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    assert result["num_results"] == 0
    assert len(result["results"]) == 0
    assert result["suggestions"] is not None
    assert len(result["suggestions"]) > 0
    assert any("Try a more general" in s for s in result["suggestions"])


def test_search_reactions_priority_ordering(sample_reactions_db):
    """Test search returns results in priority order (exact before partial)."""
    request = SearchReactionsRequest(query="malate", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    # Should find: "malate dehydrogenase" (partial name match)
    # and "malate dehydrogenase (NAD)" (partial name match)
    assert result["num_results"] >= 1

    # First result should be alphabetically first among same priority
    first_result = result["results"][0]
    assert "malate" in first_result["name"].lower()


def test_search_reactions_duplicate_removal(sample_reactions_db):
    """Test search removes duplicate results (same reaction matched in multiple fields)."""
    # "2.7.1.1" should match hexokinase by EC number
    # but if it also appears in name/alias, should only return once
    request = SearchReactionsRequest(query="2.7.1.1", limit=10)
    result = search_reactions(request, sample_reactions_db)

    # Get all reaction IDs
    reaction_ids = [r["id"] for r in result["results"]]

    # Check no duplicates
    assert len(reaction_ids) == len(set(reaction_ids))


def test_search_reactions_includes_equation(sample_reactions_db):
    """Test search results include formatted equation."""
    request = SearchReactionsRequest(query="hexokinase", limit=1)
    result = search_reactions(request, sample_reactions_db)

    assert result["num_results"] == 1
    equation = result["results"][0]["equation"]
    assert equation is not None
    assert len(equation) > 0
    # Should be formatted without compartment suffixes
    assert "[0]" not in equation or equation.count("[") == 0


def test_search_reactions_includes_ec_numbers(sample_reactions_db):
    """Test search results include parsed EC numbers."""
    request = SearchReactionsRequest(query="hexokinase", limit=1)
    result = search_reactions(request, sample_reactions_db)

    assert result["num_results"] == 1
    ec_numbers = result["results"][0]["ec_numbers"]
    assert isinstance(ec_numbers, list)
    assert "2.7.1.1" in ec_numbers


def test_search_reactions_multiple_ec_numbers(sample_reactions_db):
    """Test search handles reactions with multiple EC numbers."""
    # "malate dehydrogenase" appears twice with same EC number
    request = SearchReactionsRequest(query="1.1.1.37", limit=10)
    result = search_reactions(request, sample_reactions_db)

    assert result["success"] is True
    # Should find both malate dehydrogenase reactions
    assert result["num_results"] >= 2


def test_search_reactions_alphabetical_sorting(sample_reactions_db):
    """Test search results are sorted alphabetically within same priority."""
    request = SearchReactionsRequest(query="kinase", limit=10)
    result = search_reactions(request, sample_reactions_db)

    # All are partial name matches (same priority), so should be alphabetical
    names = [r["name"] for r in result["results"]]

    # Check names are in alphabetical order (case-insensitive)
    names_lower = [n.lower() for n in names]
    assert names_lower == sorted(names_lower)
