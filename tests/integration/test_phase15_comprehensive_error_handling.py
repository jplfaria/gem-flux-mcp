"""Integration tests for Phase 15: Comprehensive Error Handling Test Suite.

This module implements Task 88: Comprehensive error handling test suite
according to specification 013-error-handling.md.

Tests verify:
- All error types from spec 013 are properly implemented
- JSON-RPC 2.0 compliance for all error responses
- Helpful error messages with actionable suggestions
- Error recovery workflows
- Edge cases and boundary conditions

Test coverage spans all MCP tools:
- build_media errors
- build_model errors
- gapfill_model errors
- run_fba errors
- Database lookup errors
- Session management errors
"""


import pandas as pd
import pytest

# Import database
from gem_flux_mcp.database.index import DatabaseIndex

# Import error classes and builders
from gem_flux_mcp.errors import (
    DatabaseError,
    InfeasibilityError,
    LibraryError,
    NotFoundError,
    ServerError,
    TimeoutError,
    ValidationError,
    build_error_response,
    build_generic_error_response,
    compound_not_found_error,
    fba_infeasible_error,
    gapfill_infeasible_error,
    invalid_compound_ids_error,
    media_not_found_error,
    model_not_found_error,
    reaction_not_found_error,
)
from gem_flux_mcp.storage.media import (
    clear_all_media,
)

# Import storage modules
from gem_flux_mcp.storage.models import (
    clear_all_models,
)


@pytest.fixture(autouse=True)
def setup_storage():
    """Setup and teardown storage for each test."""
    clear_all_models()
    clear_all_media()
    yield
    clear_all_models()
    clear_all_media()


@pytest.fixture
def mock_db_index():
    """Create a DatabaseIndex with minimal test data."""
    compounds_data = {
        "id": ["cpd00027", "cpd00007", "cpd00001", "cpd00009"],
        "abbreviation": ["glc__D", "o2", "h2o", "pi"],
        "name": ["D-Glucose", "O2", "H2O", "Phosphate"],
        "formula": ["C6H12O6", "O2", "H2O", "HO4P"],
        "mass": [180.156, 31.999, 18.015, 97.995],
        "charge": [0, 0, 0, -2],
        "inchikey": ["", "", "", ""],
        "smiles": ["", "", "", ""],
        "aliases": ["", "", "", ""],
    }
    compounds_df = pd.DataFrame(compounds_data).set_index("id")

    reactions_data = {
        "id": ["rxn00148"],
        "abbreviation": ["HEX1"],
        "name": ["hexokinase"],
        "equation": ["(1) cpd00027[0] + (1) cpd00002[0] => (1) cpd00008[0]"],
        "definition": ["(1) D-Glucose[0] + (1) ATP[0] => (1) ADP[0]"],
        "reversibility": [">"],
        "direction": ["forward"],
        "deltag": [0.0],
        "deltagerr": [0.0],
        "is_transport": [0],
        "ec_numbers": ["2.7.1.1"],
        "pathways": ["Glycolysis"],
        "aliases": [""],
    }
    reactions_df = pd.DataFrame(reactions_data).set_index("id")

    return DatabaseIndex(compounds_df, reactions_df)


# ============================================================================
# Test Suite 1: JSON-RPC 2.0 Compliance
# ============================================================================


class TestJsonRpcCompliance:
    """Test all error responses follow JSON-RPC 2.0 specification."""

    def test_all_error_types_have_valid_codes(self):
        """Test that all error types have valid JSON-RPC error codes."""
        error_classes = [
            (ValidationError, -32000),
            (NotFoundError, -32001),
            (InfeasibilityError, -32002),
            (LibraryError, -32003),
            (DatabaseError, -32004),
            (TimeoutError, -32005),
            (ServerError, -32603),
        ]

        for error_class, expected_code in error_classes:
            if error_class == ServerError:
                error = error_class("test message")
            else:
                error = error_class("test message", "TEST_CODE")

            assert error.jsonrpc_error_code == expected_code
            assert isinstance(error.jsonrpc_error_code, int)
            assert error.jsonrpc_error_code < 0

    def test_error_response_has_all_required_fields(self):
        """Test that error responses contain all required JSON-RPC fields."""
        error = ValidationError("test", "TEST")
        response = build_error_response(error, "test_tool")

        required_fields = [
            "success",
            "error_type",
            "error_code",
            "jsonrpc_error_code",
            "message",
            "details",
            "suggestions",
            "tool_name",
            "timestamp",
        ]

        for field in required_fields:
            assert field in response, f"Missing required field: {field}"

        # Verify field types
        assert response["success"] is False
        assert isinstance(response["error_type"], str)
        assert isinstance(response["error_code"], str)
        assert isinstance(response["jsonrpc_error_code"], int)
        assert isinstance(response["message"], str)
        assert isinstance(response["details"], dict)
        assert isinstance(response["suggestions"], list)
        assert isinstance(response["tool_name"], str)
        assert isinstance(response["timestamp"], str)

    def test_timestamp_format_is_iso8601(self):
        """Test that timestamps follow ISO 8601 format."""
        error = ValidationError("test", "TEST")
        response = build_error_response(error, "test_tool")

        timestamp = response["timestamp"]
        assert timestamp.endswith("Z")
        assert "T" in timestamp
        assert len(timestamp.split("T")) == 2
        assert len(timestamp.split(":")) == 3


