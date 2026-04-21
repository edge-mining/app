"""Repositories for Notification Domain."""

import json
import sqlite3
from typing import List, Optional

from sqlalchemy import select

from edge_mining.adapters.domain.notification.tables import notifiers_table
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.adapters.infrastructure.persistence.sqlite import BaseSqliteRepository
from edge_mining.domain.common import EntityId
from edge_mining.domain.exceptions import ConfigurationError
from edge_mining.domain.notification.common import NotificationAdapter
from edge_mining.domain.notification.entities import Notifier
from edge_mining.domain.notification.exceptions import (
    NotifierAlreadyExistsError,
    NotifierConfigurationError,
    NotifierError,
    NotifierNotFoundError,
)
from edge_mining.domain.notification.ports import NotifierRepository
from edge_mining.shared.adapter_maps.notification import NOTIFIER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import NotificationConfig

# Simple In-Memory implementation for testing and basic use


class InMemoryNotifierRepository(NotifierRepository):
    """In-memory implementation of NotifierRepository for testing purposes."""

    def __init__(self):
        self._notifiers: List[Notifier] = []

    def add(self, notifier: Notifier) -> None:
        self._notifiers.append(notifier)

    def get_by_id(self, notifier_id: EntityId) -> Optional[Notifier]:
        for notifier in self._notifiers:
            if notifier.id == notifier_id:
                return notifier
        return None

    def get_all(self) -> List[Notifier]:
        return self._notifiers

    def update(self, notifier: Notifier) -> None:
        for i, existing_notifier in enumerate(self._notifiers):
            if existing_notifier.id == notifier.id:
                self._notifiers[i] = notifier
                return

    def remove(self, notifier_id: EntityId) -> None:
        self._notifiers = [n for n in self._notifiers if n.id != notifier_id]

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[Notifier]:
        """Retrieve a list of notifiers by their associated external service ID."""
        return [n for n in self._notifiers if n.external_service_id == external_service_id]


