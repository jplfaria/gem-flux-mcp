# Argo LLM Integration Specification

**Type**: MCP Integration Specification
**Status**: Phase 11.5 - Argo LLM Integration
**Version**: MVP v0.1.0
**Depends On**: 021-mcp-tool-registration.md, 015-mcp-server-setup.md

## Prerequisites

- Read: **021-mcp-tool-registration.md** (MCP tool wrappers and global state)
- Read: **015-mcp-server-setup.md** (MCP server foundations)
- Read: **001-system-overview.md** (overall architecture)
- Understand: Argo Gateway LLM-as-a-Service platform
- Understand: OpenAI-style function calling
- Understand: MCP Protocol for tool calling

## Purpose

This specification defines how to integrate Gem-Flux MCP Server with Argo Gateway LLMs to enable natural language interaction with metabolic modeling tools. It specifies the ArgoMCPClient class that manages conversations, converts MCP tools to OpenAI format, and orchestrates the multi-turn tool calling loop.

## Problem Statement

**Current Situation**:
- MCP server exposes tools via MCP protocol (spec 021)
- Tools work when called directly via MCP clients
- No way to interact via natural language
- No LLM integration for agent-driven workflows
- Cannot showcase MCP tools to team/stakeholders

**Desired State**:
- Users can interact with metabolic modeling via natural language
- LLMs can call MCP tools automatically based on user intent
- Multi-turn conversations maintain context
- Works with multiple Argo Gateway models (GPT-5, Claude 4.x, Gemini 2.5)
- Easy integration for AI systems and agents

## Architecture Solution

### Two Showcase Paths

This specification enables **Path 2** (MCP + LLM showcase) which is complementary to Path 1 (Jupyter notebooks for Python library):

**Path 1: Jupyter Notebooks** (existing)
- Direct Python library usage
- For computational biologists
- Example: `examples/01_basic_workflow.ipynb`

**Path 2: MCP + Argo LLM** (this spec)
- Natural language interaction
- For AI agents and LLM applications
- Example: `examples/argo_llm/01_simple_model_building.py`

### System Architecture

```
┌────────────────────────────────────────────────────────┐
│                  User Application                      │
│     (CLI, FastAPI, test suite, AI agent)               │
└──────────────────────┬─────────────────────────────────┘
                       │
                       │ client.chat("Build a model...")
                       ▼
┌────────────────────────────────────────────────────────┐
│                  ArgoMCPClient                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Conversation Manager                            │ │
│  │  - Maintains message history                    │ │
│  │  - Tracks tool calls and results                │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │  Tool Calling Loop                               │ │
│  │  - Detects tool_calls in LLM response           │ │
│  │  - Executes via MCP server                       │ │
│  │  - Feeds results back to LLM                     │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │  MCP Tool Manager                                │ │
│  │  - Fetches tool definitions from MCP server     │ │
│  │  - Converts to OpenAI format (spec 023)         │ │
│  └──────────────────────────────────────────────────┘ │
└────────┬─────────────────────────┬─────────────────────┘
         │                         │
         │ OpenAI API format       │ MCP protocol
         ▼                         ▼
┌──────────────────┐      ┌────────────────────────────┐
│   argo-proxy     │      │  Gem-Flux MCP Server       │
│ (localhost:8000) │      │  (FastMCP-based)           │
└────────┬─────────┘      └────────────────────────────┘
         │
         │ Authenticated requests
         ▼
┌──────────────────┐
│  Argo Gateway    │
│  (ANL cloud)     │
└──────────────────┘
```

### Component Responsibilities

**ArgoMCPClient**:
- Connects to both argo-proxy and MCP server
- Manages conversation history (messages list)
- Converts MCP tool schemas to OpenAI format (via spec 023)
- Executes multi-turn tool calling loop
- Handles streaming and error recovery

**argo-proxy**:
- Authenticates with ANL credentials
- Provides OpenAI-compatible API on localhost:8000
- Routes requests to appropriate LLM provider
- Returns OpenAI-compatible responses

