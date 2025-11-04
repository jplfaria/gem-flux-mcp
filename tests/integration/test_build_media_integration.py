"""Integration tests for build_media tool.

Tests the build_media tool with real database and MSMedia objects.
These tests use real ModelSEED data and verify end-to-end functionality.
"""

import pytest
from pathlib import Path

from gem_flux_mcp.database import load_compounds_database, load_reactions_database
from gem_flux_mcp.database.index import DatabaseIndex
from gem_flux_mcp.tools.media_builder import build_media, BuildMediaRequest
from gem_flux_mcp.storage.media import retrieve_media, clear_all_media


@pytest.fixture
def real_database():
    """Load real ModelSEED database."""
    db_dir = Path(__file__).parent.parent.parent / "data" / "database"
    compounds_df = load_compounds_database(db_dir / "compounds.tsv")
    reactions_df = load_reactions_database(db_dir / "reactions.tsv")
    return DatabaseIndex(compounds_df, reactions_df)


@pytest.fixture(autouse=True)
def cleanup_media():
    """Clear media storage before and after each test."""
    clear_all_media()
    yield
    clear_all_media()


class TestBuildMediaIntegration:
    """Integration tests for build_media tool."""

    def test_build_minimal_glucose_media(self, real_database):
        """Test building minimal glucose media with real database."""
        # Build minimal glucose media
        request = BuildMediaRequest(
            compounds=[
                "cpd00027",  # D-Glucose
                "cpd00007",  # O2
                "cpd00001",  # H2O
                "cpd00009",  # Phosphate
                "cpd00011",  # CO2
                "cpd00013",  # NH3
                "cpd00067",  # H+
            ],
            default_uptake=100.0,
            custom_bounds={
                "cpd00027": (-5.0, 100.0),
                "cpd00007": (-10.0, 100.0),
            }
        )

        # Execute
        response = build_media(request, real_database)

        # Verify response structure
        assert response["success"] is True
        assert "media_id" in response
        assert response["media_id"].startswith("media_")
        assert response["num_compounds"] == 7
        assert response["media_type"] == "minimal"
        assert response["default_uptake_rate"] == 100.0
        assert response["custom_bounds_applied"] == 2

        # Verify compounds metadata
        assert len(response["compounds"]) == 7
        for cpd in response["compounds"]:
            assert "id" in cpd
            assert "name" in cpd
            assert "formula" in cpd
            assert "bounds" in cpd
            assert isinstance(cpd["bounds"], (list, tuple))
            assert len(cpd["bounds"]) == 2

        # Verify MSMedia object is stored
        media_obj = retrieve_media(response["media_id"])
        assert media_obj is not None
        assert hasattr(media_obj, "get_media_constraints")

        # Verify media constraints
        constraints = media_obj.get_media_constraints()
        assert isinstance(constraints, dict)
        assert len(constraints) == 7

        # Check specific compound bounds
        assert "cpd00027_e0" in constraints
        assert constraints["cpd00027_e0"] == (-5.0, 100.0)
        assert "cpd00007_e0" in constraints
        assert constraints["cpd00007_e0"] == (-10.0, 100.0)

    def test_build_complex_media_with_amino_acids(self, real_database):
        """Test building complex media with amino acids."""
        request = BuildMediaRequest(
            compounds=[
                "cpd00027",  # D-Glucose
                "cpd00007",  # O2
                "cpd00001",  # H2O
                "cpd00009",  # Phosphate
                "cpd00023",  # L-Glutamate
                "cpd00033",  # Glycine
                "cpd00035",  # L-Alanine
                "cpd00039",  # L-Lysine
                "cpd00041",  # L-Aspartate
            ],
            default_uptake=100.0,
        )

        response = build_media(request, real_database)

        assert response["success"] is True
        assert response["num_compounds"] == 9
        assert response["media_type"] == "minimal"  # < 50 compounds

        # Verify all amino acids are in response
        compound_ids = {cpd["id"] for cpd in response["compounds"]}
        assert "cpd00023" in compound_ids  # L-Glutamate
        assert "cpd00033" in compound_ids  # Glycine
        assert "cpd00035" in compound_ids  # L-Alanine

    def test_build_rich_media(self, real_database):
        """Test building rich media (>50 compounds)."""
        # Build a rich media with many compounds
        compounds = [
            f"cpd{str(i).zfill(5)}" for i in [
                27, 7, 1, 9, 11, 13, 67,  # Basic minimal
                23, 33, 35, 39, 41, 51, 54, 60, 66, 69,  # Amino acids
                2, 8, 10, 12, 15, 18, 20, 22, 24, 26,  # More metabolites
                28, 29, 30, 31, 32, 34, 36, 37, 38, 40,
                42, 43, 44, 45, 46, 47, 48, 49, 50, 52,
                53, 55, 56, 57, 58, 59,  # Even more to exceed 50
            ]
        ]

        request = BuildMediaRequest(
            compounds=compounds,
            default_uptake=100.0,
        )

        response = build_media(request, real_database)

        assert response["success"] is True
        assert response["num_compounds"] == len(compounds)
        assert response["media_type"] == "rich"  # >= 50 compounds

    def test_custom_bounds_override_defaults(self, real_database):
        """Test that custom bounds override default uptake rates."""
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007", "cpd00001"],
            default_uptake=50.0,  # Default
            custom_bounds={
                "cpd00027": (-10.0, 200.0),  # Custom override
            }
        )

        response = build_media(request, real_database)

        # Find glucose in response
        glucose = next(cpd for cpd in response["compounds"] if cpd["id"] == "cpd00027")
        # Bounds are returned as tuples, not lists
        assert glucose["bounds"] == (-10.0, 200.0)

        # Find O2 (should have default)
        o2 = next(cpd for cpd in response["compounds"] if cpd["id"] == "cpd00007")
        assert o2["bounds"] == (-50.0, 100.0)

    def test_media_id_generation(self, real_database):
        """Test that media IDs are unique and properly formatted."""
        # Build two media
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007"],
            default_uptake=100.0,
        )

        response1 = build_media(request, real_database)
        response2 = build_media(request, real_database)

        # IDs should be different
        assert response1["media_id"] != response2["media_id"]

        # Both should have proper format
        assert response1["media_id"].startswith("media_")
        assert response2["media_id"].startswith("media_")

        # Both should be retrievable
        media1 = retrieve_media(response1["media_id"])
        media2 = retrieve_media(response2["media_id"])
        assert media1 is not None
        assert media2 is not None

    def test_invalid_compound_format(self, real_database):
        """Test that invalid compound ID format is caught by Pydantic validation."""
        from pydantic import ValidationError

        # Pydantic catches format errors before tool execution
        with pytest.raises(ValidationError) as exc_info:
            BuildMediaRequest(
                compounds=[
                    "cpd00027",  # Valid
                    "invalid",   # Invalid - wrong format
                ],
                default_uptake=100.0,
            )

        # Verify it's a validation error for compound format
        assert "Invalid compound ID format" in str(exc_info.value)

    def test_nonexistent_compound_ids(self, real_database):
        """Test error handling for compound IDs that don't exist in database."""
        from gem_flux_mcp.errors import ValidationError

        request = BuildMediaRequest(
            compounds=[
                "cpd00027",  # Valid - exists
                "cpd99999",  # Invalid - doesn't exist in database
            ],
            default_uptake=100.0,
        )

        with pytest.raises(ValidationError) as exc_info:
            build_media(request, real_database)

        error = exc_info.value
        assert error.error_code == "INVALID_COMPOUND_IDS"
        assert "invalid_ids" in error.details
        assert "cpd99999" in error.details["invalid_ids"]

    def test_empty_compounds_list(self, real_database):
        """Test error handling for empty compounds list."""
        from pydantic import ValidationError

        # Pydantic catches empty list before tool execution
        with pytest.raises(ValidationError) as exc_info:
            BuildMediaRequest(
                compounds=[],
                default_uptake=100.0,
            )

        # Verify it's a validation error for empty list
        assert "Compounds list must be a non-empty list" in str(exc_info.value)

    def test_media_constraints_format(self, real_database):
        """Test that MSMedia.get_media_constraints returns correct format."""
        request = BuildMediaRequest(
            compounds=["cpd00027", "cpd00007"],
            default_uptake=100.0,
            custom_bounds={
                "cpd00027": (-5.0, 100.0),
            }
        )

        response = build_media(request, real_database)
        media_obj = retrieve_media(response["media_id"])

        constraints = media_obj.get_media_constraints()

        # Verify format: {compound_id_compartment: (lower, upper)}
        assert isinstance(constraints, dict)
        for cpd_id, bounds in constraints.items():
            assert "_e0" in cpd_id  # Should have compartment suffix
            assert isinstance(bounds, tuple)
            assert len(bounds) == 2
            assert isinstance(bounds[0], (int, float))
            assert isinstance(bounds[1], (int, float))

    @pytest.mark.slow
    def test_large_media_performance(self, real_database):
        """Test building media with many compounds (performance test)."""
        import time

        # Build media with 100 compounds
        compounds = [f"cpd{str(i).zfill(5)}" for i in range(1, 101)]

        request = BuildMediaRequest(
            compounds=compounds,
            default_uptake=100.0,
        )

        start = time.perf_counter()
        response = build_media(request, real_database)
        elapsed = time.perf_counter() - start

        # Should complete in reasonable time (< 1 second)
        assert elapsed < 1.0
        assert response["success"] is True
        assert response["num_compounds"] == 100

    def test_media_storage_isolation(self, real_database):
        """Test that media objects are properly isolated in storage."""
        # Build two different media
        request1 = BuildMediaRequest(
            compounds=["cpd00027"],
            default_uptake=100.0,
        )
        request2 = BuildMediaRequest(
            compounds=["cpd00007"],
            default_uptake=50.0,
        )

        response1 = build_media(request1, real_database)
        response2 = build_media(request2, real_database)

        # Retrieve both
        media1 = retrieve_media(response1["media_id"])
        media2 = retrieve_media(response2["media_id"])

        # Should be different objects
        assert media1 is not media2

        # Should have different constraints
        constraints1 = media1.get_media_constraints()
        constraints2 = media2.get_media_constraints()
        assert constraints1 != constraints2
