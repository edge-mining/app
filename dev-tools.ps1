# PowerShell script for Edge Mining Development Tools (Windows alternative to Makefile)

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Variables
$CORE_VENV = "core\.venv\Scripts"
$PYTHON = "$CORE_VENV\python.exe"
$PIP = "$CORE_VENV\pip.exe"
$PRE_COMMIT = "$CORE_VENV\pre-commit.exe"

function Show-Help {
    Write-Host "Edge Mining App — Development & Docker Commands (PowerShell)" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Development:" -ForegroundColor Yellow
    Write-Host "  setup              - Set up full development environment (core + frontend)"
    Write-Host "  dev-core           - Set up core backend development environment only"
    Write-Host "  dev-frontend       - Install frontend dependencies only"
    Write-Host "  format             - Format core code with ruff"
    Write-Host "  lint               - Run all linting checks on core"
    Write-Host "  lint-fix           - Run linting and auto-fix on core"
    Write-Host "  test               - Run core tests"
    Write-Host "  test-cov           - Run core tests with coverage"
    Write-Host "  pre-commit         - Run pre-commit hooks on all files"
    Write-Host "  pre-commit-install - Install pre-commit hooks"
    Write-Host "  clean              - Clean cache and temporary files"
    Write-Host ""
    Write-Host "Docker:" -ForegroundColor Yellow
    Write-Host "  build              - Build the Docker image (frontend + backend + nginx)"
    Write-Host "  up                 - Start the application (docker compose up -d)"
    Write-Host "  down               - Stop the application (docker compose down)"
    Write-Host "  restart            - Rebuild and restart the application"
    Write-Host "  logs               - Follow application logs"
    Write-Host ""
    Write-Host "Usage: .\dev-tools.ps1 <command>" -ForegroundColor Cyan
    Write-Host "Example: .\dev-tools.ps1 setup" -ForegroundColor Cyan
}

function Setup-DevCore {
    Write-Host "🐍 Setting up core backend..." -ForegroundColor Blue
    Push-Location core
    & .\.venv\Scripts\pip.exe install -r requirements-dev.txt
    & .\.venv\Scripts\pre-commit.exe install
    Pop-Location
    Write-Host "✅ Core backend setup complete!" -ForegroundColor Green
}

function Setup-DevFrontend {
    Write-Host "🌐 Installing frontend dependencies..." -ForegroundColor Blue
    Push-Location frontend
    & npm install
    Pop-Location
    Write-Host "✅ Frontend dependencies installed!" -ForegroundColor Green
}

function Setup-Environment {
    Setup-DevCore
    Setup-DevFrontend
    Install-PreCommitHooks
    Write-Host "✅ Full development environment setup complete!" -ForegroundColor Green
}

function Format-Code {
    Write-Host "🔧 Formatting code..." -ForegroundColor Blue
    Push-Location core
    & .\.venv\Scripts\python.exe -m ruff format edge_mining/ tests/
    Pop-Location
    Write-Host "✅ Code formatting complete!" -ForegroundColor Green
}

function Run-Lint {
    Write-Host "🔍 Running linting checks..." -ForegroundColor Blue
    Push-Location core
    & .\.venv\Scripts\python.exe -m ruff check edge_mining/
    & .\.venv\Scripts\python.exe -m mypy edge_mining/
    & .\.venv\Scripts\python.exe -m bandit -r edge_mining/ --skip B311,B104
    Pop-Location
    Write-Host "✅ Linting complete!" -ForegroundColor Green
}

function Run-LintFix {
    Write-Host "🔧 Running auto-fixable linting..." -ForegroundColor Blue
    Push-Location core
    & .\.venv\Scripts\python.exe -m ruff check --fix edge_mining/
    & .\.venv\Scripts\python.exe -m ruff format edge_mining/
    Pop-Location
    Write-Host "✅ Auto-fix complete!" -ForegroundColor Green
}

function Run-Tests {
    Write-Host "🧪 Running tests..." -ForegroundColor Blue
    Push-Location core
    & .\.venv\Scripts\python.exe -m pytest tests/ -v
    Pop-Location
    Write-Host "✅ Tests complete!" -ForegroundColor Green
}

function Run-TestsWithCoverage {
    Write-Host "🧪 Running tests with coverage..." -ForegroundColor Blue
    Push-Location core
    & .\.venv\Scripts\python.exe -m pytest tests/ -v --cov=edge_mining --cov-report=html --cov-report=term
    Pop-Location
    Write-Host "✅ Tests with coverage complete!" -ForegroundColor Green
}

function Run-PreCommit {
    Write-Host "🔧 Running pre-commit hooks..." -ForegroundColor Blue
    & pre-commit run --all-files
    Write-Host "✅ Pre-commit complete!" -ForegroundColor Green
}

function Install-PreCommitHooks {
    Write-Host "🔧 Installing pre-commit hooks..." -ForegroundColor Blue
    & pre-commit install
    Write-Host "✅ Pre-commit hooks installed!" -ForegroundColor Green
}

function Clean-Cache {
    Write-Host "🧹 Cleaning cache and temporary files..." -ForegroundColor Blue

    Push-Location core

    # Remove __pycache__ directories
    Get-ChildItem -Path . -Recurse -Directory -Name "__pycache__" | ForEach-Object {
        Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Remove .pyc and .pyo files
    Get-ChildItem -Path . -Recurse -Include "*.pyc", "*.pyo" | Remove-Item -Force -ErrorAction SilentlyContinue

    # Remove .egg-info directories
    Get-ChildItem -Path . -Recurse -Directory -Name "*.egg-info" | ForEach-Object {
        Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Remove build artifacts
    @("build", "dist", ".coverage", "htmlcov", ".pytest_cache") | ForEach-Object {
        if (Test-Path $_) {
            Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    Pop-Location

    # Remove frontend temp files
    if (Test-Path "frontend\node_modules\.tmp") {
        Remove-Item -Path "frontend\node_modules\.tmp" -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host "✅ Cleanup complete!" -ForegroundColor Green
}

function Docker-Build {
    Write-Host "🐳 Building Docker image..." -ForegroundColor Blue
    & docker compose build
    Write-Host "✅ Docker build complete!" -ForegroundColor Green
}

function Docker-Up {
    Write-Host "🐳 Starting application..." -ForegroundColor Blue
    & docker compose up -d
    Write-Host "✅ Application started!" -ForegroundColor Green
}

function Docker-Down {
    Write-Host "🐳 Stopping application..." -ForegroundColor Blue
    & docker compose down
    Write-Host "✅ Application stopped!" -ForegroundColor Green
}

function Docker-Restart {
    Write-Host "🐳 Rebuilding and restarting application..." -ForegroundColor Blue
    & docker compose build
    & docker compose up -d
    Write-Host "✅ Application restarted!" -ForegroundColor Green
}

function Docker-Logs {
    & docker compose logs -f
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "setup" { Setup-Environment }
    "dev-core" { Setup-DevCore }
    "dev-frontend" { Setup-DevFrontend }
    "format" { Format-Code }
    "lint" { Run-Lint }
    "lint-fix" { Run-LintFix }
    "test" { Run-Tests }
    "test-cov" { Run-TestsWithCoverage }
    "pre-commit" { Run-PreCommit }
    "pre-commit-install" { Install-PreCommitHooks }
    "clean" { Clean-Cache }
    "build" { Docker-Build }
    "up" { Docker-Up }
    "down" { Docker-Down }
    "restart" { Docker-Restart }
    "logs" { Docker-Logs }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}
