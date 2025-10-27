# Claude AI Co-Scientist Implementation Guidelines

**Core Philosophy: IMPLEMENT FROM SPECS. Build behavior exactly as specified.**

## 📖 Reading Requirements

### Before Implementation
- Read ALL specs in specs/ directory first
- Understand the complete system before coding
- Trust the specs - they define all behaviors

### During Implementation
- **New file**: Read ENTIRE file before modifying
- **Small file (<500 lines)**: Read completely
- **Large file (500+ lines)**: Read at least 1500 lines
- **ALWAYS** understand existing code before adding new code

## 📁 Test Organization

### Test Directory Structure
- **Unit tests**: `tests/unit/test_*.py` - Test individual components
- **Integration tests**: `tests/integration/test_phase*_*.py` - Test system workflows
- **NO other test subdirectories** - Don't create tests/baml/, tests/agents/, etc.
- **NO tests in root tests/ directory** - All tests must be in unit/ or integration/

### Test Naming Convention
- Unit test: `tests/unit/test_<module_name>.py`
- Integration test: `tests/integration/test_phase<N>_<feature>.py`
- Example: `tests/unit/test_task_queue.py`, `tests/integration/test_phase3_queue_workflow.py`

## 🔄 Implementation Workflow

### 1. Check Status
```bash
# At start of each iteration, check for errors
if [ -f ".implementation_flags" ]; then
    if grep -q "INTEGRATION_REGRESSION=true" .implementation_flags; then
        echo "❌ Fix regression before continuing"
    elif grep -q "IMPLEMENTATION_ERROR=true" .implementation_flags; then
        echo "❌ Fix implementation to match specs"
    fi
    # After fixing: rm .implementation_flags
fi
```

### 2. One Task Per Iteration
- Pick FIRST unchecked [ ] task from IMPLEMENTATION_PLAN.md
- Implement it COMPLETELY with tests
- Don't start multiple tasks
- Each iteration MUST have passing tests before commit

### 3. Test-First Development
- Write failing tests BEFORE implementation
- Implement minimal code to pass tests
- All tests must pass (pytest)
- Coverage must meet 80% threshold
- Integration tests use test_expectations.json

### 4. Commit and Continue
```bash
# Only if all tests pass:
git add -A
git commit -m "feat: implement [component] - [what you did]"
# Then exit - the loop will continue
```

## 🧪 Testing Requirements

### Integration Test Categories
- **✅ Pass**: Implementation correct
- **⚠️ Expected Failure**: Tests in `may_fail` list
- **❌ Critical Failure**: Tests in `must_pass` list failed
- **❌ Unexpected Failure**: Unlisted tests failed
- **❌ Regression**: Previously passing test fails

### Test Expectations
The file `tests/integration/test_expectations.json` defines:
- `must_pass`: Critical tests that block progress
- `may_fail`: Tests allowed to fail (waiting for future components)
- `real_llm_tests`: Optional tests that verify actual AI behavior
- `must_use_baml`: Methods that MUST call BAML functions (Phase 1 improvement)

### BAML Mocking Requirements
When adding new BAML functions or types:
1. **Update `/tests/conftest.py`** with new function mocks
2. **Add new BAML types** to mock_types as MockBAMLType
3. **Create enum mocks** with MockEnumValue for enum types
4. **Use side_effects** for complex mock behaviors
5. See `docs/BAML_TESTING_STRATEGY.md` for detailed patterns

### BAML Integration Requirements (Phase 1 Improvements)
For agent implementations:
1. **Content-generating methods MUST use BAML** - no hardcoded mock data
2. **Check `must_use_baml` in test_expectations.json** - lists required BAML methods
3. **Verify BAML integration before marking complete** - test with real calls
4. **Mock implementations only for data transformation** - not content generation
5. See `docs/IMPLEMENTATION_LOOP_IMPROVEMENTS.md` for rationale

## 🤖 Real LLM Testing

### Purpose
Verify that agents exhibit expected AI behaviors with actual models (not mocked).

### Implementation
- Write alongside regular integration tests
- Use naming: `test_phaseN_component_real.py`
- Mark with `@pytest.mark.real_llm`
- Test behaviors, not exact outputs
- Keep token usage minimal (<100 per test)

### Example Structure
```python
@pytest.mark.real_llm
async def test_supervisor_real_orchestration():
    """Test Supervisor exhibits planning behavior with o3."""
    supervisor = SupervisorAgent()
    result = await supervisor.plan_research("Why does ice float?")
    
    # Test behavioral expectations
    assert len(result.subtasks) >= 3  # Proper decomposition
    assert "density" in str(result).lower()  # Key concepts
    # Verify o3 shows reasoning steps
    assert any(marker in result.reasoning.lower() 
              for marker in ["step", "first", "then"])
```

