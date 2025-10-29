# Converting MCP Tools to OpenAI Function Format

**Date**: 2025-10-29
**Purpose**: Technical guide for converting MCP tool definitions to OpenAI function calling format
**Audience**: Developers implementing ArgoMCPClient

---

## 1. Why Conversion is Needed

MCP servers expose tools with their own schema format, but Argo Gateway (via OpenAI API) expects a different format for function calling.

```
┌─────────────────┐        ┌─────────────────┐
│  MCP Tool       │        │  OpenAI Tool    │
│  Definition     │  --->  │  Definition     │
│  (MCP format)   │        │  (OpenAI format)│
└─────────────────┘        └─────────────────┘
```

---

## 2. MCP Tool Definition Format

MCP tools are defined using FastMCP decorators:

```python
@mcp.tool()
def build_model(
    model_id: str,
    genome_source: Literal["rast_id", "fasta_file", "annotation_dict"],
    genome_id: str,
    template: str = "auto"
) -> dict:
    """Build a metabolic model from genome annotation.

    Args:
        model_id: Unique identifier with .gf suffix (e.g., 'ecoli.gf')
        genome_source: Source type for genome data
        genome_id: RAST ID, FASTA file path, or annotation dict
        template: Template name ('auto', 'GramNegative', 'GramPositive', 'Core')

    Returns:
        dict with status, model_id, stats (reactions, metabolites, genes)
    """
    # Implementation...
```

FastMCP introspects this to generate MCP tool schema:

```json
{
  "name": "build_model",
  "description": "Build a metabolic model from genome annotation.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "model_id": {
        "type": "string",
        "description": "Unique identifier with .gf suffix (e.g., 'ecoli.gf')"
      },
      "genome_source": {
        "type": "string",
        "enum": ["rast_id", "fasta_file", "annotation_dict"],
        "description": "Source type for genome data"
      },
      "genome_id": {
        "type": "string",
        "description": "RAST ID, FASTA file path, or annotation dict"
      },
      "template": {
        "type": "string",
        "description": "Template name ('auto', 'GramNegative', 'GramPositive', 'Core')",
        "default": "auto"
      }
    },
    "required": ["model_id", "genome_source", "genome_id"]
  }
}
```

---

## 3. OpenAI Function Calling Format

OpenAI expects tools in this format:

```python
{
    "type": "function",  # Always "function"
    "function": {
        "name": "build_model",
        "description": "Build a metabolic model from genome annotation.",
        "parameters": {  # Note: "parameters", not "inputSchema"
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "Unique identifier with .gf suffix (e.g., 'ecoli.gf')"
                },
                "genome_source": {
                    "type": "string",
                    "enum": ["rast_id", "fasta_file", "annotation_dict"],
                    "description": "Source type for genome data"
                },
                "genome_id": {
                    "type": "string",
                    "description": "RAST ID, FASTA file path, or annotation dict"
                },
                "template": {
                    "type": "string",
                    "description": "Template name ('auto', 'GramNegative', 'GramPositive', 'Core')"
                }
            },
            "required": ["model_id", "genome_source", "genome_id"]
        }
    }
}
```

---

## 4. Conversion Algorithm

### 4.1 Basic Conversion

```python
def convert_mcp_tool_to_openai(mcp_tool: dict) -> dict:
    """Convert MCP tool definition to OpenAI function format.

    Args:
        mcp_tool: MCP tool schema from server

    Returns:
        OpenAI-compatible tool definition
    """
    return {
        "type": "function",
        "function": {
            "name": mcp_tool["name"],
            "description": mcp_tool["description"],
            "parameters": mcp_tool["inputSchema"]  # Rename key
        }
    }
```

### 4.2 Handling Defaults

**Problem**: OpenAI function calling doesn't support `"default"` in JSON Schema.

