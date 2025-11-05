"""Unit tests for MCP-to-OpenAI tool converter.

Tests conversion of MCP tool schemas to OpenAI function calling format,
including filtering internal parameters and preserving user-facing parameters.
"""

from unittest.mock import Mock

import pytest

from gem_flux_mcp.argo.converter import MCPToOpenAIConverter


class TestMCPToOpenAIConverter:
    """Test MCP-to-OpenAI tool schema conversion."""

    @pytest.fixture
    def converter(self):
        """Create converter instance for testing."""
        return MCPToOpenAIConverter()

    @pytest.fixture
    def mock_tool_simple(self):
        """Create a simple mock MCP tool (like build_media)."""
        tool = Mock()
        tool.name = "build_media"
        tool.description = "Create growth media from compound list"
        tool.parameters = {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "Unique identifier for media"
                },
                "compounds": {
                    "type": "array",
                    "description": "List of compound IDs",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["media_id", "compounds"]
        }
        return tool

    @pytest.fixture
    def mock_tool_with_internal_params(self):
        """Create mock MCP tool with internal parameters (like get_compound_name)."""
        tool = Mock()
        tool.name = "get_compound_name"
        tool.description = "Get compound name by ID"
        tool.parameters = {
            "type": "object",
            "properties": {
                "compound_id": {
                    "type": "string",
                    "description": "Compound ID (e.g., cpd00027)"
                },
                "db_index": {
                    "type": "object",
                    "description": "Database index (internal)"
                }
            },
            "required": ["compound_id", "db_index"]
        }
        return tool

    @pytest.fixture
    def mock_tool_with_enum(self):
        """Create mock MCP tool with enum parameter (like build_model)."""
        tool = Mock()
        tool.name = "build_model"
        tool.description = "Build metabolic model from genome"
        tool.parameters = {
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "Unique model identifier"
                },
                "genome": {
                    "type": "string",
                    "description": "FASTA genome sequence"
                },
                "template_type": {
                    "type": "string",
                    "description": "Template type for reconstruction",
                    "enum": ["GramNegative", "GramPositive", "Core"]
                },
                "templates": {
                    "type": "object",
                    "description": "Templates dictionary (internal)"
                }
            },
            "required": ["model_id", "genome", "template_type", "templates"]
        }
        return tool

    def test_convert_simple_tool(self, converter, mock_tool_simple):
        """Test conversion of simple tool without internal parameters."""
        result = converter.convert_tool("build_media", mock_tool_simple)

        # Check top-level structure
        assert result["type"] == "function"
        assert "function" in result

        func = result["function"]
        assert func["name"] == "build_media"
        assert func["description"] == "Create growth media from compound list"

        # Check parameters structure
        params = func["parameters"]
        assert params["type"] == "object"
        assert "media_id" in params["properties"]
        assert "compounds" in params["properties"]
        assert params["required"] == ["media_id", "compounds"]

        # Verify parameter details preserved
        assert params["properties"]["media_id"]["type"] == "string"
        assert "Unique identifier" in params["properties"]["media_id"]["description"]

    def test_convert_tool_filters_internal_params(self, converter, mock_tool_with_internal_params):
        """Test that internal parameters are filtered out."""
        result = converter.convert_tool("get_compound_name", mock_tool_with_internal_params)

        params = result["function"]["parameters"]

        # User-facing parameter should be present
        assert "compound_id" in params["properties"]

        # Internal parameter should be removed
        assert "db_index" not in params["properties"]

        # Required list should be filtered
        assert "compound_id" in params["required"]
        assert "db_index" not in params["required"]

    def test_convert_tool_preserves_enum(self, converter, mock_tool_with_enum):
        """Test that enum values are preserved."""
        result = converter.convert_tool("build_model", mock_tool_with_enum)

        params = result["function"]["parameters"]

        # Check enum preserved
        assert "template_type" in params["properties"]
        template_param = params["properties"]["template_type"]
        assert "enum" in template_param
        assert template_param["enum"] == ["GramNegative", "GramPositive", "Core"]

        # Internal parameter should be removed
        assert "templates" not in params["properties"]

    def test_convert_tools_batch(self, converter, mock_tool_simple, mock_tool_with_internal_params):
        """Test converting multiple tools at once."""
        mcp_tools = {
            "build_media": mock_tool_simple,
            "get_compound_name": mock_tool_with_internal_params
        }

        result = converter.convert_tools(mcp_tools)

        # Should return list with 2 tools
        assert len(result) == 2
        assert all(tool["type"] == "function" for tool in result)

        # Check names
        names = {tool["function"]["name"] for tool in result}
        assert names == {"build_media", "get_compound_name"}

    def test_validate_conversion_success(self, converter, mock_tool_simple):
        """Test validation passes for valid OpenAI tools."""
        openai_tool = converter.convert_tool("build_media", mock_tool_simple)

        assert converter.validate_conversion([openai_tool]) is True

    def test_validate_conversion_missing_type(self, converter):
        """Test validation fails for tool missing type field."""
        invalid_tool = {
            "function": {
                "name": "test",
                "description": "test",
                "parameters": {"type": "object", "properties": {}, "required": []}
            }
        }

        assert converter.validate_conversion([invalid_tool]) is False

    def test_validate_conversion_missing_required_in_properties(self, converter):
        """Test validation fails when required param not in properties."""
        invalid_tool = {
            "type": "function",
            "function": {
                "name": "test",
                "description": "test",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"}
                    },
                    "required": ["param1", "param2"]  # param2 doesn't exist
                }
            }
        }

        assert converter.validate_conversion([invalid_tool]) is False

    def test_convert_tool_no_description(self, converter):
        """Test conversion when tool has no description."""
        tool = Mock()
        tool.name = "test_tool"
        tool.description = None
        tool.__doc__ = "Test tool docstring\nSecond line"
        tool.parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }

        result = converter.convert_tool("test_tool", tool)

        # Should use first line of docstring
        assert result["function"]["description"] == "Test tool docstring"

    def test_convert_tool_no_parameters(self, converter):
        """Test conversion when tool has no parameters."""
        tool = Mock()
        tool.name = "test_tool"
        tool.description = "Test description"
        tool.parameters = None

        result = converter.convert_tool("test_tool", tool)

        # Should have empty parameters schema
        params = result["function"]["parameters"]
        assert params["type"] == "object"
        assert params["properties"] == {}
        assert params["required"] == []

    def test_internal_params_constant(self):
        """Test that INTERNAL_PARAMS contains expected parameters."""
        converter = MCPToOpenAIConverter()

        # Verify known internal parameters are in the set
        assert "db_index" in converter.INTERNAL_PARAMS
        assert "templates" in converter.INTERNAL_PARAMS

    def test_convert_tools_handles_conversion_errors(self, converter):
        """Test that convert_tools continues on error."""
        good_tool = Mock()
        good_tool.name = "good_tool"
        good_tool.description = "Good tool"
        good_tool.parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }

        bad_tool = Mock()
        bad_tool.name = "bad_tool"
        # Make get_tool_description raise an exception
        bad_tool.description = None
        bad_tool.__doc__ = None

        # Should only convert the good tool, skip the bad one
        mcp_tools = {
            "good_tool": good_tool,
            "bad_tool": bad_tool
        }

        result = converter.convert_tools(mcp_tools)

        # Should have at least the good tool
        assert len(result) >= 1
        names = {tool["function"]["name"] for tool in result}
        assert "good_tool" in names

    def test_nested_parameter_schema(self, converter):
        """Test conversion of nested parameter schemas."""
        tool = Mock()
        tool.name = "test_tool"
        tool.description = "Test nested params"
        tool.parameters = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "description": "Configuration object",
                    "properties": {
                        "setting1": {
                            "type": "string",
                            "description": "First setting"
                        },
                        "setting2": {
                            "type": "integer",
                            "description": "Second setting"
                        }
                    }
                }
            },
            "required": ["config"]
        }

        result = converter.convert_tool("test_tool", tool)

        # Check nested structure preserved
        params = result["function"]["parameters"]
        assert "config" in params["properties"]
        config = params["properties"]["config"]
        assert config["type"] == "object"
        assert "properties" in config
        assert "setting1" in config["properties"]
        assert "setting2" in config["properties"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
