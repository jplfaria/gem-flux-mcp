# CLI vs MCP Research Summary

**Date**: October 15, 2025
**Purpose**: Inform Phase 16+ implementation decisions for AI Co-Scientist

## Executive Summary

Modern AI tool design requires **both CLI and MCP interfaces**, not a choice between them. Each serves distinct use cases:

- **CLI**: Expert developers, automation, debugging, transparency
- **MCP**: AI assistants (Claude, etc.), guided workflows, embedded expertise
- **Dual Interface**: Shared core logic, maximizes reach and flexibility

## Key Research Sources

### 1. async-let.com Analysis

**Main Argument**: CLI vs MCP is not binary - context determines the right tool.

**Key Points**:
- **CLIs excel for**: Simple, transparent tasks where you know exactly what to do
- **MCPs excel for**: Complex workflows where the tool embeds domain expertise
- **Example**: `kubectl get pods` (CLI) vs MCP that understands Kubernetes deployments and suggests fixes
- **Design principle**: Tool complexity should match task complexity

**Quote**: "The right interface depends on whether you're executing a known command or exploring a problem space with embedded assistance."

### 2. mariozechner.at Benchmarks

**Research Question**: Does MCP actually save tokens vs CLI?

**Findings**:
- **terminalcp vs tmux**: 35k tokens (MCP) vs 1.3-2M tokens (CLI with security checks)
- **Key insight**: Token efficiency depends more on design than protocol
- **Critical discovery**: MCP bypasses Claude Code's security overhead
- **Design matters**: terminalcp uses single unified tool vs one-tool-per-command

**Benchmark Data**:
```
terminalcp (MCP): 35,000 tokens
tmux (CLI via Claude Code): 1,300,000 - 2,000,000 tokens
Ratio: 37-57x more efficient
```

### 3. Armin Ronacher's "Code-Based MCPs"

**Problem Identified**: Tool proliferation causes context rot (30+ tools overwhelm context)

**Proposed Solution**: Single "ubertool" that accepts code instead of multiple tools

**Example**:
```python
# Instead of 30 tools like:
# - create_file(path, content)
# - read_file(path)
# - search_code(pattern)
# etc.

# Single tool:
execute_code("""
with open('file.txt', 'w') as f:
    f.write('content')
""")
```

**Trade-off**: More power, less structured validation

### 4. MCP Specification (2025 Updates)

**Protocol**: JSON-RPC 2.0 inspired by Language Server Protocol

**March 2025 Security Update**:
- OAuth 2.1 adoption
- PKCE mandatory for all flows
- RFC 8707 Resource Indicators for fine-grained scoping
- RFC 9728 Protected Resource Metadata for server discovery
- External authorization server support

**Architecture**:
```
┌─────────────┐         ┌─────────────┐
│   Client    │◄───────►│   Server    │
│  (Claude)   │  MCP    │ (Your Tool) │
└─────────────┘         └─────────────┘
       │                       │
       │                       │
       ▼                       ▼
 ┌──────────┐          ┌──────────┐
 │ Protocol │          │Resources │
 │ Handler  │          │  Tools   │
 └──────────┘          │ Prompts  │
                       └──────────┘
```

## Modern CLI Design Principles (2024-2025)

### 1. LLM-Friendly Output

**Structured Formats**:
```bash
# JSON output (GitHub CLI pattern)
co-scientist research "liver fibrosis" --json
{
  "hypotheses": [...],
  "metadata": {...}
}

# YAML output (kubectl pattern)
co-scientist research "liver fibrosis" --yaml

# Template output (GitHub CLI pattern)
co-scientist research "liver fibrosis" --format "{{.id}}: {{.summary}}"
```

### 2. Proper Exit Codes

```bash
0   - Success
1   - General error
2   - Misuse of command
64  - Input data error
65  - Input file missing
70  - Internal error
130 - Interrupted (Ctrl+C)
```

**Usage**:
```bash
co-scientist research "..." && co-scientist evolve
# Only runs evolve if research succeeds
```

### 3. Interactive vs Non-Interactive

**Interactive** (human TTY):
```bash
$ co-scientist research
? Enter research goal: liver fibrosis treatments
? Domain: biology
✓ Research started (ID: res_abc123)
```

**Non-Interactive** (automation/LLM):
```bash
$ co-scientist research --goal "liver fibrosis" --domain biology --json
{"research_id": "res_abc123", "status": "started"}
```

**Detection**:
```python
import sys
if sys.stdin.isatty():
    # Interactive mode
else:
    # Non-interactive mode
```

### 4. Stream vs Batch Operations

**Streaming** (for long operations):
```bash
$ co-scientist research "..." --stream
{"type": "started", "id": "res_123"}
{"type": "hypothesis", "data": {...}}
{"type": "hypothesis", "data": {...}}
{"type": "complete", "count": 47}
```

