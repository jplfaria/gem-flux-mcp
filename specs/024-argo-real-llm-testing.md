# Argo Real LLM Testing Specification

**Type**: Testing Specification
**Status**: Phase 11.5 - Argo LLM Integration
**Version**: MVP v0.1.0
**Depends On**: 022-argo-llm-integration.md, 023-mcp-tool-conversion.md

## Prerequisites

- Read: **022-argo-llm-integration.md** (ArgoMCPClient)
- Read: **023-mcp-tool-conversion.md** (Tool conversion)
- Understand: pytest markers and fixtures
- Understand: Real vs mocked testing trade-offs
- Access: argo-proxy running on localhost:8000

## Purpose

This specification defines testing patterns for validating MCP tools with real LLM interactions via Argo Gateway. It establishes best practices for expensive, slow, but critical integration tests that verify LLMs can actually understand and use our tools.

## Testing Philosophy

### Why Test with Real LLMs?

**Unit tests with mocks are insufficient** for LLM + tool integration:

❌ **Unit Tests Alone Cannot Verify**:
- LLM understands tool descriptions correctly
- Parameter descriptions are clear to LLMs
- Enum values make sense in natural language
- Multi-turn conversation flows work
- Error messages guide LLM to recovery
- Tool calling format is compatible

✅ **Real LLM Integration Tests Validate**:
- LLM correctly interprets tool descriptions
- Parameter descriptions enable correct usage
- Natural language → tool call mapping works
- Realistic conversation patterns function
- Error handling leads to recovery
- Model-specific quirks are caught

### Testing Pyramid

```
        ┌────────────────┐
        │  Manual/Demo   │  <-- Interactive demos (rare)
        │   (rare)       │
        └────────────────┘
               ▲
        ┌────────────────┐
        │  Real LLM      │  <-- @pytest.mark.real_llm (selective)
        │  Tests         │      Run manually when argo-proxy available
        │  (selective)   │      ~10-15 critical tests
        └────────────────┘
               ▲
        ┌────────────────┐
        │  Unit Tests    │  <-- Fast tests with mocks (majority)
        │  (majority)    │      Run in CI on every commit
        │                │      785+ existing tests
        └────────────────┘
```

**Goal**: Most tests are fast unit tests, critical flows have real LLM coverage.

## Test Organization

### Directory Structure

```
tests/
├── unit/                           # Fast tests (mocked)
│   ├── test_build_model.py
│   ├── test_gapfill_model.py
│   └── test_argo_client_unit.py   # ArgoMCPClient with mocks
│
├── integration/
│   ├── test_phase11_mcp_server.py           # MCP server tests
│   ├── test_phase17_argo_llm_real.py        # Real LLM tests (THIS SPEC)
│   └── conftest.py                          # Argo fixtures
│
└── conftest.py                               # Root pytest config
```

### Pytest Configuration

**tests/conftest.py**:
```python
import pytest
import socket

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "real_llm: mark test as requiring real LLM API calls (expensive, slow)"
    )

@pytest.fixture
def argo_available():
    """Check if argo-proxy is available on localhost:8000.

    Skips test if argo-proxy is not running.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()

    if result != 0:
        pytest.skip("argo-proxy not running on localhost:8000")
```

**tests/integration/conftest.py**:
```python
import pytest
from gem_flux_mcp.argo import ArgoMCPClient

@pytest.fixture
def argo_client(argo_available):
    """Provide initialized ArgoMCPClient for tests."""
    client = ArgoMCPClient()
    client.initialize_sync()
    yield client
    # Cleanup - reset conversation after each test
    client.reset()
```

### Running Tests Selectively

```bash
# Run all tests EXCEPT real LLM tests (default for CI)
pytest -m "not real_llm"

# Run ONLY real LLM tests (when argo-proxy is running)
pytest -m real_llm

# Run specific real LLM test
pytest tests/integration/test_phase17_argo_llm_real.py::test_build_model_with_argo -v

# Run all tests including real LLM (local development)
pytest
```

## Real LLM Test Patterns

### Pattern 1: Basic Tool Calling

Tests that LLM correctly calls a single tool.

