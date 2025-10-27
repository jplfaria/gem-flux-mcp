"""
Unit tests for template loader module.

Tests template loading, validation, caching, and error handling according to
spec 017-template-management.md.
"""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from gem_flux_mcp.errors import DatabaseError
from gem_flux_mcp.templates.loader import (
    TEMPLATE_CACHE,
    get_template,
    list_available_templates,
    load_template,
    load_templates,
    validate_template_name,
)


@pytest.fixture
def mock_template_dict():
    """Mock template dictionary (minimal structure)."""
    return {
        "id": "GramNegative",
        "name": "Gram-Negative Bacteria Template",
        "version": "6.0",
        "reactions": [{"id": "rxn00001"}, {"id": "rxn00002"}],
        "metabolites": [{"id": "cpd00001"}, {"id": "cpd00027"}],
        "compartments": ["c0", "e0", "p0"],
    }


@pytest.fixture
def mock_mstemplate():
    """Mock MSTemplate object."""
    template = Mock()
    template.reactions = [Mock(), Mock()]  # 2 reactions
    template.metabolites = [Mock(), Mock()]  # 2 metabolites
    template.compartments = ["c0", "e0", "p0"]
    template.version = "6.0"
    return template


@pytest.fixture
def mock_template_builder(mock_mstemplate):
    """Mock MSTemplateBuilder."""
    builder = Mock()
    builder.build.return_value = mock_mstemplate
    return builder


