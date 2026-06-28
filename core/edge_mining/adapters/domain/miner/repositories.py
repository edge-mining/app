"""Repositories for the Miner domain."""

import copy
import json
import sqlite3
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from edge_mining.adapters.domain.miner.tables import (
    delete_features_for_miner,
    load_features_for_miner,
    miner_controllers_table,
    miner_features_table,
    miners_table,
    save_features_for_miner,
)
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.adapters.infrastructure.persistence.sqlite import BaseSqliteRepository
from edge_mining.domain.common import EntityId, Watts
from edge_mining.domain.miner.common import MinerControllerAdapter, MinerFeatureType
from edge_mining.domain.miner.aggregate_roots import Miner
from edge_mining.domain.miner.entities import MinerController
from edge_mining.domain.miner.exceptions import (
    MinerControllerAlreadyExistsError,
    MinerControllerConfigurationError,
    MinerControllerError,
    MinerControllerNotFoundError,
    MinerError,
)
from edge_mining.domain.miner.ports import MinerControllerRepository, MinerRepository
from edge_mining.domain.miner.value_objects import HashRate, MinerFeature
from edge_mining.shared.adapter_maps.miner import MINER_CONTROLLER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import MinerControllerConfig

# Simple In-Memory implementation for testing and basic use


class InMemoryMinerRepository(MinerRepository):
    """In-Memory implementation for the Miner Repository."""

    def __init__(self, initial_miners: Optional[Dict[EntityId, Miner]] = None):
        self._miners: Dict[EntityId, Miner] = copy.deepcopy(initial_miners) if initial_miners else {}

    def add(self, miner: Miner) -> None:
        """Add a miner to the In-Memory repository."""
        if miner.id in self._miners:
            # Handle update or raise error depending on desired behavior
            print(f"Warning: Miner {miner.id} already exists, overwriting.")
        self._miners[miner.id] = copy.deepcopy(miner)

    def get_by_id(self, miner_id: EntityId) -> Optional[Miner]:
        """Get a miner by ID from the In-Memory repository."""
        return copy.deepcopy(self._miners.get(miner_id))

    def get_all(self) -> List[Miner]:
        """Get all miners from the In-Memory repository."""
        return [copy.deepcopy(m) for m in self._miners.values()]

    def update(self, miner: Miner) -> None:
        """Update a miner in the In-Memory repository."""
        if miner.id not in self._miners:
            raise ValueError(f"Miner {miner.id} not found for update.")
        self._miners[miner.id] = copy.deepcopy(miner)

    def remove(self, miner_id: EntityId) -> None:
        """Remove a miner from the In-Memory repository."""
        if miner_id in self._miners:
            del self._miners[miner_id]

    def get_by_controller_id(self, controller_id: EntityId) -> List[Miner]:
        """Get all miners that have at least one feature provided by the given controller."""
        if not controller_id:
            return []
        return [
            copy.deepcopy(m) for m in self._miners.values() if any(f.controller_id == controller_id for f in m.features)
        ]


