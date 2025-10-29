# MCP to OpenAI Tool Conversion Specification

**Type**: MCP Integration Specification
**Status**: Phase 11.5 - Argo LLM Integration
**Version**: MVP v0.1.0
**Depends On**: 021-mcp-tool-registration.md

## Prerequisites

- Read: **021-mcp-tool-registration.md** (MCP tool definitions)
- Read: **022-argo-llm-integration.md** (ArgoMCPClient context)
- Understand: JSON Schema format
- Understand: OpenAI function calling specification
- Understand: MCP protocol tool schema format

## Purpose

This specification defines the MCPToOpenAIConverter class that converts MCP tool definitions to OpenAI function calling format. This conversion is necessary because Argo Gateway (via OpenAI API) expects a different schema format than what MCP servers provide.

## Problem Statement

**Schema Format Mismatch**:
- MCP servers define tools using MCP protocol schema format
- Argo Gateway expects OpenAI function calling format
- Direct use causes schema validation errors
- LLMs cannot understand tool definitions without conversion

**Key Differences**:
1. MCP uses `inputSchema`, OpenAI uses `parameters`
2. MCP allows `default` in properties, OpenAI does not support it
3. OpenAI requires wrapper with `{"type": "function", "function": {...}}`
4. Nested differences in schema structure

## Architecture Solution

### Conversion Flow

```
┌─────────────────────┐
│   MCP Server        │
│   (FastMCP)         │
└──────┬──────────────┘
       │
       │ session.list_tools()
       ▼
┌─────────────────────┐
│  MCP Tool Schema    │  {
│                     │    "name": "build_model",
│                     │    "description": "...",
│                     │    "inputSchema": {...}
│                     │  }
└──────┬──────────────┘
       │
       │ MCPToOpenAIConverter.convert_tool()
       ▼
┌─────────────────────┐
│ OpenAI Tool Schema  │  {
│                     │    "type": "function",
│                     │    "function": {
│                     │      "name": "build_model",
│                     │      "description": "...",
│                     │      "parameters": {...}
│                     │    }
│                     │  }
└──────┬──────────────┘
       │
       │ Pass to LLM
       ▼
┌─────────────────────┐
│  Argo Gateway LLM   │
└─────────────────────┘
```

### Schema Comparison

**MCP Format**:
```json
{
  "name": "build_model",
  "description": "Build a metabolic model from genome annotation",
  "inputSchema": {
    "type": "object",
    "properties": {
      "model_id": {
        "type": "string",
        "description": "Unique identifier with .gf suffix"
      },
      "template": {
        "type": "string",
        "description": "Template name",
        "default": "auto"
      }
    },
    "required": ["model_id"]
  }
}
```

**OpenAI Format**:
```json
{
  "type": "function",
  "function": {
    "name": "build_model",
    "description": "Build a metabolic model from genome annotation",
    "parameters": {
      "type": "object",
      "properties": {
        "model_id": {
          "type": "string",
          "description": "Unique identifier with .gf suffix"
        },
        "template": {
          "type": "string",
          "description": "Template name"
        }
      },
      "required": ["model_id"]
    }
  }
}
```

**Changes Made**:
1. Wrapped in `{"type": "function", "function": {...}}`
2. Renamed `inputSchema` → `parameters`
3. Removed `"default": "auto"` from template property

## MCPToOpenAIConverter Specification

### Class Definition

```python
class MCPToOpenAIConverter:
    """Converts MCP tool schemas to OpenAI function calling format.

    This class provides static methods for converting individual tools
    or lists of tools from MCP format to OpenAI format.

    The conversion handles:
    - Schema structure transformation (inputSchema → parameters)
    - Removal of unsupported fields (default values)
    - Wrapper addition (type: function)
    - Deep copying to avoid mutating original schemas
    """
```

### Primary Methods

#### convert_tool