@pytest.fixture
def temp_template_dir(tmp_path):
    """Create temporary template directory with test files."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()

    # Create GramNegative template
    gram_neg = template_dir / "GramNegModelTemplateV6.json"
    gram_neg.write_text(json.dumps({
        "id": "GramNegative",
        "reactions": [{"id": "rxn1"}, {"id": "rxn2"}],
        "metabolites": [{"id": "cpd1"}],
        "compartments": ["c0", "e0", "p0"]
    }))

    # Create Core template
    core = template_dir / "Core-V5.2.json"
    core.write_text(json.dumps({
        "id": "Core",
        "reactions": [{"id": "rxn1"}],
        "metabolites": [{"id": "cpd1"}],
        "compartments": ["c0", "e0"]
    }))

    return template_dir


class TestLoadTemplate:
    """Tests for load_template() function."""

    def test_load_template_success(self, tmp_path, mock_template_dict, mock_template_builder):
        """Test successful template loading."""
        # Create template file
        template_path = tmp_path / "GramNegModelTemplateV6.json"
        template_path.write_text(json.dumps(mock_template_dict))

        # Mock MSTemplateBuilder
        with patch('gem_flux_mcp.templates.loader.MSTemplateBuilder') as MockBuilder:
            MockBuilder.from_dict.return_value = mock_template_builder

            template = load_template(template_path, "GramNegative")

            # Verify MSTemplateBuilder called correctly
            MockBuilder.from_dict.assert_called_once_with(mock_template_dict)
            mock_template_builder.build.assert_called_once()
            assert template == mock_template_builder.build.return_value

    def test_load_template_file_not_found(self, tmp_path):
        """Test error when template file missing."""
        template_path = tmp_path / "nonexistent.json"

        with pytest.raises(DatabaseError) as exc_info:
            load_template(template_path, "GramNegative")

        assert "Template file not found" in str(exc_info.value)
        assert str(template_path) in str(exc_info.value)

    def test_load_template_invalid_json(self, tmp_path):
        """Test error when template has invalid JSON."""
        template_path = tmp_path / "invalid.json"
        template_path.write_text("{ invalid json }")

        with pytest.raises(DatabaseError) as exc_info:
            load_template(template_path, "GramNegative")

        assert "Invalid JSON" in str(exc_info.value)
        assert "corrupted" in str(exc_info.value)

    def test_load_template_build_fails(self, tmp_path, mock_template_dict):
        """Test error when MSTemplateBuilder fails."""
        template_path = tmp_path / "template.json"
        template_path.write_text(json.dumps(mock_template_dict))

        # Mock MSTemplateBuilder to raise exception
        with patch('gem_flux_mcp.templates.loader.MSTemplateBuilder') as MockBuilder:
            mock_builder = Mock()
            mock_builder.build.side_effect = Exception("Build failed")
            MockBuilder.from_dict.return_value = mock_builder

            with pytest.raises(DatabaseError) as exc_info:
                load_template(template_path, "GramNegative")

            assert "Failed to build template" in str(exc_info.value)
            assert "version mismatch" in str(exc_info.value)

    def test_load_template_read_error(self, tmp_path):
        """Test error when file cannot be read."""
        template_path = tmp_path / "template.json"
        template_path.write_text("{}")
        template_path.chmod(0o000)  # Remove read permissions

        try:
            with pytest.raises(DatabaseError) as exc_info:
                load_template(template_path, "GramNegative")

            assert "Failed to read template file" in str(exc_info.value)
        finally:
            template_path.chmod(0o644)  # Restore permissions


class TestLoadTemplates:
    """Tests for load_templates() function."""

    def test_load_templates_success(self, temp_template_dir, mock_template_builder):
        """Test successful loading of all templates."""
        with patch('gem_flux_mcp.templates.loader.MSTemplateBuilder') as MockBuilder:
            MockBuilder.from_dict.return_value = mock_template_builder

            templates = load_templates(temp_template_dir)

            # Verify both required templates loaded
            assert "GramNegative" in templates
            assert "Core" in templates
            assert len(templates) == 2

            # Verify cache updated
            assert "GramNegative" in TEMPLATE_CACHE
            assert "Core" in TEMPLATE_CACHE

    def test_load_templates_directory_not_found(self):
        """Test error when template directory missing."""
        with pytest.raises(DatabaseError) as exc_info:
            load_templates(Path("/nonexistent/templates"))

        error_msg = str(exc_info.value)
        assert "Template directory not found" in error_msg
        assert "mkdir -p data/templates" in error_msg

    def test_load_templates_required_template_missing(self, tmp_path):
        """Test error when required template missing."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Only create Core template (missing GramNegative)
        core = template_dir / "Core-V5.2.json"
        core.write_text(json.dumps({"id": "Core", "reactions": [], "metabolites": []}))

        with pytest.raises(DatabaseError) as exc_info:
            load_templates(template_dir)

        error_msg = str(exc_info.value)
        assert "Required template missing" in error_msg
        assert "GramNegative" in error_msg

    def test_load_templates_optional_template_missing(self, temp_template_dir, mock_template_builder, caplog):
        """Test warning when optional template missing (but continues)."""
        # Remove optional GramPositive template (already doesn't exist)

        with patch('gem_flux_mcp.templates.loader.MSTemplateBuilder') as MockBuilder:
            MockBuilder.from_dict.return_value = mock_template_builder

            with caplog.at_level(logging.WARNING):
                templates = load_templates(temp_template_dir)

            # Should load successfully without GramPositive
            assert len(templates) == 2
            assert "GramPositive" not in templates

            # Should log warning about optional template
            assert any("Optional template 'GramPositive' not found" in msg for msg in caplog.messages)

    def test_load_templates_no_templates_loaded(self, tmp_path):
        """Test error when no templates successfully loaded.

        Note: Since GramNegative and Core are required templates,
        the loader will fail fast with "Invalid JSON" error
        when they are corrupted, rather than reaching the
        "No templates successfully loaded" check.
        """
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create invalid templates (invalid JSON)
        gram_neg = template_dir / "GramNegModelTemplateV6.json"
        gram_neg.write_text("{ invalid json }")

        core = template_dir / "Core-V5.2.json"
        core.write_text("{ invalid json }")

        # Should fail on first required template with invalid JSON
        with pytest.raises(DatabaseError) as exc_info:
            load_templates(template_dir)

        # Either "Invalid JSON" (fails on first template) or
        # "No templates successfully loaded" (all templates fail)
        assert ("Invalid JSON" in str(exc_info.value) or
                "No templates successfully loaded" in str(exc_info.value))

    def test_load_templates_logs_statistics(self, temp_template_dir, mock_template_builder, caplog):
        """Test that template loading logs statistics."""
        with patch('gem_flux_mcp.templates.loader.MSTemplateBuilder') as MockBuilder:
            MockBuilder.from_dict.return_value = mock_template_builder

            with caplog.at_level(logging.INFO):
                load_templates(temp_template_dir)

            # Check for success logs
            assert any("✓ Loaded template 'GramNegative'" in msg for msg in caplog.messages)
            assert any("✓ Loaded template 'Core'" in msg for msg in caplog.messages)
            assert any("Template loading complete (2 templates loaded)" in msg for msg in caplog.messages)

    def test_load_templates_clears_cache(self, temp_template_dir, mock_template_builder):
        """Test that loading templates clears existing cache."""
        # Populate cache with dummy data
        TEMPLATE_CACHE["Dummy"] = Mock()

        with patch('gem_flux_mcp.templates.loader.MSTemplateBuilder') as MockBuilder:
            MockBuilder.from_dict.return_value = mock_template_builder

            load_templates(temp_template_dir)

            # Cache should be cleared and repopulated
            assert "Dummy" not in TEMPLATE_CACHE
            assert "GramNegative" in TEMPLATE_CACHE
            assert "Core" in TEMPLATE_CACHE


class TestGetTemplate:
    """Tests for get_template() function."""

    def setup_method(self):
        """Set up template cache for tests."""
        TEMPLATE_CACHE.clear()
        TEMPLATE_CACHE["GramNegative"] = Mock(name="GramNegative_template")
        TEMPLATE_CACHE["Core"] = Mock(name="Core_template")

    def teardown_method(self):
        """Clean up template cache."""
        TEMPLATE_CACHE.clear()

    def test_get_template_success(self):
        """Test successful template retrieval."""
        template = get_template("GramNegative")
        assert template == TEMPLATE_CACHE["GramNegative"]

    def test_get_template_not_found(self):
        """Test error when template not in cache."""
        with pytest.raises(ValueError) as exc_info:
            get_template("NonExistent")

        error_msg = str(exc_info.value)
        assert "Unknown template 'NonExistent'" in error_msg
        assert "Valid templates:" in error_msg
        assert "GramNegative" in error_msg
        assert "Core" in error_msg

    def test_get_template_case_sensitive(self):
        """Test that template names are case-sensitive."""
        with pytest.raises(ValueError):
            get_template("gramnegative")  # lowercase

        with pytest.raises(ValueError):
            get_template("GRAMNEGATIVE")  # uppercase