class SqliteNotifierRepository(NotifierRepository):
    """SQLite implementation of NotifierRepository."""

    def __init__(self, db: BaseSqliteRepository):
        self._db = db
        self.logger = db.logger

        self._create_tables()

    def _create_tables(self):
        """Create the necessary table for the Notifier if it does not exist."""
        self.logger.debug(f"Ensuring SQLite tables exist for Notifier Repository in {self._db.db_path}...")
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS notifiers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                adapter_type TEXT NOT NULL,
                config TEXT, -- JSON object of config
                external_service_id TEXT -- Optional ID for external service integration
            );
            """
        ]
        conn = self._db.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                for statement in sql_statements:
                    cursor.execute(statement)

                self.logger.debug("Notifiers tables checked/created successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating SQLite tables: {e}")
            raise ConfigurationError(f"DB error creating tables: {e}") from e
        finally:
            if conn:
                conn.close()

    def _deserialize_config(self, adapter_type: NotificationAdapter, config_json: str) -> NotificationConfig:
        """Deserialize a JSON string into NotificationConfig object."""
        data: dict = json.loads(config_json)

        if adapter_type not in NOTIFIER_CONFIG_TYPE_MAP:
            raise NotifierConfigurationError(f"Error reading Notifier configuration. Invalid type '{adapter_type}'")

        config_class: Optional[type[NotificationConfig]] = NOTIFIER_CONFIG_TYPE_MAP.get(adapter_type)
        if not config_class:
            raise NotifierConfigurationError(f"Error creating Notifier configuration. Type '{adapter_type}'")

        config_instance = config_class.from_dict(data)
        if not isinstance(config_instance, NotificationConfig):
            raise NotifierConfigurationError(
                f"Deserialized config is not of type NotificationConfig for adapter type '{adapter_type}'"
            )
        return config_instance

    def _row_to_notifier(self, row: sqlite3.Row) -> Optional[Notifier]:
        """Deserialize a row from the database into a Notifier object."""
        if not row:
            return None
        try:
            adapter_type = NotificationAdapter(row["adapter_type"])

            # Deserialize the config from the database row
            config = self._deserialize_config(adapter_type, row["config"])

            return Notifier(
                id=EntityId(row["id"]),
                name=row["name"],
                adapter_type=adapter_type,
                config=config,
                external_service_id=(EntityId(row["external_service_id"]) if row["external_service_id"] else None),
            )
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error deserializing Notifier from DB row: {row}. Error: {e}")
            return None

    def add(self, notifier: Notifier) -> None:
        """Add a new notifier to the repository."""
        self.logger.debug(f"Adding notifier {notifier.id} to SQLite repository.")
        sql = """
            INSERT INTO notifiers (id, name, adapter_type, config, external_service_id)
            VALUES (?, ?, ?, ?, ?);
        """
        conn = self._db.get_connection()
        try:
            # Serialize config to JSON for storage
            config_json: str = ""
            if notifier.config:
                config_json = json.dumps(notifier.config.to_dict())

            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (
                        notifier.id,
                        notifier.name,
                        notifier.adapter_type.value,
                        config_json,
                        notifier.external_service_id,
                    ),
                )
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Integrity error adding notifier {notifier.id}: {e}")
            # Could mean that the ID already exists
            raise NotifierAlreadyExistsError(
                f"notifier with ID {notifier.id} already exists or constraint violation: {e}"
            ) from e
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error adding notifier {notifier.id}: {e}")
            raise NotifierError(f"DB error adding notifier: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_id(self, notifier_id: EntityId) -> Optional[Notifier]:
        """Retrieve a notifier by its ID."""
        self.logger.debug(f"Retrieving notifier {notifier_id} from SQLite repository.")
        sql = "SELECT * FROM notifiers WHERE id = ?;"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (notifier_id,))
            row = cursor.fetchone()
            return self._row_to_notifier(row)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error retrieving notifier {notifier_id}: {e}")
            raise NotifierNotFoundError(f"DB error retrieving notifier: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_all(self) -> List[Notifier]:
        """Retrieve all notifiers from the repository."""
        self.logger.debug("Retrieving all notifiers from SQLite repository.")
        sql = "SELECT * FROM notifiers;"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            notifiers = []
            for row in rows:
                notifier = self._row_to_notifier(row)
                if notifier:
                    notifiers.append(notifier)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error retrieving all notifiers: {e}")
            return []
        finally:
            if conn:
                conn.close()
        return notifiers

    def update(self, notifier: Notifier) -> None:
        """Update an existing notifier in the repository."""
        self.logger.debug(f"Updating notifier {notifier.id} in SQLite repository.")
        sql = """
            UPDATE notifiers
            SET name = ?, adapter_type = ?, config = ?, external_service_id = ?
            WHERE id = ?;
        """
        conn = self._db.get_connection()
        try:
            # Serialize config to JSON for storage
            config_json: str = ""
            if notifier.config:
                config_json = json.dumps(notifier.config.to_dict())

            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (
                        notifier.name,
                        notifier.adapter_type.value,
                        config_json,
                        notifier.external_service_id,
                        notifier.id,
                    ),
                )
                if cursor.rowcount == 0:
                    raise NotifierNotFoundError(f"Notifier with ID {notifier.id} not found.")
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error updating notifier {notifier.id}: {e}")
            raise NotifierError(f"DB error updating notifier: {e}") from e
        finally:
            if conn:
                conn.close()

    def remove(self, notifier_id: EntityId) -> None:
        """Remove a notifier from the repository."""
        self.logger.debug(f"Removing notifier {notifier_id} from SQLite repository.")
        sql = "DELETE FROM notifiers WHERE id = ?;"
        conn = self._db.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql, (notifier_id,))
                if cursor.rowcount == 0:
                    self.logger.warning(f"Attempted to remove non-existent notifier {notifier_id}.")
                    # There is no need to raise an exception here, removing a
                    # non-existent is idempotent.
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error removing notifier {notifier_id}: {e}")
            raise NotifierError(f"DB error removing notifier: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[Notifier]:
        """Retrieve a list of notifiers by their associated external service ID."""
        self.logger.debug(f"Retrieving notifiers for external service {external_service_id} from SQLite repository.")
        sql = "SELECT * FROM notifiers WHERE external_service_id = ?;"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (external_service_id,))
            rows = cursor.fetchall()
            notifiers = []
            for row in rows:
                notifier = self._row_to_notifier(row)
                if notifier:
                    notifiers.append(notifier)
            return notifiers
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error retrieving notifiers for external service {external_service_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()


# SQLAlchemy implementation


class SqlAlchemyNotifierRepository(NotifierRepository):
    """SQLAlchemy implementation of NotifierRepository.

    This repository works directly with the imperatively mapped Notifier domain entity.
    The config field is automatically converted between NotificationConfig objects and JSON
    strings by the custom TypeDecorator and event listener defined in tables.py.

    Args:
        db: BaseSQLAlchemyRepository instance for database operations
    """

    def __init__(self, db: BaseSQLAlchemyRepository):
        """Initialize repository with database instance.

        Args:
            db: BaseSQLAlchemyRepository instance
        """
        self._db = db
        self.logger = db.logger

    def add(self, notifier: Notifier) -> None:
        """Add a notifier to the repository."""
        session = self._db.get_session()
        try:
            session.add(notifier)
            session.commit()
        finally:
            session.close()

    def get_by_id(self, notifier_id: EntityId) -> Optional[Notifier]:
        """Get a notifier by ID."""
        session = self._db.get_session()
        try:
            stmt = select(Notifier).where(notifiers_table.c.id == str(notifier_id))
            entity = session.execute(stmt).scalar_one_or_none()
            return entity
        finally:
            session.close()

    def get_all(self) -> List[Notifier]:
        """Get all notifiers."""
        session = self._db.get_session()
        try:
            stmt = select(Notifier)
            entities = session.execute(stmt).scalars().all()
            return list(entities)
        finally:
            session.close()

    def update(self, notifier: Notifier) -> None:
        """Update a notifier."""
        session = self._db.get_session()
        try:
            stmt = select(Notifier).where(notifiers_table.c.id == str(notifier.id))
            existing_entity = session.execute(stmt).scalar_one_or_none()

            if existing_entity:
                existing_entity.name = notifier.name
                existing_entity.adapter_type = notifier.adapter_type
                existing_entity.config = notifier.config
                existing_entity.external_service_id = notifier.external_service_id

                session.commit()
        finally:
            session.close()

    def remove(self, notifier_id: EntityId) -> None:
        """Remove a notifier by ID."""
        session = self._db.get_session()
        try:
            stmt = select(Notifier).where(notifiers_table.c.id == str(notifier_id))
            entity = session.execute(stmt).scalar_one_or_none()

            if entity:
                session.delete(entity)
                session.commit()
        finally:
            session.close()

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[Notifier]:
        """Get notifiers by external service ID."""
        session = self._db.get_session()
        try:
            stmt = select(Notifier).where(notifiers_table.c.external_service_id == str(external_service_id))
            entities = session.execute(stmt).scalars().all()
            return list(entities)
        finally:
            session.close()
