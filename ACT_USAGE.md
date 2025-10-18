# Running GitHub Actions Locally with Act

This project supports running GitHub Actions locally using [nektos/act](https://github.com/nektos/act).

## Quick Start

### Option 1: From devcontainer (after rebuild)

```bash
./run-ci-local.sh
```

### Option 2: From host machine

```bash
./run-act-host.sh
```

## Setup Options

### 1. 🔄 Rebuild devcontainer with Docker support (Recommended)

The devcontainer has been configured to mount the Docker socket. To enable act:

1. Rebuild the devcontainer: `Ctrl+Shift+P` → `Dev Containers: Rebuild Container`
2. Run: `./run-ci-local.sh`

### 2. 🖥️ Run from host machine

If you prefer to run act from your host machine:

1. Install act on your host: https://github.com/nektos/act#installation
2. Run: `./run-act-host.sh`

### 3. 🧪 Use pre-commit for local testing

For quick local testing without Docker:

```bash
pre-commit run --all-files
```

## Prerequisites

- Act is installed in the devcontainer (already configured)
- Docker is running (act uses Docker to run the actions)

## Configuration

The `.actrc` file contains default configuration:

- Uses `catthehacker/ubuntu:act-latest` runner image
- Binds current directory to `/workspaces/hacs_smartcocoon`
- Uses secrets from `.devcontainer/.env` if available
- Enables verbose output

## Common Commands

```bash
# Run specific job with secrets
act -j test --secret-file .devcontainer/.env

# Run with different runner image
act -j test -P ubuntu-latest=node:16

# Run and keep containers for debugging
act -j test --rm=false

# Run with specific event
act push -j test
```

## Troubleshooting

1. **Docker not running**: Make sure Docker is running in your devcontainer
2. **Permission issues**: Run `chmod +x run-ci-local.sh`
3. **Secrets missing**: Check `.devcontainer/.env` file exists and has required secrets
4. **Image pull issues**: Use `--pull=false` to use local images

## Benefits

- Test CI changes before pushing
- Debug failing jobs locally
- Faster iteration cycle
- No need to push to test CI changes
