"""Testing utilities for storage management.

Provides helper functions for managing storage state in tests.
These utilities are intended for test code only, not production use.
"""

from typing import Any

from gem_flux_mcp.storage.models import MODEL_STORAGE
from gem_flux_mcp.storage.media import MEDIA_STORAGE
from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)


def clear_all_storage() -> None:
    """Clear all session storage.

    Clears both MODEL_STORAGE and MEDIA_STORAGE.
    Intended for use in test fixtures to ensure clean state.

    Example:
        >>> from gem_flux_mcp.storage.testing import clear_all_storage
        >>>
        >>> @pytest.fixture(autouse=True)
        >>> def cleanup():
        >>>     clear_all_storage()
        >>>     yield
        >>>     clear_all_storage()
    """
    model_count = len(MODEL_STORAGE)
    media_count = len(MEDIA_STORAGE)

    MODEL_STORAGE.clear()
    MEDIA_STORAGE.clear()

    logger.debug(f"Cleared storage: {model_count} models, {media_count} media")


def get_storage_state() -> dict[str, Any]:
    """Get current storage state for debugging.

    Returns:
        Dict with storage counts and IDs:
            {
                "models": {"count": int, "ids": list[str]},
                "media": {"count": int, "ids": list[str]},
            }

    Example:
        >>> state = get_storage_state()
        >>> print(f"Models: {state['models']['count']}")
        >>> print(f"Media IDs: {state['media']['ids']}")
    """
    return {
        "models": {
            "count": len(MODEL_STORAGE),
            "ids": list(MODEL_STORAGE.keys()),
        },
        "media": {
            "count": len(MEDIA_STORAGE),
            "ids": list(MEDIA_STORAGE.keys()),
        },
    }


def verify_storage_clean() -> None:
    """Verify storage is empty.

    Raises:
        AssertionError: If storage is not empty

    Example:
        >>> @pytest.fixture(autouse=True)
        >>> def setup():
        >>>     clear_all_storage()
        >>>     verify_storage_clean()  # Verify clean slate
        >>>     yield
    """
    state = get_storage_state()

    assert state["models"]["count"] == 0, (
        f"MODEL_STORAGE not empty: {state['models']['ids']}"
    )
    assert state["media"]["count"] == 0, (
        f"MEDIA_STORAGE not empty: {state['media']['ids']}"
    )


def verify_media_stored(media_id: str) -> None:
    """Verify media was successfully stored.

    Args:
        media_id: Media identifier to verify

    Raises:
        AssertionError: If media is not in storage

    Example:
        >>> @pytest.fixture
        >>> def test_media():
        >>>     store_media("test_id", media)
        >>>     verify_media_stored("test_id")  # Verify storage succeeded
        >>>     yield "test_id"
    """
    from gem_flux_mcp.storage.media import media_exists

    assert media_exists(media_id), (
        f"Media '{media_id}' not found in storage. "
        f"Available: {list(MEDIA_STORAGE.keys())}"
    )


def verify_model_stored(model_id: str) -> None:
    """Verify model was successfully stored.

    Args:
        model_id: Model identifier to verify

    Raises:
        AssertionError: If model is not in storage

    Example:
        >>> @pytest.fixture
        >>> def test_model():
        >>>     store_model("test_id", model)
        >>>     verify_model_stored("test_id")  # Verify storage succeeded
        >>>     yield "test_id"
    """
    from gem_flux_mcp.storage.models import model_exists

    assert model_exists(model_id), (
        f"Model '{model_id}' not found in storage. "
        f"Available: {list(MODEL_STORAGE.keys())}"
    )


def print_storage_state() -> None:
    """Print current storage state for debugging.

    Useful for debugging test failures where storage state is unexpected.

    Example:
        >>> @pytest.fixture
        >>> def debug_storage():
        >>>     print_storage_state()  # Before test
        >>>     yield
        >>>     print_storage_state()  # After test
    """
    state = get_storage_state()

    print("\n=== Storage State ===")
    print(f"Models ({state['models']['count']}): {state['models']['ids']}")
    print(f"Media ({state['media']['count']}): {state['media']['ids']}")
    print("====================\n")


def get_storage_ids() -> tuple[list[str], list[str]]:
    """Get lists of model and media IDs currently in storage.

    Returns:
        Tuple of (model_ids, media_ids)

    Example:
        >>> model_ids, media_ids = get_storage_ids()
        >>> assert "my_model.draft" in model_ids
        >>> assert "my_media" in media_ids
    """
    return (
        list(MODEL_STORAGE.keys()),
        list(MEDIA_STORAGE.keys()),
    )


def verify_storage_ids(
    expected_models: list[str] | None = None,
    expected_media: list[str] | None = None,
) -> None:
    """Verify storage contains expected IDs.

    Args:
        expected_models: List of model IDs that should be in storage (None = don't check)
        expected_media: List of media IDs that should be in storage (None = don't check)

    Raises:
        AssertionError: If expected IDs are not found

    Example:
        >>> store_model("model1", model)
        >>> store_media("media1", media)
        >>> verify_storage_ids(
        >>>     expected_models=["model1"],
        >>>     expected_media=["media1"],
        >>> )
    """
    if expected_models is not None:
        actual_models = list(MODEL_STORAGE.keys())
        for model_id in expected_models:
            assert model_id in actual_models, (
                f"Expected model '{model_id}' not found. "
                f"Available: {actual_models}"
            )

    if expected_media is not None:
        actual_media = list(MEDIA_STORAGE.keys())
        for media_id in expected_media:
            assert media_id in actual_media, (
                f"Expected media '{media_id}' not found. "
                f"Available: {actual_media}"
            )
