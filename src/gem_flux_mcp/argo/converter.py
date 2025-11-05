"""Convert MCP tool schemas to OpenAI function calling format.

This module provides conversion logic to transform FastMCP tool schemas
into the OpenAI function calling format required by Argo Gateway.

The converter:
1. Extracts tool metadata (name, description)
2. Converts parameter schemas from MCP to OpenAI format
3. Removes internal parameters (like db_index) that shouldn't be exposed to LLM
4. Preserves user-facing parameters with descriptions and enums
"""

from typing import Any, Dict, List

from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)


class MCPToOpenAIConverter:
    """Convert MCP tools to OpenAI function calling format.

    This converter takes tool schemas from FastMCP's get_tools() method
    and transforms them into the format expected by OpenAI's function calling API.

    Example:
        >>> converter = MCPToOpenAIConverter()
        >>> mcp_tools = await mcp_server.get_tools()
        >>> openai_tools = converter.convert_tools(mcp_tools)
        >>> # Use openai_tools with OpenAI API
    """

    # Internal parameters to exclude from LLM-visible schema
    INTERNAL_PARAMS = {
        "db_index",  # Database index passed by wrapper
        "templates", # Templates dict passed by wrapper
        # Add more as needed
    }

    def convert_tools(self, mcp_tools: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert all MCP tools to OpenAI format.

        Args:
            mcp_tools: Dictionary of MCP tools from FastMCP.get_tools()
                      Format: {tool_name: tool_object, ...}

        Returns:
            List of OpenAI function calling tool definitions
            Format: [{"type": "function", "function": {...}}, ...]

        Example:
            >>> mcp_tools = {"build_media": <MCPTool>, "build_model": <MCPTool>}
            >>> openai_tools = converter.convert_tools(mcp_tools)
            >>> len(openai_tools)
            2
        """
        openai_tools = []

        for tool_name, tool_obj in mcp_tools.items():
            try:
                openai_tool = self.convert_tool(tool_name, tool_obj)
                openai_tools.append(openai_tool)
                logger.debug(f"Converted tool: {tool_name}")
            except Exception as e:
                logger.warning(f"Failed to convert tool {tool_name}: {e}")
                # Continue converting other tools

        logger.info(f"Converted {len(openai_tools)} MCP tools to OpenAI format")
        return openai_tools

    def convert_tool(self, tool_name: str, tool_obj: Any) -> Dict[str, Any]:
        """Convert a single MCP tool to OpenAI format.

        Args:
            tool_name: Name of the tool
            tool_obj: MCP tool object from FastMCP

        Returns:
            OpenAI function calling tool definition

        Example OpenAI format:
            {
                "type": "function",
                "function": {
                    "name": "build_media",
                    "description": "Create growth media...",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "media_id": {
                                "type": "string",
                                "description": "Unique identifier..."
                            }
                        },
                        "required": ["media_id"]
                    }
                }
            }
        """
        # Extract tool metadata
        description = self._get_tool_description(tool_obj)

        # Get parameter schema from MCP tool
        mcp_parameters = self._get_tool_parameters(tool_obj)

        # Convert to OpenAI format and filter internal params
        openai_parameters = self._convert_parameters(mcp_parameters)

        return {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": openai_parameters
            }
        }

    def _get_tool_description(self, tool_obj: Any) -> str:
        """Extract tool description from MCP tool object.

        Args:
            tool_obj: MCP tool object

        Returns:
            Tool description string
        """
        # FastMCP tools have description attribute
        if hasattr(tool_obj, 'description') and tool_obj.description:
            return tool_obj.description

        # Fallback to docstring if available
        if hasattr(tool_obj, '__doc__') and tool_obj.__doc__:
            # Take first line of docstring
            return tool_obj.__doc__.strip().split('\n')[0]

        # Last resort
        return f"Execute {getattr(tool_obj, 'name', 'tool')}"

    def _get_tool_parameters(self, tool_obj: Any) -> Dict[str, Any]:
        """Extract parameter schema from MCP tool object.

        Args:
            tool_obj: MCP tool object

        Returns:
            Parameter schema dictionary (MCP format)
        """
        # FastMCP tools have parameters attribute (JSON schema)
        if hasattr(tool_obj, 'parameters') and tool_obj.parameters:
            return tool_obj.parameters

        # Return empty schema if no parameters
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def _convert_parameters(self, mcp_params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP parameter schema to OpenAI format.

        This method:
        1. Filters out internal parameters
        2. Preserves user-facing parameters
        3. Maintains descriptions and enum values
        4. Ensures proper JSON schema structure

        Args:
            mcp_params: MCP parameter schema (JSON schema format)

        Returns:
            OpenAI-compatible parameter schema
        """
        # Start with base structure
        openai_params = {
            "type": "object",
            "properties": {},
            "required": []
        }

        # Get properties and required list
        properties = mcp_params.get("properties", {})
        required = mcp_params.get("required", [])

        # Filter properties - remove internal parameters
        for param_name, param_schema in properties.items():
            if param_name not in self.INTERNAL_PARAMS:
                # Copy parameter schema (preserving description, enum, etc.)
                openai_params["properties"][param_name] = self._copy_parameter_schema(
                    param_schema
                )

        # Filter required list - remove internal parameters
        openai_params["required"] = [
            param for param in required
            if param not in self.INTERNAL_PARAMS
        ]

        return openai_params

    def _copy_parameter_schema(self, param_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Deep copy parameter schema, preserving all fields.

        Args:
            param_schema: Parameter schema from MCP tool

        Returns:
            Copied parameter schema safe for OpenAI API
        """
        # Copy all fields (type, description, enum, etc.)
        copied = {}

        for key, value in param_schema.items():
            # Handle nested objects/arrays recursively if needed
            if key == "properties" and isinstance(value, dict):
                copied[key] = {
                    k: self._copy_parameter_schema(v)
                    for k, v in value.items()
                }
            elif key == "items" and isinstance(value, dict):
                copied[key] = self._copy_parameter_schema(value)
            else:
                # Simple copy for primitives, lists, etc.
                copied[key] = value

        return copied

    def validate_conversion(self, openai_tools: List[Dict[str, Any]]) -> bool:
        """Validate that converted tools follow OpenAI schema.

        Args:
            openai_tools: List of converted OpenAI tool definitions

        Returns:
            True if all tools are valid, False otherwise

        Validation checks:
        - Each tool has "type" and "function"
        - Function has "name", "description", "parameters"
        - Parameters have "type", "properties", "required"
        """
        try:
            for tool in openai_tools:
                # Check top-level structure
                assert tool.get("type") == "function", "Tool must have type='function'"
                assert "function" in tool, "Tool must have 'function' key"

                func = tool["function"]

                # Check function structure
                assert "name" in func, "Function must have 'name'"
                assert "description" in func, "Function must have 'description'"
                assert "parameters" in func, "Function must have 'parameters'"

                params = func["parameters"]

                # Check parameters structure
                assert params.get("type") == "object", "Parameters must be type='object'"
                assert "properties" in params, "Parameters must have 'properties'"
                assert "required" in params, "Parameters must have 'required'"

                # Verify required params exist in properties
                for req_param in params["required"]:
                    assert req_param in params["properties"], \
                        f"Required parameter '{req_param}' not in properties"

            logger.info(f"Validated {len(openai_tools)} OpenAI tools")
            return True

        except AssertionError as e:
            logger.error(f"Tool validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Tool validation error: {e}")
            return False