```python
@pytest.mark.real_llm
def test_build_media_with_argo(argo_client):
    """Test that Argo LLM correctly calls build_media tool.

    Validates:
    - LLM understands build_media description
    - LLM provides correct parameter format
    - Tool executes successfully
    - LLM generates coherent response
    """
    # User request in natural language
    response = argo_client.chat(
        "Create a minimal growth medium with glucose, ammonia, and phosphate"
    )

    # Verify response mentions media creation
    assert "media" in response.lower() or "medium" in response.lower()
    assert "created" in response.lower() or "built" in response.lower()

    # Verify tool was actually called
    assert len(argo_client.tool_calls_made) > 0
    tool_call = argo_client.tool_calls_made[0]
    assert tool_call["tool_name"] == "build_media"

    # Verify arguments are reasonable
    args = tool_call["arguments"]
    assert "compounds" in args
    assert isinstance(args["compounds"], list)
    assert len(args["compounds"]) >= 3  # glucose, ammonia, phosphate

    # Verify result is success
    assert tool_call["result"]["status"] == "success"
```

**Key Patterns**:
- Use semantic assertions ("media" or "medium") not exact strings
- Verify tool was called, not just response text
- Check argument structure makes sense
- Validate tool execution succeeded

### Pattern 2: Multi-Turn Conversation

Tests that LLM maintains context across multiple turns.

```python
@pytest.mark.real_llm
def test_complete_workflow_conversation(argo_client):
    """Test multi-turn conversation through complete workflow.

    Validates:
    - LLM maintains context between turns
    - Model ID from first call used in subsequent calls
    - Conversation flow is natural
    - All tools in workflow execute successfully
    """
    # Turn 1: Build model
    response1 = argo_client.chat("Build a metabolic model for E. coli genome 83333.1")
    assert "model" in response1.lower()
    assert "built" in response1.lower() or "created" in response1.lower()

    # Extract model_id from tool calls
    model_id = None
    for call in argo_client.tool_calls_made:
        if call["tool_name"] == "build_model":
            model_id = call["result"].get("model_id")
            break

    assert model_id is not None, "build_model did not return model_id"

    # Turn 2: Gapfill (should use model_id from context)
    response2 = argo_client.chat("Now gapfill it on minimal media")
    assert "gapfill" in response2.lower()

    # Verify gapfill used correct model_id
    gapfill_call = None
    for call in argo_client.tool_calls_made:
        if call["tool_name"] == "gapfill_model":
            gapfill_call = call
            break

    assert gapfill_call is not None
    assert gapfill_call["arguments"]["model_id"] == model_id

    # Turn 3: Run FBA
    response3 = argo_client.chat("Run FBA and tell me the growth rate")
    assert "growth" in response3.lower() or "fba" in response3.lower()

    # Verify all three tools were called
    tools_used = {call["tool_name"] for call in argo_client.tool_calls_made}
    assert "build_model" in tools_used
    assert "gapfill_model" in tools_used
    assert "run_fba" in tools_used
```

**Key Patterns**:
- Extract data from previous tool calls to verify context
- Verify LLM uses extracted data in subsequent calls
- Check all expected tools in workflow were called
- Validate logical flow of conversation

### Pattern 3: Parameter Understanding

Tests that LLM correctly interprets parameter values from natural language.

```python
@pytest.mark.real_llm
@pytest.mark.parametrize("user_request,expected_tool,expected_params", [
    (
        "Build a model from RAST ID 83333.1",
        "build_model",
        {"genome_source": "rast_id", "genome_id": "83333.1"}
    ),
    (
        "Build a model from FASTA file genome.fna",
        "build_model",
        {"genome_source": "fasta_file"}
    ),
    (
        "Gapfill on glucose minimal media",
        "gapfill_model",
        {"media_id": "glucose_minimal_aerobic"}  # Predefined media
    ),
    (
        "Run FBA and minimize ATP production",
        "run_fba",
        {"maximize": False}
    ),
])
def test_llm_parameter_understanding(argo_client, user_request, expected_tool, expected_params):
    """Test that LLM correctly interprets parameter values from natural language.

    Validates:
    - LLM maps natural language to correct enum values
    - LLM infers correct boolean values (minimize → maximize=False)
    - LLM selects appropriate predefined media
    """
    # Make request
    response = argo_client.chat(user_request)

    # Find the expected tool call
    tool_call = None
    for call in argo_client.tool_calls_made:
        if call["tool_name"] == expected_tool:
            tool_call = call
            break

    assert tool_call is not None, f"Expected tool {expected_tool} was not called"

    # Verify expected parameters
    for param_name, expected_value in expected_params.items():
        assert param_name in tool_call["arguments"], \
            f"Parameter {param_name} not in arguments"
        assert tool_call["arguments"][param_name] == expected_value, \
            f"Parameter {param_name} has wrong value: {tool_call['arguments'][param_name]}"
```

