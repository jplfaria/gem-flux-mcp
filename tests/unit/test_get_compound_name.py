"""Unit tests for get_compound_name tool.

Tests the get_compound_name MCP tool implementation according to
specification 008-compound-lookup-tools.md.

Test Coverage:
    - Valid lookups (common compounds, water, ATP, etc.)
    - Invalid lookups (non-existent IDs, invalid format)
    - Edge cases (no aliases, empty SMILES, special characters)
    - Case insensitivity
    - Error responses
"""

import pandas as pd
import pytest

from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.errors import NotFoundError
from gem_flux_mcp.tools import GetCompoundNameRequest, get_compound_name


@pytest.fixture
def mock_compounds_df():
    """Create mock compounds DataFrame for testing."""
    data = {
        "id": ["cpd00027", "cpd00001", "cpd00002", "cpd00029"],
        "name": ["D-Glucose", "H2O", "ATP", "Acetate"],
        "abbreviation": ["glc__D", "h2o", "atp", "ac"],
        "formula": ["C6H12O6", "H2O", "C10H12N5O13P3", "C2H3O2"],
        "mass": [180.0, 18.0, 507.0, 59.0],
        "charge": [0, 0, -4, -1],
        "inchikey": [
            "WQZGKKKJIJFFOK-GASJEMHNSA-N",
            "XLYOFNOQVPJJNP-UHFFFAOYSA-N",
            "ZKHQWZAMYRWXGA-KQYNXXCUSA-J",
            "QTBSBXVTEAMEQO-UHFFFAOYSA-M",
        ],
        "smiles": [
            "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
            "O",
            "C1=NC(=C2C(=N1)N(C=N2)[C@H]3[C@@H]([C@@H]([C@H](O3)COP(=O)([O-])OP(=O)([O-])OP(=O)([O-])[O-])O)O)N",
            "CC(=O)[O-]",
        ],
        "aliases": [
            "KEGG: C00031|BiGG: glc__D|MetaCyc: GLC",
            "KEGG: C00001|BiGG: h2o",
            "KEGG: C00002|BiGG: atp|MetaCyc: ATP",
            "",  # No aliases
        ],
    }
    df = pd.DataFrame(data)
    df = df.set_index("id")

    # Add lowercase columns for searching (as done in DatabaseIndex.__init__)
    df["name_lower"] = df["name"].str.lower()
    df["abbreviation_lower"] = df["abbreviation"].str.lower()

    return df


@pytest.fixture
def mock_reactions_df():
    """Create empty reactions DataFrame (not used in compound lookup tests)."""
    data = {
        "id": [],
        "name": [],
        "abbreviation": [],
        "equation": [],
        "definition": [],
        "stoichiometry": [],
        "reversibility": [],
        "is_transport": [],
        "ec_numbers": [],
        "pathways": [],
        "aliases": [],
    }
    df = pd.DataFrame(data, dtype=str)  # Specify dtype=str to avoid type issues
    df = df.set_index("id")
    # Add empty lowercase columns
    df["name_lower"] = pd.Series([], dtype=str)
    df["abbreviation_lower"] = pd.Series([], dtype=str)
    return df


@pytest.fixture
def db_index(mock_compounds_df, mock_reactions_df):
    """Create DatabaseIndex with mock data."""
    return DatabaseIndex(mock_compounds_df, mock_reactions_df)


# =============================================================================
# Valid Lookup Tests
# =============================================================================


def test_get_compound_name_glucose(db_index):
    """Test lookup of D-Glucose (cpd00027)."""
    request = GetCompoundNameRequest(compound_id="cpd00027")
    response = get_compound_name(request, db_index)

    assert response["success"] is True
    assert response["id"] == "cpd00027"
    assert response["name"] == "D-Glucose"
    assert response["abbreviation"] == "glc__D"
    assert response["formula"] == "C6H12O6"
    assert response["mass"] == 180.0
    assert response["charge"] == 0
    assert response["inchikey"] == "WQZGKKKJIJFFOK-GASJEMHNSA-N"
    assert "KEGG" in response["aliases"]
    assert "C00031" in response["aliases"]["KEGG"]
    assert "BiGG" in response["aliases"]
    assert "glc__D" in response["aliases"]["BiGG"]


def test_get_compound_name_water(db_index):
    """Test lookup of water (cpd00001)."""
    request = GetCompoundNameRequest(compound_id="cpd00001")
    response = get_compound_name(request, db_index)

    assert response["success"] is True
    assert response["id"] == "cpd00001"
    assert response["name"] == "H2O"
    assert response["formula"] == "H2O"
    assert response["mass"] == 18.0
    assert response["charge"] == 0


def test_get_compound_name_atp(db_index):
    """Test lookup of ATP (cpd00002) with complex aliases."""
    request = GetCompoundNameRequest(compound_id="cpd00002")
    response = get_compound_name(request, db_index)

    assert response["success"] is True
    assert response["id"] == "cpd00002"
    assert response["name"] == "ATP"
    assert response["charge"] == -4  # ATP has negative charge
    assert "KEGG" in response["aliases"]
    assert "BiGG" in response["aliases"]
    assert "MetaCyc" in response["aliases"]


