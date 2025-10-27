# Phase 0: Cleanroom Specification Generation Guide

**Complete step-by-step guide for generating behavioral specifications before implementation**

---

## Overview

Phase 0 is the **specification generation phase** that happens BEFORE any code is written. You create comprehensive behavioral specifications from source materials using the cleanroom methodology. This ensures you understand the complete system before implementing.

**Key Principle**: Specifications describe **WHAT** the system does, not **HOW** it's built.

---

## Why Cleanroom Methodology?

### Benefits
- **Complete Understanding**: Forces thorough reading of source materials
- **Clear Interfaces**: Defines inputs, outputs, behaviors before code
- **No Implementation Bias**: Specifications remain pure (WHAT, not HOW)
- **Better Planning**: Generates comprehensive implementation plan
- **Reduced Rework**: Catches design issues before coding

### Success Metrics
- All source materials read completely
- All behaviors documented
- Clear input/output specifications
- No implementation details in specs
- Team can implement from specs alone

---

## Directory Structure

```
YourProject/
├── specs-source/              # Source materials (read-only)
│   ├── main-paper.md         # Primary source document
│   ├── architecture-blog.md  # Secondary overview
│   ├── diagram-01.png        # System architecture
│   ├── diagram-02.png        # Data flow
│   └── references/           # Related frameworks, patterns
│       ├── framework-docs.md
│       └── design-patterns.md
├── specs/                     # Generated specifications (output)
│   ├── 001-system-overview.md
│   ├── 002-core-principles.md
│   └── ...
├── docs/
│   └── spec-development/     # Methodology documentation
│       └── [reference docs]
├── SPECS_PLAN.md             # Specification task list
├── run-spec-loop.sh          # Spec generation loop script
├── specs-prompt.md           # Claude prompt for spec generation
├── SPECS_CLAUDE.md           # Spec guidelines for Claude
└── README.md                 # Project overview
```

---

## Step-by-Step Process

### Phase 0.1: Setup Your Project Structure

#### 1. Create Project Directory

```bash
mkdir YourProjectName
cd YourProjectName
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

#### 2. Create Directory Structure

```bash
mkdir -p specs-source/references
mkdir -p specs
mkdir -p docs/spec-development
```

#### 3. Copy Template Files

You can use gem-flux-mcp as a template:

```bash
# From gem-flux-mcp directory
PROJECT_DIR="/path/to/your/new/project"

# Core spec loop files (to root)
cp run-spec-loop.sh $PROJECT_DIR/
cp specs-prompt.md $PROJECT_DIR/
cp SPECS_CLAUDE.md $PROJECT_DIR/

# Reference documentation
cp docs/PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md $PROJECT_DIR/docs/spec-development/

# Make script executable
chmod +x $PROJECT_DIR/run-spec-loop.sh
```

#### 4. Create Initial SPECS_PLAN.md

**Option A - Empty Approach** (AI creates the plan):
```bash
cat > SPECS_PLAN.md << 'EOF'
# Specification Plan

Nothing here yet. The AI will create a comprehensive plan after reading all source materials.
EOF
```

**Option B - Hybrid Approach** (You provide structure):
```bash
cat > SPECS_PLAN.md << 'EOF'
# Specification Plan

## Phase 1: Core Architecture
- [ ] System overview and design philosophy
- [ ] Core components and their responsibilities
- [ ] High-level architecture

## Phase 2: Key Components
- [ ] Component A specification
- [ ] Component B specification
- [ ] Component C specification

## Phase 3: Integration
- [ ] Communication protocols
- [ ] Data flow specifications
- [ ] Error handling patterns

## Phase 4: Quality & Safety
- [ ] Testing strategy
- [ ] Security requirements
- [ ] Performance expectations
EOF
```

**Recommendation**: Use **Empty Approach** for exploration projects, **Hybrid Approach** when you know the structure.

---

### Phase 0.2: Gather Source Materials

#### 1. Identify Your Sources

Source materials can be:
- **Research Papers**: Convert PDF to markdown
- **Blog Posts**: Save as markdown
- **Documentation**: Existing framework docs
- **Architecture Diagrams**: PNG, JPG images
- **Code Examples**: Reference implementations
- **Design Documents**: Technical specifications

#### 2. Convert Materials to Readable Format

```bash
# Convert PDF to text/markdown
pdftotext source.pdf specs-source/main-paper.md

