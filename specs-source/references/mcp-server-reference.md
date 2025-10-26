# MCP Server Specification

**Type**: Interface
**Interactions**: AI Assistants (Claude, Cursor, etc.), Supervisor Agent, Context Memory, All Agents

## Prerequisites
- Read: 001-system-overview.md - High-level system behavior
- Read: 002-core-principles.md - Expert-in-the-loop design
- Read: 017-natural-language-interface.md - Conceptual interface layer
- Read: 019-output-formats.md - Output formatting requirements
- Understand: Model Context Protocol (MCP) specification
- Understand: OAuth 2.1 and PKCE authentication flows

## Purpose

This specification defines the Model Context Protocol (MCP) server for the AI Co-Scientist system, enabling AI assistants like Claude Desktop and Cursor to interact with the system through structured tool calls. The MCP server provides guided workflows, embedded expertise, and fine-grained access control for AI-mediated research.

## Core Principles

### AI Assistant-First Design
The MCP server is optimized for:
- **AI assistants** (Claude Desktop, Cursor, etc.) as primary users
- **Guided workflows** through prompt templates
- **Embedded expertise** in tool descriptions
- **Natural discovery** through AI exploration

### Secure by Default
All operations enforce:
- **OAuth 2.1 authentication** with PKCE
- **Fine-grained scoping** per tool
- **Rate limiting** per client
- **Comprehensive audit logging**

### Modern MCP Patterns
Following established conventions from:
- **FastMCP** - Pythonic decorator-based API
- **MCP Specification** (March 2025) - OAuth 2.1, PKCE, resource indicators
- **terminalcp** - Single unified tool pattern for token efficiency

## Technical Implementation

### Framework
- **FastMCP** (Python 3.11+) - Modern MCP server framework
- **JSON-RPC 2.0** - MCP protocol transport
- **OAuth 2.1** - Authentication with PKCE
- **JWT** - Token validation with JWKS

### Protocol
- **Transport**: JSON-RPC 2.0 over HTTP/HTTPS
- **Authentication**: OAuth 2.1 with PKCE (no client secrets)
- **Scoping**: Hierarchical permissions per tool
- **Rate Limiting**: Token bucket algorithm

### Deployment
```bash
# Docker container
docker run -p 8080:8080 co-scientist/mcp:latest

# Kubernetes
kubectl apply -f deployments/mcp-server.yaml

# Local development
python -m fastmcp run src/mcp_server.py
```

## MCP Server Structure

### Server Configuration

```python
from fastmcp import FastMCP, Context
from fastmcp.auth import OAuth21Config

# Initialize MCP server
mcp = FastMCP(
    name="AI Co-Scientist",
    version="1.0.0",
    description="AI-powered scientific hypothesis generation and evaluation system"
)

# Configure OAuth 2.1 authentication
mcp.configure_auth(
    OAuth21Config(
        # Authorization server endpoints
        auth_url="https://auth.co-scientist.ai/authorize",
        token_url="https://auth.co-scientist.ai/token",
        jwks_url="https://auth.co-scientist.ai/.well-known/jwks.json",

        # Token validation
        audience="https://api.co-scientist.ai",
        issuer="https://auth.co-scientist.ai",

        # Scopes (hierarchical permissions)
        scopes={
            "research:read": "Read research projects and status",
            "research:write": "Create and modify research projects",
            "hypotheses:generate": "Generate new hypotheses",
            "hypotheses:evolve": "Evolve existing hypotheses",
            "reviews:read": "Read hypothesis reviews",
            "reviews:write": "Create hypothesis reviews",
            "admin": "Full system access"
        },

        # Security requirements
        pkce_required=True,  # Enforce PKCE for all flows
        refresh_token_rotation=True  # Rotate refresh tokens
    )
)
```

## Tool Definitions

### Research Management Tools

#### start_research

Start a new research project.

