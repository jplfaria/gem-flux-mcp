"""Unit tests for predefined media loader.

Tests loading predefined media from JSON files according to specification 019.
"""

import json

import pytest

from gem_flux_mcp.media.predefined_loader import (
    PREDEFINED_MEDIA_CACHE,
    get_predefined_media,
    get_predefined_media_count,
    has_predefined_media,
    list_predefined_media_names,
    load_predefined_media,
)

# Sample media definition for testing
SAMPLE_MEDIA = {
    "name": "test_media",
    "description": "Test media for unit tests",
    "compounds": {
        "cpd00027": {"name": "D-Glucose", "bounds": [-5.0, 100.0], "comment": "Carbon source"},
        "cpd00007": {"name": "O2", "bounds": [-10.0, 100.0], "comment": "Oxygen"},
    },
}


class TestLoadPredefinedMedia:
    """Test load_predefined_media function."""

    def setup_method(self):
        """Clear cache before each test."""
        PREDEFINED_MEDIA_CACHE.clear()

    def test_load_predefined_media_success(self, tmp_path):
        """Test successful loading of predefined media."""
        # Create temporary media directory with JSON files
        media_dir = tmp_path / "media"
        media_dir.mkdir()

        # Create test media file with compounds WITHOUT _e0 suffix
        # Loader stores compound IDs as-is (suffix added during media application)
        media_json = {
            "name": "test_media",
            "description": "Test media for unit tests",
            "compounds": {
                "cpd00027": {  # No _e0 suffix
                    "name": "D-Glucose",
                    "bounds": [-5.0, 100.0],
                    "comment": "Carbon source",
                },
                "cpd00007": {  # No _e0 suffix
                    "name": "O2",
                    "bounds": [-10.0, 100.0],
                    "comment": "Oxygen",
                },
            },
        }

        media_file = media_dir / "test_media.json"
        media_file.write_text(json.dumps(media_json))

        # Load predefined media
        result = load_predefined_media(str(media_dir))

        # Verify media loaded
        assert "test_media" in result
        assert result["test_media"]["name"] == "test_media"
        assert result["test_media"]["description"] == "Test media for unit tests"
        assert result["test_media"]["is_predefined"] is True

        # Verify compounds stored as-is (suffix added during apply_media_to_model)
        compounds = result["test_media"]["compounds"]
        assert "cpd00027" in compounds
        assert "cpd00007" in compounds
        assert compounds["cpd00027"] == (-5.0, 100.0)
        assert compounds["cpd00007"] == (-10.0, 100.0)

    def test_load_multiple_media(self, tmp_path):
        """Test loading multiple media files."""
        media_dir = tmp_path / "media"
        media_dir.mkdir()

        # Create multiple media files
        media1 = {"name": "media1", "compounds": {"cpd00001": {"bounds": [-1, 1]}}}
        media2 = {"name": "media2", "compounds": {"cpd00002": {"bounds": [-2, 2]}}}

        (media_dir / "media1.json").write_text(json.dumps(media1))
        (media_dir / "media2.json").write_text(json.dumps(media2))

        # Load predefined media
        result = load_predefined_media(str(media_dir))

        # Verify both media loaded
        assert len(result) == 2
        assert "media1" in result
        assert "media2" in result

    def test_load_empty_directory(self, tmp_path):
        """Test loading from empty directory."""
        media_dir = tmp_path / "media"
        media_dir.mkdir()

        # Load predefined media (should succeed but return empty dict)
        result = load_predefined_media(str(media_dir))

        assert result == {}
        assert len(PREDEFINED_MEDIA_CACHE) == 0

    def test_load_missing_directory(self):
        """Test loading from non-existent directory."""
        with pytest.raises(RuntimeError, match="not found"):
            load_predefined_media("/nonexistent/media/directory")

    def test_load_invalid_directory(self, tmp_path):
        """Test loading when path is a file, not directory."""
        # Create a file instead of directory
        media_file = tmp_path / "media.txt"
        media_file.write_text("not a directory")

        with pytest.raises(RuntimeError, match="not a directory"):
            load_predefined_media(str(media_file))

    def test_load_invalid_json(self, tmp_path):
        """Test handling of invalid JSON file."""
        media_dir = tmp_path / "media"
        media_dir.mkdir()

        # Create invalid JSON file
        invalid_file = media_dir / "invalid.json"
        invalid_file.write_text("not valid json {")

        # Load should continue despite error
        result = load_predefined_media(str(media_dir))

        # Should return empty since invalid JSON was skipped
        assert result == {}

    def test_load_missing_name_field(self, tmp_path):
        """Test handling of media definition missing 'name' field."""
        media_dir = tmp_path / "media"
        media_dir.mkdir()

        # Create media file without 'name'
        invalid_media = {"compounds": {"cpd00001": {"bounds": [-1, 1]}}}
        (media_dir / "no_name.json").write_text(json.dumps(invalid_media))

        # Load should skip this file
        result = load_predefined_media(str(media_dir))

        assert result == {}

    def test_load_missing_compounds_field(self, tmp_path):
        """Test handling of media definition missing 'compounds' field."""
        media_dir = tmp_path / "media"
        media_dir.mkdir()

        # Create media file without 'compounds'
        invalid_media = {"name": "test_media"}
        (media_dir / "no_compounds.json").write_text(json.dumps(invalid_media))

        # Load should skip this file
        result = load_predefined_media(str(media_dir))

        assert result == {}

    def test_cache_updated(self, tmp_path):
        """Test that cache is updated after loading."""
        media_dir = tmp_path / "media"
        media_dir.mkdir()

        media_file = media_dir / "test.json"
        media_file.write_text(json.dumps(SAMPLE_MEDIA))

        # Clear cache first
        PREDEFINED_MEDIA_CACHE.clear()

        # Load media
        load_predefined_media(str(media_dir))

        # Verify cache updated
        assert "test_media" in PREDEFINED_MEDIA_CACHE
        assert PREDEFINED_MEDIA_CACHE["test_media"]["name"] == "test_media"

    def test_cache_cleared_on_reload(self, tmp_path):
        """Test that cache is cleared when reloading."""
        media_dir = tmp_path / "media"
        media_dir.mkdir()

        # Add old entry to cache
        PREDEFINED_MEDIA_CACHE["old_media"] = {"name": "old"}

        # Load new media
        media_file = media_dir / "new.json"
        media_file.write_text(json.dumps({"name": "new", "compounds": {}}))

        load_predefined_media(str(media_dir))

        # Old entry should be gone
        assert "old_media" not in PREDEFINED_MEDIA_CACHE
        assert "new" in PREDEFINED_MEDIA_CACHE