```python
@staticmethod
def convert_tool(mcp_tool: dict) -> dict:
    """Convert single MCP tool to OpenAI format.

    Args:
        mcp_tool: MCP tool schema with keys:
            - name: str - Tool name
            - description: str - Tool description
            - inputSchema: dict - JSON Schema for parameters

    Returns:
        OpenAI tool definition with structure:
        {
            "type": "function",
            "function": {
                "name": str,
                "description": str,
                "parameters": dict  # JSON Schema
            }
        }

    Example:
        >>> mcp_tool = {
        ...     "name": "build_model",
        ...     "description": "Build a model",
        ...     "inputSchema": {
        ...         "type": "object",
        ...         "properties": {"model_id": {"type": "string"}},
        ...         "required": ["model_id"]
        ...     }
        ... }
        >>> openai_tool = MCPToOpenAIConverter.convert_tool(mcp_tool)
        >>> openai_tool["type"]
        'function'
        >>> openai_tool["function"]["name"]
        'build_model'
    """
```

Implementation requirements:
1. Deep copy `mcp_tool["inputSchema"]` to avoid mutations
2. Call `_remove_defaults()` on copied parameters
3. Return OpenAI format with `type: "function"` wrapper
4. Preserve all other schema fields (enum, required, etc.)

#### convert_all_tools

```python
@staticmethod
def convert_all_tools(mcp_tools: list[dict]) -> list[dict]:
    """Convert list of MCP tools to OpenAI format.

    Args:
        mcp_tools: List of MCP tool schemas

    Returns:
        List of OpenAI tool definitions

    Example:
        >>> mcp_tools = [
        ...     {"name": "tool1", "description": "...", "inputSchema": {...}},
        ...     {"name": "tool2", "description": "...", "inputSchema": {...}}
        ... ]
        >>> openai_tools = MCPToOpenAIConverter.convert_all_tools(mcp_tools)
        >>> len(openai_tools)
        2
        >>> all(tool["type"] == "function" for tool in openai_tools)
        True
    """
```

Implementation:
```python
return [
    MCPToOpenAIConverter.convert_tool(tool)
    for tool in mcp_tools
]
```

### Helper Methods

#### _remove_defaults

```python
@staticmethod
def _remove_defaults(schema: dict) -> None:
    """Remove 'default' keys from schema (OpenAI doesn't support them).

    Mutates schema in place. Recursively processes nested objects.

    Args:
        schema: JSON Schema dict (will be modified)

    Example:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "param1": {"type": "string", "default": "value"}
        ...     }
        ... }
        >>> MCPToOpenAIConverter._remove_defaults(schema)
        >>> "default" in schema["properties"]["param1"]
        False
    """
```

Implementation algorithm:
1. Check if schema has `"properties"` key
2. For each property in properties:
   - If property has `"default"` key, delete it
   - If property is nested object (`"type": "object"`), recurse
3. Handle nested schemas in:
   - `items` (for arrays)
   - `additionalProperties` (for maps)
   - `anyOf`, `oneOf`, `allOf` (for unions)

Complete implementation:
```python
@staticmethod
def _remove_defaults(schema: dict) -> None:
    """Remove 'default' keys from schema recursively."""

    # Remove defaults from properties
    if "properties" in schema:
        for prop_schema in schema["properties"].values():
            if "default" in prop_schema:
                del prop_schema["default"]

            # Recurse for nested objects
            if prop_schema.get("type") == "object":
                MCPToOpenAIConverter._remove_defaults(prop_schema)

            # Recurse for arrays
            if prop_schema.get("type") == "array" and "items" in prop_schema:
                if isinstance(prop_schema["items"], dict):
                    MCPToOpenAIConverter._remove_defaults(prop_schema["items"])

    # Handle additionalProperties
    if "additionalProperties" in schema and isinstance(schema["additionalProperties"], dict):
        MCPToOpenAIConverter._remove_defaults(schema["additionalProperties"])

    # Handle anyOf/oneOf/allOf
    for key in ["anyOf", "oneOf", "allOf"]:
        if key in schema:
            for subschema in schema[key]:
                if isinstance(subschema, dict):
                    MCPToOpenAIConverter._remove_defaults(subschema)
```

## Conversion Rules

### Rule 1: Structure Transformation

**Input** (MCP format):
```json
{
  "name": "tool_name",
  "description": "tool description",
  "inputSchema": { ... }
}
```