**Signature**:
```python
@mcp.tool(scopes=["research:write"])
async def start_research(
    goal: str,
    domain: str | None = None,
    hypothesis_count: int = 20,
    context: Context = None
) -> dict:
    """Start a new research project.

    This tool initiates a research project by:
    1. Parsing the research goal for scientific intent
    2. Identifying the scientific domain
    3. Initializing the hypothesis generation pipeline

    The system will generate hypotheses, review them through multiple
    evaluation processes, rank them using tournament-based comparison,
    and evolve top candidates.

    Args:
        goal: Research objective in natural language
              Examples:
              - "Find novel therapeutic targets for liver fibrosis"
              - "Identify drug repurposing candidates for AML"
              - "Investigate mechanisms of antimicrobial resistance"
        domain: Optional scientific domain (biology, chemistry, physics, etc.)
               If not provided, system will infer from goal
        hypothesis_count: Number of hypotheses to generate (default: 20, max: 100)
        context: MCP context with authentication and session info

    Returns:
        dict: Research project details
              {
                  "research_id": str,  # Use this ID for status queries
                  "goal": str,
                  "domain": str,
                  "status": "initializing",
                  "estimated_time_hours": float
              }

    Raises:
        PermissionError: If user lacks research:write scope
        ValueError: If goal is too short, unsafe, or invalid
        RuntimeError: If system resources unavailable

    Example:
        result = await start_research(
            goal="Find treatments for liver fibrosis",
            domain="biology",
            hypothesis_count=30
        )
        # Use result["research_id"] to check status later
    """
```

**Behavior**:
1. Validates `context.is_authenticated` - raises `PermissionError` if false
2. Checks `context.has_scope("research:write")` - raises `PermissionError` if false
3. Logs action: `await context.log_action("start_research", {goal, domain})`
4. Validates goal using Safety Framework (spec 020) - raises `ValueError` if unsafe
5. Creates research ID and stores in Context Memory
6. Submits initial generation tasks to Supervisor Agent
7. Returns immediately (non-blocking)

**Example Tool Call** (from Claude):
```
User: "Help me find new treatments for liver fibrosis using AI Co-Scientist"

Claude uses start_research tool:
{
  "goal": "Find novel therapeutic targets for liver fibrosis",
  "domain": "biology",
  "hypothesis_count": 30
}

Response:
{
  "research_id": "res_abc123",
  "goal": "Find novel therapeutic targets for liver fibrosis",
  "domain": "biology",
  "status": "initializing",
  "estimated_time_hours": 2.5
}

Claude responds: "I've started a research project to find novel therapeutic
targets for liver fibrosis. The research ID is res_abc123. The system is
currently initializing and will generate 30 hypotheses over approximately
2.5 hours. I'll check the status in a moment."
```

#### get_research_status

Get current status of a research project.

**Signature**:
```python
@mcp.tool(scopes=["research:read"])
async def get_research_status(
    research_id: str,
    context: Context = None
) -> dict:
    """Get current status of a research project.

    Provides real-time status of an active or completed research project,
    including progress metrics, hypothesis counts, and top candidates.

    Args:
        research_id: Research project identifier (from start_research)
        context: MCP context

    Returns:
        dict: Current project status
              {
                  "research_id": str,
                  "goal": str,
                  "status": str,  # "initializing", "active", "paused", "completed"
                  "progress": float,  # 0.0 to 1.0
                  "hypotheses_generated": int,
                  "hypotheses_reviewed": int,
                  "hypotheses_in_tournament": int,
                  "top_hypothesis": {
                      "id": str,
                      "summary": str,
                      "elo_score": float,
                      "status": str
                  } | None,
                  "last_update": str,  # ISO 8601 timestamp
                  "estimated_completion_minutes": int | None
              }

    Raises:
        PermissionError: If user lacks research:read scope
        ValueError: If research_id not found

    Example:
        status = await get_research_status(research_id="res_abc123")
        print(f"Progress: {status['progress'] * 100:.0f}%")
        print(f"Top hypothesis: {status['top_hypothesis']['summary']}")
    """
```

**Behavior**:
1. Verifies `context.has_scope("research:read")`
2. Fetches research metadata from Context Memory
3. Retrieves hypothesis and review counts
4. Calculates progress metrics
5. Returns current state

#### list_research_projects

List all research projects for authenticated user.

**Signature**:
```python
@mcp.tool(scopes=["research:read"])
async def list_research_projects(
    status: str | None = None,
    limit: int = 20,
    context: Context = None
) -> list[dict]:
    """List research projects for the authenticated user.

    Args:
        status: Optional filter by status (active, completed, paused)
        limit: Maximum number of projects to return (default 20, max 100)
        context: MCP context

    Returns:
        list[dict]: List of research project summaries
                    Each project includes: id, goal, domain, status,
                    hypothesis_count, created_at, last_updated

    Example:
        projects = await list_research_projects(status="active")
        for project in projects:
            print(f"{project['id']}: {project['goal']}")
    """
```

### Hypothesis Operations

#### generate_hypotheses