### When to Write
- For agent phases (9+) that use LLMs
- Focus on model-specific behaviors (o3 reasoning, Claude creativity)
- Not needed for infrastructure phases

### Execution
- NOT part of automated loop (too slow/expensive)
- Run manually: `pytest tests/integration/*_real.py -v --real-llm`
- Run before major releases or when debugging AI behavior

## 🛡️ Safety & Security

### Argo Gateway Security
- **NEVER** commit usernames or API keys
- Use environment variables for configuration
- Keep argo-api-documentation.md in .gitignore
- Ensure VPN connection for Argo access

### Safety Framework
- Check research goals before processing
- Filter unsafe hypotheses
- Monitor research directions
- Log everything for auditing

## 🏗️ Technical Stack

### Core Technologies
- **Python 3.11+**: Async/await for concurrency
- **BAML**: ALL LLM interactions (no direct API calls)
- **pytest**: Comprehensive testing with ≥80% coverage
- **File-based storage**: .aicoscientist/ directory

## 🎯 BAML Prompt Requirements

### Critical: All BAML Functions MUST Use System + User Roles
**Why**: Claude and Gemini models require at least one user message. Using only system messages causes API errors.

### Correct BAML Prompt Structure
```baml
function FunctionName(param: string) -> ReturnType {
  client ProductionClient
  
  prompt #"
    {{ _.role("system") }}
    You are an expert at [specific task].
    [General instructions and capabilities]
    
    {{ _.role("user") }}
    [Specific request that needs the LLM's help]
    
    Input: {{ param }}
    
    [Detailed task-specific instructions]
  "#
}
```

### NEVER Do This (Will Fail with Claude/Gemini)
```baml
// ❌ WRONG - System message only
prompt #"
  You are an expert...
  Input: {{ param }}
"#
```

### Implementation Checklist
- [ ] Every BAML function has `{{ _.role("system") }}` AND `{{ _.role("user") }}`
- [ ] System role contains general instructions
- [ ] User role contains the specific request
- [ ] Parameters are referenced in the user section
- [ ] Test with multiple models (o3, Claude, Gemini)

## 🔧 Tool Calling Best Practices

### Overview: Tool Calling vs BAML

These are **complementary** technologies, not alternatives:

| Technology | Purpose | When to Use |
|------------|---------|-------------|
| **Tool Calling** | Data retrieval, system actions | Dynamic context, external data, reducing input tokens |
| **BAML** | Structured output parsing, reasoning | Complex logic, content generation, structured responses |

**Golden Rule:** BAML handles reasoning/content generation, tools handle data retrieval and actions.

### When to Use Tool Calling

✅ **Use tools when:**
- Context is too large to load upfront (>10K tokens)
- Need dynamic, LLM-driven data fetching
- Integrating external APIs (Semantic Scholar, etc.)
- Performing system actions (start research, generate hypotheses)
- Reducing token costs through selective loading

❌ **Don't use tools when:**
- All context fits in prompt (<5K tokens)
- Static data that doesn't change
- Simple transformations (use BAML functions)
- Need guaranteed structured output (use BAML for parsing)

### Tool Design Principles

#### 1. Granular, Single-Purpose Tools

```python
# ✅ GOOD: Focused tools
get_hypothesis_details(hypothesis_id: str, include_embedding: bool)
get_hypothesis_reviews(hypothesis_id: str, review_type: str)

# ❌ BAD: Monolithic tool
get_all_hypothesis_data(hypothesis_id: str, include_reviews: bool,
                        include_tournaments: bool, include_similar: bool)
```

**Why:** LLM can compose multiple calls. Small tools are easier to test and maintain.

#### 2. Self-Documenting Parameters

```python
# ✅ GOOD: Clear, typed parameters with descriptions
{
    "hypothesis_id": {
        "type": "string",
        "description": "UUID of hypothesis to fetch",
        "pattern": "^[0-9a-f-]{36}$"
    },
    "review_type": {
        "type": "string",
        "enum": ["novelty", "correctness", "testability"],
        "description": "Type of reviews to fetch"
    }
}

# ❌ BAD: Vague parameters
{
    "id": {"type": "string"},  # What kind of ID?
    "options": {"type": "object"}  # What options?
}
```

#### 3. Structured Error Returns

Always return errors as structured data so LLM can decide how to proceed:

```python
async def execute(self, parameters: dict) -> dict:
    try:
        result = await self._do_work(parameters)
        return result
    except ValueError as e:
        return {
            "error": f"Invalid parameter: {str(e)}",
            "error_type": "validation_error",
            "can_retry": True  # LLM can try again with better params
        }
    except Exception as e:
        return {
            "error": f"Tool execution failed: {str(e)}",
            "error_type": "execution_error",
            "can_retry": False  # LLM should try different approach
        }
```

#### 4. Performance Limits

