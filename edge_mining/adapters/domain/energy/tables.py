"""SQLAlchemy ORM mappings for Energy domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

The mappings handle value objects (Battery, Grid, Watts) using SQLAlchemy event listeners
to convert between domain objects and database columns. Complex value objects (Battery, Grid)
are stored as JSON for flexibility, while simple value objects (Watts) are stored as floats.

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

from sqlalchemy import JSON, Column, Float, ForeignKey, String, Table, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.common import ConfigurationType
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.common import EntityId, WattHours, Watts
from edge_mining.domain.energy.common import EnergyMonitorAdapter, EnergySourceType
from edge_mining.domain.energy.entities import EnergyMonitor, EnergySource
from edge_mining.domain.energy.exceptions import EnergyMonitorConfigurationError
from edge_mining.domain.energy.value_objects import Battery, Grid
from edge_mining.shared.adapter_maps.energy import ENERGY_MONITOR_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import EnergyMonitorConfig


class EnergyMonitorConfigType(ConfigurationType):
    """SQLAlchemy type for EnergyMonitorConfig serialization.

    Inherits from ConfigurationType to handle JSON serialization/deserialization.
    """


def _deserialize_energy_monitor_config(
    adapter_type: EnergyMonitorAdapter, config_json: str
) -> Optional[EnergyMonitorConfig]:
    """Deserialize JSON string to EnergyMonitorConfig based on adapter type.

    Args:
        adapter_type: The type of energy monitor adapter
        config_json: JSON string representation of config

    Returns:
        EnergyMonitorConfig instance or None
    """
    if not config_json:
        return None

    data: dict = json.loads(config_json)

    if adapter_type not in ENERGY_MONITOR_CONFIG_TYPE_MAP:
        raise EnergyMonitorConfigurationError(
            f"Error reading EnergyMonitor configuration. Invalid type '{adapter_type}'"
        )

    config_class: Optional[type[EnergyMonitorConfig]] = ENERGY_MONITOR_CONFIG_TYPE_MAP.get(adapter_type)
    if not config_class:
        raise EnergyMonitorConfigurationError(f"Error creating EnergyMonitor configuration. Type '{adapter_type}'")

    config_instance = config_class.from_dict(data)
    if not isinstance(config_instance, EnergyMonitorConfig):
        raise EnergyMonitorConfigurationError(
            f"Deserialized config is not of type EnergyMonitorConfig for adapter type {adapter_type}."
        )
    return config_instance


@event.listens_for(EnergyMonitor, "load")
def _receive_energy_monitor_load(target: EnergyMonitor, context) -> None:
    """Event listener that deserializes config after loading from database.

    Args:
        target: The EnergyMonitor instance being loaded
        context: SQLAlchemy context
    """
    # Convert id string to EntityId if needed
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore[arg-type,misc]
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore[assignment]

    # Convert foreign keys to EntityId
    # NOTE: SQLAlchemy returns strings for UUID columns that need conversion to EntityId
    if hasattr(target, "external_service_id") and target.external_service_id is not None:
        if isinstance(target.external_service_id, str):  # type: ignore
            target.external_service_id = EntityId(uuid.UUID(target.external_service_id))  # type: ignore

    # Convert adapter_type string to enum if needed
    if isinstance(target.adapter_type, str):
        try:
            target.adapter_type = EnergyMonitorAdapter(target.adapter_type)
        except ValueError:
            # If conversion fails, leave as string (will fail in config deserialization)
            pass

    if target.config and isinstance(target.config, str):
        target.config = _deserialize_energy_monitor_config(target.adapter_type, target.config)


@event.listens_for(EnergyMonitor, "before_insert")
@event.listens_for(EnergyMonitor, "before_update")
def _flatten_energy_monitor_composites(mapper, connection, target: Any) -> None:
    """Event listener that flattens value objects before persisting.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: The EnergyMonitor instance being persisted
    """
    # Convert EnergyMonitorAdapter enum to string
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, EnergyMonitorAdapter):
            target.adapter_type = target.adapter_type.value


@event.listens_for(EnergyMonitor, "after_insert")
@event.listens_for(EnergyMonitor, "after_update")
def _restore_energy_monitor_composites(mapper, connection, target: Any) -> None:
    """Event listener that restores value objects after persisting.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: The EnergyMonitor instance that was persisted
    """
    # Restore id to EntityId if it was converted to string
    # NOTE: After SQLAlchemy flush, IDs may be strings and need restoration to EntityId
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore

    # Restore external_service_id to EntityId if needed
    if hasattr(target, "external_service_id") and target.external_service_id is not None:
        if isinstance(target.external_service_id, str):  # type: ignore
            target.external_service_id = EntityId(uuid.UUID(target.external_service_id))  # type: ignore

    # Restore adapter_type to enum
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, str):
            try:
                target.adapter_type = EnergyMonitorAdapter(target.adapter_type)
            except ValueError:
                pass


# Define the energy_monitors table using imperative style
energy_monitors_table = Table(
    "energy_monitors",
    metadata,
    # Primary Key
    Column("id", String, primary_key=True, index=True),
    # Basic attributes
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False, default="DUMMY_SOLAR"),
    # Config stored as JSON string with automatic conversion
    Column("config", EnergyMonitorConfigType, nullable=True),
    # External service reference
    Column("external_service_id", String, ForeignKey("external_services.id"), nullable=True),
)

# Define the energy_sources table using imperative style
energy_sources_table = Table(
    "energy_sources",
    metadata,
    # Primary Key
    Column("id", String, primary_key=True, index=True),
    # Basic attributes
    Column("name", String, nullable=False),
    Column("type", String, nullable=False, default="SOLAR"),
    # Watts value objects stored as float
    Column("nominal_power_max", Float, nullable=True),
    # Battery Value Object stored as JSON
    Column("storage", JSON, nullable=True),
    # Grid Value Object stored as JSON
    Column("grid", JSON, nullable=True),
    # External source power (Watts stored as float)
    Column("external_source", Float, nullable=True),
    # Foreign Keys to other entities
    Column("energy_monitor_id", String, ForeignKey("energy_monitors.id"), nullable=True),
    Column("forecast_provider_id", String, ForeignKey("forecast_providers.id"), nullable=True),
)

# Map EnergyMonitor first (parent in some relationships)
mapper_registry.map_imperatively(
    EnergyMonitor,
    energy_monitors_table,
)

# Map EnergySource - use event listeners for all value object conversions
mapper_registry.map_imperatively(
    EnergySource,
    energy_sources_table,
    # Don't exclude properties - let SQLAlchemy load them, then convert in event listener
)


# Event listeners for value object conversions
@event.listens_for(EnergySource, "load")
def _receive_energy_source_load(target: EnergySource, context) -> None:
    """Event listener that reconstructs value objects after loading.

    Args:
        target: The EnergySource instance being loaded
        context: SQLAlchemy context
    """
    # SQLAlchemy will load the raw column values as floats/strings
    # We need to convert them to proper value objects

    # Convert id string to EntityId if needed
    # NOTE: Type checker marks this as unreachable because EntityId is typed as UUID,
    # but SQLAlchemy can return strings from the database that need conversion
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore
        if isinstance(target.id, str):  # type: ignore
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore

    # Convert foreign keys to EntityId
    # NOTE: SQLAlchemy returns strings for UUID columns that need conversion to EntityId
    if hasattr(target, "energy_monitor_id") and target.energy_monitor_id is not None:
        if isinstance(target.energy_monitor_id, str):  # type: ignore
            target.energy_monitor_id = EntityId(uuid.UUID(target.energy_monitor_id))  # type: ignore

    if hasattr(target, "forecast_provider_id") and target.forecast_provider_id is not None:
        if isinstance(target.forecast_provider_id, str):  # type: ignore
            target.forecast_provider_id = EntityId(uuid.UUID(target.forecast_provider_id))  # type: ignore

    # Convert type string to enum if needed
    if hasattr(target, "type") and target.type is not None:
        if isinstance(target.type, str):
            try:
                target.type = EnergySourceType(target.type)
            except ValueError:
                # If conversion fails, leave as string
                pass

    # Convert nominal_power_max to Watts (loaded as float)
    if hasattr(target, "nominal_power_max") and target.nominal_power_max is not None:
        if not isinstance(target.nominal_power_max, type(Watts(0.0))):
            target.nominal_power_max = Watts(float(target.nominal_power_max))

    # Convert external_source to Watts (loaded as float)
    if hasattr(target, "external_source") and target.external_source is not None:
        if not isinstance(target.external_source, type(Watts(0.0))):
            target.external_source = Watts(float(target.external_source))

    # Reconstruct Battery from JSON (loaded as dict)
    if hasattr(target, "storage") and target.storage is not None:
        if isinstance(target.storage, dict):
            target.storage = Battery(nominal_capacity=WattHours(target.storage["nominal_capacity"]))
        elif isinstance(target.storage, str):
            # Handle case where it's still a JSON string
            storage_data = json.loads(target.storage)
            target.storage = Battery(nominal_capacity=WattHours(storage_data["nominal_capacity"]))

    # Reconstruct Grid from JSON (loaded as dict)
    if hasattr(target, "grid") and target.grid is not None:
        if isinstance(target.grid, dict):
            target.grid = Grid(contracted_power=Watts(target.grid["contracted_power"]))
        elif isinstance(target.grid, str):
            # Handle case where it's still a JSON string
            grid_data = json.loads(target.grid)
            target.grid = Grid(contracted_power=Watts(grid_data["contracted_power"]))


@event.listens_for(EnergySource, "before_insert")
@event.listens_for(EnergySource, "before_update")
def _flatten_energy_source_composites(mapper, connection, target: Any) -> None:
    """Event listener that flattens value objects before persisting.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: The EnergySource instance being persisted
    """
    # Convert EnergySourceType enum to string
    if hasattr(target, "type") and target.type is not None:
        if isinstance(target.type, EnergySourceType):
            target.type = target.type.value

    # Flatten nominal_power_max (Watts) to float
    if hasattr(target, "nominal_power_max") and target.nominal_power_max is not None:
        target.nominal_power_max = float(target.nominal_power_max)

    # Flatten external_source (Watts) to float
    if hasattr(target, "external_source") and target.external_source is not None:
        target.external_source = float(target.external_source)

    # Serialize Battery to JSON
    if hasattr(target, "storage") and target.storage is not None:
        if not isinstance(target.storage, (dict, str)):
            target.storage = {"nominal_capacity": float(target.storage.nominal_capacity)}

    # Serialize Grid to JSON
    if hasattr(target, "grid") and target.grid is not None:
        if not isinstance(target.grid, (dict, str)):
            target.grid = {"contracted_power": float(target.grid.contracted_power)}


@event.listens_for(EnergySource, "after_insert")
@event.listens_for(EnergySource, "after_update")
def _restore_energy_source_composites(mapper, connection, target: Any) -> None:
    """Event listener that restores value objects after persisting.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: The EnergySource instance that was persisted
    """
    # Restore id to EntityId if it was converted to string
    # NOTE: After SQLAlchemy flush, IDs may be strings and need restoration to EntityId
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore

    # Restore foreign keys to EntityId
    # NOTE: Foreign key UUIDs may be strings after persist and need conversion
    if hasattr(target, "energy_monitor_id") and target.energy_monitor_id is not None:
        if isinstance(target.energy_monitor_id, str):  # type: ignore
            target.energy_monitor_id = EntityId(uuid.UUID(target.energy_monitor_id))  # type: ignore

    if hasattr(target, "forecast_provider_id") and target.forecast_provider_id is not None:
        if isinstance(target.forecast_provider_id, str):  # type: ignore
            target.forecast_provider_id = EntityId(uuid.UUID(target.forecast_provider_id))  # type: ignore

    # Restore type to enum
    if hasattr(target, "type") and target.type is not None:
        if isinstance(target.type, str):
            try:
                target.type = EnergySourceType(target.type)
            except ValueError:
                pass

    # Restore Watts values
    if hasattr(target, "nominal_power_max") and target.nominal_power_max is not None:
        if not isinstance(target.nominal_power_max, type(Watts(0.0))):
            target.nominal_power_max = Watts(float(target.nominal_power_max))

    if hasattr(target, "external_source") and target.external_source is not None:
        if not isinstance(target.external_source, type(Watts(0.0))):
            target.external_source = Watts(float(target.external_source))

    # Restore Battery from dict
    if hasattr(target, "storage") and target.storage is not None:
        if isinstance(target.storage, dict):
            target.storage = Battery(nominal_capacity=WattHours(target.storage["nominal_capacity"]))

    # Restore Grid from dict
    if hasattr(target, "grid") and target.grid is not None:
        if isinstance(target.grid, dict):
            target.grid = Grid(contracted_power=Watts(target.grid["contracted_power"]))
