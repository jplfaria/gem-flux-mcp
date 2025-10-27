#!/bin/bash
# Generate initial prompt for first iteration when IMPLEMENTATION_PLAN.md is empty

cat > prompt.md << 'EOF'
# Gem-Flux MCP Server - Initial Implementation Planning

## Task: Generate IMPLEMENTATION_PLAN.md

You are starting a new implementation project. Your first task is to:

1. **Read and analyze all 20 specifications** in the specs/ directory
2. **Generate a comprehensive IMPLEMENTATION_PLAN.md** with phases and tasks
3. **Follow the original CogniscientAssistant methodology**: break implementation into logical phases

## All Specifications

EOF

# Append all specs
for spec in specs/*.md; do
    if [ -f "$spec" ]; then
        echo "### $(basename $spec .md | sed 's/-/ /g' | sed 's/\b\w/\u&/g')" >> prompt.md
        echo "" >> prompt.md
        cat "$spec" >> prompt.md
        echo "" >> prompt.md
        echo "---" >> prompt.md
        echo "" >> prompt.md
    fi
done

cat >> prompt.md << 'EOF'

## Implementation Guidelines

EOF

cat CLAUDE.md >> prompt.md

cat >> prompt.md << 'EOF'

## Your Task

Analyze the 20 specifications above and create a comprehensive IMPLEMENTATION_PLAN.md with:

1. **Phases**: Logical groupings of related functionality (likely 10-15 phases)
2. **Tasks**: Specific, testable implementation tasks for each phase
3. **Dependencies**: Clear ordering based on what depends on what
4. **Test Strategy**: Integration tests starting from first testable component

Use this structure:

```markdown
# Gem-Flux MCP Server Implementation Plan

## Phase 1: [Name]
**Goal**: [What this phase accomplishes]
**Dependencies**: [What must be done first]

### Tasks
- [ ] Task 1
- [ ] Task 2
...

## Phase 2: [Name]
...
```

**Guidelines**:
- Phase 1 should be infrastructure/setup
- Database and template loading should come early (Phase 2-3)
- Core tools (build_media, build_model, gapfill, run_fba) are Phases 4-7
- Session management and lookup tools follow
- Integration and error handling come last
- Each task should be atomic and testable

Generate the plan now and save it to IMPLEMENTATION_PLAN.md.
EOF

echo "✅ Generated prompt.md with all specifications"
