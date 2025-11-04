# Argo LLM + MCP Integration Reference Documentation

**Date**: 2025-10-29
**Status**: Reference materials for implementation
**Purpose**: Guide development of Gem-Flux MCP + Argo LLM integration

---

## Overview

This directory contains comprehensive reference documentation for integrating Gem-Flux MCP Server with Argo Gateway LLMs. These materials support implementation of real LLM testing, tutorial examples, and team showcase demonstrations.

---

## Contents

### 01-argo-gateway-overview.md
**What**: Introduction to Argo Gateway and integration patterns
**Covers**:
- Available models (GPT-5, Claude 4.x, Gemini 2.5, o3)
- argo-proxy architecture (localhost:8000)
- Tool calling workflow with OpenAI API format
- Why Jupyter notebooks are NOT suitable
- Recommended patterns from CogniscientAssistant

**Use this when**:
- Understanding Argo Gateway capabilities
- Designing integration architecture
- Choosing the right LLM model
- Learning about tool calling flow

---

### 02-mcp-tool-conversion.md
**What**: Technical guide for converting MCP tools to OpenAI function format
**Covers**:
- MCP tool definition format (FastMCP)
- OpenAI function calling format
- Conversion algorithm and edge cases
- Handling defaults, enums, nested objects
- Testing conversion logic

**Use this when**:
- Implementing MCPToOpenAIConverter
- Debugging tool calling issues
- Understanding format differences
- Writing tool conversion tests

---

### 03-testing-patterns.md
**What**: Best practices for testing MCP tools with real LLMs
**Covers**:
- Testing philosophy (why real LLM tests matter)
- Test organization and pytest markers
- Real LLM test patterns (basic, multi-turn, streaming)
- Circuit breaker pattern for model failures
- CI/CD integration
- Semantic vs structural assertions

**Use this when**:
- Writing integration tests
- Setting up test infrastructure
- Implementing error handling
- Configuring CI/CD pipelines
- Debugging LLM interaction issues

---

### 04-implementation-architecture.md
**What**: Detailed architecture and implementation plan for ArgoMCPClient
**Covers**:
- System architecture diagram
- Core components (ArgoMCPClient, ConversationManager)
- Tool calling loop implementation
- Streaming response handling
- MCP server connection patterns
- Configuration and usage examples
- Implementation phases (MVP to production)

**Use this when**:
- Implementing ArgoMCPClient
- Understanding component interactions
- Designing conversation management
- Adding streaming support
- Planning implementation phases

---

## Source Materials

These specifications are based on analysis of:

1. **Argo LLM Documentation** (`/Users/jplfaria/repos/gem-flux-mcp/specs-source/argo_llm_documentation/`)
   - API reference and authentication
   - Model capabilities and pricing
   - Tool calling support

2. **CogniscientAssistant Project** (`/Users/jplfaria/repos/CogniscientAssistant/`)
   - `src/llm/argo_provider.py` - Argo integration patterns
   - `tests/integration/test_phase8_argo_real.py` - Real LLM testing
   - `src/mcp/tools.py` - MCP tool implementations
   - `baml_src/clients.baml` - Type-safe LLM configuration

---

## Key Findings Summary

### ✅ What Works Well

1. **argo-proxy** provides seamless OpenAI-compatible interface
2. **Tool calling** supported by all three providers (OpenAI, Anthropic, Google)
3. **Circuit breaker pattern** handles model failures gracefully
4. **Real LLM integration tests** catch issues unit tests miss
5. **Python scripts** (not notebooks) are best for demos and testing

### ❌ What Doesn't Work

1. **Jupyter notebooks** are NOT suitable for MCP + LLM demos
   - No streaming support
   - Hard to test automatically
   - Static output doesn't show multi-turn conversations
   - Not production-like

2. **OpenAI function format doesn't support**:
   - Default values in JSON Schema
   - Some advanced JSON Schema features

3. **Mocked tests alone are insufficient**:
   - Can't verify LLM understands tool descriptions
   - Can't catch prompt engineering issues
   - Can't validate real tool calling format

---

## Implementation Roadmap

Based on these reference materials, the recommended implementation order is:

### Phase 1: Core Tool Calling (MVP)
1. Create `MCPToOpenAIConverter` class
2. Implement `ArgoMCPClient` basic chat()
3. Implement tool calling loop
4. Add MCP server connection
5. Write unit tests for conversion

**Files to create**:
- `src/gem_flux_mcp/argo_client.py`
- `src/gem_flux_mcp/mcp_converter.py`
- `tests/unit/test_mcp_converter.py`

### Phase 2: Real LLM Testing
1. Add pytest markers (`@pytest.mark.real_llm`)
2. Create integration test fixtures
3. Write basic real LLM tests
4. Test each MCP tool with real LLM

**Files to create**:
- `tests/integration/test_argo_llm_real.py`
- `tests/integration/conftest.py` (fixtures)

### Phase 3: Streaming Support
1. Implement `chat_stream()` method
2. Handle streaming tool calls
3. Add streaming tests
4. Create streaming examples

**Files to create**:
- Update `src/gem_flux_mcp/argo_client.py`
- `tests/integration/test_streaming.py`
- `examples/argo_llm/02_streaming.py`

