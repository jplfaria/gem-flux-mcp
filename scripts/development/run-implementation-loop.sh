#!/bin/bash

# run-implementation-loop-validated.sh
# Implementation loop with quality gates and validation

# Create logs directory if it doesn't exist
mkdir -p .implementation_logs

# Function to log iteration results
log_iteration_result() {
    local status=$1
    local iteration=$2
    local timestamp=$(date '+%Y-%m-%d_%H-%M-%S')
    local log_file=".implementation_logs/iteration_${iteration}_${status}_${timestamp}.log"
    
    echo "=== Iteration $iteration - Status: $status ===" > "$log_file"
    echo "Timestamp: $timestamp" >> "$log_file"
    echo "" >> "$log_file"
    
    # Capture all output from the iteration
    if [ -f ".iteration_output_${iteration}.tmp" ]; then
        cat ".iteration_output_${iteration}.tmp" >> "$log_file"
    fi
    
    # Add summary log
    echo "" >> "$log_file"
    echo "=== Summary ===" >> "$log_file"
    echo "Status: $status" >> "$log_file"
    echo "Iteration: $iteration" >> "$log_file"
    
    # If failed, capture test failures
    if [ "$status" = "failed" ] && [ -f ".test_failures_${iteration}.tmp" ]; then
        echo "" >> "$log_file"
        echo "=== Test Failures ===" >> "$log_file"
        cat ".test_failures_${iteration}.tmp" >> "$log_file"
    fi
    
    echo "" >> "$log_file"
    echo "Log saved to: $log_file"
    
    # Create a latest symlink for easy access
    ln -sf "$(basename "$log_file")" ".implementation_logs/latest_${status}.log"
    
    # Clean up temp files
    rm -f ".iteration_output_${iteration}.tmp" ".test_failures_${iteration}.tmp"
}

# Color codes for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
MAX_ITERATIONS=100
COVERAGE_THRESHOLD=80

# Function to show optimization help (defined early for help flag)
show_optimization_help() {
    echo "🔧 Context Optimization Features:"
    echo "================================="
    echo ""
    echo "Status checks:"
    echo "  check_optimization_status     - Check if optimization is enabled"
    echo "  show_optimization_report      - Show effectiveness metrics"
    echo ""
    echo "Manual controls:"
    echo "  touch .context_optimization_disabled    - Temporarily disable optimization"
    echo "  rm .context_optimization_disabled       - Re-enable optimization"
    echo ""
    echo "Log files:"
    echo "  .context_optimization_metrics.log       - Detailed usage metrics"
    echo "  optimized_prompt.md                     - Latest optimized prompt"
}

# Function to show optimization report (defined early for report flag)
show_optimization_report() {
    echo "📊 Context Optimization Report:"
    echo "=============================="

    if [ -f ".context_optimization_metrics.log" ]; then
        python3 -c "
import sys
sys.path.append('src')
try:
    from utils.optimization_analytics import ContextOptimizationAnalytics
    analytics = ContextOptimizationAnalytics()
    print(analytics.generate_report())
except ImportError:
    print('Analytics module not available - install pandas and matplotlib for detailed reports')
    print()
" 2>/dev/null || {
    echo "Basic metrics from log file:"
    tail -n 10 .context_optimization_metrics.log
}
    else
        echo "No metrics available yet. Run some iterations first."
    fi
}

# Handle command line flags
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo -e "${GREEN}=== AI Co-Scientist Implementation Loop ===${NC}"
    echo -e "${YELLOW}Usage: $0 [options]${NC}"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  --optimization-report      Show context optimization effectiveness report"
    echo ""
    show_optimization_help
    exit 0
fi

# Handle optimization report flag
if [ "$1" = "--optimization-report" ]; then
    show_optimization_report
    exit 0
fi

echo -e "${GREEN}=== AI Co-Scientist Implementation Loop (Validated) ===${NC}"
echo -e "${YELLOW}This implementation loop includes quality gates and validation.${NC}"
echo -e "${CYAN}Each iteration must pass tests and coverage checks before proceeding.${NC}"
echo -e "${YELLOW}Press Ctrl+C at any time to stop.${NC}\n"

# CRITICAL: Ensure we're using the virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Error: .venv directory not found${NC}"
    echo -e "${YELLOW}Run: uv sync${NC}"
    exit 1
fi

if [ ! -f ".venv/bin/python" ]; then
    echo -e "${RED}❌ Error: .venv/bin/python not found${NC}"
    echo -e "${YELLOW}Virtual environment appears corrupted. Run: uv sync${NC}"
    exit 1
fi

echo -e "${CYAN}✅ Using virtual environment: .venv${NC}"
echo -e "${CYAN}   Python: $(.venv/bin/python --version)${NC}"
echo -e "${CYAN}   Pytest: $(.venv/bin/pytest --version | head -1)${NC}\n"

# Function to check if pytest is available
check_pytest() {
    if [ ! -f ".venv/bin/pytest" ]; then
        echo -e "${RED}❌ pytest is not installed in .venv. Cannot proceed.${NC}"
        echo -e "${YELLOW}Run: .venv/bin/pip install pytest pytest-cov${NC}"
        return 1
    fi
    return 0
}

