# Argo Gateway LLM Integration Overview

**Date**: 2025-10-29
**Purpose**: Reference documentation for integrating Gem-Flux MCP Server with Argo Gateway LLMs
**Source**: Analysis of `/Users/jplfaria/repos/gem-flux-mcp/specs-source/argo_llm_documentation/`

---

## 1. What is Argo Gateway?

Argo Gateway is Argonne National Laboratory's LLM-as-a-Service platform providing access to multiple LLM providers through a unified interface.

### 1.1 Available Models

| Provider | Models | Strengths |
|----------|--------|-----------|
| OpenAI | GPT-5, GPT-4.1, GPT-4o | General purpose, function calling |
| Anthropic | Claude 4.x (Sonnet, Opus) | Complex reasoning, tool use |
| Google | Gemini 2.5 Pro, o3 | Multimodal, fast inference |

### 1.2 Key Features

- **Tool Calling Support**: All providers support OpenAI-style function calling
- **Streaming**: Real-time token streaming for responsive UIs
- **OpenAI-Compatible API**: Easy integration via `openai` Python package
- **Local Proxy**: `argo-proxy` runs on `localhost:8000` for transparent access

---

## 2. Argo Proxy Architecture

```
┌─────────────────┐
│  Your Python    │
│  Application    │
│  (MCP Client)   │
└────────┬────────┘
         │ HTTP requests to localhost:8000
         ▼
┌─────────────────┐
│  argo-proxy     │  <-- OpenAI-compatible local proxy
│  (localhost)    │
└────────┬────────┘
         │ Authenticated requests
         ▼
┌─────────────────┐
│  Argo Gateway   │  <-- ANL's LLM service
│  (ANL cloud)    │
└────────┬────────┘
         │ Routes to appropriate provider
         ├─────┬──────┬──────┐
         ▼     ▼      ▼      ▼
      OpenAI  Anthropic  Google  Local
```

### 2.1 How argo-proxy Works

1. **Authentication**: Handles ANL credentials automatically
2. **Translation**: Converts OpenAI API format to Argo Gateway format
3. **Routing**: Selects appropriate backend based on model name
4. **Response**: Returns OpenAI-compatible responses

### 2.2 Configuration

```python
from openai import OpenAI

# Point to argo-proxy
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="dummy"  # Not used by proxy
)

# Use any Argo model
response = client.chat.completions.create(
    model="gpt-5",  # or "claude-4-opus", "gemini-2.5-pro"
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## 3. Tool Calling with Argo

All Argo providers support **OpenAI-style function calling**. This is how LLMs interact with MCP tools.

### 3.1 Tool Definition Format

```python
tools = [
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
                        "description": "Unique identifier for the model (e.g., 'ecoli.gf')"
                    },
                    "genome_source": {
                        "type": "string",
                        "enum": ["rast_id", "fasta_file", "annotation_dict"],
                        "description": "Source type for genome data"
                    },
                    "genome_id": {
                        "type": "string",
                        "description": "RAST ID, FASTA path, or annotation dict"
                    }
                },
                "required": ["model_id", "genome_source", "genome_id"]
            }
        }
    }
]
```

### 3.2 Multi-Turn Tool Calling Workflow

```python
# Step 1: User asks a question
messages = [
    {"role": "user", "content": "Build a model for E. coli genome 83333.1"}
]

# Step 2: LLM decides to call a tool
response = client.chat.completions.create(
    model="gpt-5",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

# Response contains tool_calls
tool_call = response.choices[0].message.tool_calls[0]
# tool_call.function.name = "build_model"
# tool_call.function.arguments = '{"model_id": "ecoli.gf", ...}'

# Step 3: Execute the tool via MCP server
import json
args = json.loads(tool_call.function.arguments)
result = mcp_client.call_tool("build_model", args)

# Step 4: Send tool result back to LLM
messages.append(response.choices[0].message)  # Assistant's tool call
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps(result)
})

# Step 5: LLM generates final response
final_response = client.chat.completions.create(
    model="gpt-5",
    messages=messages
)

print(final_response.choices[0].message.content)
# "I've built the E. coli model with ID 'ecoli.gf'. The model contains 1478 reactions..."
```

---

## 4. Why NOT Jupyter Notebooks?

Based on analysis, **Jupyter notebooks are NOT ideal** for showcasing MCP + LLM integration:

### 4.1 Problems with Notebooks

❌ **No streaming support**: Can't show real-time LLM responses
❌ **Hard to test**: Difficult to automate testing with real LLMs
❌ **Static output**: Can't demonstrate multi-turn conversations well
❌ **State management**: Kernel restarts lose conversation history
❌ **Not production-like**: Teams won't deploy notebooks in production

### 4.2 Better Alternatives

✅ **Python scripts**: Easy to run, test, and version control
✅ **Integration tests**: Automated testing with `@pytest.mark.real_llm`
✅ **CLI tools**: Interactive demos via command line
✅ **FastAPI apps**: Web UI for team demos

---

## 5. Recommended Integration Patterns

Based on analysis of CogniscientAssistant project at `/Users/jplfaria/repos/CogniscientAssistant/`:

### 5.1 Circuit Breaker Pattern

Track failures and automatically switch models:

```python
class ArgoProvider:
    def __init__(self):
        self.failure_counts = {}
        self.max_failures = 3
        self.fallback_models = ["gpt-5", "claude-4-opus", "gemini-2.5-pro"]

    def call_with_circuit_breaker(self, model, messages, tools):
        if self.failure_counts.get(model, 0) >= self.max_failures:
            # Circuit open - use fallback
            model = self._get_fallback_model(model)

        try:
            response = self.client.chat.completions.create(
                model=model, messages=messages, tools=tools
            )
            # Success - reset failure count
            self.failure_counts[model] = 0
            return response
        except Exception as e:
            # Failure - increment count
            self.failure_counts[model] = self.failure_counts.get(model, 0) + 1
            raise