### Phase 4: Error Handling
1. Implement circuit breaker pattern
2. Add retry logic
3. Handle timeout scenarios
4. Test error recovery

**Files to create**:
- `src/gem_flux_mcp/circuit_breaker.py`
- `tests/integration/test_error_handling.py`

### Phase 5: Examples and Documentation
1. Create tutorial Python scripts
2. Write usage documentation
3. Prepare team showcase materials
4. Document common patterns

**Files to create**:
- `examples/argo_llm/01_simple_chat.py`
- `examples/argo_llm/03_complete_workflow.py`
- `docs/argo-llm-integration.md`
- `docs/team-showcase-guide.md`

---

## Usage Patterns

### For Developers Implementing Integration

1. **Start with**: `01-argo-gateway-overview.md` for big picture
2. **Then read**: `04-implementation-architecture.md` for detailed design
3. **Refer to**: `02-mcp-tool-conversion.md` when implementing converter
4. **Use**: `03-testing-patterns.md` when writing tests

### For Developers Writing Tests

1. **Start with**: `03-testing-patterns.md` for testing philosophy
2. **Refer to**: `01-argo-gateway-overview.md` for argo-proxy setup
3. **Use**: `04-implementation-architecture.md` for client usage examples

### For Team Showcase Preparation

1. **Start with**: `01-argo-gateway-overview.md` - Section 7 "Next Steps"
2. **Refer to**: `04-implementation-architecture.md` - Section 6 "Usage Examples"
3. **Use**: `03-testing-patterns.md` - Section 7 "Test Data Management"

---

## Key Concepts

### Multi-Turn Tool Calling

```
User: "Build a model for E. coli 83333.1"
  ↓
LLM: [Calls build_model tool]
  ↓
Client: [Executes tool via MCP server]
  ↓
Client: [Sends result back to LLM]
  ↓
LLM: "I've built a metabolic model with ID 'ecoli_83333.gf'..."
```

### OpenAI Tool Format

MCP tools must be converted to this format:

```python
{
    "type": "function",
    "function": {
        "name": "build_model",
        "description": "Build a metabolic model...",
        "parameters": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
}
```

### Circuit Breaker Pattern

Track failures and automatically switch models:

```
gpt-5 fails 3 times → Switch to claude-4-opus
claude-4-opus fails 3 times → Switch to gemini-2.5-pro
All fail → Reset counters and retry
```

### Real LLM Tests

Mark expensive tests with `@pytest.mark.real_llm`:

```python
@pytest.mark.real_llm
def test_build_model_with_argo(argo_available):
    # Real LLM call...
```

Run selectively:
- `pytest -m "not real_llm"` - Skip expensive tests (CI)
- `pytest -m real_llm` - Run only real LLM tests (local)

---

## Common Pitfalls

### ❌ Don't Do This

1. **Don't use exact string matching on LLM responses**
   ```python
   # BAD
   assert response == "I've built the model"
   ```
   Use semantic assertions:
   ```python
   # GOOD
   assert "model" in response.lower() and "built" in response.lower()
   ```

2. **Don't test every edge case with real LLMs**
   - Too slow and expensive
   - Use unit tests with mocks for edge cases
   - Use real LLM tests only for critical paths

3. **Don't commit ANL credentials**
   - Use environment variables
   - Use GitHub secrets for CI
   - Document setup in README

4. **Don't ignore timeouts**
   - LLM calls can hang
   - Always set reasonable timeouts
   - Handle timeout gracefully

### ✅ Do This Instead

1. **Use semantic assertions** for LLM responses
2. **Test critical paths** with real LLMs, edge cases with mocks
3. **Store credentials securely** in environment
4. **Set timeouts** on all LLM calls

---

## Next Actions

After reviewing these materials, the implementation should proceed in this order:

1. **Create reference docs directory structure** ✅ DONE
2. **Implement MCPToOpenAIConverter** (Phase 1)
3. **Implement ArgoMCPClient basic chat()** (Phase 1)
4. **Write unit tests** (Phase 1)
5. **Set up real LLM testing infrastructure** (Phase 2)
6. **Write integration tests** (Phase 2)
7. **Add streaming support** (Phase 3)
8. **Create tutorial examples** (Phase 5)
9. **Document for team showcase** (Phase 5)

---

## Questions to Resolve

Before implementation, clarify:

1. **Which LLM model to use as default?**
   - gpt-5 (fast, general purpose)
   - claude-4-opus (best reasoning)
   - gemini-2.5-pro (fast, multimodal)

2. **How should streaming display tool calls?**
   - Show "[Calling build_model...]" messages?
   - Show tool arguments?
   - Show tool results?

3. **Should we support async API?**
   - Or just sync wrapper over async?
   - Impacts API design

4. **Configuration approach?**
   - Environment variables only?
   - Config file support?
   - Both?

---

## References

- **Argo Gateway**: Argonne National Laboratory LLM-as-a-Service
- **MCP Protocol**: Model Context Protocol for tool calling
- **OpenAI Function Calling**: https://platform.openai.com/docs/guides/function-calling
- **CogniscientAssistant**: Example project with Argo + MCP integration
- **FastMCP**: Framework used for Gem-Flux MCP Server

---

**Status**: Reference materials complete. Ready for Phase 1 implementation.
