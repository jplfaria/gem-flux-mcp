"""Integration tests for MCP tool registration and accessibility.

Tests that all 11 tools are properly registered via @mcp.tool() decorators
and accessible through the FastMCP server instance.
"""

import pytest
import pytest_asyncio

from gem_flux_mcp.server import create_server, initialize_server


@pytest_asyncio.fixture(scope="module")
async def mcp_server():
    """Initialize server and return MCP instance for testing."""
    # Initialize global state (database, templates)
    initialize_server()

    # Create server with auto-registered tools
    server = create_server()

    return server


@pytest_asyncio.fixture(scope="module")
async def tools_dict(mcp_server):
    """Get dictionary of tools from FastMCP server using async API."""
    # FastMCP's get_tools() is async and returns a dict
    tools = await mcp_server.get_tools()
    return tools


class TestMCPToolRegistration:
    """Test MCP tool registration and accessibility."""

    @pytest.mark.asyncio
    async def test_server_instance_created(self, mcp_server):
        """Test that MCP server instance is created successfully."""
        assert mcp_server is not None
        assert hasattr(mcp_server, 'name')
        assert mcp_server.name == "gem-flux-mcp"

    @pytest.mark.asyncio
    async def test_all_tools_registered(self, tools_dict):
        """Test that all 11 tools are registered in the MCP server."""
        # Expected tool names (all 11 tools)
        expected_tools = {
            "build_media",
            "build_model",
            "gapfill_model",
            "run_fba",
            "get_compound_name",
            "get_reaction_name",
            "search_compounds",
            "search_reactions",
            "list_models",
            "delete_model",
            "list_media",
        }

        # Get registered tool names from tools dictionary
        registered_tool_names = set(tools_dict.keys())

        # Verify all expected tools are registered
        assert expected_tools.issubset(registered_tool_names), \
            f"Missing tools: {expected_tools - registered_tool_names}"

    @pytest.mark.asyncio
    async def test_tool_has_schema(self, tools_dict):
        """Test that registered tools have proper JSON schemas."""
        # Get build_media tool from dictionary
        build_media_tool = tools_dict.get("build_media")

        assert build_media_tool is not None, "build_media tool not found"

        # FastMCP tools should have parameters attribute (JSON schema for inputs)
        assert hasattr(build_media_tool, 'parameters'), "Tool missing parameters"
        assert build_media_tool.parameters is not None, "Tool parameters is None"

        # Verify it's a dictionary with required fields for JSON schema
        assert isinstance(build_media_tool.parameters, dict), "Parameters should be dict"
        assert 'type' in build_media_tool.parameters or 'properties' in build_media_tool.parameters, \
            "Parameters should contain JSON schema fields"

    @pytest.mark.asyncio
    async def test_database_lookup_tools_registered(self, tools_dict):
        """Test that database lookup tools are registered."""
        lookup_tools = [
            "get_compound_name",
            "get_reaction_name",
            "search_compounds",
            "search_reactions",
        ]

        registered_names = set(tools_dict.keys())

        for tool_name in lookup_tools:
            assert tool_name in registered_names, \
                f"Database lookup tool '{tool_name}' not registered"

    @pytest.mark.asyncio
    async def test_model_building_tools_registered(self, tools_dict):
        """Test that model building tools are registered."""
        model_tools = [
            "build_model",
            "gapfill_model",
            "run_fba",
        ]

        registered_names = set(tools_dict.keys())

        for tool_name in model_tools:
            assert tool_name in registered_names, \
                f"Model building tool '{tool_name}' not registered"

    @pytest.mark.asyncio
    async def test_session_management_tools_registered(self, tools_dict):
        """Test that session management tools are registered."""
        session_tools = [
            "list_models",
            "delete_model",
            "list_media",
        ]

        registered_names = set(tools_dict.keys())

        for tool_name in session_tools:
            assert tool_name in registered_names, \
                f"Session management tool '{tool_name}' not registered"

    @pytest.mark.asyncio
    async def test_media_building_tool_registered(self, tools_dict):
        """Test that media building tool is registered."""
        registered_names = set(tools_dict.keys())
        assert "build_media" in registered_names, "build_media tool not registered"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
