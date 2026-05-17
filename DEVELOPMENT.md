# Edge Mining Development Workflow

This guide describes the recommended workflow for contributing to the Edge Mining project.

> **Monorepo note:** This project uses a monorepo layout. Backend code lives in `core/`, frontend in `frontend/`. Docker build and orchestration files are at the repository root.

## Architecture

The project uses **Hexagonal Architecture (Ports and Adapters)** to clearly separate the business logic (Domain and Application Layer) from infrastructural dependencies (Database, external APIs, Hardware Control, User Interfaces).

-   **`edge_mining/domain`**: Contains the pure business logic, subdomains and  their models (Entities, Value Objects), domain exceptions, and the interfaces (Ports) that define the contracts with the outside world.
-   **`edge_mining/application`**: Contains the application services that orchestrate the use cases, utilizing the Domain's Ports.
-   **`edge_mining/adapters`**: Contains the concrete implementations of Ports.
    -   **`domain`**: Adapters strictly used by domain elements.
    -   **`infrastructure`**: Infrastructure adapters, used cross-domain (logger, persistence, api).
-   **`edge_mining/shared`**: Shared elements (and interfaces) used cross-domain.
-   **`test`**: Contains application tests.
-   **`edge_mining/__main__.py`**: Main entry point, responsible for "wiring" dependencies (Dependency Injection).

## Initial Setup

### 1. Clone the repository and enter the directory

```bash
git clone https://github.com/edge-mining/app.git
cd app
```

### 2. Setup development environment

Create a Python virtual environment (if you have not created it yet).

```bash
python -m venv .venv
```

and activate it before running other commands.

#### On Linux/macOS:
```bash
source .venv/bin/activate
```
#### On Windows:
```cmd
.venv\Scripts\activate
```

Install the required dependencies and development tools:

```bash
pip install -r core/requirements.txt
```

```bash
pip install -r core/requirements-dev.txt
```

Configure environment variables by copying `.env.example` to `.env` and editing the values as needed.

```bash
cp .env.example .env
nano .env # Edit the .env file
```

Key settings:
- `TIMEZONE`: Set your local timezone (e.g., `UTC`, `America/New_York`)
- `LATITUDE` and `LONGITUDE`: Set your location for sunrise/sunset calculations
- `DB_PATH`: Database URL (e.g., `sqlite:///data/db/edgemining.db` or PostgreSQL URL)
- `RUN_MIGRATIONS_ON_STARTUP`: Set to `true` to automatically apply database migrations
- `SCHEDULER_INTERVAL_SECONDS`: Set the interval for the optimization scheduler (default: `60`)

Run the setup command to install the required dependencies.

**NOTE**: Use the `make` command if you are on Linux or you are on WSL. Use `dev-tools.ps1` or `dev-tools.bat` if you are on Windows.
For more details, see [DEV_TOOLS.md](DEV_TOOLS.md).

#### From the repo root (recommended):
```bash
make setup
```
This sets up both backend and frontend environments.

#### Or from `core/` directly:
```bash
cd core
make setup
```

This command:

- Installs development dependencies from `requirements-dev.txt`.
- Configures pre-commit hooks for automatic code quality checking.

### 3. Verify everything works

Run the following command to check code formatting, linting, and tests before starting development. This ensures your environment is set up correctly and all pre-commit checks pass.

```bash
make pre-commit
```

## Execution

You can run the application in different modes via the main entry point:

1. **Standard Mode (Default):** Starts the main automation loop that checks available energy and controls miners at regular intervals. Starts a REST API (FastAPI) server also to interact with the system programmatically.
```bash
python -m core/edge_mining
# Or by explicitly specifying
python -m core/edge_mining standard
```
2. **CLI Mode:** Access the command line interface with an interactive menu to manage miners, energy sources, controller, policies, etc.
```bash
python -m core/edge_mining cli interactive

```
You can use the `--help` flag to see all available options:
```bash
python -m core/edge_mining cli --help
```

The API will be available at `http://localhost:8001` (or the configured port). You can access the interactive documentation (Swagger UI) at `http://localhost:8001/docs`.

## Development Workflow

### 1. Before starting development

```bash
# Clean temporary files
make clean

# Update dependencies if necessary
make install-dev
```

### 2. During development

#### Automatic code formatting

Run the following command to automatically format your code according to the project's style guidelines.

```bash
make format
```

#### Code quality check

Use this command to check your code for linting issues and ensure it meets quality standards.

```bash
make lint
```

#### Running tests

Execute this command to run all tests and verify your changes do not break existing functionality.

```bash
make test
```

### 3. Before committing

Pre-commit hooks run automatically, but you can run them manually.

```bash
make pre-commit
```

If there are errors, fix them and try again.

### 4. Commit and Push

```bash
git add .
git commit -m "feat: feature description"
git push
```

## Useful Commands

### Common problem solving

#### Auto-fix linting issues

```bash
make lint-fix
```

#### Clean the environment completely

```bash
make clean

# Remove virtual environment if necessary
rm -rf .venv
python -m venv .venv
make setup
```

#### Tests with detailed coverage

```bash
make test-cov
```

This will generate an HTML report in `htmlcov/index.html`

#### Security check

```bash
bandit -r core/edge_mining/
```

#### Type checking con mypy

```bash
mypy core/edge_mining/
```

## Tools Structure

See the [DEV_TOOLS.md](DEV_TOOLS.md) file for detailed information about the tools used in this project.

## Troubleshooting

### Pre-commit doesn't work

```bash
# Reinstall pre-commit
pre-commit uninstall
make pre-commit-install

# Update hooks
pre-commit autoupdate
```

### Import or dependency errors

```bash
# Check virtual environment
which python
# Should point to .venv/bin/python

# Reinstall dependencies
make clean
make install-dev
```

### Mypy errors

```bash
# Mypy is configured to be permissive during development
# Errors don't block commits but it's good to resolve them

# To run mypy manually:
mypy core/edge_mining/
```

### Formatting conflicts

```bash
make format
make lint

# The makefile is configured to handle most conflicts
```

## Best Practices

1. **Always run `make pre-commit` before committing**
2. **Use `make format` to automatically format code**
3. **Write tests for new features**
4. **Maintain high test coverage**
5. **Use type hints when possible**
6. **Follow Python naming conventions (PEP 8)**
7. **Write docstrings for public functions and classes**

## Commit Conventions

Use conventional commits:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation updates
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding/modifying tests
- `chore:` for maintenance tasks

Example commit messages:

```bash
git commit -m "feat: add energy monitoring adapter for solar panels"
git commit -m "fix: resolve memory leak in optimization service"
git commit -m "docs: update API documentation for miner endpoints"
```
