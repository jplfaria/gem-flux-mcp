"""Error handling module for Gem-Flux MCP Server.

This module defines custom exceptions and JSON-RPC 2.0 compliant error responses
for all MCP tools. All errors follow the error handling specification (013-error-handling.md).

Error Types:
    - ValidationError: Input validation failed
    - NotFoundError: Resource not found (model_id, media_id, etc.)
    - InfeasibilityError: Model or gapfilling infeasible
    - LibraryError: ModelSEEDpy or COBRApy error
    - DatabaseError: ModelSEED database lookup failed
    - ServerError: Internal server error
    - TimeoutError: Operation exceeded time limit

JSON-RPC Error Codes:
    - -32000: Validation error
    - -32001: Not found error
    - -32002: Infeasibility error
    - -32003: Library error
    - -32004: Database error
    - -32005: Timeout error
    - -32603: Internal server error
"""

from datetime import datetime, timezone
from typing import Any, Optional


# ============================================================================
# Custom Exception Classes
# ============================================================================


class GemFluxError(Exception):
    """Base exception for all Gem-Flux MCP Server errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        jsonrpc_error_code: int,
        details: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ):
        """Initialize base error.

        Args:
            message: Human-readable error message
            error_code: Specific error code (e.g., "INVALID_COMPOUND_IDS")
            jsonrpc_error_code: JSON-RPC 2.0 error code (e.g., -32000)
            details: Structured error details (optional)
            suggestions: Recovery suggestions (optional)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.jsonrpc_error_code = jsonrpc_error_code
        self.details = details or {}
        self.suggestions = suggestions or []


class ValidationError(GemFluxError):
    """Input validation failed."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            jsonrpc_error_code=-32000,
            details=details,
            suggestions=suggestions,
        )


class NotFoundError(GemFluxError):
    """Resource not found (model_id, media_id, etc.)."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            jsonrpc_error_code=-32001,
            details=details,
            suggestions=suggestions,
        )


class InfeasibilityError(GemFluxError):
    """Model or gapfilling infeasible."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            jsonrpc_error_code=-32002,
            details=details,
            suggestions=suggestions,
        )


class LibraryError(GemFluxError):
    """ModelSEEDpy or COBRApy error."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            jsonrpc_error_code=-32003,
            details=details,
            suggestions=suggestions,
        )


class DatabaseError(GemFluxError):
    """ModelSEED database lookup failed."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            jsonrpc_error_code=-32004,
            details=details,
            suggestions=suggestions,
        )


class ServerError(GemFluxError):
    """Internal server error."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            jsonrpc_error_code=-32603,
            details=details,
            suggestions=suggestions,
        )


class TimeoutError(GemFluxError):
    """Operation exceeded time limit."""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            jsonrpc_error_code=-32005,
            details=details,
            suggestions=suggestions,
        )


# ============================================================================
# Error Response Builders
# ============================================================================


