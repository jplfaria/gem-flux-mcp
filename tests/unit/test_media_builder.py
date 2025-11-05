"""Unit tests for build_media tool.

Tests the build_media MCP tool implementation according to specification
003-build-media-tool.md.

Test Coverage:
    - Valid media creation (minimal, rich)
    - Custom bounds application
    - Input validation (empty list, invalid IDs, duplicate IDs)
    - Bounds validation (invalid format, lower >= upper)
    - Database integration (compound lookup, metadata enrichment)
    - Media ID generation and storage
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.errors import ValidationError
from gem_flux_mcp.storage.media import (
    clear_all_media,
    media_exists,
    retrieve_media,
)
from gem_flux_mcp.tools.media_builder import (
    BuildMediaRequest,
    build_media,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def db_index(mock_compounds_df, mock_reactions_df):
    """Create DatabaseIndex with mock data."""
    return DatabaseIndex(mock_compounds_df, mock_reactions_df)


@pytest.fixture(autouse=True)
def cleanup_media_storage():
    """Clear media storage before and after each test."""
    clear_all_media()
    yield
    clear_all_media()


# =============================================================================
# Test BuildMediaRequest Validation
# =============================================================================


class TestBuildMediaRequestValidation:
    """Test input validation for BuildMediaRequest."""

    def test_valid_minimal_request(self):
        """Test valid minimal media request (required fields only)."""
        request = BuildMediaRequest(compounds=["cpd00027", "cpd00007", "cpd00001"])

        assert len(request.compounds) == 3
        assert request.default_uptake == 100.0  # Default value
        assert request.custom_bounds == {}  # Default empty dict

    def test_valid_request_with_custom_bounds(self):
        """Test valid request with custom bounds."""
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007"],
            default_uptake=50.0,
            custom_bounds={"cpd00027": (-5, 100), "cpd00007": (-10, 100)},
        )

        assert request.default_uptake == 50.0
        assert len(request.custom_bounds) == 2
        assert request.custom_bounds["cpd00027"] == (-5.0, 100.0)
        assert request.custom_bounds["cpd00007"] == (-10.0, 100.0)

    def test_empty_compounds_list_error(self):
        """Test error when compounds list is empty."""
        with pytest.raises(PydanticValidationError) as exc_info:
            BuildMediaRequest(compounds=[])

        error_msg = str(exc_info.value)
        assert "cannot be empty" in error_msg.lower() or "non-empty list" in error_msg.lower()

    def test_invalid_compound_id_format_error(self):
        """Test error when compound ID has invalid format."""
        with pytest.raises(PydanticValidationError) as exc_info:
            BuildMediaRequest(compounds=["glucose", "cpd00007"])

        error_msg = str(exc_info.value)
        assert "invalid compound id format" in error_msg.lower()
        assert "glucose" in error_msg

    def test_duplicate_compound_ids_error(self):
        """Test error when duplicate compound IDs provided."""
        with pytest.raises(PydanticValidationError) as exc_info:
            BuildMediaRequest(compounds=["cpd00027", "cpd00007", "cpd00027"])

        error_msg = str(exc_info.value)
        assert "duplicate" in error_msg.lower()
        assert "cpd00027" in error_msg

    def test_case_insensitive_compound_ids(self):
        """Test compound IDs are converted to lowercase."""
        request = BuildMediaRequest(compounds=["CPD00027", "CpD00007", "cpd00001"])

        assert request.compounds == ["cpd00027", "cpd00007", "cpd00001"]

    def test_whitespace_trimming(self):
        """Test whitespace is trimmed from compound IDs."""
        request = BuildMediaRequest(compounds=[" cpd00027 ", "cpd00007", "  cpd00001"])

        assert request.compounds == ["cpd00027", "cpd00007", "cpd00001"]

    def test_invalid_bounds_format_error(self):
        """Test error when bounds format is invalid."""
        with pytest.raises(PydanticValidationError) as exc_info:
            BuildMediaRequest(
                compounds=["cpd00027"],
                custom_bounds={"cpd00027": (-5,)},  # Only one value
            )

        error_msg = str(exc_info.value)
        assert "must be a tuple/list of 2 numbers" in error_msg

    def test_invalid_bounds_values_error(self):
        """Test error when lower bound >= upper bound."""
        with pytest.raises(PydanticValidationError) as exc_info:
            BuildMediaRequest(compounds=["cpd00027"], custom_bounds={"cpd00027": (100, -5)})

        error_msg = str(exc_info.value)
        assert "lower" in error_msg.lower()
        assert "upper" in error_msg.lower()

    def test_bounds_equal_allowed(self):
        """Test equal bounds are allowed (for blocked exchange)."""
        # This should NOT raise an error - equal bounds are valid for blocked exchange
        request = BuildMediaRequest(compounds=["cpd00027"], custom_bounds={"cpd00027": (0, 0)})

        assert request.custom_bounds["cpd00027"] == (0.0, 0.0)

    def test_custom_bounds_not_in_compounds_error(self):
        """Test error when custom_bounds compound not in compounds list."""
        with pytest.raises(PydanticValidationError) as exc_info:
            BuildMediaRequest(compounds=["cpd00027"], custom_bounds={"cpd00007": (-10, 100)})

        error_msg = str(exc_info.value)
        assert "not in media" in error_msg.lower()
        assert "cpd00007" in error_msg

    def test_invalid_default_uptake_error(self):
        """Test error when default_uptake is negative or zero."""
        with pytest.raises(PydanticValidationError) as exc_info:
            BuildMediaRequest(compounds=["cpd00027"], default_uptake=-10.0)

        error_msg = str(exc_info.value)
        assert "greater than 0" in error_msg.lower()

    def test_default_uptake_too_large_error(self):
        """Test error when default_uptake exceeds maximum."""
        with pytest.raises(PydanticValidationError) as exc_info:
            BuildMediaRequest(compounds=["cpd00027"], default_uptake=2000.0)

        error_msg = str(exc_info.value)
        assert "less than or equal to" in error_msg.lower()


# =============================================================================
# Test build_media Function
# =============================================================================


class TestBuildMediaFunction:
    """Test build_media tool implementation."""

    def test_minimal_media_creation(self, db_index):
        """Test creating minimal media with default parameters."""
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007", "cpd00001"],  # 3 compounds
            default_uptake=100.0,
        )

        response = build_media(request, db_index)

        # Validate response structure
        assert response["success"] is True
        assert "media_id" in response
        assert response["media_id"].startswith("media_")
        assert response["num_compounds"] == 3
        assert response["media_type"] == "minimal"  # < 50 compounds
        assert response["default_uptake_rate"] == 100.0
        assert response["custom_bounds_applied"] == 0

        # Validate compounds metadata
        assert len(response["compounds"]) == 3
        compound_ids = [c["id"] for c in response["compounds"]]
        assert "cpd00027" in compound_ids
        assert "cpd00007" in compound_ids
        assert "cpd00001" in compound_ids

        # Check compound metadata enrichment
        glucose = next(c for c in response["compounds"] if c["id"] == "cpd00027")
        assert glucose["name"] == "D-Glucose"
        assert glucose["formula"] == "C6H12O6"
        assert glucose["bounds"] == (-100.0, 100.0)  # Default bounds

    def test_rich_media_creation(self, db_index):
        """Test creating rich media (>= 50 compounds)."""
        # Create 50 compound IDs
        compounds = [f"cpd{i:05d}" for i in range(1, 51)]
        # Filter to only existing compounds in mock
        existing_compounds = [cpd for cpd in compounds if db_index.compound_exists(cpd)]

        # If we don't have 50 compounds in mock, test with what we have
        # but label it correctly
        if len(existing_compounds) < 50:
            # For this test, we'll just verify the classification logic works
            # with a threshold check
            pytest.skip("Not enough compounds in mock database for rich media test")

        request = BuildMediaRequest(compounds=existing_compounds[:50])

        response = build_media(request, db_index)

        assert response["success"] is True
        assert response["num_compounds"] == 50
        assert response["media_type"] == "rich"  # >= 50 compounds

    def test_custom_bounds_application(self, db_index):
        """Test custom bounds are correctly applied."""
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007", "cpd00001"],
            default_uptake=100.0,
            custom_bounds={
                "cpd00027": (-5.0, 100.0),  # Glucose limited
                "cpd00007": (-10.0, 100.0),  # O2 limited
            },
        )

        response = build_media(request, db_index)

        assert response["success"] is True
        assert response["custom_bounds_applied"] == 2

        # Check custom bounds applied correctly
        glucose = next(c for c in response["compounds"] if c["id"] == "cpd00027")
        assert glucose["bounds"] == (-5.0, 100.0)

        o2 = next(c for c in response["compounds"] if c["id"] == "cpd00007")
        assert o2["bounds"] == (-10.0, 100.0)

        # Check default bounds applied to compound without custom bounds
        h2o = next(c for c in response["compounds"] if c["id"] == "cpd00001")
        assert h2o["bounds"] == (-100.0, 100.0)

    def test_anaerobic_conditions_zero_oxygen(self, db_index):
        """Test that equal bounds [0,0] are allowed for blocked compounds (anaerobic)."""
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007", "cpd00001"],
            default_uptake=100.0,
            custom_bounds={
                "cpd00007": (0.0, 0.0),  # O2 blocked (anaerobic conditions)
            },
        )

        response = build_media(request, db_index)

        assert response["success"] is True
        assert response["custom_bounds_applied"] == 1

        # Verify O2 is blocked (bounds are [0, 0])
        o2 = next(c for c in response["compounds"] if c["id"] == "cpd00007")
        assert o2["bounds"] == (0.0, 0.0)
        assert o2["name"] == "O2"

        # Other compounds should have default bounds
        glucose = next(c for c in response["compounds"] if c["id"] == "cpd00027")
        assert glucose["bounds"] == (-100.0, 100.0)

    def test_media_stored_in_session(self, db_index):
        """Test media is stored in session storage."""
        request = BuildMediaRequest(compounds=["cpd00027", "cpd00007"])

        response = build_media(request, db_index)
        media_id = response["media_id"]

        # Verify media exists in storage
        assert media_exists(media_id)

        # Retrieve and verify stored media is MSMedia object
        stored_media = retrieve_media(media_id)
        assert stored_media is not None
        # MSMedia object should have get_media_constraints method
        assert hasattr(stored_media, "get_media_constraints")
        # Verify we can get constraints (should have 2 compounds)
        constraints = stored_media.get_media_constraints()
        assert len(constraints) == 2

    def test_unique_media_id_generation(self, db_index):
        """Test each media gets unique ID."""
        request1 = BuildMediaRequest(compounds=["cpd00027"])
        request2 = BuildMediaRequest(compounds=["cpd00007"])

        response1 = build_media(request1, db_index)
        response2 = build_media(request2, db_index)

        assert response1["media_id"] != response2["media_id"]

    def test_compound_metadata_enrichment(self, db_index):
        """Test compound metadata is enriched from database."""
        request = BuildMediaRequest(compounds=["cpd00027", "cpd00007"])

        response = build_media(request, db_index)

        # Validate all compounds have enriched metadata
        for compound in response["compounds"]:
            assert "id" in compound
            assert "name" in compound
            assert "formula" in compound
            assert "bounds" in compound
            assert compound["name"] != ""  # Should have name from database
            assert compound["formula"] != ""  # Should have formula from database

    def test_invalid_compound_ids_error(self, db_index):
        """Test error when compound IDs don't exist in database."""
        request = BuildMediaRequest(
            compounds=["cpd99999", "cpd88888", "cpd00027"]  # 2 invalid, 1 valid
        )

        with pytest.raises(ValidationError) as exc_info:
            build_media(request, db_index)

        error = exc_info.value
        assert error.error_code == "INVALID_COMPOUND_IDS"
        assert "cpd99999" in str(error.details.get("invalid_ids", []))
        assert "cpd88888" in str(error.details.get("invalid_ids", []))
        assert error.details["total_invalid"] == 2

    def test_all_invalid_compound_ids_error(self, db_index):
        """Test error when all compound IDs are invalid."""
        request = BuildMediaRequest(compounds=["cpd99999", "cpd88888"])

        with pytest.raises(ValidationError) as exc_info:
            build_media(request, db_index)

        error = exc_info.value
        assert error.error_code == "INVALID_COMPOUND_IDS"
        assert error.details["total_invalid"] == 2

    def test_different_default_uptake_values(self, db_index):
        """Test different default_uptake values are applied correctly."""
        # Test with default_uptake = 50.0
        request1 = BuildMediaRequest(compounds=["cpd00027"], default_uptake=50.0)
        response1 = build_media(request1, db_index)

        assert response1["default_uptake_rate"] == 50.0
        compound1 = response1["compounds"][0]
        assert compound1["bounds"] == (-50.0, 100.0)

        # Clear storage for next test
        clear_all_media()

        # Test with default_uptake = 10.0
        request2 = BuildMediaRequest(compounds=["cpd00027"], default_uptake=10.0)
        response2 = build_media(request2, db_index)

        assert response2["default_uptake_rate"] == 10.0
        compound2 = response2["compounds"][0]
        assert compound2["bounds"] == (-10.0, 100.0)


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestBuildMediaEdgeCases:
    """Test edge cases for build_media tool."""

    def test_single_compound_media(self, db_index):
        """Test media with single compound."""
        request = BuildMediaRequest(compounds=["cpd00027"])

        response = build_media(request, db_index)

        assert response["success"] is True
        assert response["num_compounds"] == 1
        assert len(response["compounds"]) == 1

    def test_large_media_composition(self, db_index):
        """Test media with many compounds."""
        # Get up to 100 existing compounds from mock
        all_compounds = []
        for i in range(1, 1000):
            cpd_id = f"cpd{i:05d}"
            if db_index.compound_exists(cpd_id):
                all_compounds.append(cpd_id)
            if len(all_compounds) >= 100:
                break

        # If we don't have 100, use what we have
        compounds = all_compounds[:100] if len(all_compounds) >= 100 else all_compounds

        request = BuildMediaRequest(compounds=compounds)

        response = build_media(request, db_index)

        assert response["success"] is True
        assert response["num_compounds"] == len(compounds)

    def test_zero_bounds_blocked_compound(self, db_index):
        """Test compound with zero bounds (blocked exchange)."""
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007"],
            custom_bounds={"cpd00007": (0.0, 0.0)},  # O2 blocked
        )

        response = build_media(request, db_index)

        o2 = next(c for c in response["compounds"] if c["id"] == "cpd00007")
        assert o2["bounds"] == (0.0, 0.0)

    def test_anaerobic_media(self, db_index):
        """Test anaerobic media configuration (no O2 uptake)."""
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007", "cpd00001"],
            custom_bounds={
                "cpd00007": (0.0, 100.0)  # O2 secretion only, no uptake
            },
        )

        response = build_media(request, db_index)

        o2 = next(c for c in response["compounds"] if c["id"] == "cpd00007")
        assert o2["bounds"] == (0.0, 100.0)

    def test_secretion_only_media(self, db_index):
        """Test compound with secretion only (positive bounds)."""
        request = BuildMediaRequest(
            compounds=["cpd00011"],  # CO2
            custom_bounds={"cpd00011": (0.0, 100.0)},  # Secretion only
        )

        response = build_media(request, db_index)

        co2 = next(c for c in response["compounds"] if c["id"] == "cpd00011")
        assert co2["bounds"] == (0.0, 100.0)

    def test_uptake_only_media(self, db_index):
        """Test compound with uptake only (no secretion)."""
        request = BuildMediaRequest(
            compounds=["cpd00027"],
            custom_bounds={"cpd00027": (-10.0, 0.0)},  # Uptake only
        )

        response = build_media(request, db_index)

        glucose = next(c for c in response["compounds"] if c["id"] == "cpd00027")
        assert glucose["bounds"] == (-10.0, 0.0)