**Batch** (for quick queries):
```bash
$ co-scientist status res_123 --json
{"status": "complete", "hypotheses": 47}
```

## Python Framework Recommendations

### For CLI: Typer

**Why Typer**:
- Type hint-based (minimal boilerplate)
- Built on Click (battle-tested)
- Automatic help generation
- Excellent for Python 3.10+ with modern type hints

**Example**:
```python
import typer
from typing import Optional

app = typer.Typer()

@app.command()
def research(
    goal: str,
    domain: Optional[str] = None,
    json_output: bool = typer.Option(False, "--json"),
):
    """Start a new research project."""
    if json_output:
        print(json.dumps({"research_id": "..."}))
    else:
        typer.echo(f"Starting research: {goal}")
```

### For MCP: FastMCP

**Why FastMCP**:
- Pythonic decorator-based API
- Automatic schema generation from type hints
- Enterprise authentication built-in
- Excellent for OAuth 2.1, PKCE, scoping

**Example**:
```python
from fastmcp import FastMCP

mcp = FastMCP("AI Co-Scientist")

@mcp.tool()
def start_research(goal: str, domain: str | None = None) -> dict:
    """Start a new research project.

    Args:
        goal: Research objective
        domain: Scientific domain (optional)
    """
    return {"research_id": "res_123", "status": "started"}
```

## Design Patterns to Follow

### 1. terminalcp Pattern

**Architecture**:
- Single unified tool (not one-per-command)
- Plain text output (more token efficient than JSON for simple cases)
- Stateful sessions with cleanup
- Async/non-blocking operations

**Key Insight**: One tool with subcommands is more token-efficient than many tools

### 2. GitHub CLI Pattern

**Field-based JSON**:
```bash
gh pr list --json number,title,state
[
  {"number": 123, "title": "Fix bug", "state": "open"}
]
```

**Template formatting**:
```bash
gh pr list --template '{{range .}}{{.number}}: {{.title}}{{"\n"}}{{end}}'
123: Fix bug
124: Add feature
```

**jq integration**:
```bash
gh pr list --json number,title | jq '.[] | select(.title | contains("bug"))'
```

### 3. kubectl Pattern

**Resource-oriented**:
```bash
kubectl get pods
kubectl describe pod my-pod
kubectl logs pod/my-pod
```

**Declarative configuration**:
```bash
kubectl apply -f research-config.yaml
```

**Multiple output formats**:
```bash
kubectl get pods -o json
kubectl get pods -o yaml
kubectl get pods -o wide
```

## Testing Strategies

### Technical Tests (Fast, Comprehensive)

**Unit Tests**:
```python
def test_research_goal_parsing():
    """Test goal parsing logic."""
    goal = "Find treatments for liver fibrosis"
    result = parse_goal(goal)
    assert result.domain == "medicine"
    assert "liver" in result.keywords
```

**Integration Tests**:
```python
@pytest.mark.asyncio
async def test_cli_workflow():
    """Test complete CLI workflow."""
    result = await run_cli(["research", "liver fibrosis", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "research_id" in data
```

### Behavioral Tests (Real LLM)

**Purpose**: Verify actual AI assistant behaviors

**Example**:
```python
@pytest.mark.real_llm
async def test_mcp_hypothesis_generation():
    """Test MCP generates viable hypotheses with Claude."""
    client = MCPClient()
    result = await client.call_tool(
        "start_research",
        goal="Why does ice float?"
    )

    # Verify behavioral expectations
    assert result["hypotheses_count"] >= 3
    assert any("density" in h["summary"].lower()
              for h in result["hypotheses"])
```

**Best Practices**:
- Keep tests under 100 tokens each
- Test behaviors, not exact outputs
- Use @pytest.mark.real_llm marker
- Run separately from main test suite

## Trade-Offs Matrix

| Aspect | CLI | MCP | Both (Recommended) |
|--------|-----|-----|-------------------|
| **Token Usage** | Can trigger security overhead (1.3-2M) | Bypasses security checks (35k) | Best of both worlds |
| **Context Efficiency** | 1-line commands | Potentially verbose | Flexible based on use |
| **User Base** | Expert developers | AI assistants + beginners | Diverse audience |
| **Learning Curve** | Steeper (must learn commands) | Gentler (guided by AI) | Options for all skill levels |
| **Debugging** | Transparent (see exact commands) | Can be opaque | CLI for debug, MCP for prod |
| **Automation** | Excellent (shell scripts) | Limited | CLI for automation |
| **Safety** | Requires user rules/knowledge | Built-in guardrails | Layered approach |
| **Discoverability** | Manual (`--help`) | AI-assisted | Both methods available |
| **Version Control** | Commands in scripts | Tool calls in logs | Both trackable |
| **Integration** | Shell, CI/CD | Claude Desktop, Cursor | Maximum reach |

