"""Repositories for the Home loads domain."""

import copy
import json
import sqlite3
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from edge_mining.adapters.domain.home_load.tables import (
    energy_load_forecast_providers_table,
    home_profiles_table,
)
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.adapters.infrastructure.persistence.sqlite import BaseSqliteRepository
from edge_mining.domain.common import EntityId
from edge_mining.domain.exceptions import ConfigurationError
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter, LoadDeviceCategory
from edge_mining.domain.home_load.entities import EnergyLoadForecastProvider, LoadDevice
from edge_mining.domain.home_load.exceptions import (
    EnergyLoadForecastProviderAlreadyExistsError,
    EnergyLoadForecastProviderConfigurationError,
    EnergyLoadForecastProviderError,
    EnergyLoadForecastProviderNotFoundError,
)
from edge_mining.domain.home_load.ports import (
    EnergyLoadForecastProviderRepository,
    HomeLoadsProfileRepository,
)
from edge_mining.shared.adapter_maps.home_load import (
    ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP,
)
from edge_mining.shared.interfaces.config import EnergyLoadForecastProviderConfig


# --- HomeLoadsProfile Repositories ---


def _device_to_dict(device: LoadDevice) -> Dict[str, Any]:
    return {
        "id": str(device.id),
        "name": device.name,
        "category": device.category.value,
        "enabled": device.enabled,
        "energy_load_forecast_provider_id": (
            str(device.energy_load_forecast_provider_id) if device.energy_load_forecast_provider_id else None
        ),
        "energy_load_history_provider_id": (
            str(device.energy_load_history_provider_id) if device.energy_load_history_provider_id else None
        ),
    }


def _dict_to_device(data: Dict[str, Any]) -> LoadDevice:
    forecast_id = data.get("energy_load_forecast_provider_id")
    history_id = data.get("energy_load_history_provider_id")
    return LoadDevice(
        id=EntityId(uuid.UUID(data["id"])),
        name=data["name"],
        category=LoadDeviceCategory(data["category"]),
        enabled=bool(data.get("enabled", True)),
        energy_load_forecast_provider_id=EntityId(uuid.UUID(forecast_id)) if forecast_id else None,
        energy_load_history_provider_id=EntityId(uuid.UUID(history_id)) if history_id else None,
    )


class InMemoryHomeLoadsProfileRepository(HomeLoadsProfileRepository):
    """In-memory implementation for the Home Loads Profile Repository."""

    def __init__(self, initial_profiles: Optional[List[HomeLoadsProfile]] = None):
        self._profiles: Dict[EntityId, HomeLoadsProfile] = {}
        if initial_profiles:
            for profile in initial_profiles:
                self._profiles[profile.id] = copy.deepcopy(profile)

    def add(self, profile: HomeLoadsProfile) -> None:
        self._profiles[profile.id] = copy.deepcopy(profile)

    def get_by_id(self, profile_id: EntityId) -> Optional[HomeLoadsProfile]:
        profile = self._profiles.get(profile_id)
        return copy.deepcopy(profile) if profile else None

    def get_all(self) -> List[HomeLoadsProfile]:
        return [copy.deepcopy(p) for p in self._profiles.values()]

    def update(self, profile: HomeLoadsProfile) -> None:
        self._profiles[profile.id] = copy.deepcopy(profile)

    def remove(self, profile_id: EntityId) -> None:
        self._profiles.pop(profile_id, None)

    def get_by_energy_load_forecast_provider_id(self, provider_id: EntityId) -> List[HomeLoadsProfile]:
        return [
            copy.deepcopy(profile)
            for profile in self._profiles.values()
            if any(device.energy_load_forecast_provider_id == provider_id for device in profile.devices)
        ]


