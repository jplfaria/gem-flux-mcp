"""Unit tests for error handling module.

Tests all custom exceptions, error response builders, and common error constructors.
Ensures JSON-RPC 2.0 compliance and proper error formatting.
"""

from datetime import datetime

from gem_flux_mcp.errors import (
    DatabaseError,
    # Exception classes
    GemFluxError,
    InfeasibilityError,
    LibraryError,
    NotFoundError,
    ServerError,
    TimeoutError,
    ValidationError,
    # Error response builders
    build_error_response,
    build_generic_error_response,
    compound_not_found_error,
    fba_infeasible_error,
    gapfill_infeasible_error,
    invalid_compound_ids_error,
    media_not_found_error,
    # Common error constructors
    model_not_found_error,
    reaction_not_found_error,
)

# ============================================================================
# Test Custom Exception Classes
# ============================================================================


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_basic(self):
        """Test basic ValidationError creation."""
        error = ValidationError(
            message="Invalid input",
            error_code="INVALID_INPUT",
        )

        assert str(error) == "Invalid input"
        assert error.message == "Invalid input"
        assert error.error_code == "INVALID_INPUT"
        assert error.jsonrpc_error_code == -32000
        assert error.details == {}
        assert error.suggestions == []

    def test_validation_error_with_details(self):
        """Test ValidationError with details and suggestions."""
        error = ValidationError(
            message="Invalid compound IDs",
            error_code="INVALID_COMPOUND_IDS",
            details={"invalid_ids": ["cpd99999"]},
            suggestions=["Use search_compounds tool"],
        )

        assert error.message == "Invalid compound IDs"
        assert error.details == {"invalid_ids": ["cpd99999"]}
        assert error.suggestions == ["Use search_compounds tool"]


class TestNotFoundError:
    """Test NotFoundError exception."""

    def test_not_found_error_basic(self):
        """Test basic NotFoundError creation."""
        error = NotFoundError(
            message="Model not found",
            error_code="MODEL_NOT_FOUND",
        )

        assert error.message == "Model not found"
        assert error.error_code == "MODEL_NOT_FOUND"
        assert error.jsonrpc_error_code == -32001

    def test_not_found_error_with_available(self):
        """Test NotFoundError with available resources."""
        error = NotFoundError(
            message="Model 'xyz' not found",
            error_code="MODEL_NOT_FOUND",
            details={
                "requested_id": "xyz",
                "available_models": ["abc", "def"],
            },
        )

        assert error.details["requested_id"] == "xyz"
        assert len(error.details["available_models"]) == 2


class TestInfeasibilityError:
    """Test InfeasibilityError exception."""

    def test_infeasibility_error_basic(self):
        """Test basic InfeasibilityError creation."""
        error = InfeasibilityError(
            message="Gapfilling infeasible",
            error_code="GAPFILL_INFEASIBLE",
        )

        assert error.message == "Gapfilling infeasible"
        assert error.error_code == "GAPFILL_INFEASIBLE"
        assert error.jsonrpc_error_code == -32002


class TestLibraryError:
    """Test LibraryError exception."""

    def test_library_error_basic(self):
        """Test basic LibraryError creation."""
        error = LibraryError(
            message="ModelSEEDpy error",
            error_code="MODELSEEDPY_ERROR",
        )

        assert error.message == "ModelSEEDpy error"
        assert error.error_code == "MODELSEEDPY_ERROR"
        assert error.jsonrpc_error_code == -32003

    def test_library_error_with_exception_details(self):
        """Test LibraryError with exception details."""
        error = LibraryError(
            message="ModelSEEDpy library error",
            error_code="MODELSEEDPY_ERROR",
            details={
                "library": "ModelSEEDpy",
                "operation": "MSBuilder.build_base_model",
                "exception_type": "ValueError",
                "exception_message": "Template not found",
            },
        )

        assert error.details["library"] == "ModelSEEDpy"
        assert error.details["operation"] == "MSBuilder.build_base_model"


