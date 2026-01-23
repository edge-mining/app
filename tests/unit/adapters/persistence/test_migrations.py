"""Test for Alembic migrations integration.

This test verifies that the migration system is properly integrated
with the application bootstrap and can run migrations successfully.
"""

import os
import tempfile
from pathlib import Path

import pytest

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.migrations import (
    check_current_revision,
    run_migrations,
)
from edge_mining.adapters.infrastructure.logging.terminal_logging import TerminalLogger


class TestMigrations:
    """Test suite for Alembic migrations."""

    @pytest.fixture
    def test_db_url(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db_url = f"sqlite:///{db_path}"
        yield db_url

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def logger(self):
        """Create a logger for testing."""
        return TerminalLogger(log_level="DEBUG")

    def test_run_migrations_from_scratch(self, test_db_url, logger):
        """Test that migrations can be applied to a fresh database."""
        # Check that no migrations have been applied yet
        current_rev = check_current_revision(test_db_url, logger)
        assert current_rev is None, "Fresh database should have no revision"

        # Run migrations
        run_migrations(test_db_url, logger)

        # Check that migrations were applied
        current_rev = check_current_revision(test_db_url, logger)
        assert current_rev is not None, "Database should have a revision after migrations"

    def test_migrations_idempotent(self, test_db_url, logger):
        """Test that running migrations multiple times is safe."""
        # Run migrations twice
        run_migrations(test_db_url, logger)
        rev1 = check_current_revision(test_db_url, logger)

        run_migrations(test_db_url, logger)
        rev2 = check_current_revision(test_db_url, logger)

        # Should be at the same revision
        assert rev1 == rev2, "Running migrations twice should result in same revision"

    def test_check_current_revision_handles_errors(self, logger):
        """Test that check_current_revision handles errors gracefully."""
        # Use invalid database URL
        invalid_url = "sqlite:///nonexistent/path/to/db.db"

        # Should not raise exception, just return None
        current_rev = check_current_revision(invalid_url, logger)
        assert current_rev is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
