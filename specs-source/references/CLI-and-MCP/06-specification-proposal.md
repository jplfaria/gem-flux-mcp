# Specification Proposal: CLI and MCP Interfaces

**Date**: October 15, 2025
**Purpose**: Propose new/updated specifications for AI Co-Scientist interfaces

## Executive Summary

Based on comprehensive research and analysis, I propose restructuring the interface specifications to support both CLI and MCP with modern design patterns. The current spec 017 should be retained as a conceptual layer, with three new technical specifications added.

## Current State Analysis

### Spec 017: Natural Language Interface

**Strengths** ✅:
- Excellent domain understanding (scientific terminology, research workflows)
- Good user intent modeling (goal parsing, constraint extraction)
- Clear interaction patterns (initial goal, ongoing collaboration, hypothesis review)
- Quality requirements well-defined (response time, clarity, scientific accuracy)

**Critical Gaps** ❌:
- No technical interface specification (CLI? Web? API?)
- No CLI command structure or hierarchy
- No MCP server design
- No structured output formats (JSON/YAML)
- No non-interactive/automation modes
- No error handling details (exit codes, formats)
- No state management strategy
- No authentication/security model
- Assumes human-only use case (ignores AI assistants)

**Verdict**: Keep as conceptual specification, add technical implementation specs.

## Research Findings Summary

### CLI vs MCP: Not Either/Or

**Key Insight**: Modern AI tools should implement BOTH interfaces:
- **CLI**: Expert developers, automation, debugging, transparency
- **MCP**: AI assistants (Claude, Cursor), guided workflows, embedded expertise
- **Shared Core**: Maximum reach, consistency, flexibility

**Token Efficiency**: MCP can bypass security checks (35k vs 1.3-2M tokens for equivalent operations)

### Modern CLI Design Patterns

1. **Typer Framework**: Type hint-based, minimal boilerplate, excellent DX
2. **Structured Output**: JSON/YAML flags for LLM consumption
3. **Interactive Detection**: TTY detection for appropriate UX
4. **Exit Codes**: Proper error signaling for shell scripting
5. **Shell Completion**: bash/zsh completions for discoverability

**References**: GitHub CLI, kubectl, terminalcp patterns

### Modern MCP Design Patterns

1. **FastMCP Framework**: Decorator-based, automatic schema generation
2. **OAuth 2.1 with PKCE**: Secure authentication without client secrets
3. **Fine-grained Scoping**: RFC 8707 resource indicators
4. **Resource Exposure**: Hypotheses, reviews as readable resources
5. **Prompt Templates**: Guide AI assistants through workflows

**References**: MCP specification (March 2025 updates), FastMCP documentation

## Proposed Specification Structure

```
specs/
├── 017-natural-language-interface.md (UPDATED)
│   └── Conceptual layer: WHAT the interface does
│       - User intent understanding
│       - Domain expertise requirements
│       - Interaction patterns
│       - Quality expectations
│       - References 017a, 017b, 017c for implementation
│
├── 017a-cli-interface.md (NEW)
│   └── Technical CLI implementation using Typer
│       - Command structure and hierarchy
│       - Output formats (JSON, YAML, text)
│       - Interactive vs non-interactive modes
│       - Exit codes and error handling
│       - Shell completion
│       - Configuration files
│       - Authentication (local + OAuth)
│
├── 017b-mcp-server.md (NEW)
│   └── Technical MCP implementation using FastMCP
│       - Tool definitions (start_research, generate_hypotheses, etc.)
│       - Resource exposure (research://, hypothesis://)
│       - Prompt templates (research-workflow, hypothesis-analysis)
│       - OAuth 2.1 authentication
│       - Scope design and enforcement
│       - Error handling
│
└── 017c-integration-architecture.md (NEW)
    └── Shared core logic between CLI and MCP
        - Architecture diagram
        - Code organization
        - Business logic layer
        - Testing strategy
        - Deployment patterns
```

## Spec 017a: CLI Interface (Outline)

### 1. Overview
- Purpose: Expert developers, automation, debugging
- Framework: Typer (Python 3.11+)
- Design principles: LLM-friendly, scriptable, transparent

### 2. Command Structure

