# PowerShell script for Edge Mining Development Tools (Windows alternative to Makefile)

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Variables
$VENV_PATH = ".venv\Scripts"
$PYTHON = "$VENV_PATH\python.exe"
$PIP = "$VENV_PATH\pip.exe"
$PRE_COMMIT = "$VENV_PATH\pre-commit.exe"

function Show-Help {
    Write-Host "Edge Mining Development Tools (PowerShell)" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  setup          - Set up development environment"
    Write-Host "  install        - Install dependencies"
    Write-Host "  install-dev    - Install development dependencies"
    Write-Host "  format         - Format code with ruff"
    Write-Host "  lint           - Run all linting checks"
    Write-Host "  lint-fix       - Run linting and fix what can be auto-fixed"
    Write-Host "  test           - Run tests"
    Write-Host "  test-cov       - Run tests with coverage"
    Write-Host "  pre-commit     - Run pre-commit hooks on all files"
    Write-Host "  pre-commit-install - Install pre-commit hooks"
    Write-Host "  clean          - Clean cache and temporary files"
    Write-Host ""
    Write-Host "Usage: .\dev-tools.ps1 <command>" -ForegroundColor Cyan
    Write-Host "Example: .\dev-tools.ps1 setup" -ForegroundColor Cyan
}

function Install-Dependencies {
    Write-Host "📦 Installing production dependencies..." -ForegroundColor Blue
    & $PIP install -r requirements.txt
    Write-Host "✅ Production dependencies installed!" -ForegroundColor Green
}

function Install-DevDependencies {
    Write-Host "📦 Installing development dependencies..." -ForegroundColor Blue
    & $PIP install -r requirements-dev.txt
    Write-Host "✅ Development dependencies installed!" -ForegroundColor Green
}

function Setup-Environment {
    Install-DevDependencies
    Install-PreCommitHooks
    Write-Host "✅ Development environment setup complete!" -ForegroundColor Green
}

function Format-Code {
    Write-Host "🔧 Formatting code..." -ForegroundColor Blue
    & $PYTHON -m ruff format edge_mining/ tests/
    Write-Host "✅ Code formatting complete!" -ForegroundColor Green
}

function Run-Lint {
    Write-Host "🔍 Running linting checks..." -ForegroundColor Blue
    & $PYTHON -m ruff check edge_mining/
    & $PYTHON -m mypy edge_mining/
    & $PYTHON -m bandit -r edge_mining/ --skip B311,B104
    Write-Host "✅ Linting complete!" -ForegroundColor Green
}

function Run-LintFix {
    Write-Host "🔧 Running auto-fixable linting..." -ForegroundColor Blue
    & $PYTHON -m ruff check --fix edge_mining/
    & $PYTHON -m ruff format edge_mining/
    Write-Host "✅ Auto-fix complete!" -ForegroundColor Green
}

function Run-Tests {
    Write-Host "🧪 Running tests..." -ForegroundColor Blue
    & $PYTHON -m pytest tests/ -v
    Write-Host "✅ Tests complete!" -ForegroundColor Green
}

function Run-TestsWithCoverage {
    Write-Host "🧪 Running tests with coverage..." -ForegroundColor Blue
    & $PYTHON -m pytest tests/ -v --cov=edge_mining --cov-report=html --cov-report=term
    Write-Host "✅ Tests with coverage complete!" -ForegroundColor Green
}

function Run-PreCommit {
    Write-Host "🔧 Running pre-commit hooks..." -ForegroundColor Blue
    & $PRE_COMMIT run --all-files
    Write-Host "✅ Pre-commit complete!" -ForegroundColor Green
}

function Install-PreCommitHooks {
    Write-Host "🔧 Installing pre-commit hooks..." -ForegroundColor Blue
    & $PRE_COMMIT install
    Write-Host "✅ Pre-commit hooks installed!" -ForegroundColor Green
}

function Clean-Cache {
    Write-Host "🧹 Cleaning cache and temporary files..." -ForegroundColor Blue

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

    # Remove build and dist directories
    @("build", "dist", ".coverage", "htmlcov", ".pytest_cache") | ForEach-Object {
        if (Test-Path $_) {
            Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    Write-Host "✅ Cleanup complete!" -ForegroundColor Green
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "setup" { Setup-Environment }
    "install" { Install-Dependencies }
    "install-dev" { Install-DevDependencies }
    "format" { Format-Code }
    "lint" { Run-Lint }
    "lint-fix" { Run-LintFix }
    "test" { Run-Tests }
    "test-cov" { Run-TestsWithCoverage }
    "pre-commit" { Run-PreCommit }
    "pre-commit-install" { Install-PreCommitHooks }
    "clean" { Clean-Cache }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}
