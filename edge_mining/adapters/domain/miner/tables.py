"""SQLAlchemy ORM mappings for Miner domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

The mappings handle value objects and enums using SQLAlchemy event listeners and custom types:
- HashRate is serialized to JSON strings and reconstructed after loading
- Watts is flattened to float columns for persistence and reconstructed after loading
- MinerStatus enum uses custom TypeDecorator for string conversion
- MinerControllerConfig is serialized using custom ConfigurationType

All tables and mappings use the shared metadata and mapper registry from
the sqlalchemy.registry module, which are available as module-level singletons.

⚠️  DEVELOPER WARNING ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANY SCHEMA CHANGE (adding/removing/modifying tables or columns) REQUIRES an
Alembic migration. Do NOT modify this file without creating a migration:

  python scripts/migrate.py create "Description of your change"

For detailed instructions, see: docs/ALEMBIC_MIGRATIONS.md
For a step-by-step example, see: docs/MIGRATION_EXAMPLE.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import uuid
from typing import Any, Optional

from sqlalchemy import Boolean, Column, Float, ForeignKey, String, Table, event
from sqlalchemy.orm import relationship

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.common import ConfigurationType
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.common import EntityId, Watts
from edge_mining.domain.miner.common import MinerControllerAdapter
from edge_mining.domain.miner.entities import Miner, MinerController
from edge_mining.domain.miner.exceptions import MinerControllerConfigurationError
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.shared.adapter_maps.miner import MINER_CONTROLLER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import MinerControllerConfig


class MinerControllerConfigType(ConfigurationType):
    """SQLAlchemy type for MinerControllerConfig serialization.

    Inherits from ConfigurationType to handle JSON serialization/deserialization.
    """


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
    # Convert id string to EntityId if needed
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):
            target.id = EntityId(uuid.UUID(target.id))

    # Convert foreign keys to EntityId
    if hasattr(target, "external_service_id") and target.external_service_id is not None:
        if isinstance(target.external_service_id, str):
            target.external_service_id = EntityId(uuid.UUID(target.external_service_id))

    # Convert adapter_type string to enum if needed
    if isinstance(target.adapter_type, str):
        try:
            target.adapter_type = MinerControllerAdapter(target.adapter_type)
        except ValueError:
            # If conversion fails, leave as string (will fail in config deserialization)
            pass

    if target.config and isinstance(target.config, str):
        target.config = _deserialize_miner_controller_config(target.adapter_type, target.config)


@event.listens_for(MinerController, "before_insert")
@event.listens_for(MinerController, "before_update")
def _flatten_miner_controller_composites(mapper, connection, target: Any) -> None:
    """Convert enum attributes to primitive values before persisting."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, MinerControllerAdapter):
            target.adapter_type = target.adapter_type.value


@event.listens_for(MinerController, "after_insert")
@event.listens_for(MinerController, "after_update")
def _restore_miner_controller_composites(mapper, connection, target: Any) -> None:
    """Restore enum attributes after persist operations."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, str):
            try:
                target.adapter_type = MinerControllerAdapter(target.adapter_type)
            except ValueError:
                pass


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
    Column("external_service_id", String, ForeignKey("external_services.id"), nullable=True),
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
    Column("active", Boolean, nullable=False, default=True),
    # Hash Rate Max Value Object - stored as TEXT (JSON) in SQLite to match existing schema
    Column("hash_rate_max", String, nullable=True),
    # Power Consumption Max (Watts Value Object stored as float)
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
    # Flatten hash_rate_max (HashRate) to JSON string
    if hasattr(target, "hash_rate_max") and target.hash_rate_max is not None:
        if not isinstance(target.hash_rate_max, str):
            hash_rate_max_dict = {"value": target.hash_rate_max.value, "unit": target.hash_rate_max.unit}
            target.hash_rate_max = json.dumps(hash_rate_max_dict)  # type: ignore[assignment]

    # Flatten power_consumption_max (Watts) to float
    if hasattr(target, "power_consumption_max") and target.power_consumption_max is not None:
        target.power_consumption_max = float(target.power_consumption_max)  # type: ignore[assignment]


@event.listens_for(Miner, "after_insert")
@event.listens_for(Miner, "after_update")
def _restore_miner_composites(mapper, connection, target: Any) -> None:
    """Event listener that restores value objects after persisting.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: The Miner instance that was persisted
    """
    # Restore id to EntityId if it was converted to string
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):
            target.id = EntityId(uuid.UUID(target.id))

    # Restore controller_id to EntityId if needed
    if hasattr(target, "controller_id") and target.controller_id is not None:
        if isinstance(target.controller_id, str):
            target.controller_id = EntityId(uuid.UUID(target.controller_id))

    # Restore hash_rate_max from JSON string
    if hasattr(target, "hash_rate_max") and target.hash_rate_max is not None:
        if isinstance(target.hash_rate_max, str):
            try:
                hash_rate_max_data = json.loads(target.hash_rate_max)
                target.hash_rate_max = HashRate(
                    value=hash_rate_max_data.get("value"), unit=hash_rate_max_data.get("unit", "TH/s")
                )
            except (json.JSONDecodeError, TypeError, KeyError):
                pass

    # Restore Watts values
    if hasattr(target, "power_consumption_max") and target.power_consumption_max is not None:
        if not isinstance(target.power_consumption_max, type(Watts(0.0))):
            target.power_consumption_max = Watts(float(target.power_consumption_max))