```bash
co-scientist
├── login                  # Authenticate (OAuth or local)
├── logout                 # Clear authentication
├── config                 # Manage configuration
│   ├── get <key>
│   ├── set <key> <value>
│   └── list
├── research               # Research project management
│   ├── start <goal>       # Start new research
│   ├── status <id>        # Get project status
│   ├── list               # List all projects
│   └── export <id>        # Export results
├── hypotheses             # Hypothesis operations
│   ├── list               # List hypotheses
│   ├── show <id>          # Show hypothesis details
│   ├── generate           # Generate new hypotheses
│   └── evolve <id>        # Evolve hypothesis
├── review                 # Review operations
│   ├── create <hyp-id>    # Review hypothesis
│   ├── show <id>          # Show review details
│   └── list               # List reviews
├── rank                   # Ranking operations
│   └── tournament <research-id>
└── results                # Results and exports
    ├── summary <research-id>
    └── export <research-id> --format <json|yaml|markdown>
```

### 3. Output Formats

**Human-Readable (Default)**:
```bash
$ co-scientist hypotheses list
ID          SUMMARY                              ELO    STATUS
hyp_abc     Target KDM4A demethylase            1432   reviewed
hyp_def     Inhibit DNMT3B methylation          1398   reviewed
hyp_ghi     Block TGF-β signaling pathway       1365   pending
```

**JSON (Machine-Readable)**:
```bash
$ co-scientist hypotheses list --json
[
  {
    "id": "hyp_abc",
    "summary": "Target KDM4A demethylase",
    "elo_score": 1432,
    "status": "reviewed"
  },
  ...
]
```

**YAML (Configuration-Friendly)**:
```bash
$ co-scientist hypotheses list --yaml
- id: hyp_abc
  summary: Target KDM4A demethylase
  elo_score: 1432
  status: reviewed
```

**Template (Custom Formatting)**:
```bash
$ co-scientist hypotheses list --format "{{.id}}: {{.summary}}"
hyp_abc: Target KDM4A demethylase
hyp_def: Inhibit DNMT3B methylation
```

### 4. Interactive vs Non-Interactive

**Interactive Mode** (TTY detected):
```bash
$ co-scientist research start
? Enter research goal: Find treatments for liver fibrosis
? Domain (optional): biology
? Hypothesis count: 30

✓ Research started
  ID: res_abc123
  Status: initializing
  Estimated time: 2.5 hours
```

**Non-Interactive Mode** (scripting):
```bash
$ co-scientist research start \
    --goal "Find treatments for liver fibrosis" \
    --domain biology \
    --count 30 \
    --json

{"research_id": "res_abc123", "status": "initializing", ...}
```

### 5. Exit Codes

```
0   - Success
1   - General error
2   - Misuse of command (invalid arguments)
64  - Input data error (validation failed)
65  - Input file missing
70  - Internal error (system failure)
130 - Interrupted by user (Ctrl+C)
```

### 6. Configuration

```yaml
# ~/.co-scientist/config.yaml
api:
  base_url: https://api.co-scientist.ai
  timeout: 120

auth:
  mode: oauth  # or 'local'
  client_id: co-scientist-cli

llm:
  provider: argo
  default_model: o3

output:
  default_format: text  # or 'json', 'yaml'
  color: auto  # auto, always, never
  pager: auto  # Use pager for long output

research:
  default_hypothesis_count: 20
  default_evolution_strategy: refine
```

### 7. Authentication

**Local Mode** (single-user, no network):
```bash
$ co-scientist login --local
Username: scientist@university.edu
Password: ********
✓ Logged in locally
```

**OAuth Mode** (multi-user, cloud):
```bash
$ co-scientist login --oauth
Opening browser for authentication...
✓ Authenticated successfully
```

### 8. Shell Completion

```bash
# Install completions
$ co-scientist --install-completion bash
Completion installed to ~/.bashrc

# Usage
$ co-scientist research <TAB>
start  status  list  export

$ co-scientist hypotheses show <TAB>
hyp_abc  hyp_def  hyp_ghi
```

### 9. Error Handling

```bash
$ co-scientist research start --goal "short"
Error: Research goal too short (minimum 10 characters)
Exit code: 64

$ co-scientist hypotheses show hyp_invalid
Error: Hypothesis not found: hyp_invalid
Suggestion: Use 'co-scientist hypotheses list' to see available IDs
Exit code: 1

$ co-scientist research start --goal "valid goal"
Error: Failed to connect to LLM provider
Cause: Network timeout after 30s
Suggestion: Check internet connection or use --offline mode
Exit code: 70
```

## Spec 017b: MCP Server (Outline)

### 1. Overview
- Purpose: AI assistants (Claude Desktop, Cursor), guided workflows
- Framework: FastMCP (Python 3.11+)
- Protocol: JSON-RPC 2.0 (MCP specification)

### 2. Tool Definitions

**Research Management**:
- `start_research(goal, domain?)` → ResearchID
- `get_research_status(research_id)` → ResearchStatus
- `list_research_projects(status?, limit?)` → ResearchProject[]

