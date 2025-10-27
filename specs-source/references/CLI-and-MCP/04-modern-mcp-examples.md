# Modern MCP Server Implementation Examples

**Date**: October 15, 2025
**Purpose**: Reference implementations for AI Co-Scientist MCP server

## Executive Summary

This document provides complete MCP server implementation patterns using FastMCP, OAuth 2.1, and modern security practices. These examples demonstrate how to expose AI Co-Scientist capabilities to AI assistants like Claude Desktop and Cursor.

## FastMCP Server Architecture

### Basic Server Structure

```python
"""AI Co-Scientist MCP Server - FastMCP implementation."""
from fastmcp import FastMCP, Context
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

# Initialize MCP server
mcp = FastMCP(
    "AI Co-Scientist",
    version="1.0.0",
    description="AI-powered scientific hypothesis generation and evaluation system"
)

# Configure OAuth 2.1 authentication
mcp.configure_auth(
    auth_url="https://auth.co-scientist.ai/authorize",
    token_url="https://auth.co-scientist.ai/token",
    scopes={
        "research:read": "Read research projects and hypotheses",
        "research:write": "Create and modify research projects",
        "hypotheses:generate": "Generate new hypotheses",
        "hypotheses:evolve": "Evolve existing hypotheses",
        "reviews:read": "Read hypothesis reviews",
        "reviews:write": "Create hypothesis reviews",
        "admin": "Full system access"
    },
    pkce_required=True  # Enforce PKCE for all flows
)
```

### Type Definitions

```python
@dataclass
class ResearchProject:
    """Research project data model."""
    id: str
    goal: str
    domain: Optional[str]
    status: str
    created_at: datetime
    hypothesis_count: int

    def to_dict(self):
        return {
            "id": self.id,
            "goal": self.goal,
            "domain": self.domain,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "hypothesis_count": self.hypothesis_count
        }

@dataclass
class Hypothesis:
    """Hypothesis data model."""
    id: str
    research_id: str
    summary: str
    rationale: str
    predictions: List[str]
    elo_score: float
    status: str

    def to_dict(self):
        return {
            "id": self.id,
            "research_id": self.research_id,
            "summary": self.summary,
            "rationale": self.rationale,
            "predictions": self.predictions,
            "elo_score": self.elo_score,
            "status": self.status
        }
```

## Tool Definitions

### Research Management Tools