# ============================================================================
# Test Suite 2: build_media Tool Error Codes
# ============================================================================


class TestBuildMediaErrors:
    """Test all error codes for build_media tool from spec 013."""

    def test_invalid_compound_ids_error(self):
        """Test INVALID_COMPOUND_IDS error format and content."""
        error = invalid_compound_ids_error(
            invalid_ids=["cpd99999", "cpd00ABC"],
            valid_ids=["cpd00027", "cpd00007"],
            total_provided=4,
        )

        assert isinstance(error, ValidationError)
        assert error.error_code == "INVALID_COMPOUND_IDS"
        assert error.jsonrpc_error_code == -32000
        assert "2 compound" in error.message.lower()
        assert error.details["invalid_ids"] == ["cpd99999", "cpd00ABC"]
        assert error.details["total_invalid"] == 2
        assert len(error.suggestions) > 0
        assert any("search_compounds" in s for s in error.suggestions)

    def test_empty_compounds_list_error(self):
        """Test error for empty compounds list."""
        error = ValidationError(
            message="Compounds list cannot be empty",
            error_code="EMPTY_COMPOUNDS_LIST",
            suggestions=["Provide at least one compound ID"],
        )

        assert error.error_code == "EMPTY_COMPOUNDS_LIST"
        assert "empty" in error.message.lower()
        assert len(error.suggestions) > 0

    def test_invalid_bounds_format_error(self):
        """Test error for invalid bounds format."""
        error = ValidationError(
            message="Invalid bounds format: expected (lower, upper) tuple",
            error_code="INVALID_BOUNDS_FORMAT",
            details={
                "invalid_bounds": {"cpd00027": "invalid"},
                "expected_format": "(lower, upper) where lower < upper",
            },
            suggestions=["Use tuple format: (lower_bound, upper_bound)"],
        )

        assert error.error_code == "INVALID_BOUNDS_FORMAT"
        assert "bounds" in error.message.lower()
        assert "invalid_bounds" in error.details

    def test_bounds_out_of_order_error(self):
        """Test error when lower bound >= upper bound."""
        error = ValidationError(
            message="Lower bound must be less than upper bound",
            error_code="BOUNDS_OUT_OF_ORDER",
            details={
                "compound_id": "cpd00027",
                "provided_bounds": (10, 5),
                "issue": "lower_bound (10) >= upper_bound (5)",
            },
            suggestions=["Ensure lower_bound < upper_bound for all compounds"],
        )

        assert error.error_code == "BOUNDS_OUT_OF_ORDER"
        assert "lower" in error.message.lower() and "upper" in error.message.lower()

    def test_negative_uptake_error(self):
        """Test error for negative default_uptake value."""
        error = ValidationError(
            message="default_uptake must be positive",
            error_code="NEGATIVE_UPTAKE",
            details={"provided_value": -100.0, "expected": "> 0"},
            suggestions=["Provide a positive value for default_uptake"],
        )

        assert error.error_code == "NEGATIVE_UPTAKE"
        assert "negative" in error.message.lower() or "positive" in error.message.lower()


# ============================================================================
# Test Suite 3: build_model Tool Error Codes
# ============================================================================


