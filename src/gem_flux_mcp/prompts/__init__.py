"""Centralized prompt management for gem-flux-mcp.

This module provides infrastructure for loading and rendering prompts
from markdown files with YAML frontmatter.
"""

from .loader import load_prompt, render_prompt

__all__ = ["load_prompt", "render_prompt"]