```python
@mcp.tool(scopes=["research:write"])
async def start_research(
    goal: str,
    domain: str | None = None,
    context: Context = None
) -> dict:
    """Start a new research project.

    This tool initiates a research project by:
    1. Parsing the research goal
    2. Identifying the scientific domain
    3. Initializing the hypothesis generation pipeline

    Args:
        goal: Research objective in natural language (e.g., "Find treatments for liver fibrosis")
        domain: Optional scientific domain (biology, chemistry, physics, etc.)
        context: MCP context with authentication and session info

    Returns:
        dict: Research project details including ID for tracking

    Example:
        {
            "research_id": "res_abc123",
            "goal": "Find treatments for liver fibrosis",
            "domain": "biology",
            "status": "initializing",
            "estimated_time_hours": 2.5
        }
    """
    # Verify authentication
    if not context.is_authenticated:
        raise PermissionError("Authentication required")

    # Check scopes
    if not context.has_scope("research:write"):
        raise PermissionError("research:write scope required")

    # Log audit trail
    await context.log_action("start_research", {"goal": goal, "domain": domain})

    # Import core logic
    from src.agents.supervisor import SupervisorAgent
    from src.core.context_memory import ContextMemory
    from src.core.task_queue import TaskQueue

    # Initialize components
    task_queue = TaskQueue()
    context_memory = ContextMemory()
    supervisor = SupervisorAgent(
        task_queue=task_queue,
        context_memory=context_memory,
        llm_provider=get_llm_provider()
    )

    # Store research goal
    research_id = generate_research_id()
    await context_memory.set(f"research:{research_id}:goal", goal)
    await context_memory.set(f"research:{research_id}:domain", domain)
    await context_memory.set(f"research:{research_id}:status", "initializing")

    # Create initial tasks
    await supervisor.create_task(
        agent_type="generation",
        priority=3,
        parameters={"research_id": research_id, "goal": goal}
    )

    return {
        "research_id": research_id,
        "goal": goal,
        "domain": domain or "general",
        "status": "initializing",
        "estimated_time_hours": 2.5
    }


@mcp.tool(scopes=["research:read"])
async def get_research_status(
    research_id: str,
    context: Context = None
) -> dict:
    """Get current status of a research project.

    Args:
        research_id: Research project identifier
        context: MCP context

    Returns:
        dict: Current project status with metrics

    Example:
        {
            "research_id": "res_abc123",
            "status": "active",
            "progress": 0.67,
            "hypotheses_generated": 47,
            "hypotheses_reviewed": 35,
            "top_hypothesis": {...}
        }
    """
    if not context.has_scope("research:read"):
        raise PermissionError("research:read scope required")

    from src.core.context_memory import ContextMemory
    context_memory = ContextMemory()

    # Fetch research data
    goal = await context_memory.get(f"research:{research_id}:goal")
    status = await context_memory.get(f"research:{research_id}:status")
    hypotheses = await context_memory.get("hypotheses") or []
    reviews = await context_memory.get("reviews") or []

    # Filter by research ID
    research_hypotheses = [h for h in hypotheses if h.get("research_id") == research_id]
    research_reviews = [r for r in reviews if r.get("research_id") == research_id]

    # Get top hypothesis
    sorted_hyps = sorted(
        research_hypotheses,
        key=lambda h: h.get("elo_score", 1000),
        reverse=True
    )
    top_hypothesis = sorted_hyps[0] if sorted_hyps else None

    return {
        "research_id": research_id,
        "goal": goal,
        "status": status,
        "progress": len(research_reviews) / max(len(research_hypotheses), 1),
        "hypotheses_generated": len(research_hypotheses),
        "hypotheses_reviewed": len(research_reviews),
        "top_hypothesis": top_hypothesis
    }


@mcp.tool(scopes=["research:read"])
async def list_research_projects(
    status: str | None = None,
    limit: int = 20,
    context: Context = None
) -> list[dict]:
    """List all research projects for the authenticated user.

    Args:
        status: Optional filter by status (active, completed, paused)
        limit: Maximum number of projects to return (default 20)
        context: MCP context

    Returns:
        list[dict]: List of research project summaries
    """
    if not context.has_scope("research:read"):
        raise PermissionError("research:read scope required")

    # Implementation would fetch from context memory
    # Filtered by user_id from context.user
    pass
```

### Hypothesis Generation Tools