```python
@dataclass
class ToolDefinition:
    timeout_seconds: int = 30  # Prevent hanging
    max_result_size: int = 10_000  # Prevent token overflow

async def execute(self, parameters: dict) -> dict:
    result = await self._fetch_data(parameters)

    # Truncate large results
    if len(json.dumps(result)) > self.max_result_size:
        result = self._summarize(result)

    return result
```

### Tool Calling Patterns by Phase

#### Phase 11 (Ranking): Selective Context Loading

**Problem:** Need context for 2 hypotheses, but loading all 50 wastes tokens.

**Solution:** LLM fetches only what it needs.

```baml
function CompareHypothesesWithTools(
    hypothesis_a_id: string,
    hypothesis_b_id: string
) -> ComparisonResult {
    prompt #"
        {{ _.role("system") }}
        You are a hypothesis evaluator with access to tools.

        Available tools:
        - get_hypothesis_details: Fetch hypothesis content and metrics
        - get_hypothesis_reviews: Fetch reviews for a hypothesis

        {{ _.role("user") }}
        Compare hypothesis {{ hypothesis_a_id }} and {{ hypothesis_b_id }}.

        PROCESS:
        1. get_hypothesis_details for both hypotheses
        2. Compare and determine winner
        3. Only if needed: get_hypothesis_reviews for deeper analysis
    "#
}
```

**Token Reduction:** 40-60%

#### Phase 14 (Meta-Review): Aggregate-First Approach

**Problem:** Synthesizing 100+ hypotheses exceeds context limits.

**Solution:** Fetch aggregates first, drill down only if needed.

```baml
function SynthesizeResearchWithTools() -> MetaReview {
    prompt #"
        {{ _.role("system") }}
        You are a research synthesizer with access to aggregation tools.

        {{ _.role("user") }}
        Synthesize findings across all hypotheses and reviews.

        PROCESS:
        1. get_review_statistics to understand overall patterns
        2. get_reviews_by_pattern for most frequent patterns
        3. get_top_hypotheses_summary for winners
        4. Synthesize high-level findings
        5. ONLY if needed for examples: get_hypothesis_details
    "#
}
```

**Token Reduction:** 70-93%

#### Phase 19 (Literature Search): Zero Hallucinated Citations

**Problem:** LLM may generate fake citations.

**Solution:** Tools ensure all citations are verified.

```baml
function GenerateHypothesisFromLiteratureWithTools(
    research_goal: string
) -> HypothesisWithEvidence {
    prompt #"
        {{ _.role("system") }}
        You are a hypothesis generator with literature search tools.

        Available tools:
        - search_semantic_scholar: Search for papers
        - get_paper_details: Get full paper metadata
        - verify_citation: Check if a citation/DOI exists

        {{ _.role("user") }}
        Generate hypothesis for: {{ research_goal }}

        CRITICAL: You MUST use verify_citation for ALL citations
        before finalizing hypothesis. No fake citations allowed!

        PROCESS:
        1. search_semantic_scholar to find relevant papers
        2. get_paper_details for most promising papers
        3. Generate hypothesis based on findings
        4. verify_citation for EVERY citation in your hypothesis
        5. If verification fails, replace with verified citation
    "#
}
```

**Key Benefit:** Zero hallucinated citations via `verify_citation`

#### Phase 21 (Conversational AI): Simplified Architecture

**Problem:** Intent router + handlers + BAML = complex architecture.

**Solution:** LLM + tools = single component.

```python
# OLD APPROACH (50+ lines, 3 components)
class ConversationGraph:
    def _create_graph(self):
        graph.add_node("intent_router", self._route_intent)
        graph.add_node("start_research_handler", self._handle_start_research)
        graph.add_node("generate_handler", self._handle_generate)
        # ... 8 more handlers

# NEW APPROACH (10 lines, 1 component)
class ConversationGraph:
    def _create_tool_enhanced_graph(self):
        # Single node: LLM + tools handles everything!
        graph.add_node("handle_with_tools", self._handle_message_with_tools)
        graph.set_entry_point("handle_with_tools")
        graph.set_finish_point("handle_with_tools")
```

**Code Reduction:** 50%
**Key Benefit:** Natural parameter extraction (LLM understands context vs regex)

### Testing Requirements for Tools

Every tool handler MUST have:

1. **Unit Tests**
   - Success case
   - Error cases (validation, execution)
   - Edge cases (empty data, large data)

2. **Integration Tests**
   - With Context Memory
   - With real BAML functions
   - Multi-tool workflows

3. **Real LLM Tests** (when applicable)
   - Token reduction verification
   - Tool selection accuracy
   - Multi-turn tool workflows

