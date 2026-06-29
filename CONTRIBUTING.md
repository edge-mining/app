# Contributing to Edge Mining

Thank you for your interest in contributing! Please follow these guidelines to help us maintain a high-quality project.

> **Note:** This project is a monorepo. The `core/` directory contains the backend, `frontend/` contains the web UI. The root directory manages Docker builds and orchestration.

## Getting Started

Refer to the [README.md](./README.md) for project overview and Docker setup.
For backend environment setup and installation instructions, see [DEVELOPMENT.md](./DEVELOPMENT.md) and [DEV_TOOLS.md](./DEV_TOOLS.md).

## Development Workflow

- Use feature branches for your work.
- Follow the _Hexagonal Architecture_ and _Domain Driven Design_ conventions described in the README.
- Keep your feature branch up to date with `main`; `main` is the active integration and development branch.
- Clean, update, and verify your environment as described in [DEVELOPMENT.md](./DEVELOPMENT.md).
- You can use `make` from the repo root for unified commands, or `cd core/ && make` for backend-specific tasks.

## Code Quality

- Pre-commit hooks and code formatting are required. See [DEV_TOOLS.md](./DEV_TOOLS.md) for details.
- Pre-commit configuration is at the repo root (`.pre-commit-config.yaml`).

## Pull Requests

- Open pull requests against `main`.
- Keep changes focused and use a feature branch rather than committing directly on `main`.
- Ensure your changes are well-tested.
- Write clear commit messages and PR descriptions.
- Link related issues if applicable.

## Need Help?

Check the [Docs repository](https://github.com/edge-mining/docs) or open an issue.