**Output** (OpenAI format):
```json
{
  "type": "function",
  "function": {
    "name": "tool_name",
    "description": "tool description",
    "parameters": { ... }
  }
}
```

### Rule 2: Default Value Removal

**Input** (MCP format):
```json
{
  "properties": {
    "param": {
      "type": "string",
      "description": "A parameter",
      "default": "default_value"
    }
  }
}
```

**Output** (OpenAI format):
```json
{
  "properties": {
    "param": {
      "type": "string",
      "description": "A parameter"
    }
  }
}
```

**Rationale**: OpenAI function calling does not support `default` in JSON Schema. Default values are documented in descriptions instead.

### Rule 3: Preserve Other Fields

The following fields are preserved without modification:
- `type` (string, number, boolean, object, array, null)
- `enum` (allowed values)
- `required` (required parameter list)
- `description` (parameter descriptions)
- `items` (for arrays)
- `properties` (for objects)
- `additionalProperties` (for maps)
- `anyOf`, `oneOf`, `allOf` (for unions)

### Rule 4: Deep Copy

Original MCP tool schemas MUST NOT be modified:
```python
# WRONG - modifies original
parameters = mcp_tool["inputSchema"]
del parameters["properties"]["param"]["default"]

# CORRECT - works on copy
import json
parameters = json.loads(json.dumps(mcp_tool["inputSchema"]))
del parameters["properties"]["param"]["default"]
```

## Edge Cases

### Empty Tools List

```python
mcp_tools = []
openai_tools = MCPToOpenAIConverter.convert_all_tools(mcp_tools)
assert openai_tools == []
```

### Tool with No Parameters

**Input**:
```json
{
  "name": "list_models",
  "description": "List all models",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

**Output**:
```json
{
  "type": "function",
  "function": {
    "name": "list_models",
    "description": "List all models",
    "parameters": {
      "type": "object",
      "properties": {}
    }
  }
}
```

### Tool with Enum

**Input**:
```json
{
  "properties": {
    "genome_source": {
      "type": "string",
      "enum": ["rast_id", "fasta_file", "annotation_dict"],
      "description": "Source type"
    }
  }
}
```

**Output** (enum preserved):
```json
{
  "properties": {
    "genome_source": {
      "type": "string",
      "enum": ["rast_id", "fasta_file", "annotation_dict"],
      "description": "Source type"
    }
  }
}
```

### Nested Objects with Defaults

**Input**:
```json
{
  "properties": {
    "options": {
      "type": "object",
      "properties": {
        "timeout": {
          "type": "number",
          "default": 30
        }
      }
    }
  }
}
```

**Output** (nested default removed):
```json
{
  "properties": {
    "options": {
      "type": "object",
      "properties": {
        "timeout": {
          "type": "number"
        }
      }
    }
  }
}
```

## Testing Requirements

### Unit Tests

**test_mcp_to_openai_converter.py**:

```python
def test_convert_basic_tool():
    """Test basic tool conversion."""
    mcp_tool = {
        "name": "test_tool",
        "description": "A test tool",
        "inputSchema": {
            "type": "object",
            "properties": {
                "param1": {"type": "string"}
            }
        }
    }

    result = MCPToOpenAIConverter.convert_tool(mcp_tool)

    assert result["type"] == "function"
    assert result["function"]["name"] == "test_tool"
    assert result["function"]["parameters"]["properties"]["param1"]["type"] == "string"


def test_removes_default_values():
    """Test that default values are removed."""
    mcp_tool = {
        "name": "test_tool",
        "description": "Test",
        "inputSchema": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "default": "value"
                }
            }
        }
    }

    result = MCPToOpenAIConverter.convert_tool(mcp_tool)

    assert "default" not in result["function"]["parameters"]["properties"]["param1"]


def test_preserves_enum():
    """Test that enum is preserved."""
    mcp_tool = {
        "name": "test_tool",
        "description": "Test",
        "inputSchema": {
            "type": "object",
            "properties": {
                "choice": {
                    "type": "string",
                    "enum": ["a", "b", "c"]
                }
            }
        }
    }

    result = MCPToOpenAIConverter.convert_tool(mcp_tool)

    assert result["function"]["parameters"]["properties"]["choice"]["enum"] == ["a", "b", "c"]


