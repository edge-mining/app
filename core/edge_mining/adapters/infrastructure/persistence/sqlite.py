"""
This module contains the BaseSqliteRepository class, which is the base class for all SQLite repositories.
It provides a base implementation for creating tables and getting connections to the SQLite database.
"""

import sqlite3
import uuid

from edge_mining.shared.logging.port import LoggerPort

# Register an adapter and a converter
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))
# sqlite3.register_converter("UUID", lambda u: uuid.UUID(u.decode("utf-8")))


class BaseSqliteRepository:
    """Base class for SQLite repositories.

    This class provides centralized database schema versioning.
    Increment CURRENT_DB_VERSION when making ANY schema changes across the application.
    """

    # Global database schema version
    CURRENT_DB_VERSION = "1.1.0"

    def __init__(self, db_path: str, logger: LoggerPort):
        self.db_path = db_path
        self.logger = logger
        self._ensure_schema_migrations_table()

    def get_connection(self):
        """Obtain a database connection."""
        try:
            # We set a timeout for blocking operations
            conn = sqlite3.connect(self.db_path, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.row_factory = sqlite3.Row  # Accessing columns by name
            conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign keys if used

            return conn
        except sqlite3.Error as e:
            self.logger.error(f"SQLite DB connection error ({self.db_path}): {e}")
            raise ConnectionError(f"SQLite Connection Error: {e}") from e

    def _ensure_schema_migrations_table(self):
        """Create the schema_migrations table if it does not exist."""
        self.logger.debug(f"Ensuring schema_migrations table exists in {self.db_path}...")
        sql = """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        conn = self.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                self.logger.debug("schema_migrations table checked/created successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating schema_migrations table: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_table_columns(self, table_name: str) -> set:
        """Get the set of column names for a given table."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = {row[1] for row in cursor.fetchall()}  # row[1] is column name
            return columns
        except sqlite3.Error as e:
            self.logger.error(f"Error getting columns for table {table_name}: {e}")
            return set()
        finally:
            if conn:
                conn.close()

    def add_column_safe(self, table_name: str, column_name: str, column_def: str):
        """Safely add a column to a table if it doesn't exist."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
            with conn:
                cursor.execute(alter_sql)
            self.logger.info(f"Successfully added column '{column_name}' to table '{table_name}'")
        except sqlite3.Error as e:
            self.logger.error(f"Error adding column {column_name} to {table_name}: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _schema_to_create_table(self, table_name: str, schema: dict[str, str]) -> str:
        """Generate CREATE TABLE SQL from schema dictionary.

        Args:
            table_name: Name of the table
            schema: Dictionary mapping column names to their SQL definitions

        Returns:
            str: Complete CREATE TABLE IF NOT EXISTS SQL statement
        """
        columns_def = []
        for col_name, col_def in schema.items():
            columns_def.append(f"    {col_name} {col_def}")

        columns_sql = ",\n".join(columns_def)

        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n{columns_sql}\n);"

    def get_current_db_version(self) -> str | None:
        """Get the current global database schema version.

        Returns:
            str | None: Current version string (e.g., "1.1.0") or None if no migrations applied
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_migrations ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            self.logger.error(f"Error getting current database version: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def apply_migration(self, version: str, description: str) -> None:
        """Apply a new migration version to the database.

        Args:
            version: Version string (e.g., "1.1.0")
            description: Human-readable description of changes in this version

        Raises:
            sqlite3.IntegrityError: If version already exists
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            with conn:
                cursor.execute(
                    """
                    INSERT INTO schema_migrations (version, description, applied_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (version, description),
                )
            self.logger.info(f"Applied database migration version {version}: {description}")
        except sqlite3.IntegrityError:
            # Version already exists - this is expected if migration was already applied
            self.logger.debug(f"Migration version {version} already applied, skipping")
        except sqlite3.Error as e:
            self.logger.error(f"Error applying migration version {version}: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def is_migration_applied(self, version: str) -> bool:
        """Check if a specific migration version has been applied.

        Args:
            version: Version string to check (e.g., "1.1.0")

        Returns:
            bool: True if version exists in migrations history
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM schema_migrations WHERE version = ?",
                (version,),
            )
            row = cursor.fetchone()
            count: int = row[0] if row else 0
            return count > 0
        except sqlite3.Error as e:
            self.logger.error(f"Error checking migration version {version}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def migrate_schema_if_needed(
        self,
        table_name: str,
        expected_schema: dict[str, str],
        target_version: str,
        migration_description: str,
        table_was_created: bool = False,
    ) -> None:
        """Smart auto-migration: adds missing columns, warns about extra ones.

        This method checks if a migration is needed and applies it using global database versioning.
        It only applies the migration if the target version hasn't been applied yet.

        Args:
            table_name: Name of the table to migrate
            expected_schema: Dictionary mapping column names to their SQL definitions
            target_version: Global database version this migration targets (e.g., "1.1.0")
            migration_description: Human-readable description of changes
            table_was_created: True if table was just created (not existing before)
        """
        # Check if this migration version was already applied
        if self.is_migration_applied(target_version):
            self.logger.debug(f"Migration {target_version} already applied, skipping schema check for '{table_name}'")
            return

        self.logger.debug(f"Checking if schema migration is needed for '{table_name}' table...")

        current_columns = self.get_table_columns(table_name)
        expected_column_names = set(expected_schema.keys())

        # SAFE OPERATION: Add missing columns
        missing_columns = expected_column_names - current_columns
        if missing_columns:
            self.logger.info(f"Missing columns detected in '{table_name}' table: {missing_columns}")
            for col_name in missing_columns:
                col_def = expected_schema[col_name]
                # Remove PRIMARY KEY constraint for ALTER TABLE (not allowed)
                if "PRIMARY KEY" in col_def:
                    self.logger.warning(
                        f"Cannot add PRIMARY KEY column '{col_name}' to existing table. Manual migration required."
                    )
                    continue
                self.add_column_safe(table_name, col_name, col_def)

        # Apply migration if changes were made OR if table was just created
        if missing_columns or table_was_created:
            self.apply_migration(target_version, migration_description)

        # WARNING: Extra columns (potential schema drift)
        extra_columns = current_columns - expected_column_names
        if extra_columns:
            self.logger.warning(
                f"Database table '{table_name}' has unexpected columns: {extra_columns}. "
                f"These columns are not defined in the current schema. "
                f"Manual migration or cleanup may be required. "
                f"No automatic removal will be performed to prevent data loss."
            )

        if not missing_columns and not extra_columns and not table_was_created:
            self.logger.debug(f"Schema for '{table_name}' table is up to date.")

    def create_tables(
        self,
        table_name: str,
        schema: dict[str, str],
    ) -> None:
        """Create tables from schema definition and apply migrations.

        Uses the global CURRENT_DB_VERSION from the class for versioning.
        Automatically generates CREATE TABLE SQL from the schema dictionary.

        Args:
            table_name: Name of the table to create
            schema: Dictionary mapping column names to their SQL definitions (with inline comments)
        """
        self.logger.debug(f"Ensuring SQLite tables exist in {self.db_path}...")

        # Generate CREATE TABLE SQL from schema
        create_table_sql = self._schema_to_create_table(table_name, schema)

        conn = self.get_connection()
        table_existed = False
        try:
            cursor = conn.cursor()
            # Check if table exists before creation
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            table_existed = cursor.fetchone() is not None

            with conn:
                cursor.execute(create_table_sql)

                table_display_name = table_name.replace("_", " ").capitalize()
                self.logger.debug(f"{table_display_name} table checked/created successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating SQLite tables: {e}")
            from edge_mining.domain.exceptions import ConfigurationError

            raise ConfigurationError(f"DB error creating tables: {e}") from e
        finally:
            if conn:
                conn.close()

        # Auto-generate migration description based on table status
        migration_description = f"Schema version {self.CURRENT_DB_VERSION} for {table_name} table"

        # Apply smart auto-migration after table creation
        self.migrate_schema_if_needed(
            table_name=table_name,
            expected_schema=schema,
            target_version=self.CURRENT_DB_VERSION,
            migration_description=migration_description,
            table_was_created=not table_existed,
        )