**Hypothesis Operations**:
- `generate_hypotheses(research_id, count?, method?)` → Hypothesis[]
- `evolve_hypothesis(hypothesis_id, strategy)` → Hypothesis
- `get_hypothesis_details(hypothesis_id)` → Hypothesis

**Review and Ranking**:
- `review_hypothesis(hypothesis_id, review_type)` → Review
- `rank_hypotheses(research_id, method)` → RankedHypothesis[]

**Results**:
- `get_results(research_id, format?)` → ResultsSummary

### 3. Resource Definitions

**Research Projects**:
```
URI: research://projects/{project_id}
Returns: Markdown-formatted research project details
```

**Hypotheses**:
```
URI: hypothesis://{hypothesis_id}
Returns: Markdown-formatted hypothesis with full details
```

**Reviews**:
```
URI: review://{review_id}
Returns: Markdown-formatted review with scores and recommendations
```

### 4. Prompt Templates

**research-workflow**: Complete research workflow guide
**hypothesis-analysis**: Deep hypothesis analysis guide
**research-goal-refinement**: Help refine vague research goals

### 5. Authentication

**OAuth 2.1 Flow**:
1. Authorization request with PKCE
2. User authorizes in browser
3. Authorization code exchange
4. Access token + refresh token
5. Token validation (JWT with JWKS)

**Scopes**:
- `research:read` - Read research projects
- `research:write` - Create/modify research projects
- `hypotheses:generate` - Generate hypotheses
- `hypotheses:evolve` - Evolve hypotheses
- `reviews:read` - Read reviews
- `reviews:write` - Create reviews
- `admin` - Full access

### 6. Error Handling

**Error Format**:
```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Hypothesis not found: hyp_invalid",
    "details": {
      "resource_type": "hypothesis",
      "resource_id": "hyp_invalid"
    }
  }
}
```

**Error Codes**:
- `invalid_input` - Validation failed
- `resource_not_found` - Resource doesn't exist
- `permission_denied` - Insufficient permissions
- `rate_limit_exceeded` - Rate limit hit
- `internal_error` - System error

### 7. Rate Limiting

Token bucket algorithm:
- 60 requests per minute per user
- Burst size: 10 requests
- 429 status code when exceeded
- Retry-After header in response

### 8. Deployment

**Docker Container**:
```dockerfile
FROM python:3.11-slim
COPY src/ baml_src/ config/ /app/
EXPOSE 8080
CMD ["python", "-m", "fastmcp", "run", "src/mcp_server.py"]
```

**Kubernetes**:
- 3 replicas for high availability
- Health checks and readiness probes
- Resource limits (512Mi-2Gi memory, 250m-1000m CPU)
- Load balancer service

## Spec 017c: Integration Architecture (Outline)

### 1. Overview

Both CLI and MCP share core business logic to ensure consistency and reduce duplication.

### 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Layer                           │
├─────────────────────────────┬───────────────────────────────┤
│         CLI Interface       │      MCP Server Interface     │
│         (Typer-based)       │      (FastMCP-based)          │
├─────────────────────────────┴───────────────────────────────┤
│                    Interface Adapters                       │
│  - CLI commands → Business logic                            │
│  - MCP tools → Business logic                               │
│  - Format conversions (JSON, YAML, Markdown)                │
├─────────────────────────────────────────────────────────────┤
│                   Business Logic Layer                      │
│  - ResearchManager                                          │
│  - HypothesisManager                                        │
│  - ReviewManager                                            │
│  - RankingManager                                           │
├─────────────────────────────────────────────────────────────┤
│                     Agent Layer                             │
│  - SupervisorAgent                                          │
│  - GenerationAgent                                          │
│  - ReflectionAgent                                          │
│  - RankingAgent                                             │
│  - EvolutionAgent                                           │
│  - ProximityAgent                                           │
│  - MetaReviewAgent                                          │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                      │
│  - TaskQueue (Redis/in-memory)                              │
│  - ContextMemory (file/PostgreSQL)                          │
│  - LLMProvider (BAML → Argo Gateway)                        │
│  - SafetyFramework                                          │
└─────────────────────────────────────────────────────────────┘
```

### 3. Code Organization

```
src/
├── cli/
│   ├── __init__.py
│   ├── main.py              # Typer app entry point
│   ├── commands/
│   │   ├── research.py      # Research commands
│   │   ├── hypotheses.py    # Hypothesis commands
│   │   ├── review.py        # Review commands
│   │   └── results.py       # Results commands
│   ├── formatters/
│   │   ├── text.py          # Human-readable output
│   │   ├── json.py          # JSON output
│   │   └── yaml.py          # YAML output
│   └── auth.py              # CLI authentication
│
├── mcp/
│   ├── __init__.py
│   ├── server.py            # FastMCP server
│   ├── tools.py             # Tool definitions
│   ├── resources.py         # Resource definitions
│   ├── prompts.py           # Prompt templates
│   └── auth.py              # MCP authentication
│
├── managers/                 # Business logic layer (SHARED)
│   ├── research.py          # ResearchManager
│   ├── hypotheses.py        # HypothesisManager
│   ├── review.py            # ReviewManager
│   └── ranking.py           # RankingManager
│
├── agents/                   # Agent layer (EXISTING)
│   ├── supervisor.py
│   ├── generation_agent.py
│   ├── reflection_agent.py
│   ├── ranking_agent.py
│   ├── evolution_agent.py
│   ├── proximity_agent.py
│   └── meta_review_agent.py
│
└── core/                     # Infrastructure (EXISTING)
    ├── task_queue.py
    ├── context_memory.py
    ├── models.py
    └── safety.py
