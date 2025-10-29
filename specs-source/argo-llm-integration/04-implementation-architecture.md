# ArgoMCPClient Implementation Architecture

**Date**: 2025-10-29
**Purpose**: Detailed architecture and implementation plan for ArgoMCPClient
**Audience**: Developers implementing Argo + MCP integration

---

## 1. System Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        User Application                           │
│  (CLI tool, FastAPI app, Jupyter notebook, test suite)           │
└─────────────────────────────┬─────────────────────────────────────┘
                              │
                              │ Simple API: client.chat("Build a model")
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│                         ArgoMCPClient                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Conversation Manager                                       │ │
│  │  - Maintains message history                               │ │
│  │  - Tracks tool calls and results                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Tool Calling Loop                                          │ │
│  │  - Detects tool_calls in LLM response                      │ │
│  │  - Executes via MCP server                                 │ │
│  │  - Feeds results back to LLM                               │ │
│  │  - Continues until LLM produces final text response        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  MCP Tool Manager                                           │ │
│  │  - Fetches tool definitions from MCP server                │ │
│  │  - Converts to OpenAI format                               │ │
│  │  - Caches converted tools                                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────┬────────────────────────────────┬─────────────────┘
               │                                │
               │ OpenAI API format              │ MCP protocol
               ▼                                ▼
┌─────────────────────────┐    ┌──────────────────────────────────┐
│     argo-proxy          │    │   Gem-Flux MCP Server            │
│  (localhost:8000)       │    │   (FastMCP-based)                │
└──────────┬──────────────┘    └──────────────────────────────────┘
           │
           │ Authenticated requests
           ▼
┌─────────────────────────┐
│    Argo Gateway         │
│    (ANL cloud)          │
└──────────┬──────────────┘
           │
           │ Routes to provider
           ├─────┬─────┬──────┐
           ▼     ▼     ▼      ▼
        OpenAI  Anthropic  Google  Local
