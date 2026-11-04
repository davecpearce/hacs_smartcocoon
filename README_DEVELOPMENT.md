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

- **Home Assistant Integration**: Your component is automatically symlinked into a
  Home Assistant `dev` checkout at `/opt/hass`
- **Port Forwarding**: Home Assistant runs on port 9123
- **Git Integration**: SSH keys are mounted for seamless git operations

## 🧪 Testing

```bash
make install   # requirements_test.txt + editable install
make test      # pytest with coverage; fails under 70%
```

Tests run against the exact Home Assistant version that
`pytest-homeassistant-custom-component` pins. `asyncio_mode = "auto"`, so async tests
need no marker. A test for a fix should fail without the fix: stash the source change
and check it goes red.

Outside the devcontainer you need Python 3.13.2 or later.

## 🛠️ Lint and CI

```bash
make lint      # pre-commit run --all-files: exactly what CI runs
make format    # ruff format + ruff check --fix
make ci-local  # the full GitHub Actions workflow via act (see ACT_USAGE.md)
```

The pre-commit hooks are ruff and ruff-format (line length 88), pylint, mypy, bandit,
semgrep, pyupgrade and prettier. Black and isort are not used. Ruff and pylint both
check test files.

Things that differ from what you might assume:

- **mypy runs in the hook's own environment, without Home Assistant installed.**
  There, Home Assistant imports resolve to `Any`, so some `# type: ignore` comments
  that look redundant in a full venv are required. Check with `pre-commit run mypy`,
  not with mypy in your project venv.
- **ruff, pylint and mypy are pinned twice**: in `requirements_test.txt` and as a `rev`
  in `.pre-commit-config.yaml`. The `check-tool-pins` hook
  (`scripts/check_tool_pins.py`) fails when they disagree. Bump both in one commit.
- **`hacs.json` must declare the Home Assistant version the tests run against.**
  `scripts/check_declared_ha_version.py` fails the test job otherwise. A
  `pytest-homeassistant-custom-component` bump therefore needs `hacs.json` updated in
  the same pull request.
- **`custom_components/__init__.py` must stay.** Without it an editable install breaks
  every test that loads the integration.

CI also runs HACS validation and hassfest, so a malformed `manifest.json` can fail
even when the tests pass.

## 🚀 Releasing

1. Bump the `pysmartcocoon` pin in both `manifest.json` and `requirements.txt`. The
   library version must already be on PyPI.
2. Bump the version in `manifest.json` (`1.5.0`) and `pyproject.toml` (`v1.5.0`).
3. Merge, tag `vX.Y.Z`, and create a GitHub release. HACS installs from releases, so
   a tag alone ships nothing.

## 📁 Project Structure

```
ha-smartcocoon/
├── custom_components/smartcocoon/    # Main integration code
│   └── brand/                        # Icons and logos shown by HA and HACS
├── blueprints/                       # Automation blueprints
├── docs/                             # User docs (automations cookbook)
├── scripts/                          # CI helpers and checks; see scripts/README.md
├── tests/                            # Test files
├── .devcontainer/                    # Devcontainer configuration
│   ├── devcontainer.json            # VS Code devcontainer config
│   ├── Dockerfile                   # Container definition
│   └── configuration.yaml           # Home Assistant config
├── hacs.json                         # HACS metadata, incl. minimum HA version
├── requirements.txt                  # Main dependencies
├── requirements_test.txt             # Test dependencies
├── .pre-commit-config.yaml          # Pre-commit hooks
└── mypy.ini                         # MyPy configuration
```

## 🚀 Quick Start

1. **Open in VS Code**
2. **Reopen in Container** when prompted
3. **Wait for setup** (first time only)
4. **Run tests**: `make test`
5. **Start coding!**

## 💡 Tips

- **Port 9123**: Home Assistant runs on this port (forwarded from container)
- **Symlink**: Your component is automatically linked to Home Assistant core
- **Git**: SSH keys are mounted for seamless git operations
- **Extensions**: All necessary VS Code extensions are pre-installed
- **Debugging**: Set breakpoints and debug directly in VS Code