```

### 4. Business Logic Layer (New)

**ResearchManager** - Encapsulates research operations:
```python
class ResearchManager:
    """Manages research projects."""

    def __init__(
        self,
        task_queue: TaskQueue,
        context_memory: ContextMemory,
        supervisor: SupervisorAgent
    ):
        self.task_queue = task_queue
        self.context_memory = context_memory
        self.supervisor = supervisor

    async def start_research(
        self,
        goal: str,
        domain: str | None = None,
        hypothesis_count: int = 20
    ) -> ResearchProject:
        """Start new research project.

        Used by BOTH CLI and MCP.
        """
        # Validate input
        goal = validate_research_goal(goal)

        # Create research ID
        research_id = generate_research_id()

        # Store in context
        await self.context_memory.set(f"research:{research_id}:goal", goal)
        await self.context_memory.set(f"research:{research_id}:domain", domain)
        await self.context_memory.set(f"research:{research_id}:status", "initializing")

        # Create initial tasks
        await self.supervisor.create_task(
            agent_type="generation",
            priority=3,
            parameters={
                "research_id": research_id,
                "goal": goal,
                "count": hypothesis_count
            }
        )

        # Return project object
        return ResearchProject(
            id=research_id,
            goal=goal,
            domain=domain,
            status="initializing",
            created_at=utcnow(),
            hypothesis_count=0
        )

    async def get_research_status(self, research_id: str) -> ResearchStatus:
        """Get research project status.

        Used by BOTH CLI and MCP.
        """
        # Fetch from context memory
        goal = await self.context_memory.get(f"research:{research_id}:goal")
        status = await self.context_memory.get(f"research:{research_id}:status")

        if not goal:
            raise ResourceNotFoundError("research", research_id)

        # Get hypotheses and reviews
        hypotheses = await self.context_memory.get("hypotheses") or []
        reviews = await self.context_memory.get("reviews") or []

        research_hyps = [h for h in hypotheses if h.get("research_id") == research_id]
        research_reviews = [r for r in reviews if r.get("research_id") == research_id]

        # Return status object
        return ResearchStatus(
            research_id=research_id,
            goal=goal,
            status=status,
            hypotheses_generated=len(research_hyps),
            hypotheses_reviewed=len(research_reviews),
            progress=len(research_reviews) / max(len(research_hyps), 1)
        )
```

**CLI Usage**:
```python
# src/cli/commands/research.py
from src.managers.research import ResearchManager

@research_app.command("start")
def start_research(
    goal: str = typer.Argument(..., help="Research goal"),
    domain: Optional[str] = typer.Option(None, "--domain"),
    count: int = typer.Option(20, "--count"),
    output_format: OutputFormat = typer.Option(OutputFormat.text, "--format")
):
    """Start a new research project."""
    manager = get_research_manager()

    # Call shared business logic
    project = asyncio.run(manager.start_research(goal, domain, count))

    # Format for CLI output
    if output_format == OutputFormat.json:
        print(json.dumps(project.to_dict()))
    elif output_format == OutputFormat.yaml:
        print(yaml.dump(project.to_dict()))
    else:
        print(f"✓ Research started")
        print(f"  ID: {project.id}")
        print(f"  Status: {project.status}")
```

**MCP Usage**:
```python
# src/mcp/tools.py
from src.managers.research import ResearchManager

@mcp.tool(scopes=["research:write"])
async def start_research(
    goal: str,
    domain: str | None = None,
    context: Context = None
) -> dict:
    """Start new research project."""
    manager = get_research_manager()

    # Call shared business logic
    project = await manager.start_research(goal, domain)

    # Return as dict for MCP
    return project.to_dict()