Generate new hypotheses for a research project.

**Signature**:
```python
@mcp.tool(scopes=["hypotheses:generate"])
async def generate_hypotheses(
    research_id: str,
    count: int = 10,
    method: str = "literature_based",
    context: Context = None
) -> list[dict]:
    """Generate new hypotheses for a research project.

    This tool creates novel scientific hypotheses using various generation
    strategies. Each hypothesis includes a summary, rationale, experimental
    protocol, and literature grounding.

    Args:
        research_id: Research project identifier
        count: Number of hypotheses to generate (default 10, max 50)
        method: Generation method
                - "literature_based": Extract from scientific literature
                - "debate": Generate through simulated expert debate
                - "assumptions": Challenge existing assumptions
                - "expansion": Expand on existing high-scoring hypotheses
        context: MCP context

    Returns:
        list[dict]: Generated hypotheses
                    Each hypothesis includes:
                    - id: Unique identifier
                    - summary: Concise description (50-100 words)
                    - rationale: Scientific justification
                    - experimental_protocol: Validation approach
                    - elo_score: Initial rating (1000)
                    - status: "pending"

    Raises:
        PermissionError: If user lacks hypotheses:generate scope
        ValueError: If count > 50 or invalid method
        RuntimeError: If research_id not found

    Example:
        hypotheses = await generate_hypotheses(
            research_id="res_abc123",
            count=20,
            method="debate"
        )
        print(f"Generated {len(hypotheses)} hypotheses")
        for hyp in hypotheses[:3]:
            print(f"- {hyp['summary']}")
    """
```

**Behavior**:
1. Validates parameters (count ≤ 50, method in allowed list)
2. Retrieves research goal from Context Memory
3. Submits generation task to Supervisor Agent
4. Waits for completion (blocking operation)
5. Stores hypotheses in Context Memory
6. Returns hypothesis list

#### evolve_hypothesis

Evolve an existing hypothesis using specified strategy.

**Signature**:
```python
@mcp.tool(scopes=["hypotheses:evolve"])
async def evolve_hypothesis(
    hypothesis_id: str,
    strategy: str = "refine",
    context: Context = None
) -> dict:
    """Evolve an existing hypothesis using specified strategy.

    Evolution strategies improve hypotheses through different approaches,
    creating new variations while preserving the core insight.

    Args:
        hypothesis_id: Hypothesis identifier to evolve
        strategy: Evolution strategy
                  - "refine": Improve specificity and testability
                  - "combine": Merge with complementary hypothesis
                  - "simplify": Reduce complexity while preserving insight
                  - "paradigm_shift": Challenge fundamental assumptions
        context: MCP context

    Returns:
        dict: Evolved hypothesis with new ID
              Original hypothesis remains in system for comparison

    Example:
        evolved = await evolve_hypothesis(
            hypothesis_id="hyp_abc123",
            strategy="refine"
        )
        print(f"Original: {hypothesis_id}")
        print(f"Evolved: {evolved['id']}")
        print(f"Improvement: {evolved['summary']}")
    """
```

**Behavior**:
1. Retrieves original hypothesis from Context Memory
2. Submits evolution task to Evolution Agent (spec 010)
3. Waits for completion (blocking)
4. Stores evolved hypothesis with new ID
5. Returns evolved hypothesis (original preserved)

#### list_hypotheses

List hypotheses for a research project.

**Signature**:
```python
@mcp.tool(scopes=["hypotheses:generate", "research:read"])
async def list_hypotheses(
    research_id: str,
    status: str | None = None,
    min_elo: float | None = None,
    limit: int = 50,
    context: Context = None
) -> list[dict]:
    """List hypotheses for a research project.

    Args:
        research_id: Research project identifier
        status: Optional filter by status (pending, reviewed, evolved)
        min_elo: Optional minimum ELO score
        limit: Maximum results (default 50, max 200)
        context: MCP context

    Returns:
        list[dict]: Hypotheses sorted by ELO score (descending)

    Example:
        # Get top 10 hypotheses with ELO > 1400
        top_hypotheses = await list_hypotheses(
            research_id="res_abc123",
            min_elo=1400,
            limit=10
        )
        for hyp in top_hypotheses:
            print(f"{hyp['elo_score']:.0f}: {hyp['summary']}")
    """
```

### Review and Ranking Tools

#### review_hypothesis

Create a review for a hypothesis.