```python
@mcp.tool(scopes=["hypotheses:generate"])
async def generate_hypotheses(
    research_id: str,
    count: int = 10,
    method: str = "literature_based",
    context: Context = None
) -> list[dict]:
    """Generate new hypotheses for a research project.

    Args:
        research_id: Research project identifier
        count: Number of hypotheses to generate (default 10, max 50)
        method: Generation method (literature_based, debate, assumptions, expansion)
        context: MCP context

    Returns:
        list[dict]: Generated hypotheses with IDs

    Methods:
        - literature_based: Extract from scientific literature
        - debate: Generate through simulated expert debate
        - assumptions: Challenge existing assumptions
        - expansion: Expand on existing high-scoring hypotheses
    """
    if not context.has_scope("hypotheses:generate"):
        raise PermissionError("hypotheses:generate scope required")

    # Validate parameters
    if count > 50:
        raise ValueError("Maximum 50 hypotheses per generation")

    if method not in ["literature_based", "debate", "assumptions", "expansion"]:
        raise ValueError(f"Unknown method: {method}")

    from src.agents.generation_agent import GenerationAgent
    from src.core.context_memory import ContextMemory

    context_memory = ContextMemory()
    generation_agent = GenerationAgent(
        context_memory=context_memory,
        llm_provider=get_llm_provider()
    )

    # Get research goal
    goal = await context_memory.get(f"research:{research_id}:goal")

    # Generate hypotheses
    hypotheses = await generation_agent.generate_hypotheses(
        goal=goal,
        count=count,
        method=method
    )

    # Store in context
    all_hypotheses = await context_memory.get("hypotheses") or []
    for hyp in hypotheses:
        hyp["research_id"] = research_id
        all_hypotheses.append(hyp)
    await context_memory.set("hypotheses", all_hypotheses)

    return [h.to_dict() for h in hypotheses]


@mcp.tool(scopes=["hypotheses:evolve"])
async def evolve_hypothesis(
    hypothesis_id: str,
    strategy: str = "refine",
    context: Context = None
) -> dict:
    """Evolve an existing hypothesis using specified strategy.

    Args:
        hypothesis_id: Hypothesis identifier to evolve
        strategy: Evolution strategy (refine, combine, simplify, paradigm_shift)
        context: MCP context

    Returns:
        dict: Evolved hypothesis with new ID

    Strategies:
        - refine: Improve specificity and testability
        - combine: Merge with complementary hypothesis
        - simplify: Reduce complexity while preserving insight
        - paradigm_shift: Challenge fundamental assumptions
    """
    if not context.has_scope("hypotheses:evolve"):
        raise PermissionError("hypotheses:evolve scope required")

    from src.agents.evolution_agent import EvolutionAgent
    from src.core.context_memory import ContextMemory

    context_memory = ContextMemory()
    evolution_agent = EvolutionAgent(
        context_memory=context_memory,
        llm_provider=get_llm_provider()
    )

    # Get hypothesis
    hypotheses = await context_memory.get("hypotheses") or []
    hypothesis = next((h for h in hypotheses if h["id"] == hypothesis_id), None)

    if not hypothesis:
        raise ValueError(f"Hypothesis not found: {hypothesis_id}")

    # Evolve
    evolved = await evolution_agent.evolve_hypothesis(
        hypothesis=hypothesis,
        strategy=strategy
    )

    # Store
    hypotheses.append(evolved.to_dict())
    await context_memory.set("hypotheses", hypotheses)

    return evolved.to_dict()
```

### Review and Ranking Tools

```python
@mcp.tool(scopes=["reviews:write"])
async def review_hypothesis(
    hypothesis_id: str,
    review_type: str = "initial",
    context: Context = None
) -> dict:
    """Review and evaluate a hypothesis.

    Args:
        hypothesis_id: Hypothesis to review
        review_type: Type of review (initial, deep_verification, simulation)
        context: MCP context

    Returns:
        dict: Review results with scores and recommendations
    """
    if not context.has_scope("reviews:write"):
        raise PermissionError("reviews:write scope required")

    from src.agents.reflection_agent import ReflectionAgent

    reflection_agent = ReflectionAgent(
        context_memory=get_context_memory(),
        llm_provider=get_llm_provider()
    )

    review = await reflection_agent.review_hypothesis(
        hypothesis_id=hypothesis_id,
        review_type=review_type
    )

    return review.to_dict()


@mcp.tool(scopes=["hypotheses:generate", "reviews:read"])
async def rank_hypotheses(
    research_id: str,
    method: str = "tournament",
    context: Context = None
) -> list[dict]:
    """Rank hypotheses for a research project.

    Args:
        research_id: Research project identifier
        method: Ranking method (tournament, direct_comparison)
        context: MCP context

    Returns:
        list[dict]: Ranked hypotheses with scores
    """
    if not all([
        context.has_scope("hypotheses:generate"),
        context.has_scope("reviews:read")
    ]):
        raise PermissionError("Multiple scopes required")

    from src.agents.ranking_agent import RankingAgent

    ranking_agent = RankingAgent(
        context_memory=get_context_memory(),
        llm_provider=get_llm_provider()
    )

    ranked = await ranking_agent.rank_hypotheses(
        research_id=research_id,
        method=method
    )

    return [h.to_dict() for h in ranked]
```