```

### 5. Testing Strategy

**Unit Tests** - Test business logic in isolation:
```python
@pytest.mark.asyncio
async def test_start_research():
    """Test ResearchManager.start_research()."""
    manager = ResearchManager(mock_queue, mock_memory, mock_supervisor)

    project = await manager.start_research("Test goal", "biology")

    assert project.id.startswith("res_")
    assert project.goal == "Test goal"
    assert project.domain == "biology"
```

**CLI Integration Tests** - Test CLI commands:
```python
def test_cli_research_start():
    """Test 'co-scientist research start' command."""
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["research", "start", "Test goal", "--domain", "biology", "--json"]
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "research_id" in data
```

**MCP Integration Tests** - Test MCP tools:
```python
@pytest.mark.asyncio
async def test_mcp_start_research():
    """Test start_research MCP tool."""
    client = MCPTestClient(mcp)

    result = await client.call_tool("start_research", goal="Test goal")

    assert "research_id" in result
    assert result["goal"] == "Test goal"
```

**Real LLM Tests** - Test with actual models:
```python
@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_cli_generates_valid_hypotheses():
    """Test CLI generates scientifically valid hypotheses."""
    runner = CliRunner()

    result = runner.invoke(app, [
        "research", "start",
        "Why does ice float?",
        "--count", "5",
        "--json"
    ])

    assert result.exit_code == 0
    data = json.loads(result.stdout)

    # Behavioral expectations
    assert data["hypotheses_count"] >= 3
    assert any("density" in h["summary"].lower()
              for h in data["hypotheses"])
```

### 6. Deployment Patterns

**CLI Deployment**:
- PyPI package: `pip install co-scientist-cli`
- Homebrew formula: `brew install co-scientist`
- Binary releases: GitHub Releases

**MCP Deployment**:
- Docker Hub: `docker pull co-scientist/mcp:latest`
- Kubernetes Helm chart
- Claude Desktop integration (config file)

## Implementation Roadmap

### Phase 16a: CLI Foundation (2-3 weeks)
1. Create business logic layer (managers/)
2. Implement Typer CLI structure
3. Add output formatters (JSON, YAML, text)
4. Implement authentication (local + OAuth)
5. Add shell completion
6. Write CLI integration tests

### Phase 16b: MCP Server (2-3 weeks)
1. Implement FastMCP server
2. Define tools (research, hypotheses, review, rank)
3. Expose resources (research://, hypothesis://)
4. Create prompt templates
5. Implement OAuth 2.1 authentication
6. Write MCP integration tests

### Phase 16c: Integration & Polish (1-2 weeks)
1. Refactor to use shared business logic
2. Add comprehensive error handling
3. Implement rate limiting and audit logging
4. Performance optimization
5. Write real LLM behavioral tests
6. Documentation and examples

### Phase 16d: Deployment (1 week)
1. PyPI package for CLI
2. Docker images for MCP
3. Kubernetes manifests
4. Claude Desktop integration guide
5. Installation documentation

## Success Criteria

### CLI Success Criteria
- ✅ All commands work in interactive and non-interactive modes
- ✅ JSON/YAML output parseable by jq/yq
- ✅ Proper exit codes for all error conditions
- ✅ Shell completion works in bash/zsh
- ✅ OAuth authentication functional
- ✅ Can be scripted for automation

### MCP Success Criteria
- ✅ All tools callable from Claude Desktop
- ✅ OAuth 2.1 authentication with PKCE works
- ✅ Resources accessible via URIs
- ✅ Prompt templates guide AI assistants effectively
- ✅ Rate limiting prevents abuse
- ✅ Audit logging captures all actions

### Integration Success Criteria
- ✅ CLI and MCP produce identical results for same operations
- ✅ Shared business logic has ≥80% test coverage
- ✅ Real LLM tests pass with o3, Claude, Gemini
- ✅ Performance acceptable (<2s for simple operations)
- ✅ Documentation complete and clear

## Conclusion

This proposal provides a comprehensive path forward for implementing modern CLI and MCP interfaces for AI Co-Scientist. By:

1. **Retaining spec 017** as conceptual foundation
2. **Adding spec 017a** for CLI technical implementation
3. **Adding spec 017b** for MCP technical implementation
4. **Adding spec 017c** for integration architecture
5. **Following modern design patterns** from GitHub CLI, kubectl, terminalcp, FastMCP

We will create a system that serves both expert developers (CLI) and AI assistants (MCP) while maintaining consistency, security, and usability.

The phased implementation approach (16a→16b→16c→16d) ensures steady progress with testable milestones.
