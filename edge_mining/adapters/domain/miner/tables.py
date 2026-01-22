"""SQLAlchemy ORM mappings for Miner domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

The mappings handle value objects (HashRate, Watts) using SQLAlchemy's composite()
to map multiple columns to single value object instances.

All tables and mappings use the shared metadata and mapper registry from
the sqlalchemy.registry module, which are available as module-level singletons.
"""

import json
from typing import Optional

from sqlalchemy import Boolean, Column, Float, ForeignKey, String, Table, TypeDecorator, event
from sqlalchemy.orm import relationship

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.common import ConfigurationType
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.common import Watts
from edge_mining.domain.miner.common import MinerControllerAdapter, MinerStatus
from edge_mining.domain.miner.entities import Miner, MinerController
from edge_mining.domain.miner.exceptions import MinerControllerConfigurationError
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.shared.adapter_maps.miner import MINER_CONTROLLER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import MinerControllerConfig


class MinerControllerConfigType(ConfigurationType):
    """SQLAlchemy type for MinerControllerConfig serialization.

    Inherits from ConfigurationType to handle JSON serialization/deserialization.
    """


class MinerStatusType(TypeDecorator):
    """Custom SQLAlchemy type that converts MinerStatus enum to/from string.

    SQLite doesn't natively support enums, so we need to convert them to strings.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[MinerStatus], dialect) -> Optional[str]:
        """Convert MinerStatus enum to string before storing in DB.

        Args:
            value: MinerStatus enum instance or None
            dialect: SQLAlchemy dialect

        Returns:
            String value of enum or None
        """
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.value  # Get the string value from enum

    def process_result_value(self, value: Optional[str], dialect) -> Optional[MinerStatus]:
        """Convert string back to MinerStatus enum after loading from DB.

        Args:
            value: String from database or None
            dialect: SQLAlchemy dialect

        Returns:
            MinerStatus enum instance or None
        """
        if value is None:
            return None
        if isinstance(value, MinerStatus):
            return value
        return MinerStatus(value)


def _deserialize_miner_controller_config(
    adapter_type: MinerControllerAdapter, config_json: str
) -> Optional[MinerControllerConfig]:
    """Deserialize JSON string to MinerControllerConfig based on adapter type.

    Args:
        adapter_type: The type of miner controller adapter
        config_json: JSON string representation of config

    Returns:
        MinerControllerConfig instance or None
    """
    if not config_json:
        return None

    data: dict = json.loads(config_json)

    if adapter_type not in MINER_CONTROLLER_CONFIG_TYPE_MAP:
        raise MinerControllerConfigurationError(
            f"Error reading MinerController configuration. Invalid type '{adapter_type}'"
        )

    config_class: Optional[type[MinerControllerConfig]] = MINER_CONTROLLER_CONFIG_TYPE_MAP.get(adapter_type)
    if not config_class:
        raise MinerControllerConfigurationError(f"Error creating MinerController configuration. Type '{adapter_type}'")

    config_instance = config_class.from_dict(data)
    if not isinstance(config_instance, MinerControllerConfig):
        raise MinerControllerConfigurationError(
            f"Deserialized config is not of type MinerControllerConfig for adapter type {adapter_type}."
        )
    return config_instance


@event.listens_for(MinerController, "load")
def _receive_miner_controller_load(target: MinerController, context) -> None:
    """Event listener that deserializes config after loading from database.

    Args:
        target: The MinerController instance being loaded
        context: SQLAlchemy context
    """
    # Convert adapter_type string to enum if needed
    if isinstance(target.adapter_type, str):
        try:
            target.adapter_type = MinerControllerAdapter(target.adapter_type)
        except ValueError:
            # If conversion fails, leave as string (will fail in config deserialization)
            pass

    if target.config and isinstance(target.config, str):
        target.config = _deserialize_miner_controller_config(target.adapter_type, target.config)


# Define the miner_controllers table using imperative style
miner_controllers_table = Table(
    "miner_controllers",
    metadata,
    # Primary Key
    Column("id", String, primary_key=True, index=True),
    # Basic attributes
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False, default="DUMMY"),
    # Config stored as JSON string with automatic conversion
    Column("config", MinerControllerConfigType, nullable=True),
    # External service reference
    Column("external_service_id", String, nullable=True),
)

# Define the miners table using imperative style
miners_table = Table(
    "miners",
    metadata,
    # Primary Key
    Column("id", String, primary_key=True, index=True),
    # Basic attributes
    Column("name", String, nullable=False),
    Column("model", String, nullable=True),
    Column("status", MinerStatusType, nullable=False, default="UNKNOWN"),
    Column("active", Boolean, nullable=False, default=True),
    # Hash Rate Value Object - stored as TEXT (JSON) in SQLite to match existing schema
    Column("hash_rate", String, nullable=True),
    Column("hash_rate_max", String, nullable=True),
    # Power Consumption (Watts Value Object stored as float)
    Column("power_consumption", Float, nullable=True),
    Column("power_consumption_max", Float, nullable=True),
    # Foreign Key to MinerController
    Column("controller_id", String, ForeignKey("miner_controllers.id"), nullable=True),
)

# Map MinerController first (parent in the relationship)
mapper_registry.map_imperatively(
    MinerController,
    miner_controllers_table,
    properties={
        "miners": relationship(
            "Miner",
            back_populates="controller",
            lazy="select",
        )
    },
)

# Map Miner (child in the relationship) - use event listeners for value object conversions
mapper_registry.map_imperatively(
    Miner,
    miners_table,
    properties={
        # Relationship to controller
        "controller": relationship(
            "MinerController",
            foreign_keys=[miners_table.c.controller_id],
            lazy="joined",
        ),
    },
    # Don't exclude properties - let SQLAlchemy load them, then convert in event listener
)


# Event listeners for value object conversions
@event.listens_for(Miner, "load")
def _receive_miner_load(target: Miner, context) -> None:
    """Event listener that reconstructs value objects after loading.

    Args:
        target: The Miner instance being loaded
        context: SQLAlchemy context
    """
    # SQLAlchemy will load the raw column values as strings/floats
    # We need to convert them to proper value objects

    # Reconstruct hash_rate (HashRate) from JSON string
    if hasattr(target, "hash_rate") and target.hash_rate:
        if isinstance(target.hash_rate, str):
            try:
                hash_rate_data = json.loads(target.hash_rate)
                target.hash_rate = HashRate(value=hash_rate_data.get("value"), unit=hash_rate_data.get("unit", "TH/s"))
            except (json.JSONDecodeError, TypeError, KeyError):
                target.hash_rate = None

    # Reconstruct hash_rate_max (HashRate) from JSON string
    if hasattr(target, "hash_rate_max") and target.hash_rate_max:
        if isinstance(target.hash_rate_max, str):
            try:
                hash_rate_max_data = json.loads(target.hash_rate_max)
                target.hash_rate_max = HashRate(
                    value=hash_rate_max_data.get("value"), unit=hash_rate_max_data.get("unit", "TH/s")
                )
            except (json.JSONDecodeError, TypeError, KeyError):
                target.hash_rate_max = None

    # Convert power_consumption to Watts (it's loaded as float)
    if hasattr(target, "power_consumption") and target.power_consumption is not None:
        if not isinstance(target.power_consumption, type(Watts(0.0))):
            target.power_consumption = Watts(float(target.power_consumption))

    # Convert power_consumption_max to Watts (it's loaded as float)
    if hasattr(target, "power_consumption_max") and target.power_consumption_max is not None:
        if not isinstance(target.power_consumption_max, type(Watts(0.0))):
            target.power_consumption_max = Watts(float(target.power_consumption_max))


@event.listens_for(Miner, "before_insert")
@event.listens_for(Miner, "before_update")
def _flatten_miner_value_objects(mapper, connection, target: Miner) -> None:
    """Event listener that flattens value objects before persisting.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: The Miner instance being persisted
    """
    # Flatten hash_rate (HashRate) to JSON string
    if hasattr(target, "hash_rate") and target.hash_rate is not None:
        if not isinstance(target.hash_rate, str):
            hash_rate_dict = {"value": target.hash_rate.value, "unit": target.hash_rate.unit}
            target.hash_rate = json.dumps(hash_rate_dict)

    # Flatten hash_rate_max (HashRate) to JSON string
    if hasattr(target, "hash_rate_max") and target.hash_rate_max is not None:
        if not isinstance(target.hash_rate_max, str):
            hash_rate_max_dict = {"value": target.hash_rate_max.value, "unit": target.hash_rate_max.unit}
            target.hash_rate_max = json.dumps(hash_rate_max_dict)

    # Flatten power_consumption (Watts) to float
    # Watts is a NewType (alias for float), so just ensure it's a float
    if hasattr(target, "power_consumption") and target.power_consumption is not None:
        target.power_consumption = float(target.power_consumption)

    # Flatten power_consumption_max (Watts) to float
    if hasattr(target, "power_consumption_max") and target.power_consumption_max is not None:
        target.power_consumption_max = float(target.power_consumption_max)
