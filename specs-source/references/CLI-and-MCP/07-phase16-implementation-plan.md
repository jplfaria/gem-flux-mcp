# Phase 16 Implementation Plan: Natural Language Interface

**Status**: Ready for Implementation
**Prerequisites**: Phases 1-15 complete
**Duration Estimate**: 6-8 weeks
**Specifications**: 017-natural-language-interface.md, 017a-cli-interface.md, 017b-mcp-server.md, 017c-integration-architecture.md

## Overview

Phase 16 implements the Natural Language Interface layer that allows scientists to interact with the AI Co-Scientist system through two channels:
1. **CLI (spec 017a)**: Typer-based command-line interface for expert developers
2. **MCP (spec 017b)**: FastMCP-based server for AI assistants (Claude Desktop, Cursor, etc.)
3. **Shared Business Logic (spec 017c)**: Manager classes that ensure both interfaces produce identical results

## Architecture

```
User Layer
    ↓
┌─────────────┬─────────────┐
│  CLI        │  MCP        │
│  (Typer)    │  (FastMCP)  │
└─────────────┴─────────────┘
         ↓          ↓
    Interface Adapters
         ↓          ↓
┌────────────────────────────┐
│  Business Logic Layer      │
│  (Managers - SHARED)       │
│  - ResearchManager         │
│  - HypothesisManager       │
│  - ReviewManager           │
│  - RankingManager          │
└────────────────────────────┘
         ↓
┌────────────────────────────┐
│  Agent Layer (EXISTING)    │
│  - SupervisorAgent         │
│  - GenerationAgent         │
│  - ReflectionAgent, etc.   │
└────────────────────────────┘
         ↓
┌────────────────────────────┐
│  Infrastructure (EXISTING) │
│  - TaskQueue               │
│  - ContextMemory           │
│  - LLMProvider             │
└────────────────────────────┘
```

## Implementation Strategy

### Phase 16a: Business Logic Layer (Weeks 1-2)
Create shared manager classes that both CLI and MCP will use.

### Phase 16b: CLI Interface (Weeks 3-4)
Implement Typer-based command-line interface.

### Phase 16c: MCP Server (Weeks 5-6)
Implement FastMCP-based server for AI assistants.

### Phase 16d: Integration & Polish (Weeks 7-8)
Integration testing, documentation, and refinement.

---

## Phase 16a: Business Logic Layer

### Directory Structure
```
src/managers/
├── __init__.py
├── research.py          # ResearchManager
├── hypotheses.py        # HypothesisManager
├── review.py            # ReviewManager
├── ranking.py           # RankingManager
└── base.py              # Base manager class (optional)
```

### Task Breakdown

#### 1. Create ResearchManager (src/managers/research.py)
**Purpose**: Orchestrate research project lifecycle.

**Dependencies**:
- SupervisorAgent (existing)
- ContextMemory (existing)
- TaskQueue (existing)
- SafetyFramework (existing)

**Methods to Implement**:
```python
class ResearchManager:
    async def start_research(
        goal: str,
        domain: Optional[str] = None,
        hypothesis_count: int = 20,
        constraints: Optional[Dict[str, Any]] = None
    ) -> ResearchProject

    async def get_research_status(
        research_id: str
    ) -> ResearchStatus

    async def list_research_projects(
        user_id: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[ResearchProject]

    async def stop_research(
        research_id: str
    ) -> bool

    async def get_research_metrics(
        research_id: str
    ) -> Dict[str, Any]
```

**Integration Points**:
- Validates research goals via SafetyFramework (spec 020)
- Creates research project ID
- Submits initial tasks via SupervisorAgent
- Stores project state in ContextMemory
- Returns structured ResearchProject objects

#### 2. Create HypothesisManager (src/managers/hypotheses.py)
**Purpose**: Manage hypothesis generation, retrieval, and filtering.

**Dependencies**:
- GenerationAgent (existing)
- EvolutionAgent (existing)
- ContextMemory (existing)
- TaskQueue (existing)

**Methods to Implement**:
```python
class HypothesisManager:
    async def generate_hypotheses(
        research_id: str,
        count: int = 5,
        method: Optional[str] = None,
        focus_area: Optional[str] = None
    ) -> List[Hypothesis]

    async def get_hypothesis(
        hypothesis_id: str
    ) -> Optional[Hypothesis]

    async def list_hypotheses(
        research_id: str,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "elo",
        limit: int = 20
    ) -> List[Hypothesis]

    async def evolve_hypothesis(
        hypothesis_id: str,
        strategy: str = "refine"
    ) -> Hypothesis

    async def submit_custom_hypothesis(
        research_id: str,
        summary: str,
        full_description: str,
        rationale: str,
        experimental_approach: str
    ) -> Hypothesis
```

**Integration Points**:
- Creates generation tasks via TaskQueue
- Retrieves hypotheses from ContextMemory
- Formats hypothesis data for presentation
- Validates custom hypotheses via SafetyFramework

#### 3. Create ReviewManager (src/managers/review.py)
**Purpose**: Manage hypothesis reviews and feedback.

**Dependencies**:
- ReflectionAgent (existing)
- ContextMemory (existing)

**Methods to Implement**:
```python
class ReviewManager:
    async def submit_review(
        hypothesis_id: str,
        rating: int,
        comments: str,
        reviewer: str = "user"
    ) -> Review

    async def get_reviews(
        hypothesis_id: str
    ) -> List[Review]

    async def get_review_statistics(
        research_id: str
    ) -> Dict[str, Any]

    async def update_review(
        review_id: str,
        rating: Optional[int] = None,
        comments: Optional[str] = None
    ) -> Review
```