**Key Patterns**:
- Use `@pytest.mark.parametrize` for multiple test cases
- Test enum value mapping (natural language → enum)
- Test boolean inference ("minimize" → `maximize=False`)
- Test predefined value selection (media names)

### Pattern 4: Error Handling

Tests that LLM handles tool errors gracefully and recovers.

```python
@pytest.mark.real_llm
def test_llm_handles_tool_errors_gracefully(argo_client):
    """Test that LLM handles tool errors and suggests recovery.

    Validates:
    - LLM acknowledges error in response
    - LLM suggests corrective action
    - LLM doesn't crash or give nonsensical response
    """
    # Request that will cause error (nonexistent model)
    response = argo_client.chat("Run FBA on nonexistent_model.gf with minimal media")

    # LLM should acknowledge error
    error_indicators = ["error", "not found", "doesn't exist", "cannot find", "invalid"]
    assert any(indicator in response.lower() for indicator in error_indicators), \
        f"Response did not acknowledge error: {response}"

    # LLM should suggest fix
    fix_indicators = ["build", "create", "first"]
    assert any(indicator in response.lower() for indicator in fix_indicators), \
        f"Response did not suggest fix: {response}"

    # Verify error was logged in tool calls
    assert len(argo_client.tool_calls_made) > 0
    last_call = argo_client.tool_calls_made[-1]
    assert last_call["result"]["status"] == "error"
```

**Key Patterns**:
- Test with inputs that cause errors
- Use multiple possible error indicators (LLM phrasing varies)
- Verify LLM suggests corrective action
- Check error is properly logged

### Pattern 5: Streaming

Tests that streaming works with tool calls.

```python
@pytest.mark.real_llm
def test_streaming_with_tool_calls(argo_client):
    """Test that streaming works with tool calls.

    Validates:
    - Chunks arrive incrementally
    - Tool call notifications appear in stream
    - Complete response is coherent
    """
    # Collect streamed chunks
    chunks = []

    def chunk_handler(chunk: str):
        chunks.append(chunk)
        print(chunk, end="", flush=True)

    # Make streaming request
    list(argo_client.chat_stream(
        "Build a metabolic model for E. coli",
        on_chunk=chunk_handler
    ))

    # Verify we got multiple chunks (streaming worked)
    assert len(chunks) > 1, "Expected multiple chunks but got single response"

    # Verify complete response is coherent
    full_response = "".join(chunks)
    assert "model" in full_response.lower()

    # Verify tool was called
    assert len(argo_client.tool_calls_made) > 0
```

**Key Patterns**:
- Collect chunks to verify streaming
- Use callback to print real-time (for manual observation)
- Verify chunk count > 1
- Verify reassembled response is coherent

## Test Phase Definition

### Phase 17 Test Configuration

**File**: `tests/integration/test_expectations.json`

```json
{
  "phase_17": {
    "name": "Argo LLM Integration",
    "must_pass": [
      "test_mcp_to_openai_converter_basic",
      "test_mcp_to_openai_converter_all_tools",
      "test_mcp_to_openai_converter_removes_defaults",
      "test_mcp_to_openai_converter_preserves_enum",
      "test_argo_client_initialization",
      "test_argo_client_message_history",
      "test_argo_client_tool_call_logging",
      "test_argo_client_reset"
    ],
    "may_fail": [
      "test_streaming_basic",
      "test_streaming_with_tool_calls",
      "test_circuit_breaker",
      "test_model_switching"
    ],
    "real_llm_tests": [
      "test_build_media_with_argo",
      "test_build_model_with_argo",
      "test_gapfill_model_with_argo",
      "test_run_fba_with_argo",
      "test_complete_workflow_conversation",
      "test_llm_parameter_understanding",
      "test_llm_handles_tool_errors_gracefully",
      "test_streaming_with_tool_calls"
    ]
  }
}
```

**Test Categories**:
- **must_pass**: Unit tests (mocked, always run)
- **may_fail**: Experimental features (allowed to fail)
- **real_llm_tests**: Real LLM integration tests (run manually)

## Test File Structure

**tests/integration/test_phase17_argo_llm_real.py**:

