"""
This module contains the adapter classes implementing the SettingsRepository interface.
"""

import copy
import json
import sqlite3
from typing import Dict, Optional

from sqlalchemy import select

from edge_mining.adapters.domain.user.tables import settings_table
from edge_mining.adapters.infrastructure.persistence.sqlite import BaseSqliteRepository
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.domain.exceptions import ConfigurationError
from edge_mining.domain.user.common import UserId
from edge_mining.domain.user.entities import SystemSettings
from edge_mining.shared.settings.ports import SettingsRepository

# Simple In-Memory implementation for testing and basic use


class InMemorySettingsRepository(SettingsRepository):
    """In-Memory implementation of the SettingsRepository."""

    # We dont have different users, so we use a single ID.
    _SETTINGS_ID: str = "global_settings"

    def __init__(self, initial_settings: Optional[Dict[UserId, SystemSettings]] = None):
        self._settings: Dict[UserId, SystemSettings] = copy.deepcopy(initial_settings) if initial_settings else {}

    def get_settings(self, user_id: Optional[UserId]) -> Optional[SystemSettings]:
        user_id = user_id or UserId(self._SETTINGS_ID)
        if user_id in self._settings:
            return copy.deepcopy(self._settings[user_id])
        return None

    def save_settings(self, user_id: Optional[UserId], settings: SystemSettings) -> None:
        user_id = user_id or UserId(self._SETTINGS_ID)
        self._settings[user_id] = copy.deepcopy(settings)


class SqliteSettingsRepository(SettingsRepository):
    """SQLite implementation of the SettingsRepository."""

    # We dont have different users, so we use a single ID.
    _SETTINGS_ID: str = "global_settings"

    def __init__(self, db: BaseSqliteRepository):
        self._db = db
        self.logger = db.logger

        self._create_tables()

    def _create_tables(self):
        """Create the necessary tables for the Settings domain if they do not exist."""
        self.logger.debug(f"Ensuring SQLite tables exist for Settings Repository in {self._db.db_path}...")
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS settings (
                id TEXT PRIMARY KEY, -- e.g., 'global'
                settings_json TEXT NOT NULL -- JSON blob
            );
            """
        ]

        conn = self._db.get_connection()

        try:
            with conn:
                cursor = conn.cursor()
                for statement in sql_statements:
                    cursor.execute(statement)

                self.logger.debug("Settings tables checked/created successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating SQLite tables: {e}")
            raise ConfigurationError(f"DB error creating tables: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_settings(self, user_id: Optional[UserId]) -> Optional[SystemSettings]:
        self.logger.debug("Getting settings from SQLite.")
        user_id = user_id or UserId(self._SETTINGS_ID)
        sql = "SELECT settings_json FROM settings WHERE id = ?"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            if row:
                settings_dict = json.loads(row["settings_json"])
                return SystemSettings(id=user_id, settings=settings_dict)
            else:
                self.logger.info("No settings found in DB, returning None.")
                return None  # No settings found in DB, return None
        except (sqlite3.Error, json.JSONDecodeError) as e:
            self.logger.error(f"Errore SQLite o JSON ottenendo settings: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def save_settings(self, user_id: Optional[UserId], settings: SystemSettings) -> None:
        self.logger.debug("Saving settings to SQLite.")
        user_id = user_id or UserId(self._SETTINGS_ID)
        sql = "INSERT OR REPLACE INTO settings (id, settings_json) VALUES (?, ?)"
        conn = self._db.get_connection()
        try:
            settings_json = json.dumps(settings.settings)  # Serialize the inner dictionary
            with conn:
                conn.execute(sql, (user_id, settings_json))
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error saving settings: {e}")
            raise ConfigurationError(f"SQLite error saving settings: {e}") from e
        finally:
            if conn:
                conn.close()


# SQLAlchemy implementation


class SqlAlchemySettingsRepository(SettingsRepository):
    """SQLAlchemy implementation of the SettingsRepository.

    This repository works directly with the imperatively mapped SystemSettings entity.
    The settings field is stored as JSON in the database.

    Args:
        db: BaseSQLAlchemyRepository instance for database operations
    """

    # We dont have different users, so we use a single ID.
    _SETTINGS_ID: str = "global_settings"

    def __init__(self, db: BaseSQLAlchemyRepository):
        """Initialize repository with database instance.

        Args:
            db: BaseSQLAlchemyRepository instance
        """
        self._db = db
        self.logger = db.logger

    def get_settings(self, user_id: Optional[UserId]) -> Optional[SystemSettings]:
        """Get settings for a user (or global settings if user_id is None)."""
        user_id = user_id or UserId(self._SETTINGS_ID)
        session = self._db.get_session()
        try:
            stmt = select(SystemSettings).where(settings_table.c.id == str(user_id))
            entity = session.execute(stmt).scalar_one_or_none()
            return entity
        finally:
            session.close()

    def save_settings(self, user_id: Optional[UserId], settings: SystemSettings) -> None:
        """Save settings for a user (or global settings if user_id is None)."""
        user_id = user_id or UserId(self._SETTINGS_ID)
        session = self._db.get_session()
        try:
            # Check if settings already exist
            stmt = select(SystemSettings).where(settings_table.c.id == str(user_id))
            existing_entity = session.execute(stmt).scalar_one_or_none()

            if existing_entity:
                # Update existing settings
                existing_entity.settings = settings.settings
                session.commit()
            else:
                # Create new settings with the provided user_id
                new_settings = SystemSettings(id=user_id, settings=settings.settings)
                session.add(new_settings)
                session.commit()
        finally:
            session.close()