**Integration Points**:
- Stores reviews in ContextMemory
- Updates hypothesis Elo scores via RankingAgent
- Tracks user feedback for preference learning

#### 4. Create RankingManager (src/managers/ranking.py)
**Purpose**: Manage hypothesis ranking and tournament results.

**Dependencies**:
- RankingAgent (existing)
- ContextMemory (existing)

**Methods to Implement**:
```python
class RankingManager:
    async def get_top_hypotheses(
        research_id: str,
        limit: int = 10,
        metric: str = "elo"
    ) -> List[Hypothesis]

    async def run_tournament(
        research_id: str,
        hypothesis_ids: List[str]
    ) -> TournamentResults

    async def get_ranking_explanation(
        hypothesis_id: str
    ) -> str

    async def compare_hypotheses(
        hypothesis_id_1: str,
        hypothesis_id_2: str
    ) -> ComparisonResult
```

**Integration Points**:
- Retrieves Elo scores from ContextMemory
- Runs tournament matches via RankingAgent
- Formats ranking explanations

#### 5. Create Base Manager (src/managers/base.py) - Optional
**Purpose**: Shared utilities and initialization logic.

**Methods**:
```python
class BaseManager:
    def __init__(
        self,
        context_memory: ContextMemory,
        task_queue: TaskQueue,
        llm_provider: LLMProvider
    ):
        self.context_memory = context_memory
        self.task_queue = task_queue
        self.llm_provider = llm_provider

    def _validate_research_id(self, research_id: str) -> bool
    def _get_current_user(self) -> Optional[str]
    def _format_timestamp(self, dt: datetime) -> str
```

### Unit Tests for Phase 16a

#### tests/unit/test_research_manager.py
```python
- test_start_research_creates_project
- test_start_research_validates_goal
- test_start_research_submits_tasks
- test_get_research_status_returns_metrics
- test_list_research_projects_filters_by_status
- test_stop_research_terminates_tasks
- test_invalid_research_id_raises_error
```

#### tests/unit/test_hypothesis_manager.py
```python
- test_generate_hypotheses_creates_tasks
- test_get_hypothesis_retrieves_from_memory
- test_list_hypotheses_applies_filters
- test_list_hypotheses_sorts_by_elo
- test_evolve_hypothesis_creates_evolution_task
- test_submit_custom_hypothesis_validates_safety
- test_submit_custom_hypothesis_stores_in_memory
```

#### tests/unit/test_review_manager.py
```python
- test_submit_review_stores_in_memory
- test_submit_review_updates_elo
- test_get_reviews_retrieves_all_for_hypothesis
- test_get_review_statistics_aggregates_ratings
- test_update_review_modifies_existing
```

#### tests/unit/test_ranking_manager.py
```python
- test_get_top_hypotheses_sorts_by_elo
- test_run_tournament_creates_matches
- test_get_ranking_explanation_provides_reasoning
- test_compare_hypotheses_shows_differences
```

---

## Phase 16b: CLI Interface

### Directory Structure
```
src/cli/
├── __init__.py
├── main.py              # Typer app entry point
├── commands/
│   ├── __init__.py
│   ├── research.py      # Research commands
│   ├── hypotheses.py    # Hypothesis commands
│   ├── review.py        # Review commands
│   └── results.py       # Results commands
├── formatters/
│   ├── __init__.py
│   ├── text.py          # Text output formatter
│   ├── json.py          # JSON output formatter
│   ├── yaml.py          # YAML output formatter
│   └── template.py      # Template-based formatter
├── auth.py              # Authentication (local + OAuth 2.1)
├── config.py            # CLI configuration
└── utils.py             # CLI utilities

pyproject.toml           # Add CLI entry point
```

### Dependencies to Add
```toml
[tool.poetry.dependencies]
typer = "^0.9.0"
rich = "^13.0.0"          # For rich terminal output
httpx = "^0.25.0"         # For OAuth 2.1 flows
pyjwt = "^2.8.0"          # For JWT token handling
pyyaml = "^6.0.1"         # For YAML output
jinja2 = "^3.1.2"         # For template formatting

[tool.poetry.scripts]
co-scientist = "src.cli.main:app"
```

### Task Breakdown

#### 1. Create CLI Entry Point (src/cli/main.py)
```python
import typer
from rich.console import Console

app = typer.Typer(
    name="co-scientist",
    help="AI Co-Scientist command-line interface",
    add_completion=True
)

console = Console()

# Subcommands
from src.cli.commands import research, hypotheses, review, results

app.add_typer(research.app, name="research")
app.add_typer(hypotheses.app, name="hypotheses")
app.add_typer(review.app, name="review")
app.add_typer(results.app, name="results")

# Global options
@app.callback()
def main(
    ctx: typer.Context,
    config: Optional[str] = typer.Option(None, "--config", help="Config file path"),
    format: str = typer.Option("text", "--format", help="Output format (text/json/yaml)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """AI Co-Scientist CLI - Collaborative research with AI."""
    ctx.obj = {
        "config": config,
        "format": format,
        "verbose": verbose
    }
```

#### 2. Create Research Commands (src/cli/commands/research.py)
```python
research_app = typer.Typer(help="Research project management")

@research_app.command("start")
async def start_research(
    goal: str = typer.Argument(..., help="Research goal"),
    domain: Optional[str] = typer.Option(None, "--domain", help="Scientific domain"),
    count: int = typer.Option(20, "--count", help="Number of hypotheses"),
    format: str = typer.Option("text", "--format", help="Output format")
):
    """Start a new research project."""
    manager = get_research_manager()
    project = await manager.start_research(goal, domain, count)
    output = format_output(project, format)
    console.print(output)

@research_app.command("status")
async def get_status(
    research_id: str = typer.Argument(..., help="Research ID"),
    format: str = typer.Option("text", "--format")
):
    """Get research project status."""
    # Implementation

@research_app.command("list")
async def list_projects(
    status: Optional[str] = typer.Option(None, "--status"),
    format: str = typer.Option("text", "--format")
):
    """List research projects."""
    # Implementation

@research_app.command("stop")
async def stop_research(
    research_id: str = typer.Argument(..., help="Research ID")
):
    """Stop a research project."""
    # Implementation
```

