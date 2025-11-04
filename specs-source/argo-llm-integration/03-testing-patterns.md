# Testing Patterns for MCP + Argo LLM Integration

**Date**: 2025-10-29
**Purpose**: Best practices for testing MCP tools with real LLM interactions
**Source**: Patterns from CogniscientAssistant project

---

## 1. Testing Philosophy

### 1.1 Why Test with Real LLMs?

**Unit tests with mocks are not enough** for LLM + tool integration:

❌ **Unit Tests Alone**:
- Can't verify LLM understands tool descriptions
- Can't catch prompt engineering issues
- Can't validate tool call format compatibility
- Can't test multi-turn conversation flows

✅ **Real LLM Integration Tests**:
- Verify LLM correctly interprets tool descriptions
- Catch issues with parameter descriptions/enums
- Validate actual tool calling format
- Test realistic conversation patterns
- Detect model-specific quirks

### 1.2 Testing Pyramid

```
        ┌─────────────────┐
        │  Manual/Demo    │  <-- Interactive CLI demos
        │   (rare)        │
        └─────────────────┘
               ▲
        ┌─────────────────┐
        │  Real LLM Tests │  <-- Integration tests with @pytest.mark.real_llm
        │   (selective)   │
        └─────────────────┘
               ▲
        ┌─────────────────┐
        │   Unit Tests    │  <-- Fast tests with mocks
        │   (majority)    │
        └─────────────────┘
```

**Goal**: Most tests are fast unit tests, but critical flows have real LLM coverage.

---

## 2. Test Organization

### 2.1 Directory Structure

```
tests/
├── unit/                          # Fast tests with mocks
│   ├── test_build_model.py
│   ├── test_gapfill_model.py
│   └── test_run_fba.py
│
├── integration/                   # Real LLM tests
│   ├── test_argo_llm_real.py     # <-- Real Argo LLM calls
│   ├── test_mcp_server.py
│   └── conftest.py                # Shared fixtures
│
└── conftest.py                    # Root fixtures
```

### 2.2 Pytest Markers

Define in `tests/conftest.py`:

```python
import pytest

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "real_llm: mark test as requiring real LLM API calls (expensive, slow)"
    )

# Fixture to check if argo-proxy is running
@pytest.fixture
def argo_available():
    """Check if argo-proxy is available."""
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()

    if result != 0:
        pytest.skip("argo-proxy not running on localhost:8000")
```

### 2.3 Running Tests Selectively

```bash
# Run all tests EXCEPT real LLM tests (default for CI)
pytest -m "not real_llm"

# Run ONLY real LLM tests (when argo-proxy is running)
pytest -m real_llm

# Run specific real LLM test
pytest tests/integration/test_argo_llm_real.py::test_build_model_with_argo -v

# Run all tests including real LLM (local development)
pytest
```

---

## 3. Real LLM Test Patterns

### 3.1 Basic Real LLM Test

```python
import pytest
import json
from openai import OpenAI
from gem_flux_mcp.argo_client import ArgoMCPClient

@pytest.mark.real_llm
def test_build_model_tool_calling(argo_available):
    """Test that Argo LLM correctly calls build_model tool."""

    # Setup
    client = ArgoMCPClient()

    # User request that should trigger build_model
    user_message = "Build a metabolic model for E. coli genome 83333.1"

    # Get LLM response (with automatic tool calling)
    response = client.chat(user_message, model="gpt-5")

    # Verify response mentions model was built
    assert "model" in response.lower()
    assert "built" in response.lower() or "created" in response.lower()

    # Verify tool was actually called
    assert len(client.tool_calls_made) > 0
    assert client.tool_calls_made[0]["tool_name"] == "build_model"

    # Verify arguments are reasonable
    args = client.tool_calls_made[0]["arguments"]
    assert "model_id" in args
    assert args["model_id"].endswith(".gf")
```

### 3.2 Multi-Turn Conversation Test

```python
@pytest.mark.real_llm
def test_complete_workflow_conversation(argo_available):
    """Test multi-turn conversation through complete workflow."""

    client = ArgoMCPClient()

    # Turn 1: Build model
    response1 = client.chat("Build a model for E. coli genome 83333.1")
    assert "built" in response1.lower()

    # Extract model_id from conversation history
    model_id = None
    for call in client.tool_calls_made:
        if call["tool_name"] == "build_model":
            model_id = call["arguments"]["model_id"]
            break

    assert model_id is not None

    # Turn 2: Gapfill (should use model_id from context)
    response2 = client.chat(f"Gapfill {model_id} on complete media")
    assert "gapfill" in response2.lower()

    # Turn 3: Run FBA
    response3 = client.chat(f"Run FBA on {model_id}")
    assert "growth" in response3.lower() or "fba" in response3.lower()

    # Verify all three tools were called
    tools_used = {call["tool_name"] for call in client.tool_calls_made}
    assert tools_used == {"build_model", "gapfill_model", "run_fba"}
```