**Signature**:
```python
@mcp.tool(scopes=["reviews:write"])
async def review_hypothesis(
    hypothesis_id: str,
    review_type: str = "initial",
    context: Context = None
) -> dict:
    """Review and evaluate a hypothesis.

    The system conducts a thorough scientific review using multiple
    criteria including plausibility, novelty, testability, and safety.

    Args:
        hypothesis_id: Hypothesis to review
        review_type: Type of review
                     - "initial": Quick initial assessment
                     - "deep_verification": Thorough literature-based review
                     - "simulation": Simulated experimental outcomes
        context: MCP context

    Returns:
        dict: Review results
              {
                  "review_id": str,
                  "hypothesis_id": str,
                  "review_type": str,
                  "scores": {
                      "plausibility": float,  # 0.0-1.0
                      "novelty": float,
                      "testability": float,
                      "safety": float,
                      "overall": float
                  },
                  "strengths": list[str],
                  "weaknesses": list[str],
                  "recommendations": list[str],
                  "citations": list[str],
                  "created_at": str
              }

    Example:
        review = await review_hypothesis(
            hypothesis_id="hyp_abc123",
            review_type="deep_verification"
        )
        print(f"Overall score: {review['scores']['overall']:.2f}")
        print(f"Strengths: {', '.join(review['strengths'])}")
    """
```

**Behavior**:
1. Submits review task to Reflection Agent (spec 008)
2. Waits for completion (blocking)
3. Stores review in Context Memory
4. Updates hypothesis metadata
5. Returns review details

#### rank_hypotheses

Rank hypotheses for a research project using tournament.

**Signature**:
```python
@mcp.tool(scopes=["hypotheses:generate", "reviews:read"])
async def rank_hypotheses(
    research_id: str,
    method: str = "tournament",
    context: Context = None
) -> list[dict]:
    """Rank hypotheses for a research project.

    Uses tournament-based comparison to establish relative rankings
    with ELO scores. More reliable than absolute scoring.

    Args:
        research_id: Research project identifier
        method: Ranking method
                - "tournament": Tournament-based pairwise comparison (recommended)
                - "direct_comparison": Direct quality assessment
        context: MCP context

    Returns:
        list[dict]: Ranked hypotheses with updated ELO scores
                    Sorted by ELO score descending

    Example:
        ranked = await rank_hypotheses(research_id="res_abc123")
        print("Top 5 hypotheses:")
        for i, hyp in enumerate(ranked[:5], 1):
            print(f"{i}. {hyp['summary']} (ELO: {hyp['elo_score']:.0f})")
    """
```

**Behavior**:
1. Retrieves all hypotheses for research project
2. Submits ranking task to Ranking Agent (spec 009)
3. Waits for completion (may take several minutes for large sets)
4. Updates ELO scores in Context Memory
5. Returns ranked list

### Results Tools

#### get_results

Get research results summary.

**Signature**:
```python
@mcp.tool(scopes=["research:read", "hypotheses:generate"])
async def get_results(
    research_id: str,
    format: str = "summary",
    top_n: int = 10,
    context: Context = None
) -> dict:
    """Get research results for a project.

    Args:
        research_id: Research project identifier
        format: Result format
                - "summary": Executive summary with top hypotheses
                - "detailed": Full hypotheses with protocols
                - "nih_aims": NIH Specific Aims page format
        top_n: Number of top hypotheses to include (default 10)
        context: MCP context

    Returns:
        dict: Research results formatted per spec 019 (Output Formats)

    Example:
        results = await get_results(
            research_id="res_abc123",
            format="summary",
            top_n=5
        )
        print(results["executive_summary"])
        for hyp in results["top_hypotheses"]:
            print(f"- {hyp['summary']} (ELO: {hyp['elo_score']})")
    """
```

## Resource Definitions

Resources expose data that AI assistants can read directly without tool calls.

### research://projects/{project_id}

Expose research project as readable resource.

**URI Pattern**: `research://projects/{project_id}`

**Signature**:
```python
@mcp.resource("research://projects/{project_id}")
async def get_research_resource(project_id: str, context: Context) -> str:
    """Expose research project as readable resource.

    Returns markdown-formatted research project details that AI assistants
    can read to understand project status and results.

    Args:
        project_id: Research project ID
        context: MCP context

    Returns:
        str: Markdown-formatted research project details

    Permissions:
        Requires: research:read scope

    Format:
        # Research Project: {project_id}

        ## Goal
        {goal}

        ## Status
        {status}

        ## Statistics
        - Hypotheses Generated: {count}
        - Average ELO Score: {average}

        ## Top Hypotheses
        1. **{summary}** (ELO: {elo_score})
           {rationale}...
        2. ...
    """
```