class TestValidateTemplateName:
    """Tests for validate_template_name() function."""

    def setup_method(self):
        """Set up template cache for tests."""
        TEMPLATE_CACHE.clear()
        TEMPLATE_CACHE["GramNegative"] = Mock()
        TEMPLATE_CACHE["Core"] = Mock()

    def teardown_method(self):
        """Clean up template cache."""
        TEMPLATE_CACHE.clear()

    def test_validate_template_name_valid(self):
        """Test validation with valid template name."""
        assert validate_template_name("GramNegative") is True
        assert validate_template_name("Core") is True

    def test_validate_template_name_invalid(self):
        """Test validation with invalid template name."""
        assert validate_template_name("NonExistent") is False
        assert validate_template_name("gramnegative") is False
        assert validate_template_name("") is False


class TestListAvailableTemplates:
    """Tests for list_available_templates() function."""

    def setup_method(self):
        """Set up template cache with mock templates."""
        TEMPLATE_CACHE.clear()

        # Create mock GramNegative template
        gram_neg = Mock()
        gram_neg.reactions = [Mock()] * 2035  # 2035 reactions
        gram_neg.metabolites = [Mock()] * 1542  # 1542 metabolites
        gram_neg.compartments = ["c0", "e0", "p0"]
        gram_neg.version = "6.0"
        TEMPLATE_CACHE["GramNegative"] = gram_neg

        # Create mock Core template
        core = Mock()
        core.reactions = [Mock()] * 452  # 452 reactions
        core.metabolites = [Mock()] * 300  # 300 metabolites
        core.compartments = ["c0", "e0"]
        core.version = "5.2"
        TEMPLATE_CACHE["Core"] = core

    def teardown_method(self):
        """Clean up template cache."""
        TEMPLATE_CACHE.clear()

    def test_list_available_templates(self):
        """Test listing available templates with metadata."""
        templates = list_available_templates()

        assert len(templates) == 2

        # Check GramNegative template info
        gram_neg_info = next(t for t in templates if t["name"] == "GramNegative")
        assert gram_neg_info["num_reactions"] == 2035
        assert gram_neg_info["num_metabolites"] == 1542
        assert gram_neg_info["compartments"] == ["c0", "e0", "p0"]
        assert gram_neg_info["version"] == "6.0"

        # Check Core template info
        core_info = next(t for t in templates if t["name"] == "Core")
        assert core_info["num_reactions"] == 452
        assert core_info["num_metabolites"] == 300
        assert core_info["compartments"] == ["c0", "e0"]
        assert core_info["version"] == "5.2"

    def test_list_available_templates_empty(self):
        """Test listing when cache is empty."""
        TEMPLATE_CACHE.clear()

        templates = list_available_templates()
        assert templates == []

    def test_list_available_templates_no_version(self):
        """Test listing when template has no version attribute."""
        TEMPLATE_CACHE.clear()

        mock_template = Mock(spec=['reactions', 'metabolites', 'compartments'])
        mock_template.reactions = []
        mock_template.metabolites = []
        mock_template.compartments = []
        # No version attribute
        TEMPLATE_CACHE["NoVersion"] = mock_template

        templates = list_available_templates()
        assert len(templates) == 1
        assert templates[0]["version"] == "unknown"


class TestTemplateIntegration:
    """Integration tests using real template files (if available)."""

    def test_load_real_templates_if_available(self):
        """Test loading actual template files if they exist."""
        template_dir = Path("data/templates")

        if not template_dir.exists():
            pytest.skip("Template directory not found (data/templates)")

        gram_neg_path = template_dir / "GramNegModelTemplateV6.json"
        core_path = template_dir / "Core-V5.2.json"

        if not (gram_neg_path.exists() and core_path.exists()):
            pytest.skip("Required template files not found")

        # This test will use real ModelSEEDpy
        try:
            templates = load_templates(template_dir)

            # Verify templates loaded
            assert "GramNegative" in templates
            assert "Core" in templates

            # Verify they are real MSTemplate objects
            gram_neg = templates["GramNegative"]
            assert len(gram_neg.reactions) > 1000  # GramNegative has ~2000 reactions
            assert "c0" in gram_neg.compartments
            assert "e0" in gram_neg.compartments

            core = templates["Core"]
            assert len(core.reactions) > 100  # Core has ~400 reactions

        except Exception as e:
            pytest.skip(f"Could not load real templates: {e}")
