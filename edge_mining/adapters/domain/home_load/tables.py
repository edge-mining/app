"""SQLAlchemy ORM mappings for HomeLoad domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

The mappings handle complex objects using SQLAlchemy event listeners and custom types:
- LoadDevice dictionaries are serialized to JSON and reconstructed after loading
- HomeForecastProviderConfig is serialized using custom ConfigurationType
- EntityId value objects are implicitly converted to/from strings

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
from typing import Optional

from sqlalchemy import JSON, Column, ForeignKey, String, Table, TypeDecorator, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.common import ConfigurationType
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.common import EntityId
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import HomeForecastProviderAdapter
from edge_mining.domain.home_load.entities import HomeForecastProvider, LoadDevice
from edge_mining.domain.home_load.exceptions import HomeForecastProviderConfigurationError
from edge_mining.shared.adapter_maps.home_load import HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import HomeForecastProviderConfig


class HomeForecastProviderConfigType(ConfigurationType):
    """SQLAlchemy type for HomeForecastProviderConfig serialization.

    Inherits from ConfigurationType to handle JSON serialization/deserialization.
    """


def _deserialize_home_forecast_provider_config(
    adapter_type: HomeForecastProviderAdapter, config_json: str
) -> Optional[HomeForecastProviderConfig]:
    """Deserialize JSON string to HomeForecastProviderConfig based on adapter type."""
    if not config_json:
        return None

    data: dict = json.loads(config_json)

    if adapter_type not in HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP:
        raise HomeForecastProviderConfigurationError(
            f"Error reading HomeForecastProvider configuration. Invalid type '{adapter_type}'"
        )

    config_class: Optional[type[HomeForecastProviderConfig]] = HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(adapter_type)
    if not config_class:
        raise HomeForecastProviderConfigurationError(
            f"Error creating HomeForecastProvider configuration. Type '{adapter_type}'"
        )

    config_instance = config_class.from_dict(data)
    if not isinstance(config_instance, HomeForecastProviderConfig):
        raise HomeForecastProviderConfigurationError(
            f"Deserialized config is not of type HomeForecastProviderConfig for adapter type {adapter_type}."
        )
    return config_instance


@event.listens_for(HomeForecastProvider, "load")
def _receive_home_forecast_provider_load(target: HomeForecastProvider, context) -> None:
    """Event listener that deserializes config after loading from database."""
    if target.config and isinstance(target.config, str):
        target.config = _deserialize_home_forecast_provider_config(target.adapter_type, target.config)


# Define the home_forecast_providers table using imperative style
home_forecast_providers_table = Table(
    "home_forecast_providers",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False),
    Column("config", HomeForecastProviderConfigType, nullable=True),
    Column("external_service_id", String, ForeignKey("external_services.id"), nullable=True),
)

# Map HomeForecastProvider
mapper_registry.map_imperatively(
    HomeForecastProvider,
    home_forecast_providers_table,
)


# Custom TypeDecorator for LoadDevice dictionary serialization
class LoadDevicesDictType(TypeDecorator):
    """Custom type for serializing Dict[EntityId, LoadDevice] to JSON."""

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert Dict[EntityId, LoadDevice] to JSON dict for database storage."""
        if value is None:
            return None
        # Convert to dict with string keys and LoadDevice dicts
        return {
            str(device_id): {
                "id": str(device.id),
                "name": device.name,
                "type": device.type,
            }
            for device_id, device in value.items()
        }

    def process_result_value(self, value, dialect):
        """Return raw JSON dict - will be reconstructed in event listener."""
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
    if target.devices and isinstance(target.devices, dict):
        reconstructed_devices = {}
        for device_id_str, device_data in target.devices.items():
            if isinstance(device_data, dict):
                device = LoadDevice(
                    id=EntityId(device_data["id"]),
                    name=device_data["name"],
                    type=device_data["type"],
                )
                reconstructed_devices[EntityId(device_id_str)] = device
        target.devices = reconstructed_devices


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
