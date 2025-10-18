#!/bin/bash
# Run this script from your host machine (outside the devcontainer)
# to test GitHub Actions locally with act

set -e

echo "🚀 Running GitHub Actions locally with act (from host machine)..."
echo ""

# Check if we're in the right directory
if [ ! -f ".github/workflows/tests.yaml" ]; then
    echo "❌ Please run this script from the project root directory"
    echo "   (where .github/workflows/tests.yaml exists)"
    exit 1
fi

# Check if act is available
if ! command -v act &> /dev/null; then
    echo "❌ act is not installed on your host machine."
    echo "   Install it with: https://github.com/nektos/act#installation"
    exit 1
fi

# Check if Docker is available
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running on your host machine."
    echo "   Please start Docker and try again."
    exit 1
fi

echo "✅ Docker and act are available!"
echo ""

# List available jobs
echo "📋 Available jobs:"
act -W .github/workflows/tests.yaml -l
echo ""

# Run the test job
echo "📋 Running test job..."
act -W .github/workflows/tests.yaml -j test --rm --pull=false

echo ""
echo "📋 Running HACS job..."
act -W .github/workflows/tests.yaml -j hacs --rm --pull=false

echo ""
echo "✅ All CI jobs completed locally!"
echo ""
echo "💡 Tips:"
echo "   - Use 'act -W .github/workflows/tests.yaml -l' to list available jobs"
echo "   - Use 'act -W .github/workflows/tests.yaml -j test --dry-run' to see what would run"
echo "   - Use 'act --secret-file .env' to use secrets from .env file"


