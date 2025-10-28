#!/bin/bash
# Pre-commit hook to detect caplog assertions in test files
# These are flaky and should use functional behavior tests instead

set -e

# Find all staged test files
staged_test_files=$(git diff --cached --name-only --diff-filter=ACM | grep '^tests/.*\.py$' || true)

if [ -z "$staged_test_files" ]; then
    exit 0
fi

# Check for caplog assertion patterns
found_issues=0

for file in $staged_test_files; do
    # Look for common caplog assertion patterns
    if grep -n "assert.*caplog\.text" "$file" > /dev/null 2>&1; then
        if [ $found_issues -eq 0 ]; then
            echo "⚠️  WARNING: Flaky logging test pattern detected!"
            echo ""
            found_issues=1
        fi

        echo "File: $file"
        grep -n "assert.*caplog\.text" "$file" | while IFS=: read -r line_num line_content; do
            echo "  Line $line_num: $line_content"
        done
        echo ""
    fi
done

if [ $found_issues -eq 1 ]; then
    echo "❌ Tests using 'assert ... in caplog.text' are FLAKY and fail intermittently."
    echo ""
    echo "🔧 Solution: Test functional behavior instead of logging output."
    echo "📖 See: docs/testing-guidelines.md for patterns and examples"
    echo ""
    echo "Examples:"
    echo "  ❌ assert 'warning' in caplog.text"
    echo "  ✅ assert result == []"
    echo "  ✅ assert len(cache) == 0"
    echo "  ✅ assert has_data() is False"
    echo ""
    echo "To bypass this check (not recommended): git commit --no-verify"
    exit 1
fi

exit 0
