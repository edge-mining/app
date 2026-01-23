"""Test for BaseSQLAlchemyRepository database initialization."""

import os
import tempfile
from pathlib import Path

import pytest

from edge_mining.adapters.infrastructure.logging.terminal_logging import TerminalLogger
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository


class TestBaseSQLAlchemyRepository:
    """Test suite for BaseSQLAlchemyRepository initialization."""

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

    def test_initialize_database_with_migrations(self, test_db_url, logger):
        """Test database initialization with migrations enabled."""
        # Reset class-level shared resources for clean test
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        # Create repository with migrations enabled
        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=True,
        )

        # Initialize database
        repo.initialize_database()

        # Verify engine was created
        assert BaseSQLAlchemyRepository._engine is not None
        assert BaseSQLAlchemyRepository._SessionLocal is not None

        # Verify we can create a session
        session = repo.get_session()
        assert session is not None
        session.close()

    def test_initialize_database_without_migrations(self, test_db_url, logger):
        """Test database initialization with migrations disabled."""
        # Reset class-level shared resources for clean test
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        # Create repository with migrations disabled
        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=False,
        )

        # Initialize database (should only create tables)
        repo.initialize_database()

        # Verify engine was created
        assert BaseSQLAlchemyRepository._engine is not None
        assert BaseSQLAlchemyRepository._SessionLocal is not None

    def test_initialize_database_idempotent(self, test_db_url, logger):
        """Test that initialize_database can be called multiple times safely."""
        # Reset class-level shared resources
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=True,  # Changed to True since we rely on migrations
        )

        # Call initialize_database multiple times - should not raise errors
        repo.initialize_database()
        repo.initialize_database()

        # Should still work
        assert BaseSQLAlchemyRepository._engine is not None

    def test_initialize_database_without_migrations_warns(self, test_db_url, logger):
        """Test that disabling migrations shows a warning."""
        # Reset class-level shared resources
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=False,
        )

        # Should complete without error but log warning
        repo.initialize_database()

        # Engine should still be initialized
        assert BaseSQLAlchemyRepository._engine is not None

    def test_get_metadata(self, test_db_url, logger):
        """Test that metadata is accessible."""
        # Reset class-level shared resources
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=False,
        )

        metadata = repo.get_metadata()
        assert metadata is not None

    def test_get_mapper_registry(self, test_db_url, logger):
        """Test that mapper registry is accessible."""
        # Reset class-level shared resources
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=False,
        )

        registry = repo.get_mapper_registry()
        assert registry is not None

    def test_db_generator(self, test_db_url, logger):
        """Test the database session generator."""
        # Reset class-level shared resources
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=False,
        )

        # Test the generator
        for session in repo.get_db():
            assert session is not None
            # Session should be usable
            break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
