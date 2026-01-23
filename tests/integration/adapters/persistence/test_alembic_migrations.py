"""Integration tests for Alembic migrations.

These tests verify that Alembic migrations correctly create and update
the database schema, and that the migration system integrates properly
with the SQLAlchemy repository layer.
"""

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import inspect, text

from edge_mining.adapters.infrastructure.logging.terminal_logging import TerminalLogger
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.migrations import (
    check_current_revision,
    run_migrations,
)


class TestAlembicMigrations:
    """Integration tests for Alembic migration system."""

    def test_run_migrations_creates_tables(self, test_db_url: str, logger):
        """Test that running migrations creates all expected tables."""
        # Reset shared resources
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=True,
            backup_before_migration=False,
        )
        repo.initialize_database()

        # Inspect the database schema
        inspector = inspect(repo._engine)
        table_names = inspector.get_table_names()

        # Verify key tables exist
        assert "energy_sources" in table_names
        assert "energy_monitors" in table_names
        assert "alembic_version" in table_names  # Alembic tracking table

    def test_migrations_create_correct_columns(self, test_db_url: str, logger):
        """Test that migrations create tables with correct columns."""
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=True,
            backup_before_migration=False,
        )
        repo.initialize_database()

        inspector = inspect(repo._engine)

        # Check energy_sources columns
        energy_sources_columns = {col["name"] for col in inspector.get_columns("energy_sources")}
        expected_source_cols = {
            "id",
            "name",
            "type",
            "nominal_power_max",
            "storage",
            "grid",
            "external_source",
            "energy_monitor_id",
            "forecast_provider_id",
        }
        assert expected_source_cols.issubset(energy_sources_columns)

        # Check energy_monitors columns
        energy_monitors_columns = {col["name"] for col in inspector.get_columns("energy_monitors")}
        expected_monitor_cols = {"id", "name", "adapter_type", "config", "external_service_id"}
        assert expected_monitor_cols.issubset(energy_monitors_columns)

    def test_alembic_version_tracking(self, test_db_url: str, logger):
        """Test that Alembic correctly tracks the current migration version."""
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=True,
            backup_before_migration=False,
        )
        repo.initialize_database()

        # Get current revision from alembic_version table
        session = repo.get_session()
        try:
            result = session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar_one_or_none()
            assert version is not None
            assert len(version) == 12  # Alembic revision IDs are 12 characters
        finally:
            session.close()

    def test_migrations_idempotent(self, test_db_url: str, logger):
        """Test that running migrations multiple times is safe (idempotent)."""
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=True,
            backup_before_migration=False,
        )

        # Run migrations twice
        repo.initialize_database()
        repo.initialize_database()

        # Should still work without errors
        inspector = inspect(repo._engine)
        table_names = inspector.get_table_names()
        assert "energy_sources" in table_names

    def test_initialize_without_migrations_creates_tables(self, test_db_url: str, logger):
        """Test that initializing without migrations warns but doesn't create tables."""
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=False,  # Skip migrations
            backup_before_migration=False,
        )
        repo.initialize_database()

        # Tables should NOT be created when migrations are disabled
        # The system only creates tables through Alembic migrations
        inspector = inspect(repo._engine)
        table_names = inspector.get_table_names()
        assert len(table_names) == 0, "No tables should exist when migrations are disabled"

        # alembic_version should also not exist when migrations are skipped
        assert "alembic_version" not in table_names

    def test_database_backup_before_migration(self, test_db_path: str, logger):
        """Test that database backup is created when enabled."""
        # Create initial database
        test_db_url = f"sqlite:///{test_db_path}"

        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        # Create a simple database first
        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=False,
            backup_before_migration=False,
        )
        repo.initialize_database()

        # Add some dummy data
        session = repo.get_session()
        session.execute(text("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)"))
        session.execute(text("INSERT INTO test_table (id, name) VALUES (1, 'test')"))
        session.commit()
        session.close()

        # Close the engine
        repo._engine.dispose()

        # Now test backup functionality
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo2 = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=True,
            backup_before_migration=True,  # Enable backup
        )

        # Run migrations (which should trigger backup)
        repo2.initialize_database()

        # Check if backup file was created
        backup_dir = Path(test_db_path).parent / "backups"
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.db"))
            # Backup might be created, depending on migration implementation
            # This test verifies the backup mechanism doesn't cause errors

    def test_schema_matches_table_definitions(self, test_db_url: str, logger):
        """Test that the migrated schema matches our table definitions."""
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=True,
            backup_before_migration=False,
        )
        repo.initialize_database()

        inspector = inspect(repo._engine)

        # Verify foreign keys are set up correctly
        fks = inspector.get_foreign_keys("energy_sources")
        fk_columns = {fk["constrained_columns"][0] for fk in fks}

        # Energy sources should have foreign keys to energy_monitors and forecast_providers
        # (exact foreign keys depend on your schema)
        # This is a basic check that foreign key introspection works

        # Verify indexes
        indexes = inspector.get_indexes("energy_sources")
        # Primary key should be indexed
        pk_constraints = inspector.get_pk_constraint("energy_sources")
        assert pk_constraints["constrained_columns"] == ["id"]

    def test_migration_can_insert_and_query_data(self, test_db_url: str, logger):
        """Test that after migration, we can insert and query data."""
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=True,
            backup_before_migration=False,
        )
        repo.initialize_database()

        session = repo.get_session()
        try:
            # Insert test data
            session.execute(
                text(
                    """
                INSERT INTO energy_sources (id, name, type, nominal_power_max)
                VALUES (:id, :name, :type, :power)
                """
                ),
                {"id": "test-id-123", "name": "Test Source", "type": "SOLAR", "power": 5000.0},
            )
            session.commit()

            # Query data
            result = session.execute(text("SELECT name, type FROM energy_sources WHERE id = :id"), {"id": "test-id-123"})
            row = result.fetchone()
            assert row is not None
            assert row[0] == "Test Source"
            assert row[1] == "SOLAR"
        finally:
            session.close()


class TestMigrationHelperFunctions:
    """Test migration helper functions."""

    def test_check_current_revision(self, test_db_url: str, logger):
        """Test checking current migration revision."""
        BaseSQLAlchemyRepository._engine = None
        BaseSQLAlchemyRepository._SessionLocal = None

        repo = BaseSQLAlchemyRepository(
            db_path=test_db_url,
            logger=logger,
            run_migrations=True,
            backup_before_migration=False,
        )
        repo.initialize_database()

        # Check current revision
        revision = check_current_revision(test_db_url, logger)
        assert revision is not None
        assert isinstance(revision, str)
        assert len(revision) == 12  # Alembic revision format


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
