# Gem-Flux MCP Server Specification Task

Read all materials in specs-source/ and any existing work in specs/.

Your task: Implement the FIRST UNCHECKED item from SPECS_PLAN.md by creating
CLEANROOM specifications (implementation-free behavioral specs).

## Requirements:
- Focus only on WHAT the system does, not HOW
- Define clear interfaces and capabilities
- Specify expected inputs/outputs
- Document behavioral contracts
- Follow the guidelines in docs/spec-development/SPECS_CLAUDE.md
- Consider MCP server patterns and OAuth 2.1 flows

## Process:
1. Read SPECS_PLAN.md
   - If it contains "Nothing here yet" or is empty:
     a. Study ALL materials in specs-source/ thoroughly
     b. CREATE a comprehensive specification plan with phases and checkboxes
     c. Save this plan to SPECS_PLAN.md
     d. Exit with message: "PLAN_CREATED - Please run again to start creating specs"
   - Otherwise, find the first unchecked [ ] item
2. Study all relevant materials in specs-source/, including:
   - references/mcp-server-reference.md for MCP patterns
   - Any other reference materials provided
3. Review any existing specs in specs/ for context and consistency
4. Create a new specification file in specs/ with appropriate naming
   - Use numbered prefixes: 001-system-overview.md, 002-oauth-authentication.md, etc.
   - Follow document organization from SPECS_CLAUDE.md
5. Update SPECS_PLAN.md to mark the item as complete [x]

## Completion Handling:
If you cannot find any incomplete tasks after checking SPECS_PLAN.md thoroughly:
- Output: "ALL_TASKS_COMPLETE"
- List all phases you checked
- Confirm all items show [x] instead of [ ]
- Exit without creating any new specifications

## Specification Format:
- Use clear section headers
- Add Prerequisites section when specs depend on others
- Define interfaces using BAML when appropriate
- Include relevant examples and edge cases
- Document error handling behavior

## Key Elements to Specify (as relevant):
- Core behaviors and responsibilities
- Communication protocols (JSON-RPC 2.0, OAuth 2.1)
- API interfaces (tools, resources, prompts)
- Safety and security boundaries
- Integration patterns with MCP clients

## Examples of Good MCP Specifications:

### Example 1: Tool Specification
```
Tool: list_hypotheses
Input:
  - research_id: string (required)
  - status: string (optional, values: "pending", "reviewed", "evolved")
  - min_elo: float (optional, filter by minimum ELO score)

Output:
  - List[Hypothesis] sorted by ELO score descending

Behavior:
  - Validates research_id exists
  - Filters by status if provided
  - Filters by min_elo if provided
  - Returns maximum 100 hypotheses
  - Requires scope: hypotheses:generate OR research:read
```

### Example 2: OAuth Flow Specification
```
Authorization Flow: OAuth 2.1 with PKCE
1. Client generates code_verifier (random 32 bytes)
2. Client computes code_challenge = SHA256(code_verifier)
3. Client requests authorization with code_challenge
4. User authorizes in browser
5. Server returns authorization code
6. Client exchanges code + code_verifier for tokens
7. Server validates SHA256(code_verifier) == code_challenge
8. Server returns access_token + refresh_token
```

### Example 3: Resource Specification
```
Resource: research://projects/{project_id}
Format: Markdown
Permissions: Requires research:read scope

Content includes:
- Research goal
- Current status
- Progress metrics
- Top hypotheses with ELO scores
- Recent updates

Used by AI assistants to:
- Inspect project state
- Understand research direction
- Report progress to user
```

Write your output to specs/ folder.
