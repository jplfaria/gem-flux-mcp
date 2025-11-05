"""Predefined media library constants.

This module defines constants for predefined growth media that are available
in the server's media library. These media compositions are loaded on startup
and available to all tools.

See specification: 019-predefined-media-library.md
"""

# Predefined media IDs available in the library
# These are loaded from data/media/*.json on server startup
PREDEFINED_MEDIA_IDS = frozenset(
    [
        "glucose_minimal_aerobic",
        "glucose_minimal_anaerobic",
        "pyruvate_minimal_aerobic",
        "pyruvate_minimal_anaerobic",
    ]
)

# Fixed timestamp for predefined media (used for sorting consistency)
PREDEFINED_MEDIA_TIMESTAMP = "2025-10-27T00:00:00Z"