**Example Usage** (Claude Desktop):
```
Claude reads resource: research://projects/res_abc123

Content:
# Research Project: res_abc123

## Goal
Find novel therapeutic targets for liver fibrosis

## Status
active (78% complete)

## Statistics
- Hypotheses Generated: 47
- Average ELO Score: 1315

## Top Hypotheses
1. **Target KDM4A demethylase to reverse stellate cell activation** (ELO: 1432)
   Based on literature showing KDM4A upregulation in fibrotic tissue...

2. **Inhibit DNMT3B to prevent hepatocyte-to-myofibroblast transition** (ELO: 1398)
   Novel connection between DNA methylation and cellular phenotype...

Claude: "I can see your research is 78% complete with 47 hypotheses generated.
The top candidate is targeting KDM4A demethylase with an ELO score of 1432.
Would you like me to review this hypothesis in more detail?"
```

### hypothesis://{hypothesis_id}

Expose hypothesis as readable resource.

**URI Pattern**: `hypothesis://{hypothesis_id}`

**Signature**:
```python
@mcp.resource("hypothesis://{hypothesis_id}")
async def get_hypothesis_resource(hypothesis_id: str, context: Context) -> str:
    """Expose hypothesis as readable resource.

    Returns markdown-formatted hypothesis with full details including
    rationale, experimental protocol, and literature citations.

    Args:
        hypothesis_id: Hypothesis ID
        context: MCP context

    Returns:
        str: Markdown-formatted hypothesis

    Permissions:
        Requires: hypotheses:generate scope

    Format:
        # Hypothesis: {summary}

        **ID**: {id}
        **ELO Score**: {elo_score}
        **Status**: {status}

        ## Rationale
        {rationale}

        ## Experimental Protocol
        {protocol}

        ## Predictions
        1. {prediction_1}
        2. {prediction_2}

        ## Literature Grounding
        - {citation_1}
        - {citation_2}
    """
```

## Prompt Templates

Prompt templates guide AI assistants through common workflows.

### research-workflow

Complete research workflow template.

**Signature**:
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
```

**Content**:
```markdown
# AI Co-Scientist Research Workflow

Follow these steps to conduct scientific research:

## 1. Start Research Project
Use `start_research` tool with:
- Clear research goal (e.g., "Find novel treatments for Alzheimer's disease")
- Optional domain specification (biology, chemistry, physics, etc.)
- Hypothesis count: 20-30 for initial batch

## 2. Generate Initial Hypotheses
Use `generate_hypotheses` tool with:
- research_id from step 1
- count: 20-30 for first round
- method: "literature_based" is recommended initially

## 3. Monitor Progress
Use `get_research_status` tool periodically to check:
- How many hypotheses have been generated
- How many have been reviewed
- Current top hypothesis

## 4. Review Hypotheses
For promising hypotheses, use `review_hypothesis` tool:
- Start with "initial" review type
- Use "deep_verification" for top candidates

## 5. Rank Hypotheses
Use `rank_hypotheses` tool with method="tournament":
- Establishes relative rankings through pairwise comparison
- Updates ELO scores for all hypotheses

## 6. Evolve Top Hypotheses
For top 5 hypotheses, use `evolve_hypothesis`:
- strategy: "refine" to improve specificity
- strategy: "combine" to merge complementary ideas

## 7. Iterate
Repeat steps 2-6 until:
- ELO scores converge (changes < 10 points)
- Time/resource budget exhausted
- User satisfied with results

## 8. Export Results
Use `get_results` to retrieve final results:
- format: "summary" for overview
- format: "nih_aims" for grant proposals
- Specify top_n for number of hypotheses to include