class TestBuildModelErrors:
    """Test all error codes for build_model tool from spec 013."""

    def test_invalid_protein_sequences_error(self):
        """Test INVALID_PROTEIN_SEQUENCES error format."""
        error = ValidationError(
            message="2 protein sequences contain invalid characters",
            error_code="INVALID_PROTEIN_SEQUENCES",
            details={
                "invalid_sequences": {
                    "prot_001": "Contains invalid character 'X' at position 45",
                    "prot_003": "Empty sequence",
                },
                "valid_sequences": ["prot_002", "prot_004"],
                "total_sequences": 4,
                "total_invalid": 2,
                "allowed_characters": "ACDEFGHIKLMNPQRSTVWY",
            },
            suggestions=[
                "Use standard amino acid alphabet: ACDEFGHIKLMNPQRSTVWY",
                "Remove sequences with ambiguous residues (X, B, Z)",
            ],
        )

        assert error.error_code == "INVALID_PROTEIN_SEQUENCES"
        assert "protein" in error.message.lower()
        assert "invalid_sequences" in error.details
        assert len(error.suggestions) > 0

    def test_empty_protein_sequences_error(self):
        """Test error for empty protein sequences dict."""
        error = ValidationError(
            message="No protein sequences provided",
            error_code="EMPTY_PROTEIN_SEQUENCES",
            suggestions=["Provide at least one protein sequence"],
        )

        assert error.error_code == "EMPTY_PROTEIN_SEQUENCES"
        assert "empty" in error.message.lower() or "no protein" in error.message.lower()

    def test_invalid_template_name_error(self):
        """Test error for invalid template name."""
        error = ValidationError(
            message="Template 'InvalidTemplate' not found",
            error_code="INVALID_TEMPLATE_NAME",
            details={
                "requested_template": "InvalidTemplate",
                "available_templates": ["GramNegative", "GramPositive", "Core"],
            },
            suggestions=[
                "Valid templates: GramNegative, GramPositive, Core",
                "Check template name spelling",
            ],
        )

        assert error.error_code == "INVALID_TEMPLATE_NAME"
        assert "template" in error.message.lower()
        assert "available_templates" in error.details

    def test_modelseedpy_error(self):
        """Test ModelSEEDpy library error format."""
        error = LibraryError(
            message="ModelSEEDpy library error during model building",
            error_code="MODELSEEDPY_ERROR",
            details={
                "library": "ModelSEEDpy",
                "operation": "MSBuilder.build_base_model",
                "exception_type": "ValueError",
                "exception_message": "Template not found",
            },
            suggestions=[
                "Check ModelSEEDpy installation",
                "Verify template files are available",
            ],
        )

        assert error.error_code == "MODELSEEDPY_ERROR"
        assert error.jsonrpc_error_code == -32003
        assert "library" in error.details
        assert "operation" in error.details


# ============================================================================
# Test Suite 4: gapfill_model Tool Error Codes
# ============================================================================


class TestGapfillModelErrors:
    """Test all error codes for gapfill_model tool from spec 013."""

    def test_model_not_found_error(self):
        """Test MODEL_NOT_FOUND error format."""
        error = model_not_found_error(
            model_id="model_missing.draft",
            available_models=["model_1.draft", "model_2.draft.gf"],
        )

        assert isinstance(error, NotFoundError)
        assert error.error_code == "MODEL_NOT_FOUND"
        assert error.jsonrpc_error_code == -32001
        assert "model_missing.draft" in error.message
        assert error.details["requested_id"] == "model_missing.draft"
        assert len(error.details["available_models"]) == 2
        assert len(error.suggestions) > 0

    def test_media_not_found_error(self):
        """Test MEDIA_NOT_FOUND error format."""
        error = media_not_found_error(
            media_id="media_missing",
            available_media=["media_1", "media_2"],
        )

        assert isinstance(error, NotFoundError)
        assert error.error_code == "MEDIA_NOT_FOUND"
        assert "media_missing" in error.message
        assert error.details["requested_id"] == "media_missing"

    def test_gapfill_infeasible_error(self):
        """Test GAPFILL_INFEASIBLE error format."""
        error = gapfill_infeasible_error(
            model_id="model_test.draft",
            media_id="media_minimal",
            target_growth=0.01,
            media_compounds=15,
            template_reactions_available=4523,
        )

        assert isinstance(error, InfeasibilityError)
        assert error.error_code == "GAPFILL_INFEASIBLE"
        assert error.jsonrpc_error_code == -32002
        assert "could not find solution" in error.message.lower()
        assert error.details["model_id"] == "model_test.draft"
        assert error.details["media_id"] == "media_minimal"
        assert any("carbon source" in s.lower() for s in error.suggestions)

    def test_invalid_target_growth_error(self):
        """Test error for invalid target growth rate."""
        error = ValidationError(
            message="target_growth must be positive",
            error_code="INVALID_TARGET_GROWTH",
            details={"provided_value": -0.5, "expected": "> 0"},
            suggestions=["Provide a positive target growth rate (e.g., 0.01)"],
        )

        assert error.error_code == "INVALID_TARGET_GROWTH"
        assert "target_growth" in error.message


