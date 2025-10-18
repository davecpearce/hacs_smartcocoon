#!/bin/bash

# Setup Git and GitHub CLI for devcontainer
set -e

echo "🔧 Setting up Git and GitHub CLI support..."

# Load .env file if it exists
if [ -f "/workspaces/hacs_smartcocoon/.devcontainer/.env" ]; then
    echo "📁 Loading .env file..."
    set -a  # automatically export all variables
    source /workspaces/hacs_smartcocoon/.devcontainer/.env
    set +a  # stop automatically exporting
    echo "✅ .env file loaded"
fi

# Configure Git if not already configured
if [ -z "$(git config --global user.name)" ]; then
    echo "🔧 Configuring Git..."

    # Use environment variables or defaults
    GIT_USER_NAME=${GIT_USER_NAME:-"Developer"}
    GIT_USER_EMAIL=${GIT_USER_EMAIL:-"developer@example.com"}

    git config --global user.name "$GIT_USER_NAME"
    git config --global user.email "$GIT_USER_EMAIL"
    git config --global credential.helper store
    echo "✅ Git configured (User: $GIT_USER_NAME, Email: $GIT_USER_EMAIL)"
else
    echo "✅ Git already configured"
fi

# Test GitHub CLI authentication
if command -v gh >/dev/null 2>&1; then
    echo "🔍 Checking GitHub CLI authentication..."
    if gh auth status >/dev/null 2>&1; then
        echo "✅ GitHub CLI authenticated"
    else
        echo "⚠️  GitHub CLI not authenticated - run 'gh auth login' when needed"
    fi
else
    echo "⚠️  GitHub CLI not found"
fi

echo "🎉 Git and GitHub CLI setup complete!"
echo ""
echo "📋 Available commands:"
echo "  git status                    - Check git status"
echo "  git push origin <branch>      - Push to GitHub (will prompt for token)"
echo "  gh pr create                  - Create pull request"
echo "  gh auth login                 - Authenticate with GitHub"
echo ""
echo "💡 For Git operations, you can:"
echo "  1. Use 'gh auth login' for GitHub CLI"
echo "  2. Set GITHUB_TOKEN environment variable for git push"
echo "  3. Use Personal Access Token when prompted"
echo ""
echo "🔧 To customize Git user info:"
echo "  1. Copy .devcontainer/env.example to .devcontainer/.env"
echo "  2. Edit .devcontainer/.env with your information"
echo "  3. Rebuild the devcontainer"
echo ""
