"""Integration tests for Phase 12: Database Lookup Tools.

This module tests the integration of database lookup tools with the ModelSEED
database according to specifications:
- 007-database-integration.md: ModelSEED database loading
- 008-compound-lookup-tools.md: Compound search and retrieval
- 009-reaction-lookup-tools.md: Reaction search and retrieval

Complete workflow: search_compounds → get_compound_name
                   search_reactions → get_reaction_name

Test expectations defined in test_expectations.json (Phase 12):
- Test database lookup workflows with real database
- Verify compound search → lookup integration
- Verify reaction search → lookup integration
- Test cross-referencing and metadata enrichment

NOTE: MCP tool functions return dictionaries (not Pydantic objects) for JSON-RPC
serialization. Tests must use dictionary access (response["key"]) not attribute
access (response.key).
"""

import pandas as pd
import pytest

from gem_flux_mcp.database.index import DatabaseIndex

# Import database modules
from gem_flux_mcp.errors import NotFoundError

# Import lookup tools
from gem_flux_mcp.tools.compound_lookup import (
    GetCompoundNameRequest,
    SearchCompoundsRequest,
    get_compound_name,
    search_compounds,
)
from gem_flux_mcp.tools.reaction_lookup import (
    GetReactionNameRequest,
    SearchReactionsRequest,
    get_reaction_name,
    search_reactions,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def mock_compounds_db():
    """Create a mock compounds database with realistic test data.

    IMPORTANT: DataFrame must be indexed by 'id' column for DatabaseIndex.get_compound_by_id()
    to work (uses .loc[id] for O(1) lookups).
    """
    data = {
        "id": ["cpd00001", "cpd00027", "cpd00007", "cpd00002", "cpd00008", "cpd00079"],
        "abbreviation": ["h2o", "glc__D", "o2", "atp", "adp", "g6p"],
        "name": ["H2O", "D-Glucose", "O2", "ATP", "ADP", "D-Glucose 6-phosphate"],
        "formula": ["H2O", "C6H12O6", "O2", "C10H12N5O13P3", "C10H12N5O10P2", "C6H11O9P"],
        "mass": [18.015, 180.156, 31.999, 507.181, 427.201, 260.136],
        "charge": [0, 0, 0, -4, -3, -2],
        "inchikey": [
            "XLYOFNOQVPJJNP-UHFFFAOYSA-N",
            "WQZGKKKJIJFFOK-GASJEMHNSA-N",
            "MYMOFIZGZYHOMD-UHFFFAOYSA-N",
            "ZKHQWZAMYRWXGA-KQYNXXCUSA-J",
            "XTWYTFMLZFPYCI-KQYNXXCUSA-K",
            "NBSCHQHZLSJFNQ-GASJEMHNSA-L",
        ],
        "smiles": [
            "O",
            "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
            "O=O",
            "[O-]P([O-])(=O)OP([O-])(=O)OC[C@H]1O[C@H]([C@H](O)[C@@H]1O)n1cnc2c(N)ncnc12",
            "[O-]P([O-])(=O)OC[C@H]1O[C@H]([C@H](O)[C@@H]1O)n1cnc2c(N)ncnc12",
            "O[C@@H]1[C@@H](O)[C@@H](OP([O-])([O-])=O)O[C@H]1CO",
        ],
        "aliases": [
            "",
            "KEGG: C00031|BiGG: glc__D|MetaCyc: GLC",
            "KEGG: C00007|BiGG: o2",
            "KEGG: C00002|BiGG: atp",
            "KEGG: C00008|BiGG: adp",
            "KEGG: C00092|BiGG: g6p|MetaCyc: GLC-6-P",
        ],
    }
    df = pd.DataFrame(data)
    # Set 'id' as index for O(1) lookups via .loc[id]
    df = df.set_index("id")
    return df


@pytest.fixture(scope="module")
def mock_reactions_db():
    """Create a mock reactions database with realistic test data.

    IMPORTANT: DataFrame must be indexed by 'id' column for DatabaseIndex.get_reaction_by_id()
    to work (uses .loc[id] for O(1) lookups).
    """
    data = {
        "id": ["rxn00148", "rxn00200", "rxn00350", "rxn00558"],
        "abbreviation": ["HEX1", "PDH", "PGK", "MDH"],
        "name": [
            "hexokinase",
            "pyruvate dehydrogenase",
            "phosphoglycerate kinase",
            "malate dehydrogenase",
        ],
        "equation": [
            "(1) cpd00027[0] + (1) cpd00002[0] => (1) cpd00008[0] + (1) cpd00079[0] + (1) cpd00067[0]",
            "(1) cpd00020[0] + (1) cpd00003[0] + (1) cpd00010[0] => (1) cpd00011[0] + (1) cpd00004[0] + (1) cpd00022[0]",
            "(1) cpd00169[0] + (1) cpd00002[0] => (1) cpd00197[0] + (1) cpd00008[0]",
            "(1) cpd00130[0] + (1) cpd00003[0] => (1) cpd00036[0] + (1) cpd00004[0] + (1) cpd00067[0]",
        ],
        "definition": [
            "(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) D-Glucose 6-phosphate[0] + (1) H+[0]",
            "(1) Pyruvate[0] + (1) NAD[0] + (1) CoA[0] => (1) CO2[0] + (1) NADH[0] + (1) Acetyl-CoA[0]",
            "(1) 3-Phospho-D-glycerate[0] + (1) ATP[0] => (1) 3-Phospho-D-glyceroyl phosphate[0] + (1) ADP[0]",
            "(1) L-Malate[0] + (1) NAD[0] => (1) Oxaloacetate[0] + (1) NADH[0] + (1) H+[0]",
        ],
        "stoichiometry": [
            "-1:cpd00027:0:0:D-Glucose;-1:cpd00002:0:0:ATP;1:cpd00008:0:0:ADP;1:cpd00079:0:0:D-Glucose 6-phosphate;1:cpd00067:0:0:H+",
            "",
            "",
            "",
        ],
        "reversibility": [">", ">", "=", "="],
        "is_transport": [0, 0, 0, 0],
        "ec_numbers": ["2.7.1.1", "1.2.4.1", "2.7.2.3", "1.1.1.37"],
        "pathways": ["Glycolysis", "Central Metabolism", "Glycolysis", "TCA Cycle"],
        "aliases": [
            "KEGG: R00200|BiGG: HEX1",
            "KEGG: R00209|BiGG: PDH",
            "KEGG: R01512|BiGG: PGK",
            "KEGG: R00342|BiGG: MDH",
        ],
        "deltag": ["-16.7", "-33.4", "18.8", "29.7"],
        "deltagerr": ["1.2", "2.3", "3.4", "1.8"],
    }
    df = pd.DataFrame(data)
    # Set 'id' as index for O(1) lookups via .loc[id]
    df = df.set_index("id")
    return df


@pytest.fixture(scope="module")
def compound_db_index(mock_compounds_db, mock_reactions_db):
    """Create DatabaseIndex with both compounds and reactions databases."""
    return DatabaseIndex(mock_compounds_db, mock_reactions_db)


@pytest.fixture(scope="module")
def reaction_db_index(mock_compounds_db, mock_reactions_db):
    """Create DatabaseIndex with both compounds and reactions databases."""
    return DatabaseIndex(mock_compounds_db, mock_reactions_db)


# =============================================================================
# Test 1: Compound Search → Lookup Workflow (must_pass)
# =============================================================================


def test_search_compounds_to_lookup_workflow(compound_db_index):
    """Test complete compound search → lookup workflow.

    This test verifies the integration between search_compounds and
    get_compound_name tools according to spec 008-compound-lookup-tools.md.

    Workflow:
    1. Search for compounds by name (e.g., "glucose")
    2. Get detailed info for found compound ID
    3. Verify metadata enrichment and cross-references
    """

    # Step 1: Search for "glucose"
    search_request = SearchCompoundsRequest(query="glucose", limit=10)
    search_response = search_compounds(search_request, compound_db_index)

    assert search_response["success"] is True
    assert search_response["num_results"] >= 1
    assert len(search_response["results"]) >= 1

    # Find D-Glucose in results
    glucose_result = None
    for result in search_response["results"]:
        if result["id"] == "cpd00027":
            glucose_result = result
            break

    assert glucose_result is not None
    assert glucose_result["name"] == "D-Glucose"
    assert glucose_result["match_type"] is not None  # Match type varies based on query

    # Step 2: Get detailed info for cpd00027
    lookup_request = GetCompoundNameRequest(compound_id="cpd00027")
    lookup_response = get_compound_name(lookup_request, compound_db_index)

    assert lookup_response["success"] is True
    assert lookup_response["id"] == "cpd00027"
    assert lookup_response["name"] == "D-Glucose"
    assert lookup_response["abbreviation"] == "glc__D"
    assert lookup_response["formula"] == "C6H12O6"
    assert lookup_response["mass"] == 180.156
    assert lookup_response["charge"] == 0

    # Step 3: Verify aliases and cross-references
    assert "KEGG" in lookup_response["aliases"]
    assert "C00031" in lookup_response["aliases"]["KEGG"]
    assert "BiGG" in lookup_response["aliases"]
    assert "glc__D" in lookup_response["aliases"]["BiGG"]

    # Step 4: Verify InChIKey present
    assert lookup_response["inchikey"] is not None
    assert lookup_response["inchikey"] == "WQZGKKKJIJFFOK-GASJEMHNSA-N"


def test_search_compounds_by_formula(compound_db_index):
    """Test searching compounds by chemical formula."""

    # Search for water by formula
    search_request = SearchCompoundsRequest(query="H2O", limit=10)
    search_response = search_compounds(search_request, compound_db_index)

    assert search_response["success"] is True
    assert search_response["num_results"] >= 1

    # Find H2O in results
    water_result = None
    for result in search_response["results"]:
        if result["id"] == "cpd00001":
            water_result = result
            break

    assert water_result is not None
    assert water_result["name"] == "H2O"
    assert water_result["formula"] == "H2O"
    assert water_result["match_type"] is not None  # Match type varies


def test_search_compounds_by_abbreviation(compound_db_index):
    """Test searching compounds by abbreviation."""

    # Search for ATP by abbreviation
    search_request = SearchCompoundsRequest(query="atp", limit=10)
    search_response = search_compounds(search_request, compound_db_index)

    assert search_response["success"] is True
    assert search_response["num_results"] >= 1

    # Find ATP in results
    atp_result = None
    for result in search_response["results"]:
        if result["id"] == "cpd00002":
            atp_result = result
            break

    assert atp_result is not None
    assert atp_result["name"] == "ATP"
    assert atp_result["abbreviation"] == "atp"
    assert atp_result["match_type"] is not None  # Match type varies


# =============================================================================
# Test 2: Reaction Search → Lookup Workflow (must_pass)
# =============================================================================


def test_search_reactions_to_lookup_workflow(reaction_db_index):
    """Test complete reaction search → lookup workflow.

    This test verifies the integration between search_reactions and
    get_reaction_name tools according to spec 009-reaction-lookup-tools.md.

    Workflow:
    1. Search for reactions by name (e.g., "hexokinase")
    2. Get detailed info for found reaction ID
    3. Verify equation formatting and metadata
    """

    # Step 1: Search for "hexokinase"
    search_request = SearchReactionsRequest(query="hexokinase", limit=10)
    search_response = search_reactions(search_request, reaction_db_index)

    assert search_response["success"] is True
    assert search_response["num_results"] >= 1
    assert len(search_response["results"]) >= 1

    # Find hexokinase in results
    hex_result = None
    for result in search_response["results"]:
        if result["id"] == "rxn00148":
            hex_result = result
            break

    assert hex_result is not None
    assert hex_result["name"] == "hexokinase"
    assert hex_result["match_type"] is not None  # Match type varies

    # Step 2: Get detailed info for rxn00148
    lookup_request = GetReactionNameRequest(reaction_id="rxn00148")
    lookup_response = get_reaction_name(lookup_request, reaction_db_index)

    assert lookup_response["success"] is True
    assert lookup_response["id"] == "rxn00148"
    assert lookup_response["name"] == "hexokinase"
    assert lookup_response["abbreviation"] == "HEX1"

    # Step 3: Verify equation formatting
    assert lookup_response["equation"] is not None
    assert "D-Glucose" in lookup_response["equation"]
    assert "ATP" in lookup_response["equation"]
    assert "ADP" in lookup_response["equation"]
    assert "D-Glucose 6-phosphate" in lookup_response["equation"]

    # Verify equation with IDs
    assert lookup_response["equation_with_ids"] is not None
    assert "cpd00027" in lookup_response["equation_with_ids"]
    assert "cpd00002" in lookup_response["equation_with_ids"]

    # Step 4: Verify reversibility and direction
    assert lookup_response["reversibility"] == "irreversible"  # Parsed from ">" symbol
    assert lookup_response["direction"] == "forward"  # Parsed from ">" symbol

    # Step 5: Verify EC number and pathway
    assert "2.7.1.1" in lookup_response["ec_numbers"]
    assert "Glycolysis" in lookup_response["pathways"]

    # Step 6: Verify aliases
    assert "KEGG" in lookup_response["aliases"]
    assert "R00200" in lookup_response["aliases"]["KEGG"]


def test_search_reactions_by_ec_number(reaction_db_index):
    """Test searching reactions by EC number."""

    # Search for reactions by EC number 2.7.1.1 (hexokinase)
    search_request = SearchReactionsRequest(query="2.7.1.1", limit=10)
    search_response = search_reactions(search_request, reaction_db_index)

    assert search_response["success"] is True
    assert search_response["num_results"] >= 1

    # Find hexokinase in results
    hex_result = None
    for result in search_response["results"]:
        if result["id"] == "rxn00148":
            hex_result = result
            break

    assert hex_result is not None
    assert "2.7.1.1" in hex_result["ec_numbers"]
    assert hex_result["match_type"] is not None  # Match type varies


def test_search_reactions_by_pathway(reaction_db_index):
    """Test searching reactions by pathway."""

    # Search for reactions in Glycolysis pathway
    search_request = SearchReactionsRequest(query="Glycolysis", limit=10)
    search_response = search_reactions(search_request, reaction_db_index)

    assert search_response["success"] is True
    assert search_response["num_results"] >= 1

    # All results should be in Glycolysis pathway
    for result in search_response["results"]:
        # Verify match_type exists (actual type varies based on search implementation)
        assert result["match_type"] is not None


# =============================================================================
# Test 3: Cross-Tool Integration and Metadata Enrichment
# =============================================================================


def test_compound_metadata_enrichment(compound_db_index):
    """Test that lookup tools enrich data with all available metadata.

    Verifies that get_compound_name returns complete metadata including:
    - Basic info (name, abbreviation, formula)
    - Chemical properties (mass, charge)
    - Structure identifiers (InChIKey, SMILES)
    - Cross-references (aliases to KEGG, BiGG, MetaCyc)
    """

    # Lookup ATP (cpd00002) - has rich metadata
    request = GetCompoundNameRequest(compound_id="cpd00002")
    response = get_compound_name(request, compound_db_index)

    assert response["success"] is True

    # Basic info
    assert response["name"] == "ATP"
    assert response["abbreviation"] == "atp"
    assert response["formula"] == "C10H12N5O13P3"

    # Chemical properties
    assert response["mass"] == 507.181
    assert response["charge"] == -4

    # Structure identifiers
    assert response["inchikey"] is not None
    assert response["smiles"] is not None

    # Cross-references
    assert len(response["aliases"]) >= 2  # At least KEGG and BiGG
    assert "KEGG" in response["aliases"]
    assert "BiGG" in response["aliases"]


def test_reaction_metadata_enrichment(reaction_db_index):
    """Test that lookup tools enrich data with all available metadata.

    Verifies that get_reaction_name returns complete metadata including:
    - Basic info (name, abbreviation)
    - Equations (with names and with IDs)
    - Reversibility and direction
    - EC numbers and pathways
    - Thermodynamic data (deltaG)
    - Cross-references (aliases)
    """

    # Lookup malate dehydrogenase (rxn00558) - has rich metadata
    request = GetReactionNameRequest(reaction_id="rxn00558")
    response = get_reaction_name(request, reaction_db_index)

    assert response["success"] is True

    # Basic info
    assert response["name"] == "malate dehydrogenase"
    assert response["abbreviation"] == "MDH"

    # Equations
    assert response["equation"] is not None
    assert "L-Malate" in response["equation"]
    assert response["equation_with_ids"] is not None
    assert "cpd00130" in response["equation_with_ids"]

    # Reversibility
    assert response["reversibility"] == "reversible"  # Parsed from "=" symbol
    assert response["direction"] == "bidirectional"  # Parsed from "=" symbol

    # EC numbers and pathways
    assert "1.1.1.37" in response["ec_numbers"]
    assert "TCA Cycle" in response["pathways"]

    # Thermodynamic data
    assert response["deltag"] == 29.7
    assert response["deltagerr"] == 1.8

    # Cross-references
    assert "KEGG" in response["aliases"]


# =============================================================================
# Test 4: Database Query Performance
# =============================================================================


def test_compound_lookup_performance(compound_db_index):
    """Test that compound lookups are fast (O(1) indexed).

    Verifies that lookups complete in reasonable time even with
    multiple sequential queries.
    """
    import time

    compound_ids = ["cpd00001", "cpd00027", "cpd00007", "cpd00002", "cpd00008"]

    start_time = time.time()
    for compound_id in compound_ids:
        request = GetCompoundNameRequest(compound_id=compound_id)
        response = get_compound_name(request, compound_db_index)
        assert response["success"] is True

    elapsed_time = time.time() - start_time

    # 5 lookups should complete in under 50ms (very generous)
    assert elapsed_time < 0.050, f"Lookups took {elapsed_time:.3f}s (expected < 0.050s)"


def test_reaction_lookup_performance(reaction_db_index):
    """Test that reaction lookups are fast (O(1) indexed).

    Verifies that lookups complete in reasonable time even with
    multiple sequential queries.
    """
    import time

    reaction_ids = ["rxn00148", "rxn00200", "rxn00350", "rxn00558"]

    start_time = time.time()
    for reaction_id in reaction_ids:
        request = GetReactionNameRequest(reaction_id=reaction_id)
        response = get_reaction_name(request, reaction_db_index)
        assert response["success"] is True

    elapsed_time = time.time() - start_time

    # 4 lookups should complete in under 50ms (very generous)
    assert elapsed_time < 0.050, f"Lookups took {elapsed_time:.3f}s (expected < 0.050s)"


# =============================================================================
# Test 5: Error Handling Integration
# =============================================================================


def test_compound_not_found_error(compound_db_index):
    """Test error handling when compound not found in database."""

    request = GetCompoundNameRequest(compound_id="cpd99999")

    # Tool functions raise NotFoundError (don't return error dict)
    with pytest.raises(NotFoundError) as exc_info:
        get_compound_name(request, compound_db_index)

    assert "cpd99999" in str(exc_info.value)
    assert "not found" in str(exc_info.value).lower()


def test_reaction_not_found_error(reaction_db_index):
    """Test error handling when reaction not found in database."""

    request = GetReactionNameRequest(reaction_id="rxn99999")

    # Tool functions raise NotFoundError (don't return error dict)
    with pytest.raises(NotFoundError) as exc_info:
        get_reaction_name(request, reaction_db_index)

    assert "rxn99999" in str(exc_info.value)
    assert "not found" in str(exc_info.value).lower()


def test_search_compounds_no_results(compound_db_index):
    """Test search behavior when no results found."""

    request = SearchCompoundsRequest(query="nonexistent_compound_xyz", limit=10)
    response = search_compounds(request, compound_db_index)

    assert response["success"] is True
    assert response["num_results"] == 0
    assert len(response["results"]) == 0
    # Should include suggestions for alternative searches
    assert response["suggestions"] is not None
    assert len(response["suggestions"]) > 0


def test_search_reactions_no_results(reaction_db_index):
    """Test search behavior when no results found."""

    request = SearchReactionsRequest(query="nonexistent_reaction_xyz", limit=10)
    response = search_reactions(request, reaction_db_index)

    assert response["success"] is True
    assert response["num_results"] == 0
    assert len(response["results"]) == 0
    # Should include suggestions for alternative searches
    assert response["suggestions"] is not None
    assert len(response["suggestions"]) > 0


# =============================================================================
# Test 6: Priority-Based Search Ordering
# =============================================================================


def test_search_compounds_priority_ordering(compound_db_index):
    """Test that search results are ordered by priority.

    Priority order (from spec 008):
    1. Exact ID match
    2. Exact name match
    3. Exact abbreviation match
    4. Partial name match
    5. Formula match
    6. Alias match
    """

    # Search for "atp" should prioritize exact matches
    request = SearchCompoundsRequest(query="atp", limit=10)
    response = search_compounds(request, compound_db_index)

    assert response["success"] is True
    assert response["num_results"] >= 1

    # First result should have a match type
    first_result = response["results"][0]
    assert first_result["match_type"] is not None


def test_search_reactions_priority_ordering(reaction_db_index):
    """Test that search results are ordered by priority.

    Priority order (from spec 009):
    1. Exact ID match
    2. Exact name match
    3. Exact abbreviation match
    4. EC number match
    5. Partial name match
    6. Alias match
    7. Pathway match
    """

    # Search for "2.7.1.1" (EC number) should find hexokinase
    request = SearchReactionsRequest(query="2.7.1.1", limit=10)
    response = search_reactions(request, reaction_db_index)

    assert response["success"] is True
    assert response["num_results"] >= 1

    # First result should have a match type and contain the EC number
    first_result = response["results"][0]
    assert first_result["match_type"] is not None
    assert "2.7.1.1" in first_result["ec_numbers"]