## Tips
- Generate in batches (20-30 hypotheses per batch)
- Review before ranking (improves tournament accuracy)
- Evolve only top candidates (saves resources)
- Monitor ELO scores for convergence
- Use resources (research://, hypothesis://) to inspect details
```

### hypothesis-analysis

Deep hypothesis analysis template.

**Signature**:
```python
@mcp.prompt("hypothesis-analysis")
async def hypothesis_analysis_prompt(hypothesis_id: str, context: Context) -> str:
    """Template for deep hypothesis analysis.

    Args:
        hypothesis_id: Hypothesis to analyze
    """
```

**Content** (parameterized):
```markdown
# Deep Hypothesis Analysis: {hypothesis_id}

{hypothesis_resource_content}

## Analysis Tasks

1. **Testability Assessment**
   - Are predictions specific enough?
   - What experiments would validate/falsify?
   - What resources are required?
   - Timeline estimate?

2. **Literature Review**
   - What existing research supports this?
   - What contradicts it?
   - What are the gaps?
   - Key papers to read?

3. **Mechanism Analysis**
   - Is the proposed mechanism plausible?
   - What are the key assumptions?
   - What could go wrong?
   - Alternative explanations?

4. **Impact Assessment**
   - If true, what are the implications?
   - What fields would be affected?
   - What are the ethical considerations?
   - Translational potential?

## Recommended Actions

Use `review_hypothesis` tool with review_type="deep_verification" to get
AI-powered analysis of these questions.

If hypothesis looks promising, use `evolve_hypothesis` to:
- Refine experimental protocol
- Add missing details
- Address potential weaknesses
```

## OAuth 2.1 Authentication

### Authorization Flow

The MCP server uses OAuth 2.1 with PKCE for secure authentication without client secrets.

**Flow Diagram**:
```
┌───────────┐                                  ┌────────────┐
│  Claude   │                                  │   Auth     │
│ Desktop   │                                  │  Server    │
└─────┬─────┘                                  └──────┬─────┘
      │                                               │
      │ 1. Generate code_verifier (random)           │
      │    code_challenge = SHA256(code_verifier)    │
      │                                               │
      │ 2. Authorization Request                     │
      │    + client_id                               │
      │    + code_challenge                          │
      │    + code_challenge_method=S256              │
      │    + scope=research:read research:write      │
      ├──────────────────────────────────────────────>│
      │                                               │
      │ 3. User authorizes in browser                │
      │                                               │
      │ 4. Authorization Code                        │
      │<──────────────────────────────────────────────┤
      │                                               │
      │ 5. Token Request                             │
      │    + code                                    │
      │    + code_verifier                           │
      ├──────────────────────────────────────────────>│
      │                                               │
      │    Server verifies:                          │
      │    SHA256(code_verifier) == code_challenge   │
      │                                               │
      │ 6. Access Token + Refresh Token              │
      │<──────────────────────────────────────────────┤
      │                                               │
```

**Implementation**:
```python
from fastmcp.auth import OAuth21Flow
import secrets, hashlib, base64

class CoScientistOAuth(OAuth21Flow):
    """OAuth 2.1 flow with PKCE."""

    async def start_authorization(self, client_id: str, redirect_uri: str) -> dict:
        """Start authorization flow.

        Returns authorization URL and PKCE parameters.
        """
        # Generate PKCE parameters
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')

        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')

        # Generate state (CSRF protection)
        state = secrets.token_urlsafe(32)

        # Build authorization URL
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "research:read research:write hypotheses:generate",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state
        }

        auth_url = f"{self.auth_url}?{urlencode(params)}"

        return {
            "authorization_url": auth_url,
            "state": state,
            "code_verifier": code_verifier  # Store for token exchange
        }

    async def exchange_code(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        client_id: str
    ) -> dict:
        """Exchange authorization code for tokens.

        Uses PKCE for verification (no client secret needed).
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "code_verifier": code_verifier  # PKCE verification
            })

            response.raise_for_status()
            return response.json()  # {access_token, refresh_token, ...}
```

### Token Validation

The MCP server validates JWT access tokens:

```python
import jwt
from jwt import PyJWKClient

class TokenValidator:
    """Validate JWT access tokens."""

    def __init__(self, jwks_url: str, audience: str, issuer: str):
        self.jwks_client = PyJWKClient(jwks_url)
        self.audience = audience
        self.issuer = issuer

    def validate(self, access_token: str) -> dict:
        """Validate JWT and return payload."""
        # Get signing key from JWKS endpoint
        signing_key = self.jwks_client.get_signing_key_from_jwt(access_token)

        # Decode and validate
        payload = jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.audience,
            issuer=self.issuer,
            options={
                "verify_signature": True,
                "verify_exp": True,  # Check expiration
                "verify_aud": True,  # Check audience
                "verify_iss": True   # Check issuer
            }
        )

        return {
            "user_id": payload["sub"],
            "scopes": payload["scope"].split(),
            "email": payload.get("email"),
            "expires_at": payload["exp"]
        }
```

## Scope Design

### Hierarchical Scopes

Scopes provide fine-grained access control with hierarchical permissions:

```python
SCOPES = {
    # Read-only scopes
    "research:read": {
        "description": "Read research projects and status",
        "implies": []
    },
    "hypotheses:read": {
        "description": "Read hypotheses and their details",
        "implies": []
    },
    "reviews:read": {
        "description": "Read hypothesis reviews and scores",
        "implies": []
    },

    # Write scopes
    "research:write": {
        "description": "Create and modify research projects",
        "implies": ["research:read"]  # Write implies read
    },
    "hypotheses:generate": {
        "description": "Generate new hypotheses",
        "implies": ["research:read", "hypotheses:read"]
    },
    "hypotheses:evolve": {
        "description": "Evolve existing hypotheses",
        "implies": ["hypotheses:read"]
    },
    "reviews:write": {
        "description": "Create and modify reviews",
        "implies": ["reviews:read", "hypotheses:read"]
    },

    # Administrative scopes
    "admin": {
        "description": "Full system access",
        "implies": [
            "research:read", "research:write",
            "hypotheses:read", "hypotheses:generate", "hypotheses:evolve",
            "reviews:read", "reviews:write"
        ]
    }
}

def has_scope(user_scopes: list[str], required_scope: str) -> bool:
    """Check if user has required scope (including implied scopes)."""
    # Direct match
    if required_scope in user_scopes:
        return True

    # Check implied scopes
    for user_scope in user_scopes:
        if user_scope in SCOPES:
            implied = SCOPES[user_scope].get("implies", [])
            if required_scope in implied:
                return True

    return False
```

## Error Handling

### Error Types

```python
from fastmcp import MCPError

class CoScientistError(MCPError):
    """Base error for MCP server."""

    def __init__(self, code: str, message: str, details: dict = None):
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
    """Resource does not exist."""
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
```

### Error Handler

```python
@mcp.error_handler
async def handle_errors(error: Exception, context: Context) -> dict:
    """Global error handler for MCP server."""

    # Log error
    logger.error(f"MCP error: {error}", exc_info=True)

    # Handle specific error types
    if isinstance(error, CoScientistError):
        return error.to_json()
    elif isinstance(error, PermissionError):
        return CoScientistError("permission_denied", str(error)).to_json()
    elif isinstance(error, ValueError):
        return CoScientistError("invalid_input", str(error)).to_json()
    else:
        return CoScientistError("internal_error", "An unexpected error occurred").to_json()
```

## Rate Limiting

### Token Bucket Algorithm

```python
from collections import defaultdict
from datetime import datetime
import asyncio

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        self.rate = requests_per_minute / 60.0  # requests per second
        self.burst_size = burst_size
        self.buckets: dict[str, tuple[float, datetime]] = defaultdict(
            lambda: (burst_size, datetime.utcnow())
        )
        self.lock = asyncio.Lock()

    async def check_limit(self, user_id: str) -> tuple[bool, int]:
        """Check if request is allowed.

        Returns:
            tuple: (allowed, retry_after_seconds)
        """
        async with self.lock:
            now = datetime.utcnow()
            tokens, last_update = self.buckets[user_id]

            # Refill tokens based on time elapsed
            elapsed = (now - last_update).total_seconds()
            tokens = min(self.burst_size, tokens + elapsed * self.rate)

            if tokens >= 1.0:
                # Allow request
                tokens -= 1.0
                self.buckets[user_id] = (tokens, now)
                return True, 0
            else:
                # Rate limited
                retry_after = int((1.0 - tokens) / self.rate)
                return False, retry_after

# Usage
rate_limiter = RateLimiter(requests_per_minute=60, burst_size=10)

@mcp.before_tool
async def check_rate_limit(context: Context):
    """Check rate limit before executing tool."""
    allowed, retry_after = await rate_limiter.check_limit(context.user.id)

    if not allowed:
        raise RateLimitExceededError(retry_after)
```

## Audit Logging

### Audit Logger

```python
from dataclasses import dataclass
import json

@dataclass
class AuditLogEntry:
    """Audit log entry."""
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    parameters: dict
    result: str  # success, failure, error
    ip_address: str
    user_agent: str

class AuditLogger:
    """Audit logger for security events."""

    def __init__(self, log_file: Path):
        self.log_file = log_file

    async def log_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        parameters: dict,
        result: str,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Log a user action."""
        entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            resource=resource,
            parameters=parameters,
            result=result,
            ip_address=ip_address or "unknown",
            user_agent=user_agent or "unknown"
        )

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry.__dict__, default=str) + '\n')