# Download blog post as markdown
curl https://example.com/blog | pandoc -f html -t markdown -o specs-source/blog.md

# Copy images
cp diagrams/*.png specs-source/
```

#### 3. Organize in specs-source/

```
specs-source/
├── main-paper.md              # PRIMARY SOURCE (most important)
├── supplementary-blog.md      # Additional context
├── architecture-diagram.png   # Visual reference
├── workflow-diagram.png       # Process flow
└── references/
    ├── mcp-specification.md   # Related framework
    ├── oauth-rfc.md          # Security standard
    └── fastmcp-docs.md       # Implementation framework
```

**Critical**: Claude will read ALL files in specs-source/. Ensure quality and relevance.

---

### Phase 0.3: Customize Template Files

#### 1. Edit specs-prompt.md

Update project-specific sections:

```markdown
# [Your Project Name] Specification Task

Read all materials in specs-source/ and any existing work in specs/.

Your task: Implement the FIRST UNCHECKED item from SPECS_PLAN.md by creating
CLEANROOM specifications (implementation-free behavioral specs).

## Requirements:
- Focus only on WHAT the system does, not HOW
- Define clear interfaces and capabilities
- Specify expected inputs/outputs
- Document behavioral contracts
- Follow the guidelines in SPECS_CLAUDE.md
- Consider [your domain-specific patterns]  # ← CUSTOMIZE

## Key Elements to Specify (as relevant):
- [Domain-specific element 1]  # ← CUSTOMIZE
- [Domain-specific element 2]  # ← CUSTOMIZE
- Communication protocols
- API interfaces
- Safety and security boundaries
```

#### 2. Edit SPECS_CLAUDE.md

Update the **Project Context** section:

```markdown
## Project Context

[Your Project Name] is a [brief description]:
- [Key capability 1]
- [Key capability 2]
- [Architecture pattern]
- [Main use cases]

## 📊 UNDERSTANDING THE SYSTEM

From your complete read, you know:
- **Component A**: [Responsibilities and behaviors]
- **Component B**: [Responsibilities and behaviors]
- **Component C**: [Responsibilities and behaviors]
```

#### 3. Create .gitignore

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store

# Spec loop artifacts
.spec_loop_state

# Environment
.env
EOF
```

---

### Phase 0.4: Run the Specification Loop

#### 1. Make Script Executable (if not already)

```bash
chmod +x run-spec-loop.sh
```

#### 2. Start the Loop

```bash
./run-spec-loop.sh
```

#### 3. What Happens - Iteration Flow

**First Iteration** (Empty Approach):
```
=== Gem-Flux MCP Server Spec Creation Loop ===
This will run up to 10 iterations, pausing between each for review.
Press Ctrl+C at any time to stop.

=== Running spec creation iteration 1 ===

[Claude reads ALL materials in specs-source/]
[Claude analyzes the domain and creates comprehensive plan]
[Claude writes plan to SPECS_PLAN.md]

✓ Plan has been created! Check SPECS_PLAN.md
The model will now start creating individual specs on the next run.

Recent changes:
M SPECS_PLAN.md

Press Enter to continue to next iteration, or Ctrl+C to stop...
```

**Second Iteration**:
```
=== Running spec creation iteration 2 ===

[Claude reads SPECS_PLAN.md]
[Finds first unchecked item: "- [ ] System overview and design philosophy"]
[Reads relevant source materials]
[Creates specs/001-system-overview.md]
[Marks task complete: "- [x] System overview and design philosophy"]

Recent changes:
M SPECS_PLAN.md
A specs/001-system-overview.md

Press Enter to continue to next iteration, or Ctrl+C to stop...
```

**Subsequent Iterations**:
- Claude finds next unchecked task
- Creates corresponding spec file
- Updates SPECS_PLAN.md
- Pauses for your review

**Completion**:
```
✓ All tasks completed!

=== Spec creation loop finished ===
To see all changes: git status
To see specs created: ls -la specs/
```

#### 4. Review Each Iteration

After each spec is created:

**Quality Checks**:
- [ ] Describes **WHAT**, not **HOW**
- [ ] Clear inputs and outputs defined
- [ ] Interaction patterns specified
- [ ] Examples provided
- [ ] No implementation details (no classes, functions, algorithms)
- [ ] Consistent with source materials

**Common Issues**:
- ❌ "The system uses a HashMap to store..." → Implementation detail
- ✅ "The system stores key-value pairs..." → Behavioral description
- ❌ "Class DatabaseManager with connect() method" → Implementation
- ✅ "Database connection must support reconnection on failure" → Behavior

**If Quality Issues Found**:
```bash
# Edit the spec manually
vim specs/001-system-overview.md

# Or ask Claude to revise
echo "The spec includes implementation details. Please revise to focus on behaviors only." | claude -p
```

**If Satisfied**:
```bash
# Press Enter to continue
# Loop will generate next spec
```

---

### Phase 0.5: Validate Specifications

#### 1. Review SPECS_PLAN.md Completion

```bash
# Check for remaining unchecked tasks
grep "^\- \[ \]" SPECS_PLAN.md

# Should return nothing if complete
```

Expected final state:
```markdown
## Phase 1: Core Architecture
- [x] System overview and design philosophy
- [x] Core components and their responsibilities
- [x] High-level architecture

## Phase 2: Key Components
- [x] Component A specification
- [x] Component B specification
...

ALL PHASES COMPLETE
```

#### 2. Quality Audit

**Automated Checks**:
```bash
# Count specifications created
SPEC_COUNT=$(ls specs/*.md | wc -l)
echo "Total specifications: $SPEC_COUNT"

# Check for implementation keywords (should be minimal)
grep -ri "class\|function\|algorithm\|implement" specs/ | wc -l

# Check for behavioral keywords (should be abundant)
grep -ri "must\|should\|behavior\|input\|output" specs/ | wc -l
```

**Manual Review Checklist**:
- [ ] All specs in numbered format (001-, 002-, etc.)
- [ ] Each spec has clear purpose statement
- [ ] Prerequisites listed when specs depend on others
- [ ] Examples provided for complex behaviors
- [ ] Error conditions documented
- [ ] No code snippets (except interface definitions)
- [ ] Consistent terminology across specs

#### 3. Create Completeness Report

```bash
cat > SPECIFICATION_COMPLETENESS_REPORT.md << EOF
# Specification Completion Report

**Date**: $(date +%Y-%m-%d)
**Total Specifications**: $(ls specs/*.md | wc -l)

## Status
✅ All planned specifications have been created following CLEANROOM principles.

## Phases Completed
$(grep "^## Phase" SPECS_PLAN.md | while read line; do
    phase_num=$(echo "$line" | grep -oP 'Phase \K\d+')
    spec_count=$(grep -c "^\- \[x\]" <<< "$(awk "/^## Phase $phase_num:/,/^## Phase/" SPECS_PLAN.md)")
    echo "- Phase $phase_num: $spec_count specs"
done)

## Specifications Created
$(ls specs/*.md | while read spec; do
    title=$(head -1 "$spec" | sed 's/# //')
    echo "- $(basename $spec): $title"
done)

## Quality Validation
- Behavioral focus: ✅ (no implementation details)
- Clear interfaces: ✅ (inputs/outputs defined)
- Examples provided: ✅
- Consistent terminology: ✅

## Ready for Implementation
✅ Specifications complete
✅ Implementation plan can now be generated
✅ Ready to transition to Phase 1 (Implementation Loop)

## Next Steps
1. Create IMPLEMENTATION_PLAN.md from specifications
2. Copy implementation loop files
3. Begin test-driven development
EOF
```

---

### Phase 0.6: Commit Specifications

#### 1. Review All Changes

```bash
git status
git diff SPECS_PLAN.md
git diff specs/
```

#### 2. Commit in Logical Groups

**Option A - Single commit** (if small project):
```bash
git add -A
git commit -m "docs: complete cleanroom specification phase

- Generated comprehensive specification plan
- Created $(ls specs/*.md | wc -l) behavioral specifications
- All specs follow CLEANROOM principles (WHAT, not HOW)
- Ready for implementation phase"
```

**Option B - Per-spec commits** (if using version control during loop):
```bash
# Already committed during loop iterations
git log --oneline | head -10
```

---

## Transition to Implementation Phase

### Checkpoint: Are You Ready?

Before moving to implementation, verify:

- [ ] All tasks in SPECS_PLAN.md marked [x]
- [ ] Specifications describe WHAT, not HOW
- [ ] Clear interfaces defined for all components
- [ ] Examples provided for complex behaviors
- [ ] Completeness report created
- [ ] All specs committed to git
- [ ] Team understands the system from specs alone

### Next Phase: Implementation Loop

See `/docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md` for:
- Creating IMPLEMENTATION_PLAN.md from specs
- Setting up test-driven development
- Configuring quality gates
- Running the implementation loop
- Context optimization (ACE-FCA)

---

## Example: Complete Phase 0 Flow

```bash
# 1. SETUP (5 minutes)
mkdir AwesomeProject && cd AwesomeProject
git init
mkdir -p specs-source/references specs docs/spec-development

# 2. COPY TEMPLATES (2 minutes)
cp ~/gem-flux-mcp/run-spec-loop.sh ./
cp ~/gem-flux-mcp/specs-prompt.md ./
cp ~/gem-flux-mcp/SPECS_CLAUDE.md ./
chmod +x run-spec-loop.sh

# 3. ADD SOURCES (10-30 minutes)
# Download/convert your source materials
curl https://paper-url.com/paper.pdf | pdftotext - specs-source/main-paper.md
# Add diagrams, references, etc.

# 4. CUSTOMIZE (10 minutes)
# Edit specs-prompt.md (update project name, domain-specific elements)
# Edit SPECS_CLAUDE.md (update project context)
# Create SPECS_PLAN.md (empty or hybrid approach)

# 5. RUN SPEC LOOP (30-60 minutes for small project, 2-4 hours for large)
./run-spec-loop.sh
# Review each iteration
# Press Enter to continue
# Claude generates ~1 spec per 3-5 minutes

# 6. VALIDATE (15 minutes)
grep "^\- \[ \]" SPECS_PLAN.md  # Should be empty
ls specs/*.md | wc -l           # Count specs
# Create completeness report

# 7. COMMIT (5 minutes)
git add -A
git commit -m "docs: complete cleanroom specification phase"

# 8. TRANSITION TO IMPLEMENTATION
# See Phase 1 guide
```

**Total Time**: 1-6 hours depending on project complexity

---

## Tips & Best Practices

### Source Material Quality

**Good Sources**:
- ✅ Research papers with clear methodology
- ✅ Well-documented frameworks
- ✅ Architecture diagrams with explanations
- ✅ API documentation with examples
- ✅ Design documents with rationale

**Poor Sources**:
- ❌ Marketing materials (lacks technical detail)
- ❌ Code without documentation
- ❌ Incomplete drafts
- ❌ Contradictory documents

### Claude Prompting Tips

**During Spec Loop**:
- Let Claude read completely first (don't rush)
- Review each spec before continuing (quality over speed)
- Provide feedback if spec has implementation details
- Ask for clarification if behaviors unclear

**Feedback Examples**:
```
# If too much implementation
"This spec describes HOW (using classes). Revise to describe WHAT (behaviors only)."

# If missing details
"The authentication spec doesn't specify error conditions. Add failure behaviors."

# If good
[Press Enter to continue]
```

### Iteration Count

**Typical Ranges**:
- Small project (5-10 components): 6-12 specs, 2-4 iterations
- Medium project (10-20 components): 15-25 specs, 4-8 iterations
- Large project (20+ components): 30+ specs, 8-10+ iterations

**If Hitting 10 Iteration Limit**:
```bash
# Edit run-spec-loop.sh
# Change: for i in {1..10}
# To: for i in {1..20}

# Or run loop again after completion
./run-spec-loop.sh  # Continues from where it left off
```

### Spec Numbering

**Convention**:
- 001-009: System-level (overview, principles, workflow)
- 010-019: Core infrastructure (models, queue, memory)
- 020-029: Services (authentication, security, APIs)
- 030+: Domain components (agents, tools, specialized)

**Example**:
```
001-system-overview.md
002-core-principles.md
003-research-workflow.md
010-data-models.md
011-task-queue.md
020-authentication.md
021-authorization.md
030-generation-agent.md
031-reflection-agent.md
```

### Common Mistakes

**Mistake 1**: Not reading source materials completely
- **Symptom**: Specs miss key features or have gaps
- **Fix**: Ensure Claude sees "I've read all materials in specs-source/" before creating plan

**Mistake 2**: Allowing implementation details
- **Symptom**: Specs mention classes, algorithms, data structures
- **Fix**: Review each spec; provide feedback to revise

**Mistake 3**: Vague specifications
- **Symptom**: "The system handles data" (what data? how?)
- **Fix**: Ask for specific inputs, outputs, behaviors

**Mistake 4**: Inconsistent terminology
- **Symptom**: "hypothesis" vs "research idea" used interchangeably
- **Fix**: Create glossary in 001-system-overview.md

---

## Troubleshooting

### Problem: Loop creates plan but no specs

**Cause**: specs-prompt.md not checking for PLAN_CREATED signal

**Fix**:
```bash
# Check specs-prompt.md contains:
grep "PLAN_CREATED" specs-prompt.md

# Should see:
# d. Exit with message: "PLAN_CREATED - Please run again to start creating specs"
```

### Problem: Specs contain code snippets

**Cause**: SPECS_CLAUDE.md guidelines not clear enough

**Fix**:
```bash
# Add to SPECS_CLAUDE.md under "WHAT TO EXCLUDE":
- Class definitions
- Function implementations
- Algorithms (sorting, searching, etc.)
- Data structure internals
- Code examples (except interface definitions)
```

### Problem: Loop completes but tasks still unchecked

**Cause**: Claude marking wrong file or format issue

**Fix**:
```bash
# Check SPECS_PLAN.md format
# Correct: - [x] Task name
# Wrong: -[x] Task name (no space)
# Wrong: - [ x ] Task name (extra spaces)

# Manually mark completed tasks
vim SPECS_PLAN.md
```

### Problem: Too many/too few specs

**Cause**: Granularity mismatch in plan

**Fix**:
```markdown
# Too granular (30+ specs for small project)
- [ ] Component A initialization
- [ ] Component A method 1
- [ ] Component A method 2
# Fix: Combine into single "Component A" spec

# Too coarse (5 specs for large project)
- [ ] All agents
# Fix: Split into individual agent specs
```

---

## Reference Files

### Files in This Repository

```
gem-flux-mcp/
├── run-spec-loop.sh              # Main spec loop script
├── specs-prompt.md               # Claude prompt template
├── SPECS_CLAUDE.md               # Guidelines for Claude
├── SPECS_PLAN.md                 # Task list (generated)
├── docs/
│   ├── PHASE_0_CLEANROOM_SPECIFICATION_GUIDE.md  # This file
│   └── spec-development/
│       └── [reference materials]
└── specs-source/
    └── references/
        └── mcp-server-reference.md  # Example source material
```

### Related Documentation

- **Phase 1 Guide**: `/docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md` (implementation phase)
- **ACE-FCA Context**: How context optimization works during implementation
- **Test Strategy**: How test-driven development integrates with loop

---

## Success Stories

### CogniscientAssistant Project

**Stats**:
- 28 specifications created
- 8 phases planned
- 3 days of spec generation
- Zero rework during implementation (specs were complete)

**Key Insight**: "Spending 3 days on specs saved 2 weeks of refactoring"

### Gem-Flux MCP Server Project

**Stats** (example):
- 12 specifications planned
- 4 phases (Auth, Tools, Resources, Deployment)
- 1 day of spec generation
- Empty approach (AI created plan)

**Key Insight**: "AI-generated plan was more comprehensive than our initial outline"

---

## Summary Checklist

**Before Starting**:
- [ ] Project directory created
- [ ] Git initialized
- [ ] Directory structure created (specs-source/, specs/)
- [ ] Template files copied and customized
- [ ] Source materials gathered and organized
- [ ] SPECS_PLAN.md created (empty or hybrid)

**During Spec Loop**:
- [ ] Review each spec for quality (WHAT not HOW)
- [ ] Verify behaviors clearly documented
- [ ] Check inputs/outputs defined
- [ ] Ensure examples provided
- [ ] Confirm no implementation details

**After Completion**:
- [ ] All SPECS_PLAN.md tasks marked [x]
- [ ] Quality audit passed
- [ ] Completeness report created
- [ ] Specifications committed to git
- [ ] Ready to create IMPLEMENTATION_PLAN.md

**Next Phase**:
- [ ] Read Phase 1 Implementation Loop Guide
- [ ] Create IMPLEMENTATION_PLAN.md from specs
- [ ] Copy implementation loop files
- [ ] Begin test-driven development

---

**You are now ready to run Phase 0!** Follow the steps above, and you'll have comprehensive specifications before writing any code.

For the next phase (implementation), see: `/docs/PHASE_1_IMPLEMENTATION_LOOP_GUIDE.md`