## Recommendations for AI Co-Scientist

### Architecture: Dual Interface

**Shared Core Logic**:
```
┌─────────────────────────────────────┐
│         Core Research Engine        │
│  (hypothesis generation, ranking,   │
│   evolution, meta-review, etc.)     │
└─────────────┬───────────────────────┘
              │
        ┌─────┴─────┐
        │           │
        ▼           ▼
    ┌─────┐   ┌─────────┐
    │ CLI │   │   MCP   │
    │     │   │ Server  │
    └─────┘   └─────────┘
        │           │
        ▼           ▼
   Experts    AI Assistants
```

### Implementation Phases

**Phase 16a: CLI Foundation** (2-3 weeks)
- Typer-based CLI with commands
- JSON/YAML output formats
- Interactive and non-interactive modes
- Proper exit codes and error handling
- Shell completion

**Phase 16b: MCP Server** (2-3 weeks)
- FastMCP server implementation
- OAuth 2.1 authentication
- Tool definitions matching CLI capabilities
- Resource exposure (hypotheses, reviews)
- Prompt templates for common workflows

**Phase 16c: Integration & Polish** (1-2 weeks)
- Shared business logic extraction
- Comprehensive testing (unit + integration + real LLM)
- Documentation and examples
- Performance optimization

**Phase 16d: Deployment** (1 week)
- PyPI package publication
- Docker containers
- Claude Desktop integration
- Installation guides

### Suggested Command Structure

**CLI Commands**:
```bash
# Research management
co-scientist research start "liver fibrosis treatments"
co-scientist research status res_123
co-scientist research list --json

# Hypothesis operations
co-scientist hypotheses list --research res_123
co-scientist hypotheses show hyp_456
co-scientist hypotheses evolve hyp_456 --strategy refine

# Review and ranking
co-scientist review hyp_456 --type full
co-scientist rank --research res_123 --tournament

# Results
co-scientist results --research res_123 --format json
co-scientist overview --research res_123
```

**MCP Tools** (matching CLI):
```python
@mcp.tool()
def start_research(goal: str) -> ResearchID:
    """Start new research project."""

@mcp.tool()
def list_hypotheses(research_id: str) -> list[Hypothesis]:
    """List all hypotheses for a research project."""

@mcp.tool()
def evolve_hypothesis(hypothesis_id: str, strategy: str) -> Hypothesis:
    """Evolve a hypothesis using specified strategy."""
```

### Security Considerations

**CLI**:
- Local-only by default (no network exposure)
- Environment variable configuration
- Optional API key authentication for remote
- Audit logging

**MCP**:
- OAuth 2.1 with PKCE (mandatory)
- Fine-grained scoping per tool
- Rate limiting per client
- Comprehensive audit trail
- Optional approval workflows for sensitive operations

## Critical Design Decisions

### 1. Output Format Default

**Recommendation**: Human-readable by default, `--json` flag for structured

**Rationale**:
- Matches kubectl, gh CLI patterns
- Better DX for humans
- Easy automation with flag
- Clear separation of concerns

**Example**:
```bash
$ co-scientist hypotheses list
ID          SUMMARY                         ELO
hyp_123     Target KDM4A demethylase        1432
hyp_124     Inhibit DNMT3B                  1398

$ co-scientist hypotheses list --json
[{"id": "hyp_123", "summary": "...", "elo": 1432}, ...]
```

### 2. State Management

**Recommendation**: Hybrid approach

**CLI**:
- Local state in `~/.co-scientist/`
- Config file for preferences
- Optional remote sync

**MCP**:
- Server-side state management
- Client session tracking
- Automatic cleanup

### 3. Error Handling Philosophy

**Recommendation**: Graceful degradation with clear messaging

**CLI**:
```bash
$ co-scientist research start "..."
Error: Failed to connect to LLM provider
Cause: Network timeout after 30s
Suggestion: Check your internet connection or use --offline mode

Exit code: 70 (internal error)
```

**MCP**:
```json
{
  "error": {
    "code": "llm_connection_failed",
    "message": "Failed to connect to LLM provider",
    "details": "Network timeout after 30s",
    "recovery": "Retry with exponential backoff or switch providers"
  }
}
```

## Conclusion

The AI Co-Scientist system should implement **both CLI and MCP interfaces** with:

1. **Shared core logic** for consistency
2. **CLI** for expert users, automation, debugging
3. **MCP** for AI assistants, guided workflows, beginners
4. **Modern patterns** from GitHub CLI, kubectl, terminalcp
5. **Proper testing** including real LLM behavioral tests
6. **Security first** with OAuth 2.1, scoping, audit trails

This dual-interface approach maximizes reach while maintaining flexibility and proper separation of concerns.
