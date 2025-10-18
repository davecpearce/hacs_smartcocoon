# Development Setup

This project supports both **devcontainer** and **local virtual environment** development.

## 🐳 Devcontainer (Recommended)

The devcontainer provides a complete Home Assistant development environment with:
- Python 3.13.2
- Home Assistant core installed
- All dependencies pre-installed
- VS Code extensions configured
- Symlink to Home Assistant components

### Using Devcontainer

1. **Open in VS Code**: Open this folder in VS Code
2. **Reopen in Container**: VS Code will prompt to reopen in container, or use `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"
3. **Wait for Setup**: The container will build and set up the environment
4. **Start Developing**: Everything is ready to go!

### Devcontainer Features

- **Home Assistant Integration**: Your component is automatically symlinked to HA core
- **Testing**: Run `python -m pytest` to run tests
- **Linting**: Pre-configured with pylint, black, mypy
- **Debugging**: Full debugging support with breakpoints
- **Port Forwarding**: Home Assistant runs on port 9123

## 🐍 Local Virtual Environment

For local development without Docker:

### Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_test.txt
```

### Usage

```bash
# Activate environment
source venv/bin/activate

# Run tests
python -m pytest

# Run linting
pre-commit run --all-files
```

## 🔄 Switching Between Environments

### From Devcontainer to Local

1. Close VS Code
2. Delete `.vscode/settings.json` (or rename to `.vscode/settings.json.backup`)
3. Open VS Code normally
4. Activate virtual environment in terminal

### From Local to Devcontainer

1. Close VS Code
2. Restore `.vscode/settings.json` if you backed it up
3. Open VS Code
4. Reopen in container

## 🧪 Testing

Both environments support the same testing commands:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=custom_components/smartcocoon --cov-report=term

# Run specific test file
python -m pytest tests/test_final.py -v
```

## 🛠️ Development Tools

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks
pre-commit run --all-files
```

### Code Quality

- **Black**: Code formatting
- **isort**: Import sorting
- **pylint**: Code linting
- **mypy**: Type checking
- **bandit**: Security scanning
- **semgrep**: Security analysis

## 📁 Project Structure

```
hacs_smartcocoon/
├── custom_components/smartcocoon/    # Main integration code
├── tests/                            # Test files
├── .devcontainer/                    # Devcontainer configuration
├── .vscode/                          # VS Code settings (local)
├── requirements.txt                  # Main dependencies
├── requirements_test.txt             # Test dependencies
├── .pre-commit-config.yaml          # Pre-commit hooks
└── mypy.ini                         # MyPy configuration
```

## 🚀 Quick Start

1. **Choose your environment** (devcontainer recommended)
2. **Open in VS Code**
3. **Run tests**: `python -m pytest`
4. **Start coding!**

## 💡 Tips

- **Devcontainer**: Best for Home Assistant integration testing
- **Local**: Faster for simple changes and debugging
- **Both**: Use the same test suite and code quality tools
- **Git**: Both environments use the same git configuration