# Function to detect current implementation phase
detect_implementation_phase() {
    if [ ! -f "IMPLEMENTATION_PLAN.md" ]; then
        echo "0"
        return
    fi

    # Check phases in order - return the first one with uncompleted tasks
    # Use same pattern matching as extract_current_task() for consistency
    for phase_num in 1 2 3 4 5 6 7 7.5 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22; do
        pattern="## Phase $phase_num:"

        # Get the phase section content - stop at next ## Phase heading
        phase_section=$(awk -v pattern="$pattern" '
            $0 ~ pattern { found=1; print; next }
            found && /^## Phase/ { exit }
            found { print }
        ' IMPLEMENTATION_PLAN.md)

        # Check if this phase has any unchecked tasks
        if echo "$phase_section" | grep -q "^\- \[ \]"; then
            echo "$phase_num"
            return
        fi
    done

    # If we get here, all phases are complete or no phases found
    echo "22"  # Assume final phase if all complete
}

extract_current_task() {
    # Extract detailed task description for context scoring
    # Enhanced to detect section groupings and count related tasks
    echo "🔍 Extracting current task details..." >&2

    # Check phases in the same order as find_current_phase
    for phase_num in 1 2 3 4 5 6 7 7.5 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22; do
        pattern="## Phase $phase_num:"

        # Get the phase section content - stop at next ## Phase heading
        # This prevents capturing tasks from subsequent phases
        phase_content=$(awk -v pattern="$pattern" '
            $0 ~ pattern { found=1; print; next }
            found && /^## Phase/ { exit }
            found { print }
        ' IMPLEMENTATION_PLAN.md)

        if [ -z "$phase_content" ]; then
            continue
        fi

        # Find first unchecked task in this phase
        first_unchecked=$(echo "$phase_content" | grep -m1 "^\- \[ \]" | sed 's/^- \[ \] //')

        if [ ! -z "$first_unchecked" ]; then
            # Try to detect if this task is part of a section
            # Look for the most recent ### heading before this task
            # Use simpler awk with explicit found variable handling
            section_header=$(echo "$phase_content" | awk '
                /^### / {
                    current_section = $0
                    gsub(/^### /, "", current_section)
                }
                /^- \[ \]/ {
                    if (found == 0) {
                        print current_section
                        found = 1
                        exit
                    }
                }
                BEGIN { found = 0 }
            ')

            if [ ! -z "$section_header" ]; then
                # Count unchecked tasks in this section
                # Extract from section header until next ### or ## or end
                section_tasks=$(echo "$phase_content" | awk -v header="$section_header" '
                    /^### / {
                        current = $0
                        gsub(/^### /, "", current)
                        if (current == header) {
                            in_section = 1
                            next
                        } else if (in_section == 1) {
                            exit
                        }
                    }
                    /^## / && in_section == 1 {
                        exit
                    }
                    in_section == 1 && /^- \[ \]/ {
                        count++
                    }
                    END {
                        print count + 0
                    }
                    BEGIN {
                        in_section = 0
                        count = 0
                    }
                ')

                # Only use section info if we found multiple related tasks
                if [ "$section_tasks" -gt 1 ]; then
                    echo "Phase $phase_num: $section_header - $section_tasks tasks ($first_unchecked, ...)"
                    return 0
                fi
            fi

            # Fallback: just return the single task (original behavior)
            echo "Phase $phase_num: $first_unchecked"
            return 0
        fi
    done

    echo "No active task found"
    return 1
}

extract_unchecked_tasks() {
    # Extract specific unchecked tasks for Claude to mark as complete
    # This ensures Claude knows which checkboxes to update in IMPLEMENTATION_PLAN.md

    local phase_num=$1

    if [ -z "$phase_num" ]; then
        return 1
    fi

    pattern="## Phase $phase_num:"

    # Get the phase section content
    phase_content=$(awk -v pattern="$pattern" '
        $0 ~ pattern { found=1; print; next }
        found && /^## Phase/ { exit }
        found { print }
    ' IMPLEMENTATION_PLAN.md)

    if [ -z "$phase_content" ]; then
        return 1
    fi

    # Extract all unchecked tasks (up to 10 to avoid overwhelming)
    echo "$phase_content" | grep "^\- \[ \]" | head -10
}

optimize_context_selection() {
    echo "📖 Analyzing task context requirements..." >&2

    # Extract current task and phase
    CURRENT_PHASE=$(detect_implementation_phase)
    CURRENT_TASK=$(extract_current_task)

    if [ $? -ne 0 ] || [ -z "$CURRENT_TASK" ]; then
        echo "⚠️  Could not extract current task, falling back to full context" >&2
        return 1
    fi

    # Validate phase consistency - extract phase number from CURRENT_TASK
    TASK_PHASE=$(echo "$CURRENT_TASK" | grep -o "^Phase [0-9.]*" | grep -o "[0-9.]*")

    # Debug logging for phase detection (helps diagnose issues)
    echo "   Phase detection: detect_implementation_phase=$CURRENT_PHASE, extract_current_task=$TASK_PHASE" >&2

    if [ "$CURRENT_PHASE" != "$TASK_PHASE" ]; then
        echo "" >&2
        echo "❌ ERROR: Phase detection mismatch detected!" >&2
        echo "   detect_implementation_phase() returned: $CURRENT_PHASE" >&2
        echo "   extract_current_task() returned phase: $TASK_PHASE" >&2
        echo "   Task description: $CURRENT_TASK" >&2
        echo "" >&2
        echo "   This indicates a bug in phase detection logic or stale IMPLEMENTATION_PLAN.md." >&2
        echo "   Aborting iteration to prevent implementing wrong phase." >&2
        echo "" >&2
        echo "   Please verify:" >&2
        echo "   1. Run 'git diff IMPLEMENTATION_PLAN.md' to check for uncommitted changes" >&2
        echo "   2. Check that all Phase $TASK_PHASE tasks are marked [x] if phase $CURRENT_PHASE is active" >&2
        echo "   3. Report this bug with the log file to maintainers" >&2
        echo "" >&2
        return 1
    fi

    echo "✅ Phase validation passed: Phase $CURRENT_PHASE" >&2
    echo "🎯 $CURRENT_TASK" >&2

    # Save current directory and ensure we're in project root for Python imports
    ORIG_DIR=$(pwd)

    # Find the actual project root (where src/ and specs/ directories are)
    if [ -d "src" ] && [ -d "specs" ]; then
        PROJECT_ROOT=$(pwd)
    elif [ -d "../../src" ] && [ -d "../../specs" ]; then
        PROJECT_ROOT=$(cd ../.. && pwd)
    else
        # Try to find project root by looking for src directory
        PROJECT_ROOT=$(pwd)
        while [ ! -d "$PROJECT_ROOT/src" ] && [ "$PROJECT_ROOT" != "/" ]; do
            PROJECT_ROOT=$(dirname "$PROJECT_ROOT")
        done
    fi

    cd "$PROJECT_ROOT"

    # Enhanced context selection with phase awareness
    CONTEXT_RESULT=$(python3 -c "
import sys
sys.path.append('src')
from gem_flux_mcp.utils.context_relevance import SpecificationRelevanceScorer

try:
    scorer = SpecificationRelevanceScorer()

    # Analyze task context with phase awareness
    task_analysis = scorer.analyze_task_context('$CURRENT_TASK', $CURRENT_PHASE)
    print('ANALYSIS:' + str(task_analysis), file=sys.stderr)

    # Determine max_specs based on phase complexity
    # Tool implementation phases may need more specs for dependencies
    if $CURRENT_PHASE >= 5 and $CURRENT_PHASE <= 7:
        max_specs = 9  # Core tool phases: need tool spec + database + template + storage
    elif $CURRENT_PHASE >= 10:
        max_specs = 8  # Integration phases: need multiple system specs
    else:
        max_specs = 6  # Infrastructure phases: simpler, fewer dependencies

    print(f'MAX_SPECS: {max_specs} (Phase {$CURRENT_PHASE})', file=sys.stderr)

    # Select specs with enhanced analysis
    recommendation = scorer.select_optimal_specs_with_analysis('$CURRENT_TASK', task_analysis, max_specs=max_specs)

    print('SPECS:' + ' '.join(recommendation.specs))
    print('CONFIDENCE:' + str(recommendation.confidence_score))
    print('REASONING:' + recommendation.reasoning)
    print('FALLBACK:' + str(recommendation.fallback_needed))
except Exception as e:
    print('ERROR:' + str(e), file=sys.stderr)
    sys.exit(1)
")

    if [ $? -ne 0 ]; then
        echo "⚠️  Context optimization failed, falling back to full context" >&2
        return 1
    fi

    # Parse results
    SELECTED_SPECS=$(echo "$CONTEXT_RESULT" | grep "^SPECS:" | cut -d: -f2-)
    CONFIDENCE=$(echo "$CONTEXT_RESULT" | grep "^CONFIDENCE:" | cut -d: -f2)
    REASONING=$(echo "$CONTEXT_RESULT" | grep "^REASONING:" | cut -d: -f2)
    FALLBACK=$(echo "$CONTEXT_RESULT" | grep "^FALLBACK:" | cut -d: -f2)

    if [ "$FALLBACK" = "True" ]; then
        echo "⚠️  Low confidence ($CONFIDENCE), falling back to full context" >&2
        return 1
    fi

    echo "📋 Selected specs: $SELECTED_SPECS" >&2
    echo "🎯 Confidence: $CONFIDENCE" >&2
    echo "💡 Reasoning: $REASONING" >&2

    # Generate optimized prompt
    generate_optimized_prompt "$CURRENT_TASK" "$SELECTED_SPECS"

    # Return to original directory
    cd "$ORIG_DIR"
    return 0
}

generate_optimized_prompt() {
    local task="$1"
    local selected_specs="$2"

    echo "📝 Generating optimized prompt..." >&2

    # Extract phase number from task
    local phase_num=$(echo "$task" | grep -o "^Phase [0-9.]*" | grep -o "[0-9.]*")

    # Get unchecked tasks for this phase
    local unchecked_tasks=""
    if [ -n "$phase_num" ]; then
        unchecked_tasks=$(extract_unchecked_tasks "$phase_num")
    fi

    cat > optimized_prompt.md << EOF
# CogniscientAssistant Implementation Task

## Current Task Focus
$task

$(if [ -n "$unchecked_tasks" ]; then
echo "## Specific Tasks to Complete"
echo "Mark these items as [x] in IMPLEMENTATION_PLAN.md after completion:"
echo ""
echo "$unchecked_tasks"
echo ""
echo "**CRITICAL**: After completing tasks, edit IMPLEMENTATION_PLAN.md to mark completed items as [x] before committing."
echo ""
fi)
## Relevant Specifications
$(for spec in $selected_specs; do
    if [ -f "specs/$spec" ]; then
        echo "### $(basename $spec .md | sed 's/-/ /g' | sed 's/\b\w/\u&/g')"
        echo ""
        cat "specs/$spec"
        echo ""
        echo "---"
        echo ""
    fi
done)

## Implementation Guidelines
$(cat CLAUDE.md)

## Quality Requirements
- Maintain 100% test pass rate for must-pass tests
- Follow specification requirements exactly
- Implement atomic features only
- Use FastMCP for all MCP tool implementations
- Maintain ≥80% test coverage

## Context Optimization
This prompt has been optimized to include only specifications relevant to the current task.
If additional context is needed, the system will automatically fall back to full specifications.

Generated at: $(date)
Task: $task
Selected specifications: $(echo $selected_specs | wc -w) of $(ls specs/*.md | wc -l) total
EOF

    echo "✅ Optimized prompt generated: optimized_prompt.md" >&2
}

# Function to analyze test failures against expectations
analyze_test_failures() {
    local phase=$1
    local test_output_file=$2
    local expectations_file="tests/integration/test_expectations.json"
    
    # Check if expectations file exists
    if [ ! -f "$expectations_file" ]; then
        return 1  # No expectations defined, use default behavior
    fi
    
    # Extract test names and files that failed
    # Use Python for more robust parsing that handles both specific test failures
    # and file-level collection errors
    python3 << PYTHON_EOF
import re
import json

# Read test output
with open('$test_output_file', 'r') as f:
    output = f.read()

# Read expectations
with open('$expectations_file', 'r') as f:
    expectations = json.load(f)

phase_key = 'phase_$phase'
must_pass = set(expectations.get(phase_key, {}).get('must_pass', []))

# Collect may_fail from ALL phases, not just current phase
# This is needed because we run all integration tests, not just current phase tests
may_fail = set()
for phase_data in expectations.values():
    if isinstance(phase_data, dict) and 'may_fail' in phase_data:
        may_fail.update(phase_data['may_fail'])

# Extract failed tests (both specific test names and file-level errors)
failed_items = set()

# Pattern 1: FAILED tests/path/test_file.py::test_name
for match in re.finditer(r'FAILED tests/[^/]+/(test_\w+\.py)::(test_\w+)', output):
    test_file = match.group(1).replace('.py', '')
    test_name = match.group(2)
    # Add both the specific test name and file prefix for matching
    failed_items.add(test_name)
    failed_items.add(test_file)

# Pattern 2: ERROR collecting tests/path/test_file.py
for match in re.finditer(r'ERROR collecting tests/[^/]+/(test_\w+\.py)', output):
    test_file = match.group(1).replace('.py', '')
    failed_items.add(test_file)

# Check if any failed items match must_pass tests
critical_failures = []
for item in failed_items:
    # Check exact match or if item is prefix of must_pass test
    for must_pass_test in must_pass:
        if item == must_pass_test or must_pass_test.startswith(item + '_'):
            critical_failures.append(item)
            break

if critical_failures:
    print("CRITICAL")
    for item in critical_failures:
        print(item)
else:
    # Check if any failed items are NOT in may_fail list
    # For file-level errors (e.g., test_cli_auth), check if ANY test from may_fail
    # could come from that file (e.g., test_cli_authentication_flow)
    unexpected_failures = []
    for item in failed_items:
        # Check if item matches any may_fail test
        is_expected = False
        for may_fail_test in may_fail:
            # Match if:
            # 1. Exact match: item == may_fail_test
            # 2. File prefix match: may_fail_test starts with item (e.g., test_cli_auth -> test_cli_authentication_flow)
            # 3. Reverse match: item starts with may_fail_test (for cases where test name is prefix of file)
            if (item == may_fail_test or
                may_fail_test.startswith(item) or
                item.startswith(may_fail_test)):
                is_expected = True
                break

        if not is_expected:
            unexpected_failures.append(item)

    if unexpected_failures:
        print("UNEXPECTED")
        for item in unexpected_failures:
            print(item)
    else:
        print("EXPECTED")
        for item in failed_items:
            print(item)
PYTHON_EOF
}

# Function to run phase-specific integration tests
run_phase_integration_tests() {
    local current_phase=$(detect_implementation_phase)
    
    echo -e "\n${BLUE}=== Phase Integration Testing ===${NC}"
    
    # Only run integration tests if we have completed phases
    if [ "$current_phase" -ge "3" ] && [ -d "tests/integration" ]; then
        # Find integration test files for current or previous phases
        local test_files=""
        for phase in $(seq 3 $current_phase); do
            if ls tests/integration/test_phase${phase}_*.py 2>/dev/null | grep -q .; then
                test_files="$test_files tests/integration/test_phase${phase}_*.py"
            fi
        done
        
        if [ -n "$test_files" ]; then
            echo -e "${CYAN}Running integration tests for completed phases...${NC}"
            echo -e "${CYAN}Current implementation phase: $current_phase${NC}"
            
            # Save test output to analyze failures
            INTEGRATION_TEST_OUTPUT=".integration-test-output-$$.tmp"
            
            # Run the integration tests and capture output
            if .venv/bin/pytest $test_files -v --tb=short 2>&1 | tee "$INTEGRATION_TEST_OUTPUT"; then
                echo -e "${GREEN}✅ Integration tests passed${NC}"
                # Save success state
                echo "LAST_INTEGRATION_STATUS=passed" > .integration_test_state
                echo "LAST_PASSING_PHASE=$current_phase" >> .integration_test_state
                echo "LAST_PASSING_TIMESTAMP=$(date -Iseconds)" >> .integration_test_state
            else
                # Analyze the failure type
                local skip_count=$(grep -c "SKIPPED" "$INTEGRATION_TEST_OUTPUT" || echo "0")
                local xfail_count=$(grep -c "XFAIL" "$INTEGRATION_TEST_OUTPUT" || echo "0")
                local fail_count=$(grep -c "FAILED" "$INTEGRATION_TEST_OUTPUT" || echo "0")
                local error_count=$(grep -c "ERROR" "$INTEGRATION_TEST_OUTPUT" || echo "0")
                
                # Check if this test file has run before for this phase
                local test_history_file=".integration_test_history_phase${current_phase}"
                local is_first_run=true
                if [ -f "$test_history_file" ]; then
                    is_first_run=false
                fi
                
                # Analyze failures against expectations
                local failure_analysis=$(analyze_test_failures "$current_phase" "$INTEGRATION_TEST_OUTPUT")
                local failure_type=$(echo "$failure_analysis" | head -1)
                local failed_test_names=$(echo "$failure_analysis" | tail -n +2)
                
                # Check if this is a regression
                if [ -f ".integration_test_state" ] && grep -q "LAST_INTEGRATION_STATUS=passed" .integration_test_state; then
                    echo -e "${RED}❌ REGRESSION DETECTED: Integration tests that were passing now fail!${NC}"
                    echo -e "${YELLOW}This indicates broken functionality in completed components.${NC}"
                    echo -e "${CYAN}This needs immediate attention before proceeding.${NC}"
                    
                    # Set regression flag for Claude to see
                    echo "INTEGRATION_REGRESSION=true" > .implementation_flags
                    echo "REGRESSION_DETECTED_AT=$(date -Iseconds)" >> .implementation_flags
                    echo "REGRESSION_PHASE=$current_phase" >> .implementation_flags
                # Check if critical tests failed (must_pass tests)
                elif [ "$failure_type" = "CRITICAL" ]; then
                    echo -e "${RED}❌ CRITICAL TEST FAILURE: Required tests for Phase $current_phase failed!${NC}"
                    echo -e "${YELLOW}Failed critical tests:${NC}$failed_test_names"
                    echo -e "${CYAN}These tests MUST pass according to test_expectations.json${NC}"
                    echo -e "${CYAN}Fix the implementation to make these tests pass before proceeding.${NC}"
                    
                    # Set implementation error flag
                    echo "IMPLEMENTATION_ERROR=true" > .implementation_flags
                    echo "ERROR_DETECTED_AT=$(date -Iseconds)" >> .implementation_flags
                    echo "ERROR_PHASE=$current_phase" >> .implementation_flags
                    echo "CRITICAL_TESTS_FAILED=$failed_test_names" >> .implementation_flags
                    
                    # Clean up and exit to force fix
                    rm -f "$INTEGRATION_TEST_OUTPUT"
                    return 2  # Special return code for implementation error
                # Check for unexpected failures
                elif [ "$failure_type" = "UNEXPECTED" ] && [ "$is_first_run" = true ]; then
                    echo -e "${RED}❌ UNEXPECTED TEST FAILURE: Tests not in may_fail list failed!${NC}"
                    echo -e "${YELLOW}Unexpected failures:${NC}$failed_test_names"
                    echo -e "${CYAN}Either fix the implementation or update test_expectations.json${NC}"
                    
                    # Set implementation error flag
                    echo "IMPLEMENTATION_ERROR=true" > .implementation_flags
                    echo "ERROR_DETECTED_AT=$(date -Iseconds)" >> .implementation_flags
                    echo "ERROR_PHASE=$current_phase" >> .implementation_flags
                    echo "UNEXPECTED_TESTS_FAILED=$failed_test_names" >> .implementation_flags
                    
                    # Clean up and exit to force fix
                    rm -f "$INTEGRATION_TEST_OUTPUT"
                    return 2  # Special return code for implementation error
                else
                    # Expected failures or informational
                    if [ "$failure_type" = "EXPECTED" ]; then
                        echo -e "${YELLOW}⚠️  Integration tests failed (expected - in may_fail list)${NC}"
                        echo -e "${CYAN}Failed tests that are allowed to fail:${NC}$failed_test_names"
                    else
                        echo -e "${YELLOW}⚠️  Integration tests failed (informational)${NC}"
                    fi
                    echo -e "${CYAN}This helps identify integration issues early${NC}"
                    echo -e "${CYAN}These failures are non-blocking${NC}"
                    if [ "$skip_count" -gt 0 ]; then
                        echo -e "${CYAN}Skipped tests: $skip_count (expected - waiting for future components)${NC}"
                    fi
                    if [ "$xfail_count" -gt 0 ]; then
                        echo -e "${CYAN}Expected failures: $xfail_count${NC}"
                    fi
                fi
                
                # Mark that we've run tests for this phase
                echo "FIRST_RUN_AT=$(date -Iseconds)" > "$test_history_file"
                
                # Save failure state
                echo "LAST_INTEGRATION_STATUS=failed" > .integration_test_state
                echo "LAST_FAILING_PHASE=$current_phase" >> .integration_test_state
                echo "LAST_FAILING_TIMESTAMP=$(date -Iseconds)" >> .integration_test_state
            fi
            
            # Clean up temp file
            rm -f "$INTEGRATION_TEST_OUTPUT"
        else
            echo -e "${CYAN}No integration tests available for phase $current_phase yet${NC}"
        fi
    else
        echo -e "${CYAN}Skipping integration tests - implementation not at testable phase yet${NC}"
    fi
}

# Function to validate context optimization effectiveness
validate_context_optimization() {
    echo "🔍 Validating context optimization effectiveness..." >&2

    if [ ! -f "optimized_prompt.md" ]; then
        echo "✅ No context optimization used this iteration" >&2
        return 0
    fi

    # Check if optimization maintained quality
    CURRENT_PHASE=$(detect_implementation_phase)
    CURRENT_TASK=$(extract_current_task)

    python3 -c "
import sys
sys.path.append('src')
from gem_flux_mcp.utils.context_relevance import SpecificationRelevanceScorer

scorer = SpecificationRelevanceScorer()
selected_specs = []

# Extract selected specs from optimized prompt
with open('optimized_prompt.md', 'r') as f:
    content = f.read()

# Simple extraction - find spec patterns
import re
spec_matches = re.findall(r'### ([0-9]+[^\\n]*)', content)
selected_specs = [match.lower().replace(' ', '-') + '.md' for match in spec_matches]

validation = scorer.validate_context_selection('$CURRENT_TASK', selected_specs, $CURRENT_PHASE)

if not validation['is_valid']:
    print('VALIDATION_FAILED')
    for issue in validation['critical_issues']:
        print('Critical:', issue)
    sys.exit(1)
elif validation['warnings']:
    print('VALIDATION_WARNINGS')
    for warning in validation['warnings']:
        print('Warning:', warning)
else:
    print('VALIDATION_PASSED')
"

    VALIDATION_RESULT=$?

    if [ $VALIDATION_RESULT -ne 0 ]; then
        echo "❌ Context optimization validation failed" >&2
        echo "📋 Recommendation: Use full context for next iteration" >&2

        # Create flag to disable optimization temporarily
        touch .context_optimization_disabled
        return 1
    fi

    echo "✅ Context optimization validation passed" >&2
    return 0
}

# Function to run quality gates
run_quality_gates() {
    local iteration=$1
    echo -e "\n${BLUE}=== Running Quality Gates ===${NC}"

    # Only run if we have Python files to test
    if [ -d "src" ] && find src -name "*.py" -type f | grep -q .; then
        # 1. Run tests
        echo -e "${YELLOW}Running tests...${NC}"
        .venv/bin/pytest tests/ --tb=short -q 2>&1 | tee ".test_output_${iteration}.tmp"
        test_exit_status=${PIPESTATUS[0]}

        if [ $test_exit_status -eq 0 ]; then
            echo -e "${GREEN}✅ All tests passed${NC}"
        else
            # Analyze test failures against test_expectations.json
            local current_phase=$(detect_implementation_phase)
            local failure_analysis=$(analyze_test_failures "$current_phase" ".test_output_${iteration}.tmp")
            local failure_type=$(echo "$failure_analysis" | head -1)
            local failed_test_names=$(echo "$failure_analysis" | tail -n +2)

            if [ "$failure_type" = "CRITICAL" ]; then
                echo -e "${RED}❌ CRITICAL TEST FAILURE: Required tests failed!${NC}"
                echo -e "${YELLOW}Failed critical tests:${NC}$failed_test_names"
                echo -e "${CYAN}These tests MUST pass according to test_expectations.json${NC}"
                # Extract test failures for the log
                grep -E "FAILED|ERROR" ".test_output_${iteration}.tmp" > ".test_failures_${iteration}.tmp" 2>/dev/null || true
                rm -f ".test_output_${iteration}.tmp"
                return 1
            elif [ "$failure_type" = "UNEXPECTED" ]; then
                echo -e "${RED}❌ UNEXPECTED TEST FAILURE: Tests not in may_fail list failed!${NC}"
                echo -e "${YELLOW}Unexpected failures:${NC}$failed_test_names"
                echo -e "${CYAN}Either fix the implementation or update test_expectations.json${NC}"
                # Extract test failures for the log
                grep -E "FAILED|ERROR" ".test_output_${iteration}.tmp" > ".test_failures_${iteration}.tmp" 2>/dev/null || true
                rm -f ".test_output_${iteration}.tmp"
                return 1
            else
                # Expected failures (in may_fail list)
                echo -e "${YELLOW}⚠️  Some tests failed (expected - in may_fail list)${NC}"
                echo -e "${CYAN}Failed tests that are allowed to fail:${NC}$failed_test_names"
                echo -e "${GREEN}✅ All required tests passed${NC}"
                # These are non-blocking, so we continue
            fi
        fi
        
        # 2. Check coverage (Unit tests only for threshold)
        echo -e "\n${YELLOW}Checking unit test coverage...${NC}"
        echo -e "${CYAN}Note: 80% coverage threshold applies to unit tests only${NC}"
        
        # Run unit tests with coverage threshold
        unit_coverage_output=$(.venv/bin/pytest tests/unit/ --cov=src --cov-report=term-missing --cov-fail-under=$COVERAGE_THRESHOLD 2>&1)
        unit_coverage_status=$?
        
        echo "$unit_coverage_output" | tail -20  # Show last 20 lines of coverage report
        
        if [ $unit_coverage_status -eq 0 ]; then
            echo -e "${GREEN}✅ Unit test coverage meets ${COVERAGE_THRESHOLD}% threshold${NC}"
        else
            echo -e "${RED}❌ Unit test coverage below ${COVERAGE_THRESHOLD}% threshold!${NC}"
            echo -e "${YELLOW}Improve unit test coverage before continuing.${NC}"
            return 1
        fi
        
        # Run integration test coverage (informational only)
        if [ -d "tests/integration" ] && ls tests/integration/test_*.py 2>/dev/null | grep -q .; then
            echo -e "\n${YELLOW}Running integration test coverage (informational)...${NC}"
            integration_coverage_output=$(.venv/bin/pytest tests/integration/ --cov=src --cov-report=term-missing 2>&1)
            echo "$integration_coverage_output" | tail -15  # Show coverage summary
            echo -e "${CYAN}Integration test coverage is informational only (no threshold)${NC}"
        fi
        
        # 3. Type checking (if mypy configured)
        if command -v mypy &> /dev/null && [ -f "mypy.ini" ]; then
            echo -e "\n${YELLOW}Running type checks...${NC}"
            if mypy src/; then
                echo -e "${GREEN}✅ Type checks passed${NC}"
            else
                echo -e "${YELLOW}⚠️  Type errors detected (non-blocking)${NC}"
            fi
        fi
        
        # 4. Linting (if ruff configured)
        if command -v ruff &> /dev/null && [ -f ".ruff.toml" ]; then
            echo -e "\n${YELLOW}Running linter...${NC}"
            if ruff check src/ tests/; then
                echo -e "${GREEN}✅ Linting passed${NC}"
            else
                echo -e "${YELLOW}⚠️  Linting issues detected (non-blocking)${NC}"
            fi
        fi
        
        # 5. Run phase-specific integration tests
        run_phase_integration_tests
        local integration_result=$?

        # Check if integration tests found implementation errors
        if [ $integration_result -eq 2 ]; then
            echo -e "\n${RED}❌ Implementation error detected in integration tests!${NC}"
            echo -e "${YELLOW}The implementation doesn't match the specifications.${NC}"
            echo -e "${CYAN}Fix the implementation to match the expected behavior before continuing.${NC}"
            return 1  # Fail quality gates to stop the loop
        fi

        # 6. Validate context optimization if used
        validate_context_optimization
        if [ $? -ne 0 ]; then
            echo -e "\n${RED}❌ Context optimization validation failed!${NC}"
            echo -e "${YELLOW}Context selection doesn't meet quality requirements.${NC}"
            return 1
        fi
    else
        echo -e "${CYAN}No Python files to test yet - skipping quality gates${NC}"
    fi

    echo "✅ All quality gates passed"
    return 0
}

# Function to check optimization status
check_optimization_status() {
    # Check if context optimization is temporarily disabled
    if [ -f ".context_optimization_disabled" ]; then
        # Get file modification time based on OS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS uses stat -f %m
            local disable_time=$(stat -f %m .context_optimization_disabled 2>/dev/null || echo 0)
        else
            # Linux uses stat -c %Y
            local disable_time=$(stat -c %Y .context_optimization_disabled 2>/dev/null || echo 0)
        fi
        local current_time=$(date +%s)
        local time_diff=$((current_time - disable_time))

        # Re-enable after 30 minutes
        if [ $time_diff -gt 1800 ]; then  # 30 minutes
            echo "⏰ Re-enabling context optimization after cool-down period" >&2
            rm -f .context_optimization_disabled
            return 0
        else
            echo "❄️  Context optimization disabled for $((1800 - time_diff)) more seconds" >&2
            return 1
        fi
    fi

    return 0
}

# Function to log context optimization metrics
log_context_optimization_metrics() {
    local prompt_file="$1"
    local iteration="$2"

    # Create metrics log if it doesn't exist
    if [ ! -f ".context_optimization_metrics.log" ]; then
        echo "timestamp,iteration,prompt_file,line_count,spec_count,task_phase,optimization_used" > .context_optimization_metrics.log
    fi

    local line_count=$(wc -l < "$prompt_file")
    local spec_count=$(grep -c "^### " "$prompt_file" 2>/dev/null || echo 0)
    local current_phase=$(detect_implementation_phase)
    local optimization_used=$([[ "$prompt_file" == "optimized_prompt.md" ]] && echo "true" || echo "false")

    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),$iteration,$prompt_file,$line_count,$spec_count,$current_phase,$optimization_used" >> .context_optimization_metrics.log

    # Show metrics summary every 5 iterations
    if [ $((iteration % 5)) -eq 0 ]; then
        echo "📊 Context Optimization Metrics (last 5 iterations):" >&2
        tail -n 5 .context_optimization_metrics.log | while IFS=',' read -r timestamp iter_num file lines specs phase opt_used; do
            echo "  Iteration $iter_num: $lines lines, $specs specs, optimization=$opt_used" >&2
        done
    fi
}


# Track iterations
ITERATION=0

# Main loop
while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    ITERATION=$((ITERATION + 1))
    
    echo -e "\n${GREEN}=== Running implementation iteration $ITERATION ===${NC}"
    
    # Start capturing all output for this iteration
    exec 3>&1 4>&2
    exec 1> >(tee -a ".iteration_output_${ITERATION}.tmp")
    exec 2>&1
    
    echo -e "${BLUE}--- Claude is implementing... ---${NC}\n"
    
    # Create temporary file for output
    TEMP_OUTPUT=".claude-implementation-output-$$.tmp"
    
    echo "🚀 Starting iteration $ITERATION with context optimization..."

    # Check optimization status
    OPTIMIZATION_ENABLED=false
    if check_optimization_status; then
        OPTIMIZATION_ENABLED=true
    fi

    # Attempt context optimization if enabled
    PROMPT_FILE="prompt.md"
    if [ "$OPTIMIZATION_ENABLED" = true ] && optimize_context_selection; then
        PROMPT_FILE="optimized_prompt.md"

        # Calculate reduction based on what full context would be
        optimized_lines=$(wc -l < optimized_prompt.md)

        # Estimate full context size (CLAUDE.md + all specs + overhead)
        if [ -f "CLAUDE.md" ]; then
            claude_lines=$(wc -l < CLAUDE.md)
        else
            claude_lines=300  # fallback estimate
        fi

        total_specs=$(find specs/ -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
        estimated_full_lines=$((claude_lines + total_specs * 200 + 100))  # rough estimate

        if [ $estimated_full_lines -gt 0 ]; then
            reduction_percent=$(( (estimated_full_lines - optimized_lines) * 100 / estimated_full_lines ))
            echo "✅ Using optimized context: $optimized_lines lines (${reduction_percent}% reduction from estimated $estimated_full_lines lines)"
        else
            echo "✅ Using optimized context: $optimized_lines lines"
        fi
    else
        echo "⚠️  Using full context as fallback"
        # prompt.md should exist as a static file (not generated)
        if [ ! -f "prompt.md" ]; then
            echo "❌ Error: prompt.md not found. This should be a static file in the repo."
            echo "   Create it following the pattern from specs-prompt.md"
            exit 1
        fi
    fi

    # Log metrics
    log_context_optimization_metrics "$PROMPT_FILE" "$ITERATION"

    echo "🤖 Invoking Claude with implementation prompt..."
    claude -p --dangerously-skip-permissions "$(cat "$PROMPT_FILE")" 2>&1 | tee "$TEMP_OUTPUT"
    
    echo -e "\n${MAGENTA}--- End of Claude's implementation ---${NC}"
    
    # Check if implementation is complete
    if grep -q "Implementation complete\|All components implemented\|No more implementation tasks" "$TEMP_OUTPUT" 2>/dev/null; then
        echo -e "\n${GREEN}✅ Implementation complete!${NC}"
        echo -e "${GREEN}Total iterations: $ITERATION${NC}"
        rm -f "$TEMP_OUTPUT"
        break
    fi
    
    # Check IMPLEMENTATION_PLAN.md for progress
    if [ -f "IMPLEMENTATION_PLAN.md" ]; then
        UNCHECKED_COUNT=$(grep -E "^\- \[ \]" IMPLEMENTATION_PLAN.md 2>/dev/null | wc -l | tr -d ' ')
        
        if [ "$UNCHECKED_COUNT" -eq 0 ] && [ "$(cat IMPLEMENTATION_PLAN.md)" != "Nothing here yet" ]; then
            echo -e "\n${GREEN}✅ All implementation tasks completed!${NC}"
            echo -e "${GREEN}Total iterations: $ITERATION${NC}"
            rm -f "$TEMP_OUTPUT"
            break
        fi
    fi
    
    # Show what was created/modified
    echo -e "\n${YELLOW}Recent changes:${NC}"
    git status --short | head -10
    
    # Show implementation progress
    echo -e "\n${YELLOW}Implementation progress:${NC}"
    if [ -f "IMPLEMENTATION_PLAN.md" ] && [ "$(cat IMPLEMENTATION_PLAN.md)" != "Nothing here yet" ]; then
        echo -e "${CYAN}Recently completed:${NC}"
        grep -E "^\- \[x\]" IMPLEMENTATION_PLAN.md 2>/dev/null | tail -5 || echo "None yet"
        
        echo -e "\n${CYAN}Next tasks:${NC}"
        grep -E "^\- \[ \]" IMPLEMENTATION_PLAN.md 2>/dev/null | head -5 || echo "None"
    fi
    
    # Run quality gates
    if ! run_quality_gates $ITERATION; then
        echo -e "\n${RED}⚠️  Quality gates failed!${NC}"
        echo -e "${YELLOW}Please fix the issues above before continuing.${NC}"
        echo -e "${CYAN}The implementation has been paused.${NC}"
        
        # Restore original stdout/stderr
        exec 1>&3 2>&4
        exec 3>&- 4>&-
        
        # Log failed iteration
        log_iteration_result "failed" "$ITERATION"
        
        # Show helpful commands
        echo -e "\n${YELLOW}Helpful commands:${NC}"
        echo -e "  ${CYAN}Run tests:${NC} pytest tests/ -v"
        echo -e "  ${CYAN}Check coverage:${NC} pytest --cov=src --cov-report=term-missing"
        echo -e "  ${CYAN}Type check:${NC} mypy src/"
        echo -e "  ${CYAN}Lint:${NC} ruff check src/ tests/"
        echo -e "  ${CYAN}Integration tests:${NC} pytest tests/integration/ -v"
        
        rm -f "$TEMP_OUTPUT"
        exit 1
    fi
    
    # Show latest commits
    echo -e "\n${YELLOW}Recent commits:${NC}"
    git log --oneline -5
    
    # Cleanup temp file
    rm -f "$TEMP_OUTPUT"
    
    # Pause for review
    echo -e "\n${GREEN}✅ Quality gates passed!${NC}"
    
    # Restore original stdout/stderr
    exec 1>&3 2>&4
    exec 3>&- 4>&-
    
    # Log successful iteration
    log_iteration_result "success" "$ITERATION"
    
    echo -e "${CYAN}Press Enter to continue to next iteration, or Ctrl+C to stop...${NC}"
    read -r
done

if [ $ITERATION -eq $MAX_ITERATIONS ]; then
    echo -e "\n${RED}⚠️  Reached maximum iterations ($MAX_ITERATIONS). Stopping to prevent infinite loop.${NC}"
fi

# Final summary
echo -e "\n${GREEN}=== Implementation Summary ===${NC}"
echo -e "${YELLOW}Total iterations:${NC} $ITERATION"

if [ -d "src" ]; then
    echo -e "${YELLOW}Python files created:${NC} $(find src -name "*.py" -type f 2>/dev/null | wc -l | tr -d ' ')"
fi

if [ -d "tests" ]; then
    echo -e "${YELLOW}Test files created:${NC} $(find tests -name "*.py" -type f 2>/dev/null | wc -l | tr -d ' ')"
fi

if [ -f "IMPLEMENTATION_PLAN.md" ]; then
    COMPLETED=$(grep -E "^\- \[x\]" IMPLEMENTATION_PLAN.md 2>/dev/null | wc -l | tr -d ' ')
    REMAINING=$(grep -E "^\- \[ \]" IMPLEMENTATION_PLAN.md 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${YELLOW}Tasks completed:${NC} $COMPLETED"
    echo -e "${YELLOW}Tasks remaining:${NC} $REMAINING"
fi

# Run final quality check
if [ -d "src" ] && find src -name "*.py" -type f | grep -q .; then
    echo -e "\n${BLUE}=== Final Quality Report ===${NC}"
    echo -e "${YELLOW}Unit Test Coverage:${NC}"
    .venv/bin/pytest tests/unit/ --cov=src --cov-report=term-missing --tb=short -q

    if [ -d "tests/integration" ] && ls tests/integration/test_*.py 2>/dev/null | grep -q .; then
        echo -e "\n${YELLOW}Integration Test Coverage:${NC}"
        .venv/bin/pytest tests/integration/ --cov=src --cov-report=term-missing --tb=short -q
    fi
fi

# Check for available real LLM tests
REAL_LLM_COUNT=$(find tests/integration -name "*_real.py" -type f 2>/dev/null | wc -l | tr -d ' ')
if [ "$REAL_LLM_COUNT" -gt 0 ]; then
    echo -e "\n${BLUE}💡 Real LLM Tests Available${NC}"
    echo -e "${YELLOW}Found $REAL_LLM_COUNT real LLM test files${NC}"
    echo -e "Run with: ${CYAN}pytest tests/integration/*_real.py -v --real-llm${NC}"
    
    # Get current phase
    CURRENT_PHASE=$(detect_implementation_phase)
    if [ -n "$CURRENT_PHASE" ]; then
        echo -e "For current phase: ${CYAN}pytest tests/integration/test_phase${CURRENT_PHASE}_*_real.py -v --real-llm${NC}"
    fi
fi

echo -e "\n${GREEN}✨ Implementation loop completed!${NC}"

# Create summary log
if [ -d ".implementation_logs" ]; then
    summary_file=".implementation_logs/session_summary_$(date '+%Y-%m-%d_%H-%M-%S').log"
    echo "=== Implementation Session Summary ===" > "$summary_file"
    echo "Total iterations: $ITERATION" >> "$summary_file"
    echo "" >> "$summary_file"
    echo "Logs created:" >> "$summary_file"
    ls -la .implementation_logs/iteration_*.log >> "$summary_file" 2>/dev/null || true
    echo "" >> "$summary_file"
    echo "Session summary saved to: $summary_file"
fi