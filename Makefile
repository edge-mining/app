# Makefile for Edge Mining App (monorepo)
#
# Unified entry point for development and Docker operations.
# For core-specific commands, you can also use: cd core/ && make <target>

.PHONY: help setup dev-core dev-frontend format lint lint-fix test test-cov \
        pre-commit pre-commit-install clean build up down logs restart

help:
	@echo "Edge Mining App — Development & Docker Commands"
	@echo "================================================"
	@echo ""
	@echo "Development:"
	@echo "  setup            - Set up full development environment (core + frontend)"
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

setup: dev-core dev-frontend pre-commit-install
	@echo "✅ Full development environment setup complete!"

dev-core:
	@echo "🐍 Setting up core backend..."
	cd core && $(MAKE) setup

dev-frontend:
	@echo "🌐 Installing frontend dependencies..."
	cd frontend && npm install

format:
	cd core && $(MAKE) format

lint:
	cd core && $(MAKE) lint

lint-fix:
	cd core && $(MAKE) lint-fix

test:
	cd core && $(MAKE) test

test-cov:
	cd core && $(MAKE) test-cov

pre-commit:
	pre-commit run --all-files

pre-commit-install:
	pre-commit install

clean:
	cd core && $(MAKE) clean
	rm -rf frontend/node_modules/.tmp 2>/dev/null || true

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