#### 3. Create Hypothesis Commands (src/cli/commands/hypotheses.py)
```python
hypotheses_app = typer.Typer(help="Hypothesis management")

@hypotheses_app.command("generate")
async def generate(
    research_id: str = typer.Argument(...),
    count: int = typer.Option(5, "--count"),
    method: Optional[str] = typer.Option(None, "--method"),
    format: str = typer.Option("text", "--format")
):
    """Generate new hypotheses."""
    # Implementation

@hypotheses_app.command("list")
async def list_hypotheses(
    research_id: str = typer.Argument(...),
    sort: str = typer.Option("elo", "--sort"),
    limit: int = typer.Option(20, "--limit"),
    format: str = typer.Option("text", "--format")
):
    """List hypotheses for research project."""
    # Implementation

@hypotheses_app.command("show")
async def show_hypothesis(
    hypothesis_id: str = typer.Argument(...),
    format: str = typer.Option("text", "--format")
):
    """Show hypothesis details."""
    # Implementation

@hypotheses_app.command("evolve")
async def evolve(
    hypothesis_id: str = typer.Argument(...),
    strategy: str = typer.Option("refine", "--strategy"),
    format: str = typer.Option("text", "--format")
):
    """Evolve a hypothesis."""
    # Implementation

@hypotheses_app.command("submit")
async def submit_custom(
    research_id: str = typer.Argument(...),
    summary: str = typer.Option(..., "--summary"),
    description: str = typer.Option(..., "--description"),
    rationale: str = typer.Option(..., "--rationale"),
    approach: str = typer.Option(..., "--approach")
):
    """Submit a custom hypothesis."""
    # Implementation
```

#### 4. Create Review Commands (src/cli/commands/review.py)
```python
review_app = typer.Typer(help="Hypothesis review")

@review_app.command("submit")
async def submit_review(
    hypothesis_id: str = typer.Argument(...),
    rating: int = typer.Option(..., "--rating", min=1, max=5),
    comments: str = typer.Option("", "--comments")
):
    """Submit a review for a hypothesis."""
    # Implementation

@review_app.command("list")
async def list_reviews(
    hypothesis_id: str = typer.Argument(...),
    format: str = typer.Option("text", "--format")
):
    """List reviews for a hypothesis."""
    # Implementation

@review_app.command("stats")
async def review_statistics(
    research_id: str = typer.Argument(...),
    format: str = typer.Option("text", "--format")
):
    """Get review statistics for research project."""
    # Implementation
```

#### 5. Create Results Commands (src/cli/commands/results.py)
```python
results_app = typer.Typer(help="Research results")

@results_app.command("top")
async def top_hypotheses(
    research_id: str = typer.Argument(...),
    limit: int = typer.Option(10, "--limit"),
    format: str = typer.Option("text", "--format")
):
    """Get top-ranked hypotheses."""
    # Implementation

@results_app.command("export")
async def export_results(
    research_id: str = typer.Argument(...),
    output_file: str = typer.Option(..., "--output"),
    format: str = typer.Option("json", "--format")
):
    """Export research results to file."""
    # Implementation

@results_app.command("summary")
async def research_summary(
    research_id: str = typer.Argument(...),
    template: Optional[str] = typer.Option(None, "--template"),
    format: str = typer.Option("text", "--format")
):
    """Generate research summary."""
    # Implementation
```

#### 6. Create Output Formatters

**Text Formatter (src/cli/formatters/text.py)**:
```python
from rich.table import Table
from rich.panel import Panel

def format_research_project(project: ResearchProject) -> Table:
    """Format research project as rich table."""
    # Implementation

def format_hypothesis(hypothesis: Hypothesis) -> Panel:
    """Format hypothesis as rich panel."""
    # Implementation

def format_hypothesis_list(hypotheses: List[Hypothesis]) -> Table:
    """Format hypothesis list as rich table."""
    # Implementation
```

**JSON Formatter (src/cli/formatters/json.py)**:
```python
import json
from typing import Any

def format_as_json(data: Any, pretty: bool = True) -> str:
    """Format data as JSON string."""
    # Implementation
```

**YAML Formatter (src/cli/formatters/yaml.py)**:
```python
import yaml
from typing import Any

def format_as_yaml(data: Any) -> str:
    """Format data as YAML string."""
    # Implementation
```

**Template Formatter (src/cli/formatters/template.py)**:
```python
from jinja2 import Environment, FileSystemLoader

def format_with_template(data: Any, template_path: str) -> str:
    """Format data using Jinja2 template."""
    # Implementation
```

#### 7. Create Authentication (src/cli/auth.py)
```python
from typing import Optional
import httpx
import jwt
from pathlib import Path

class CLIAuthenticator:
    """Handle CLI authentication (local + OAuth 2.1)."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".co-scientist"

    def local_login(self, user_id: str) -> bool:
        """Local authentication for single-user mode."""
        # Implementation

    async def oauth_login(self) -> str:
        """OAuth 2.1 with PKCE flow."""
        # Implementation

    def get_current_token(self) -> Optional[str]:
        """Get current access token."""
        # Implementation

    def refresh_token(self) -> str:
        """Refresh expired access token."""
        # Implementation
```

