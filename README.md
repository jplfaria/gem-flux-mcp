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

## Development Methodology

This project follows a **two-phase AI-assisted development methodology**:

### Phase 0: Cleanroom Specification Generation

Generate behavioral specifications BEFORE writing code:

1. **Read source materials** - Study all materials in `specs-source/`
2. **Generate plan** - AI creates comprehensive specification plan
3. **Create specs** - AI generates CLEANROOM behavioral specifications (WHAT, not HOW)
4. **Review and iterate** - Human reviews, AI refines

**Run the spec loop**:
```bash
./run-spec-loop.sh
```

**Documentation**: See `/docs/PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md` for complete step-by-step instructions.

### Phase 1: Implementation Loop (After Specs Complete)

Implement code with AI assistance and quality gates:

1. **Create implementation plan** - Break specs into atomic tasks
2. **Run implementation loop** - AI implements with test-driven development
3. **Quality gates** - Tests (≥80% coverage), no regressions
4. **Context optimization** - Only load relevant specs (40-90% reduction)

**Documentation**: See `/docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md` for complete instructions.

**Template files**: Available in `/docs/implementation-loop-development/to-use-later/`

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

See `SPECS_CLAUDE.md` for complete guidelines.

## Reference Materials

- **MCP Server Reference** - `specs-source/references/mcp-server-reference.md`
  - FastMCP patterns
  - OAuth 2.1 with PKCE
  - Tool/Resource/Prompt definitions
  - Complete MCP server example

## Documentation

### For Developers Setting Up This Methodology

- **Phase 0 Guide**: `/docs/PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md`
  - Complete cleanroom spec generation instructions
  - How to gather source materials
  - How to run the spec loop
  - Quality validation checklist

- **Phase 1 Guide**: `/docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md`
  - Implementation loop setup
  - Test-driven development workflow
  - Quality gates and coverage requirements
  - Context optimization (ACE-FCA)
  - Troubleshooting and best practices

- **Implementation Loop Resources**: `/docs/implementation-loop-development/`
  - Template files for implementation phase
  - README with file descriptions
  - Reference implementation from CogniscientAssistant

### For AI Agents Reading This

**If you're Claude Code working in this project**:

1. **First**: Read `/docs/PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md` to understand the methodology
2. **During Spec Generation**: Follow guidelines in `SPECS_CLAUDE.md`
3. **During Implementation**: Follow guidelines in `CLAUDE.md` (after Phase 0)

## Next Steps

1. ✅ Project structure created
2. ✅ Reference materials added
3. ✅ Comprehensive guides created
4. ⏭️ **START HERE**: Run `./run-spec-loop.sh` to generate specs (Phase 0)
5. ⏭️ Review and validate all specifications
6. ⏭️ Create `IMPLEMENTATION_PLAN.md` from specs
7. ⏭️ Copy implementation loop files from `/docs/implementation-loop-development/to-use-later/`
8. ⏭️ Run implementation loop (Phase 1)

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
