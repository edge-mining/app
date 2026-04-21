# Makefile for Edge Mining Development Tools

# Detect operating system
ifeq ($(OS),Windows_NT)
# On native Windows, instruct to use WSL or the provided scripts
.PHONY: help setup install install-dev format lint lint-fix test test-cov pre-commit pre-commit-install clean
help setup install install-dev format lint lint-fix test test-cov pre-commit pre-commit-install clean:
	@echo "Windows environment detected."
	@echo "This Makefile is intended to run under WSL (Linux) or on macOS/Linux."
	@echo "Please either:"
	@echo "  - Use WSL and run 'make <target>' from your Linux shell, or"
	@echo "  - Use the Windows scripts: .\\dev-tools.ps1 or .\\dev-tools.bat"
	@echo ""
	@echo "Examples:"
	@echo "  PowerShell: .\\dev-tools.ps1 help"
	@echo "  CMD:        .\\dev-tools.bat help"
	@exit
else
	# Unix-like (Linux, macOS)
	VENV_BIN := .venv/bin
	PYTHON := $(VENV_BIN)/python
	PIP := $(VENV_BIN)/pip
	PRE_COMMIT := $(VENV_BIN)/pre-commit

# Default target
help:
	@echo "Edge Mining Development Tools"
	@echo "============================="
	@echo ""
	@echo "Available commands:"
	@echo "  setup          - Set up development environment"
	@echo "  install        - Install dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo "  format         - Format code with ruff"
	@echo "  lint           - Run all linting checks"
	@echo "  lint-fix       - Run linting and fix what can be auto-fixed"
	@echo "  test           - Run tests"
	@echo "  test-cov       - Run tests with coverage"
	@echo "  pre-commit     - Run pre-commit hooks on all files"
	@echo "  pre-commit-install - Install pre-commit hooks"
	@echo "  clean          - Clean cache and temporary files"

# Setup development environment
setup: install-dev pre-commit-install
	@echo "✅ Development environment setup complete!"

# Install production dependencies
install:
	$(PIP) install -r requirements.txt

# Install development dependencies
install-dev:
	$(PIP) install -r requirements-dev.txt

# Format code
format:
	@echo "🔧 Formatting code..."
	$(PYTHON) -m ruff format edge_mining/ tests/
	@echo "✅ Code formatting complete!"

# Run linting
lint:
	@echo "🔍 Running linting checks..."
	$(PYTHON) -m ruff check edge_mining/
	$(PYTHON) -m mypy edge_mining/ || true
	$(PYTHON) -m bandit -r edge_mining/ --skip B311,B104 || true
	@echo "✅ Linting complete!"

# Run linting and fix what can be auto-fixed
lint-fix:
	@echo "🔧 Running auto-fixable linting..."
	$(PYTHON) -m ruff check --fix edge_mining/
	$(PYTHON) -m ruff format edge_mining/
	@echo "✅ Auto-fix complete!"

# Run tests
test:
	@echo "🧪 Running tests..."
	$(PYTHON) -m pytest tests/ -v
	@echo "✅ Tests complete!"

# Run tests with coverage
test-cov:
	@echo "🧪 Running tests with coverage..."
	$(PYTHON) -m pytest tests/ -v --cov=edge_mining --cov-report=html --cov-report=term
	@echo "✅ Tests with coverage complete!"

# Run pre-commit on all files
pre-commit:
	@echo "🔧 Running pre-commit hooks..."
	$(PRE_COMMIT) run --all-files
	@echo "✅ Pre-commit complete!"

# Install pre-commit hooks
pre-commit-install:
	@echo "🔧 Installing pre-commit hooks..."
	$(PRE_COMMIT) install
	@echo "✅ Pre-commit hooks installed!"

# Clean cache and temporary files
clean:
	@echo "🧹 Cleaning cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ 2>/dev/null || true
	@echo "✅ Cleanup complete!"

endif
