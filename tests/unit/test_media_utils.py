"""Unit tests for media utilities (src/gem_flux_mcp/utils/media.py)."""

import pytest
from unittest.mock import Mock, patch
import math

from gem_flux_mcp.utils.media import apply_media_to_model


class TestApplyMediaToModel:
    """Test shared media application utility."""

    def test_msmedia_object_application(self):
        """Test media application with MSMedia object."""
        # Create mock model
        model = Mock()
        model.reactions = Mock()
        model.reactions.__contains__ = Mock(
            side_effect=lambda x: x in ["EX_cpd00027_e0", "EX_cpd00007_e0"]
        )

        # Create mock MSMedia
        media = Mock()
        media.get_media_constraints = Mock(
            return_value={
                "cpd00027_e0": (-5.0, 100.0),  # Glucose
                "cpd00007_e0": (-10.0, 100.0),  # Oxygen
            }
        )

        # Apply media
        apply_media_to_model(model, media, compartment="e0")

        # Verify medium was set correctly
        assert model.medium == {
            "EX_cpd00027_e0": 5.0,  # Positive uptake rate
            "EX_cpd00007_e0": 10.0,  # Positive uptake rate
        }

    def test_dict_with_compounds_key(self):
        """Test media application with dict (compounds key)."""
        # Create mock model
        model = Mock()
        model.reactions = Mock()
        model.reactions.__contains__ = Mock(
            side_effect=lambda x: x in ["EX_cpd00027_e0", "EX_cpd00007_e0"]
        )

        # Dict format with "compounds" key
        media_dict = {
            "compounds": {
                "cpd00027_e0": (-5.0, 100.0),
                "cpd00007_e0": (-10.0, 100.0),
            }
        }

        # Apply media
        apply_media_to_model(model, media_dict)

        # Verify medium was set
        assert model.medium == {
            "EX_cpd00027_e0": 5.0,
            "EX_cpd00007_e0": 10.0,
        }

    def test_dict_with_bounds_key(self):
        """Test media application with dict (bounds key for backwards compatibility)."""
        # Create mock model
        model = Mock()
        model.reactions = Mock()
        model.reactions.__contains__ = Mock(
            side_effect=lambda x: x in ["EX_cpd00027_e0"]
        )

        # Dict format with "bounds" key
        media_dict = {
            "bounds": {
                "cpd00027_e0": (-5.0, 100.0),
            }
        }

        # Apply media
        apply_media_to_model(model, media_dict)

        # Verify medium was set
        assert model.medium == {"EX_cpd00027_e0": 5.0}

    def test_compound_without_compartment_suffix(self):
        """Test that compartment suffix is added if missing."""
        # Create mock model
        model = Mock()
        model.reactions = Mock()
        model.reactions.__contains__ = Mock(
            side_effect=lambda x: x == "EX_cpd00027_e0"
        )

        # Dict with compound ID missing compartment suffix
        media_dict = {
            "compounds": {
                "cpd00027": (-5.0, 100.0),  # Missing _e0 suffix
            }
        }

        # Apply media
        apply_media_to_model(model, media_dict, compartment="e0")

        # Verify compartment suffix was added
        assert model.medium == {"EX_cpd00027_e0": 5.0}

    def test_missing_exchange_reaction_warning(self, caplog):
        """Test warning when exchange reaction not in model."""
        import logging

        # Set logging level to DEBUG to capture debug messages
        caplog.set_level(logging.DEBUG)

        # Create mock model with no exchange reactions
        model = Mock()
        model.reactions = Mock()
        model.reactions.__contains__ = Mock(return_value=False)

        # Create mock MSMedia
        media = Mock()
        media.get_media_constraints = Mock(
            return_value={"cpd00027_e0": (-5.0, 100.0)}
        )

        # Apply media
        apply_media_to_model(model, media)

        # Verify empty medium (no matching exchanges)
        assert model.medium == {}

        # Verify debug message logged
        assert "not in model" in caplog.text

    def test_math_fabs_conversion(self):
        """Test that negative lower bounds are converted to positive uptake rates."""
        # Create mock model
        model = Mock()
        model.reactions = Mock()
        model.reactions.__contains__ = Mock(return_value=True)

        # Create mock MSMedia with various bounds
        media = Mock()
        media.get_media_constraints = Mock(
            return_value={
                "cpd00027_e0": (-5.0, 100.0),  # Negative lower bound
                "cpd00007_e0": (-10.5, 100.0),  # Decimal negative
                "cpd00001_e0": (0.0, 100.0),  # Zero (secretion only)
            }
        )

        # Apply media
        apply_media_to_model(model, media)

        # Verify all values are positive (absolute values)
        assert model.medium["EX_cpd00027_e0"] == 5.0
        assert model.medium["EX_cpd00007_e0"] == 10.5
        assert model.medium["EX_cpd00001_e0"] == 0.0

    def test_invalid_media_type_error(self):
        """Test that invalid media type raises TypeError."""
        model = Mock()

        # Try to apply invalid media type (string)
        with pytest.raises(TypeError, match="media must be MSMedia object or dict"):
            apply_media_to_model(model, "invalid_media")

        # Try to apply invalid media type (list)
        with pytest.raises(TypeError, match="media must be MSMedia object or dict"):
            apply_media_to_model(model, ["cpd00027"])

    def test_empty_media(self):
        """Test application of empty media."""
        model = Mock()

        # Empty MSMedia
        media = Mock()
        media.get_media_constraints = Mock(return_value={})

        # Apply media
        apply_media_to_model(model, media)

        # Verify empty medium
        assert model.medium == {}

    def test_custom_compartment(self):
        """Test media application with non-default compartment."""
        # Create mock model
        model = Mock()
        model.reactions = Mock()
        model.reactions.__contains__ = Mock(
            side_effect=lambda x: x == "EX_cpd00027_c0"  # Cytosol compartment
        )

        # Create mock MSMedia with c0 compartment
        media = Mock()
        media.get_media_constraints = Mock(
            return_value={"cpd00027_c0": (-5.0, 100.0)}
        )

        # Apply media with custom compartment
        apply_media_to_model(model, media, compartment="c0")

        # Verify medium applied to c0 exchange
        assert model.medium == {"EX_cpd00027_c0": 5.0}