### 3.3 Parameter Understanding Test

```python
@pytest.mark.real_llm
@pytest.mark.parametrize("user_request,expected_tool,expected_params", [
    (
        "Build a model from RAST ID 83333.1",
        "build_model",
        {"genome_source": "rast_id"}
    ),
    (
        "Build a model from FASTA file genome.fna",
        "build_model",
        {"genome_source": "fasta_file"}
    ),
    (
        "Gapfill on minimal media",
        "gapfill_model",
        {"media_id": "minimal"}  # Predefined media
    ),
    (
        "Run FBA and minimize ATP production",
        "run_fba",
        {"maximize": False}
    ),
])
def test_llm_parameter_understanding(argo_available, user_request, expected_tool, expected_params):
    """Test that LLM correctly interprets parameter values from natural language."""

    client = ArgoMCPClient()

    # Make request
    response = client.chat(user_request)

    # Find the expected tool call
    tool_call = None
    for call in client.tool_calls_made:
        if call["tool_name"] == expected_tool:
            tool_call = call
            break

    assert tool_call is not None, f"Expected tool {expected_tool} was not called"

    # Verify expected parameters
    for param_name, expected_value in expected_params.items():
        assert param_name in tool_call["arguments"]
        assert tool_call["arguments"][param_name] == expected_value
```

### 3.4 Error Handling Test

```python
@pytest.mark.real_llm
def test_llm_handles_tool_errors_gracefully(argo_available):
    """Test that LLM handles tool errors and recovers."""

    client = ArgoMCPClient()

    # Request that will cause error (invalid model_id)
    response = client.chat("Run FBA on nonexistent_model.gf")

    # LLM should acknowledge error
    assert "error" in response.lower() or "not found" in response.lower() or "doesn't exist" in response.lower()

    # LLM should suggest fix
    assert "build" in response.lower() or "create" in response.lower()
```

### 3.5 Streaming Response Test

```python
@pytest.mark.real_llm
def test_streaming_with_tool_calls(argo_available):
    """Test that streaming works with tool calls."""

    client = ArgoMCPClient()

    # Collect streamed chunks
    chunks = []

    def chunk_handler(chunk: str):
        chunks.append(chunk)
        print(chunk, end="", flush=True)

    # Make streaming request
    response = client.chat_stream(
        "Build a model for E. coli",
        on_chunk=chunk_handler
    )

    # Verify we got multiple chunks
    assert len(chunks) > 1

    # Verify complete response is coherent
    full_response = "".join(chunks)
    assert "model" in full_response.lower()
```

---

## 4. Test Fixtures

### 4.1 ArgoMCPClient Fixture

```python
# tests/integration/conftest.py

import pytest
from gem_flux_mcp.argo_client import ArgoMCPClient

@pytest.fixture
def argo_client():
    """Provide ArgoMCPClient instance for tests."""
    client = ArgoMCPClient()
    yield client
    # Cleanup: delete any models created during test
    for model_id in client.models_created:
        try:
            client.delete_model(model_id)
        except Exception:
            pass  # Best effort cleanup

@pytest.fixture
def sample_genome_id():
    """Provide sample genome ID for testing."""
    return "83333.1"  # E. coli K-12

@pytest.fixture
def sample_fasta_file(tmp_path):
    """Create temporary FASTA file for testing."""
    fasta_content = """>gene1
ATGCGATCGATCGATCG
>gene2
GCTAGCTAGCTAGCTAG
"""
    fasta_file = tmp_path / "genome.fna"
    fasta_file.write_text(fasta_content)
    return str(fasta_file)
```

### 4.2 Model Cleanup Fixture

```python
@pytest.fixture
def auto_cleanup_models(argo_client):
    """Automatically cleanup models created during test."""
    models_before = set(argo_client.list_models())

    yield argo_client

    # Cleanup: delete any new models
    models_after = set(argo_client.list_models())
    new_models = models_after - models_before

    for model_id in new_models:
        try:
            argo_client.delete_model(model_id)
        except Exception as e:
            print(f"Failed to cleanup {model_id}: {e}")
```

---