def build_error_response(
    error: GemFluxError,
    tool_name: str,
) -> dict[str, Any]:
    """Build JSON-RPC 2.0 compliant error response.

    Args:
        error: GemFluxError instance
        tool_name: Name of the tool that produced the error

    Returns:
        Error response dictionary with all required fields

    Example:
        >>> error = ValidationError(
        ...     message="Invalid compound IDs",
        ...     error_code="INVALID_COMPOUND_IDS",
        ...     details={"invalid_ids": ["cpd99999"]},
        ...     suggestions=["Use search_compounds tool"]
        ... )
        >>> response = build_error_response(error, "build_media")
        >>> response["success"]
        False
        >>> response["error_type"]
        'validation_error'
    """
    # Map exception class to error_type string
    error_type_map = {
        ValidationError: "validation_error",
        NotFoundError: "not_found_error",
        InfeasibilityError: "infeasibility_error",
        LibraryError: "library_error",
        DatabaseError: "database_error",
        ServerError: "server_error",
        TimeoutError: "timeout_error",
    }

    error_type = error_type_map.get(type(error), "server_error")

    return {
        "success": False,
        "error_type": error_type,
        "error_code": error.error_code,
        "jsonrpc_error_code": error.jsonrpc_error_code,
        "message": error.message,
        "details": error.details,
        "suggestions": error.suggestions,
        "tool_name": tool_name,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def build_generic_error_response(
    exception: Exception,
    tool_name: str,
    error_code: str = "INTERNAL_ERROR",
) -> dict[str, Any]:
    """Build error response from generic Python exception.

    Use this for unexpected exceptions that don't inherit from GemFluxError.

    Args:
        exception: Any Python exception
        tool_name: Name of the tool that produced the error
        error_code: Error code to use (default: INTERNAL_ERROR)

    Returns:
        Error response dictionary

    Example:
        >>> try:
        ...     raise ValueError("Something went wrong")
        ... except ValueError as e:
        ...     response = build_generic_error_response(e, "build_media")
        >>> response["error_type"]
        'server_error'
    """
    error = ServerError(
        message=f"Unexpected error: {str(exception)}",
        error_code=error_code,
        details={
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
        },
        suggestions=[
            "Check server logs for detailed error information",
            "Contact support if error persists",
        ],
    )

    return build_error_response(error, tool_name)


# ============================================================================
# Common Error Constructors
# ============================================================================


def model_not_found_error(
    model_id: str,
    available_models: list[str],
) -> NotFoundError:
    """Construct MODEL_NOT_FOUND error.

    Args:
        model_id: The requested model ID that was not found
        available_models: List of available model IDs in session

    Returns:
        NotFoundError instance
    """
    return NotFoundError(
        message=f"Model '{model_id}' not found in current session",
        error_code="MODEL_NOT_FOUND",
        details={
            "requested_id": model_id,
            "available_models": available_models,
            "num_available": len(available_models),
        },
        suggestions=[
            "Use build_model tool to create a new model",
            "Check model_id spelling",
            "Available models listed in details.available_models",
        ],
    )


def media_not_found_error(
    media_id: str,
    available_media: list[str],
) -> NotFoundError:
    """Construct MEDIA_NOT_FOUND error.

    Args:
        media_id: The requested media ID that was not found
        available_media: List of available media IDs in session

    Returns:
        NotFoundError instance
    """
    return NotFoundError(
        message=f"Media '{media_id}' not found in current session",
        error_code="MEDIA_NOT_FOUND",
        details={
            "requested_id": media_id,
            "available_media": available_media,
            "num_available": len(available_media),
        },
        suggestions=[
            "Use build_media tool to create new media",
            "Check media_id spelling",
            "Available media listed in details.available_media",
        ],
    )


def invalid_compound_ids_error(
    invalid_ids: list[str],
    valid_ids: list[str],
    total_provided: int,
) -> ValidationError:
    """Construct INVALID_COMPOUND_IDS error.

    Args:
        invalid_ids: List of invalid compound IDs
        valid_ids: List of valid compound IDs
        total_provided: Total number of compound IDs provided

    Returns:
        ValidationError instance
    """
    num_invalid = len(invalid_ids)
    return ValidationError(
        message=f"{num_invalid} compound ID(s) not found in ModelSEED database",
        error_code="INVALID_COMPOUND_IDS",
        details={
            "invalid_ids": invalid_ids,
            "valid_ids": valid_ids,
            "total_provided": total_provided,
            "total_invalid": num_invalid,
        },
        suggestions=[
            "Use search_compounds tool to find correct compound IDs",
            "Common compounds: cpd00027 (glucose), cpd00007 (O2), cpd00001 (H2O)",
            "Check for typos in compound IDs",
        ],
    )


def compound_not_found_error(
    compound_id: str,
    total_compounds: int,
    similar_ids: Optional[list[str]] = None,
) -> DatabaseError:
    """Construct COMPOUND_NOT_FOUND error.

    Args:
        compound_id: The requested compound ID
        total_compounds: Total number of compounds in database
        similar_ids: List of similar compound IDs (optional)

    Returns:
        DatabaseError instance
    """
    return DatabaseError(
        message=f"Compound '{compound_id}' not found in ModelSEED database",
        error_code="COMPOUND_NOT_FOUND",
        details={
            "requested_id": compound_id,
            "database": "compounds.tsv",
            "total_compounds": total_compounds,
            "similar_ids": similar_ids or [],
        },
        suggestions=[
            "Use search_compounds to find correct ID",
            "Check for typos in compound ID",
            "Verify compound exists in ModelSEED database",
            "Similar IDs listed in details.similar_ids" if similar_ids else "",
        ],
    )


def reaction_not_found_error(
    reaction_id: str,
    total_reactions: int,
    similar_ids: Optional[list[str]] = None,
) -> DatabaseError:
    """Construct REACTION_NOT_FOUND error.

    Args:
        reaction_id: The requested reaction ID
        total_reactions: Total number of reactions in database
        similar_ids: List of similar reaction IDs (optional)

    Returns:
        DatabaseError instance
    """
    return DatabaseError(
        message=f"Reaction '{reaction_id}' not found in ModelSEED database",
        error_code="REACTION_NOT_FOUND",
        details={
            "requested_id": reaction_id,
            "database": "reactions.tsv",
            "total_reactions": total_reactions,
            "similar_ids": similar_ids or [],
        },
        suggestions=[
            "Use search_reactions to find correct ID",
            "Check for typos in reaction ID",
            "Verify reaction exists in ModelSEED database",
            "Similar IDs listed in details.similar_ids" if similar_ids else "",
        ],
    )


def gapfill_infeasible_error(
    model_id: str,
    media_id: str,
    target_growth: float,
    media_compounds: int,
    template_reactions_available: int,
) -> InfeasibilityError:
    """Construct GAPFILL_INFEASIBLE error.

    Args:
        model_id: The model ID that failed gapfilling
        media_id: The media ID used for gapfilling
        target_growth: Target growth rate
        media_compounds: Number of compounds in media
        template_reactions_available: Number of reactions available from template

    Returns:
        InfeasibilityError instance
    """
    return InfeasibilityError(
        message="Gapfilling could not find solution to enable growth in specified media",
        error_code="GAPFILL_INFEASIBLE",
        details={
            "model_id": model_id,
            "media_id": media_id,
            "target_growth": target_growth,
            "media_compounds": media_compounds,
            "template_reactions_available": template_reactions_available,
        },
        suggestions=[
            "Verify media contains carbon source (glucose, acetate, etc.)",
            "Check media composition with get_compound_name for each compound",
            "Try complete media (LB, M9+aa) instead of minimal media",
            "Verify model has biomass reaction",
        ],
    )


def fba_infeasible_error(
    model_id: str,
    media_id: str,
    objective: str,
    solver_status: str,
    num_reactions: int,
    num_metabolites: int,
) -> InfeasibilityError:
    """Construct FBA_INFEASIBLE error.

    Args:
        model_id: The model ID that failed FBA
        media_id: The media ID used for FBA
        objective: The objective function
        solver_status: Status from COBRApy solver
        num_reactions: Number of reactions in model
        num_metabolites: Number of metabolites in model

    Returns:
        InfeasibilityError instance
    """
    return InfeasibilityError(
        message="FBA optimization failed - model infeasible in specified media",
        error_code="FBA_INFEASIBLE",
        details={
            "model_id": model_id,
            "media_id": media_id,
            "objective": objective,
            "solver_status": solver_status,
            "num_reactions": num_reactions,
            "num_metabolites": num_metabolites,
        },
        suggestions=[
            "Verify media contains essential nutrients (C, N, P, S sources)",
            "Check exchange reaction bounds are not too restrictive",
            "Try gapfilling model first if not already gapfilled",
            "Use get_compound_name to verify media composition",
        ],
    )
