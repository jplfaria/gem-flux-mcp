"""Unit tests for media utilities (src/gem_flux_mcp/utils/media.py)."""

from unittest.mock import Mock

import pytest

from gem_flux_mcp.utils.media import apply_media_to_model


def create_mock_model_with_exchanges(exchange_ids):
    """Helper to create a mock model with iterable exchange reactions.

    Args:
        exchange_ids: List of exchange reaction IDs (e.g., ["EX_cpd00027_e0"])

    Returns:
        Mock model with properly configured reactions
    """
    model = Mock()

    # Create mock reactions
    mock_reactions = []
    for rxn_id in exchange_ids:
        mock_rxn = Mock()
        mock_rxn.id = rxn_id
        mock_rxn.lower_bound = 0.0
        mock_rxn.upper_bound = 1000.0
        mock_reactions.append(mock_rxn)

    # Create a Mock for reactions that is both iterable and supports 'in' operator
    reactions_mock = Mock()
    reactions_mock.__iter__ = Mock(return_value=iter(mock_reactions))
    reactions_mock.__contains__ = Mock(side_effect=lambda x: x in [r.id for r in mock_reactions])
    model.reactions = reactions_mock

    # Add .medium attribute (will be set by apply_media_to_model)
    model.medium = {}

    return model


class TestApplyMediaToModel:
    """Test shared media application utility."""

    def test_msmedia_object_application(self):
        """Test media application with MSMedia object."""
        # Create mock model with exchange reactions
        model = create_mock_model_with_exchanges(["EX_cpd00027_e0", "EX_cpd00007_e0"])

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
        # Create mock model with exchange reactions
        model = create_mock_model_with_exchanges(["EX_cpd00027_e0", "EX_cpd00007_e0"])

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
        # Create mock model with exchange reaction
        model = create_mock_model_with_exchanges(["EX_cpd00027_e0"])

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
        # Create mock model with exchange reaction
        model = create_mock_model_with_exchanges(["EX_cpd00027_e0"])

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
        """Test that ValueError is raised when no exchange reactions match."""
        import logging

        # Set logging level to DEBUG to capture debug messages
        caplog.set_level(logging.DEBUG)

        # Create mock model with no exchange reactions
        model = create_mock_model_with_exchanges([])

        # Create mock MSMedia
        media = Mock()
        media.get_media_constraints = Mock(return_value={"cpd00027_e0": (-5.0, 100.0)})

        # Apply media - should raise ValueError
        with pytest.raises(ValueError, match="no exchange reactions matched"):
            apply_media_to_model(model, media)

    def test_math_fabs_conversion(self):
        """Test that negative lower bounds are converted to positive uptake rates."""
        # Create mock model with exchange reactions
        model = create_mock_model_with_exchanges(
            ["EX_cpd00027_e0", "EX_cpd00007_e0", "EX_cpd00001_e0"]
        )

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
        """Test application of empty media raises ValueError."""
        model = Mock()

        # Empty MSMedia
        media = Mock()
        media.get_media_constraints = Mock(return_value={})

        # Apply media - should raise ValueError
        with pytest.raises(ValueError, match="no compound constraints found"):
            apply_media_to_model(model, media)

    def test_custom_compartment(self):
        """Test media application with non-default compartment."""
        # Create mock model with c0 compartment exchange
        model = create_mock_model_with_exchanges(["EX_cpd00027_c0"])

        # Create mock MSMedia with c0 compartment
        media = Mock()
        media.get_media_constraints = Mock(return_value={"cpd00027_c0": (-5.0, 100.0)})

        # Apply media with custom compartment
        apply_media_to_model(model, media, compartment="c0")

        # Verify medium applied to c0 exchange
        assert model.medium == {"EX_cpd00027_c0": 5.0}
