#!/bin/bash
# Update pre-commit hooks to latest versions

echo "🔄 Updating pre-commit hooks to latest versions..."

# Update pre-commit hooks
pre-commit autoupdate

echo "✅ Pre-commit hooks updated!"
echo ""
echo "📋 Changes made:"
git diff .pre-commit-config.yaml

echo ""
echo "🧪 Testing updated hooks..."
pre-commit run --all-files

echo ""
echo "💡 If tests pass, commit the changes:"
echo "   git add .pre-commit-config.yaml"
echo "   git commit -m 'Update pre-commit hooks to latest versions'"