**Gem-Flux MCP Server**:
- Provides MCP tool definitions
- Executes tool calls (build_model, gapfill_model, etc.)
- Returns structured results

## ArgoMCPClient Specification

### Class Definition

```python
class ArgoMCPClient:
    """Client for interacting with Gem-Flux MCP tools via Argo Gateway LLMs.

    This client provides a simple interface for natural language interaction
    with metabolic modeling tools. It automatically handles:
    - Tool calling loop (LLM decides when to call tools)
    - MCP tool execution
    - Conversation state management
    - Multi-turn context
    """

    def __init__(
        self,
        argo_base_url: str = "http://localhost:8000/v1",
        mcp_server_command: str = "gem-flux-mcp",
        default_model: str = "gpt-5"
    ):
        """Initialize client.

        Args:
            argo_base_url: Base URL for argo-proxy (OpenAI-compatible)
            mcp_server_command: Command to start MCP server
            default_model: Default LLM model to use (gpt-5, claude-4-opus, gemini-2.5-pro)
        """
```

### Initialization

```python
async def initialize(self):
    """Connect to MCP server and load tools.

    This method:
    1. Starts MCP server connection via stdio
    2. Fetches all available tool definitions
    3. Converts tools to OpenAI format (spec 023)
    4. Caches converted tools for reuse

    Must be called before chat() or chat_stream().

    Raises:
        RuntimeError: If MCP server cannot be started
        ConnectionError: If argo-proxy not available
    """
```

Implementation requirements:
1. Connect to MCP server using `mcp.client.stdio.stdio_client`
2. Use `StdioServerParameters` with command="uv", args=["run", mcp_server_command]
3. Call `session.initialize()` after connection
4. Call `session.list_tools()` to get tool definitions
5. Convert tools using `MCPToOpenAIConverter.convert_all_tools()` (spec 023)
6. Store converted tools in `self.mcp_tools_openai`

### Synchronous Wrapper

```python
def initialize_sync(self):
    """Synchronous wrapper for initialize().

    For use in synchronous code and tests.
    """
    asyncio.run(self.initialize())
```

### Chat Interface

```python
def chat(
    self,
    message: str,
    model: str = None,
    max_turns: int = 10
) -> str:
    """Send message and get response (with automatic tool calling).

    This is the main interface for users. The LLM will automatically:
    - Decide which tools to call based on user intent
    - Call tools via MCP server
    - Process tool results
    - Generate final natural language response

    Args:
        message: User message in natural language
        model: LLM model to use (default: self.default_model)
        max_turns: Max tool calling iterations (prevents infinite loops)

    Returns:
        Final text response from LLM

    Raises:
        RuntimeError: If tool calling loop exceeds max_turns
        Exception: If MCP tool execution fails

    Example:
        >>> client = ArgoMCPClient()
        >>> client.initialize_sync()
        >>> response = client.chat("Build a model for E. coli genome 83333.1")
        >>> print(response)
        "I've built a metabolic model with ID 'ecoli_83333.gf'..."
    """
```

### Streaming Interface

```python
def chat_stream(
    self,
    message: str,
    model: str = None,
    on_chunk: callable = None,
    max_turns: int = 10
) -> Generator[str, None, None]:
    """Stream response with real-time updates.

    Args:
        message: User message
        model: LLM model to use
        on_chunk: Optional callback for each text chunk
        max_turns: Max tool calling iterations

    Yields:
        Text chunks as they arrive from LLM

    Example:
        >>> for chunk in client.chat_stream("Build a model"):
        ...     print(chunk, end="", flush=True)
    """
```

### Conversation Management

```python
def reset(self):
    """Clear conversation history.

    Call this to start a new conversation session.
    Tool calls from previous conversation will be forgotten.
    """
    self.messages = []
    self.tool_calls_made = []
```

### Instance Variables