## Resource Definitions

Resources expose data that AI assistants can read directly.

```python
@mcp.resource("research://projects/{project_id}")
async def get_research_resource(project_id: str, context: Context) -> str:
    """Expose research project as readable resource.

    Args:
        project_id: Research project ID
        context: MCP context

    Returns:
        str: Markdown-formatted research project details
    """
    if not context.has_scope("research:read"):
        raise PermissionError("research:read scope required")

    from src.core.context_memory import ContextMemory
    context_memory = ContextMemory()

    goal = await context_memory.get(f"research:{project_id}:goal")
    status = await context_memory.get(f"research:{project_id}:status")
    hypotheses = await context_memory.get("hypotheses") or []

    research_hyps = [h for h in hypotheses if h.get("research_id") == project_id]

    # Format as markdown
    md = f"""# Research Project: {project_id}

## Goal
{goal}

## Status
{status}

## Statistics
- Hypotheses Generated: {len(research_hyps)}
- Average ELO Score: {sum(h.get('elo_score', 1000) for h in research_hyps) / len(research_hyps) if research_hyps else 0:.1f}

## Top Hypotheses
"""

    sorted_hyps = sorted(research_hyps, key=lambda h: h.get('elo_score', 1000), reverse=True)
    for i, hyp in enumerate(sorted_hyps[:5], 1):
        md += f"\n{i}. **{hyp['summary']}** (ELO: {hyp['elo_score']:.0f})\n"
        md += f"   {hyp['rationale'][:200]}...\n"

    return md


@mcp.resource("hypothesis://{hypothesis_id}")
async def get_hypothesis_resource(hypothesis_id: str, context: Context) -> str:
    """Expose hypothesis as readable resource.

    Returns markdown-formatted hypothesis with full details.
    """
    if not context.has_scope("hypotheses:generate"):
        raise PermissionError("hypotheses:generate scope required")

    from src.core.context_memory import ContextMemory
    context_memory = ContextMemory()

    hypotheses = await context_memory.get("hypotheses") or []
    hyp = next((h for h in hypotheses if h["id"] == hypothesis_id), None)

    if not hyp:
        raise ValueError(f"Hypothesis not found: {hypothesis_id}")

    md = f"""# Hypothesis: {hyp['summary']}

**ID**: {hyp['id']}
**ELO Score**: {hyp.get('elo_score', 1000):.0f}
**Status**: {hyp.get('status', 'unknown')}

## Rationale
{hyp['rationale']}

## Predictions
"""
    for i, pred in enumerate(hyp.get('predictions', []), 1):
        md += f"{i}. {pred}\n"

    return md
```

## Prompt Templates

Prompts guide AI assistants in using the MCP server effectively.