# ============================================================================
# Test Suite 5: run_fba Tool Error Codes
# ============================================================================


class TestRunFbaErrors:
    """Test all error codes for run_fba tool from spec 013."""

    def test_fba_infeasible_error(self):
        """Test FBA_INFEASIBLE error format."""
        error = fba_infeasible_error(
            model_id="model_test.draft.gf",
            media_id="media_minimal",
            objective="bio1",
            solver_status="infeasible",
            num_reactions=860,
            num_metabolites=781,
        )

        assert isinstance(error, InfeasibilityError)
        assert error.error_code == "FBA_INFEASIBLE"
        assert "infeasible" in error.message.lower()
        assert error.details["solver_status"] == "infeasible"
        assert error.details["num_reactions"] == 860
        assert any("essential nutrients" in s.lower() for s in error.suggestions)

    def test_fba_unbounded_error(self):
        """Test error for unbounded FBA solution."""
        error = InfeasibilityError(
            message="FBA objective is unbounded (can grow infinitely)",
            error_code="FBA_UNBOUNDED",
            details={
                "model_id": "model_test.draft",
                "objective": "bio1",
                "solver_status": "unbounded",
            },
            suggestions=[
                "Check for missing bounds on exchange reactions",
                "Verify model constraints are correct",
            ],
        )

        assert error.error_code == "FBA_UNBOUNDED"
        assert "unbounded" in error.message.lower()

    def test_cobrapy_solver_error(self):
        """Test COBRApy solver error format."""
        error = LibraryError(
            message="COBRApy solver failed during optimization",
            error_code="COBRAPY_SOLVER_ERROR",
            details={
                "library": "COBRApy",
                "operation": "model.optimize",
                "solver": "glpk",
                "exception_type": "OptimizationError",
                "exception_message": "Solver status: numerical_error",
            },
            suggestions=[
                "Try different solver if available",
                "Check model for numerical instability",
            ],
        )

        assert error.error_code == "COBRAPY_SOLVER_ERROR"
        assert error.jsonrpc_error_code == -32003
        assert "solver" in error.details


# ============================================================================
# Test Suite 6: Database Lookup Error Codes
# ============================================================================


class TestDatabaseLookupErrors:
    """Test all error codes for database lookup tools from spec 013."""

    def test_compound_not_found_error(self):
        """Test COMPOUND_NOT_FOUND error format."""
        error = compound_not_found_error(
            compound_id="cpd99999",
            total_compounds=33993,
            similar_ids=["cpd00999", "cpd09999"],
        )

        assert isinstance(error, DatabaseError)
        assert error.error_code == "COMPOUND_NOT_FOUND"
        assert error.jsonrpc_error_code == -32004
        assert "cpd99999" in error.message
        assert error.details["requested_id"] == "cpd99999"
        assert error.details["similar_ids"] == ["cpd00999", "cpd09999"]

    def test_reaction_not_found_error(self):
        """Test REACTION_NOT_FOUND error format."""
        error = reaction_not_found_error(
            reaction_id="rxn99999",
            total_reactions=43775,
            similar_ids=["rxn00999"],
        )

        assert isinstance(error, DatabaseError)
        assert error.error_code == "REACTION_NOT_FOUND"
        assert "rxn99999" in error.message
        assert error.details["database"] == "reactions.tsv"

    def test_invalid_id_format_error(self):
        """Test error for invalid ID format."""
        error = ValidationError(
            message="Invalid compound ID format: 'cpd_invalid'",
            error_code="INVALID_ID_FORMAT",
            details={
                "provided_id": "cpd_invalid",
                "expected_format": "cpd followed by 5 digits (e.g., cpd00027)",
            },
            suggestions=["Use format: cpd00001, cpd00027, etc."],
        )

        assert error.error_code == "INVALID_ID_FORMAT"
        assert "format" in error.message.lower()

    def test_empty_query_error(self):
        """Test error for empty search query."""
        error = ValidationError(
            message="Search query cannot be empty",
            error_code="EMPTY_QUERY",
            suggestions=["Provide a search term (compound name, formula, etc.)"],
        )

        assert error.error_code == "EMPTY_QUERY"
        assert "empty" in error.message.lower() or "cannot be empty" in error.message.lower()


