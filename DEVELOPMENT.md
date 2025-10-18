# Development Guide

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality and consistency. The hooks are configured in `.pre-commit-config.yaml`.

### Keeping Versions in Sync

To prevent version drift between local development and CI:

1. **Always run pre-commit locally** before committing:

   ```bash
   pre-commit run --all-files
   ```

2. **Update pre-commit hooks regularly**:

   ```bash
   ./scripts/update-precommit.sh
   ```

3. **CI runs the same pre-commit** - The GitHub Actions workflow runs `pre-commit run --all-files`, ensuring consistency.

### Black Formatting

- **Local Black**: Use `python -m black --safe` to match pre-commit formatting
- **Pre-commit Black**: Uses `--safe` mode for conservative line breaking
- **CI Black**: Uses the same pre-commit configuration

### Version Management

- Pre-commit versions are pinned in `.pre-commit-config.yaml`
- CI uses the same pre-commit configuration
- Regular updates via `./update-precommit.sh` script

## Testing

Run the full CI locally:

```bash
./scripts/run-ci-local.sh
```

Run just the tests:

```bash
./scripts/run-ci-summary.sh
```
