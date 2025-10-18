#!/bin/bash
# Run GitHub Actions locally with act and show only test summary

set -e

echo "🚀 Running GitHub Actions locally with act (summary mode)..."
echo ""

# Check if act is available
if ! command -v act &> /dev/null; then
    echo "❌ act is not installed. Please rebuild the devcontainer."
    exit 1
fi

# Check if Docker is available
if ! docker info &> /dev/null; then
    echo "❌ Docker is not available or not running."
    echo "💡 This is expected inside a devcontainer. Use pre-commit instead:"
    echo "   pre-commit run --all-files"
    exit 1
fi

# Check if workflow file exists
WORKFLOW_FILE=".github/workflows/tests.yaml"
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ Workflow file $WORKFLOW_FILE not found!"
    exit 1
fi

echo "📋 Running test job (showing only test results)..."
echo ""

# Run the test job and filter output to show only test results
act -W "$WORKFLOW_FILE" -j test --rm --pull=false 2>/dev/null | \
    grep -E "(tests coverage|TOTAL|Coverage HTML|Required test coverage|✅|❌|Failed|Passed|Failed -|Success -)" || \
    echo "No test summary found in output"

echo ""
echo "📋 Running HACS job (showing only validation results)..."
echo ""

# Run the HACS job and filter output to show only validation results
act -W "$WORKFLOW_FILE" -j hacs --rm --pull=false 2>/dev/null | \
    grep -E "(Validation|checks passed|All.*checks passed|✅|❌|Failed|Passed|Failed -|Success -)" || \
    echo "No validation summary found in output"

echo ""
echo "✅ All CI jobs completed locally!"
echo ""
echo "💡 For full output, use: ./run-ci-local.sh"