#### 8. Create Configuration (src/cli/config.py)
```python
from pathlib import Path
from pydantic import BaseModel
import yaml

class CLIConfig(BaseModel):
    """CLI configuration."""
    auth_mode: str = "local"
    output_format: str = "text"
    api_endpoint: Optional[str] = None
    oauth_client_id: Optional[str] = None

    @classmethod
    def load(cls, path: Path) -> "CLIConfig":
        """Load config from YAML file."""
        # Implementation

    def save(self, path: Path):
        """Save config to YAML file."""
        # Implementation
```

### Unit Tests for Phase 16b

#### tests/unit/test_cli_commands.py
```python
- test_research_start_command
- test_research_status_command
- test_research_list_command
- test_hypotheses_generate_command
- test_hypotheses_list_command
- test_hypotheses_show_command
- test_review_submit_command
- test_results_top_command
- test_results_export_command
```

#### tests/unit/test_cli_formatters.py
```python
- test_text_formatter_research_project
- test_text_formatter_hypothesis_list
- test_json_formatter_output
- test_yaml_formatter_output
- test_template_formatter_with_jinja2
```

#### tests/unit/test_cli_auth.py
```python
- test_local_login_stores_user_id
- test_oauth_login_pkce_flow
- test_get_current_token_retrieves_valid_token
- test_refresh_token_updates_expired_token
- test_invalid_token_raises_error
```

#### tests/unit/test_cli_config.py
```python
- test_config_loads_from_yaml
- test_config_saves_to_yaml
- test_config_defaults_applied
- test_config_validation_errors
```

---

## Phase 16c: MCP Server

### Directory Structure
```
src/mcp/
├── __init__.py
├── server.py            # FastMCP server
├── tools.py             # MCP tool definitions
├── resources.py         # MCP resource definitions
├── prompts.py           # MCP prompt templates
├── auth.py              # OAuth 2.1 with PKCE
├── rate_limiter.py      # Token bucket rate limiting
└── errors.py            # MCP error handling

scripts/
├── start-mcp-server.sh  # MCP server startup script
```

### Dependencies to Add
```toml
[tool.poetry.dependencies]
fastmcp = "^0.2.0"
pydantic = "^2.5.0"
httpx = "^0.25.0"
pyjwt = "^2.8.0"
cryptography = "^41.0.0"  # For PKCE
```

### Task Breakdown

#### 1. Create MCP Server (src/mcp/server.py)
```python
from fastmcp import FastMCP
from src.mcp.tools import register_tools
from src.mcp.resources import register_resources
from src.mcp.prompts import register_prompts

mcp = FastMCP("AI Co-Scientist")

# OAuth 2.1 configuration
mcp.configure_oauth(
    authorization_url="https://auth.coscientist.ai/authorize",
    token_url="https://auth.coscientist.ai/token",
    scopes=[
        "research:read",
        "research:write",
        "hypotheses:generate",
        "hypotheses:read",
        "reviews:write",
        "reviews:read",
        "results:read"
    ],
    pkce_required=True
)

# Register tools, resources, prompts
register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

if __name__ == "__main__":
    mcp.run()
```

#### 2. Create MCP Tools (src/mcp/tools.py)
```python
from fastmcp import FastMCP, Context
from typing import Optional

def register_tools(mcp: FastMCP):

    @mcp.tool(scopes=["research:write"])
    async def start_research(
        goal: str,
        domain: str | None = None,
        hypothesis_count: int = 20,
        context: Context = None
    ) -> dict:
        """Start a new research project.

        Args:
            goal: Research objective in natural language
            domain: Optional scientific domain
            hypothesis_count: Number of hypotheses to generate
            context: MCP context with authentication

        Returns:
            Research project details with ID for tracking
        """
        await context.log_action("start_research", {"goal": goal})
        manager = get_research_manager()
        project = await manager.start_research(goal, domain, hypothesis_count)
        return project.dict()

    @mcp.tool(scopes=["hypotheses:generate"])
    async def generate_hypotheses(
        research_id: str,
        count: int = 5,
        method: str | None = None,
        focus_area: str | None = None,
        context: Context = None
    ) -> dict:
        """Generate new hypotheses for research project."""
        await context.log_action("generate_hypotheses", {"research_id": research_id})
        manager = get_hypothesis_manager()
        hypotheses = await manager.generate_hypotheses(
            research_id, count, method, focus_area
        )
        return {"hypotheses": [h.dict() for h in hypotheses]}

    @mcp.tool(scopes=["hypotheses:read"])
    async def list_hypotheses(
        research_id: str,
        sort_by: str = "elo",
        limit: int = 20,
        context: Context = None
    ) -> dict:
        """List hypotheses for research project."""
        # Implementation

    @mcp.tool(scopes=["hypotheses:generate"])
    async def evolve_hypothesis(
        hypothesis_id: str,
        strategy: str = "refine",
        context: Context = None
    ) -> dict:
        """Evolve an existing hypothesis."""
        # Implementation

    @mcp.tool(scopes=["reviews:write"])
    async def review_hypothesis(
        hypothesis_id: str,
        rating: int,
        comments: str = "",
        context: Context = None
    ) -> dict:
        """Submit a review for a hypothesis."""
        # Implementation

    @mcp.tool(scopes=["results:read"])
    async def get_results(
        research_id: str,
        limit: int = 10,
        context: Context = None
    ) -> dict:
        """Get top-ranked hypotheses for research project."""
        # Implementation
```