```

---

## 2. Core Components

### 2.1 ArgoMCPClient Class

Main interface for user applications:

```python
class ArgoMCPClient:
    """Client for interacting with Gem-Flux MCP tools via Argo Gateway LLMs."""

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
            default_model: Default LLM model to use
        """
        self.argo_base_url = argo_base_url
        self.mcp_server_command = mcp_server_command
        self.default_model = default_model

        # OpenAI client for Argo Gateway
        self.openai_client = OpenAI(
            base_url=argo_base_url,
            api_key="dummy"  # Not used by argo-proxy
        )

        # MCP client for tool execution
        self.mcp_client = None  # Lazy-initialized
        self.mcp_tools_openai = []  # Cached OpenAI-format tools

        # Conversation state
        self.messages = []  # Message history
        self.tool_calls_made = []  # Tool call log

    async def initialize(self):
        """Connect to MCP server and load tools."""
        # Connect to MCP server
        self.mcp_client = await self._connect_to_mcp_server()

        # Fetch and convert tools
        mcp_tools = await self._fetch_mcp_tools()
        self.mcp_tools_openai = MCPToOpenAIConverter.convert_all_tools(mcp_tools)

    def chat(
        self,
        message: str,
        model: str = None,
        max_turns: int = 10
    ) -> str:
        """Send message and get response (with automatic tool calling).

        Args:
            message: User message
            model: LLM model to use (default: self.default_model)
            max_turns: Max tool calling iterations (prevents infinite loops)

        Returns:
            Final text response from LLM
        """
        # Implementation in section 3...

    def chat_stream(
        self,
        message: str,
        model: str = None,
        on_chunk: callable = None
    ):
        """Stream response with real-time updates.

        Args:
            message: User message
            model: LLM model to use
            on_chunk: Callback for each text chunk

        Yields:
            Text chunks as they arrive
        """
        # Implementation in section 4...

    def reset(self):
        """Clear conversation history."""
        self.messages = []
        self.tool_calls_made = []
```

### 2.2 MCPToOpenAIConverter

Converts MCP tool definitions to OpenAI format (see 02-mcp-tool-conversion.md):

```python
class MCPToOpenAIConverter:
    """Converts MCP tool schemas to OpenAI function calling format."""

    @staticmethod
    def convert_tool(mcp_tool: dict) -> dict:
        """Convert single MCP tool to OpenAI format."""
        # Implementation in 02-mcp-tool-conversion.md

    @staticmethod
    def convert_all_tools(mcp_tools: list) -> list:
        """Convert list of MCP tools to OpenAI format."""
        return [
            MCPToOpenAIConverter.convert_tool(tool)
            for tool in mcp_tools
        ]
```

### 2.3 ConversationManager

Manages message history and state:

```python
class ConversationManager:
    """Manages conversation history and tool call tracking."""

    def __init__(self):
        self.messages = []
        self.tool_calls_made = []

    def add_user_message(self, content: str):
        """Add user message to history."""
        self.messages.append({
            "role": "user",
            "content": content
        })

    def add_assistant_message(self, message):
        """Add assistant message (may include tool_calls)."""
        self.messages.append(message)

    def add_tool_result(self, tool_call_id: str, result: dict):
        """Add tool execution result to history."""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps(result)
        })

        # Log tool call
        self.tool_calls_made.append({
            "tool_call_id": tool_call_id,
            "result": result
        })

    def get_messages(self) -> list:
        """Get all messages for next LLM call."""
        return self.messages.copy()

    def clear(self):
        """Clear conversation history."""
        self.messages = []
        self.tool_calls_made = []
```

---

## 3. Tool Calling Loop Implementation

### 3.1 Basic Tool Calling Loop

```python
def chat(
    self,
    message: str,
    model: str = None,
    max_turns: int = 10
) -> str:
    """Send message and get response (with automatic tool calling)."""

    if model is None:
        model = self.default_model

    # Add user message to history
    self.messages.append({"role": "user", "content": message})

    # Tool calling loop (max iterations to prevent infinite loops)
    for turn in range(max_turns):
        # Call LLM with current conversation
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=self.messages,
            tools=self.mcp_tools_openai,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # Check if LLM wants to call tools
        if response_message.tool_calls:
            # Add assistant's tool call to history
            self.messages.append(response_message)

            # Execute each tool call
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # Execute via MCP server
                try:
                    result = self._execute_mcp_tool(tool_name, tool_args)
                except Exception as e:
                    result = {"status": "error", "message": str(e)}

                # Add tool result to history
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

                # Log tool call
                self.tool_calls_made.append({
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "result": result
                })

            # Continue loop - LLM will process tool results
            continue

        else:
            # No tool calls - LLM produced final response
            self.messages.append(response_message)
            return response_message.content

    # Max turns reached
    raise RuntimeError(f"Tool calling loop exceeded max turns ({max_turns})")
```

### 3.2 MCP Tool Execution

```python
def _execute_mcp_tool(self, tool_name: str, arguments: dict) -> dict:
    """Execute tool via MCP server.

    Args:
        tool_name: Name of tool to call
        arguments: Tool arguments (dict)

    Returns:
        Tool result (dict)

    Raises:
        Exception: If tool execution fails
    """
    # Use MCP client to call tool
    result = asyncio.run(
        self.mcp_client.call_tool(tool_name, arguments)
    )

    return result
```

### 3.3 Error Handling

```python
def _execute_mcp_tool_safe(self, tool_name: str, arguments: dict) -> dict:
    """Execute tool with error handling.

    Returns error dict on failure instead of raising exception.
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

---

## 4. Streaming Implementation

### 4.1 Streaming with Tool Calls

