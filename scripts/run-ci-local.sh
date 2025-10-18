#!/bin/bash
# Run GitHub Actions locally using act

set -e

echo "🚀 Running GitHub Actions locally with act..."
echo ""

# Check if act is available
if ! command -v act &> /dev/null; then
    echo "❌ act is not installed. Please rebuild the devcontainer."
    exit 1
fi

# Check if Docker is available
if ! docker info &> /dev/null; then
    echo "❌ Docker is not available or not running."
    echo ""
    echo "💡 To run act locally, you have several options:"
    echo ""
    echo "1. 🔄 Rebuild devcontainer with Docker support:"
    echo "   - The devcontainer.json has been updated to mount Docker socket"
    echo "   - Rebuild the devcontainer: Ctrl+Shift+P -> 'Dev Containers: Rebuild Container'"
    echo "   - Then run this script again"
    echo ""
    echo "2. 🖥️  Run from host machine:"
    echo "   - Use: ./run-act-host.sh (from your host machine)"
    echo ""
    echo "3. 🧪 Use pre-commit for local testing:"
    echo "   - pre-commit run --all-files"
    echo "   - This runs the same checks as CI"
    echo ""
    echo "4. 🔧 Run individual checks:"
    echo "   - python -m pytest tests/"
    echo "   - python -m mypy custom_components/smartcocoon/"
    echo "   - python -m black --check custom_components/ tests/"
    echo "   - python -m isort --check-only custom_components/ tests/"
    exit 1
fi

# Check if workflow file exists
WORKFLOW_FILE=".github/workflows/tests.yaml"
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ Workflow file $WORKFLOW_FILE not found!"
    exit 1
fi

# Run the test job
echo "📋 Running test job..."
act -W "$WORKFLOW_FILE" -j test --rm --pull=false

echo ""
echo "📋 Running HACS job..."
act -W "$WORKFLOW_FILE" -j hacs --rm --pull=false

echo ""
echo "✅ All CI jobs completed locally!"
echo ""
echo "💡 Tips:"
echo "   - Use 'act -W $WORKFLOW_FILE -l' to list available jobs"
echo "   - Use 'act -W $WORKFLOW_FILE -j test --dry-run' to see what would run"
echo "   - Use 'act --secret-file .env' to use secrets from .env file"
