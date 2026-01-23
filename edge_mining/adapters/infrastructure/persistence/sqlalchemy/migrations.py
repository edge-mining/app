"""Alembic migrations management for SQLAlchemy.

This module provides functions to run Alembic migrations programmatically,
maintaining DDD and hexagonal architecture principles by keeping migration
logic separate from domain logic.

The migrations are run automatically during application startup when using
SQLAlchemy as the persistence adapter.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy import create_engine

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from edge_mining.shared.logging.port import LoggerPort


def _find_project_root() -> Path:
    """Find project root by looking for alembic.ini marker file.

    This method walks up the directory tree from the current file until it finds
    a directory containing alembic.ini, which marks the project root.

    Returns:
        Path to the project root directory

    Raises:
        FileNotFoundError: If alembic.ini cannot be found in any parent directory
    """
    current_path = Path(__file__).resolve()

    # Walk up the directory tree
    for parent in [current_path] + list(current_path.parents):
        alembic_ini = parent / "alembic.ini"
        if alembic_ini.exists():
            return parent

    # If we get here, we couldn't find the project root
    raise FileNotFoundError(
        "Could not find project root (alembic.ini not found in any parent directory). "
        "Make sure alembic.ini exists at the project root."
    )


def backup_database(db_url: str, logger: Optional[LoggerPort] = None) -> Optional[str]:
    """Create a backup of the SQLite database file before migrations.

    Args:
        db_url: Database URL (currently only SQLite is supported)
        logger: Logger instance for logging backup operations

    Returns:
        Path to the backup file if created, None if backup was not needed or failed

    Note:
        Only SQLite databases are backed up. For other database types,
        this function returns None and logs a warning.
    """
    # Only backup SQLite databases
    if not db_url.startswith("sqlite"):
        if logger:
            logger.warning("Database backup is only supported for SQLite databases")
        return None

    try:
        # Parse the SQLite database path from the URL
        # Format: sqlite:///path/to/file.db or sqlite:///./relative/path.db
        parsed = urlparse(db_url)
        db_path = parsed.path

        # Remove leading slash for absolute paths on Unix, but keep for relative paths
        if db_path.startswith("/") and not db_path.startswith("///"):
            db_path = db_path[1:]

        db_file = Path(db_path)

        # Check if database file exists
        if not db_file.exists():
            if logger:
                logger.debug(f"Database file does not exist yet: {db_file}. Skipping backup.")
            return None

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = db_file.parent / f"{db_file.stem}_backup_{timestamp}{db_file.suffix}"

        # Copy the database file
        shutil.copy2(db_file, backup_file)

        if logger:
            logger.info(f"Database backed up to: {backup_file}")

        return str(backup_file)

    except Exception as e:
        if logger:
            logger.error(f"Failed to create database backup: {e}")
        # Don't raise - backup failure should not prevent migrations
        return None


def get_alembic_config(db_url: str, script_location: Optional[str] = None) -> Config:
    """Create and configure an Alembic Config object.

    Args:
        db_url: Database URL for SQLAlchemy connection
        script_location: Path to alembic directory. If None, uses default location

    Returns:
        Configured Alembic Config object
    """
    # Determine alembic directory location
    if script_location is None:
        # Find project root by looking for alembic.ini
        project_root = _find_project_root()
        script_location = str(project_root / "alembic")
        alembic_ini_path = str(project_root / "alembic.ini")
    else:
        # If script_location is provided, assume alembic.ini is in the parent directory
        alembic_ini_path = str(Path(script_location).parent / "alembic.ini")

    # Verify paths exist
    if not Path(script_location).exists():
        raise FileNotFoundError(f"Alembic script location not found: {script_location}")
    if not Path(alembic_ini_path).exists():
        raise FileNotFoundError(f"Alembic configuration file not found: {alembic_ini_path}")

    # Create Alembic config
    alembic_cfg = Config(alembic_ini_path)

    # Override database URL from settings
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    alembic_cfg.set_main_option("script_location", script_location)

    return alembic_cfg


def run_migrations(
    db_url: str,
    logger: Optional[LoggerPort] = None,
    script_location: Optional[str] = None,
    backup_enabled: bool = True,
) -> None:
    """Run Alembic migrations to upgrade database to the latest revision.

    This function checks if there are pending migrations and only runs them
    if the database is not already at the latest revision.

    Args:
        db_url: Database URL for SQLAlchemy connection
        logger: Logger instance for logging migration operations
        script_location: Path to alembic directory. If None, uses default location
        backup_enabled: If True, create a backup of SQLite database before migrations

    Raises:
        Exception: If migrations fail to execute
    """
    # Check if there are pending migrations
    if not has_pending_migrations(db_url, logger, script_location):
        if logger:
            logger.info("Database is already up to date - no migrations needed")
        return

    if logger:
        logger.info("Pending migrations detected - starting migration process...")

    # Create database backup if enabled (only when migrations will actually run)
    if backup_enabled:
        backup_database(db_url, logger)

    try:
        alembic_cfg = get_alembic_config(db_url, script_location)

        # Run migrations to head (latest revision)
        command.upgrade(alembic_cfg, "head")

        if logger:
            logger.info("Alembic migrations completed successfully")

    except Exception as e:
        if logger:
            logger.error(f"Error running Alembic migrations: {e}")
        raise


def check_current_revision(
    db_url: str,
    logger: Optional[LoggerPort] = None,
    script_location: Optional[str] = None,
) -> Optional[str]:
    """Check the current database revision.

    Args:
        db_url: Database URL for SQLAlchemy connection
        logger: Logger instance for logging
        script_location: Path to alembic directory. If None, uses default location

    Returns:
        Current revision ID or None if no migrations have been applied
    """
    try:
        # Get current revision by connecting directly to the database
        # Note: This returns None if no migrations have been applied
        engine = create_engine(db_url)
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

            if logger:
                if current_rev:
                    logger.debug(f"Current database revision: {current_rev}")
                else:
                    logger.debug("No migrations have been applied yet")

            return current_rev

    except Exception as e:
        if logger:
            logger.warning(f"Could not check current revision: {e}")
        return None


def has_pending_migrations(
    db_url: str,
    logger: Optional[LoggerPort] = None,
    script_location: Optional[str] = None,
) -> bool:
    """Check if there are pending migrations to apply.

    Args:
        db_url: Database URL for SQLAlchemy connection
        logger: Logger instance for logging
        script_location: Path to alembic directory. If None, uses default location

    Returns:
        True if there are pending migrations, False otherwise
    """
    try:
        alembic_cfg = get_alembic_config(db_url, script_location)
        script = ScriptDirectory.from_config(alembic_cfg)

        # Get current database revision
        current_rev = check_current_revision(db_url, logger, script_location)

        # Get head (latest) revision from migration scripts
        head_rev = script.get_current_head()

        # If current is None, database needs initialization (migrations pending)
        if current_rev is None:
            if logger:
                logger.debug("Database not initialized - migrations pending")
            return True

        # If current revision differs from head, migrations are pending
        if current_rev != head_rev:
            if logger:
                logger.debug(f"Migrations pending: current={current_rev}, head={head_rev}")
            return True

        if logger:
            logger.debug("Database is up to date - no pending migrations")
        return False

    except Exception as e:
        if logger:
            logger.warning(f"Could not check for pending migrations: {e}")
        # If we can't determine, assume migrations might be needed
        return True


def create_migration(
    db_url: str,
    message: str,
    logger: Optional[LoggerPort] = None,
    script_location: Optional[str] = None,
    autogenerate: bool = True,
) -> None:
    """Create a new Alembic migration script.

    This is typically used during development when schema changes are made.
    Not recommended for automatic execution during application startup.

    Args:
        db_url: Database URL for SQLAlchemy connection
        message: Migration message/description
        logger: Logger instance for logging
        script_location: Path to alembic directory. If None, uses default location
        autogenerate: Whether to auto-generate migration from model changes

    Raises:
        Exception: If migration creation fails
    """
    if logger:
        logger.info(f"Creating new migration: {message}")

    try:
        alembic_cfg = get_alembic_config(db_url, script_location)

        # Create new migration
        command.revision(
            alembic_cfg,
            message=message,
            autogenerate=autogenerate,
        )

        if logger:
            logger.info(f"Migration '{message}' created successfully")

    except Exception as e:
        if logger:
            logger.error(f"Error creating migration: {e}")
        raise


def downgrade_migration(
    db_url: str,
    revision: str = "-1",
    logger: Optional[LoggerPort] = None,
    script_location: Optional[str] = None,
) -> None:
    """Downgrade database to a specific revision.

    Args:
        db_url: Database URL for SQLAlchemy connection
        revision: Target revision (default: -1 for previous revision)
        logger: Logger instance for logging
        script_location: Path to alembic directory. If None, uses default location

    Raises:
        Exception: If downgrade fails
    """
    if logger:
        logger.warning(f"Downgrading database to revision: {revision}")

    try:
        alembic_cfg = get_alembic_config(db_url, script_location)

        # Downgrade to specified revision
        command.downgrade(alembic_cfg, revision)

        if logger:
            logger.info("Database downgrade completed successfully")

    except Exception as e:
        if logger:
            logger.error(f"Error downgrading database: {e}")
        raise