#### 3. Create MCP Resources (src/mcp/resources.py)
```python
from fastmcp import FastMCP

def register_resources(mcp: FastMCP):

    @mcp.resource("research://projects/{research_id}")
    async def get_research_project(
        uri: str,
        research_id: str
    ) -> str:
        """Get research project details in markdown format."""
        manager = get_research_manager()
        project = await manager.get_research_status(research_id)

        # Format as markdown
        markdown = f"""# Research Project: {project.goal}

**ID**: {research_id}
**Status**: {project.status}
**Domain**: {project.domain}
**Created**: {project.created_at}

## Progress
- Hypotheses Generated: {project.hypothesis_count}
- Reviews Completed: {project.review_count}
- Top Hypothesis Elo: {project.top_elo}

## Metrics
- Average Elo: {project.avg_elo}
- Novelty Score: {project.novelty_score}
- Review Coverage: {project.review_coverage}%
"""
        return markdown

    @mcp.resource("hypothesis://{hypothesis_id}")
    async def get_hypothesis(
        uri: str,
        hypothesis_id: str
    ) -> str:
        """Get hypothesis details in markdown format."""
        manager = get_hypothesis_manager()
        hypothesis = await manager.get_hypothesis(hypothesis_id)

        # Format as markdown
        markdown = f"""# Hypothesis: {hypothesis.summary}

**ID**: {hypothesis_id}
**Elo Score**: {hypothesis.elo}
**Confidence**: {hypothesis.confidence}

## Full Description
{hypothesis.full_description}

## Rationale
{hypothesis.rationale}

## Experimental Approach
{hypothesis.experimental_approach}

## Reviews
{len(hypothesis.reviews)} reviews submitted
"""
        return markdown
```

#### 4. Create MCP Prompts (src/mcp/prompts.py)
```python
from fastmcp import FastMCP

def register_prompts(mcp: FastMCP):

    @mcp.prompt()
    async def research_workflow(
        research_goal: str
    ) -> str:
        """Guided workflow for starting research."""
        return f"""I'll help you start a research project with the AI Co-Scientist system.

Research Goal: {research_goal}

Let me break this down into steps:

1. **Validate Goal**: First, I'll check if this research goal is appropriate
2. **Start Research**: Create a new research project with ID for tracking
3. **Generate Hypotheses**: Create initial set of hypotheses
4. **Review Top Candidates**: Show you the most promising hypotheses
5. **Iterative Refinement**: Evolve and improve based on feedback

Would you like me to proceed with starting the research project?
"""

    @mcp.prompt()
    async def hypothesis_analysis(
        hypothesis_id: str
    ) -> str:
        """Guided analysis of a hypothesis."""
        manager = get_hypothesis_manager()
        hypothesis = await manager.get_hypothesis(hypothesis_id)

        return f"""I'll help you analyze this hypothesis:

**Summary**: {hypothesis.summary}
**Elo Score**: {hypothesis.elo} (ranking: {hypothesis.rank}/{hypothesis.total_count})

I can help you:
1. **Understand the Rationale**: Explain the scientific reasoning
2. **Review Experimental Approach**: Assess the validation method
3. **Compare with Others**: Show how it differs from similar hypotheses
4. **Evolve the Hypothesis**: Refine or improve this idea
5. **Submit a Review**: Provide your expert feedback

What would you like to explore?
"""
```

#### 5. Create OAuth 2.1 Authentication (src/mcp/auth.py)
```python
import secrets
import hashlib
import base64
from typing import Optional
from datetime import datetime, timedelta
import jwt

class MCPAuthenticator:
    """OAuth 2.1 with PKCE for MCP server."""

    def __init__(self, config):
        self.config = config
        self.active_flows = {}  # Store PKCE verifiers

    def create_authorization_url(
        self,
        client_id: str,
        redirect_uri: str,
        scopes: List[str]
    ) -> tuple[str, str]:
        """Create OAuth authorization URL with PKCE.

        Returns:
            (authorization_url, code_verifier)
        """
        # Generate PKCE challenge
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)

        # Build authorization URL
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "response_type": "code",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

        url = f"{self.config.authorization_url}?{urlencode(params)}"
        return url, code_verifier

    async def exchange_code_for_token(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str
    ) -> dict:
        """Exchange authorization code for access token."""
        # Implementation

    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier."""
        return secrets.token_urlsafe(32)

    def _generate_code_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge."""
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")
```

#### 6. Create Rate Limiter (src/mcp/rate_limiter.py)
```python
from datetime import datetime, timedelta
from typing import Dict
import asyncio

class TokenBucketRateLimiter:
    """Token bucket rate limiter for MCP tools."""

    def __init__(
        self,
        rate: int = 60,  # Requests per minute
        burst: int = 10  # Burst capacity
    ):
        self.rate = rate
        self.burst = burst
        self.buckets: Dict[str, tuple[float, datetime]] = {}

    async def check_rate_limit(self, client_id: str) -> bool:
        """Check if request is within rate limit.

        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.utcnow()

        if client_id not in self.buckets:
            self.buckets[client_id] = (self.burst - 1, now)
            return True

        tokens, last_update = self.buckets[client_id]

        # Refill tokens based on time elapsed
        elapsed = (now - last_update).total_seconds()
        tokens_to_add = elapsed * (self.rate / 60)
        tokens = min(self.burst, tokens + tokens_to_add)

        if tokens >= 1:
            self.buckets[client_id] = (tokens - 1, now)
            return True
        else:
            return False
```

