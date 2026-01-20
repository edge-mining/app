"""Database configuration and session management for SQLAlchemy.

This module provides centralized SQLAlchemy configuration similar to BaseSqliteRepository.
It manages the database engine, session factory, metadata, and a shared mapper registry
for imperative mapping of domain entities.
"""

from typing import Generator, Optional

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import Session, registry, sessionmaker

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
    ):
        """Initialize the SQLAlchemy repository base.

        Args:
            db_path: Database path/URL. If None, uses DATABASE_URL env var or default SQLite path
            logger: Logger instance for logging database operations
            echo: If True, SQLAlchemy will log all SQL statements
        """
        self.logger = logger
        self.db_path = db_path

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
        BaseSQLAlchemyRepository._SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
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

    def create_all_tables(self) -> None:
        """Create all tables defined in the metadata.

        This method is idempotent and safe to call multiple times.
        It uses SQLAlchemy's create_all() which only creates tables that don't exist.

        Note:
            For production, use Alembic migrations instead.
            This method should be called after all table definitions are loaded.
        """
        if self.logger:
            self.logger.info("Creating database tables (if not exist)...")

        if BaseSQLAlchemyRepository._engine is None:
            raise RuntimeError("Engine not initialized.")

        # create_all() is idempotent - only creates tables that don't exist
        metadata.create_all(bind=BaseSQLAlchemyRepository._engine)

        if self.logger:
            self.logger.info("Database tables ready")
