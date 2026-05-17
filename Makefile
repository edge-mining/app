# Makefile for Edge Mining App (monorepo)
#
# Unified entry point for development and Docker operations.

.PHONY: help setup venv dev-core dev-frontend format lint lint-fix test test-cov \
        pre-commit pre-commit-install clean build up down logs restart

# ── Variables ────────────────────────────────────────────────────────

VENV := .venv/bin

help:
	@echo "Edge Mining App — Development & Docker Commands"
	@echo "================================================"
	@echo ""
	@echo "Development:"
	@echo "  setup            - Set up full development environment (core + frontend)"
	@echo "  venv             - Create .venv and install all Python dependencies"
	@echo "  dev-core         - Set up core backend development environment only"
	@echo "  dev-frontend     - Install frontend dependencies only"
	@echo "  format           - Format core code with ruff"
	@echo "  lint             - Run all linting checks on core"
	@echo "  lint-fix         - Run linting and auto-fix on core"
	@echo "  test             - Run core tests"
	@echo "  test-cov         - Run core tests with coverage"
	@echo "  pre-commit       - Run pre-commit hooks on all files"
	@echo "  pre-commit-install - Install pre-commit hooks"
	@echo "  clean            - Clean cache and temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  build            - Build the Docker image (frontend + backend + nginx)"
	@echo "  up               - Start the application (docker compose up -d)"
	@echo "  down             - Stop the application (docker compose down)"
	@echo "  restart          - Rebuild and restart the application"
	@echo "  logs             - Follow application logs"

# ── Development ──────────────────────────────────────────────────────

setup: venv dev-core dev-frontend pre-commit-install
	@echo "✅ Full development environment setup complete!"

venv:
	@echo "🐍 Creating virtual environment and installing dependencies..."
	test -d .venv || python3 -m venv .venv
	$(VENV)/pip install --upgrade pip
	$(VENV)/pip install -r core/requirements.txt
	@echo "✅ Virtual environment ready!"

dev-core:
	@echo "🐍 Setting up core backend..."
	$(VENV)/pip install -r core/requirements-dev.txt
	@echo "✅ Core backend setup complete!"

dev-frontend:
	@echo "🌐 Installing frontend dependencies..."
	cd frontend && npm install

format:
	@echo "🔧 Formatting code..."
	cd core && ../$(VENV)/python -m ruff format edge_mining/ tests/
	@echo "✅ Code formatting complete!"

lint:
	@echo "🔍 Running linting checks..."
	cd core && ../$(VENV)/python -m ruff check edge_mining/
	cd core && ../$(VENV)/python -m mypy edge_mining/ || true
	cd core && ../$(VENV)/python -m bandit -r edge_mining/ --skip B311,B104 || true
	@echo "✅ Linting complete!"

lint-fix:
	@echo "🔧 Running auto-fixable linting..."
	cd core && ../$(VENV)/python -m ruff check --fix edge_mining/
	cd core && ../$(VENV)/python -m ruff format edge_mining/
	@echo "✅ Auto-fix complete!"

test:
	@echo "🧪 Running tests..."
	cd core && ../$(VENV)/python -m pytest tests/ -v
	@echo "✅ Tests complete!"

test-cov:
	@echo "🧪 Running tests with coverage..."
	cd core && ../$(VENV)/python -m pytest tests/ -v --cov=edge_mining --cov-report=html --cov-report=term
	@echo "✅ Tests with coverage complete!"

pre-commit:
	$(VENV)/pre-commit run --all-files

pre-commit-install:
	$(VENV)/pre-commit install

clean:
	@echo "🧹 Cleaning cache and temporary files..."
	find core/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find core/ -type f -name "*.pyc" -delete 2>/dev/null || true
	find core/ -type f -name "*.pyo" -delete 2>/dev/null || true
	find core/ -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf core/build/ core/dist/ core/.coverage core/htmlcov/ core/.pytest_cache/ 2>/dev/null || true
	rm -rf frontend/node_modules/.tmp 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# ── Docker ───────────────────────────────────────────────────────────

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart: build
	docker compose up -d

logs:
	docker compose logs -f