#### 7. Create Error Handling (src/mcp/errors.py)
```python
from fastmcp import MCPError

class ResearchNotFoundError(MCPError):
    """Research project not found."""
    code = "RESEARCH_NOT_FOUND"
    status = 404

class HypothesisNotFoundError(MCPError):
    """Hypothesis not found."""
    code = "HYPOTHESIS_NOT_FOUND"
    status = 404

class RateLimitError(MCPError):
    """Rate limit exceeded."""
    code = "RATE_LIMIT_EXCEEDED"
    status = 429

class InsufficientScopesError(MCPError):
    """Insufficient OAuth scopes."""
    code = "INSUFFICIENT_SCOPES"
    status = 403

class InvalidInputError(MCPError):
    """Invalid input provided."""
    code = "INVALID_INPUT"
    status = 400
```

### Unit Tests for Phase 16c

#### tests/unit/test_mcp_tools.py
```python
- test_start_research_tool
- test_generate_hypotheses_tool
- test_list_hypotheses_tool
- test_evolve_hypothesis_tool
- test_review_hypothesis_tool
- test_get_results_tool
- test_tools_require_authentication
- test_tools_check_scopes
```

#### tests/unit/test_mcp_resources.py
```python
- test_research_project_resource
- test_hypothesis_resource
- test_resources_format_markdown
- test_resource_not_found_error
```

#### tests/unit/test_mcp_prompts.py
```python
- test_research_workflow_prompt
- test_hypothesis_analysis_prompt
- test_prompts_include_context
```

#### tests/unit/test_mcp_auth.py
```python
- test_create_authorization_url_with_pkce
- test_exchange_code_for_token
- test_pkce_code_verifier_generation
- test_pkce_code_challenge_generation
- test_invalid_code_verifier_rejected
```

#### tests/unit/test_mcp_rate_limiter.py
```python
- test_rate_limiter_allows_within_limit
- test_rate_limiter_blocks_over_limit
- test_rate_limiter_refills_tokens
- test_rate_limiter_per_client
```

---

## Phase 16d: Integration & Testing

### Integration Tests

#### tests/integration/test_phase16_cli.py
```python
@pytest.mark.asyncio
async def test_cli_full_research_workflow():
    """Test complete CLI workflow from start to results."""
    # 1. Start research via CLI
    # 2. Generate hypotheses via CLI
    # 3. Submit reviews via CLI
    # 4. Get top results via CLI
    # 5. Verify all operations worked correctly

@pytest.mark.asyncio
async def test_cli_output_formats():
    """Test CLI output in text, JSON, YAML formats."""
    # Test same command with different --format flags

@pytest.mark.asyncio
async def test_cli_authentication_flow():
    """Test CLI authentication (local and OAuth)."""
    # Test local login
    # Test OAuth login flow
    # Test token refresh
```

#### tests/integration/test_phase16_mcp.py
```python
@pytest.mark.asyncio
async def test_mcp_full_research_workflow():
    """Test complete MCP workflow from start to results."""
    # 1. Call start_research tool
    # 2. Call generate_hypotheses tool
    # 3. Call review_hypothesis tool
    # 4. Call get_results tool
    # 5. Verify all operations worked correctly

@pytest.mark.asyncio
async def test_mcp_resources_accessible():
    """Test MCP resources are accessible."""
    # Test research://projects/{id}
    # Test hypothesis://{id}

@pytest.mark.asyncio
async def test_mcp_authentication_flow():
    """Test MCP OAuth 2.1 with PKCE."""
    # Test authorization URL generation
    # Test code exchange
    # Test scope checking
```

#### tests/integration/test_phase16_integration.py
```python
@pytest.mark.asyncio
async def test_cli_mcp_produce_identical_results():
    """Test that CLI and MCP produce identical results.

    This is the CRITICAL test - both interfaces must call the same
    manager methods and produce identical business logic results.
    """
    # 1. Start research via CLI
    cli_project = await cli_start_research("Test goal")

    # 2. Start research via MCP
    mcp_project = await mcp_start_research("Test goal")

    # 3. Verify both projects have same structure
    assert cli_project.goal == mcp_project.goal
    assert cli_project.domain == mcp_project.domain

    # 4. Generate hypotheses via both interfaces
    cli_hypotheses = await cli_generate_hypotheses(cli_project.id, count=5)
    mcp_hypotheses = await mcp_generate_hypotheses(mcp_project.id, count=5)

    # 5. Verify hypotheses use same generation logic
    assert len(cli_hypotheses) == len(mcp_hypotheses)
    # Note: Can't compare exact hypotheses due to randomness,
    # but can verify they follow same validation rules

@pytest.mark.asyncio
async def test_shared_manager_layer():
    """Test that both CLI and MCP use shared managers."""
    # Verify CLI research command uses ResearchManager
    # Verify MCP start_research tool uses same ResearchManager
    # Both should share state via ContextMemory

@pytest.mark.asyncio
async def test_concurrent_cli_mcp_access():
    """Test CLI and MCP can access same research concurrently."""
    # Start research via CLI
    # Generate hypotheses via MCP
    # Submit review via CLI
    # Get results via MCP
    # Verify all operations see consistent state
```

### Test Expectations for test_expectations.json

```json
{
  "phase_16": {
    "name": "Natural Language Interface (CLI and MCP)",
    "must_pass": [
      "test_research_manager_start_research",
      "test_hypothesis_manager_generate_hypotheses",
      "test_review_manager_submit_review",
      "test_ranking_manager_get_top_hypotheses",
      "test_cli_research_start_command",
      "test_cli_hypotheses_list_command",
      "test_cli_output_formats",
      "test_mcp_start_research_tool",
      "test_mcp_generate_hypotheses_tool",
      "test_mcp_authentication_flow",
      "test_cli_mcp_produce_identical_results",
      "test_shared_manager_layer",
      "test_concurrent_cli_mcp_access"
    ],
    "may_fail": [
      "test_cli_shell_completion",
      "test_mcp_rate_limiter_complex_scenarios",
      "test_template_formatter_custom_templates"
    ],
    "real_llm_tests": [],
    "must_use_baml": [],
    "description": "CLI and MCP interfaces must work correctly and produce identical results through shared manager layer. Authentication, output formatting, and concurrent access must function properly."
  }
}
```