**Solution**: Remove default values from parameters (they're documented in descriptions):

```python
def convert_mcp_tool_to_openai(mcp_tool: dict) -> dict:
    """Convert MCP tool definition to OpenAI function format."""

    # Deep copy to avoid modifying original
    parameters = json.loads(json.dumps(mcp_tool["inputSchema"]))

    # Remove 'default' from all properties (OpenAI doesn't support it)
    for prop_name, prop_schema in parameters.get("properties", {}).items():
        if "default" in prop_schema:
            del prop_schema["default"]

    return {
        "type": "function",
        "function": {
            "name": mcp_tool["name"],
            "description": mcp_tool["description"],
            "parameters": parameters
        }
    }
```

### 4.3 Complete Implementation

```python
import json
from typing import List, Dict, Any

class MCPToOpenAIConverter:
    """Converts MCP tool schemas to OpenAI function calling format."""

    @staticmethod
    def convert_tool(mcp_tool: Dict[str, Any]) -> Dict[str, Any]:
        """Convert single MCP tool to OpenAI format.

        Args:
            mcp_tool: MCP tool schema with keys:
                - name: str
                - description: str
                - inputSchema: dict (JSON Schema)

        Returns:
            OpenAI tool definition
        """
        # Deep copy parameters to avoid modifying original
        parameters = json.loads(json.dumps(mcp_tool["inputSchema"]))

        # Remove unsupported fields
        MCPToOpenAIConverter._remove_defaults(parameters)

        return {
            "type": "function",
            "function": {
                "name": mcp_tool["name"],
                "description": mcp_tool["description"],
                "parameters": parameters
            }
        }

    @staticmethod
    def _remove_defaults(schema: Dict[str, Any]) -> None:
        """Remove 'default' keys from schema (OpenAI doesn't support them).

        Mutates schema in place.
        """
        if "properties" in schema:
            for prop_schema in schema["properties"].values():
                if "default" in prop_schema:
                    del prop_schema["default"]

                # Recurse for nested objects
                if prop_schema.get("type") == "object":
                    MCPToOpenAIConverter._remove_defaults(prop_schema)

    @staticmethod
    def convert_all_tools(mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert list of MCP tools to OpenAI format.

        Args:
            mcp_tools: List of MCP tool schemas

        Returns:
            List of OpenAI tool definitions
        """
        return [
            MCPToOpenAIConverter.convert_tool(tool)
            for tool in mcp_tools
        ]
```

---

## 5. Fetching MCP Tools

### 5.1 Via MCP Protocol

MCP servers expose a `tools/list` endpoint:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def get_mcp_tools() -> List[Dict[str, Any]]:
    """Fetch tool definitions from MCP server."""

    # Connect to MCP server
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "gem-flux-mcp"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()

            # List available tools
            tools_result = await session.list_tools()

            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools_result.tools
            ]

# Usage
mcp_tools = asyncio.run(get_mcp_tools())
openai_tools = MCPToOpenAIConverter.convert_all_tools(mcp_tools)
```

### 5.2 Via Direct Import (Testing Only)

For testing, you can import tools directly:

```python
from gem_flux_mcp.server import get_tool_definitions

def get_mcp_tools_sync() -> List[Dict[str, Any]]:
    """Get MCP tool definitions synchronously (testing only)."""
    return get_tool_definitions()  # Returns list of MCP tool schemas
```

---

## 6. Example: Full Conversion

### Input (MCP Tool)

```json
{
  "name": "gapfill_model",
  "description": "Gapfill a metabolic model to enable growth on a specified media.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "model_id": {
        "type": "string",
        "description": "Model identifier with .gf suffix"
      },
      "media_id": {
        "type": "string",
        "description": "Media identifier or predefined name"
      },
      "target_reaction": {
        "type": "string",
        "description": "Target reaction to enable",
        "default": "bio1"
      },
      "minimum_fraction": {
        "type": "number",
        "description": "Minimum growth fraction",
        "default": 0.01
      }
    },
    "required": ["model_id", "media_id"]
  }
}
```

### Output (OpenAI Tool)

```json
{
  "type": "function",
  "function": {
    "name": "gapfill_model",
    "description": "Gapfill a metabolic model to enable growth on a specified media.",
    "parameters": {
      "type": "object",
      "properties": {
        "model_id": {
          "type": "string",
          "description": "Model identifier with .gf suffix"
        },
        "media_id": {
          "type": "string",
          "description": "Media identifier or predefined name"
        },
        "target_reaction": {
          "type": "string",
          "description": "Target reaction to enable"
        },
        "minimum_fraction": {
          "type": "number",
          "description": "Minimum growth fraction"
        }
      },
      "required": ["model_id", "media_id"]
    }
  }
}
```

**Changes**:
1. Wrapped in `{"type": "function", "function": {...}}`
2. Renamed `inputSchema` → `parameters`
3. Removed `"default"` keys from properties

---

## 7. Testing Conversion

```python
import pytest
from gem_flux_mcp.argo_client import MCPToOpenAIConverter

