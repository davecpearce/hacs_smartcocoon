# Development Setup

This project uses **devcontainer** for development, providing a complete Home Assistant development environment.

## 🐳 Devcontainer Setup

The devcontainer provides a complete Home Assistant development environment with:

- Python 3.13.2 (Home Assistant minimum requirement)
- Home Assistant core installed
- All dependencies pre-installed
- VS Code extensions configured
- Symlink to Home Assistant components

### Getting Started

1. **Prerequisites**:
   - VS Code with the "Dev Containers" extension
   - Docker Desktop running

2. **Open in Devcontainer**:
   - Open this folder in VS Code
   - VS Code will prompt to reopen in container, or use `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"
   - Wait for the container to build and set up the environment (first time takes 3-5 minutes)

3. **Start Developing**: Everything is ready to go!

### Devcontainer Features

- **Home Assistant Integration**: Your component is automatically symlinked to HA core
- **Testing**: Run `python -m pytest` to run tests
- **Linting**: Pre-configured with pylint, black, mypy
- **Debugging**: Full debugging support with breakpoints
- **Port Forwarding**: Home Assistant runs on port 9123
- **Git Integration**: SSH keys are mounted for seamless git operations

## 🧪 Testing

Run tests directly in the devcontainer:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=custom_components/smartcocoon --cov-report=term

# Run specific test file
python -m pytest tests/test_final.py -v

# Run tests with verbose output
python -m pytest -v
```

## 🛠️ Development Tools

### Pre-commit Hooks

```bash
# Install pre-commit hooks (already done in devcontainer)
pre-commit install

# Run all hooks
pre-commit run --all-files
```

### Code Quality

All tools are pre-configured in the devcontainer:

- **Black**: Code formatting (auto-format on save)
- **isort**: Import sorting
- **pylint**: Code linting
- **mypy**: Type checking
- **bandit**: Security scanning
- **semgrep**: Security analysis

### Home Assistant Testing

```bash
# Start Home Assistant (in devcontainer)
hass --config /opt/hass --open-ui

# Run Home Assistant tests
cd /opt/hass
python -m pytest tests/components/smartcocoon/
```

## 📁 Project Structure

```
ha-smartcocoon/
├── custom_components/smartcocoon/    # Main integration code
├── tests/                            # Test files
├── .devcontainer/                    # Devcontainer configuration
│   ├── devcontainer.json            # VS Code devcontainer config
│   ├── Dockerfile                   # Container definition
│   └── configuration.yaml           # Home Assistant config
├── requirements.txt                  # Main dependencies
├── requirements_test.txt             # Test dependencies
├── .pre-commit-config.yaml          # Pre-commit hooks
└── mypy.ini                         # MyPy configuration
```

## 🚀 Quick Start

1. **Open in VS Code**
2. **Reopen in Container** when prompted
3. **Wait for setup** (first time only)
4. **Run tests**: `python -m pytest`
5. **Start coding!**

## 💡 Tips

- **Port 9123**: Home Assistant runs on this port (forwarded from container)
- **Symlink**: Your component is automatically linked to Home Assistant core
- **Git**: SSH keys are mounted for seamless git operations
- **Extensions**: All necessary VS Code extensions are pre-installed
- **Debugging**: Set breakpoints and debug directly in VS Code
