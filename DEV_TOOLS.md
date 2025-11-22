# Development Tools

This project uses various tools to maintain code quality and includes a Makefile for common development tasks. The Makefile is cross-platform compatible and works on both Windows and Linux/macOS.

### Prerequisites for Windows users:
To use the Makefile on Windows, you must run `make` via Windows Subsystem for Linux (WSL).
- Install [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install)
- Run the `make` commands from a WSL shell (e.g., Ubuntu)

**Alternative for Windows users:** If you prefer not to use WSL, you can use the provided alternative scripts:

PowerShell:
```powershell
.\dev-tools.ps1 help          # Show all available commands
.\dev-tools.ps1 setup         # Set up development environment
.\dev-tools.ps1 install       # Install dependencies
# ... (same commands as make)
```

Command Prompt (Batch):
```cmd
.\dev-tools.bat help           # Show all available commands
.\dev-tools.bat setup          # Set up development environment
.\dev-tools.bat install        # Install dependencies
# ... (same commands as make)
```

### Available commands:
```bash
make help          # Show all available commands
make setup         # Set up development environment
make install       # Install dependencies
make install-dev   # Install development dependencies
make format        # Format code with ruff
make lint          # Run all linting checks
make lint-fix      # Run linting and fix what can be auto-fixed
make test          # Run tests
make test-cov      # Run tests with coverage
make pre-commit    # Run pre-commit hooks on all files
make clean         # Clean cache and temporary files
```

## Quick Setup

To quickly configure the development environment:

```bash
make setup
```

## Development Dependencies Installation

```bash
# Production dependencies only
make install

# Development dependencies
make install-dev
```

## Pre-commit Hooks

Pre-commit hooks are automatically executed on each commit to verify code quality.

### Installation

```bash
make pre-commit-install
```

### Manual execution on all files

```bash
make pre-commit
```

## Formatting and Linting

### Automatic formatting

```bash
make format
```

### Complete linting

```bash
make lint
```

### Auto-fix linting issues

```bash
make lint-fix
```

## Tests

### Running tests

```bash
make test
```

### Tests with coverage

```bash
make test-cov
```

## Available Makefile Commands

- `make setup` - Sets up the complete development environment
- `make install` - Installs production dependencies
- `make install-dev` - Installs development dependencies
- `make format` - Formats code with black and isort
- `make lint` - Runs all linting checks
- `make lint-fix` - Runs linting and automatically fixes issues
- `make test` - Runs tests
- `make test-cov` - Runs tests with coverage
- `make pre-commit` - Runs pre-commit on all files
- `make pre-commit-install` - Installs pre-commit hooks
- `make clean` - Cleans cache and temporary files

## Linting and Formatting Tools

### Ruff - Code formatting

```bash
ruff format edge_mining/
```

### Ruff - Linting

```bash
ruff check edge_mining/
```

Use the option `--ignore=E501` to disable line length checks.
```bash
ruff check edge_mining/ --ignore=E501
```

### mypy - Type checking

```bash
mypy edge_mining/
```

### bandit - Security check

```bash
bandit -r edge_mining/
```

## Configurations

- **`.pre-commit-config.yaml`**: Pre-commit hooks configuration
- **`pyproject.toml`**: Configuration for mypy, ruff, bandit, pytest and coverage
- **`requirements-dev.txt`**: Development dependencies
- **`Makefile`**: Automation commands

## Troubleshooting

If pre-commit doesn't work properly:

1. Make sure git is initialized: `git init`
2. Reinstall pre-commit: `make pre-commit-install`
3. Update hooks: `pre-commit autoupdate`

If you have dependency issues:

1. Clean the environment: `make clean`
2. Recreate the virtual environment: `python -m venv .venv`
3. Reinstall dependencies: `make setup`
