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
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
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

# Simple In-Memory implementation for testing and basic use


class InMemoryHomeLoadsProfileRepository(HomeLoadsProfileRepository):
    """In-Memory implementation for the Home Loads Profile Repository."""

    def __init__(self, initial_profile: Optional[HomeLoadsProfile] = None):
        self._profile: Optional[HomeLoadsProfile] = copy.deepcopy(initial_profile)

    def get_profile(self) -> Optional[HomeLoadsProfile]:
        return copy.deepcopy(self._profile)

    def save_profile(self, profile: HomeLoadsProfile) -> None:
        self._profile = copy.deepcopy(profile)


class SqliteHomeLoadsProfileRepository(HomeLoadsProfileRepository):
    """SQLite implementation for the Home Loads Profile Repository."""

    # fixed UUID for the default profile
    _DEFAULT_PROFILE_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")

    def __init__(self, db: BaseSqliteRepository):
        self._db = db
        self.logger = db.logger

        self._create_tables()

    def _create_tables(self):
        """Create the necessary tables for the Home Load domain if they do not exist."""
        self.logger.debug(f"Ensuring SQLite tables exist for Home Loads Profile Repository in {self._db.db_path}...")
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS home_profiles (
                id TEXT PRIMARY KEY, -- e.g., fixed UUID for default profile
                name TEXT NOT NULL,
                devices_json TEXT -- JSON Dict[EntityId_str, LoadDevice_dict]
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

    def _device_to_dict(self, device: LoadDevice) -> Dict[str, Any]:
        return {"id": str(device.id), "name": device.name, "category": device.category.value}

    def _dict_to_device(self, data: Dict[str, Any]) -> LoadDevice:
        """Convert a dictionary to a LoadDevice."""
        from edge_mining.domain.home_load.common import LoadDeviceCategory

        return LoadDevice(
            id=EntityId(uuid.UUID(data["id"])),
            name=data["name"],
            category=LoadDeviceCategory(data["category"]),
        )

    def _row_to_profile(self, row: sqlite3.Row) -> Optional[HomeLoadsProfile]:
        """Convert a row to a HomeLoadsProfile."""
        if not row:
            return None
        try:
            devices_data: Dict = json.loads(row["devices_json"] or "{}")
            devices = {
                EntityId(uuid.UUID(id_str)): self._dict_to_device(dev_dict) for id_str, dev_dict in devices_data.items()
            }
            return HomeLoadsProfile(id=row["id"], name=row["name"], devices=devices)  # UUID
        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
            self.logger.error(f"Error deserializing HomeLoadsProfile from DB line: {dict(row)}. Error: {e}")
            return None

    def get_profile(self) -> Optional[HomeLoadsProfile]:
        """Get the home load profile from SQLite."""
        self.logger.debug("Getting home load profile from SQLite.")
        sql = "SELECT * FROM home_profiles WHERE id = ?"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (self._DEFAULT_PROFILE_UUID,))
            row = cursor.fetchone()
            if row:
                return self._row_to_profile(row)
            else:
                self.logger.info("No home load profile found in DB, returning None.")
                return None
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error getting home profile: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def save_profile(self, profile: HomeLoadsProfile) -> None:
        """Save the home load profile to SQLite."""
        self.logger.debug(f"Saving home load profile '{profile.name}' to SQLite.")
        sql = "INSERT OR REPLACE INTO home_profiles (id, name, devices_json) VALUES (?, ?, ?)"
        conn = self._db.get_connection()
        try:
            # Serialize the dictionary of devices
            devices_json = json.dumps({str(id): self._device_to_dict(dev) for id, dev in profile.devices.items()})
            with conn:
                # Always use the fixed UUID for the default profile
                # default
                conn.execute(
                    sql,
                    (self._DEFAULT_PROFILE_UUID, profile.name, devices_json),
                )
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error saving home profile: {e}")
            raise ConfigurationError(f"DB error saving home profile: {e}") from e
        finally:
            if conn:
                conn.close()


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
        """Create the necessary table for the Energy Load Forecast Provider if it does not exist."""
        self.logger.debug(
            f"Ensuring SQLite tables exist for Energy Load Forecast Provider Repository in {self._db.db_path}..."
        )
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS energy_load_forecast_providers (
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

                self.logger.debug("Energy Load Forecast providers tables checked/created successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Error creating SQLite tables: {e}")
            raise ConfigurationError(f"DB error creating tables: {e}") from e
        finally:
            if conn:
                conn.close()

    def _deserialize_config(
        self, adapter_type: EnergyLoadForecastProviderAdapter, config_json: str
    ) -> EnergyLoadForecastProviderConfig:
        """Deserialize a JSON string into EnergyLoadForecastProviderConfig object."""
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
        """Deserialize a row from the database into an EnergyLoadForecastProvider object."""
        if not row:
            return None
        try:
            provider_type = EnergyLoadForecastProviderAdapter(row["adapter_type"])

            # Deserialize the config from the database row
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
        """Add a new energy load forecast provider to the repository."""
        self.logger.debug(f"Adding forecast provider {energy_load_forecast_provider.id} to SQLite repository.")
        sql = """
            INSERT INTO energy_load_forecast_providers (id, name, adapter_type, config, external_service_id)
            VALUES (?, ?, ?, ?, ?);
        """
        conn = self._db.get_connection()
        try:
            # Serialize config to JSON for storage
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
            # Could mean that the ID already exists
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
        """Retrieve an energy load forecast provider by its ID."""
        self.logger.debug(
            f"Retrieving energy load forecast provider {energy_load_forecast_provider_id} from SQLite repository."
        )
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
        """Retrieve all energy load forecast providers from the repository."""
        self.logger.debug("Retrieving all energy load forecast providers from SQLite repository.")
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
        """Update an existing energy load forecast provider in the repository."""
        self.logger.debug(
            f"Updating energy load forecast provider {energy_load_forecast_provider.id} in SQLite repository."
        )
        sql = """
            UPDATE energy_load_forecast_providers
            SET name = ?, adapter_type = ?, config = ?, external_service_id = ?
            WHERE id = ?;
        """
        conn = self._db.get_connection()
        try:
            # Serialize config to JSON for storage
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
        """Remove an energy load forecast provider from the repository."""
        self.logger.debug(f"Removing forecast provider {energy_load_forecast_provider_id} from SQLite repository.")
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
                    # There is no need to raise an exception here, removing a
                    # non-existent is idempotent.
        except sqlite3.Error as e:
            self.logger.error(
                f"SQLite error removing energy load forecast provider {energy_load_forecast_provider_id}: {e}"
            )
            raise EnergyLoadForecastProviderError(f"DB error removing energy load forecast provider: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[EnergyLoadForecastProvider]:
        """Retrieve all energy load forecast providers linked to a specific external service."""
        self.logger.debug(
            "Retrieving energy load forecast providers linked to external service "
            f"{external_service_id} from SQLite repository."
        )
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


# SQLAlchemy implementation


class SqlAlchemyEnergyLoadForecastProviderRepository(EnergyLoadForecastProviderRepository):
    """SQLAlchemy implementation of EnergyLoadForecastProviderRepository.

    This repository works directly with the imperatively mapped EnergyLoadForecastProvider domain entity.
    The config field is automatically converted between EnergyLoadForecastProviderConfig objects and JSON
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

    def add(self, energy_load_forecast_provider: EnergyLoadForecastProvider) -> None:
        """Add an energy load forecast provider to the repository."""
        session = self._db.get_session()
        try:
            session.add(energy_load_forecast_provider)
            session.commit()
        finally:
            session.close()

    def get_by_id(self, energy_load_forecast_provider_id: EntityId) -> Optional[EnergyLoadForecastProvider]:
        """Get an energy load forecast provider by ID."""
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
        """Get all energy load forecast providers."""
        session = self._db.get_session()
        try:
            stmt = select(EnergyLoadForecastProvider)
            entities = session.execute(stmt).scalars().all()
            return list(entities)
        finally:
            session.close()

    def update(self, energy_load_forecast_provider: EnergyLoadForecastProvider) -> None:
        """Update an energy load forecast provider."""
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
        """Remove an energy load forecast provider by ID."""
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
        """Get energy load forecast providers by external service ID."""
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
    """SQLAlchemy implementation of the HomeLoadsProfileRepository.

    This repository works directly with the imperatively mapped HomeLoadsProfile aggregate root.
    The devices field is automatically converted between Dict[EntityId, LoadDevice] and JSON
    by the custom TypeDecorator and event listener defined in tables.py.

    Args:
        db: BaseSQLAlchemyRepository instance for database operations
    """

    # fixed UUID for the default profile
    _DEFAULT_PROFILE_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")

    def __init__(self, db: BaseSQLAlchemyRepository):
        """Initialize repository with database instance.

        Args:
            db: BaseSQLAlchemyRepository instance
        """
        self._db = db
        self.logger = db.logger

    def get_profile(self) -> Optional[HomeLoadsProfile]:
        """Get the home load profile from the database."""
        session = self._db.get_session()
        try:
            stmt = select(HomeLoadsProfile).where(home_profiles_table.c.id == str(self._DEFAULT_PROFILE_UUID))
            entity = session.execute(stmt).scalar_one_or_none()
            return entity
        finally:
            session.close()

    def save_profile(self, profile: HomeLoadsProfile) -> None:
        """Save the home load profile to the database."""
        session = self._db.get_session()
        try:
            # Check if profile already exists
            stmt = select(HomeLoadsProfile).where(home_profiles_table.c.id == str(self._DEFAULT_PROFILE_UUID))
            existing_entity = session.execute(stmt).scalar_one_or_none()

            if existing_entity:
                # Update existing profile
                existing_entity.name = profile.name
                existing_entity.devices = profile.devices
                session.commit()
            else:
                # Create new profile with fixed UUID
                new_profile = HomeLoadsProfile(
                    id=EntityId(self._DEFAULT_PROFILE_UUID), name=profile.name, devices=profile.devices
                )
                session.add(new_profile)
                session.commit()
        finally:
            session.close()
