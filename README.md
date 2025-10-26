# Gem-Flux MCP Server

A Model Context Protocol (MCP) server for [project purpose - to be defined during spec generation].

## Status

🚧 **In Specification Phase** - Using cleanroom methodology to generate specifications before implementation.

## Project Structure

```
gem-flux-mcp/
├── specs-source/          # Source materials for spec generation
│   └── references/        # Reference documentation
├── specs/                 # Generated specifications
├── docs/
│   └── spec-development/  # Spec generation tools and guidelines
└── README.md
```

## Cleanroom Spec Generation

This project uses the cleanroom methodology:

1. **Read source materials** - Study all materials in `specs-source/`
2. **Generate plan** - AI creates comprehensive specification plan
3. **Create specs** - AI generates CLEANROOM behavioral specifications (WHAT, not HOW)
4. **Review and iterate** - Human reviews, AI refines

### Running the Spec Loop

```bash
# Make script executable
chmod +x docs/spec-development/run-spec-loop.sh

# Run the spec generation loop
./docs/spec-development/run-spec-loop.sh
```

The loop will:
- Create `SPECS_PLAN.md` on first run (if empty approach)
- Generate individual specs one at a time
- Pause between iterations for human review
- Stop after 10 iterations or when all tasks complete

### What Gets Generated

- **SPECS_PLAN.md** - Comprehensive plan with all specification tasks
- **specs/*.md** - Individual specification files (001-system-overview.md, etc.)
- Each spec describes BEHAVIORS, not implementation

### Guidelines

All specs must follow:
- **CLEANROOM principles** - No implementation details
- **MCP patterns** - FastMCP, OAuth 2.1, JSON-RPC 2.0
- **Clear interfaces** - Inputs, outputs, behaviors
- **Security** - OAuth flows, scopes, rate limiting

See `docs/spec-development/SPECS_CLAUDE.md` for complete guidelines.

## Reference Materials

- **MCP Server Reference** - `specs-source/references/mcp-server-reference.md`
  - FastMCP patterns
  - OAuth 2.1 with PKCE
  - Tool/Resource/Prompt definitions
  - Complete MCP server example

## Next Steps

1. ✅ Project structure created
2. ✅ Reference materials added
3. ⏭️ Run `./docs/spec-development/run-spec-loop.sh` to generate specs
4. ⏭️ Review and refine specifications
5. ⏭️ Create `IMPLEMENTATION_PLAN.md` from specs
6. ⏭️ Begin implementation with AI-assisted development loop

## Technology Stack (After Implementation)

- **Python 3.11+** - Core runtime
- **FastMCP** - MCP server framework
- **OAuth 2.1 + PKCE** - Secure authentication
- **JSON-RPC 2.0** - Protocol transport
- **JWT** - Token validation

## License

[License to be determined]

---

*Generated with cleanroom methodology - specifications define WHAT, implementation defines HOW.*
