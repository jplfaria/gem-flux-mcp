"""
Unit tests for media storage module.

Tests session-based in-memory media storage according to
specification 010-model-storage.md.
"""

import re

import pytest

from gem_flux_mcp.storage.media import (
    MEDIA_STORAGE,
    clear_all_media,
    delete_media,
    generate_media_id,
    get_media_count,
    list_media_ids,
    media_exists,
    retrieve_media,
    store_media,
)


class MockMSMedia:
    """Mock MSMedia object for testing."""

    def __init__(self, name: str):
        self.name = name


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before and after each test."""
    MEDIA_STORAGE.clear()
    yield
    MEDIA_STORAGE.clear()


class TestGenerateMediaId:
    """Test media ID generation."""

    def test_generate_media_id_format(self):
        """Test generated media ID has correct format."""
        media_id = generate_media_id()

        # Should match: media_YYYYMMDD_HHMMSS_xxxxxx
        pattern = r"^media_\d{8}_\d{6}_[a-z0-9]{6}$"
        assert re.match(pattern, media_id), f"Invalid media ID format: {media_id}"

    def test_generate_media_id_uniqueness(self):
        """Test that generated media IDs are unique."""
        ids = [generate_media_id() for _ in range(100)]

        # All IDs should be unique
        assert len(ids) == len(set(ids)), "Generated media IDs are not unique"

    def test_generate_media_id_has_timestamp(self):
        """Test that media ID contains timestamp."""
        media_id = generate_media_id()

        # Extract timestamp from media_YYYYMMDD_HHMMSS_random
        parts = media_id.split("_")
        assert len(parts) == 4, f"Invalid media ID parts: {parts}"

        timestamp_date = parts[1]  # YYYYMMDD
        timestamp_time = parts[2]  # HHMMSS

        # Validate date format
        assert len(timestamp_date) == 8, f"Invalid date: {timestamp_date}"
        assert timestamp_date.isdigit(), f"Date not numeric: {timestamp_date}"

        # Validate time format
        assert len(timestamp_time) == 6, f"Invalid time: {timestamp_time}"
        assert timestamp_time.isdigit(), f"Time not numeric: {timestamp_time}"

    def test_generate_media_id_has_random_suffix(self):
        """Test that media ID contains random suffix."""
        media_id = generate_media_id()

        # Extract random suffix from media_YYYYMMDD_HHMMSS_random
        parts = media_id.split("_")
        random_suffix = parts[3]

        # Should be 6 lowercase alphanumeric characters
        assert len(random_suffix) == 6, f"Random suffix length != 6: {random_suffix}"
        assert random_suffix.isalnum(), f"Random suffix not alphanumeric: {random_suffix}"
        assert random_suffix.islower(), f"Random suffix not lowercase: {random_suffix}"


class TestStoreMedia:
    """Test media storage."""

    def test_store_media_success(self):
        """Test successful media storage."""
        media = MockMSMedia("test_media")
        media_id = "media_001"

        store_media(media_id, media)

        assert media_id in MEDIA_STORAGE
        assert MEDIA_STORAGE[media_id] == media

    def test_store_media_multiple(self):
        """Test storing multiple media."""
        media1 = MockMSMedia("media1")
        media2 = MockMSMedia("media2")

        store_media("media_001", media1)
        store_media("media_002", media2)

        assert len(MEDIA_STORAGE) == 2
        assert MEDIA_STORAGE["media_001"] == media1
        assert MEDIA_STORAGE["media_002"] == media2

    def test_store_media_empty_id_raises_error(self):
        """Test that empty media_id raises ValueError."""
        media = MockMSMedia("test")

        with pytest.raises(ValueError, match="media_id cannot be empty"):
            store_media("", media)

    def test_store_media_none_media_raises_error(self):
        """Test that None media raises ValueError."""
        with pytest.raises(ValueError, match="media cannot be None"):
            store_media("media_001", None)

    def test_store_media_collision_raises_error(self):
        """Test that duplicate media_id raises RuntimeError."""
        media1 = MockMSMedia("media1")
        media2 = MockMSMedia("media2")

        store_media("media_001", media1)

        with pytest.raises(RuntimeError, match="already exists"):
            store_media("media_001", media2)

    def test_store_media_overwrites_if_collision_not_checked(self):
        """Test that collision error prevents overwrite."""
        media1 = MockMSMedia("media1")
        media2 = MockMSMedia("media2")

        store_media("media_001", media1)

        # Verify collision is detected
        with pytest.raises(RuntimeError):
            store_media("media_001", media2)

        # Verify original media is preserved
        assert MEDIA_STORAGE["media_001"] == media1


class TestRetrieveMedia:
    """Test media retrieval."""

    def test_retrieve_media_success(self):
        """Test successful media retrieval."""
        media = MockMSMedia("test_media")
        MEDIA_STORAGE["media_001"] = media

        retrieved = retrieve_media("media_001")

        assert retrieved == media

    def test_retrieve_media_not_found_raises_error(self):
        """Test that non-existent media_id raises KeyError."""
        MEDIA_STORAGE["media_002"] = MockMSMedia("other")

        with pytest.raises(KeyError, match="not found"):
            retrieve_media("media_001")

    def test_retrieve_media_error_includes_available_media(self):
        """Test that error message is descriptive."""
        MEDIA_STORAGE["media_002"] = MockMSMedia("media2")
        MEDIA_STORAGE["media_003"] = MockMSMedia("media3")

        with pytest.raises(KeyError) as exc_info:
            retrieve_media("media_001")

        error_msg = str(exc_info.value)
        # Check that error message mentions the media_id
        assert "media_001" in error_msg.lower()
        assert "not found" in error_msg.lower()

    def test_retrieve_media_empty_id_raises_error(self):
        """Test that empty media_id raises ValueError."""
        with pytest.raises(ValueError, match="media_id cannot be empty"):
            retrieve_media("")


class TestMediaExists:
    """Test media existence checks."""

    def test_media_exists_true(self):
        """Test that media_exists returns True for existing media."""
        MEDIA_STORAGE["media_001"] = MockMSMedia("test")

        assert media_exists("media_001") is True

    def test_media_exists_false(self):
        """Test that media_exists returns False for non-existent media."""
        assert media_exists("media_999") is False

    def test_media_exists_after_storage(self):
        """Test media_exists after storing media."""
        media = MockMSMedia("test")

        assert media_exists("media_001") is False

        store_media("media_001", media)

        assert media_exists("media_001") is True

    def test_media_exists_empty_storage(self):
        """Test media_exists with empty storage."""
        assert media_exists("media_001") is False


class TestListMediaIds:
    """Test listing media IDs."""

    def test_list_media_ids_empty(self):
        """Test listing media IDs with empty storage."""
        ids = list_media_ids()

        assert ids == []

    def test_list_media_ids_single(self):
        """Test listing media IDs with single media."""
        MEDIA_STORAGE["media_001"] = MockMSMedia("test")

        ids = list_media_ids()

        assert ids == ["media_001"]

    def test_list_media_ids_multiple(self):
        """Test listing media IDs with multiple media."""
        MEDIA_STORAGE["media_003"] = MockMSMedia("media3")
        MEDIA_STORAGE["media_001"] = MockMSMedia("media1")
        MEDIA_STORAGE["media_002"] = MockMSMedia("media2")

        ids = list_media_ids()

        # Should be sorted alphabetically
        assert ids == ["media_001", "media_002", "media_003"]

    def test_list_media_ids_sorted(self):
        """Test that media IDs are sorted alphabetically."""
        MEDIA_STORAGE["media_z"] = MockMSMedia("z")
        MEDIA_STORAGE["media_a"] = MockMSMedia("a")
        MEDIA_STORAGE["media_m"] = MockMSMedia("m")

        ids = list_media_ids()

        assert ids == sorted(ids)


class TestDeleteMedia:
    """Test media deletion."""

    def test_delete_media_success(self):
        """Test successful media deletion."""
        MEDIA_STORAGE["media_001"] = MockMSMedia("test")

        delete_media("media_001")

        assert "media_001" not in MEDIA_STORAGE
        assert len(MEDIA_STORAGE) == 0

    def test_delete_media_not_found_raises_error(self):
        """Test that deleting non-existent media raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            delete_media("media_999")

    def test_delete_media_empty_id_raises_error(self):
        """Test that empty media_id raises ValueError."""
        with pytest.raises(ValueError, match="media_id cannot be empty"):
            delete_media("")

    def test_delete_media_leaves_others(self):
        """Test that deleting one media leaves others intact."""
        MEDIA_STORAGE["media_001"] = MockMSMedia("media1")
        MEDIA_STORAGE["media_002"] = MockMSMedia("media2")
        MEDIA_STORAGE["media_003"] = MockMSMedia("media3")

        delete_media("media_002")

        assert "media_002" not in MEDIA_STORAGE
        assert "media_001" in MEDIA_STORAGE
        assert "media_003" in MEDIA_STORAGE
        assert len(MEDIA_STORAGE) == 2