```python
# Configuration
self.argo_base_url: str          # argo-proxy URL
self.mcp_server_command: str      # MCP server command
self.default_model: str           # Default LLM model

# Clients
self.openai_client: OpenAI        # OpenAI client for Argo Gateway
self.mcp_client: ClientSession    # MCP client for tool execution

# Tool definitions
self.mcp_tools_openai: list       # Cached OpenAI-format tools

# Conversation state
self.messages: list               # Message history
self.tool_calls_made: list        # Tool call log
```

## Tool Calling Loop Specification

### Loop Algorithm

The tool calling loop enables multi-turn tool execution:

```python
def chat(self, message: str, model: str = None, max_turns: int = 10) -> str:
    # 1. Add user message to history
    self.messages.append({"role": "user", "content": message})

    # 2. Loop until LLM produces final response (up to max_turns)
    for turn in range(max_turns):
        # 3. Call LLM with conversation history and tool definitions
        response = self.openai_client.chat.completions.create(
            model=model or self.default_model,
            messages=self.messages,
            tools=self.mcp_tools_openai,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # 4. Check if LLM wants to call tools
        if response_message.tool_calls:
            # 5. Add assistant's tool call message to history
            self.messages.append(response_message)

            # 6. Execute each tool call via MCP
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # Execute via MCP server
                result = self._execute_mcp_tool(tool_name, tool_args)

                # 7. Add tool result to history
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

                # 8. Log tool call for debugging
                self.tool_calls_made.append({
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "result": result
                })

            # 9. Continue loop - LLM will process tool results
            continue

        else:
            # 10. No tool calls - LLM produced final response
            self.messages.append(response_message)
            return response_message.content

    # 11. Max turns reached - prevent infinite loop
    raise RuntimeError(f"Tool calling loop exceeded max turns ({max_turns})")
```

### Loop Invariants

1. **Message History Consistency**: `self.messages` always contains valid OpenAI chat format
2. **Tool Call Ordering**: Tool results always follow tool calls in conversation
3. **Turn Limit**: Loop always terminates (either final response or max_turns)
4. **State Preservation**: All tool calls logged in `self.tool_calls_made`

### MCP Tool Execution

```python
def _execute_mcp_tool(self, tool_name: str, arguments: dict) -> dict:
    """Execute tool via MCP server.

    Args:
        tool_name: Name of tool to call (e.g., "build_model")
        arguments: Tool arguments as dict

    Returns:
        Tool result as dict

    Raises:
        Exception: If tool execution fails
    """
    # Use MCP client to call tool
    result = asyncio.run(
        self.mcp_client.call_tool(tool_name, arguments)
    )

    return result
```

### Error Handling in Loop

```python
def _execute_mcp_tool_safe(self, tool_name: str, arguments: dict) -> dict:
    """Execute tool with error handling.

    Returns error dict on failure instead of raising exception.
    This allows LLM to see errors and respond appropriately.
    """
    try:
        result = self._execute_mcp_tool(tool_name, arguments)

        # Validate result structure
        if not isinstance(result, dict):
            return {
                "status": "error",
                "message": f"Tool returned invalid type: {type(result)}"
            }

        return result

    except Exception as e:
        # Return error in standard format
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }
```

## Configuration and Environment

### Environment Variables

Support for environment-based configuration:

```python
import os

# Default values with environment variable fallbacks
argo_base_url = os.getenv("ARGO_BASE_URL", "http://localhost:8000/v1")
mcp_server_command = os.getenv("MCP_SERVER_COMMAND", "gem-flux-mcp")
default_model = os.getenv("ARGO_DEFAULT_MODEL", "gpt-5")
```

### Supported Models

All Argo Gateway models are supported:

| Provider | Model Names | Strengths |
|----------|------------|-----------|
| OpenAI | gpt-5, gpt-4.1, gpt-4o | General purpose, fast, reliable |
| Anthropic | claude-4-opus, claude-4-sonnet | Complex reasoning, tool use |
| Google | gemini-2.5-pro, o3 | Multimodal, fast inference |