```python
@mcp.prompt("research-workflow")
async def research_workflow_prompt(context: Context) -> str:
    """Template for complete research workflow.

    Guides AI assistant through:
    1. Starting research
    2. Generating hypotheses
    3. Reviewing and ranking
    4. Evolving top candidates
    5. Exporting results
    """
    return """# AI Co-Scientist Research Workflow

Follow these steps to conduct scientific research:

## 1. Start Research Project
Use `start_research` tool with:
- Clear research goal (e.g., "Find novel treatments for Alzheimer's disease")
- Optional domain specification (biology, chemistry, physics, etc.)

## 2. Generate Initial Hypotheses
Use `generate_hypotheses` tool with:
- research_id from step 1
- count: 20-30 for initial batch
- method: "literature_based" for first round

## 3. Review Hypotheses
For each hypothesis, use `review_hypothesis` tool:
- Start with "initial" review type
- Use "deep_verification" for promising candidates

## 4. Rank Hypotheses
Use `rank_hypotheses` tool:
- method: "tournament" for comprehensive comparison
- This updates ELO scores

## 5. Evolve Top Hypotheses
For top 5 hypotheses, use `evolve_hypothesis`:
- strategy: "refine" to improve specificity
- strategy: "combine" to merge complementary ideas

## 6. Iterate
Repeat steps 2-5 until convergence or time limit

## 7. Export Results
Use `get_research_status` to retrieve final results

## Tips
- Generate in batches (20-30 hypotheses)
- Review before ranking
- Evolve top candidates only
- Monitor ELO scores for convergence
"""


@mcp.prompt("hypothesis-analysis")
async def hypothesis_analysis_prompt(hypothesis_id: str, context: Context) -> str:
    """Template for deep hypothesis analysis.

    Args:
        hypothesis_id: Hypothesis to analyze
    """
    # Fetch hypothesis
    hyp_resource = await get_hypothesis_resource(hypothesis_id, context)

    return f"""# Deep Hypothesis Analysis

{hyp_resource}

## Analysis Tasks

1. **Testability Assessment**
   - Are predictions specific enough?
   - What experiments would validate/falsify?
   - What resources are required?

2. **Literature Review**
   - What existing research supports this?
   - What contradicts it?
   - What are the gaps?

3. **Mechanism Analysis**
   - Is the proposed mechanism plausible?
   - What are the key assumptions?
   - What could go wrong?

4. **Impact Assessment**
   - If true, what are the implications?
   - What fields would be affected?
   - What are the ethical considerations?

Use the `review_hypothesis` tool with review_type="deep_verification" to get LLM analysis.
"""
```

## OAuth 2.1 Authentication Flow

### Authorization Code Flow with PKCE

```python
from fastmcp.auth import OAuth21Flow
import secrets
import hashlib
import base64

class CoScientistAuthFlow(OAuth21Flow):
    """OAuth 2.1 authentication for AI Co-Scientist MCP server."""

    def __init__(self):
        super().__init__(
            auth_url="https://auth.co-scientist.ai/authorize",
            token_url="https://auth.co-scientist.ai/token",
            scopes=[
                "research:read",
                "research:write",
                "hypotheses:generate",
                "hypotheses:evolve",
                "reviews:read",
                "reviews:write",
                "admin"
            ]
        )

    async def start_authorization(self, client_id: str, redirect_uri: str) -> dict:
        """Start OAuth 2.1 authorization flow with PKCE.

        Returns authorization URL and state/verifier for validation.
        """
        # Generate PKCE parameters
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
        code_verifier = code_verifier.rstrip('=')  # Remove padding

        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.rstrip('=')

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Build authorization URL
        auth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

        auth_url = f"{self.auth_url}?{urlencode(auth_params)}"

        return {
            "authorization_url": auth_url,
            "state": state,
            "code_verifier": code_verifier
        }

    async def exchange_code(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        client_id: str
    ) -> dict:
        """Exchange authorization code for access token.

        Uses PKCE for enhanced security (no client secret needed).
        """
        token_params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "code_verifier": code_verifier  # PKCE verification
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=token_params)
            response.raise_for_status()

            token_data = response.json()

            return {
                "access_token": token_data["access_token"],
                "token_type": token_data["token_type"],
                "expires_in": token_data["expires_in"],
                "refresh_token": token_data.get("refresh_token"),
                "scope": token_data["scope"]
            }
```

### Token Validation and Refresh

