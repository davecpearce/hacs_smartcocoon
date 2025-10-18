# DevContainer Setup

This devcontainer provides a complete development environment for the SmartCocoon Home Assistant integration.

## 🚀 Quick Start

1. **Open in VS Code** with the Dev Containers extension
2. **Wait for container to build** (first time only)
3. **Start developing!** Everything is pre-configured

## 🔧 Git Configuration (Optional)

To customize Git user information:

1. **Copy the example file:**
   ```bash
   cp .devcontainer/env.example .devcontainer/.env
   ```

2. **Edit `.devcontainer/.env`** with your information:
   ```bash
   GIT_USER_NAME=Your Name
   GIT_USER_EMAIL=your.email@example.com
   GITHUB_TOKEN=ghp_your_token_here
   ```

3. **Rebuild the devcontainer** to apply changes

## 📋 What's Included

- ✅ **Python 3.13.2** with Home Assistant core
- ✅ **Git & GitHub CLI** for version control
- ✅ **All dependencies** pre-installed
- ✅ **VS Code extensions** configured
- ✅ **Testing tools** (pytest, coverage, pre-commit)
- ✅ **SmartCocoon component** symlinked

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components.smartcocoon

# Run pre-commit checks
pre-commit run --all-files
```

## 🔐 GitHub Authentication

The devcontainer supports multiple authentication methods:

1. **GitHub CLI** (recommended):
   ```bash
   gh auth login
   ```

2. **Personal Access Token**:
   ```bash
   export GITHUB_TOKEN=your_token_here
   git push origin branch-name
   ```

3. **Interactive**:
   ```bash
   git push origin branch-name
   # Enter username and token when prompted
   ```

## 📁 Files

- `Dockerfile` - Container definition
- `devcontainer.json` - VS Code configuration
- `setup-git.sh` - Git setup script
- `env.example` - Environment variables template
- `README.md` - This file
