"""Prompt loader for centralized markdown prompts with YAML frontmatter."""

import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, Template

from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)

# Cache for loaded prompts
_prompt_cache: Dict[str, tuple[Dict[str, Any], str]] = {}
_jinja_env: Optional[Environment] = None


def _get_prompts_dir() -> Path:
    """Get the prompts directory path."""
    # prompts/ at repo root
    return Path(__file__).parent.parent.parent.parent / "prompts"


def _get_jinja_env() -> Environment:
    """Get or create Jinja2 environment."""
    global _jinja_env
    if _jinja_env is None:
        prompts_dir = _get_prompts_dir()
        _jinja_env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=False,  # We control the templates
            trim_blocks=True,
            lstrip_blocks=True,
        )
    return _jinja_env


def _parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (metadata dict, content without frontmatter)
    """
    # Match YAML frontmatter: ---\n...yaml...\n---
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if match:
        yaml_content = match.group(1)
        markdown_content = match.group(2)

        try:
            metadata = yaml.safe_load(yaml_content)
            return metadata or {}, markdown_content.strip()
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse YAML frontmatter: {e}")
            return {}, content

    # No frontmatter found
    return {}, content


def load_prompt(prompt_path: str) -> tuple[Dict[str, Any], str]:
    """Load a prompt from markdown file with YAML frontmatter.

    Args:
        prompt_path: Path to prompt file relative to prompts/ directory
                    (without .md extension)
                    Example: "interpretations/gapfill_model"

    Returns:
        Tuple of (metadata dict, template content)

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    # Check cache first
    if prompt_path in _prompt_cache:
        return _prompt_cache[prompt_path]

    # Load from file
    prompts_dir = _get_prompts_dir()
    file_path = prompts_dir / f"{prompt_path}.md"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {file_path}\n"
            f"Looking for: {prompt_path}.md in {prompts_dir}"
        )

    logger.debug(f"Loading prompt from {file_path}")
    content = file_path.read_text(encoding="utf-8")

    metadata, template_content = _parse_frontmatter(content)

    # Cache the result
    _prompt_cache[prompt_path] = (metadata, template_content)

    return metadata, template_content


def render_prompt(prompt_path: str, **variables) -> str:
    """Load and render a prompt template with variables.

    Args:
        prompt_path: Path to prompt file relative to prompts/ directory
        **variables: Variables to pass to template rendering

    Returns:
        Rendered prompt as string

    Raises:
        FileNotFoundError: If prompt file doesn't exist

    Example:
        >>> result = render_prompt(
        ...     "interpretations/gapfill_model",
        ...     num_reactions=5,
        ...     gapfilling_successful=True
        ... )
    """
    metadata, template_content = load_prompt(prompt_path)

    # Create Jinja2 template
    from jinja2 import StrictUndefined
    template = Template(template_content, undefined=StrictUndefined)

    # Render with variables
    try:
        rendered = template.render(**variables)
        return rendered.strip()
    except Exception as e:
        logger.error(f"Failed to render prompt {prompt_path}: {e}")
        logger.error(f"Variables provided: {list(variables.keys())}")
        raise


def clear_cache():
    """Clear the prompt cache. Useful for testing or hot-reload."""
    global _prompt_cache, _jinja_env
    _prompt_cache.clear()
    _jinja_env = None
    logger.debug("Prompt cache cleared")