class TestClearAllMedia:
    """Test clearing all media."""

    def test_clear_all_media_empty(self):
        """Test clearing empty storage."""
        count = clear_all_media()

        assert count == 0
        assert len(MEDIA_STORAGE) == 0

    def test_clear_all_media_single(self):
        """Test clearing storage with single media."""
        MEDIA_STORAGE["media_001"] = MockMSMedia("test")

        count = clear_all_media()

        assert count == 1
        assert len(MEDIA_STORAGE) == 0

    def test_clear_all_media_multiple(self):
        """Test clearing storage with multiple media."""
        MEDIA_STORAGE["media_001"] = MockMSMedia("media1")
        MEDIA_STORAGE["media_002"] = MockMSMedia("media2")
        MEDIA_STORAGE["media_003"] = MockMSMedia("media3")

        count = clear_all_media()

        assert count == 3
        assert len(MEDIA_STORAGE) == 0


class TestGetMediaCount:
    """Test getting media count."""

    def test_get_media_count_empty(self):
        """Test media count with empty storage."""
        count = get_media_count()

        assert count == 0

    def test_get_media_count_single(self):
        """Test media count with single media."""
        MEDIA_STORAGE["media_001"] = MockMSMedia("test")

        count = get_media_count()

        assert count == 1

    def test_get_media_count_multiple(self):
        """Test media count with multiple media."""
        MEDIA_STORAGE["media_001"] = MockMSMedia("media1")
        MEDIA_STORAGE["media_002"] = MockMSMedia("media2")
        MEDIA_STORAGE["media_003"] = MockMSMedia("media3")

        count = get_media_count()

        assert count == 3

    def test_get_media_count_after_operations(self):
        """Test media count after various operations."""
        assert get_media_count() == 0

        store_media("media_001", MockMSMedia("media1"))
        assert get_media_count() == 1

        store_media("media_002", MockMSMedia("media2"))
        assert get_media_count() == 2

        delete_media("media_001")
        assert get_media_count() == 1

        clear_all_media()
        assert get_media_count() == 0