## File Structure

```
src/gem_flux_mcp/
├── argo/                       # NEW - Argo integration
│   ├── __init__.py
│   ├── client.py               # ArgoMCPClient
│   ├── converter.py            # MCPToOpenAIConverter (spec 023)
│   └── config.py               # Configuration loading
│
examples/
├── 01_basic_workflow.ipynb     # EXISTS - Python library
├── argo_llm/                   # NEW - MCP + LLM showcase
│   ├── 01_simple_model_building.py
│   ├── 02_complete_workflow.py
│   └── 03_interactive_cli.py
│
tests/integration/
├── test_phase11_mcp_server.py  # EXISTS - MCP server tests
├── test_phase17_argo_llm_real.py  # NEW - Real LLM tests (spec 024)
```

## Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    # ... existing ...
    "openai>=1.0.0",   # For argo-proxy OpenAI-compatible client
    "httpx>=0.28.0",   # For checking argo-proxy availability
]
```

**IMPORTANT: argo-proxy is NOT a dependency**

`argo-proxy` is a **standalone service** that users install and run separately:

```bash
# Users install argo-proxy SEPARATELY (not in our project)
pip install argo-proxy  # Install in separate environment (global, conda, pipx, etc.)
argo-proxy             # Start server on localhost:8000

# Our project connects to the already-running service
# via OpenAI client pointing to localhost:8000
```

**Why argo-proxy is not a dependency**:
- It's infrastructure (like a database), not a library
- Users might run it on different machines
- It serves multiple projects, not just ours
- Has its own configuration (config.yaml, ANL credentials)
- Users might already have it installed globally

**Our code only requires**:
- `openai` package (to make HTTP requests to argo-proxy)
- `httpx` package (to check if argo-proxy is available)

**Do NOT add `argo-proxy` to pyproject.toml**

## Testing Requirements

### Unit Tests (No Real LLM)

**test_argo_client_unit.py**:
1. `test_client_initialization` - Client creates successfully
2. `test_message_history_management` - Messages appended correctly
3. `test_tool_call_logging` - Tool calls logged properly
4. `test_reset_clears_state` - reset() clears messages and tool_calls_made

### Integration Tests (Real LLM)

See **spec 024-argo-real-llm-testing.md** for detailed testing patterns.

**test_phase17_argo_llm_real.py** (marked with `@pytest.mark.real_llm`):
1. `test_build_media_with_argo` - Simple tool call
2. `test_build_model_with_argo` - Async tool call
3. `test_gapfill_model_with_argo` - Complex parameters
4. `test_complete_workflow_multi_turn` - Full workflow conversation
5. `test_error_handling_invalid_model` - LLM handles errors

## Success Criteria

Argo LLM integration is successful when:

1. ✅ ArgoMCPClient connects to both argo-proxy and MCP server
2. ✅ MCP tools converted to OpenAI format correctly (spec 023)
3. ✅ LLM can call all MCP tools via natural language
4. ✅ Multi-turn conversations maintain context
5. ✅ Tool calling loop handles errors gracefully
6. ✅ Streaming works with real-time responses
7. ✅ All real LLM integration tests pass (spec 024)
8. ✅ Tutorial scripts run successfully
9. ✅ Team can demo agent usage to stakeholders

## Usage Examples

### Simple Chat

```python
from gem_flux_mcp.argo import ArgoMCPClient

# Create client
client = ArgoMCPClient()
client.initialize_sync()

# Natural language interaction
response = client.chat("Build a metabolic model for E. coli genome 83333.1")
print(response)
# "I've built a metabolic model with ID 'ecoli_83333.gf'.
#  The model contains 1478 reactions, 1032 metabolites, and 1515 genes."
```

### Multi-Turn Conversation

```python
client = ArgoMCPClient()
client.initialize_sync()