## 5. Assertion Strategies

### 5.1 Semantic Assertions (LLM Responses)

For LLM-generated text, use **semantic assertions** instead of exact string matching:

```python
def assert_mentions_growth(response: str):
    """Assert response mentions growth/FBA results."""
    keywords = ["growth", "rate", "objective", "flux", "hr⁻¹", "mmol"]
    assert any(kw in response.lower() for kw in keywords), \
        f"Response doesn't mention growth: {response}"

def assert_acknowledges_error(response: str):
    """Assert response acknowledges an error occurred."""
    error_phrases = ["error", "failed", "not found", "doesn't exist", "couldn't"]
    assert any(phrase in response.lower() for phrase in error_phrases), \
        f"Response doesn't acknowledge error: {response}"
```

### 5.2 Tool Call Assertions

For tool calls, use **structural assertions**:

```python
def assert_tool_called(client, tool_name: str):
    """Assert specific tool was called."""
    tools_called = [call["tool_name"] for call in client.tool_calls_made]
    assert tool_name in tools_called, \
        f"Tool {tool_name} not called. Called: {tools_called}"

def assert_parameter_has_type(tool_call, param_name: str, expected_type: type):
    """Assert parameter has expected type."""
    assert param_name in tool_call["arguments"]
    value = tool_call["arguments"][param_name]
    assert isinstance(value, expected_type), \
        f"Parameter {param_name} has type {type(value)}, expected {expected_type}"
```

---

## 6. Circuit Breaker Pattern

Pattern from CogniscientAssistant for handling model failures:

```python
# tests/integration/conftest.py

import pytest
from collections import defaultdict

class CircuitBreaker:
    """Track model failures and switch to fallback."""

    def __init__(self, max_failures: int = 3):
        self.max_failures = max_failures
        self.failure_counts = defaultdict(int)
        self.fallback_models = ["gpt-5", "claude-4-opus", "gemini-2.5-pro"]

    def record_failure(self, model: str):
        """Record a failure for a model."""
        self.failure_counts[model] += 1

    def is_circuit_open(self, model: str) -> bool:
        """Check if circuit is open (too many failures)."""
        return self.failure_counts[model] >= self.max_failures

    def get_fallback_model(self, failed_model: str) -> str:
        """Get fallback model when circuit is open."""
        for model in self.fallback_models:
            if not self.is_circuit_open(model):
                return model
        # All models failed - reset and try again
        self.failure_counts.clear()
        return self.fallback_models[0]

@pytest.fixture
def circuit_breaker():
    """Provide circuit breaker for model failure handling."""
    return CircuitBreaker()
```

Usage in tests:

```python
@pytest.mark.real_llm
def test_with_circuit_breaker(argo_client, circuit_breaker):
    """Test with automatic fallback on model failures."""

    model = "gpt-5"

    while circuit_breaker.is_circuit_open(model):
        model = circuit_breaker.get_fallback_model(model)

    try:
        response = argo_client.chat("Build a model", model=model)
        # Success - test passes
        assert "model" in response.lower()
    except Exception as e:
        # Failure - record and retry
        circuit_breaker.record_failure(model)
        pytest.fail(f"All models failed: {e}")
```

---

## 7. Test Data Management

### 7.1 Predefined Test Data

```python
# tests/integration/test_data.py

SAMPLE_GENOMES = {
    "ecoli": {
        "rast_id": "83333.1",
        "description": "E. coli K-12 MG1655"
    },
    "saureus": {
        "rast_id": "93061.1",
        "description": "S. aureus NCTC 8325"
    }
}

SAMPLE_MEDIA = {
    "complete": "Complete media (all compounds)",
    "minimal": "Minimal media (glucose minimal)",
    "rich": "Rich media (LB-like)"
}

TEST_SCENARIOS = [
    {
        "name": "complete_workflow",
        "steps": [
            {"action": "build", "genome": "ecoli"},
            {"action": "gapfill", "media": "complete"},
            {"action": "fba", "media": "complete"}
        ]
    },
    {
        "name": "minimal_media_gapfill",
        "steps": [
            {"action": "build", "genome": "ecoli"},
            {"action": "gapfill", "media": "minimal"},
            {"action": "fba", "media": "minimal"}
        ]
    }
]
```

### 7.2 Using Test Data