class SqliteHomeLoadsProfileRepository(HomeLoadsProfileRepository):
    """SQLite implementation for the Home Loads Profile Repository."""

    def __init__(self, db: BaseSqliteRepository):
        self._db = db
        self.logger = db.logger
        self._create_tables()

    def _create_tables(self):
        self.logger.debug(f"Ensuring SQLite tables exist for Home Loads Profile Repository in {self._db.db_path}...")
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS home_profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                devices_json TEXT -- JSON list of LoadDevice dicts
            );
            """
        ]

        conn = self._db.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                for statement in sql_statements:
                    cursor.execute(statement)
                self.logger.debug("Home Loads Profile tables checked/created successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating SQLite tables: {e}")
            raise ConfigurationError(f"DB error creating tables: {e}") from e
        finally:
            if conn:
                conn.close()

    def _row_to_profile(self, row: sqlite3.Row) -> Optional[HomeLoadsProfile]:
        if not row:
            return None
        try:
            devices_data: List = json.loads(row["devices_json"] or "[]")
            devices = [_dict_to_device(dev) for dev in devices_data if isinstance(dev, dict)]
            return HomeLoadsProfile(id=EntityId(uuid.UUID(row["id"])), name=row["name"], devices=devices)
        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error deserializing HomeLoadsProfile from DB row: {dict(row)}. Error: {e}")
            return None

    def add(self, profile: HomeLoadsProfile) -> None:
        self.logger.debug(f"Adding home loads profile '{profile.name}' ({profile.id}) to SQLite.")
        sql = "INSERT INTO home_profiles (id, name, devices_json) VALUES (?, ?, ?)"
        conn = self._db.get_connection()
        try:
            devices_json = json.dumps([_device_to_dict(dev) for dev in profile.devices])
            with conn:
                conn.execute(sql, (str(profile.id), profile.name, devices_json))
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error adding profile {profile.id}: {e}")
            raise ConfigurationError(f"DB error adding profile: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_id(self, profile_id: EntityId) -> Optional[HomeLoadsProfile]:
        sql = "SELECT * FROM home_profiles WHERE id = ?"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (str(profile_id),))
            row = cursor.fetchone()
            return self._row_to_profile(row) if row else None
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error getting profile {profile_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all(self) -> List[HomeLoadsProfile]:
        sql = "SELECT * FROM home_profiles"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            profiles: List[HomeLoadsProfile] = []
            for row in rows:
                profile = self._row_to_profile(row)
                if profile:
                    profiles.append(profile)
            return profiles
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error getting all profiles: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def update(self, profile: HomeLoadsProfile) -> None:
        sql = "UPDATE home_profiles SET name = ?, devices_json = ? WHERE id = ?"
        conn = self._db.get_connection()
        try:
            devices_json = json.dumps([_device_to_dict(dev) for dev in profile.devices])
            with conn:
                conn.execute(sql, (profile.name, devices_json, str(profile.id)))
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error updating profile {profile.id}: {e}")
            raise ConfigurationError(f"DB error updating profile: {e}") from e
        finally:
            if conn:
                conn.close()

    def remove(self, profile_id: EntityId) -> None:
        sql = "DELETE FROM home_profiles WHERE id = ?"
        conn = self._db.get_connection()
        try:
            with conn:
                conn.execute(sql, (str(profile_id),))
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error removing profile {profile_id}: {e}")
            raise ConfigurationError(f"DB error removing profile: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_energy_load_forecast_provider_id(self, provider_id: EntityId) -> List[HomeLoadsProfile]:
        return [
            profile
            for profile in self.get_all()
            if any(device.energy_load_forecast_provider_id == provider_id for device in profile.devices)
        ]


# --- EnergyLoadForecastProvider Repositories ---


class InMemoryEnergyLoadForecastProviderRepository(EnergyLoadForecastProviderRepository):
    """In-memory implementation of EnergyLoadForecastProviderRepository for testing purposes."""

    def __init__(self):
        self._energy_load_forecast_providers: List[EnergyLoadForecastProvider] = []

    def add(self, energy_load_forecast_provider: EnergyLoadForecastProvider) -> None:
        self._energy_load_forecast_providers.append(energy_load_forecast_provider)

    def get_by_id(self, energy_load_forecast_provider_id: EntityId) -> Optional[EnergyLoadForecastProvider]:
        for energy_load_forecast_provider in self._energy_load_forecast_providers:
            if energy_load_forecast_provider.id == energy_load_forecast_provider_id:
                return energy_load_forecast_provider
        return None

    def get_all(self) -> List[EnergyLoadForecastProvider]:
        return self._energy_load_forecast_providers

    def update(self, energy_load_forecast_provider: EnergyLoadForecastProvider) -> None:
        for i, existing_provider in enumerate(self._energy_load_forecast_providers):
            if existing_provider.id == energy_load_forecast_provider.id:
                self._energy_load_forecast_providers[i] = energy_load_forecast_provider
                return

    def remove(self, energy_load_forecast_provider_id: EntityId) -> None:
        self._energy_load_forecast_providers = [
            n for n in self._energy_load_forecast_providers if n.id != energy_load_forecast_provider_id
        ]

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[EnergyLoadForecastProvider]:
        """Retrieve all energy load forecast providers linked to a specific external service."""
        return (
            [
                provider
                for provider in self._energy_load_forecast_providers
                if provider.external_service_id == external_service_id
            ]
            if external_service_id
            else []
        )


class SqliteEnergyLoadForecastProviderRepository(EnergyLoadForecastProviderRepository):
    """SQLite implementation of EnergyLoadForecastProviderRepository."""

    def __init__(self, db: BaseSqliteRepository):
        self._db = db
        self.logger = db.logger

        self._create_tables()

    def _create_tables(self):
        self.logger.debug(
            f"Ensuring SQLite tables exist for Energy Load Forecast Provider Repository in {self._db.db_path}..."
        )
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS energy_load_forecast_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                adapter_type TEXT NOT NULL,
                config TEXT,
                external_service_id TEXT
            );
            """
        ]
        conn = self._db.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                for statement in sql_statements:
                    cursor.execute(statement)
        except sqlite3.Error as e:
            self.logger.error(f"Error creating SQLite tables: {e}")
            raise ConfigurationError(f"DB error creating tables: {e}") from e
        finally:
            if conn:
                conn.close()

    def _deserialize_config(
        self, adapter_type: EnergyLoadForecastProviderAdapter, config_json: str
    ) -> EnergyLoadForecastProviderConfig:
        data: dict = json.loads(config_json)

        if adapter_type not in ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP:
            raise EnergyLoadForecastProviderNotFoundError(
                f"Error reading EnergyLoadForecastProvider configuration. Invalid type '{adapter_type}'"
            )

        config_class: Optional[type[EnergyLoadForecastProviderConfig]] = (
            ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(adapter_type)
        )
        if not config_class:
            raise EnergyLoadForecastProviderNotFoundError(
                f"Error creating EnergyLoadForecastProviderConfig configuration. Type '{adapter_type}'"
            )

        config_instance = config_class.from_dict(data)
        if not isinstance(config_instance, EnergyLoadForecastProviderConfig):
            raise EnergyLoadForecastProviderConfigurationError(
                f"Deserialized config is not of type EnergyLoadForecastProviderConfig "
                f"for adapter type {adapter_type}."
            )
        return config_instance

    def _row_to_energy_load_forecast_provider(self, row: sqlite3.Row) -> Optional[EnergyLoadForecastProvider]:
        if not row:
            return None
        try:
            provider_type = EnergyLoadForecastProviderAdapter(row["adapter_type"])
            config = self._deserialize_config(provider_type, row["config"])

            return EnergyLoadForecastProvider(
                id=EntityId(row["id"]),
                name=row["name"],
                adapter_type=provider_type,
                config=config,
                external_service_id=(EntityId(row["external_service_id"]) if row["external_service_id"] else None),
            )
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error deserializing EnergyLoadForecastProvider from DB row: {row}. Error: {e}")
            return None

    def add(self, energy_load_forecast_provider: EnergyLoadForecastProvider) -> None:
        self.logger.debug(f"Adding forecast provider {energy_load_forecast_provider.id} to SQLite repository.")
        sql = """
            INSERT INTO energy_load_forecast_providers (id, name, adapter_type, config, external_service_id)
            VALUES (?, ?, ?, ?, ?);
        """
        conn = self._db.get_connection()
        try:
            config_json: str = ""
            if energy_load_forecast_provider.config:
                config_json = json.dumps(energy_load_forecast_provider.config.to_dict())

            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (
                        energy_load_forecast_provider.id,
                        energy_load_forecast_provider.name,
                        energy_load_forecast_provider.adapter_type.value,
                        config_json,
                        energy_load_forecast_provider.external_service_id,
                    ),
                )
        except sqlite3.IntegrityError as e:
            self.logger.error(
                f"Integrity error adding energy load forecast provider {energy_load_forecast_provider.id}: {e}"
            )
            raise EnergyLoadForecastProviderAlreadyExistsError(
                f"Energy load forecast provider with ID {energy_load_forecast_provider.id} "
                f"already exists or constraint violation: {e}"
            ) from e
        except sqlite3.Error as e:
            self.logger.error(
                f"SQLite error adding energy load forecast provider {energy_load_forecast_provider.id}: {e}"
            )
            raise EnergyLoadForecastProviderError(f"DB error adding energy load forecast provider: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_id(self, energy_load_forecast_provider_id: EntityId) -> Optional[EnergyLoadForecastProvider]:
        sql = "SELECT * FROM energy_load_forecast_providers WHERE id = ?;"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (energy_load_forecast_provider_id,))
            row = cursor.fetchone()
            return self._row_to_energy_load_forecast_provider(row)
        except sqlite3.Error as e:
            self.logger.error(
                f"SQLite error retrieving energy load forecast provider {energy_load_forecast_provider_id}: {e}"
            )
            raise EnergyLoadForecastProviderNotFoundError(
                f"DB error retrieving energy load forecast provider: {e}"
            ) from e
        finally:
            if conn:
                conn.close()

    def get_all(self) -> List[EnergyLoadForecastProvider]:
        sql = "SELECT * FROM energy_load_forecast_providers;"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            energy_load_forecast_providers = []
            for row in rows:
                provider = self._row_to_energy_load_forecast_provider(row)
                if provider:
                    energy_load_forecast_providers.append(provider)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error retrieving all energy load forecast providers: {e}")
            return []
        finally:
            if conn:
                conn.close()
        return energy_load_forecast_providers

    def update(self, energy_load_forecast_provider: EnergyLoadForecastProvider) -> None:
        sql = """
            UPDATE energy_load_forecast_providers
            SET name = ?, adapter_type = ?, config = ?, external_service_id = ?
            WHERE id = ?;
        """
        conn = self._db.get_connection()
        try:
            config_json = json.dumps(energy_load_forecast_provider.config)

            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (
                        energy_load_forecast_provider.name,
                        energy_load_forecast_provider.adapter_type.value,
                        config_json,
                        energy_load_forecast_provider.external_service_id,
                        energy_load_forecast_provider.id,
                    ),
                )
                if cursor.rowcount == 0:
                    raise EnergyLoadForecastProviderNotFoundError(
                        f"Energy Load Forecast Provider with ID {energy_load_forecast_provider.id} not found."
                    )
        except sqlite3.Error as e:
            self.logger.error(
                f"SQLite error updating energy load forecast provider {energy_load_forecast_provider.id}: {e}"
            )
            raise EnergyLoadForecastProviderError(f"DB error updating energy load forecast provider: {e}") from e
        finally:
            if conn:
                conn.close()

    def remove(self, energy_load_forecast_provider_id: EntityId) -> None:
        sql = "DELETE FROM energy_load_forecast_providers WHERE id = ?;"
        conn = self._db.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql, (energy_load_forecast_provider_id,))
                if cursor.rowcount == 0:
                    self.logger.warning(
                        f"Attempted to remove non-existent energy load forecast provider "
                        f"{energy_load_forecast_provider_id}."
                    )
        except sqlite3.Error as e:
            self.logger.error(
                f"SQLite error removing energy load forecast provider {energy_load_forecast_provider_id}: {e}"
            )
            raise EnergyLoadForecastProviderError(f"DB error removing energy load forecast provider: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[EnergyLoadForecastProvider]:
        sql = "SELECT * FROM energy_load_forecast_providers WHERE external_service_id = ?;"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (external_service_id,))
            rows = cursor.fetchall()
            energy_load_forecast_providers = []
            for row in rows:
                provider = self._row_to_energy_load_forecast_provider(row)
                if provider:
                    energy_load_forecast_providers.append(provider)
            return energy_load_forecast_providers
        except sqlite3.Error as e:
            self.logger.error(
                f"SQLite error retrieving energy load forecast providers by external service ID "
                f"{external_service_id}: {e}"
            )
            return []
        finally:
            if conn:
                conn.close()