# Turn 1
response1 = client.chat("Build a model for E. coli 83333.1")
print("Assistant:", response1)

# Turn 2 (continues conversation)
response2 = client.chat("Now gapfill it on minimal media")
print("Assistant:", response2)

# Turn 3
response3 = client.chat("Run FBA and show me the growth rate")
print("Assistant:", response3)

# Check tools used
for call in client.tool_calls_made:
    print(f"  - {call['tool_name']}")
```

### Complete Workflow Example

```python
"""Complete metabolic modeling workflow via natural language."""
import asyncio
from gem_flux_mcp.argo_client import ArgoMCPClient

async def main():
    # Initialize client
    client = ArgoMCPClient()
    await client.initialize()

    print("🤖 ArgoMCPClient initialized with MCP tools\n")

    # Natural language → Tool calls
    print("User: Build a model for E. coli genome 83333.1")
    response1 = client.chat("Build a metabolic model for E. coli genome 83333.1")
    print(f"Assistant: {response1}\n")
    # LLM internally calls build_model tool via MCP

    # Multi-turn conversation (LLM remembers context)
    print("User: Now gapfill it on minimal media")
    response2 = client.chat("Now gapfill it on minimal media")
    print(f"Assistant: {response2}\n")
    # LLM calls gapfill_model tool with remembered model_id

    # Query results
    print("User: What's the growth rate?")
    response3 = client.chat("What's the growth rate?")
    print(f"Assistant: {response3}\n")
    # LLM calls run_fba tool, returns results in natural language

    # Inspect tool calls made
    print(f"📊 Tools called: {len(client.tool_calls_made)}")
    for call in client.tool_calls_made:
        print(f"  - {call['tool_name']}: {call['arguments']}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Expected Output**:
```
🤖 ArgoMCPClient initialized with MCP tools

User: Build a model for E. coli genome 83333.1
Assistant: I've built a metabolic model for E. coli with ID 'ecoli_83333.gf'.
The model contains 1247 reactions, 892 compounds, and 4140 genes. It was built
using the GramNegative template.

User: Now gapfill it on minimal media
Assistant: I've gapfilled the model for growth on minimal media. Added 23 new
reactions to enable biomass production. The gapfilling was successful.

User: What's the growth rate?
Assistant: The growth rate is 0.8540 per hour on minimal media.

📊 Tools called: 3
  - build_model: {'model_id': 'ecoli_83333.gf', 'genome_source_type': 'rast_id', ...}
  - gapfill_model: {'model_id': 'ecoli_83333.gf', 'media_id': 'minimal'}
  - run_fba: {'model_id': 'ecoli_83333.gf', 'media_id': 'minimal'}
```

### Streaming

```python
client = ArgoMCPClient()
client.initialize_sync()

print("User: Build a model for E. coli")
print("Assistant: ", end="", flush=True)

for chunk in client.chat_stream("Build a model for E. coli"):
    print(chunk, end="", flush=True)

print()  # Newline
```

## Alignment with Other Specifications

**Depends On**:
- **021-mcp-tool-registration.md**: MCP tools must be registered first
- **015-mcp-server-setup.md**: Server startup and initialization
- **023-mcp-tool-conversion.md**: MCP to OpenAI format conversion
- **024-argo-real-llm-testing.md**: Testing patterns for validation

**Extends**:
- **001-system-overview.md**: Adds LLM integration layer

**Enables**:
- Natural language interface to metabolic modeling
- Agent-driven workflows
- Team showcase and demonstrations

## Future Enhancements

**Post-MVP Improvements** (v0.2.0+):
1. Circuit breaker pattern for LLM failures
2. Model switching on errors
3. Conversation persistence (save/load)
4. Tool call replay and debugging
5. Custom system prompts
6. Token usage tracking and limits
7. Multi-user session management
8. WebSocket streaming for web UIs

---

**This specification defines the Argo LLM integration layer that enables natural language interaction with metabolic modeling tools via the MCP protocol.**