def test_mcp_to_openai_conversion():
    """Test MCP tool conversion to OpenAI format."""

    # Sample MCP tool
    mcp_tool = {
        "name": "build_model",
        "description": "Build a metabolic model",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "Model ID"
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

    # Convert
    openai_tool = MCPToOpenAIConverter.convert_tool(mcp_tool)

    # Verify structure
    assert openai_tool["type"] == "function"
    assert openai_tool["function"]["name"] == "build_model"
    assert openai_tool["function"]["description"] == "Build a metabolic model"

    # Verify parameters
    params = openai_tool["function"]["parameters"]
    assert params["type"] == "object"
    assert "model_id" in params["properties"]
    assert "template" in params["properties"]
    assert params["required"] == ["model_id"]

    # Verify default removed
    assert "default" not in params["properties"]["template"]

def test_convert_all_gem_flux_tools():
    """Test conversion of all Gem-Flux MCP tools."""
    from gem_flux_mcp.server import get_tool_definitions

    # Get all MCP tools
    mcp_tools = get_tool_definitions()

    # Convert to OpenAI format
    openai_tools = MCPToOpenAIConverter.convert_all_tools(mcp_tools)

    # Verify count matches
    assert len(openai_tools) == len(mcp_tools)

    # Verify all have correct structure
    for tool in openai_tools:
        assert tool["type"] == "function"
        assert "name" in tool["function"]
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]
        assert tool["function"]["parameters"]["type"] == "object"
```

---

## 8. Integration with Argo Client

The conversion happens automatically in `ArgoMCPClient`:

```python
class ArgoMCPClient:
    def __init__(self):
        self.openai_client = OpenAI(
            base_url="http://localhost:8000/v1",
            api_key="dummy"
        )
        self.mcp_tools = self._load_mcp_tools()
        self.openai_tools = MCPToOpenAIConverter.convert_all_tools(self.mcp_tools)

    def chat(self, message: str) -> str:
        """Send message and handle tool calls automatically."""
        messages = [{"role": "user", "content": message}]

        response = self.openai_client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            tools=self.openai_tools  # <-- Converted tools
        )

        # Handle tool calls...
```

---

## 9. Common Issues

### Issue 1: Default Values Not Working

**Problem**: LLM doesn't use default values for optional parameters.

**Solution**: Include defaults in the parameter description:

```python
"target_reaction": {
    "type": "string",
    "description": "Target reaction to enable (default: 'bio1')"
}
```

### Issue 2: Enum Values Not Respected

**Problem**: LLM suggests invalid enum values.

**Solution**: List valid values in description:

```python
"genome_source": {
    "type": "string",
    "enum": ["rast_id", "fasta_file", "annotation_dict"],
    "description": "Source type for genome data. Must be one of: 'rast_id', 'fasta_file', or 'annotation_dict'"
}
```

### Issue 3: Complex Nested Objects

**Problem**: LLM struggles with deeply nested object structures.

**Solution**: Flatten or simplify schema, or provide examples in description.

---

## 10. References

- **OpenAI Function Calling Docs**: https://platform.openai.com/docs/guides/function-calling
- **JSON Schema Spec**: https://json-schema.org/
- **MCP Protocol Spec**: https://spec.modelcontextprotocol.io/specification/2025-06-18/server/tools/
- **FastMCP Tool Introspection**: Uses Python type hints + docstrings
