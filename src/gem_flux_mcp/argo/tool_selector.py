"""Dynamic tool selection for Argo LLM integration.

This module implements intelligent tool selection to work around Argo's payload
size limits (~40KB for all tools). Instead of loading all 11 tools at once,
we select 3-4 relevant tools based on the user's query using keyword matching.

Architecture:
    User Query → Tool Selector → 3-4 Relevant Tools → Argo LLM
"""

import re
from typing import List, Set

from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)


class ToolSelector:
    """Selects relevant tools based on user query keywords.

    Tool Categories:
    - Database: Compound/reaction lookups and searches
    - Media: Building and managing growth media
    - Model: Building, listing, deleting metabolic models
    - Analysis: Gapfilling and FBA simulations

    Strategy:
        Each query gets 3-4 tools:
        - Always include database tools (for looking up IDs)
        - Add category-specific tools based on keywords
        - Keep total under 6 tools (~15KB, well under 40KB limit)
    """

    # Tool categories with their tools
    TOOL_CATEGORIES = {
        "database": {
            "get_compound_name",
            "get_reaction_name",
            "search_compounds",
            "search_reactions",
        },
        "media": {"build_media", "list_media"},
        "model": {"build_model", "list_models", "delete_model"},
        "analysis": {"gapfill_model", "run_fba"},
    }

    # Keywords that trigger each category
    CATEGORY_KEYWORDS = {
        "database": {
            "compound",
            "cpd",
            "reaction",
            "rxn",
            "formula",
            "molecular",
            "search",
            "find",
            "lookup",
            "what is",
            "tell me about",
            "glucose",
            "atp",
            "metabolite",
            "enzyme",
        },
        "media": {
            "media",
            "medium",
            "growth",
            "nutrients",
            "feed",
            "supplement",
            "composition",
            "uptake",
            "bounds",
        },
        "model": {
            "model",
            "build",
            "construct",
            "create",
            "genome",
            "fasta",
            "template",
            "reconstruction",
            "draft",
            "list models",
            "delete",
        },
        "analysis": {
            "gapfill",
            "gap",
            "fill",
            "fba",
            "flux",
            "balance",
            "analysis",
            "simulate",
            "growth rate",
            "optimize",
            "objective",
        },
    }

    def __init__(self, max_tools: int = 6):
        """Initialize tool selector.

        Args:
            max_tools: Maximum number of tools to select (default: 6)
                      6 tools ≈ 15KB, well under 40KB Argo limit
        """
        self.max_tools = max_tools
        logger.info(f"ToolSelector initialized with max_tools={max_tools}")

    def select_tools(self, query: str, available_tools: Set[str]) -> List[str]:
        """Select relevant tools for a query.

        Args:
            query: User's natural language query
            available_tools: Set of all available tool names

        Returns:
            List of selected tool names (3-6 tools)

        Strategy:
            1. Always include 2 database tools (lookups are common)
            2. Detect categories from keywords
            3. Add tools from detected categories
            4. Cap at max_tools
        """
        query_lower = query.lower()
        selected = set()

        # Step 1: Always include core database tools (for ID lookups)
        core_db_tools = {"get_compound_name", "get_reaction_name"}
        selected.update(core_db_tools & available_tools)

        # Step 2: Detect categories from keywords
        detected_categories = self._detect_categories(query_lower)
        logger.info(f"Detected categories for query: {detected_categories}")

        # Step 3: Add tools from detected categories (in priority order)
        priority_order = ["analysis", "model", "media", "database"]

        for category in priority_order:
            if category in detected_categories:
                category_tools = self.TOOL_CATEGORIES[category] & available_tools
                # Add tools from this category until we hit max
                for tool in category_tools:
                    if len(selected) >= self.max_tools:
                        break
                    selected.add(tool)

        # Step 4: If still under limit, add database search tools
        if len(selected) < self.max_tools:
            search_tools = {"search_compounds", "search_reactions"} & available_tools
            selected.update(list(search_tools)[: self.max_tools - len(selected)])

        selected_list = list(selected)
        logger.info(f"Selected {len(selected_list)} tools: {selected_list}")
        return selected_list

    def _detect_categories(self, query_lower: str) -> Set[str]:
        """Detect relevant categories from query keywords.

        Args:
            query_lower: Lowercased query string

        Returns:
            Set of detected category names
        """
        detected = set()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                # Use word boundaries to avoid partial matches
                pattern = r"\b" + re.escape(keyword) + r"\b"
                if re.search(pattern, query_lower):
                    detected.add(category)
                    break  # One match is enough for this category

        # Always include database for lookups
        detected.add("database")

        return detected

    def get_category_for_tool(self, tool_name: str) -> str:
        """Get category name for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Category name, or "unknown" if not found
        """
        for category, tools in self.TOOL_CATEGORIES.items():
            if tool_name in tools:
                return category
        return "unknown"