```

### 5.2 Real LLM Testing Pattern

```python
import pytest

@pytest.mark.real_llm  # Mark for conditional execution
def test_build_model_with_argo():
    """Integration test with real Argo LLM call."""

    # Setup
    client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
    mcp_tools = get_mcp_tool_definitions()

    # User request
    messages = [
        {"role": "user", "content": "Build a model for E. coli genome 83333.1"}
    ]

    # LLM call
    response = client.chat.completions.create(
        model="gpt-5",
        messages=messages,
        tools=mcp_tools
    )

    # Verify tool call
    assert response.choices[0].message.tool_calls is not None
    tool_call = response.choices[0].message.tool_calls[0]
    assert tool_call.function.name == "build_model"

    # Execute tool
    args = json.loads(tool_call.function.arguments)
    result = execute_mcp_tool(tool_call.function.name, args)

    # Verify result
    assert result["status"] == "success"
    assert "ecoli" in result["model_id"]
```

Run with: `pytest -m real_llm` (only when argo-proxy is running)

### 5.3 Streaming Response Pattern

```python
def stream_llm_response(client, messages, tools):
    """Show real-time LLM response with tool calling."""

    stream = client.chat.completions.create(
        model="gpt-5",
        messages=messages,
        tools=tools,
        stream=True
    )

    current_tool_call = None

    for chunk in stream:
        delta = chunk.choices[0].delta

        if delta.content:
            # Regular text response
            print(delta.content, end="", flush=True)

        elif delta.tool_calls:
            # Tool call in progress
            for tool_call_delta in delta.tool_calls:
                if tool_call_delta.function.name:
                    print(f"\n[Calling tool: {tool_call_delta.function.name}]")
                    current_tool_call = tool_call_delta
                elif tool_call_delta.function.arguments:
                    # Accumulate arguments
                    pass

    print()  # Newline after streaming
    return current_tool_call
```

---

## 6. MCP + Argo Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Application                      │
│  (CLI, FastAPI, or Test Suite)                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ 1. User query
                 ▼
┌─────────────────────────────────────────────────────────┐
│              ArgoMCPClient (our code)                    │
│  - Manages conversation state                           │
│  - Converts MCP tools → OpenAI tool format              │
│  - Handles multi-turn tool calling loop                 │
└────────┬────────────────────────────┬───────────────────┘
         │                            │
         │ 2. Chat request            │ 4. Execute tool
         │    with tools              │    call
         ▼                            ▼
┌─────────────────┐         ┌─────────────────────────────┐
│  argo-proxy     │         │  Gem-Flux MCP Server        │
│  (localhost)    │         │  (FastMCP-based)            │
└────────┬────────┘         └─────────────────────────────┘
         │
         │ 3. Returns tool_calls
         ▼
┌─────────────────┐
│  Argo Gateway   │
│  LLMs           │
└─────────────────┘
```

### 6.1 Component Responsibilities

**ArgoMCPClient**:
- Connects to both argo-proxy and MCP server
- Manages conversation history (messages list)
- Converts MCP tool schemas to OpenAI format
- Executes multi-turn tool calling loop
- Handles streaming and error recovery

**argo-proxy**:
- Authenticates with ANL credentials
- Routes requests to appropriate LLM provider
- Returns OpenAI-compatible responses

**Gem-Flux MCP Server**:
- Provides MCP tool definitions
- Executes tool calls (build_model, gapfill_model, etc.)
- Returns structured results

---

## 7. Next Steps

1. **Create `ArgoMCPClient` class** (`src/gem_flux_mcp/argo_client.py`)
   - Connect to argo-proxy and MCP server
   - Convert MCP tools to OpenAI format
   - Implement multi-turn tool calling loop

2. **Create integration tests** (`tests/integration/test_argo_llm_real.py`)
   - Mark with `@pytest.mark.real_llm`
   - Test each MCP tool with real LLM calls
   - Verify tool calling and results

3. **Create tutorial scripts** (`examples/argo_llm/`)
   - `01_simple_model_building.py`: Single tool call
   - `02_complete_workflow.py`: Multi-turn conversation
   - `03_interactive_cli.py`: Command-line chat interface

4. **Document for team** (`docs/argo-llm-integration.md`)
   - How to set up argo-proxy
   - How to run examples
   - How to test with real LLMs
   - How to integrate in their own projects

---

## 8. References

- **Argo Gateway Docs**: `/Users/jplfaria/repos/gem-flux-mcp/specs-source/argo_llm_documentation/`
- **CogniscientAssistant Patterns**: `/Users/jplfaria/repos/CogniscientAssistant/`
  - `src/llm/argo_provider.py`: Circuit breaker implementation
  - `tests/integration/test_phase8_argo_real.py`: Real LLM testing
  - `src/mcp/tools.py`: MCP tool implementations
- **OpenAI Function Calling Docs**: https://platform.openai.com/docs/guides/function-calling
- **MCP Protocol Spec**: https://spec.modelcontextprotocol.io/
