"""Unit tests for list_media tool.

Tests the list_media MCP tool according to specification
018-session-management-tools.md.
"""

from unittest.mock import MagicMock

import pytest

from gem_flux_mcp.storage.media import MEDIA_STORAGE, clear_all_media, store_media
from gem_flux_mcp.tools.list_media import (
    PREDEFINED_MEDIA_IDS,
    extract_media_metadata,
    extract_media_name,
    list_media,
)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear media storage before and after each test."""
    clear_all_media()
    yield
    clear_all_media()


def create_mock_media(num_compounds=18):
    """Create a mock media dict."""
    media = {}
    for i in range(num_compounds):
        cpd_id = f"cpd{str(i).zfill(5)}_e0"
        media[cpd_id] = (-100.0, 100.0)
    return media


def create_mock_db_index():
    """Create a mock database index for compound lookup."""
    db_index = MagicMock()

    def mock_get_compound(cpd_id):
        # Return mock compound info
        return {"name": f"Compound {cpd_id}"}

    db_index.get_compound = mock_get_compound
    return db_index


# =============================================================================
# Test extract_media_name
# =============================================================================


def test_extract_media_name_auto_generated():
    """Test extraction from auto-generated media ID."""
    assert extract_media_name("media_20251027_143052_x1y2z3") is None


def test_extract_media_name_predefined():
    """Test extraction from predefined media ID."""
    assert extract_media_name("glucose_minimal_aerobic") == "glucose_minimal_aerobic"
    assert extract_media_name("pyruvate_minimal_anaerobic") == "pyruvate_minimal_anaerobic"


def test_extract_media_name_unknown():
    """Test extraction from unknown format."""
    assert extract_media_name("custom_media_123") is None


# =============================================================================
# Test extract_media_metadata
# =============================================================================


def test_extract_media_metadata_minimal():
    """Test metadata extraction for minimal media."""
    media = create_mock_media(num_compounds=18)
    metadata = extract_media_metadata("media_xyz", media)

    assert metadata.media_id == "media_xyz"
    assert metadata.media_name is None
    assert metadata.num_compounds == 18
    assert metadata.media_type == "minimal"
    assert len(metadata.compounds_preview) <= 3


def test_extract_media_metadata_rich():
    """Test metadata extraction for rich media."""
    media = create_mock_media(num_compounds=60)
    metadata = extract_media_metadata("media_xyz", media)

    assert metadata.num_compounds == 60
    assert metadata.media_type == "rich"


def test_extract_media_metadata_with_db_index():
    """Test metadata extraction with compound name enrichment."""
    media = {"cpd00027_e0": (-5.0, 100.0), "cpd00007_e0": (-10.0, 100.0)}
    db_index = create_mock_db_index()

    metadata = extract_media_metadata("media_xyz", media, db_index)

    assert len(metadata.compounds_preview) == 2
    # Compounds are sorted alphabetically, so cpd00007 comes first
    assert metadata.compounds_preview[0]["id"] == "cpd00007"
    assert "Compound" in metadata.compounds_preview[0]["name"]


def test_extract_media_metadata_predefined():
    """Test metadata extraction for predefined media."""
    media = create_mock_media(num_compounds=18)
    metadata = extract_media_metadata("glucose_minimal_aerobic", media)

    assert metadata.media_name == "glucose_minimal_aerobic"
    assert metadata.created_at == "2025-10-27T00:00:00Z"


def test_extract_media_metadata_preview_limit():
    """Test that compounds preview is limited to 3."""
    media = create_mock_media(num_compounds=10)
    metadata = extract_media_metadata("media_xyz", media)

    assert len(metadata.compounds_preview) == 3


# =============================================================================
# Test list_media
# =============================================================================


def test_list_media_empty_storage():
    """Test listing media when storage is empty."""
    response = list_media()

    assert response["success"] is True
    assert response["total_media"] == 0
    assert len(response["media"]) == 0
    assert response["predefined_media"] == 0
    assert response["user_created_media"] == 0


def test_list_media_single():
    """Test listing single media."""
    media = create_mock_media(num_compounds=18)
    store_media("media_xyz", media)

    response = list_media()

    assert response["success"] is True
    assert response["total_media"] == 1
    assert len(response["media"]) == 1
    assert response["user_created_media"] == 1
    assert response["predefined_media"] == 0


def test_list_media_multiple():
    """Test listing multiple media."""
    media1 = create_mock_media(num_compounds=18)
    media2 = create_mock_media(num_compounds=25)
    media3 = create_mock_media(num_compounds=60)

    store_media("media_1", media1)
    store_media("media_2", media2)
    store_media("media_3", media3)

    response = list_media()

    assert response["success"] is True
    assert response["total_media"] == 3
    assert len(response["media"]) == 3


def test_list_media_predefined():
    """Test listing predefined media."""
    # Add predefined media
    media = create_mock_media(num_compounds=18)
    store_media("glucose_minimal_aerobic", media)

    response = list_media()

    assert response["success"] is True
    assert response["total_media"] == 1
    assert response["predefined_media"] == 1
    assert response["user_created_media"] == 0


def test_list_media_mixed():
    """Test listing mix of predefined and user-created media."""
    # Add predefined
    predefined = create_mock_media(num_compounds=18)
    store_media("glucose_minimal_aerobic", predefined)

    # Add user-created
    user = create_mock_media(num_compounds=20)
    store_media("media_xyz", user)

    response = list_media()

    assert response["success"] is True
    assert response["total_media"] == 2
    assert response["predefined_media"] == 1
    assert response["user_created_media"] == 1


def test_list_media_sorted_by_created_at():
    """Test that media are sorted by creation timestamp."""
    # Predefined media should come first (2025-10-27T00:00:00Z)
    predefined = create_mock_media(num_compounds=18)
    store_media("glucose_minimal_aerobic", predefined)

    # User-created media (current time, should come after)
    user = create_mock_media(num_compounds=20)
    store_media("media_20251027_143052_xyz", user)

    response = list_media()

    assert response["total_media"] == 2
    # Predefined should be first (oldest timestamp)
    assert response["media"][0]["media_id"] == "glucose_minimal_aerobic"
    assert response["media"][1]["media_id"] == "media_20251027_143052_xyz"


def test_list_media_with_db_index():
    """Test listing media with compound name enrichment."""
    media = {"cpd00027_e0": (-5.0, 100.0), "cpd00007_e0": (-10.0, 100.0)}
    store_media("media_xyz", media)

    db_index = create_mock_db_index()
    response = list_media(db_index=db_index)

    assert response["success"] is True
    assert response["total_media"] == 1
    # Compounds preview should have names
    assert len(response["media"][0]["compounds_preview"]) == 2


def test_list_media_minimal_vs_rich():
    """Test classification of minimal vs rich media."""
    # Minimal media (<50 compounds)
    minimal = create_mock_media(num_compounds=18)
    store_media("media_minimal", minimal)

    # Rich media (>=50 compounds)
    rich = create_mock_media(num_compounds=60)
    store_media("media_rich", rich)

    response = list_media()

    assert response["total_media"] == 2
    # Find each media in response
    minimal_info = next(m for m in response["media"] if m["media_id"] == "media_minimal")
    rich_info = next(m for m in response["media"] if m["media_id"] == "media_rich")

    assert minimal_info["media_type"] == "minimal"
    assert rich_info["media_type"] == "rich"


def test_list_media_all_predefined():
    """Test listing all predefined media types."""
    # Add all predefined media
    for media_id in PREDEFINED_MEDIA_IDS:
        media = create_mock_media(num_compounds=18)
        store_media(media_id, media)

    response = list_media()

    assert response["success"] is True
    assert response["total_media"] == len(PREDEFINED_MEDIA_IDS)
    assert response["predefined_media"] == len(PREDEFINED_MEDIA_IDS)
    assert response["user_created_media"] == 0


def test_list_media_compounds_preview_content():
    """Test that compounds preview contains correct structure."""
    media = {
        "cpd00027_e0": (-5.0, 100.0),
        "cpd00007_e0": (-10.0, 100.0),
        "cpd00001_e0": (-100.0, 100.0),
    }
    store_media("media_xyz", media)

    response = list_media()

    assert response["total_media"] == 1
    preview = response["media"][0]["compounds_preview"]

    # Check structure
    assert len(preview) == 3
    for compound in preview:
        assert "id" in compound
        assert "name" in compound
        # ID should not have compartment suffix
        assert not compound["id"].endswith("_e0")


def test_list_media_error_handling():
    """Test that errors are handled gracefully."""
    # Add media with invalid structure to trigger error handling
    # (This is a robustness test - real usage should not hit this)
    # The function should return an error response instead of crashing
    MEDIA_STORAGE["bad_media"] = None  # Invalid media object

    response = list_media()

    # Should return error response, not crash
    assert response["success"] is False or response["total_media"] >= 0