```python
from fastmcp.auth import TokenValidator
import jwt
from datetime import datetime, timedelta

class CoScientistTokenValidator(TokenValidator):
    """Validate and refresh OAuth tokens."""

    def __init__(self, jwks_url: str):
        self.jwks_url = jwks_url
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    async def validate_token(self, access_token: str) -> dict:
        """Validate JWT access token.

        Returns decoded token with user info and scopes.
        """
        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(access_token)

            # Decode and validate token
            decoded = jwt.decode(
                access_token,
                signing_key.key,
                algorithms=["RS256"],
                audience="https://api.co-scientist.ai",
                issuer="https://auth.co-scientist.ai"
            )

            # Check expiration
            exp = decoded.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise jwt.ExpiredSignatureError("Token expired")

            return {
                "user_id": decoded.get("sub"),
                "scopes": decoded.get("scope", "").split(),
                "email": decoded.get("email"),
                "expires_at": exp
            }

        except jwt.InvalidTokenError as e:
            raise PermissionError(f"Invalid token: {e}")

    async def refresh_token(self, refresh_token: str, client_id: str) -> dict:
        """Refresh access token using refresh token.

        Returns new access token with updated expiration.
        """
        token_params = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://auth.co-scientist.ai/token",
                data=token_params
            )
            response.raise_for_status()

            return response.json()
```

## Server Configuration

### Development Configuration

```python
# config/dev.yaml
server:
  host: localhost
  port: 8080
  debug: true

auth:
  enabled: false  # Disable for local dev
  mock_user:
    user_id: "dev_user_123"
    scopes: ["admin"]

llm:
  provider: "argo"
  base_url: "http://localhost:8000/v1"
  api_key: "dummy-key"
  default_model: "o3"

storage:
  type: "file"
  path: "./.aicoscientist/"

logging:
  level: "DEBUG"
  format: "json"
```

### Production Configuration

```python
# config/prod.yaml
server:
  host: 0.0.0.0
  port: 443
  ssl_cert: "/etc/ssl/certs/co-scientist.crt"
  ssl_key: "/etc/ssl/private/co-scientist.key"
  debug: false

auth:
  enabled: true
  oauth:
    auth_url: "https://auth.co-scientist.ai/authorize"
    token_url: "https://auth.co-scientist.ai/token"
    jwks_url: "https://auth.co-scientist.ai/.well-known/jwks.json"
    audience: "https://api.co-scientist.ai"
    issuer: "https://auth.co-scientist.ai"
  pkce_required: true

llm:
  provider: "argo"
  base_url: "${ARGO_BASE_URL}"
  api_key: "${ARGO_API_KEY}"
  default_model: "o3"
  timeout: 120

storage:
  type: "postgresql"
  connection_string: "${DATABASE_URL}"
  pool_size: 20

rate_limiting:
  enabled: true
  requests_per_minute: 60
  burst_size: 10

logging:
  level: "INFO"
  format: "json"
  output: "/var/log/co-scientist/mcp.log"

monitoring:
  metrics_port: 9090
  health_check_path: "/health"
```

## Error Handling

```python
from fastmcp import MCPError
from typing import Dict, Any

class CoScientistError(MCPError):
    """Base error for AI Co-Scientist MCP server."""

    def __init__(self, code: str, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def to_json(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": str(self),
                "details": self.details
            }
        }


class ResourceNotFoundError(CoScientistError):
    """Requested resource does not exist."""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            code="resource_not_found",
            message=f"{resource_type} not found: {resource_id}",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class InsufficientPermissionsError(CoScientistError):
    """User lacks required permissions."""
    def __init__(self, required_scopes: list[str], user_scopes: list[str]):
        super().__init__(
            code="insufficient_permissions",
            message=f"Missing scopes: {set(required_scopes) - set(user_scopes)}",
            details={"required": required_scopes, "user_has": user_scopes}
        )


class RateLimitExceededError(CoScientistError):
    """Rate limit exceeded."""
    def __init__(self, retry_after: int):
        super().__init__(
            code="rate_limit_exceeded",
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            details={"retry_after": retry_after}
        )


# Error handler decorator
@mcp.error_handler
async def handle_errors(error: Exception, context: Context) -> dict:
    """Global error handler for MCP server."""

    # Log error
    logger.error(f"MCP error: {error}", exc_info=True)

    # Handle specific error types
    if isinstance(error, CoScientistError):
        return error.to_json()

    elif isinstance(error, PermissionError):
        return CoScientistError(
            code="permission_denied",
            message=str(error)
        ).to_json()

    elif isinstance(error, ValueError):
        return CoScientistError(
            code="invalid_input",
            message=str(error)
        ).to_json()

    elif isinstance(error, TimeoutError):
        return CoScientistError(
            code="timeout",
            message="Operation timed out"
        ).to_json()

    else:
        # Generic error
        return CoScientistError(
            code="internal_error",
            message="An unexpected error occurred"
        ).to_json()
```