# Usage
audit_logger = AuditLogger(Path("/var/log/co-scientist/audit.log"))

@mcp.before_tool
async def log_tool_call(context: Context, tool_name: str, parameters: dict):
    """Log all tool calls."""
    await audit_logger.log_action(
        user_id=context.user.id,
        action=f"tool:{tool_name}",
        resource=f"mcp://tools/{tool_name}",
        parameters=parameters,
        result="started",
        ip_address=context.request.client_ip,
        user_agent=context.request.user_agent
    )
```

## Claude Desktop Configuration

### Configuration File

To use with Claude Desktop, add to `claude_desktop_config.json`:

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

## Integration with System Components

### Supervisor Agent Integration
```python
# MCP server calls Supervisor Agent methods
from src.agents.supervisor import SupervisorAgent

supervisor = SupervisorAgent(
    task_queue=task_queue,
    context_memory=context_memory,
    llm_provider=llm_provider
)

@mcp.tool(scopes=["research:write"])
async def start_research(goal: str, domain: str = None, context: Context = None):
    """MCP tool implementation."""
    # Create research ID
    research_id = generate_research_id()

    # Store in Context Memory
    await context_memory.set(f"research:{research_id}:goal", goal)

    # Submit tasks via Supervisor
    await supervisor.create_task(
        agent_type="generation",
        priority=3,
        parameters={"research_id": research_id, "goal": goal}
    )

    # Log for audit
    await context.log_action("start_research", {"goal": goal, "domain": domain})

    return {"research_id": research_id, ...}
