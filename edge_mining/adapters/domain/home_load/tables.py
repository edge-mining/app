"""SQLAlchemy ORM mappings for HomeLoad domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

The mappings handle complex objects using SQLAlchemy event listeners and custom types:
- LoadDevice dictionaries are serialized to JSON and reconstructed after loading
- EnergyLoadForecastProviderConfig is serialized using custom ConfigurationType
- EntityId value objects are implicitly converted to/from strings

All tables and mappings use the shared metadata and mapper registry from
the sqlalchemy.registry module, which are available as module-level singletons.

WARNING - DEVELOPER WARNING
ANY SCHEMA CHANGE (adding/removing/modifying tables or columns) REQUIRES an
Alembic migration. Do NOT modify this file without creating a migration:

  python scripts/migrate.py create "Description of your change"

For detailed instructions, see: docs/ALEMBIC_MIGRATIONS.md
For a step-by-step example, see: docs/MIGRATION_EXAMPLE.md
"""

import json
import uuid
from typing import Any, Optional

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Index, String, Table, TypeDecorator, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.common import ConfigurationType
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.common import EntityId
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import (
    EnergyLoadForecastProviderAdapter,
    EnergyLoadHistoryProviderAdapter,
    LoadDeviceCategory,
)
from edge_mining.domain.home_load.entities import EnergyLoadForecastProvider, EnergyLoadHistoryProvider, LoadDevice
from edge_mining.domain.home_load.exceptions import (
    EnergyLoadForecastProviderConfigurationError,
    EnergyLoadHistoryProviderConfigurationError,
)
from edge_mining.shared.adapter_maps.home_load import (
    ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP,
    ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_TYPE_MAP,
)
from edge_mining.shared.interfaces.config import EnergyLoadForecastProviderConfig, EnergyLoadHistoryProviderConfig


class EnergyLoadForecastProviderConfigType(ConfigurationType):
    """SQLAlchemy type for EnergyLoadForecastProviderConfig serialization.

    Inherits from ConfigurationType to handle JSON serialization/deserialization.
    """


def _deserialize_energy_load_forecast_provider_config(
    adapter_type: EnergyLoadForecastProviderAdapter, config_json: str
) -> Optional[EnergyLoadForecastProviderConfig]:
    """Deserialize JSON string to EnergyLoadForecastProviderConfig based on adapter type."""
    if not config_json:
        return None

    data: dict = json.loads(config_json)

    if adapter_type not in ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP:
        raise EnergyLoadForecastProviderConfigurationError(
            f"Error reading EnergyLoadForecastProvider configuration. Invalid type '{adapter_type}'"
        )

    config_class: Optional[type[EnergyLoadForecastProviderConfig]] = ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(
        adapter_type
    )
    if not config_class:
        raise EnergyLoadForecastProviderConfigurationError(
            f"Error creating EnergyLoadForecastProvider configuration. Type '{adapter_type}'"
        )

    config_instance = config_class.from_dict(data)
    if not isinstance(config_instance, EnergyLoadForecastProviderConfig):
        raise EnergyLoadForecastProviderConfigurationError(
            f"Deserialized config is not of type EnergyLoadForecastProviderConfig for adapter type {adapter_type}."
        )
    return config_instance


@event.listens_for(EnergyLoadForecastProvider, "load")
def _receive_energy_load_forecast_provider_load(target: EnergyLoadForecastProvider, context) -> None:
    """Event listener that deserializes config after loading from database."""
    # Convert id string to EntityId if needed
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore[arg-type,misc]
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore[assignment]

    # Convert foreign keys to EntityId
    if hasattr(target, "external_service_id") and target.external_service_id is not None:
        if isinstance(target.external_service_id, str):  # type: ignore
            target.external_service_id = EntityId(uuid.UUID(target.external_service_id))  # type: ignore

    # Convert adapter_type string to enum if needed
    if isinstance(target.adapter_type, str):
        try:
            target.adapter_type = EnergyLoadForecastProviderAdapter(target.adapter_type)
        except ValueError:
            pass

    if target.config and isinstance(target.config, str):
        target.config = _deserialize_energy_load_forecast_provider_config(target.adapter_type, target.config)