# --- SQLAlchemy implementations ---


class SqlAlchemyEnergyLoadForecastProviderRepository(EnergyLoadForecastProviderRepository):
    """SQLAlchemy implementation of EnergyLoadForecastProviderRepository."""

    def __init__(self, db: BaseSQLAlchemyRepository):
        self._db = db
        self.logger = db.logger

    def add(self, energy_load_forecast_provider: EnergyLoadForecastProvider) -> None:
        session = self._db.get_session()
        try:
            session.add(energy_load_forecast_provider)
            session.commit()
        finally:
            session.close()

    def get_by_id(self, energy_load_forecast_provider_id: EntityId) -> Optional[EnergyLoadForecastProvider]:
        session = self._db.get_session()
        try:
            stmt = select(EnergyLoadForecastProvider).where(
                energy_load_forecast_providers_table.c.id == str(energy_load_forecast_provider_id)
            )
            entity = session.execute(stmt).scalar_one_or_none()
            return entity
        finally:
            session.close()

    def get_all(self) -> List[EnergyLoadForecastProvider]:
        session = self._db.get_session()
        try:
            stmt = select(EnergyLoadForecastProvider)
            entities = session.execute(stmt).scalars().all()
            return list(entities)
        finally:
            session.close()

    def update(self, energy_load_forecast_provider: EnergyLoadForecastProvider) -> None:
        session = self._db.get_session()
        try:
            stmt = select(EnergyLoadForecastProvider).where(
                energy_load_forecast_providers_table.c.id == str(energy_load_forecast_provider.id)
            )
            existing_entity = session.execute(stmt).scalar_one_or_none()

            if existing_entity:
                existing_entity.name = energy_load_forecast_provider.name
                existing_entity.adapter_type = energy_load_forecast_provider.adapter_type
                existing_entity.config = energy_load_forecast_provider.config
                existing_entity.external_service_id = energy_load_forecast_provider.external_service_id

                session.commit()
        finally:
            session.close()

    def remove(self, energy_load_forecast_provider_id: EntityId) -> None:
        session = self._db.get_session()
        try:
            stmt = select(EnergyLoadForecastProvider).where(
                energy_load_forecast_providers_table.c.id == str(energy_load_forecast_provider_id)
            )
            entity = session.execute(stmt).scalar_one_or_none()

            if entity:
                session.delete(entity)
                session.commit()
        finally:
            session.close()

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[EnergyLoadForecastProvider]:
        session = self._db.get_session()
        try:
            stmt = select(EnergyLoadForecastProvider).where(
                energy_load_forecast_providers_table.c.external_service_id == str(external_service_id)
            )
            entities = session.execute(stmt).scalars().all()
            return list(entities)
        finally:
            session.close()