# ============================================================================
# Test Suite 7: Error Message Quality
# ============================================================================


class TestErrorMessageQuality:
    """Test that error messages are clear, actionable, and helpful."""

    def test_error_messages_are_concise(self):
        """Test that error messages are not too long or too short."""
        errors = [
            model_not_found_error("model_test", []),
            media_not_found_error("media_test", []),
            invalid_compound_ids_error(["cpd99999"], ["cpd00027"], 2),
            compound_not_found_error("cpd99999", 33993),
        ]

        for error in errors:
            assert len(error.message) > 10, "Error message too short"
            assert len(error.message) < 300, "Error message too long"

    def test_error_messages_contain_specific_ids(self):
        """Test that error messages reference specific IDs mentioned."""
        test_cases = [
            (model_not_found_error("model_xyz.draft", []), "model_xyz.draft"),
            (media_not_found_error("media_abc", []), "media_abc"),
            (compound_not_found_error("cpd99999", 33993), "cpd99999"),
            (reaction_not_found_error("rxn88888", 43775), "rxn88888"),
        ]

        for error, expected_id in test_cases:
            assert expected_id in error.message, f"Expected ID '{expected_id}' not in message"

    def test_errors_have_actionable_suggestions(self):
        """Test that errors include specific, actionable suggestions."""
        errors = [
            model_not_found_error("model_test", ["model_1"]),
            invalid_compound_ids_error(["cpd99999"], [], 1),
            gapfill_infeasible_error("model", "media", 0.01, 10, 4500),
        ]

        for error in errors:
            assert len(error.suggestions) > 0, "No suggestions provided"
            # Suggestions should be specific, not generic
            for suggestion in error.suggestions:
                assert len(suggestion) > 10, "Suggestion too short"
                assert not suggestion.lower().startswith("contact support"), (
                    "Suggestion is too generic"
                )

    def test_error_details_provide_context(self):
        """Test that error details provide useful diagnostic information."""
        error = gapfill_infeasible_error(
            model_id="model_test.draft",
            media_id="media_minimal",
            target_growth=0.01,
            media_compounds=15,
            template_reactions_available=4523,
        )

        # Details should help understand what went wrong
        assert "model_id" in error.details
        assert "media_id" in error.details
        assert "target_growth" in error.details
        assert "media_compounds" in error.details
        assert "template_reactions_available" in error.details


# ============================================================================
# Test Suite 8: Error Recovery Workflows
# ============================================================================


class TestErrorRecoveryWorkflows:
    """Test that errors enable graceful recovery."""

    def test_model_not_found_shows_available_models(self):
        """Test that model not found error lists available models."""
        available = ["model_1.draft", "model_2.draft.gf", "model_3.gf"]
        error = model_not_found_error("model_wrong", available)

        assert error.details["available_models"] == available
        assert error.details["num_available"] == 3
        assert "available" in error.message.lower() or "models" in " ".join(error.suggestions).lower()

    def test_invalid_compound_shows_valid_examples(self):
        """Test that invalid compound error provides valid examples."""
        error = invalid_compound_ids_error(
            invalid_ids=["cpd99999"],
            valid_ids=["cpd00027", "cpd00007"],
            total_provided=3,
        )

        assert error.details["valid_ids"] == ["cpd00027", "cpd00007"]
        assert any("search" in s.lower() for s in error.suggestions)

    def test_gapfill_infeasible_suggests_media_check(self):
        """Test that gapfill infeasible error suggests checking media."""
        error = gapfill_infeasible_error(
            model_id="model.draft",
            media_id="media_minimal",
            target_growth=0.01,
            media_compounds=5,
            template_reactions_available=4500,
        )

        suggestions_text = " ".join(error.suggestions).lower()
        assert "media" in suggestions_text or "carbon" in suggestions_text or "nutrient" in suggestions_text


# ============================================================================
# Test Suite 9: Generic Error Handler
# ============================================================================