@event.listens_for(EnergyLoadForecastProvider, "before_insert")
@event.listens_for(EnergyLoadForecastProvider, "before_update")
def _flatten_energy_load_forecast_provider_composites(mapper, connection, target: Any) -> None:
    """Convert enum attributes to primitive values before persisting."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, EnergyLoadForecastProviderAdapter):
            target.adapter_type = target.adapter_type.value


@event.listens_for(EnergyLoadForecastProvider, "after_insert")
@event.listens_for(EnergyLoadForecastProvider, "after_update")
def _restore_energy_load_forecast_provider_composites(mapper, connection, target: Any) -> None:
    """Restore enum attributes after persist operations."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, str):
            try:
                target.adapter_type = EnergyLoadForecastProviderAdapter(target.adapter_type)
            except ValueError:
                pass


# Define the energy_load_forecast_providers table using imperative style
energy_load_forecast_providers_table = Table(
    "energy_load_forecast_providers",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False),
    Column("config", EnergyLoadForecastProviderConfigType, nullable=True),
    Column("external_service_id", String, ForeignKey("external_services.id"), nullable=True),
)

# Map EnergyLoadForecastProvider
mapper_registry.map_imperatively(
    EnergyLoadForecastProvider,
    energy_load_forecast_providers_table,
)


# Custom TypeDecorator for LoadDevice list serialization
class LoadDevicesDictType(TypeDecorator):
    """Custom type for serializing List[LoadDevice] to a JSON array."""

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert List[LoadDevice] to a JSON list for database storage."""
        if value is None:
            return None
        return [
            {
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
            for device in value
        ]

    def process_result_value(self, value, dialect):
        """Return raw JSON list - will be reconstructed in event listener."""
        return value


# HomeLoadsProfile table
home_profiles_table = Table(
    "home_profiles",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("devices_json", LoadDevicesDictType, nullable=True),
)


# Event listener to reconstruct LoadDevice objects after loading
@event.listens_for(HomeLoadsProfile, "load")
def _receive_home_profile_load(target, context):
    """Reconstruct LoadDevice objects from JSON after loading from database."""
    if isinstance(target.id, str):
        target.id = EntityId(uuid.UUID(target.id))

    if target.devices and isinstance(target.devices, list):
        reconstructed: list = []
        for device_data in target.devices:
            if not isinstance(device_data, dict):
                continue
            forecast_id = device_data.get("energy_load_forecast_provider_id")
            history_id = device_data.get("energy_load_history_provider_id")
            reconstructed.append(
                LoadDevice(
                    id=EntityId(uuid.UUID(device_data["id"])),
                    name=device_data["name"],
                    category=LoadDeviceCategory(device_data["category"]),
                    enabled=bool(device_data.get("enabled", True)),
                    energy_load_forecast_provider_id=(EntityId(uuid.UUID(forecast_id)) if forecast_id else None),
                    energy_load_history_provider_id=(EntityId(uuid.UUID(history_id)) if history_id else None),
                )
            )
        target.devices = reconstructed
    elif target.devices is None:
        target.devices = []


# Map HomeLoadsProfile aggregate root to table
mapper_registry.map_imperatively(
    HomeLoadsProfile,
    home_profiles_table,
    properties={
        "id": home_profiles_table.c.id,
        "name": home_profiles_table.c.name,
        "devices": home_profiles_table.c.devices_json,
    },
)


# --- EnergyLoadHistoryProvider table + mapping ---


class EnergyLoadHistoryProviderConfigType(ConfigurationType):
    """SQLAlchemy type for EnergyLoadHistoryProviderConfig serialization."""


def _deserialize_energy_load_history_provider_config(
    adapter_type: EnergyLoadHistoryProviderAdapter, config_json: str
) -> Optional[EnergyLoadHistoryProviderConfig]:
    """Deserialize JSON string to EnergyLoadHistoryProviderConfig based on adapter type."""
    if not config_json:
        return None

    data: dict = json.loads(config_json)

    if adapter_type not in ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_TYPE_MAP:
        raise EnergyLoadHistoryProviderConfigurationError(
            f"Error reading EnergyLoadHistoryProvider configuration. Invalid type '{adapter_type}'"
        )

    config_class: Optional[type[EnergyLoadHistoryProviderConfig]] = ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_TYPE_MAP.get(
        adapter_type
    )
    if not config_class:
        # Some adapters (e.g. DUMMY) have no config
        return None

    config_instance = config_class.from_dict(data)
    if not isinstance(config_instance, EnergyLoadHistoryProviderConfig):
        raise EnergyLoadHistoryProviderConfigurationError(
            f"Deserialized config is not of type EnergyLoadHistoryProviderConfig for adapter type {adapter_type}."
        )
    return config_instance


@event.listens_for(EnergyLoadHistoryProvider, "load")
def _receive_energy_load_history_provider_load(target: EnergyLoadHistoryProvider, context) -> None:
    """Event listener that deserializes config after loading from database."""
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore[arg-type,misc]
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore[assignment]

    if hasattr(target, "external_service_id") and target.external_service_id is not None:
        if isinstance(target.external_service_id, str):  # type: ignore
            target.external_service_id = EntityId(uuid.UUID(target.external_service_id))  # type: ignore

    if isinstance(target.adapter_type, str):
        try:
            target.adapter_type = EnergyLoadHistoryProviderAdapter(target.adapter_type)
        except ValueError:
            pass

    if target.config and isinstance(target.config, str):
        target.config = _deserialize_energy_load_history_provider_config(target.adapter_type, target.config)


@event.listens_for(EnergyLoadHistoryProvider, "before_insert")
@event.listens_for(EnergyLoadHistoryProvider, "before_update")
def _flatten_energy_load_history_provider_composites(mapper, connection, target: Any) -> None:
    """Convert enum attributes to primitive values before persisting."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, EnergyLoadHistoryProviderAdapter):
            target.adapter_type = target.adapter_type.value