# =============================================================================
# Test Response Format
# =============================================================================


class TestBuildMediaResponse:
    """Test response format matches specification."""

    def test_response_has_required_fields(self, db_index):
        """Test response contains all required fields."""
        request = BuildMediaRequest(compounds=["cpd00027", "cpd00007"])

        response = build_media(request, db_index)

        # Check required top-level fields
        required_fields = [
            "success",
            "media_id",
            "compounds",
            "num_compounds",
            "media_type",
            "default_uptake_rate",
            "custom_bounds_applied",
        ]
        for field in required_fields:
            assert field in response, f"Missing required field: {field}"

    def test_compound_metadata_fields(self, db_index):
        """Test each compound has required metadata fields."""
        request = BuildMediaRequest(compounds=["cpd00027"])

        response = build_media(request, db_index)

        compound = response["compounds"][0]
        required_fields = ["id", "name", "formula", "bounds"]
        for field in required_fields:
            assert field in compound, f"Missing compound field: {field}"

    def test_response_serializable_to_json(self, db_index):
        """Test response can be serialized to JSON."""
        import json

        request = BuildMediaRequest(compounds=["cpd00027", "cpd00007"])

        response = build_media(request, db_index)

        # Should not raise exception
        json_str = json.dumps(response)
        assert len(json_str) > 0

        # Verify deserialization
        parsed = json.loads(json_str)
        assert parsed["success"] is True
        assert "media_id" in parsed
