@echo off
REM Batch script for Edge Mining Development Tools (Windows CMD alternative to Makefile)

setlocal EnableDelayedExpansion

REM Variables
set VENV_PATH=.venv\Scripts
set PYTHON=%VENV_PATH%\python.exe
set PIP=%VENV_PATH%\pip.exe
set PRE_COMMIT=%VENV_PATH%\pre-commit.exe

REM Get command from first argument
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=help

REM Main command dispatcher
if /i "%COMMAND%"=="help" goto :help
if /i "%COMMAND%"=="setup" goto :setup
if /i "%COMMAND%"=="install" goto :install
if /i "%COMMAND%"=="install-dev" goto :install-dev
if /i "%COMMAND%"=="format" goto :format
if /i "%COMMAND%"=="lint" goto :lint
if /i "%COMMAND%"=="lint-fix" goto :lint-fix
if /i "%COMMAND%"=="test" goto :test
if /i "%COMMAND%"=="test-cov" goto :test-cov
if /i "%COMMAND%"=="pre-commit" goto :pre-commit
if /i "%COMMAND%"=="pre-commit-install" goto :pre-commit-install
if /i "%COMMAND%"=="clean" goto :clean

echo Unknown command: %COMMAND%
echo.
goto :help

:help
echo Edge Mining Development Tools (Batch)
echo ====================================
echo.
echo Available commands:
echo   setup          - Set up development environment
echo   install        - Install dependencies
echo   install-dev    - Install development dependencies
echo   format         - Format code with ruff
echo   lint           - Run all linting checks
echo   lint-fix       - Run linting and fix what can be auto-fixed
echo   test           - Run tests
echo   test-cov       - Run tests with coverage
echo   pre-commit     - Run pre-commit hooks on all files
echo   pre-commit-install - Install pre-commit hooks
echo   clean          - Clean cache and temporary files
echo.
echo Usage: dev-tools.bat ^<command^>
echo Example: dev-tools.bat setup
goto :end

:setup
call :install-dev
call :pre-commit-install
echo ✅ Development environment setup complete!
goto :end

:install
echo 📦 Installing production dependencies...
%PIP% install -r requirements.txt
echo ✅ Production dependencies installed!
goto :end

:install-dev
echo 📦 Installing development dependencies...
%PIP% install -r requirements-dev.txt
echo ✅ Development dependencies installed!
goto :end

:format
echo 🔧 Formatting code...
%PYTHON% -m ruff format edge_mining/ tests/
echo ✅ Code formatting complete!
goto :end

:lint
echo 🔍 Running linting checks...
%PYTHON% -m ruff check edge_mining/
%PYTHON% -m mypy edge_mining/
%PYTHON% -m bandit -r edge_mining/ --skip B311,B104
echo ✅ Linting complete!
goto :end

:lint-fix
echo 🔧 Running auto-fixable linting...
%PYTHON% -m ruff check --fix edge_mining/
%PYTHON% -m ruff format edge_mining/
echo ✅ Auto-fix complete!
goto :end

:test
echo 🧪 Running tests...
%PYTHON% -m pytest tests/ -v
echo ✅ Tests complete!
goto :end

:test-cov
echo 🧪 Running tests with coverage...
%PYTHON% -m pytest tests/ -v --cov=edge_mining --cov-report=html --cov-report=term
echo ✅ Tests with coverage complete!
goto :end

:pre-commit
echo 🔧 Running pre-commit hooks...
%PRE_COMMIT% run --all-files
echo ✅ Pre-commit complete!
goto :end

:pre-commit-install
echo 🔧 Installing pre-commit hooks...
%PRE_COMMIT% install
echo ✅ Pre-commit hooks installed!
goto :end

:clean
echo 🧹 Cleaning cache and temporary files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc *.pyo) do @if exist "%%f" del /q "%%f" 2>nul
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d" 2>nul
if exist build rd /s /q build 2>nul
if exist dist rd /s /q dist 2>nul
if exist .coverage del /q .coverage 2>nul
if exist htmlcov rd /s /q htmlcov 2>nul
if exist .pytest_cache rd /s /q .pytest_cache 2>nul
echo ✅ Cleanup complete!
goto :end

:end