Example:
```python
@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_tool_calling_token_reduction():
    """Verify tool calling reduces token usage."""
    # Baseline: Load all context
    response_baseline = await argo_provider.generate(
        messages=[{"role": "user", "content": all_context}]
    )
    baseline_tokens = response_baseline.usage.prompt_tokens

    # Optimized: Use tools
    response_tools = await argo_provider.execute_tool_call_workflow(
        messages=[{"role": "user", "content": query}],
        tools=["get_hypothesis_details"]
    )
    tools_tokens = response_tools.usage.prompt_tokens

    # Assert reduction
    reduction = (baseline_tokens - tools_tokens) / baseline_tokens
    assert reduction >= 0.30  # At least 30% reduction
```

### Common Pitfalls

#### Pitfall 1: Tool Results Too Verbose

❌ **Problem:**
```python
return {
    "hypothesis": full_hypothesis_object,  # 2000 tokens
    "reviews": all_reviews,  # 5000 tokens
    "debates": all_debates  # 8000 tokens
}
```

✅ **Solution:**
```python
return {
    "hypothesis_summary": hypothesis.content[:500],  # Truncated
    "review_count": len(reviews),
    "avg_score": sum(r.score for r in reviews) / len(reviews),
    "top_3_reviews": reviews[:3]  # Only top items
}
```

#### Pitfall 2: Not Guiding LLM to Use Tools Efficiently

❌ **Problem:** LLM fetches all data anyway.

✅ **Solution:** Add explicit guidance in prompt:
```baml
prompt #"
    IMPORTANT: Fetch only the minimum data needed.
    - Start with summary tools (get_review_statistics)
    - Only use detail tools (get_hypothesis_details) if you need specific content
    - Prefer aggregate data over individual records
"#
```

#### Pitfall 3: Ambiguous Tool Descriptions

❌ **Problem:**
```python
description="Get hypothesis"  # Too vague
```

✅ **Solution:**
```python
description="""
Fetch full hypothesis details including content, Elo rating, and match history.

Use this tool when you need to:
- Compare two hypotheses
- Analyze hypothesis content
- Check Elo ratings

Do NOT use this tool for:
- Fetching reviews (use get_hypothesis_reviews)
- Finding similar hypotheses (use get_similar_hypotheses)
"""
```

### Quick Reference

See `docs/tool-development-guide.md` for comprehensive tool development documentation.

### Implementation Phases (1-22)
1. **Project Setup**: Structure and dependencies
2. **Core Models**: Task, Hypothesis, Review
3. **Task Queue**: First integrable component
4. **Context Memory**: Persistent state management
5. **Safety Framework**: Multi-layer protection
6. **LLM Abstraction**: Interface layer
7. **BAML Infrastructure**: Argo Gateway setup
8. **Supervisor Agent**: Orchestration
9. **Generation Agent**: Hypothesis creation
10. **Reflection Agent**: Review system
11. **Ranking Agent**: Tournament system
12. **Evolution Agent**: Enhancement
13. **Proximity Agent**: Clustering
14. **Meta-Review Agent**: Synthesis
15. **Natural Language Interface**: CLI
16. **Integration and Polish**: Full system
17. **Final Validation**: Complete testing

## 🚨 Critical Rules

1. **Follow specs exactly** - no deviations
2. **Integration tests start at Phase 3** (first integrable component)
3. **Every file should get smaller after iteration 10+**
4. **Use BAML for all AI interactions**
5. **Maintain ≥80% test coverage always**
6. **One atomic feature per iteration**
7. **Update IMPLEMENTATION_PLAN.md after each task**

## 📋 Working Memory

Maintain a TODO list between iterations:
```markdown
## Current TODO List
1. [ ] Current task from IMPLEMENTATION_PLAN.md
2. [ ] Files to read before modifying
3. [ ] Tests to write
4. [ ] Integration points to verify
5. [ ] Refactoring opportunities
6. [ ] Duplicate code to remove
```

Remember: The specs are your truth. Implement exactly what's specified.

## 🎯 Context Optimization Guidelines

### ACE-FCA Integration Status

The development loop has been enhanced with ACE-FCA context optimization principles:

#### Context Relevance Scoring
- **Intelligent Spec Selection**: 3-7 most relevant specifications based on current task
- **Automatic Fallback**: Full context when optimization confidence is low
- **Quality Validation**: Context selections validated against phase requirements

#### Usage
- **Automatic**: Context optimization runs automatically during development loop
- **Monitoring**: Metrics logged to `.context_optimization_metrics.log`
- **Manual Control**: Can be disabled with `.context_optimization_disabled` file

#### Quality Requirements
- **Same Standards Apply**: All existing quality gates must pass with optimized context
- **Fallback Guarantee**: System automatically uses full context if quality issues detected
- **Coverage Maintained**: ≥80% test coverage required regardless of context optimization

### Implementation Priority

Context optimization is production-ready and should be used for all development iterations.