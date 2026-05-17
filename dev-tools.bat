@echo off
REM Batch script for Edge Mining Development Tools (Windows CMD alternative to Makefile)

setlocal EnableDelayedExpansion

REM Variables
set VENV=.venv\Scripts
set PYTHON=%VENV%\python.exe
set PIP=%VENV%\pip.exe
set PRE_COMMIT=%VENV%\pre-commit.exe

REM Get command from first argument
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=help

REM Main command dispatcher
if /i "%COMMAND%"=="help" goto :help
if /i "%COMMAND%"=="setup" goto :setup
if /i "%COMMAND%"=="venv" goto :venv
if /i "%COMMAND%"=="dev-core" goto :dev-core
if /i "%COMMAND%"=="dev-frontend" goto :dev-frontend
if /i "%COMMAND%"=="format" goto :format
if /i "%COMMAND%"=="lint" goto :lint
if /i "%COMMAND%"=="lint-fix" goto :lint-fix
if /i "%COMMAND%"=="test" goto :test
if /i "%COMMAND%"=="test-cov" goto :test-cov
if /i "%COMMAND%"=="pre-commit" goto :pre-commit
if /i "%COMMAND%"=="pre-commit-install" goto :pre-commit-install
if /i "%COMMAND%"=="clean" goto :clean
if /i "%COMMAND%"=="build" goto :build
if /i "%COMMAND%"=="up" goto :up
if /i "%COMMAND%"=="down" goto :down
if /i "%COMMAND%"=="restart" goto :restart
if /i "%COMMAND%"=="logs" goto :logs

echo Unknown command: %COMMAND%
echo.
goto :help

:help
echo Edge Mining App — Development ^& Docker Commands (Batch)
echo ========================================================
echo.
echo Development:
echo   setup              - Set up full development environment (core + frontend)
echo   venv               - Create .venv and install all Python dependencies
echo   dev-core           - Set up core backend development environment only
echo   dev-frontend       - Install frontend dependencies only
echo   format             - Format core code with ruff
echo   lint               - Run all linting checks on core
echo   lint-fix           - Run linting and auto-fix on core
echo   test               - Run core tests
echo   test-cov           - Run core tests with coverage
echo   pre-commit         - Run pre-commit hooks on all files
echo   pre-commit-install - Install pre-commit hooks
echo   clean              - Clean cache and temporary files
echo.
echo Docker:
echo   build              - Build the Docker image (frontend + backend + nginx)
echo   up                 - Start the application (docker compose up -d)
echo   down               - Stop the application (docker compose down)
echo   restart            - Rebuild and restart the application
echo   logs               - Follow application logs
echo.
echo Usage: dev-tools.bat ^<command^>
echo Example: dev-tools.bat setup
goto :end

:setup
call :do_venv
call :do_dev_core
call :do_dev_frontend
call :do_pre_commit_install
echo ✅ Full development environment setup complete!
goto :end

:venv
call :do_venv
goto :end

:do_venv
echo 🐍 Creating virtual environment and installing dependencies...
if not exist .venv (
    python -m venv .venv
)
%PIP% install --upgrade pip
%PIP% install -r core\requirements.txt
echo ✅ Virtual environment ready!
exit /b

:dev-core
call :do_dev_core
goto :end

:do_dev_core
echo 🐍 Setting up core backend...
%PIP% install -r core\requirements-dev.txt
exit /b

:dev-frontend
call :do_dev_frontend
goto :end

:do_dev_frontend
echo 🌐 Installing frontend dependencies...
pushd frontend
call npm install
popd
exit /b

:format
echo 🔧 Formatting code...
pushd core
..\%PYTHON% -m ruff format edge_mining/ tests/
popd
echo ✅ Code formatting complete!
goto :end

:lint
echo 🔍 Running linting checks...
pushd core
..\%PYTHON% -m ruff check edge_mining/
..\%PYTHON% -m mypy edge_mining/
..\%PYTHON% -m bandit -r edge_mining/ --skip B311,B104
popd
echo ✅ Linting complete!
goto :end

:lint-fix
echo 🔧 Running auto-fixable linting...
pushd core
..\%PYTHON% -m ruff check --fix edge_mining/
..\%PYTHON% -m ruff format edge_mining/
popd
echo ✅ Auto-fix complete!
goto :end

:test
echo 🧪 Running tests...
pushd core
..\%PYTHON% -m pytest tests/ -v
popd
echo ✅ Tests complete!
goto :end

:test-cov
echo 🧪 Running tests with coverage...
pushd core
..\%PYTHON% -m pytest tests/ -v --cov=edge_mining --cov-report=html --cov-report=term
popd
echo ✅ Tests with coverage complete!
goto :end

:pre-commit
echo 🔧 Running pre-commit hooks...
call :do_pre_commit
goto :end

:do_pre_commit
%PRE_COMMIT% run --all-files
exit /b

:pre-commit-install
call :do_pre_commit_install
goto :end

:do_pre_commit_install
echo 🔧 Installing pre-commit hooks...
%PRE_COMMIT% install
exit /b

:clean
echo 🧹 Cleaning cache and temporary files...
pushd core
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc *.pyo) do @if exist "%%f" del /q "%%f" 2>nul
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d" 2>nul
if exist build rd /s /q build 2>nul
if exist dist rd /s /q dist 2>nul
if exist .coverage del /q .coverage 2>nul
if exist htmlcov rd /s /q htmlcov 2>nul
if exist .pytest_cache rd /s /q .pytest_cache 2>nul
popd
if exist frontend\node_modules\.tmp rd /s /q frontend\node_modules\.tmp 2>nul
echo ✅ Cleanup complete!
goto :end

:build
echo 🐳 Building Docker image...
docker compose build
echo ✅ Docker build complete!
goto :end

:up
echo 🐳 Starting application...
docker compose up -d
echo ✅ Application started!
goto :end

:down
echo 🐳 Stopping application...
docker compose down
echo ✅ Application stopped!
goto :end

:restart
echo 🐳 Rebuilding and restarting application...
docker compose build
docker compose up -d
echo ✅ Application restarted!
goto :end

:logs
docker compose logs -f
goto :end

:end