```python
"""Real LLM integration tests for Argo Gateway.

These tests require argo-proxy running on localhost:8000.
Run with: pytest -m real_llm
Skip with: pytest -m "not real_llm"
"""

import pytest
from gem_flux_mcp.argo import ArgoMCPClient


@pytest.mark.real_llm
def test_build_media_with_argo(argo_client):
    """Test LLM can call build_media tool."""
    # Implementation...


@pytest.mark.real_llm
def test_build_model_with_argo(argo_client):
    """Test LLM can call build_model tool."""
    # Implementation...


@pytest.mark.real_llm
def test_gapfill_model_with_argo(argo_client):
    """Test LLM can call gapfill_model tool."""
    # Implementation...


@pytest.mark.real_llm
def test_run_fba_with_argo(argo_client):
    """Test LLM can call run_fba tool."""
    # Implementation...


@pytest.mark.real_llm
def test_complete_workflow_conversation(argo_client):
    """Test multi-turn conversation through complete workflow."""
    # Implementation...


@pytest.mark.real_llm
@pytest.mark.parametrize("user_request,expected_tool,expected_params", [
    # Test cases...
])
def test_llm_parameter_understanding(argo_client, user_request, expected_tool, expected_params):
    """Test LLM parameter interpretation."""
    # Implementation...


@pytest.mark.real_llm
def test_llm_handles_tool_errors_gracefully(argo_client):
    """Test LLM error handling."""
    # Implementation...


@pytest.mark.real_llm
def test_streaming_with_tool_calls(argo_client):
    """Test streaming functionality."""
    # Implementation...
```

## Assertion Best Practices

### DO: Semantic Assertions

```python
# GOOD - flexible, works with different LLM phrasings
assert "model" in response.lower()
assert "built" in response.lower() or "created" in response.lower()

# GOOD - multiple acceptable indicators
error_words = ["error", "not found", "doesn't exist"]
assert any(word in response.lower() for word in error_words)
```

### DON'T: Exact String Matching

```python
# BAD - too brittle, fails if LLM rephrases
assert response == "I've built the model successfully"

# BAD - assumes exact phrasing
assert "I have built" in response
```

### DO: Verify Tool Calls, Not Just Responses

```python
# GOOD - verifies actual behavior
assert len(argo_client.tool_calls_made) > 0
assert argo_client.tool_calls_made[0]["tool_name"] == "build_model"

# GOOD - checks tool arguments
assert "model_id" in argo_client.tool_calls_made[0]["arguments"]
```

### DON'T: Trust Response Text Alone

```python
# BAD - LLM could hallucinate without calling tool
assert "model built" in response  # No verification tool was actually called
```

## Cost and Performance Considerations

### Test Execution Time

Real LLM tests are **expensive** in both time and resources:

| Test Type | Execution Time | Cost | When to Run |
|-----------|---------------|------|-------------|
| Unit test | <1 second | Free | Every commit (CI) |
| Real LLM test | 5-30 seconds | API cost | Manual, pre-release |

**Recommendations**:
- Keep real LLM test count low (~10-15 tests)
- Focus on critical paths
- Run locally before major releases
- NOT in CI (too slow, requires argo-proxy)

### Reducing Test Time

```python
# Use default model (fastest)
client = ArgoMCPClient(default_model="gpt-5")  # Fastest

# Avoid streaming tests when not needed
# Streaming adds overhead

# Use parametrize to combine similar tests
@pytest.mark.parametrize("test_case", [...])
def test_multiple_scenarios(test_case):
    # One test function, multiple scenarios
```

## Success Criteria

Argo real LLM testing is successful when:

1. ✅ All 8 real_llm_tests pass with argo-proxy running
2. ✅ LLMs correctly call all core tools (build_media, build_model, gapfill_model, run_fba)
3. ✅ Multi-turn conversation maintains context
4. ✅ Parameter understanding tests pass (enums, booleans, predefined values)
5. ✅ Error handling test shows LLM recovers gracefully
6. ✅ Streaming test demonstrates real-time response
7. ✅ Tests run cleanly with `pytest -m real_llm`
8. ✅ Tests skip cleanly when argo-proxy unavailable

## Alignment with Other Specifications

**Validates**:
- **022-argo-llm-integration.md**: ArgoMCPClient functionality
- **023-mcp-tool-conversion.md**: Tool conversion correctness
- **021-mcp-tool-registration.md**: MCP tool definitions work with LLMs

**Depends On**:
- **022-argo-llm-integration.md**: ArgoMCPClient must exist
- **023-mcp-tool-conversion.md**: Converter must work

**Enables**:
- Confidence in LLM integration
- Detection of prompt engineering issues
- Validation of tool descriptions
- Team showcase readiness

---

**This specification defines comprehensive testing patterns for validating MCP tools with real LLM interactions, ensuring production-ready natural language interfaces to metabolic modeling.**
