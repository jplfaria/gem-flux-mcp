"""Unit tests for get_reaction_name tool.

Tests the get_reaction_name tool implementation as specified in
009-reaction-lookup-tools.md.
"""

import pandas as pd
import pytest
from pydantic import ValidationError

from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.errors import NotFoundError
from gem_flux_mcp.tools.reaction_lookup import (
    GetReactionNameRequest,
    format_equation_readable,
    get_reaction_name,
    parse_ec_numbers,
    parse_pathways,
    parse_reversibility_and_direction,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_reactions_df():
    """Create sample reactions DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": ["rxn00148", "rxn00200", "rxn05064", "rxn00216"],
            "name": ["hexokinase", "pyruvate dehydrogenase", "glucose transport", "citrate synthase"],
            "abbreviation": ["R00200", "R01196", "GLCt", "R00351"],
            "equation": [
                "(1) cpd00027[c0] + (1) cpd00002[c0] => (1) cpd00008[c0] + (1) cpd00067[c0] + (1) cpd00079[c0]",
                "(1) cpd00020[c0] + (1) cpd00003[c0] => (1) cpd00022[c0] + (1) cpd00011[c0] + (1) cpd00004[c0]",
                "(1) cpd00027[e0] => (1) cpd00027[c0]",
                "(1) cpd00022[c0] + (1) cpd00024[c0] => (1) cpd00036[c0]",
            ],
            "definition": [
                "(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0] + (1) H+[0] + (1) D-Glucose-6-phosphate[0]",
                "(1) Pyruvate[0] + (1) NAD[0] => (1) Acetyl-CoA[0] + (1) CO2[0] + (1) NADH[0]",
                "(1) D-Glucose[e0] => (1) D-Glucose[c0]",
                "(1) Acetyl-CoA[0] + (1) Oxaloacetate[0] => (1) Citrate[0]",
            ],
            "reversibility": [">", ">", "=", ">"],
            "is_transport": [0, 0, 1, 0],
            "ec_numbers": ["2.7.1.1", "1.2.4.1", "", "2.3.3.1"],
            "pathways": [
                "Glycolysis",
                "MetaCyc: TCA Cycle|KEGG: rn00020 (Citrate cycle)",
                "",
                "Glycolysis; Central Metabolism",
            ],
            "deltag": [-16.7, -33.4, 0.0, -31.5],
            "deltagerr": [1.5, 2.0, 0.0, 1.8],
            "aliases": [
                "KEGG: R00200|BiGG: HEX1|MetaCyc: GLUCOKIN-RXN",
                "KEGG: R01196",
                "",
                "KEGG: R00351|BiGG: CS",
            ],
        }
    ).set_index("id")


@pytest.fixture
def db_index(sample_reactions_df):
    """Create DatabaseIndex with sample reactions."""
    # Create empty compounds dataframe (not used in these tests)
    # Set explicit dtype to avoid str accessor issues
    compounds_df = pd.DataFrame(
        columns=["id", "name", "abbreviation", "formula", "mass", "charge", "inchikey", "smiles", "aliases"]
    ).astype({
        "name": str,
        "abbreviation": str,
        "formula": str,
        "aliases": str
    }).set_index("id")

    return DatabaseIndex(compounds_df, sample_reactions_df)


# =============================================================================
# Request Validation Tests
# =============================================================================


def test_valid_reaction_id():
    """Test valid reaction ID format."""
    request = GetReactionNameRequest(reaction_id="rxn00148")
    assert request.reaction_id == "rxn00148"


def test_case_insensitive_reaction_id():
    """Test reaction ID is case-insensitive."""
    request = GetReactionNameRequest(reaction_id="RXN00148")
    assert request.reaction_id == "rxn00148"


def test_reaction_id_with_whitespace():
    """Test reaction ID with leading/trailing whitespace."""
    request = GetReactionNameRequest(reaction_id="  rxn00148  ")
    assert request.reaction_id == "rxn00148"


def test_empty_reaction_id():
    """Test empty reaction ID raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        GetReactionNameRequest(reaction_id="")

    error = exc_info.value.errors()[0]
    assert "Reaction ID must be a non-empty string" in str(error["ctx"])


def test_invalid_reaction_id_format():
    """Test invalid reaction ID format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        GetReactionNameRequest(reaction_id="reaction001")

    error = exc_info.value.errors()[0]
    assert "rxn" in str(error["ctx"]).lower()


def test_reaction_id_wrong_prefix():
    """Test reaction ID with wrong prefix raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        GetReactionNameRequest(reaction_id="cpd00001")

    error = exc_info.value.errors()[0]
    assert "rxn" in str(error["ctx"]).lower()


def test_reaction_id_too_short():
    """Test reaction ID with too few digits raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        GetReactionNameRequest(reaction_id="rxn001")

    error = exc_info.value.errors()[0]
    assert "5 digits" in str(error["ctx"]).lower()


# =============================================================================
# get_reaction_name Tests
# =============================================================================


def test_get_reaction_name_success(db_index):
    """Test successful reaction lookup returns complete metadata."""
    request = GetReactionNameRequest(reaction_id="rxn00148")
    response = get_reaction_name(request, db_index)

    assert response["success"] is True
    assert response["id"] == "rxn00148"
    assert response["name"] == "hexokinase"
    assert response["abbreviation"] == "R00200"
    assert "D-Glucose" in response["equation"]
    assert "ATP" in response["equation"]
    assert "cpd00027" in response["equation_with_ids"]
    assert response["reversibility"] == "irreversible"
    assert response["direction"] == "forward"
    assert response["is_transport"] is False
    assert response["ec_numbers"] == ["2.7.1.1"]
    assert response["pathways"] == ["Glycolysis"]
    assert response["deltag"] == -16.7
    assert response["deltagerr"] == 1.5
    assert "KEGG" in response["aliases"]
    assert "R00200" in response["aliases"]["KEGG"]


def test_get_reaction_name_not_found(db_index):
    """Test reaction not found raises NotFoundError."""
    request = GetReactionNameRequest(reaction_id="rxn99999")

    with pytest.raises(NotFoundError) as exc_info:
        get_reaction_name(request, db_index)

    error = exc_info.value
    assert error.error_code == "REACTION_NOT_FOUND"
    assert "rxn99999" in error.message
    assert "not found" in error.message.lower()
    # Suggestions are part of the error, not in details
    assert hasattr(error, "suggestions") or "suggestions" in error.details


def test_get_reaction_name_transport_reaction(db_index):
    """Test transport reaction has is_transport=True."""
    request = GetReactionNameRequest(reaction_id="rxn05064")
    response = get_reaction_name(request, db_index)

    assert response["success"] is True
    assert response["name"] == "glucose transport"
    assert response["is_transport"] is True
    assert response["reversibility"] == "reversible"
    assert response["direction"] == "bidirectional"


def test_get_reaction_name_reversible_reaction(db_index):
    """Test reversible reaction parsing."""
    request = GetReactionNameRequest(reaction_id="rxn05064")
    response = get_reaction_name(request, db_index)

    assert response["reversibility"] == "reversible"
    assert response["direction"] == "bidirectional"


def test_get_reaction_name_with_multiple_pathways(db_index):
    """Test reaction with multiple pathways."""
    request = GetReactionNameRequest(reaction_id="rxn00216")
    response = get_reaction_name(request, db_index)

    assert "Glycolysis" in response["pathways"]
    assert "Central Metabolism" in response["pathways"]
    assert len(response["pathways"]) == 2


def test_get_reaction_name_with_complex_pathways(db_index):
    """Test reaction with pathways having database prefixes."""
    request = GetReactionNameRequest(reaction_id="rxn00200")
    response = get_reaction_name(request, db_index)

    # Should extract pathway names without database prefixes
    # The spec example shows removing descriptions in parens: "rn00020 (Citrate cycle)" -> "rn00020"
    # So we extract the actual pathway names after database prefixes
    assert "TCA Cycle" in response["pathways"]
    assert "rn00020" in response["pathways"]  # KEGG ID after prefix "KEGG:"


def test_get_reaction_name_no_ec_numbers(db_index):
    """Test reaction with no EC numbers."""
    request = GetReactionNameRequest(reaction_id="rxn05064")
    response = get_reaction_name(request, db_index)

    assert response["ec_numbers"] == []


def test_get_reaction_name_no_pathways(db_index):
    """Test reaction with no pathways."""
    request = GetReactionNameRequest(reaction_id="rxn05064")
    response = get_reaction_name(request, db_index)

    assert response["pathways"] == []


def test_get_reaction_name_no_aliases(db_index):
    """Test reaction with no aliases."""
    request = GetReactionNameRequest(reaction_id="rxn05064")
    response = get_reaction_name(request, db_index)

    assert response["aliases"] == {}


# =============================================================================
# Helper Function Tests
# =============================================================================


def test_parse_reversibility_forward():
    """Test parsing forward irreversible reaction."""
    reversibility, direction = parse_reversibility_and_direction(">")
    assert reversibility == "irreversible"
    assert direction == "forward"


def test_parse_reversibility_reverse():
    """Test parsing reverse irreversible reaction."""
    reversibility, direction = parse_reversibility_and_direction("<")
    assert reversibility == "irreversible_reverse"
    assert direction == "reverse"


def test_parse_reversibility_bidirectional():
    """Test parsing reversible reaction."""
    reversibility, direction = parse_reversibility_and_direction("=")
    assert reversibility == "reversible"
    assert direction == "bidirectional"


def test_parse_reversibility_unknown():
    """Test parsing unknown reversibility symbol defaults to reversible."""
    reversibility, direction = parse_reversibility_and_direction("?")
    assert reversibility == "reversible"
    assert direction == "bidirectional"


def test_parse_ec_numbers_single():
    """Test parsing single EC number."""
    ec_numbers = parse_ec_numbers("2.7.1.1")
    assert ec_numbers == ["2.7.1.1"]


def test_parse_ec_numbers_multiple_semicolon():
    """Test parsing multiple EC numbers separated by semicolon."""
    ec_numbers = parse_ec_numbers("2.7.1.1; 2.7.1.2")
    assert ec_numbers == ["2.7.1.1", "2.7.1.2"]


def test_parse_ec_numbers_multiple_pipe():
    """Test parsing multiple EC numbers separated by pipe."""
    ec_numbers = parse_ec_numbers("2.7.1.1|2.7.1.2")
    assert ec_numbers == ["2.7.1.1", "2.7.1.2"]


def test_parse_ec_numbers_empty():
    """Test parsing empty EC numbers."""
    assert parse_ec_numbers("") == []
    assert parse_ec_numbers(None) == []
    assert parse_ec_numbers(pd.NA) == []


def test_parse_pathways_simple():
    """Test parsing simple pathway."""
    pathways = parse_pathways("Glycolysis")
    assert pathways == ["Glycolysis"]


def test_parse_pathways_semicolon():
    """Test parsing pathways separated by semicolon."""
    pathways = parse_pathways("Glycolysis; Central Metabolism")
    assert pathways == ["Glycolysis", "Central Metabolism"]


def test_parse_pathways_with_database_prefix():
    """Test parsing pathways with database prefixes."""
    pathways = parse_pathways("MetaCyc: Glycolysis|KEGG: rn00010")
    assert "Glycolysis" in pathways
    assert "rn00010" in pathways


def test_parse_pathways_with_description():
    """Test parsing pathways with descriptive text in parentheses."""
    pathways = parse_pathways("MetaCyc: Glycolysis (Glucose Degradation)|KEGG: rn00010 (Glycolysis / Gluconeogenesis)")
    assert "Glycolysis" in pathways
    assert "rn00010" in pathways


def test_parse_pathways_empty():
    """Test parsing empty pathways."""
    assert parse_pathways("") == []
    assert parse_pathways(None) == []
    assert parse_pathways(pd.NA) == []


def test_format_equation_readable():
    """Test formatting equation for readability."""
    equation_with_ids = "(1) cpd00027[c0] + (1) cpd00002[c0] => (1) cpd00008[c0]"
    definition = "(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0]"

    readable = format_equation_readable(equation_with_ids, definition)

    assert "[0]" not in readable
    assert "[c0]" not in readable
    assert "D-Glucose" in readable
    assert "ATP" in readable


def test_format_equation_readable_no_definition():
    """Test formatting equation when definition is missing."""
    equation_with_ids = "(1) cpd00027[c0] + (1) cpd00002[c0] => (1) cpd00008[c0]"
    definition = None

    readable = format_equation_readable(equation_with_ids, definition)

    assert "[c0]" not in readable
    assert "cpd00027" in readable  # IDs still present


def test_format_equation_readable_empty():
    """Test formatting equation when both are empty."""
    readable = format_equation_readable("", "")
    assert readable == ""