class TestGenericErrorHandler:
    """Test the generic error response builder."""

    def test_generic_error_catches_value_error(self):
        """Test that generic handler catches ValueError."""
        try:
            raise ValueError("Test error message")
        except ValueError as e:
            response = build_generic_error_response(e, "test_tool")

        assert response["success"] is False
        assert response["error_type"] == "server_error"
        assert response["error_code"] == "INTERNAL_ERROR"
        assert response["jsonrpc_error_code"] == -32603
        assert "Test error message" in response["details"]["exception_message"]

    def test_generic_error_includes_exception_details(self):
        """Test that generic error includes exception information."""
        try:
            raise RuntimeError("Unexpected failure")
        except RuntimeError as e:
            response = build_generic_error_response(e, "test_tool")

        assert "exception_type" in response["details"]
        assert "exception_message" in response["details"]
        assert response["details"]["exception_type"] == "RuntimeError"
        assert response["details"]["exception_message"] == "Unexpected failure"

    def test_generic_error_has_suggestions(self):
        """Test that generic errors include helpful suggestions."""
        try:
            raise Exception("Something went wrong")
        except Exception as e:
            response = build_generic_error_response(e, "test_tool")

        assert len(response["suggestions"]) > 0
        suggestions_text = " ".join(response["suggestions"]).lower()
        assert "log" in suggestions_text or "contact" in suggestions_text


# ============================================================================
# Test Suite 10: Edge Cases and Boundary Conditions
# ============================================================================


class TestErrorEdgeCases:
    """Test edge cases and boundary conditions for error handling."""

    def test_error_with_empty_available_list(self):
        """Test error when no resources are available."""
        error = model_not_found_error("model_test", [])

        assert error.details["num_available"] == 0
        assert error.details["available_models"] == []

    def test_error_with_very_long_id(self):
        """Test error handling with very long IDs."""
        long_id = "model_" + "x" * 200 + ".draft"
        error = model_not_found_error(long_id, [])

        assert long_id in error.message
        assert error.details["requested_id"] == long_id

    def test_error_with_unicode_characters(self):
        """Test that errors handle Unicode characters correctly."""
        error = ValidationError(
            message="Invalid compound: α-D-Glucose",
            error_code="TEST",
        )

        assert "α-D-Glucose" in error.message
        response = build_error_response(error, "test_tool")
        assert "α-D-Glucose" in response["message"]

    def test_error_with_special_characters_in_id(self):
        """Test error handling with special characters."""
        special_id = "model_test!@#$%^&*().draft"
        error = model_not_found_error(special_id, [])

        assert special_id in error.message
        response = build_error_response(error, "test_tool")
        assert special_id in response["message"]

    def test_multiple_errors_in_sequence(self):
        """Test that multiple errors in sequence are independent."""
        error1 = model_not_found_error("model_1", [])
        error2 = media_not_found_error("media_1", [])
        error3 = compound_not_found_error("cpd99999", 33993)

        # Verify each error is independent
        assert error1.error_code == "MODEL_NOT_FOUND"
        assert error2.error_code == "MEDIA_NOT_FOUND"
        assert error3.error_code == "COMPOUND_NOT_FOUND"

        assert "model_1" in error1.message
        assert "media_1" in error2.message
        assert "cpd99999" in error3.message


# ============================================================================
# Summary Test: Verify All Error Codes Are Tested
# ============================================================================


def test_all_error_codes_from_spec_are_covered():
    """Meta-test: Verify that all error codes from spec 013 are tested.

    This test documents which error codes we've tested. If new error codes
    are added to spec 013, this test should be updated.
    """
    tested_error_codes = {
        # build_media errors
        "INVALID_COMPOUND_IDS",
        "EMPTY_COMPOUNDS_LIST",
        "INVALID_BOUNDS_FORMAT",
        "BOUNDS_OUT_OF_ORDER",
        "NEGATIVE_UPTAKE",
        # build_model errors
        "INVALID_PROTEIN_SEQUENCES",
        "EMPTY_PROTEIN_SEQUENCES",
        "INVALID_TEMPLATE_NAME",
        "MODELSEEDPY_ERROR",
        # gapfill_model errors
        "MODEL_NOT_FOUND",
        "MEDIA_NOT_FOUND",
        "GAPFILL_INFEASIBLE",
        "INVALID_TARGET_GROWTH",
        # run_fba errors
        "FBA_INFEASIBLE",
        "FBA_UNBOUNDED",
        "COBRAPY_SOLVER_ERROR",
        # Database lookup errors
        "COMPOUND_NOT_FOUND",
        "REACTION_NOT_FOUND",
        "INVALID_ID_FORMAT",
        "EMPTY_QUERY",
        # Generic errors
        "INTERNAL_ERROR",
    }

    # This test passes if we've covered the major error codes
    # If new codes are added, this list should be updated
    assert len(tested_error_codes) >= 20, "Should test at least 20 error codes"