### Documentation Requirements

1. **CLI User Guide** (docs/cli-user-guide.md)
   - Installation instructions
   - Command reference
   - Output format examples
   - Authentication setup
   - Configuration file format

2. **MCP Integration Guide** (docs/mcp-integration-guide.md)
   - MCP server setup
   - Claude Desktop configuration
   - Cursor integration
   - OAuth 2.1 setup
   - Tool descriptions

3. **API Reference** (docs/api-reference.md)
   - Manager class documentation
   - CLI command reference
   - MCP tool reference
   - Resource URI patterns
   - Prompt templates

---

## Implementation Checklist

### Phase 16a: Business Logic Layer
- [ ] Create src/managers/ directory
- [ ] Implement ResearchManager with start_research, get_status, list_projects
- [ ] Implement HypothesisManager with generate, list, evolve, submit_custom
- [ ] Implement ReviewManager with submit_review, get_reviews, get_statistics
- [ ] Implement RankingManager with get_top, run_tournament, compare
- [ ] Write unit tests for all managers (≥80% coverage)
- [ ] Verify managers integrate with existing agents
- [ ] Verify managers use ContextMemory for persistence

### Phase 16b: CLI Interface
- [ ] Add typer, rich, httpx, pyjwt dependencies
- [ ] Create src/cli/ directory structure
- [ ] Implement CLI entry point (main.py)
- [ ] Implement research commands (start, status, list, stop)
- [ ] Implement hypothesis commands (generate, list, show, evolve, submit)
- [ ] Implement review commands (submit, list, stats)
- [ ] Implement results commands (top, export, summary)
- [ ] Implement text formatter with rich tables/panels
- [ ] Implement JSON formatter
- [ ] Implement YAML formatter
- [ ] Implement template formatter with Jinja2
- [ ] Implement local authentication
- [ ] Implement OAuth 2.1 with PKCE
- [ ] Implement CLI configuration (load/save YAML)
- [ ] Add CLI entry point to pyproject.toml
- [ ] Write unit tests for CLI commands (≥80% coverage)
- [ ] Write unit tests for formatters
- [ ] Write unit tests for authentication
- [ ] Test CLI with all output formats