class TestDatabaseError:
    """Test DatabaseError exception."""

    def test_database_error_basic(self):
        """Test basic DatabaseError creation."""
        error = DatabaseError(
            message="Compound not found",
            error_code="COMPOUND_NOT_FOUND",
        )

        assert error.message == "Compound not found"
        assert error.error_code == "COMPOUND_NOT_FOUND"
        assert error.jsonrpc_error_code == -32004


class TestServerError:
    """Test ServerError exception."""

    def test_server_error_basic(self):
        """Test basic ServerError creation."""
        error = ServerError(
            message="Internal server error",
        )

        assert error.message == "Internal server error"
        assert error.error_code == "INTERNAL_ERROR"
        assert error.jsonrpc_error_code == -32603

    def test_server_error_custom_code(self):
        """Test ServerError with custom error code."""
        error = ServerError(
            message="Database connection failed",
            error_code="DATABASE_CONNECTION_ERROR",
        )

        assert error.error_code == "DATABASE_CONNECTION_ERROR"


class TestTimeoutError:
    """Test TimeoutError exception."""

    def test_timeout_error_basic(self):
        """Test basic TimeoutError creation."""
        error = TimeoutError(
            message="Operation timed out",
            error_code="OPERATION_TIMEOUT",
        )

        assert error.message == "Operation timed out"
        assert error.error_code == "OPERATION_TIMEOUT"
        assert error.jsonrpc_error_code == -32005


# ============================================================================
# Test Error Response Builders
# ============================================================================


class TestBuildErrorResponse:
    """Test build_error_response function."""

    def test_build_error_response_validation(self):
        """Test building error response for ValidationError."""
        error = ValidationError(
            message="Invalid compound IDs",
            error_code="INVALID_COMPOUND_IDS",
            details={"invalid_ids": ["cpd99999"]},
            suggestions=["Use search_compounds tool"],
        )

        response = build_error_response(error, "build_media")

        assert response["success"] is False
        assert response["error_type"] == "validation_error"
        assert response["error_code"] == "INVALID_COMPOUND_IDS"
        assert response["jsonrpc_error_code"] == -32000
        assert response["message"] == "Invalid compound IDs"
        assert response["details"] == {"invalid_ids": ["cpd99999"]}
        assert response["suggestions"] == ["Use search_compounds tool"]
        assert response["tool_name"] == "build_media"
        assert "timestamp" in response

    def test_build_error_response_not_found(self):
        """Test building error response for NotFoundError."""
        error = NotFoundError(
            message="Model not found",
            error_code="MODEL_NOT_FOUND",
        )

        response = build_error_response(error, "run_fba")

        assert response["error_type"] == "not_found_error"
        assert response["jsonrpc_error_code"] == -32001

    def test_build_error_response_infeasibility(self):
        """Test building error response for InfeasibilityError."""
        error = InfeasibilityError(
            message="Gapfilling infeasible",
            error_code="GAPFILL_INFEASIBLE",
        )

        response = build_error_response(error, "gapfill_model")

        assert response["error_type"] == "infeasibility_error"
        assert response["jsonrpc_error_code"] == -32002

    def test_build_error_response_library(self):
        """Test building error response for LibraryError."""
        error = LibraryError(
            message="ModelSEEDpy error",
            error_code="MODELSEEDPY_ERROR",
        )

        response = build_error_response(error, "build_model")

        assert response["error_type"] == "library_error"
        assert response["jsonrpc_error_code"] == -32003

    def test_build_error_response_database(self):
        """Test building error response for DatabaseError."""
        error = DatabaseError(
            message="Compound not found",
            error_code="COMPOUND_NOT_FOUND",
        )

        response = build_error_response(error, "get_compound_name")

        assert response["error_type"] == "database_error"
        assert response["jsonrpc_error_code"] == -32004

    def test_build_error_response_server(self):
        """Test building error response for ServerError."""
        error = ServerError(
            message="Internal error",
            error_code="INTERNAL_ERROR",
        )

        response = build_error_response(error, "build_media")

        assert response["error_type"] == "server_error"
        assert response["jsonrpc_error_code"] == -32603

    def test_build_error_response_timeout(self):
        """Test building error response for TimeoutError."""
        error = TimeoutError(
            message="Operation timed out",
            error_code="OPERATION_TIMEOUT",
        )

        response = build_error_response(error, "gapfill_model")

        assert response["error_type"] == "timeout_error"
        assert response["jsonrpc_error_code"] == -32005

    def test_build_error_response_timestamp_format(self):
        """Test timestamp format is ISO 8601 with Z suffix."""
        error = ValidationError(
            message="Test error",
            error_code="TEST_ERROR",
        )

        response = build_error_response(error, "test_tool")

        # Check timestamp format: YYYY-MM-DDTHH:MM:SSZ
        timestamp = response["timestamp"]
        assert timestamp.endswith("Z")
        assert "T" in timestamp

        # Verify it's a valid ISO 8601 timestamp
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