@event.listens_for(EnergyLoadHistoryProvider, "after_insert")
@event.listens_for(EnergyLoadHistoryProvider, "after_update")
def _restore_energy_load_history_provider_composites(mapper, connection, target: Any) -> None:
    """Restore enum attributes after persist operations."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, str):
            try:
                target.adapter_type = EnergyLoadHistoryProviderAdapter(target.adapter_type)
            except ValueError:
                pass


energy_load_history_providers_table = Table(
    "energy_load_history_providers",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False),
    Column("config", EnergyLoadHistoryProviderConfigType, nullable=True),
    Column("external_service_id", String, ForeignKey("external_services.id"), nullable=True),
)

mapper_registry.map_imperatively(
    EnergyLoadHistoryProvider,
    energy_load_history_providers_table,
)


# HomeLoadPowerPoint table (device-scoped time series).
#
# Not imperatively mapped: HomeLoadPowerPoint is a Value Object (frozen
# dataclass) and the SQLAlchemy repository interacts with this table via
# Core (insert/select statements) to keep the domain model pure.
#
# Composite primary key (device_id, timestamp) yields:
#   - natural uniqueness per device over time
#   - idempotent ingestion (re-fetching the same HA window is a no-op)
#   - clustered index on (device_id, timestamp) for O(log n) range scans
home_load_power_points_table = Table(
    "home_load_power_points",
    metadata,
    Column("device_id", String, nullable=False, primary_key=True),
    Column("timestamp", DateTime(timezone=True), nullable=False, primary_key=True),
    Column("power", Float, nullable=False),
    Index("ix_home_load_power_points_device_ts", "device_id", "timestamp"),
)