class TestMediaStorageIntegration:
    """Integration tests for media storage."""

    def test_complete_media_lifecycle(self):
        """Test complete media lifecycle: create → store → retrieve → delete."""
        # Generate ID
        media_id = generate_media_id()
        assert media_id.startswith("media_")

        # Store media
        media = MockMSMedia("test_media")
        store_media(media_id, media)
        assert media_exists(media_id)

        # Retrieve media
        retrieved = retrieve_media(media_id)
        assert retrieved == media

        # List media
        ids = list_media_ids()
        assert media_id in ids

        # Delete media
        delete_media(media_id)
        assert not media_exists(media_id)

    def test_multiple_media_workflow(self):
        """Test workflow with multiple media."""
        # Create and store multiple media
        media_ids = []
        for i in range(5):
            media_id = generate_media_id()
            media = MockMSMedia(f"media_{i}")
            store_media(media_id, media)
            media_ids.append(media_id)

        # Verify all stored
        assert get_media_count() == 5
        stored_ids = list_media_ids()
        for media_id in media_ids:
            assert media_id in stored_ids

        # Delete some media
        delete_media(media_ids[0])
        delete_media(media_ids[2])
        assert get_media_count() == 3

        # Clear remaining
        count = clear_all_media()
        assert count == 3
        assert get_media_count() == 0

    def test_media_id_format_consistency(self):
        """Test that generated media IDs follow consistent format."""
        ids = [generate_media_id() for _ in range(10)]

        pattern = r"^media_\d{8}_\d{6}_[a-z0-9]{6}$"
        for media_id in ids:
            assert re.match(pattern, media_id), f"Inconsistent format: {media_id}"