class TestBuildGenericErrorResponse:
    """Test build_generic_error_response function."""

    def test_build_generic_error_response_value_error(self):
        """Test building error response from ValueError."""
        try:
            raise ValueError("Something went wrong")
        except ValueError as e:
            response = build_generic_error_response(e, "build_media")

        assert response["success"] is False
        assert response["error_type"] == "server_error"
        assert response["error_code"] == "INTERNAL_ERROR"
        assert response["jsonrpc_error_code"] == -32603
        assert "Unexpected error" in response["message"]
        assert response["details"]["exception_type"] == "ValueError"
        assert response["details"]["exception_message"] == "Something went wrong"
        assert response["tool_name"] == "build_media"

    def test_build_generic_error_response_custom_code(self):
        """Test building error response with custom error code."""
        try:
            raise KeyError("missing_key")
        except KeyError as e:
            response = build_generic_error_response(e, "test_tool", error_code="CUSTOM_ERROR")

        assert response["error_code"] == "CUSTOM_ERROR"
        assert response["details"]["exception_type"] == "KeyError"

    def test_build_generic_error_response_has_suggestions(self):
        """Test that generic error response includes helpful suggestions."""
        try:
            raise RuntimeError("Unexpected failure")
        except RuntimeError as e:
            response = build_generic_error_response(e, "test_tool")

        assert len(response["suggestions"]) > 0
        assert any("server logs" in s.lower() for s in response["suggestions"])


# ============================================================================
# Test Common Error Constructors
# ============================================================================


class TestModelNotFoundError:
    """Test model_not_found_error constructor."""

    def test_model_not_found_error_basic(self):
        """Test basic model not found error."""
        error = model_not_found_error(
            model_id="model_xyz",
            available_models=["model_abc", "model_def"],
        )

        assert isinstance(error, NotFoundError)
        assert error.error_code == "MODEL_NOT_FOUND"
        assert "model_xyz" in error.message
        assert error.details["requested_id"] == "model_xyz"
        assert error.details["available_models"] == ["model_abc", "model_def"]
        assert error.details["num_available"] == 2
        assert len(error.suggestions) > 0

    def test_model_not_found_error_no_available_models(self):
        """Test model not found with no available models."""
        error = model_not_found_error(
            model_id="model_xyz",
            available_models=[],
        )

        assert error.details["num_available"] == 0
        assert error.details["available_models"] == []


class TestMediaNotFoundError:
    """Test media_not_found_error constructor."""

    def test_media_not_found_error_basic(self):
        """Test basic media not found error."""
        error = media_not_found_error(
            media_id="media_xyz",
            available_media=["media_abc", "media_def"],
        )

        assert isinstance(error, NotFoundError)
        assert error.error_code == "MEDIA_NOT_FOUND"
        assert "media_xyz" in error.message
        assert error.details["requested_id"] == "media_xyz"
        assert error.details["available_media"] == ["media_abc", "media_def"]
        assert error.details["num_available"] == 2