```

### Context Memory Integration
- MCP server reads/writes directly to Context Memory
- Consistent state across MCP and CLI interfaces
- Supports local file-based or remote database storage

### Safety Framework Integration
- All research goals validated by Safety Framework (spec 020)
- Unsafe operations blocked with clear explanation
- Audit logging for security review

## Alignment with Core Principles

### Expert-in-the-Loop (spec 002)
- AI assistants facilitate human-AI collaboration
- All critical decisions require human approval
- Transparent reasoning available for inspection

### Safety Framework (spec 020)
- Research goals validated before processing
- Unsafe hypotheses blocked from generation
- Multi-layer safety checks enforced

### Scientific Success Criteria (spec 002)
- Outputs include quality metrics (ELO, novelty)
- Evidence and citations preserved
- Experimental protocols generated

### Transparency and Explainability (spec 002)
- All operations logged
- Decision reasoning available
- State queryable via resources

## Testing Strategy

### Unit Tests
```python
import pytest
from fastmcp.testing import MCPTestClient

@pytest.fixture
async def mcp_client():
    """Test client with mock authentication."""
    client = MCPTestClient(mcp)
    client.set_auth_context({
        "user_id": "test_user",
        "scopes": ["research:read", "research:write", "hypotheses:generate"],
        "email": "test@example.com"
    })
    return client

@pytest.mark.asyncio
async def test_start_research(mcp_client):
    """Test starting research via MCP."""
    result = await mcp_client.call_tool(
        "start_research",
        goal="Find treatments for liver fibrosis",
        domain="biology"
    )

    assert "research_id" in result
    assert result["goal"] == "Find treatments for liver fibrosis"
    assert result["status"] == "initializing"

@pytest.mark.asyncio
async def test_insufficient_permissions(mcp_client):
    """Test permission enforcement."""
    mcp_client.set_auth_context({
        "user_id": "test_user",
        "scopes": ["research:read"],  # Missing research:write
        "email": "test@example.com"
    })

    with pytest.raises(PermissionError, match="research:write scope required"):
        await mcp_client.call_tool("start_research", goal="Test goal")
```

## Performance Characteristics

### Response Times

Target response times for MCP operations:

- **Tool calls (non-blocking)**: <2 seconds
- **Tool calls (blocking)**: Variable (depends on LLM)
- **Resource reads**: <1 second
- **Prompt templates**: <500ms

### Optimization Strategies

- **Async operations**: Non-blocking where possible
- **Caching**: Cache Context Memory queries
- **Connection pooling**: Reuse database connections
- **Rate limiting**: Prevent abuse

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

This MCP server specification provides a comprehensive, modern interface for AI assistants to interact with the AI Co-Scientist system, enabling guided workflows, embedded expertise, and secure access control while maintaining full alignment with the system's core principles and existing components.
