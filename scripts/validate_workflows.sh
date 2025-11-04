#!/bin/bash

# Validate GitHub Actions Workflows
# This script checks workflow files for common issues

set -e

echo "🔍 Validating GitHub Actions workflows..."

WORKFLOWS_DIR=".github/workflows"
ERRORS=0

# Check if workflows directory exists
if [ ! -d "$WORKFLOWS_DIR" ]; then
    echo "❌ Error: Workflows directory not found: $WORKFLOWS_DIR"
    exit 1
fi

echo "✅ Workflows directory found"

# Count workflow files
WORKFLOW_COUNT=$(find "$WORKFLOWS_DIR" -name "*.yml" -type f | wc -l | tr -d ' ')
echo "📄 Found $WORKFLOW_COUNT workflow files"

# Validate each workflow file
for workflow in "$WORKFLOWS_DIR"/*.yml; do
    echo ""
    echo "Checking: $(basename "$workflow")"

    # Check if file is readable
    if [ ! -r "$workflow" ]; then
        echo "  ❌ File not readable"
        ((ERRORS++))
        continue
    fi

    # Check for basic YAML syntax (requires Python)
    if command -v python3 &> /dev/null; then
        python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✅ Valid YAML syntax"
        else
            echo "  ❌ Invalid YAML syntax"
            ((ERRORS++))
        fi
    fi

    # Check for required fields
    grep -q "^name:" "$workflow"
    if [ $? -eq 0 ]; then
        echo "  ✅ Has 'name' field"
    else
        echo "  ⚠️  Missing 'name' field"
    fi

    grep -q "^on:" "$workflow"
    if [ $? -eq 0 ]; then
        echo "  ✅ Has 'on' trigger definition"
    else
        echo "  ❌ Missing 'on' trigger definition"
        ((ERRORS++))
    fi

    grep -q "^jobs:" "$workflow"
    if [ $? -eq 0 ]; then
        echo "  ✅ Has 'jobs' definition"
    else
        echo "  ❌ Missing 'jobs' definition"
        ((ERRORS++))
    fi

    # Check for UV setup action
    if grep -q "astral-sh/setup-uv@v3" "$workflow"; then
        echo "  ✅ Uses UV setup action"
    fi

    # Check for Python 3.11 requirement
    if grep -q "3.11" "$workflow"; then
        echo "  ✅ Specifies Python 3.11"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ]; then
    echo "✅ All workflows validated successfully"
    echo "📊 Summary: $WORKFLOW_COUNT workflow files checked"
    exit 0
else
    echo "❌ Found $ERRORS error(s) in workflows"
    exit 1
fi
