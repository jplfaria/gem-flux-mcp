"""Integration tests for database lookup tools.

Tests the compound and reaction lookup tools with real database.
These tests use real ModelSEED data and verify end-to-end functionality.
"""

import pytest
from pathlib import Path

from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.tools.compound_lookup import (
    get_compound_name,
    search_compounds,
    GetCompoundNameRequest,
    SearchCompoundsRequest,
)
from gem_flux_mcp.tools.reaction_lookup import (
    get_reaction_name,
    search_reactions,
    GetReactionNameRequest,
    SearchReactionsRequest,
)


@pytest.fixture
def real_database():
    """Load real ModelSEED database."""
    db_dir = Path(__file__).parent.parent.parent / "data" / "database"
    compounds_df = load_compounds_database(db_dir / "compounds.tsv")
    reactions_df = load_reactions_database(db_dir / "reactions.tsv")
    return DatabaseIndex(compounds_df, reactions_df)


class TestCompoundLookupIntegration:
    """Integration tests for compound lookup tools."""

    def test_get_compound_name_glucose(self, real_database):
        """Test retrieving glucose by ID."""
        request = GetCompoundNameRequest(compound_id="cpd00027")
        response = get_compound_name(request, real_database)

        assert response["success"] is True
        assert response["id"] == "cpd00027"
        assert "glucose" in response["name"].lower() or "dextrose" in response["name"].lower()
        assert response["formula"] == "C6H12O6"
        assert "abbreviation" in response
        assert "charge" in response
        assert "mass" in response
        assert "aliases" in response

    def test_get_compound_name_not_found(self, real_database):
        """Test error handling for nonexistent compound."""
        from gem_flux_mcp.errors import NotFoundError

        request = GetCompoundNameRequest(compound_id="cpd99999")

        with pytest.raises(NotFoundError) as exc_info:
            get_compound_name(request, real_database)

        error = exc_info.value
        assert error.error_code == "COMPOUND_NOT_FOUND"
        assert "cpd99999" in error.message

    def test_search_compounds_glucose(self, real_database):
        """Test searching for glucose."""
        request = SearchCompoundsRequest(query="glucose")
        response = search_compounds(request, real_database)

        assert response["success"] is True
        assert response["num_results"] > 0
        assert len(response["results"]) > 0

        # Verify result structure and that results contain glucose
        for cpd in response["results"]:
            assert "id" in cpd
            assert "name" in cpd
            assert "formula" in cpd
            assert "match_field" in cpd
            assert "match_type" in cpd
            # All results should have glucose in name or be glucose-related
            assert "glucose" in cpd["name"].lower() or "glu" in cpd["abbreviation"].lower()

    def test_search_compounds_with_limit(self, real_database):
        """Test searching with result limit."""
        request = SearchCompoundsRequest(query="acid", limit=5)
        response = search_compounds(request, real_database)

        assert response["success"] is True
        assert len(response["results"]) <= 5
        assert response["num_results"] == len(response["results"])

    def test_search_compounds_no_results(self, real_database):
        """Test searching with query that returns no results."""
        request = SearchCompoundsRequest(query="xyznonexistent123")
        response = search_compounds(request, real_database)

        assert response["success"] is True
        assert response["num_results"] == 0
        assert len(response["results"]) == 0

    def test_search_compounds_by_formula(self, real_database):
        """Test searching by molecular formula."""
        request = SearchCompoundsRequest(query="C6H12O6")
        response = search_compounds(request, real_database)

        assert response["success"] is True
        assert response["num_results"] > 0

        # Should find compounds with C6H12O6 formula (hexoses)
        # Verify that all results have this formula
        for cpd in response["results"]:
            assert cpd["formula"] == "C6H12O6"