class SqliteMinerRepository(MinerRepository):
    """SQLite implementation for the Miner Repository."""

    TABLE_NAME = "miners"
    FEATURES_TABLE_NAME = "miner_features"

    SCHEMA = {
        "id": "TEXT PRIMARY KEY",
        "name": "TEXT NOT NULL",
        "model": "TEXT",
        "active": "INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))",
        "hash_rate_max": "TEXT",
        "power_consumption_max": "REAL",
    }

    FEATURES_SCHEMA = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "miner_id": "TEXT NOT NULL",
        "controller_id": "TEXT NOT NULL",
        "feature_type": "TEXT NOT NULL",
        "priority": "INTEGER NOT NULL DEFAULT 50",
        "enabled": "INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1))",
    }

    def __init__(self, db: BaseSqliteRepository):
        self._db = db
        self.logger = db.logger

        self._db.create_tables(table_name=self.TABLE_NAME, schema=self.SCHEMA)
        self._db.create_tables(table_name=self.FEATURES_TABLE_NAME, schema=self.FEATURES_SCHEMA)

    def _dict_to_hashrate(self, data: Dict[str, Any]) -> HashRate:
        """Deserialize a dictionary (from JSON) into an HashRate object."""
        return HashRate(value=float(data["value"]), unit=data["unit"])

    def _hashrate_to_dict(self, hash_rate: Optional[HashRate]) -> Dict[str, Any]:
        """Serializes an HashRate object into a dictionary for JSON."""
        return {
            "value": hash_rate.value if hash_rate else 0,
            "unit": hash_rate.unit if hash_rate else "TH/s",
        }

    def _row_to_miner(self, row: sqlite3.Row, conn: Optional[sqlite3.Connection] = None) -> Optional[Miner]:
        """Deserialize a row from the database into a Miner object."""
        if not row:
            return None
        try:
            hash_rate_max_data = json.loads(row["hash_rate_max"]) if row["hash_rate_max"] else None
            hash_rate_max = self._dict_to_hashrate(hash_rate_max_data) if hash_rate_max_data else None

            miner_id = EntityId(row["id"])
            features: List[MinerFeature] = []
            if conn:
                features = self._load_features(conn, miner_id)

            return Miner(
                id=miner_id,
                name=row["name"] if row["name"] is not None else "",
                model=row["model"] if row["model"] is not None else None,
                active=(row["active"] == 1 if row["active"] is not None else False),
                hash_rate_max=hash_rate_max,
                power_consumption_max=(
                    Watts(row["power_consumption_max"]) if row["power_consumption_max"] is not None else None
                ),
                features=features,
            )
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error deserializing Miner from DB row: {row}. Error: {e}")
            return None

    def _load_features(self, conn: sqlite3.Connection, miner_id: EntityId) -> List[MinerFeature]:
        """Load features for a miner from the features table."""
        sql = f"SELECT * FROM {self.FEATURES_TABLE_NAME} WHERE miner_id = ?"
        cursor = conn.cursor()
        cursor.execute(sql, (str(miner_id),))
        rows = cursor.fetchall()
        features = []
        for r in rows:
            features.append(
                MinerFeature(
                    feature_type=MinerFeatureType(r["feature_type"]),
                    controller_id=EntityId(r["controller_id"]),
                    priority=r["priority"],
                    enabled=bool(r["enabled"]),
                )
            )
        return features

    def _save_features(self, conn: sqlite3.Connection, miner_id: EntityId, features: List[MinerFeature]) -> None:
        """Replace all features for a miner."""
        conn.execute(f"DELETE FROM {self.FEATURES_TABLE_NAME} WHERE miner_id = ?", (str(miner_id),))
        for f in features:
            conn.execute(
                f"INSERT INTO {self.FEATURES_TABLE_NAME} "
                "(miner_id, controller_id, feature_type, priority, enabled) "
                "VALUES (?, ?, ?, ?, ?)",
                (str(miner_id), str(f.controller_id), f.feature_type.value, f.priority, int(f.enabled)),
            )

    def add(self, miner: Miner) -> None:
        """Add a miner to the SQLite database."""
        self.logger.debug(f"Adding miner {miner.id} to SQLite.")

        sql = f"""
            INSERT INTO {self.TABLE_NAME} (id, name, model, active, hash_rate_max, power_consumption_max)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        conn = self._db.get_connection()
        try:
            hash_rate_max_json = json.dumps(self._hashrate_to_dict(miner.hash_rate_max))

            with conn:
                conn.execute(
                    sql,
                    (
                        miner.id,
                        miner.name,
                        miner.model,
                        miner.active,
                        hash_rate_max_json,
                        (float(miner.power_consumption_max) if miner.power_consumption_max is not None else 0.0),
                    ),
                )
                self._save_features(conn, miner.id, miner.features)
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Integrity error adding miner {miner.id}: {e}")
            # Could mean that the ID already exists
            raise MinerError(f"Miner with ID {miner.id} already exists or constraint violation: {e}") from e
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error adding miner {miner.id}: {e}")
            raise MinerError(f"DB error adding miner: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_id(self, miner_id: EntityId) -> Optional[Miner]:
        """Get a miner by ID from the SQLite database."""
        self.logger.debug(f"Getting miner {miner_id} from SQLite.")

        sql = f"SELECT * FROM {self.TABLE_NAME} WHERE id = ?"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (miner_id,))
            row = cursor.fetchone()
            return self._row_to_miner(row, conn)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error getting miner {miner_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_all(self) -> List[Miner]:
        """Get all miners from the SQLite database."""
        self.logger.debug("Getting all miners from SQLite.")

        sql = f"SELECT * FROM {self.TABLE_NAME}"
        conn = self._db.get_connection()
        miners = []
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                miner = self._row_to_miner(row, conn)
                if miner:
                    miners.append(miner)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error getting all miners: {e}")
            return []
        finally:
            if conn:
                conn.close()
        return miners

    def update(self, miner: Miner) -> None:
        """Update a miner in the SQLite database."""
        self.logger.debug(f"Updating miner {miner.id} in SQLite.")

        sql = f"""
            UPDATE {self.TABLE_NAME}
            SET name = ?, model = ?, active = ?, hash_rate_max = ?, power_consumption_max = ?
            WHERE id = ?
        """
        conn = self._db.get_connection()
        try:
            hash_rate_max_json = json.dumps(self._hashrate_to_dict(miner.hash_rate_max))

            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (
                        miner.name,
                        miner.model,
                        miner.active,
                        hash_rate_max_json,
                        (float(miner.power_consumption_max) if miner.power_consumption_max is not None else 0.0),
                        miner.id,
                    ),
                )
                if cursor.rowcount == 0:
                    raise MinerError(f"No miner found with ID {miner.id} for update.")
                self._save_features(conn, miner.id, miner.features)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error updating miner {miner.id}: {e}")
            raise MinerError(f"DB error updating miner: {e}") from e
        finally:
            if conn:
                conn.close()

    def remove(self, miner_id: EntityId) -> None:
        """Remove a miner from the SQLite database."""
        self.logger.debug(f"Removing miner {miner_id} from SQLite.")

        conn = self._db.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                # Delete features first
                cursor.execute(f"DELETE FROM {self.FEATURES_TABLE_NAME} WHERE miner_id = ?", (str(miner_id),))
                cursor.execute(f"DELETE FROM {self.TABLE_NAME} WHERE id = ?", (str(miner_id),))
                if cursor.rowcount == 0:
                    self.logger.warning(f"Attempt to remove non-existent miner with ID {miner_id}.")
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error removing miner {miner_id}: {e}")
            raise MinerError(f"DB error removing miner: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_controller_id(self, controller_id: EntityId) -> List[Miner]:
        """Get all miners that have at least one feature provided by the given controller."""
        self.logger.debug(f"Getting miners by controller ID {controller_id} from SQLite.")

        sql = f"""
            SELECT DISTINCT m.* FROM {self.TABLE_NAME} m
            INNER JOIN {self.FEATURES_TABLE_NAME} f ON m.id = f.miner_id
            WHERE f.controller_id = ?
        """
        conn = self._db.get_connection()
        miners = []
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (str(controller_id),))
            rows = cursor.fetchall()
            for row in rows:
                miner = self._row_to_miner(row, conn)
                if miner:
                    miners.append(miner)
            return miners
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error getting miners by controller ID {controller_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()


class SqlAlchemyMinerRepository(MinerRepository):
    """SQLAlchemy-based implementation of the MinerRepository port.

    Features are persisted in the miner_features table and loaded/saved
    separately from the Miner entity (which is mapped without the features field).
    """

    def __init__(self, db: BaseSQLAlchemyRepository):
        self._db = db
        self.logger = db.logger

    def _populate_features(self, session, miner: Miner) -> Miner:
        """Load features from DB and attach to the miner entity."""
        miner.features = load_features_for_miner(session, miner.id)
        return miner

    def add(self, miner: Miner) -> None:
        """Add a new miner to the repository."""
        session = self._db.get_session()
        try:
            features = list(miner.features)
            session.add(miner)
            session.flush()
            save_features_for_miner(session, miner.id, features)
            session.commit()
            miner.features = features
        finally:
            session.close()

    def get_by_id(self, miner_id: EntityId) -> Optional[Miner]:
        """Retrieve a miner by its ID."""
        session = self._db.get_session()
        try:
            stmt = select(Miner).where(miners_table.c.id == str(miner_id))
            entity = session.execute(stmt).scalar_one_or_none()
            if entity:
                self._populate_features(session, entity)
            return entity
        finally:
            session.close()

    def get_all(self) -> List[Miner]:
        """Retrieve all miners from the repository."""
        session = self._db.get_session()
        try:
            stmt = select(Miner)
            entities = session.execute(stmt).scalars().all()
            for entity in entities:
                self._populate_features(session, entity)
            return list(entities)
        finally:
            session.close()

    def update(self, miner: Miner) -> None:
        """Update an existing miner in the repository."""
        session = self._db.get_session()
        try:
            stmt = select(Miner).where(miners_table.c.id == str(miner.id))
            existing_entity = session.execute(stmt).scalar_one_or_none()

            if existing_entity:
                existing_entity.name = miner.name
                existing_entity.model = miner.model
                existing_entity.active = miner.active
                existing_entity.hash_rate_max = miner.hash_rate_max
                existing_entity.power_consumption_max = miner.power_consumption_max

                save_features_for_miner(session, miner.id, miner.features)
                session.commit()
                existing_entity.features = list(miner.features)
        finally:
            session.close()

    def remove(self, miner_id: EntityId) -> None:
        """Remove a miner from the repository."""
        session = self._db.get_session()
        try:
            delete_features_for_miner(session, miner_id)
            stmt = select(Miner).where(miners_table.c.id == str(miner_id))
            entity = session.execute(stmt).scalar_one_or_none()

            if entity:
                session.delete(entity)
                session.commit()
        finally:
            session.close()

    def get_by_controller_id(self, controller_id: EntityId) -> List[Miner]:
        """Retrieve all miners that have at least one feature from the given controller."""
        session = self._db.get_session()
        try:
            # Subquery: distinct miner_ids from miner_features where controller matches
            subq = (
                select(miner_features_table.c.miner_id)
                .where(miner_features_table.c.controller_id == str(controller_id))
                .distinct()
                .subquery()
            )
            stmt = select(Miner).where(miners_table.c.id.in_(select(subq)))
            entities = session.execute(stmt).scalars().all()
            for entity in entities:
                self._populate_features(session, entity)
            return list(entities)
        finally:
            session.close()


class InMemoryMinerControllerRepository(MinerControllerRepository):
    """In-Memory implementation for the Miner Controller Repository."""

    def __init__(
        self,
        initial_miner_controllers: Optional[Dict[EntityId, MinerController]] = None,
    ):
        self._miner_controllers: Dict[EntityId, MinerController] = (
            copy.deepcopy(initial_miner_controllers) if initial_miner_controllers else {}
        )

    def add(self, miner_controller: MinerController) -> None:
        """Add a miner controller to the In-Memory repository."""
        if miner_controller.id in self._miner_controllers:
            # Handle update or raise error depending on desired behavior
            print(f"Warning: Miner Controller {miner_controller.id} already exists, overwriting.")
        self._miner_controllers[miner_controller.id] = copy.deepcopy(miner_controller)

    def get_by_id(self, miner_controller_id: EntityId) -> Optional[MinerController]:
        """Get a miner controller by ID from the In-Memory repository."""
        return copy.deepcopy(self._miner_controllers.get(miner_controller_id))

    def get_all(self) -> List[MinerController]:
        """Get all miner controllers from the In-Memory repository."""
        return [copy.deepcopy(m) for m in self._miner_controllers.values()]

    def update(self, miner_controller: MinerController) -> None:
        """Update a miner controller in the In-Memory repository."""
        if miner_controller.id not in self._miner_controllers:
            raise ValueError(f"Miner Controller {miner_controller.id} not found for update.")
        self._miner_controllers[miner_controller.id] = copy.deepcopy(miner_controller)

    def remove(self, miner_controller_id: EntityId) -> None:
        """Remove a miner controller from the In-Memory repository."""
        if miner_controller_id in self._miner_controllers:
            del self._miner_controllers[miner_controller_id]

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[MinerController]:
        """Get all miner controllers associated with a specific external service ID."""
        return (
            [
                copy.deepcopy(mc)
                for mc in self._miner_controllers.values()
                if mc.external_service_id == external_service_id
            ]
            if external_service_id
            else []
        )


class SqliteMinerControllerRepository(MinerControllerRepository):
    """SQLite implementation for the Miner Controller Repository."""

    TABLE_NAME = "miner_controllers"

    # Declarative schema definition
    # NOTE: If you modify SCHEMA, update BaseSqliteRepository.CURRENT_DB_VERSION
    SCHEMA = {
        "id": "TEXT PRIMARY KEY",
        "name": "TEXT NOT NULL",
        "adapter_type": "TEXT NOT NULL",
        "config": "TEXT",  # JSON object of config
        "external_service_id": "TEXT",  # Optional ID for external service integration
    }

    def __init__(self, db: BaseSqliteRepository):
        self._db = db
        self.logger = db.logger

        # BaseSqliteRepository generates CREATE TABLE SQL automatically
        self._db.create_tables(
            table_name=self.TABLE_NAME,
            schema=self.SCHEMA,
        )

    def _deserialize_config(self, adapter_type: MinerControllerAdapter, config_json: str) -> MinerControllerConfig:
        """Deserialize a JSON string into MinerControllerConfig object."""
        data: dict = json.loads(config_json)

        if adapter_type not in MINER_CONTROLLER_CONFIG_TYPE_MAP:
            raise MinerControllerConfigurationError(
                f"Error reading MinerController configuration. Invalid type '{adapter_type}'"
            )

        config_class: Optional[type[MinerControllerConfig]] = MINER_CONTROLLER_CONFIG_TYPE_MAP.get(adapter_type)
        if not config_class:
            raise MinerControllerConfigurationError(
                f"Error creating MinerController configuration. Type '{adapter_type}'"
            )

        config_instance = config_class.from_dict(data)
        if not isinstance(config_instance, MinerControllerConfig):
            raise MinerControllerConfigurationError(
                f"Deserialized config is not of type MinerControllerConfig for adapter type {adapter_type}."
            )
        return config_instance

    def _row_to_miner_controller(self, row: sqlite3.Row) -> Optional[MinerController]:
        """Deserialize a row from the database into a MinerController object."""
        if not row:
            return None
        try:
            miner_controller_type = MinerControllerAdapter(row["adapter_type"])

            # Deserialize the config from the database row
            config = self._deserialize_config(miner_controller_type, row["config"])

            return MinerController(
                id=EntityId(row["id"]),
                name=row["name"],
                adapter_type=miner_controller_type,
                config=config,
                external_service_id=(EntityId(row["external_service_id"]) if row["external_service_id"] else None),
            )
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error deserializing MinerController from DB row: {row}. Error: {e}")
            return None

    def add(self, miner_controller: MinerController) -> None:
        """Add a miner controller to the SQLite database."""
        self.logger.debug(f"Adding miner controller {miner_controller.id} to SQLite.")

        sql = f"""
            INSERT INTO {self.TABLE_NAME} (id, name, adapter_type, config, external_service_id)
            VALUES (?, ?, ?, ?, ?)
        """
        conn = self._db.get_connection()
        try:
            # Serialize config to JSON for storage
            config_json: str = ""
            if miner_controller.config:
                config_json = json.dumps(miner_controller.config.to_dict())

            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (
                        miner_controller.id,
                        miner_controller.name,
                        miner_controller.adapter_type.value,
                        config_json,
                        miner_controller.external_service_id,
                    ),
                )
        except sqlite3.IntegrityError as e:
            self.logger.error(f"Integrity error adding miner controller {miner_controller.id}: {e}")
            # Could mean that the ID already exists
            raise MinerControllerAlreadyExistsError(
                f"Miner Controller with ID {miner_controller.id} already exists or constraint violation: {e}"
            ) from e
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error adding miner controller {miner_controller.id}: {e}")
            raise MinerControllerError(f"DB error adding miner controller: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_id(self, miner_controller_id: EntityId) -> Optional[MinerController]:
        """Get a miner controller by ID from the SQLite database."""
        self.logger.debug(f"Getting miner controller {miner_controller_id} from SQLite.")

        sql = f"SELECT * FROM {self.TABLE_NAME} WHERE id = ?;"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (miner_controller_id,))
            row = cursor.fetchone()
            return self._row_to_miner_controller(row)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error getting miner controller {miner_controller_id}: {e}")
            return None  # Or raise exception? Returning None is more forgiving
        finally:
            if conn:
                conn.close()

    def get_all(self) -> List[MinerController]:
        """Get all miner controllers from the SQLite database."""
        self.logger.debug("Getting all miner controllers from SQLite.")

        sql = f"SELECT * FROM {self.TABLE_NAME}"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            miner_controllers = []
            for row in rows:
                miner_controller = self._row_to_miner_controller(row)
                if miner_controller:
                    miner_controllers.append(miner_controller)
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error getting all miner controllers: {e}")
            return []
        finally:
            if conn:
                conn.close()
        return miner_controllers

    def update(self, miner_controller: MinerController) -> None:
        """Update a miner controller in the SQLite database."""
        self.logger.debug(f"Updating miner controller {miner_controller.id} in SQLite.")

        sql = f"""
            UPDATE {self.TABLE_NAME}
            SET name = ?, adapter_type = ?, config = ?, external_service_id = ?
            WHERE id = ?
        """
        conn = self._db.get_connection()
        try:
            # Serialize config to JSON for storage
            config_json: str = ""
            if miner_controller.config:
                config_json = json.dumps(miner_controller.config.to_dict())

            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    sql,
                    (
                        miner_controller.name,
                        miner_controller.adapter_type.value,
                        config_json,
                        miner_controller.external_service_id,
                        miner_controller.id,
                    ),
                )
                if cursor.rowcount == 0:
                    raise MinerControllerNotFoundError(
                        f"No miner controller found with ID {miner_controller.id} for update."
                    )
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error updating miner controller {miner_controller.id}: {e}")
            raise MinerControllerError(f"DB error updating miner controller: {e}") from e
        finally:
            if conn:
                conn.close()

    def remove(self, miner_controller_id: EntityId) -> None:
        """Remove a miner controller from the SQLite database."""
        self.logger.debug(f"Removing miner controller {miner_controller_id} from SQLite.")

        sql = f"DELETE FROM {self.TABLE_NAME} WHERE id = ?"
        conn = self._db.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(sql, (miner_controller_id,))
                if cursor.rowcount == 0:
                    self.logger.warning(
                        f"Attempt to remove non-existent miner controller with ID {miner_controller_id}."
                    )
                    # There is no need to raise an exception here, removing a
                    # non-existent is idempotent.
        except sqlite3.Error as e:
            self.logger.error(f"SQLite error removing miner controller {miner_controller_id}: {e}")
            raise MinerControllerError(f"DB error removing miner controller: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[MinerController]:
        """Get all miner controllers associated with a specific external service ID."""
        self.logger.debug(f"Getting miner controllers for external service ID {external_service_id} from SQLite.")

        sql = f"SELECT * FROM {self.TABLE_NAME} WHERE external_service_id = ?"
        conn = self._db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (external_service_id,))
            rows = cursor.fetchall()
            miner_controllers = []
            for row in rows:
                miner_controller = self._row_to_miner_controller(row)
                if miner_controller:
                    miner_controllers.append(miner_controller)
            return miner_controllers
        except sqlite3.Error as e:
            self.logger.error(
                f"SQLite error getting miner controllers by external service ID {external_service_id}: {e}"
            )
            return []
        finally:
            if conn:
                conn.close()


class SqlAlchemyMinerControllerRepository(MinerControllerRepository):
    """SQLAlchemy-based implementation of the MinerControllerRepository port.

    This repository works directly with the imperatively mapped MinerController domain entity.
    The config field is automatically converted between MinerControllerConfig objects and JSON
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

    def add(self, miner_controller: MinerController) -> None:
        """Add a new miner controller to the repository.

        Args:
            miner_controller: Domain entity to persist
        """
        session = self._db.get_session()
        try:
            session.add(miner_controller)
            session.commit()
        except Exception as e:
            session.rollback()
            if "UNIQUE constraint failed" in str(e) or "already exists" in str(e):
                raise MinerControllerAlreadyExistsError(
                    f"Miner Controller with ID {miner_controller.id} already exists: {e}"
                ) from e
            raise MinerControllerError(f"Error adding miner controller: {e}") from e
        finally:
            session.close()

    def get_by_id(self, miner_controller_id: EntityId) -> Optional[MinerController]:
        """Retrieve a miner controller by its ID.

        Args:
            miner_controller_id: Unique identifier of the miner controller

        Returns:
            Domain entity if found, None otherwise
        """
        session = self._db.get_session()
        try:
            stmt = select(MinerController).where(miner_controllers_table.c.id == str(miner_controller_id))
            entity = session.execute(stmt).scalar_one_or_none()
            return entity
        finally:
            session.close()

    def get_all(self) -> List[MinerController]:
        """Retrieve all miner controllers from the repository.

        Returns:
            List of all miner controller domain entities
        """
        session = self._db.get_session()
        try:
            stmt = select(MinerController)
            entities = session.execute(stmt).scalars().all()
            return list(entities)
        finally:
            session.close()

    def update(self, miner_controller: MinerController) -> None:
        """Update an existing miner controller in the repository.

        Args:
            miner_controller: Domain entity with updated state
        """
        session = self._db.get_session()
        try:
            stmt = select(MinerController).where(miner_controllers_table.c.id == str(miner_controller.id))
            existing_controller = session.execute(stmt).scalar_one_or_none()

            if existing_controller:
                # Update all fields from the new entity
                existing_controller.name = miner_controller.name
                existing_controller.adapter_type = miner_controller.adapter_type
                existing_controller.external_service_id = miner_controller.external_service_id
                existing_controller.config = miner_controller.config

                # SQLAlchemy's dirty tracking + TypeDecorator will handle serialization automatically
                session.commit()
            else:
                raise MinerControllerNotFoundError(
                    f"No miner controller found with ID {miner_controller.id} for update."
                )
        except MinerControllerNotFoundError:
            raise
        except Exception as e:
            session.rollback()
            raise MinerControllerError(f"Error updating miner controller: {e}") from e
        finally:
            session.close()

    def remove(self, miner_controller_id: EntityId) -> None:
        """Remove a miner controller from the repository.

        Args:
            miner_controller_id: Unique identifier of the miner controller to remove
        """
        session = self._db.get_session()
        try:
            stmt = select(MinerController).where(miner_controllers_table.c.id == str(miner_controller_id))
            entity = session.execute(stmt).scalar_one_or_none()

            if entity:
                session.delete(entity)
                session.commit()
        finally:
            session.close()

    def get_by_external_service_id(self, external_service_id: EntityId) -> List[MinerController]:
        """Retrieve all miner controllers associated with a specific external service.

        Args:
            external_service_id: Unique identifier of the external service

        Returns:
            List of miner controller domain entities associated with the external service
        """
        session = self._db.get_session()
        try:
            stmt = select(MinerController).where(
                miner_controllers_table.c.external_service_id == str(external_service_id)
            )
            entities = session.execute(stmt).scalars().all()
            return list(entities)
        finally:
            session.close()