### Phase 16c: MCP Server
- [ ] Add fastmcp dependency
- [ ] Create src/mcp/ directory structure
- [ ] Implement MCP server (server.py)
- [ ] Configure OAuth 2.1 with PKCE
- [ ] Implement start_research tool
- [ ] Implement generate_hypotheses tool
- [ ] Implement list_hypotheses tool
- [ ] Implement evolve_hypothesis tool
- [ ] Implement review_hypothesis tool
- [ ] Implement get_results tool
- [ ] Implement research project resource (research://projects/{id})
- [ ] Implement hypothesis resource (hypothesis://{id})
- [ ] Implement research_workflow prompt
- [ ] Implement hypothesis_analysis prompt
- [ ] Implement OAuth authentication with PKCE
- [ ] Implement token bucket rate limiter
- [ ] Implement error handling (custom MCPError classes)
- [ ] Write unit tests for MCP tools (≥80% coverage)
- [ ] Write unit tests for resources
- [ ] Write unit tests for prompts
- [ ] Write unit tests for authentication
- [ ] Write unit tests for rate limiter

### Phase 16d: Integration & Testing
- [ ] Write CLI integration tests (test_phase16_cli.py)
- [ ] Write MCP integration tests (test_phase16_mcp.py)
- [ ] Write CLI-MCP consistency tests (test_phase16_integration.py)
- [ ] Test CLI full research workflow
- [ ] Test MCP full research workflow
- [ ] Test CLI and MCP produce identical results (CRITICAL)
- [ ] Test concurrent CLI and MCP access
- [ ] Update test_expectations.json with Phase 16 entries
- [ ] Write CLI user guide documentation
- [ ] Write MCP integration guide documentation
- [ ] Write API reference documentation
- [ ] Create example scripts for common workflows
- [ ] Test CLI shell completion (bash, zsh, fish)
- [ ] Test MCP with Claude Desktop
- [ ] Test MCP with Cursor

---

## Success Criteria

### Phase 16a Success Criteria
- [ ] All manager classes implemented with full method coverage
- [ ] Managers integrate correctly with existing agents
- [ ] Managers use ContextMemory for state persistence
- [ ] All manager unit tests pass with ≥80% coverage
- [ ] No code duplication between managers and agents

### Phase 16b Success Criteria
- [ ] CLI commands work correctly for all operations
- [ ] All output formats (text, JSON, YAML, template) produce correct output
- [ ] Authentication works for both local and OAuth modes
- [ ] CLI configuration loads/saves correctly
- [ ] Shell completion works for bash/zsh/fish
- [ ] All CLI unit tests pass with ≥80% coverage
- [ ] CLI exit codes follow spec (0, 1, 64, 70, 130)

### Phase 16c Success Criteria
- [ ] All MCP tools work correctly and enforce scopes
- [ ] Resources return markdown-formatted content
- [ ] Prompts provide helpful guided workflows
- [ ] OAuth 2.1 with PKCE authentication works end-to-end
- [ ] Rate limiting prevents abuse
- [ ] All MCP unit tests pass with ≥80% coverage
- [ ] MCP server works with Claude Desktop and Cursor

### Phase 16d Success Criteria
- [ ] CLI and MCP produce **identical business logic results**
- [ ] Both interfaces can access same research concurrently
- [ ] Integration tests verify full workflows work end-to-end
- [ ] All Phase 16 tests in test_expectations.json pass
- [ ] Documentation complete and accurate
- [ ] No regressions in Phases 1-15

---

## Dependencies and Prerequisites

### Python Package Dependencies
- typer ^0.9.0
- rich ^13.0.0
- httpx ^0.25.0
- pyjwt ^2.8.0
- pyyaml ^6.0.1
- jinja2 ^3.1.2
- fastmcp ^0.2.0
- cryptography ^41.0.0

### Existing Components Used
- SupervisorAgent (Phase 9)
- GenerationAgent (Phase 10)
- ReflectionAgent (Phase 11)
- RankingAgent (Phase 12)
- EvolutionAgent (Phase 13)
- ProximityAgent (Phase 14)
- MetaReviewAgent (Phase 15)
- TaskQueue (Phase 3)
- ContextMemory (Phase 4)
- SafetyFramework (Phase 5)
- LLMProvider (Phase 6)

### External Services
- OAuth 2.1 authorization server (for multi-user deployments)
- Claude Desktop (for MCP testing)
- Cursor IDE (for MCP testing)

---

## Risk Mitigation

### Risk: CLI and MCP Divergence
**Mitigation**: Shared manager layer ensures both interfaces use identical business logic. Integration tests specifically verify this.

### Risk: Authentication Complexity
**Mitigation**: Start with local authentication (simple), add OAuth 2.1 incrementally. Use well-tested libraries (pyjwt, httpx).

### Risk: Output Format Bugs
**Mitigation**: Comprehensive formatter unit tests. Test with real data from existing phases.

### Risk: MCP Integration Issues
**Mitigation**: Follow FastMCP best practices. Test with actual Claude Desktop and Cursor.

### Risk: Rate Limiting False Positives
**Mitigation**: Token bucket algorithm is well-understood. Configurable rates for testing vs production.

---

## Implementation Notes

### BAML Usage
Phase 16 does NOT require new BAML functions. The CLI and MCP interfaces are presentation layers that use existing agents (which already use BAML).

The `must_use_baml` array in test_expectations.json is empty for Phase 16.

### Testing Strategy
- **Unit tests**: Test each manager, CLI command, MCP tool, formatter in isolation
- **Integration tests**: Test full workflows end-to-end
- **Consistency tests**: Verify CLI and MCP produce identical results
- **Real integration tests**: Test with actual Claude Desktop and Cursor (manual)

### Context Optimization
Phase 16 implementation will benefit from context optimization:
- Relevant specs: 017, 017a, 017b, 017c, 001, 002, 004
- Will automatically select 3-7 most relevant specs per task
- Loop will use optimized context for faster iterations

### Development Loop Integration
The implementation loop will:
1. Detect Phase 16 by finding first unchecked task in IMPLEMENTATION_PLAN.md
2. Extract current task with section context
3. Select relevant specs using context optimization
4. Run quality gates (tests, coverage ≥80%, integration tests)
5. Validate test results against test_expectations.json
6. Mark task complete and commit
7. Continue to next task

---

## Timeline Estimate

### Week 1: Phase 16a (Business Logic - Part 1)
- Day 1-2: ResearchManager + tests
- Day 3-4: HypothesisManager + tests
- Day 5: Integration with existing agents

### Week 2: Phase 16a (Business Logic - Part 2)
- Day 1-2: ReviewManager + tests
- Day 3-4: RankingManager + tests
- Day 5: Phase 16a integration testing

### Week 3: Phase 16b (CLI - Part 1)
- Day 1: CLI structure and entry point
- Day 2-3: Research and hypothesis commands
- Day 4-5: Review and results commands

### Week 4: Phase 16b (CLI - Part 2)
- Day 1-2: Output formatters (text, JSON, YAML, template)
- Day 3-4: Authentication (local + OAuth)
- Day 5: CLI testing and polish

### Week 5: Phase 16c (MCP - Part 1)
- Day 1: MCP server structure
- Day 2-3: MCP tools implementation
- Day 4-5: MCP resources and prompts

### Week 6: Phase 16c (MCP - Part 2)
- Day 1-2: OAuth 2.1 with PKCE
- Day 3-4: Rate limiting and error handling
- Day 5: MCP testing

### Week 7: Phase 16d (Integration - Part 1)
- Day 1-2: CLI integration tests
- Day 3-4: MCP integration tests
- Day 5: CLI-MCP consistency tests

### Week 8: Phase 16d (Integration - Part 2)
- Day 1-2: Documentation (CLI guide, MCP guide, API reference)
- Day 3-4: Real integration testing (Claude Desktop, Cursor)
- Day 5: Final polish and Phase 16 completion

**Total Duration**: 8 weeks (6-8 weeks estimated range)

---

## Next Steps

1. **Review this plan with user** - Get approval on approach and timeline
2. **Update IMPLEMENTATION_PLAN.md** - Replace skeletal Phase 16 with detailed tasks from this plan
3. **Update test_expectations.json** - Add Phase 16 test expectations
4. **Begin Phase 16a** - Start with ResearchManager implementation
5. **Iterate through tasks** - One atomic task per loop iteration
6. **Maintain test coverage** - Keep ≥80% coverage throughout
7. **Integration test early** - Test manager layer works before building interfaces
8. **CLI before MCP** - CLI is simpler, validate approach before MCP
9. **Test consistency** - Verify CLI and MCP produce identical results (critical)
10. **Document as we go** - Keep documentation up to date with implementation