## Testing MCP Server

```python
import pytest
from fastmcp.testing import MCPTestClient

@pytest.fixture
async def mcp_client():
    """Test client with mock authentication."""
    client = MCPTestClient(mcp)

    # Mock authentication
    client.set_auth_context({
        "user_id": "test_user",
        "scopes": ["research:read", "research:write", "hypotheses:generate"],
        "email": "test@example.com"
    })

    return client


@pytest.mark.asyncio
async def test_start_research(mcp_client):
    """Test starting a research project via MCP."""
    result = await mcp_client.call_tool(
        "start_research",
        goal="Find treatments for liver fibrosis",
        domain="biology"
    )

    assert "research_id" in result
    assert result["goal"] == "Find treatments for liver fibrosis"
    assert result["domain"] == "biology"
    assert result["status"] == "initializing"


@pytest.mark.asyncio
async def test_insufficient_permissions(mcp_client):
    """Test permission enforcement."""
    # Remove required scope
    mcp_client.set_auth_context({
        "user_id": "test_user",
        "scopes": ["research:read"],  # Missing research:write
        "email": "test@example.com"
    })

    with pytest.raises(PermissionError, match="research:write scope required"):
        await mcp_client.call_tool(
            "start_research",
            goal="Test goal"
        )


@pytest.mark.asyncio
async def test_resource_access(mcp_client):
    """Test resource URI access."""
    # Start research first
    result = await mcp_client.call_tool("start_research", goal="Test goal")
    research_id = result["research_id"]

    # Access resource
    resource_content = await mcp_client.get_resource(f"research://projects/{research_id}")

    assert "Test goal" in resource_content
    assert "Statistics" in resource_content
```

## Deployment

### Docker Container

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY baml_src/ ./baml_src/
COPY config/ ./config/

# Expose MCP port
EXPOSE 8080

# Run server
CMD ["python", "-m", "fastmcp", "run", "src/mcp_server.py", "--config", "config/prod.yaml"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: co-scientist-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: co-scientist-mcp
  template:
    metadata:
      labels:
        app: co-scientist-mcp
    spec:
      containers:
      - name: mcp-server
        image: co-scientist/mcp:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: connection-string
        - name: ARGO_BASE_URL
          value: "https://argo.example.com/v1"
        - name: ARGO_API_KEY
          valueFrom:
            secretKeyRef:
              name: argo-credentials
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: co-scientist-mcp
spec:
  selector:
    app: co-scientist-mcp
  ports:
  - protocol: TCP
    port: 443
    targetPort: 8080
  type: LoadBalancer
```

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "co-scientist": {
      "url": "https://mcp.co-scientist.ai",
      "auth": {
        "type": "oauth2",
        "clientId": "claude-desktop-abc123",
        "scopes": [
          "research:read",
          "research:write",
          "hypotheses:generate",
          "hypotheses:evolve",
          "reviews:read",
          "reviews:write"
        ]
      },
      "description": "AI-powered scientific hypothesis generation and evaluation",
      "icon": "https://co-scientist.ai/icon.png"
    }
  }
}
```

## Conclusion

This MCP server implementation provides:

1. **Complete tool coverage** for research workflows
2. **OAuth 2.1 authentication** with PKCE for security
3. **Fine-grained scoping** for permission control
4. **Resource exposure** for direct data access
5. **Prompt templates** for guided workflows
6. **Comprehensive error handling** with structured responses
7. **Production-ready deployment** with Docker/Kubernetes

The server exposes AI Co-Scientist capabilities to AI assistants while maintaining security, performance, and usability.
