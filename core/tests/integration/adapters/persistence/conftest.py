"""Shared fixtures for persistence integration tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from edge_mining.adapters.infrastructure.logging.terminal_logging import TerminalLogger
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.shared.logging.port import LoggerPort


@pytest.fixture
def logger() -> LoggerPort:
    """Create a logger for testing."""
    return TerminalLogger(log_level="DEBUG")


@pytest.fixture
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary database file path for testing.

    Yields:
        Path to a temporary database file that will be cleaned up after the test.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_db_url(test_db_path: str) -> str:
    """Create a SQLite database URL for testing.

    Args:
        test_db_path: Path to the temporary database file

    Returns:
        SQLite database URL string
    """
    return f"sqlite:///{test_db_path}"


@pytest.fixture
def sqlalchemy_repo(test_db_url: str, logger: LoggerPort) -> Generator[BaseSQLAlchemyRepository, None, None]:
    """Create a BaseSQLAlchemyRepository instance with migrations.

    Args:
        test_db_url: Database URL for testing
        logger: Logger instance

    Yields:
        Initialized BaseSQLAlchemyRepository instance
    """
    # Reset class-level shared resources for clean test
    BaseSQLAlchemyRepository._engine = None
    BaseSQLAlchemyRepository._SessionLocal = None

    repo = BaseSQLAlchemyRepository(
        db_path=test_db_url,
        logger=logger,
        run_migrations=True,
        backup_before_migration=False,  # No backup for test databases
    )

    # Initialize the database with migrations
    repo.initialize_database()

    yield repo

    # Cleanup: close any remaining connections
    if BaseSQLAlchemyRepository._engine:
        BaseSQLAlchemyRepository._engine.dispose()


@pytest.fixture
def sqlalchemy_repo_no_migrations(
    test_db_url: str, logger: LoggerPort
) -> Generator[BaseSQLAlchemyRepository, None, None]:
    """Create a BaseSQLAlchemyRepository instance without running migrations.

    Useful for testing migration behavior separately.

    Args:
        test_db_url: Database URL for testing
        logger: Logger instance

    Yields:
        BaseSQLAlchemyRepository instance (not yet initialized)
    """
    # Reset class-level shared resources for clean test
    BaseSQLAlchemyRepository._engine = None
    BaseSQLAlchemyRepository._SessionLocal = None

    repo = BaseSQLAlchemyRepository(
        db_path=test_db_url,
        logger=logger,
        run_migrations=False,
        backup_before_migration=False,
    )

    yield repo

    # Cleanup
    if BaseSQLAlchemyRepository._engine:
        BaseSQLAlchemyRepository._engine.dispose()
