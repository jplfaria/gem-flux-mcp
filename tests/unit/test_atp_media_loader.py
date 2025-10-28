"""
Unit tests for ATP media loader.

Tests the loading, caching, and error handling of ATP gapfilling media
according to spec 015-mcp-server-setup.md.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from gem_flux_mcp.media import (
    ATP_MEDIA_CACHE,
    get_atp_media,
    get_atp_media_info,
    has_atp_media,
    load_atp_media,
)


@pytest.fixture
def clear_atp_cache():
    """Clear ATP media cache before and after each test."""
    ATP_MEDIA_CACHE.clear()
    yield
    ATP_MEDIA_CACHE.clear()


@pytest.fixture
def mock_atp_media():
    """Create mock ATP media objects for testing."""
    mock_medias = []

    for i in range(3):  # Create 3 mock media for testing
        mock_media = MagicMock()
        mock_media.id = f"test_media_{i}"
        mock_media.name = f"Test Media {i}"
        mock_media.mediacompounds = {
            f"cpd0000{j}": (-10, 100) for j in range(5)
        }
        min_obj = 0.01 + (i * 0.005)  # Varying min_obj values
        mock_medias.append((mock_media, min_obj))

    return mock_medias


class TestLoadATPMedia:
    """Tests for load_atp_media function."""

    def test_load_atp_media_success(self, clear_atp_cache, mock_atp_media):
        """Test successful loading of ATP media."""
        with patch('gem_flux_mcp.media.atp_loader.load_default_medias') as mock_load:
            mock_load.return_value = mock_atp_media

            result = load_atp_media()

            # Verify load_default_medias was called
            mock_load.assert_called_once_with(default_media_path=None)

            # Verify result matches mock data
            assert len(result) == 3
            assert result == mock_atp_media

            # Verify cache was updated
            assert len(ATP_MEDIA_CACHE) == 3
            assert ATP_MEDIA_CACHE == mock_atp_media

    def test_load_atp_media_with_custom_path(self, clear_atp_cache, mock_atp_media):
        """Test loading ATP media with custom path."""
        custom_path = "/path/to/custom_atp_medias.tsv"

        with patch('gem_flux_mcp.media.atp_loader.load_default_medias') as mock_load:
            mock_load.return_value = mock_atp_media

            result = load_atp_media(media_path=custom_path)

            # Verify custom path was passed
            mock_load.assert_called_once_with(default_media_path=custom_path)

            assert len(result) == 3

    def test_load_atp_media_logs_success(self, clear_atp_cache, mock_atp_media, caplog):
        """Test that successful loading logs info message."""
        with patch('gem_flux_mcp.media.atp_loader.load_default_medias') as mock_load:
            mock_load.return_value = mock_atp_media

            with caplog.at_level(logging.INFO):
                load_atp_media()

            # Verify success log message
            assert "✓ Loaded 3 ATP test media conditions" in caplog.text

    def test_load_atp_media_empty_result(self, clear_atp_cache):
        """Test loading ATP media when ModelSEEDpy returns empty list."""
        with patch('gem_flux_mcp.media.atp_loader.load_default_medias') as mock_load:
            mock_load.return_value = []

            result = load_atp_media()

            assert len(result) == 0
            assert len(ATP_MEDIA_CACHE) == 0

    def test_load_atp_media_file_not_found(self, clear_atp_cache, caplog):
        """Test handling of FileNotFoundError during loading."""
        with patch('gem_flux_mcp.media.atp_loader.load_default_medias') as mock_load:
            mock_load.side_effect = FileNotFoundError("ATP media file not found")

            with caplog.at_level(logging.WARNING):
                result = load_atp_media()

            # Verify warning was logged
            assert "ATP media file not found" in caplog.text
            assert "ATP correction will be unavailable" in caplog.text

            # Verify empty result returned (non-fatal error)
            assert result == []
            assert len(ATP_MEDIA_CACHE) == 0

    def test_load_atp_media_generic_error(self, clear_atp_cache, caplog):
        """Test handling of generic exception during loading."""
        with patch('gem_flux_mcp.media.atp_loader.load_default_medias') as mock_load:
            mock_load.side_effect = Exception("Unexpected error")

            with caplog.at_level(logging.WARNING):
                result = load_atp_media()

            # Verify warning was logged
            assert "Failed to load ATP gapfilling media" in caplog.text
            assert "Server will continue without ATP media" in caplog.text

            # Verify empty result returned (non-fatal error)
            assert result == []
            assert len(ATP_MEDIA_CACHE) == 0

    def test_load_atp_media_clears_previous_cache(self, clear_atp_cache, mock_atp_media):
        """Test that loading ATP media clears previous cache."""
        # Populate cache with initial data
        ATP_MEDIA_CACHE.extend(mock_atp_media[:1])
        assert len(ATP_MEDIA_CACHE) == 1

        # Load new media
        with patch('gem_flux_mcp.media.atp_loader.load_default_medias') as mock_load:
            mock_load.return_value = mock_atp_media

            load_atp_media()

            # Verify cache was cleared and repopulated
            assert len(ATP_MEDIA_CACHE) == 3
            assert ATP_MEDIA_CACHE == mock_atp_media


class TestGetATPMedia:
    """Tests for get_atp_media function."""

    def test_get_atp_media_returns_copy(self, clear_atp_cache, mock_atp_media):
        """Test that get_atp_media returns a copy of the cache."""
        ATP_MEDIA_CACHE.extend(mock_atp_media)

        result = get_atp_media()

        # Verify result matches cache
        assert result == mock_atp_media

        # Verify result is a copy (modifying result shouldn't affect cache)
        result.clear()
        assert len(ATP_MEDIA_CACHE) == 3

    def test_get_atp_media_empty_cache(self, clear_atp_cache):
        """Test get_atp_media with empty cache."""
        result = get_atp_media()

        assert result == []


class TestHasATPMedia:
    """Tests for has_atp_media function."""

    def test_has_atp_media_true(self, clear_atp_cache, mock_atp_media):
        """Test has_atp_media returns True when media loaded."""
        ATP_MEDIA_CACHE.extend(mock_atp_media)

        assert has_atp_media() is True

    def test_has_atp_media_false(self, clear_atp_cache):
        """Test has_atp_media returns False when no media loaded."""
        assert has_atp_media() is False


class TestGetATPMediaInfo:
    """Tests for get_atp_media_info function."""

    def test_get_atp_media_info_success(self, clear_atp_cache, mock_atp_media):
        """Test getting ATP media metadata."""
        ATP_MEDIA_CACHE.extend(mock_atp_media)

        info = get_atp_media_info()

        assert len(info) == 3

        # Verify first media info
        assert info[0]["id"] == "test_media_0"
        assert info[0]["name"] == "Test Media 0"
        assert info[0]["num_compounds"] == 5
        assert info[0]["min_objective"] == 0.01

        # Verify second media info
        assert info[1]["id"] == "test_media_1"
        assert info[1]["min_objective"] == 0.015

    def test_get_atp_media_info_empty_cache(self, clear_atp_cache):
        """Test get_atp_media_info with empty cache."""
        info = get_atp_media_info()

        assert info == []

    def test_get_atp_media_info_media_without_compounds(self, clear_atp_cache):
        """Test get_atp_media_info when media lacks mediacompounds attribute."""
        mock_media = MagicMock()
        mock_media.id = "test_media"
        mock_media.name = "Test Media"
        # Don't set mediacompounds attribute
        delattr(mock_media, 'mediacompounds')

        ATP_MEDIA_CACHE.append((mock_media, 0.01))

        info = get_atp_media_info()

        assert len(info) == 1
        assert info[0]["num_compounds"] == 0  # Default when attribute missing


class TestATPMediaIntegration:
    """Integration tests for ATP media loading workflow."""

    def test_full_loading_workflow(self, clear_atp_cache, mock_atp_media):
        """Test complete workflow: load, check, get info."""
        # Initially no media
        assert has_atp_media() is False
        assert get_atp_media() == []

        # Load media
        with patch('gem_flux_mcp.media.atp_loader.load_default_medias') as mock_load:
            mock_load.return_value = mock_atp_media

            load_atp_media()

        # Verify media available
        assert has_atp_media() is True

        # Get media
        media = get_atp_media()
        assert len(media) == 3

        # Get info
        info = get_atp_media_info()
        assert len(info) == 3
        assert info[0]["id"] == "test_media_0"

    def test_loading_failure_workflow(self, clear_atp_cache, caplog):
        """Test workflow when loading fails."""
        # Attempt to load with error
        with patch('gem_flux_mcp.media.atp_loader.load_default_medias') as mock_load:
            mock_load.side_effect = FileNotFoundError("File not found")

            with caplog.at_level(logging.WARNING):
                result = load_atp_media()

        # Verify no media available
        assert result == []
        assert has_atp_media() is False
        assert get_atp_media() == []
        assert get_atp_media_info() == []

        # Verify warning logged
        assert "ATP media file not found" in caplog.text