class SqlAlchemyHomeLoadsProfileRepository(HomeLoadsProfileRepository):
    """SQLAlchemy implementation of the HomeLoadsProfileRepository."""

    def __init__(self, db: BaseSQLAlchemyRepository):
        self._db = db
        self.logger = db.logger

    def add(self, profile: HomeLoadsProfile) -> None:
        session = self._db.get_session()
        try:
            session.add(profile)
            session.commit()
        finally:
            session.close()

    def get_by_id(self, profile_id: EntityId) -> Optional[HomeLoadsProfile]:
        session = self._db.get_session()
        try:
            stmt = select(HomeLoadsProfile).where(home_profiles_table.c.id == str(profile_id))
            entity = session.execute(stmt).scalar_one_or_none()
            return entity
        finally:
            session.close()

    def get_all(self) -> List[HomeLoadsProfile]:
        session = self._db.get_session()
        try:
            stmt = select(HomeLoadsProfile)
            entities = session.execute(stmt).scalars().all()
            return list(entities)
        finally:
            session.close()

    def update(self, profile: HomeLoadsProfile) -> None:
        session = self._db.get_session()
        try:
            stmt = select(HomeLoadsProfile).where(home_profiles_table.c.id == str(profile.id))
            existing_entity = session.execute(stmt).scalar_one_or_none()

            if existing_entity:
                existing_entity.name = profile.name
                existing_entity.devices = profile.devices
                session.commit()
        finally:
            session.close()

    def remove(self, profile_id: EntityId) -> None:
        session = self._db.get_session()
        try:
            stmt = select(HomeLoadsProfile).where(home_profiles_table.c.id == str(profile_id))
            entity = session.execute(stmt).scalar_one_or_none()
            if entity:
                session.delete(entity)
                session.commit()
        finally:
            session.close()

    def get_by_energy_load_forecast_provider_id(self, provider_id: EntityId) -> List[HomeLoadsProfile]:
        return [
            profile
            for profile in self.get_all()
            if any(device.energy_load_forecast_provider_id == provider_id for device in profile.devices)
        ]