```python
def chat_stream(
    self,
    message: str,
    model: str = None,
    on_chunk: callable = None,
    max_turns: int = 10
):
    """Stream response with real-time updates.

    Args:
        message: User message
        model: LLM model to use
        on_chunk: Callback for each text chunk (optional)
        max_turns: Max tool calling iterations

    Yields:
        Text chunks as they arrive
    """
    if model is None:
        model = self.default_model

    # Add user message
    self.messages.append({"role": "user", "content": message})

    for turn in range(max_turns):
        # Create streaming request
        stream = self.openai_client.chat.completions.create(
            model=model,
            messages=self.messages,
            tools=self.mcp_tools_openai,
            tool_choice="auto",
            stream=True  # Enable streaming
        )

        # Accumulate response
        accumulated_message = {
            "role": "assistant",
            "content": "",
            "tool_calls": []
        }

        current_tool_call = None

        # Process stream chunks
        for chunk in stream:
            delta = chunk.choices[0].delta

            # Text content
            if delta.content:
                accumulated_message["content"] += delta.content

                # Yield to user
                if on_chunk:
                    on_chunk(delta.content)
                yield delta.content

            # Tool call
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    if tool_call_delta.index is not None:
                        # New tool call
                        if tool_call_delta.index >= len(accumulated_message["tool_calls"]):
                            accumulated_message["tool_calls"].append({
                                "id": tool_call_delta.id or "",
                                "type": "function",
                                "function": {
                                    "name": tool_call_delta.function.name or "",
                                    "arguments": ""
                                }
                            })

                        current_tool_call = accumulated_message["tool_calls"][tool_call_delta.index]

                        # Accumulate function name
                        if tool_call_delta.function.name:
                            current_tool_call["function"]["name"] = tool_call_delta.function.name

                        # Accumulate arguments
                        if tool_call_delta.function.arguments:
                            current_tool_call["function"]["arguments"] += tool_call_delta.function.arguments

        # Check if we have tool calls
        if accumulated_message["tool_calls"]:
            # Add to history
            self.messages.append(accumulated_message)

            # Execute tools (NOT streamed - instant execution)
            for tool_call in accumulated_message["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])

                # Show tool call to user
                yield f"\n\n[Calling {tool_name}...]\n"

                # Execute
                result = self._execute_mcp_tool_safe(tool_name, tool_args)

                # Add to history
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result)
                })

                # Log
                self.tool_calls_made.append({
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "result": result
                })

            # Continue loop
            continue

        else:
            # No tool calls - done
            self.messages.append(accumulated_message)
            return

    raise RuntimeError(f"Streaming loop exceeded max turns ({max_turns})")
```

---

## 5. MCP Server Connection

### 5.1 Async MCP Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def _connect_to_mcp_server(self):
    """Connect to MCP server via stdio.

    Returns:
        ClientSession for making MCP calls
    """
    # Setup server parameters
    server_params = StdioServerParameters(
        command="uv",
        args=["run", self.mcp_server_command],
        env=None
    )

    # Connect (stdio transport)
    read, write = await stdio_client(server_params).__aenter__()
    session = await ClientSession(read, write).__aenter__()

    # Initialize
    await session.initialize()

    return session

async def _fetch_mcp_tools(self) -> list:
    """Fetch tool definitions from MCP server.

    Returns:
        List of MCP tool schemas
    """
    # List tools
    tools_result = await self.mcp_client.list_tools()

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema
        }
        for tool in tools_result.tools
    ]
```

### 5.2 Synchronous Wrapper

For non-async user code:

```python
def initialize_sync(self):
    """Synchronous wrapper for initialize()."""
    asyncio.run(self.initialize())

def _execute_mcp_tool(self, tool_name: str, arguments: dict) -> dict:
    """Execute MCP tool synchronously."""
    return asyncio.run(
        self.mcp_client.call_tool(tool_name, arguments)
    )
```

---

## 6. Usage Examples

### 6.1 Simple Chat

```python
from gem_flux_mcp.argo_client import ArgoMCPClient

# Create client
client = ArgoMCPClient()
client.initialize_sync()

# Send message
response = client.chat("Build a metabolic model for E. coli genome 83333.1")
print(response)

# Output:
# "I've built a metabolic model for E. coli with ID 'ecoli_83333.gf'.
#  The model contains 1478 reactions, 1032 metabolites, and 1515 genes."
```

### 6.2 Multi-Turn Conversation

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

# Check what tools were called
print("\nTools used:")
for call in client.tool_calls_made:
    print(f"  - {call['tool_name']}: {call['arguments']}")
```

### 6.3 Streaming Response

```python
client = ArgoMCPClient()
client.initialize_sync()

print("User: Build a model for E. coli")
print("Assistant: ", end="", flush=True)

for chunk in client.chat_stream("Build a model for E. coli"):
    print(chunk, end="", flush=True)

print()  # Newline
```

### 6.4 Error Handling