class TestGetPredefinedMedia:
    """Test get_predefined_media function."""

    def setup_method(self):
        """Setup test cache."""
        PREDEFINED_MEDIA_CACHE.clear()
        PREDEFINED_MEDIA_CACHE["test_media"] = {"name": "test_media"}

    def test_get_existing_media(self):
        """Test getting existing predefined media."""
        result = get_predefined_media("test_media")

        assert result is not None
        assert result["name"] == "test_media"

    def test_get_nonexistent_media(self):
        """Test getting non-existent media."""
        result = get_predefined_media("nonexistent")

        assert result is None


class TestHasPredefinedMedia:
    """Test has_predefined_media function."""

    def setup_method(self):
        """Setup test cache."""
        PREDEFINED_MEDIA_CACHE.clear()
        PREDEFINED_MEDIA_CACHE["test_media"] = {"name": "test_media"}

    def test_has_existing_media(self):
        """Test checking for existing media."""
        assert has_predefined_media("test_media") is True

    def test_has_nonexistent_media(self):
        """Test checking for non-existent media."""
        assert has_predefined_media("nonexistent") is False


class TestListPredefinedMediaNames:
    """Test list_predefined_media_names function."""

    def setup_method(self):
        """Setup test cache."""
        PREDEFINED_MEDIA_CACHE.clear()

    def test_list_media_names(self):
        """Test listing predefined media names."""
        PREDEFINED_MEDIA_CACHE["media_b"] = {"name": "media_b"}
        PREDEFINED_MEDIA_CACHE["media_a"] = {"name": "media_a"}
        PREDEFINED_MEDIA_CACHE["media_c"] = {"name": "media_c"}

        result = list_predefined_media_names()

        # Should be sorted alphabetically
        assert result == ["media_a", "media_b", "media_c"]

    def test_list_empty_cache(self):
        """Test listing when cache is empty."""
        result = list_predefined_media_names()

        assert result == []


class TestGetPredefinedMediaCount:
    """Test get_predefined_media_count function."""

    def setup_method(self):
        """Setup test cache."""
        PREDEFINED_MEDIA_CACHE.clear()

    def test_count_media(self):
        """Test counting predefined media."""
        PREDEFINED_MEDIA_CACHE["media1"] = {"name": "media1"}
        PREDEFINED_MEDIA_CACHE["media2"] = {"name": "media2"}

        assert get_predefined_media_count() == 2

    def test_count_empty_cache(self):
        """Test counting when cache is empty."""
        assert get_predefined_media_count() == 0
