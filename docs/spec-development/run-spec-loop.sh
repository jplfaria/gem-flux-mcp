#!/bin/bash

# Color codes for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Gem-Flux MCP Server Spec Creation Loop ===${NC}"
echo -e "${YELLOW}This will run up to 10 iterations, pausing between each for review.${NC}"
echo -e "${YELLOW}Press Ctrl+C at any time to stop.${NC}\n"

# Track if we've created the plan
PLAN_CREATED=false

for i in {1..10}; do
    echo -e "\n${GREEN}=== Running spec creation iteration $i ===${NC}"

    # Run Claude and capture output
    OUTPUT=$(cat docs/spec-development/specs-prompt.md | claude -p --output-format=stream-json --dangerously-skip-permissions --verbose 2>/dev/null | jq -r .message.content)

    # Display the output
    echo "$OUTPUT"

    # Check for different completion states
    if echo "$OUTPUT" | grep -q "PLAN_CREATED"; then
        echo -e "\n${GREEN}✓ Plan has been created! Check SPECS_PLAN.md${NC}"
        PLAN_CREATED=true
        echo -e "${YELLOW}The model will now start creating individual specs on the next run.${NC}"
    elif echo "$OUTPUT" | grep -q "ALL_TASKS_COMPLETE"; then
        echo -e "\n${GREEN}✓ All tasks completed!${NC}"
        break
    fi

    # Show what was created
    echo -e "\n${YELLOW}Recent changes:${NC}"
    git status --short

    # Pause for review
    echo -e "\n${YELLOW}Press Enter to continue to next iteration, or Ctrl+C to stop...${NC}"
    read -r
done

echo -e "\n${GREEN}=== Spec creation loop finished ===${NC}"
echo -e "${YELLOW}To see all changes: git status${NC}"
echo -e "${YELLOW}To see specs created: ls -la specs/${NC}"
