"""Database configuration and session management for SQLAlchemy.

This module provides centralized SQLAlchemy configuration similar to BaseSqliteRepository.
It manages the database engine, session factory, metadata, and a shared mapper registry
for imperative mapping of domain entities.

The BaseSQLAlchemyRepository class handles:
- Engine and session factory creation
- Database schema initialization (migrations + table creation)
- Shared metadata and mapper registry management
"""

from typing import Generator, Optional

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import Session, registry, sessionmaker

# Import registry_loader at module level to ensure all table definitions are registered
# This must happen before any migration or table creation operations
from edge_mining.adapters.infrastructure.persistence.sqlalchemy import registry_loader  # noqa: F401
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.migrations import run_migrations
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.shared.logging.port import LoggerPort


class BaseSQLAlchemyRepository:
    """Base class for SQLAlchemy repositories.

    This class provides centralized database configuration and session management,
    similar to BaseSqliteRepository. It creates a single engine, session factory,
    and shared mapper registry for imperative mapping.

    Attributes:
        db_path: Path to the database file (for SQLite) or database URL
        logger: Logger instance for logging database operations
        echo: If True, SQLAlchemy will log all SQL statements
    """

    # Shared resources
    _engine: Optional[Engine] = None
    _SessionLocal = None

    def __init__(
        self,
        db_path: str,
        logger: Optional[LoggerPort] = None,
        echo: bool = False,
        run_migrations: bool = True,
        backup_before_migration: bool = True,
    ):
        """Initialize the SQLAlchemy repository base.

        Args:
            db_path: Database path/URL. If None, uses DATABASE_URL env var or default SQLite path
            logger: Logger instance for logging database operations
            echo: If True, SQLAlchemy will log all SQL statements
            run_migrations: If True, automatically run Alembic migrations
            backup_before_migration: If True, create database backup before running migrations
        """
        self.logger = logger
        self.db_path = db_path
        self.run_migrations = run_migrations
        self.backup_before_migration = backup_before_migration

        # Initialize shared resources if not already initialized
        if BaseSQLAlchemyRepository._engine is None:
            self._initialize_shared_resources(echo)

    def _initialize_shared_resources(self, echo: bool = False) -> None:
        """Initialize shared database resources (engine, session factory, metadata, registry).

        Args:
            echo: If True, SQLAlchemy will log all SQL statements
        """
        if self.logger:
            self.logger.debug(f"Initializing SQLAlchemy with database: {self.db_path}")

        # Create engine with appropriate settings
        connect_args = {}
        if self.db_path.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        BaseSQLAlchemyRepository._engine = create_engine(
            self.db_path,
            connect_args=connect_args,
            echo=echo,
        )

        # Create session factory
        # expire_on_commit=False prevents attributes from being marked as expired
        # after commit, allowing detached objects to retain their values
        BaseSQLAlchemyRepository._SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=BaseSQLAlchemyRepository._engine,
        )

        if self.logger:
            self.logger.info("SQLAlchemy initialized successfully")

    @classmethod
    def get_mapper_registry(cls) -> registry:
        """Get the shared mapper registry for imperative mappings.

        Returns:
            Shared registry instance for mapping domain entities to tables
        """
        return mapper_registry

    @classmethod
    def get_metadata(cls) -> MetaData:
        """Get the shared metadata instance for table definitions.

        Returns:
            Shared MetaData instance
        """
        return metadata

    @classmethod
    def get_engine(cls) -> Engine:
        """Get the shared SQLAlchemy engine.

        Returns:
            SQLAlchemy Engine instance
        """
        if cls._engine is None:
            raise RuntimeError("Engine not initialized. Create a BaseSQLAlchemyRepository instance first.")
        return cls._engine

    def get_session(self) -> Session:
        """Create a new database session.

        Returns:
            New SQLAlchemy Session instance

        Note:
            Caller is responsible for closing the session
        """
        if BaseSQLAlchemyRepository._SessionLocal is None:
            raise RuntimeError("Session factory not initialized.")
        return BaseSQLAlchemyRepository._SessionLocal()

    def get_db(self) -> Generator[Session, None, None]:
        """Dependency injection helper for database sessions.

        Yields:
            Session: SQLAlchemy database session

        Usage:
            Can be used with FastAPI's Depends() or manually in application layer.
        """
        session = self.get_session()
        try:
            yield session
        finally:
            session.close()

    def initialize_database(self) -> None:
        """Initialize database schema using Alembic migrations.

        This method handles the complete database initialization workflow:
        1. Imports all table definitions (via registry_loader imported at module level)
        2. Runs Alembic migrations to create/update the database schema
        3. Validates data integrity

        Database schema creation is EXCLUSIVELY managed through Alembic migrations:
        - On first run: Alembic creates the database and applies the initial migration
        - On subsequent runs: Alembic applies only pending migrations
        - All schema changes (new tables, columns, indexes, etc.) must be done via migrations

        If migrations are disabled (run_migrations=False), the database must be
        initialized manually using: alembic upgrade head

        Raises:
            RuntimeError: If engine is not initialized or no migrations are found
            Exception: If migrations fail to execute
        """
        if self.logger:
            self.logger.debug("Initializing database schema...")

        # Run Alembic migrations if enabled
        if self.run_migrations:
            if self.logger:
                self.logger.info("Running Alembic migrations...")

            try:
                run_migrations(
                    db_url=self.db_path,
                    logger=self.logger,
                    backup_enabled=self.backup_before_migration,
                )

                if self.logger:
                    self.logger.info("Database initialization complete")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to run migrations: {e}")
                raise
        else:
            if self.logger:
                self.logger.warning(
                    "Automatic migrations disabled. Database must be initialized manually with: alembic upgrade head"
                )

        # Validate data integrity after migrations
        self._cleanup_unknown_miner_features()

    def _cleanup_unknown_miner_features(self) -> None:
        """Remove miner_features rows whose feature_type is not in MinerFeatureType.

        This handles the case where feature types were renamed or removed between
        application versions, preventing load errors at runtime.
        """
        from sqlalchemy import select

        from edge_mining.adapters.domain.miner.tables import miner_features_table
        from edge_mining.domain.miner.common import MinerFeatureType

        valid_types = {ft.value for ft in MinerFeatureType}

        try:
            session = self.get_session()
            try:
                rows = session.execute(
                    select(
                        miner_features_table.c.id,
                        miner_features_table.c.feature_type,
                        miner_features_table.c.miner_id,
                    )
                ).fetchall()

                unknown_rows = [r for r in rows if r.feature_type not in valid_types]

                if not unknown_rows:
                    return

                unknown_ids = [r.id for r in unknown_rows]
                unknown_descriptions = [
                    f"feature_type='{r.feature_type}' (miner_id={r.miner_id})" for r in unknown_rows
                ]

                if self.logger:
                    self.logger.warning(
                        f"Found {len(unknown_rows)} miner feature(s) with unknown type, removing: "
                        + ", ".join(unknown_descriptions)
                    )

                session.execute(miner_features_table.delete().where(miner_features_table.c.id.in_(unknown_ids)))
                session.commit()

                if self.logger:
                    self.logger.info(f"Removed {len(unknown_ids)} obsolete miner feature(s) from database.")
            except Exception as e:
                session.rollback()
                if self.logger:
                    self.logger.error(f"Failed to clean up unknown miner features: {e}")
            finally:
                session.close()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to clean up unknown miner features: {e}")