def test_get_compound_name_acetate_with_charge(db_index):
    """Test lookup of acetate (cpd00029) with charge=-1."""
    request = GetCompoundNameRequest(compound_id="cpd00029")
    response = get_compound_name(request, db_index)

    assert response["success"] is True
    assert response["id"] == "cpd00029"
    assert response["name"] == "Acetate"
    assert response["charge"] == -1
    # No aliases for this compound
    assert response["aliases"] == {}


# =============================================================================
# Case Insensitivity Tests
# =============================================================================


def test_get_compound_name_case_insensitive(db_index):
    """Test that compound ID lookup is case-insensitive."""
    # Uppercase
    request_upper = GetCompoundNameRequest(compound_id="CPD00027")
    response_upper = get_compound_name(request_upper, db_index)

    # Lowercase (default)
    request_lower = GetCompoundNameRequest(compound_id="cpd00027")
    response_lower = get_compound_name(request_lower, db_index)

    # Mixed case
    request_mixed = GetCompoundNameRequest(compound_id="CpD00027")
    response_mixed = get_compound_name(request_mixed, db_index)

    # All should return same result
    assert response_upper["name"] == "D-Glucose"
    assert response_lower["name"] == "D-Glucose"
    assert response_mixed["name"] == "D-Glucose"


# =============================================================================
# Invalid Lookup Tests
# =============================================================================


def test_get_compound_name_not_found(db_index):
    """Test lookup of non-existent compound ID."""
    request = GetCompoundNameRequest(compound_id="cpd99999")

    with pytest.raises(NotFoundError) as exc_info:
        get_compound_name(request, db_index)

    error = exc_info.value
    assert error.error_code == "COMPOUND_NOT_FOUND"
    assert "cpd99999" in error.message
    assert "not found" in error.message.lower()
    assert error.details["compound_id"] == "cpd99999"
    assert len(error.suggestions) > 0


def test_get_compound_name_invalid_format_too_short(db_index):
    """Test invalid compound ID format (too short)."""
    with pytest.raises(ValueError) as exc_info:
        GetCompoundNameRequest(compound_id="cpd001")

    assert "Invalid compound ID format" in str(exc_info.value)


def test_get_compound_name_invalid_format_wrong_prefix(db_index):
    """Test invalid compound ID format (wrong prefix)."""
    with pytest.raises(ValueError) as exc_info:
        GetCompoundNameRequest(compound_id="compound00027")

    assert "Invalid compound ID format" in str(exc_info.value)


def test_get_compound_name_invalid_format_letters(db_index):
    """Test invalid compound ID format (letters in number part)."""
    with pytest.raises(ValueError) as exc_info:
        GetCompoundNameRequest(compound_id="cpdABCDE")

    assert "Invalid compound ID format" in str(exc_info.value)


def test_get_compound_name_empty_input(db_index):
    """Test empty compound ID input."""
    with pytest.raises(ValueError):
        GetCompoundNameRequest(compound_id="")


# =============================================================================
# Edge Cases
# =============================================================================


def test_get_compound_name_whitespace_trimmed(db_index):
    """Test that whitespace is trimmed from compound ID."""
    request = GetCompoundNameRequest(compound_id="  cpd00027  ")
    response = get_compound_name(request, db_index)

    assert response["success"] is True
    assert response["id"] == "cpd00027"
    assert response["name"] == "D-Glucose"


def test_get_compound_name_no_aliases(db_index):
    """Test compound with no aliases (empty aliases field)."""
    request = GetCompoundNameRequest(compound_id="cpd00029")
    response = get_compound_name(request, db_index)

    assert response["success"] is True
    assert response["aliases"] == {}


def test_get_compound_name_response_structure(db_index):
    """Test that response contains all required fields."""
    request = GetCompoundNameRequest(compound_id="cpd00027")
    response = get_compound_name(request, db_index)

    # Check all required fields present
    required_fields = [
        "success",
        "id",
        "name",
        "abbreviation",
        "formula",
        "mass",
        "charge",
        "inchikey",
        "smiles",
        "aliases",
    ]
    for field in required_fields:
        assert field in response, f"Missing required field: {field}"

    # Check types
    assert isinstance(response["success"], bool)
    assert isinstance(response["id"], str)
    assert isinstance(response["name"], str)
    assert isinstance(response["formula"], str)
    assert isinstance(response["mass"], float)
    assert isinstance(response["charge"], int)
    assert isinstance(response["aliases"], dict)


# =============================================================================
# Performance Tests
# =============================================================================


def test_get_compound_name_performance(db_index):
    """Test that lookup performance is fast (spec requirement: < 1ms)."""
    import time

    request = GetCompoundNameRequest(compound_id="cpd00027")

    # Measure time for multiple lookups
    start = time.perf_counter()
    for _ in range(100):
        result = get_compound_name(request, db_index)
    end = time.perf_counter()

    # Calculate average time per lookup
    avg_time_ms = ((end - start) / 100) * 1000

    # Verify result is correct
    assert result["name"] == "D-Glucose"

    # Performance should be much faster than 1ms (spec requirement)
    # In practice, should be < 0.1ms with indexed lookups
    assert avg_time_ms < 1.0, f"Average lookup time {avg_time_ms:.3f}ms exceeds 1ms"