```python
import pytest
from tests.integration.test_data import SAMPLE_GENOMES, TEST_SCENARIOS

@pytest.mark.real_llm
@pytest.mark.parametrize("scenario", TEST_SCENARIOS, ids=lambda s: s["name"])
def test_workflow_scenario(argo_client, scenario):
    """Test predefined workflow scenarios."""

    for step in scenario["steps"]:
        if step["action"] == "build":
            genome = SAMPLE_GENOMES[step["genome"]]
            response = argo_client.chat(
                f"Build a model for {genome['description']}"
            )
            assert "model" in response.lower()

        elif step["action"] == "gapfill":
            response = argo_client.chat(
                f"Gapfill on {step['media']} media"
            )
            assert "gapfill" in response.lower()

        elif step["action"] == "fba":
            response = argo_client.chat("Run FBA")
            assert "growth" in response.lower()
```

---

## 8. Performance Testing

### 8.1 Response Time Tracking

```python
@pytest.mark.real_llm
def test_response_time_reasonable(argo_client):
    """Test that LLM + tool call completes in reasonable time."""
    import time

    start = time.time()
    response = argo_client.chat("Build a model for E. coli 83333.1")
    duration = time.time() - start

    # Should complete in under 30 seconds
    assert duration < 30, f"Response took {duration:.1f}s (too slow)"

    # Record timing for analysis
    print(f"\nResponse time: {duration:.2f}s")
```

### 8.2 Token Usage Tracking

```python
@pytest.mark.real_llm
def test_token_usage_reasonable(argo_client):
    """Test that tool calls don't use excessive tokens."""

    response = argo_client.chat("Build a model for E. coli")

    # Check usage
    usage = argo_client.last_usage
    total_tokens = usage["total_tokens"]

    # Should be under 2000 tokens for simple request
    assert total_tokens < 2000, f"Used {total_tokens} tokens (too many)"

    print(f"\nTokens: {total_tokens} (prompt: {usage['prompt_tokens']}, completion: {usage['completion_tokens']})")
```

---

## 9. CI/CD Integration

### 9.1 GitHub Actions Example

```yaml
# .github/workflows/test.yml

name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run unit tests (fast)
        run: uv run pytest -m "not real_llm" -v

  integration-tests:
    runs-on: ubuntu-latest
    # Only run on main branch or manual trigger
    if: github.ref == 'refs/heads/main' || github.event_name == 'workflow_dispatch'

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Start argo-proxy
        run: |
          # Setup ANL credentials from secrets
          echo "${{ secrets.ANL_USERNAME }}" > ~/.anl_username
          # Start argo-proxy in background
          nohup argo-proxy &
          sleep 5  # Wait for startup

      - name: Run real LLM tests
        run: uv run pytest -m real_llm -v
        timeout-minutes: 10  # Prevent hanging
```

### 9.2 Local Testing Script

```bash
#!/bin/bash
# scripts/test_with_argo.sh

echo "Starting argo-proxy..."
argo-proxy &
PROXY_PID=$!

# Wait for proxy to start
sleep 5

# Check if proxy is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "ERROR: argo-proxy failed to start"
    kill $PROXY_PID
    exit 1
fi

echo "Running real LLM tests..."
uv run pytest -m real_llm -v

# Capture test exit code
TEST_EXIT=$?

# Cleanup
echo "Stopping argo-proxy..."
kill $PROXY_PID

exit $TEST_EXIT
```

---

## 10. Best Practices Summary

### DO

✅ Use `@pytest.mark.real_llm` for expensive tests
✅ Test critical paths with real LLMs
✅ Use semantic assertions for LLM responses
✅ Use structural assertions for tool calls
✅ Implement circuit breaker for model failures
✅ Track response times and token usage
✅ Cleanup test resources (models, media)
✅ Run unit tests frequently, real LLM tests selectively
✅ Document expected behavior in test docstrings

### DON'T

❌ Test every edge case with real LLMs (too slow/expensive)
❌ Use exact string matching on LLM responses
❌ Commit sensitive data (ANL credentials)
❌ Let tests create permanent resources
❌ Run real LLM tests in CI on every commit
❌ Ignore timeout limits (LLM calls can hang)
❌ Skip error handling tests
❌ Test UI/formatting details with real LLMs

---

## 11. References

- **CogniscientAssistant Integration Tests**: `/Users/jplfaria/repos/CogniscientAssistant/tests/integration/test_phase8_argo_real.py`
- **CogniscientAssistant Argo Provider**: `/Users/jplfaria/repos/CogniscientAssistant/src/llm/argo_provider.py`
- **Pytest Markers Docs**: https://docs.pytest.org/en/stable/how-to/mark.html
- **OpenAI Python Client**: https://github.com/openai/openai-python