```python
client = ArgoMCPClient()
client.initialize_sync()

try:
    response = client.chat("Run FBA on nonexistent_model.gf")
    print(response)
    # LLM will acknowledge the error and suggest building model first
except Exception as e:
    print(f"Error: {e}")
```

---

## 7. Configuration

### 7.1 Environment Variables

```python
import os

class ArgoMCPClient:
    def __init__(
        self,
        argo_base_url: str = None,
        mcp_server_command: str = None,
        default_model: str = None
    ):
        """Initialize with environment variable fallbacks."""
        self.argo_base_url = argo_base_url or os.getenv(
            "ARGO_BASE_URL",
            "http://localhost:8000/v1"
        )

        self.mcp_server_command = mcp_server_command or os.getenv(
            "MCP_SERVER_COMMAND",
            "gem-flux-mcp"
        )

        self.default_model = default_model or os.getenv(
            "ARGO_DEFAULT_MODEL",
            "gpt-5"
        )
```

### 7.2 Config File Support

```python
import json
from pathlib import Path

def load_config(config_path: str = None) -> dict:
    """Load configuration from JSON file.

    Args:
        config_path: Path to config file (default: ~/.gem-flux-mcp/config.json)

    Returns:
        Config dict
    """
    if config_path is None:
        config_path = Path.home() / ".gem-flux-mcp" / "config.json"

    if not Path(config_path).exists():
        return {}

    with open(config_path) as f:
        return json.load(f)
```

---

## 8. Testing Strategy

### 8.1 Unit Tests (No Real LLM)

```python
def test_mcp_tool_conversion():
    """Test tool conversion without LLM calls."""
    from gem_flux_mcp.argo_client import MCPToOpenAIConverter

    mcp_tool = {
        "name": "build_model",
        "description": "Build a model",
        "inputSchema": {"type": "object", "properties": {}}
    }

    openai_tool = MCPToOpenAIConverter.convert_tool(mcp_tool)

    assert openai_tool["type"] == "function"
    assert openai_tool["function"]["name"] == "build_model"
```

### 8.2 Integration Tests (Real LLM)

```python
@pytest.mark.real_llm
def test_chat_with_tool_calling():
    """Test actual tool calling with Argo LLM."""
    client = ArgoMCPClient()
    client.initialize_sync()

    response = client.chat("Build a model for E. coli 83333.1")

    assert "model" in response.lower()
    assert len(client.tool_calls_made) > 0
```

---

## 9. File Structure

```
src/gem_flux_mcp/
├── argo_client.py              # ArgoMCPClient implementation
├── conversation.py             # ConversationManager
├── mcp_converter.py            # MCPToOpenAIConverter
└── config.py                   # Configuration loading

tests/
├── unit/
│   ├── test_argo_client.py     # Unit tests (mocked)
│   └── test_mcp_converter.py   # Conversion tests
└── integration/
    └── test_argo_llm_real.py   # Real LLM tests

examples/
└── argo_llm/
    ├── 01_simple_chat.py       # Basic usage
    ├── 02_streaming.py         # Streaming demo
    └── 03_complete_workflow.py # Multi-turn workflow
```

---

## 10. Implementation Phases

### Phase 1: Core Tool Calling (MVP)
- [x] MCPToOpenAIConverter
- [ ] ArgoMCPClient basic chat()
- [ ] Tool calling loop
- [ ] MCP server connection
- [ ] Basic tests

### Phase 2: Streaming Support
- [ ] chat_stream() implementation
- [ ] Chunk accumulation
- [ ] Streaming tests

### Phase 3: Error Handling
- [ ] Circuit breaker pattern
- [ ] Retry logic
- [ ] Error recovery tests

### Phase 4: Configuration
- [ ] Environment variables
- [ ] Config file support
- [ ] Model selection

### Phase 5: Examples and Docs
- [ ] Tutorial scripts
- [ ] Usage documentation
- [ ] Team showcase materials

---

## 11. References

- **OpenAI Python Client**: https://github.com/openai/openai-python
- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **CogniscientAssistant Argo Provider**: `/Users/jplfaria/repos/CogniscientAssistant/src/llm/argo_provider.py`
- **Tool Conversion Spec**: `02-mcp-tool-conversion.md`
- **Testing Patterns**: `03-testing-patterns.md`
