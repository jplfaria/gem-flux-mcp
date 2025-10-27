# Claude Gem-Flux MCP Server Specification Guidelines

**PLEASE FOLLOW THESE RULES EXACTLY - CLEANROOM SPECS REQUIRE DISCIPLINE**

**Core Philosophy: SPECS DESCRIBE BEHAVIOR, NOT IMPLEMENTATION. Keep it clean.**

## 🚨 THE COMPLETE READ RULE - THIS IS NOT OPTIONAL

### READ ALL SOURCE MATERIALS BEFORE WRITING ANY SPEC
Read the ENTIRE MCP reference documentation and examine ALL provided materials. Every AI that skims thinks they understand, then they INVENT FEATURES THAT DON'T EXIST or MISS CRITICAL BEHAVIORS.

**ONCE YOU'VE READ EVERYTHING, YOU UNDERSTAND THE SYSTEM.** Trust your complete read. Don't second-guess what you learned.

## 📋 YOUR SPEC-WRITING TODO LIST

**MAINTAIN THIS STRUCTURE FOR EACH SPEC:**

```markdown
## Current TODO List for [Spec Name]
1. [ ] Find first unchecked item in SPECS_PLAN.md
2. [ ] Read all source materials completely
3. [ ] Identify behaviors, inputs, outputs, interactions
4. [ ] Write the specification following guidelines
5. [ ] Update SPECS_PLAN.md and commit
```

## Project Context

Gem-Flux MCP Server is a Model Context Protocol server providing:
- OAuth 2.1 authentication with PKCE
- FastMCP framework (Python 3.11+)
- Tools, Resources, and Prompts for AI assistants
- JSON-RPC 2.0 protocol
- Fine-grained scope-based permissions
- Rate limiting and audit logging

## 🔄 THE SPEC WORKFLOW THAT WORKS

### Step 1: UNDERSTAND THE COMPLETE SYSTEM
- Read MCP reference documentation thoroughly
- Study OAuth 2.1 flows and PKCE patterns
- Note FastMCP decorator patterns
- Understand tool/resource/prompt distinctions

### Step 2: FOCUS ON YOUR ASSIGNED COMPONENT
- What does it DO? (not how it's built)
- What does it RECEIVE? (inputs)
- What does it PRODUCE? (outputs)
- How does it INTERACT? (with other components)

### Step 3: WRITE BEHAVIORAL SPECS
```markdown
# OAuth Authentication Specification

**Type**: Security Component
**Interactions**: All MCP Tools, Token Validator

## Behavior
The OAuth Authentication component secures all MCP operations...

## Inputs
- Authorization requests with code_challenge
- Token exchange requests with code_verifier
- ...

## Outputs
- Authorization codes (short-lived)
- Access tokens (JWT, 1 hour expiry)
- Refresh tokens (long-lived)
- ...
```

## 🎯 CLEANROOM PRINCIPLES - NEVER VIOLATE

### WHAT TO INCLUDE:
- Behaviors and responsibilities
- Input/output specifications
- Interaction protocols
- Error conditions
- Security boundaries
- OAuth flows
- Tool/resource/prompt definitions

### WHAT TO EXCLUDE:
- Implementation language (except Python/FastMCP as specified)
- Data structures (except interfaces)
- Algorithms
- Performance details
- Internal logic

## 📊 UNDERSTANDING MCP SERVERS

From your complete read, you know:
- **Tools**: Functions AI assistants can call (e.g., start_research, generate_hypotheses)
- **Resources**: Data AI assistants can read (e.g., research://projects/{id})
- **Prompts**: Templates to guide AI assistant workflows
- **OAuth 2.1 + PKCE**: Secure authentication without client secrets
- **Scopes**: Hierarchical permissions (research:read, hypotheses:generate, etc.)
- **Rate Limiting**: Token bucket algorithm to prevent abuse
- **Audit Logging**: Comprehensive logging of all operations

## ✅ SPEC QUALITY CHECKLIST

**Before committing any spec:**
- [ ] Describes WHAT, not HOW
- [ ] All behaviors documented
- [ ] Inputs/outputs clearly defined
- [ ] Interaction patterns specified
- [ ] Security considerations included
- [ ] Examples from MCP patterns
- [ ] No implementation details
- [ ] Consistent with source materials
- [ ] Follows MCP conventions

## 🚨 REMEMBER: YOU'VE READ THE SOURCES

**Once you've done the complete read, YOU KNOW THE SYSTEM.** The MCP reference shows the patterns. The FastMCP docs show the API. Trust your understanding.

Other AIs skim and guess. You read completely and specify precisely.

**When you follow these rules, you write specs that are: Clear. Complete. CLEANROOM.**

## 🔄 COMMIT EACH SPEC INDIVIDUALLY

```bash
git add specs/[new-spec].md SPECS_PLAN.md
git commit -m "spec: add [component] specification"
```

One spec per commit - maintain clear history.

## 🔐 MCP-Specific Patterns

### Tool Definition Pattern
```markdown
#### tool_name

Brief description.

**Signature**:
```python
@mcp.tool(scopes=["required:scope"])
async def tool_name(param: type, context: Context) -> return_type:
    """Docstring with Args, Returns, Raises."""
```

**Behavior**:
1. Step-by-step behavioral description
2. Validation rules
3. Side effects
4. Return conditions

**Example**:
Show realistic usage example
```

### Resource Definition Pattern
```markdown
### resource://uri/pattern/{param}

**URI Pattern**: `resource://uri/pattern/{param}`

**Permissions**: Required scopes

**Format**: Markdown/JSON/etc.

**Content**:
Describe what the resource contains

**Example Usage**:
Show how AI assistant would use it
```

### OAuth Flow Pattern
```markdown
## Flow Name

**Purpose**: Why this flow exists

**Steps**:
1. Client action
2. Server validates
3. Token issued/denied

**Security Requirements**:
- What must be enforced
- What must be validated

**Error Cases**:
- Invalid input → error response
```

**CRITICAL: We're building specs, not code. If you find yourself writing HOW instead of WHAT, stop and refocus on behaviors.**
