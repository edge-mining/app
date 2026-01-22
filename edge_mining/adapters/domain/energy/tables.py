"""SQLAlchemy ORM mappings for Energy domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

The mappings handle value objects (Battery, Grid, Watts) using SQLAlchemy's composite()
to map multiple columns to single value object instances.

All tables and mappings use the shared metadata and mapper registry from
the sqlalchemy.registry module, which are available as module-level singletons.
"""

import json
from typing import Optional

from sqlalchemy import Column, Float, ForeignKey, String, Table, TypeDecorator, event
from sqlalchemy.orm import composite

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.common import ConfigurationType
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.common import WattHours, Watts
from edge_mining.domain.energy.common import EnergyMonitorAdapter
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
    if target.config and isinstance(target.config, str):
        target.config = _deserialize_energy_monitor_config(target.adapter_type, target.config)


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
    Column("external_service_id", String, nullable=True),
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
    Column("nominal_power_max", Float, nullable=True),
    # Battery Value Object flattened into one column
    Column("storage_nominal_capacity", Float, nullable=True),
    # Grid Value Object flattened into one column
    Column("grid_contracted_power", Float, nullable=True),
    # External source power (Watts stored as float)
    Column("external_source", Float, nullable=True),
    # Foreign Keys to other entities
    Column("energy_monitor_id", String, ForeignKey("energy_monitors.id"), nullable=True),
    Column("forecast_provider_id", String, nullable=True),  # FK to forecast_providers
)

# Map EnergyMonitor first (parent in some relationships)
mapper_registry.map_imperatively(
    EnergyMonitor,
    energy_monitors_table,
)

# Map EnergySource with composite value objects
mapper_registry.map_imperatively(
    EnergySource,
    energy_sources_table,
    properties={
        # Map nominal_power_max as composite (Watts wraps a single float)
        "nominal_power_max": composite(
            Watts,
            energy_sources_table.c.nominal_power_max,
        ),
        # Map external_source as composite (Watts wraps a single float)
        "external_source": composite(
            Watts,
            energy_sources_table.c.external_source,
        ),
        # Note: storage (Battery) and grid (Grid) are composite value objects
        # that wrap other value objects (WattHours, Watts). These are handled
        # via event listeners since SQLAlchemy's composite() doesn't handle Optional
        # wrapped value objects well. The columns storage_nominal_capacity and
        # grid_contracted_power are excluded from automatic mapping.
    },
    # Exclude the columns used by composites and custom event handlers
    exclude_properties=["nominal_power_max", "external_source", "storage_nominal_capacity", "grid_contracted_power"],
)


# Event listeners for Battery and Grid composite value objects
@event.listens_for(EnergySource, "load")
def _receive_energy_source_load(target: EnergySource, context) -> None:
    """Event listener that reconstructs Battery and Grid value objects after loading.

    Args:
        target: The EnergySource instance being loaded
        context: SQLAlchemy context
    """
    # Reconstruct Battery from storage_nominal_capacity column
    if hasattr(target, "_sa_instance_state"):
        state = target._sa_instance_state
        if "storage_nominal_capacity" in state.dict:
            capacity = state.dict["storage_nominal_capacity"]
            if capacity is not None:
                target.storage = Battery(nominal_capacity=WattHours(capacity))
            else:
                target.storage = None

        # Reconstruct Grid from grid_contracted_power column
        if "grid_contracted_power" in state.dict:
            power = state.dict["grid_contracted_power"]
            if power is not None:
                target.grid = Grid(contracted_power=Watts(power))
            else:
                target.grid = None


@event.listens_for(EnergySource, "before_insert")
@event.listens_for(EnergySource, "before_update")
def _flatten_energy_source_composites(mapper, connection, target: EnergySource) -> None:
    """Event listener that flattens Battery and Grid before persisting.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: The EnergySource instance being persisted
    """
    # Flatten Battery to storage_nominal_capacity column
    if hasattr(target, "storage") and target.storage is not None:
        mapper.columns["storage_nominal_capacity"].set_value(target, float(target.storage.nominal_capacity))
    else:
        mapper.columns["storage_nominal_capacity"].set_value(target, None)

    # Flatten Grid to grid_contracted_power column
    if hasattr(target, "grid") and target.grid is not None:
        mapper.columns["grid_contracted_power"].set_value(target, float(target.grid.contracted_power))
    else:
        mapper.columns["grid_contracted_power"].set_value(target, None)