class TestInvalidCompoundIdsError:
    """Test invalid_compound_ids_error constructor."""

    def test_invalid_compound_ids_error_basic(self):
        """Test basic invalid compound IDs error."""
        error = invalid_compound_ids_error(
            invalid_ids=["cpd99999", "cpd00ABC"],
            valid_ids=["cpd00027", "cpd00007"],
            total_provided=4,
        )

        assert isinstance(error, ValidationError)
        assert error.error_code == "INVALID_COMPOUND_IDS"
        assert "2 compound" in error.message
        assert error.details["invalid_ids"] == ["cpd99999", "cpd00ABC"]
        assert error.details["valid_ids"] == ["cpd00027", "cpd00007"]
        assert error.details["total_provided"] == 4
        assert error.details["total_invalid"] == 2
        assert any("search_compounds" in s for s in error.suggestions)

    def test_invalid_compound_ids_error_single_invalid(self):
        """Test invalid compound IDs error with single invalid ID."""
        error = invalid_compound_ids_error(
            invalid_ids=["cpd99999"],
            valid_ids=["cpd00027"],
            total_provided=2,
        )

        assert "1 compound" in error.message
        assert error.details["total_invalid"] == 1


class TestCompoundNotFoundError:
    """Test compound_not_found_error constructor."""

    def test_compound_not_found_error_basic(self):
        """Test basic compound not found error."""
        error = compound_not_found_error(
            compound_id="cpd99999",
            total_compounds=33993,
        )

        assert isinstance(error, DatabaseError)
        assert error.error_code == "COMPOUND_NOT_FOUND"
        assert "cpd99999" in error.message
        assert error.details["requested_id"] == "cpd99999"
        assert error.details["database"] == "compounds.tsv"
        assert error.details["total_compounds"] == 33993
        assert error.details["similar_ids"] == []

    def test_compound_not_found_error_with_similar(self):
        """Test compound not found error with similar IDs."""
        error = compound_not_found_error(
            compound_id="cpd99999",
            total_compounds=33993,
            similar_ids=["cpd00999", "cpd09999"],
        )

        assert error.details["similar_ids"] == ["cpd00999", "cpd09999"]
        assert any("similar" in s.lower() for s in error.suggestions)


class TestReactionNotFoundError:
    """Test reaction_not_found_error constructor."""

    def test_reaction_not_found_error_basic(self):
        """Test basic reaction not found error."""
        error = reaction_not_found_error(
            reaction_id="rxn99999",
            total_reactions=43775,
        )

        assert isinstance(error, DatabaseError)
        assert error.error_code == "REACTION_NOT_FOUND"
        assert "rxn99999" in error.message
        assert error.details["requested_id"] == "rxn99999"
        assert error.details["database"] == "reactions.tsv"
        assert error.details["total_reactions"] == 43775

    def test_reaction_not_found_error_with_similar(self):
        """Test reaction not found error with similar IDs."""
        error = reaction_not_found_error(
            reaction_id="rxn99999",
            total_reactions=43775,
            similar_ids=["rxn00999", "rxn09999"],
        )

        assert error.details["similar_ids"] == ["rxn00999", "rxn09999"]


class TestGapfillInfeasibleError:
    """Test gapfill_infeasible_error constructor."""

    def test_gapfill_infeasible_error_basic(self):
        """Test basic gapfill infeasible error."""
        error = gapfill_infeasible_error(
            model_id="model_abc.draft",
            media_id="media_xyz",
            target_growth=0.01,
            media_compounds=15,
            template_reactions_available=4523,
        )

        assert isinstance(error, InfeasibilityError)
        assert error.error_code == "GAPFILL_INFEASIBLE"
        assert "could not find solution" in error.message.lower()
        assert error.details["model_id"] == "model_abc.draft"
        assert error.details["media_id"] == "media_xyz"
        assert error.details["target_growth"] == 0.01
        assert error.details["media_compounds"] == 15
        assert error.details["template_reactions_available"] == 4523
        assert any("carbon source" in s.lower() for s in error.suggestions)


class TestFbaInfeasibleError:
    """Test fba_infeasible_error constructor."""

    def test_fba_infeasible_error_basic(self):
        """Test basic FBA infeasible error."""
        error = fba_infeasible_error(
            model_id="model_abc.draft.gf",
            media_id="media_xyz",
            objective="bio1",
            solver_status="infeasible",
            num_reactions=860,
            num_metabolites=781,
        )

        assert isinstance(error, InfeasibilityError)
        assert error.error_code == "FBA_INFEASIBLE"
        assert "infeasible" in error.message.lower()
        assert error.details["model_id"] == "model_abc.draft.gf"
        assert error.details["media_id"] == "media_xyz"
        assert error.details["objective"] == "bio1"
        assert error.details["solver_status"] == "infeasible"
        assert error.details["num_reactions"] == 860
        assert error.details["num_metabolites"] == 781
        assert any("essential nutrients" in s.lower() for s in error.suggestions)