def test_deep_copy():
    """Test that original schema is not modified."""
    mcp_tool = {
        "name": "test_tool",
        "description": "Test",
        "inputSchema": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "default": "value"
                }
            }
        }
    }

    result = MCPToOpenAIConverter.convert_tool(mcp_tool)

    # Original should still have default
    assert "default" in mcp_tool["inputSchema"]["properties"]["param1"]
    # Converted should not have default
    assert "default" not in result["function"]["parameters"]["properties"]["param1"]


def test_convert_all_tools():
    """Test converting multiple tools."""
    mcp_tools = [
        {
            "name": "tool1",
            "description": "First tool",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "tool2",
            "description": "Second tool",
            "inputSchema": {"type": "object", "properties": {}}
        }
    ]

    result = MCPToOpenAIConverter.convert_all_tools(mcp_tools)

    assert len(result) == 2
    assert result[0]["function"]["name"] == "tool1"
    assert result[1]["function"]["name"] == "tool2"


def test_nested_objects():
    """Test conversion with nested object properties."""
    mcp_tool = {
        "name": "test_tool",
        "description": "Test",
        "inputSchema": {
            "type": "object",
            "properties": {
                "options": {
                    "type": "object",
                    "properties": {
                        "nested_param": {
                            "type": "string",
                            "default": "nested_value"
                        }
                    }
                }
            }
        }
    }

    result = MCPToOpenAIConverter.convert_tool(mcp_tool)

    # Nested default should be removed
    nested = result["function"]["parameters"]["properties"]["options"]["properties"]["nested_param"]
    assert "default" not in nested
```

### Integration Tests

**test_converter_with_real_mcp_tools.py**:

```python
@pytest.mark.asyncio
async def test_convert_real_mcp_tools():
    """Test conversion with actual MCP server tools."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    # Connect to MCP server
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "gem-flux-mcp"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Get real tools
            tools_result = await session.list_tools()
            mcp_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools_result.tools
            ]

            # Convert all tools
            openai_tools = MCPToOpenAIConverter.convert_all_tools(mcp_tools)

            # Verify all tools converted successfully
            assert len(openai_tools) == len(mcp_tools)

            # Verify structure
            for tool in openai_tools:
                assert tool["type"] == "function"
                assert "name" in tool["function"]
                assert "description" in tool["function"]
                assert "parameters" in tool["function"]

            # Verify no defaults remain
            for tool in openai_tools:
                _assert_no_defaults(tool["function"]["parameters"])


def _assert_no_defaults(schema: dict):
    """Recursively verify no 'default' keys in schema."""
    if "properties" in schema:
        for prop_schema in schema["properties"].values():
            assert "default" not in prop_schema
            if prop_schema.get("type") == "object":
                _assert_no_defaults(prop_schema)
```

## File Location

```
src/gem_flux_mcp/
└── argo/
    ├── __init__.py
    ├── client.py       # ArgoMCPClient (spec 022)
    └── converter.py    # MCPToOpenAIConverter (THIS SPEC)
```

## Dependencies

No additional dependencies required - uses only Python standard library:
- `json` - for deep copying
- `typing` - for type hints

## Success Criteria

MCP to OpenAI conversion is successful when:

1. ✅ All MCP tools convert to valid OpenAI format
2. ✅ `default` fields removed from all properties
3. ✅ Original MCP schemas not modified (deep copy)
4. ✅ `enum`, `required`, and other fields preserved
5. ✅ Nested objects handled correctly
6. ✅ Converted tools work with Argo Gateway LLMs
7. ✅ All unit tests pass
8. ✅ Integration test with real MCP server passes

## Alignment with Other Specifications

**Used By**:
- **022-argo-llm-integration.md**: ArgoMCPClient uses this for tool conversion

**Depends On**:
- **021-mcp-tool-registration.md**: Defines MCP tool schema format

**Enables**:
- Natural language tool calling via Argo Gateway
- LLM understanding of MCP tool capabilities

---

**This specification defines the precise conversion algorithm from MCP tool schemas to OpenAI function calling format, enabling Argo Gateway LLMs to understand and call MCP tools.**
