"""Alembic migrations management for SQLAlchemy.

This module provides functions to run Alembic migrations programmatically,
maintaining DDD and hexagonal architecture principles by keeping migration
logic separate from domain logic.

The migrations are run automatically during application startup when using
SQLAlchemy as the persistence adapter.
"""

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
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
) -> None:
    """Run Alembic migrations to upgrade database to the latest revision.

    This function runs all pending migrations to bring the database schema
    up to date with the current application version.

    Args:
        db_url: Database URL for SQLAlchemy connection
        logger: Logger instance for logging migration operations
        script_location: Path to alembic directory. If None, uses default location

    Raises:
        Exception: If migrations fail to execute
    """
    if logger:
        logger.info("Running Alembic migrations...")

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