class TestReactionLookupIntegration:
    """Integration tests for reaction lookup tools."""

    def test_get_reaction_name_by_id(self, real_database):
        """Test retrieving reaction by ID."""
        request = GetReactionNameRequest(reaction_id="rxn00001")
        response = get_reaction_name(request, real_database)

        assert response["success"] is True
        assert response["id"] == "rxn00001"
        assert "name" in response
        assert "equation" in response
        assert "equation_with_ids" in response
        assert "reversibility" in response
        assert "direction" in response
        assert "ec_numbers" in response
        assert "pathways" in response

    def test_get_reaction_name_not_found(self, real_database):
        """Test error handling for nonexistent reaction."""
        from gem_flux_mcp.errors import NotFoundError

        request = GetReactionNameRequest(reaction_id="rxn99999")

        with pytest.raises(NotFoundError) as exc_info:
            get_reaction_name(request, real_database)

        error = exc_info.value
        assert error.error_code == "REACTION_NOT_FOUND"
        assert "rxn99999" in error.message

    def test_search_reactions_kinase(self, real_database):
        """Test searching for kinase reactions."""
        request = SearchReactionsRequest(query="kinase")
        response = search_reactions(request, real_database)

        assert response["success"] is True
        assert response["num_results"] > 0
        assert len(response["results"]) > 0

        # Verify reaction structure
        for rxn in response["results"]:
            assert "id" in rxn
            assert "name" in rxn
            assert "equation" in rxn
            assert "match_field" in rxn
            assert "match_type" in rxn

    def test_search_reactions_with_limit(self, real_database):
        """Test searching reactions with result limit."""
        request = SearchReactionsRequest(query="synthase", limit=10)
        response = search_reactions(request, real_database)

        assert response["success"] is True
        assert len(response["results"]) <= 10
        assert response["num_results"] == len(response["results"])

    def test_search_reactions_no_results(self, real_database):
        """Test searching reactions with query that returns no results."""
        request = SearchReactionsRequest(query="xyznonexistent123")
        response = search_reactions(request, real_database)

        assert response["success"] is True
        assert response["num_results"] == 0
        assert len(response["results"]) == 0


class TestDatabaseLookupCrossReference:
    """Integration tests for cross-referencing compounds and reactions."""

    def test_find_compound_and_reactions(self, real_database):
        """Test workflow: find compound -> search for related reactions."""
        # Get glucose
        glucose_req = GetCompoundNameRequest(compound_id="cpd00027")
        glucose_resp = get_compound_name(glucose_req, real_database)
        assert glucose_resp["success"] is True
        assert "glucose" in glucose_resp["name"].lower()

        # Search for reactions involving glucose
        glucose_rxn_req = SearchReactionsRequest(query="glucose", limit=5)
        glucose_rxn_resp = search_reactions(glucose_rxn_req, real_database)
        assert glucose_rxn_resp["success"] is True
        # Many reactions involve glucose
        assert glucose_rxn_resp["num_results"] > 0

    def test_compound_search_then_detail_lookup(self, real_database):
        """Test workflow: search compounds -> get details for specific one."""
        # Search for ATP
        search_req = SearchCompoundsRequest(query="ATP", limit=5)
        search_resp = search_compounds(search_req, real_database)
        assert search_resp["success"] is True
        assert search_resp["num_results"] > 0

        # Get full details for first result
        first_compound_id = search_resp["results"][0]["id"]
        detail_req = GetCompoundNameRequest(compound_id=first_compound_id)
        detail_resp = get_compound_name(detail_req, real_database)
        assert detail_resp["success"] is True
        assert detail_resp["id"] == first_compound_id


@pytest.mark.slow
class TestDatabaseLookupPerformance:
    """Performance tests for database lookups."""

    def test_large_search_performance_compounds(self, real_database):
        """Test performance of broad compound search."""
        import time

        request = SearchCompoundsRequest(query="acid", limit=100)

        start = time.perf_counter()
        response = search_compounds(request, real_database)
        elapsed = time.perf_counter() - start

        # Should complete quickly (< 0.5 seconds)
        assert elapsed < 0.5
        assert response["success"] is True
        assert len(response["results"]) <= 100

    def test_multiple_lookups_performance(self, real_database):
        """Test performance of multiple sequential lookups."""
        import time

        compound_ids = ["cpd00027", "cpd00002", "cpd00001", "cpd00007", "cpd00009"]

        start = time.perf_counter()
        for cpd_id in compound_ids:
            request = GetCompoundNameRequest(compound_id=cpd_id)
            response = get_compound_name(request, real_database)
            assert response["success"] is True
        elapsed = time.perf_counter() - start

        # 5 lookups should complete quickly (< 0.1 seconds)
        assert elapsed < 0.1
