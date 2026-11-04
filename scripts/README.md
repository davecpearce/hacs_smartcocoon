# Scripts

This directory contains utility scripts for development and CI testing.

## Available Scripts

### CI Testing

- **`run-ci-local.sh`** - Run full GitHub Actions CI locally using act
- **`run-ci-summary.sh`** - Run CI with summary output (less verbose)
- **`run-act-host.sh`** - Run CI from host machine (outside devcontainer)

### Checks (run by pre-commit and CI)

- **`check_tool_pins.py`** - Fails when ruff, pylint or mypy has a different version in
  `requirements_test.txt` than in `.pre-commit-config.yaml`. Runs as a pre-commit hook.
- **`check_declared_ha_version.py`** - Fails when `hacs.json` declares a different Home
  Assistant version from the one the tests run against. Runs in the CI test job.

### Development

- **`update-precommit.sh`** - Update pre-commit hooks to latest versions

## Usage

Run from project root:

```bash
# Full CI test
./scripts/run-ci-local.sh

# Quick CI test with summary
./scripts/run-ci-summary.sh

# Update pre-commit hooks
./scripts/update-precommit.sh
```

Or use the Makefile:

```bash
make ci-local
make ci-summary
make update-hooks
```

## Prerequisites

- **Docker** - Required for act (CI testing)
- **act** - GitHub Actions runner (installed in devcontainer)
- **pre-commit** - Code quality hooks