# ============================================================================
# Test Error Inheritance
# ============================================================================


class TestErrorInheritance:
    """Test exception class inheritance hierarchy."""

    def test_all_errors_inherit_from_gemflux_error(self):
        """Test that all custom errors inherit from GemFluxError."""
        errors = [
            ValidationError("test", "TEST"),
            NotFoundError("test", "TEST"),
            InfeasibilityError("test", "TEST"),
            LibraryError("test", "TEST"),
            DatabaseError("test", "TEST"),
            ServerError("test"),
            TimeoutError("test", "TEST"),
        ]

        for error in errors:
            assert isinstance(error, GemFluxError)
            assert isinstance(error, Exception)

    def test_gemflux_error_is_exception(self):
        """Test that GemFluxError is a Python Exception."""
        error = GemFluxError(
            message="test",
            error_code="TEST",
            jsonrpc_error_code=-32000,
        )

        assert isinstance(error, Exception)


# ============================================================================
# Test JSON-RPC 2.0 Compliance
# ============================================================================


class TestJsonRpcCompliance:
    """Test JSON-RPC 2.0 compliance of error responses."""

    def test_error_codes_in_valid_range(self):
        """Test that all error codes are in valid JSON-RPC range."""
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
            error = (
                error_class("test", "TEST") if error_class != ServerError else error_class("test")
            )
            assert error.jsonrpc_error_code == expected_code
            # All codes should be negative integers in range -32768 to -32000 or standard codes
            assert isinstance(error.jsonrpc_error_code, int)
            assert error.jsonrpc_error_code < 0

    def test_error_response_has_required_fields(self):
        """Test that error response has all required fields."""
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

    def test_error_response_success_always_false(self):
        """Test that success field is always False in error responses."""
        errors = [
            ValidationError("test", "TEST"),
            NotFoundError("test", "TEST"),
            InfeasibilityError("test", "TEST"),
        ]

        for error in errors:
            response = build_error_response(error, "test_tool")
            assert response["success"] is False


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_error_with_empty_details(self):
        """Test error with empty details dict."""
        error = ValidationError("test", "TEST", details={})
        response = build_error_response(error, "test_tool")

        assert response["details"] == {}

    def test_error_with_empty_suggestions(self):
        """Test error with empty suggestions list."""
        error = ValidationError("test", "TEST", suggestions=[])
        response = build_error_response(error, "test_tool")

        assert response["suggestions"] == []

    def test_error_with_none_details(self):
        """Test error initialized with None details."""
        error = ValidationError("test", "TEST", details=None)

        assert error.details == {}

    def test_error_with_none_suggestions(self):
        """Test error initialized with None suggestions."""
        error = ValidationError("test", "TEST", suggestions=None)

        assert error.suggestions == []

    def test_model_not_found_with_long_model_list(self):
        """Test model not found error with many available models."""
        available = [f"model_{i}" for i in range(100)]
        error = model_not_found_error("model_xyz", available)

        assert error.details["num_available"] == 100
        assert len(error.details["available_models"]) == 100

    def test_unicode_in_error_message(self):
        """Test that errors handle Unicode characters correctly."""
        error = ValidationError(
            message="Invalid compound: α-D-Glucose",
            error_code="TEST",
        )

        assert "α-D-Glucose" in error.message
        response = build_error_response(error, "test_tool")
        assert "α-D-Glucose" in response["message"]

    def test_very_long_error_message(self):
        """Test errors with very long messages."""
        long_message = "Error: " + "x" * 1000
        error = ValidationError(long_message, "TEST")

        assert len(error.message) > 1000
        response = build_error_response(error, "test_tool")
        assert len(response["message"]) > 1000
