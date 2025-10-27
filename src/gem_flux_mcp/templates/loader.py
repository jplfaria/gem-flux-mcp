"""
Template loader module for ModelSEED template management.

This module provides functions to load ModelSEED template files at server startup
and access them during runtime. Templates define the reaction sets available for
template-based metabolic model construction.

According to spec 017-template-management.md:
- Templates loaded at server startup from data/templates/ directory
- Cached in memory for fast O(1) access
- Pre-loaded templates: GramNegative (required), Core (required), GramPositive (optional)
- Server fails to start if required templates missing
"""

import json
import logging
from pathlib import Path
from typing import Any

from modelseedpy.core.mstemplate import MSTemplate, MSTemplateBuilder

from gem_flux_mcp.errors import DatabaseError

logger = logging.getLogger(__name__)


# Template file mapping (spec 017)
TEMPLATE_FILES = {
    "GramNegative": "GramNegModelTemplateV6.json",
    "GramPositive": "GramPosModelTemplateV6.json",  # Optional
    "Core": "Core-V5.2.json",
}

# Required templates for server operation (spec 017)
REQUIRED_TEMPLATES = ["GramNegative", "Core"]

# Global template cache (populated at startup)
TEMPLATE_CACHE: dict[str, MSTemplate] = {}


def load_template(template_path: Path, template_name: str) -> MSTemplate:
    """Load a single ModelSEED template from JSON file.

    Args:
        template_path: Path to template JSON file
        template_name: Name of template (e.g., "GramNegative")

    Returns:
        MSTemplate object ready for model building

    Raises:
        DatabaseError: If template file missing, invalid JSON, or build fails
    """
    # Verify file exists
    if not template_path.exists():
        raise DatabaseError(
            message=f"Template file not found: {template_path}\n"
                    f"Template '{template_name}' file is missing.",
            error_code="TEMPLATE_FILE_NOT_FOUND"
        )

    # Load and parse JSON
    try:
        with open(template_path, 'r') as fh:
            template_dict = json.load(fh)
    except json.JSONDecodeError as e:
        raise DatabaseError(
            message=f"Invalid JSON in {template_path}: {e}\n"
                    f"The template file appears to be corrupted.",
            error_code="INVALID_TEMPLATE_JSON"
        )
    except Exception as e:
        raise DatabaseError(
            message=f"Failed to read template file {template_path}: {e}",
            error_code="TEMPLATE_READ_ERROR"
        )

    # Build MSTemplate object using ModelSEEDpy
    try:
        template = MSTemplateBuilder.from_dict(template_dict).build()
    except Exception as e:
        raise DatabaseError(
            message=f"Failed to build template '{template_name}': {e}\n"
                    "This may indicate a template version mismatch or corrupted file.",
            error_code="TEMPLATE_BUILD_FAILED"
        )

    return template


def load_templates(template_dir: Path | str | None = None) -> dict[str, MSTemplate]:
    """Load all ModelSEED templates at server startup.

    This function:
    1. Verifies template directory exists
    2. Loads required templates (GramNegative, Core)
    3. Attempts to load optional templates (GramPositive)
    4. Caches templates in TEMPLATE_CACHE global
    5. Logs loading statistics

    Args:
        template_dir: Path to templates directory (default: data/templates)

    Returns:
        Dict mapping template names to MSTemplate objects

    Raises:
        DatabaseError: If template directory missing or required templates fail to load
    """
    # Default template directory
    if template_dir is None:
        template_dir = Path("data/templates")
    else:
        template_dir = Path(template_dir)

    # Verify directory exists
    if not template_dir.exists():
        raise DatabaseError(
            message=f"Template directory not found: {template_dir}\n\n"
                    "The server requires ModelSEED template files to operate.\n\n"
                    "To fix:\n"
                    "1. Create directory: mkdir -p data/templates\n"
                    "2. Download required templates:\n"
                    "   - GramNegModelTemplateV6.json\n"
                    "   - Core-V5.2.json\n"
                    "3. Place templates in data/templates/\n"
                    "4. Restart server\n\n"
                    "See docs/template-installation.md for detailed instructions.",
            error_code="TEMPLATE_DIRECTORY_NOT_FOUND"
        )

    templates = {}

    # Load each template
    for template_name, filename in TEMPLATE_FILES.items():
        filepath = template_dir / filename

        # Check if file exists
        if not filepath.exists():
            if template_name in REQUIRED_TEMPLATES:
                raise DatabaseError(
                    message=f"Required template missing: {filepath}\n\n"
                            f"Template '{template_name}' is required for server operation.\n\n"
                            "To fix:\n"
                            f"1. Download {filename} from ModelSEED\n"
                            "2. Place in data/templates/\n"
                            "3. Verify file integrity (valid JSON)\n"
                            "4. Restart server\n\n"
                            "Template source: https://github.com/ModelSEED/ModelSEEDDatabase",
                    error_code="REQUIRED_TEMPLATE_MISSING"
                )
            else:
                logger.warning(f"Optional template '{template_name}' not found at {filepath}, skipping")
                continue

        # Load template
        try:
            template = load_template(filepath, template_name)
            templates[template_name] = template

            # Log success with statistics
            num_reactions = len(template.reactions)
            logger.info(f"✓ Loaded template '{template_name}': {num_reactions} reactions")

        except DatabaseError as e:
            if template_name in REQUIRED_TEMPLATES:
                # Re-raise for required templates
                raise
            else:
                # Log warning for optional templates
                logger.warning(f"Failed to load optional template '{template_name}': {e}")

    # Verify at least one template loaded
    if not templates:
        raise DatabaseError(
            message="No templates successfully loaded. Cannot start server.\n"
                    "At least one template (GramNegative or Core) is required.",
            error_code="NO_TEMPLATES_LOADED"
        )

    # Update global cache
    TEMPLATE_CACHE.clear()
    TEMPLATE_CACHE.update(templates)

    logger.info(f"Template loading complete ({len(templates)} templates loaded)")

    return templates


def get_template(template_name: str) -> MSTemplate:
    """Get cached template by name.

    This function provides O(1) runtime access to pre-loaded templates.

    Args:
        template_name: One of "GramNegative", "GramPositive", "Core"

    Returns:
        MSTemplate object

    Raises:
        ValueError: If template name unknown or not loaded
    """
    if template_name not in TEMPLATE_CACHE:
        valid_names = list(TEMPLATE_CACHE.keys())
        raise ValueError(
            f"Unknown template '{template_name}'. "
            f"Valid templates: {valid_names}"
        )

    return TEMPLATE_CACHE[template_name]


def validate_template_name(template_name: str) -> bool:
    """Check if template name is valid and available.

    Args:
        template_name: Template name to validate

    Returns:
        True if valid and available, False otherwise
    """
    return template_name in TEMPLATE_CACHE


def list_available_templates() -> list[dict[str, Any]]:
    """List all available templates with metadata.

    Returns:
        List of dicts with template info (name, num_reactions, num_metabolites, etc.)
    """
    templates_info = []

    for name, template in TEMPLATE_CACHE.items():
        templates_info.append({
            "name": name,
            "num_reactions": len(template.reactions),
            "num_metabolites": len(template.metabolites),
            "compartments": template.compartments,
            "version": getattr(template, 'version', 'unknown')
        })

    return templates_info
