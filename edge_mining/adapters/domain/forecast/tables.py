"""SQLAlchemy ORM mappings for Forecast domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

All tables and mappings use the shared metadata and mapper registry from
the sqlalchemy.registry module, which are available as module-level singletons.
"""

import json
from typing import Optional

from sqlalchemy import Column, String, Table, TypeDecorator, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.forecast.common import ForecastProviderAdapter
from edge_mining.domain.forecast.entities import ForecastProvider
from edge_mining.domain.forecast.exceptions import ForecastProviderConfigurationError
from edge_mining.shared.adapter_maps.forecast import FORECAST_PROVIDER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import ForecastProviderConfig


class ForecastProviderConfigType(TypeDecorator):
    """Custom SQLAlchemy type that converts ForecastProviderConfig to/from JSON string.

    This type handles serialization when writing to the database.
    Deserialization is handled by the @event.listens_for decorator on the entity.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[ForecastProviderConfig], dialect) -> Optional[str]:
        """Convert ForecastProviderConfig to JSON string before storing in DB."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value.to_dict())

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Return the JSON string as-is. Actual deserialization happens in the event listener."""
        return value


def _deserialize_forecast_provider_config(
    adapter_type: ForecastProviderAdapter, config_json: str
) -> Optional[ForecastProviderConfig]:
    """Deserialize JSON string to ForecastProviderConfig based on adapter type."""
    if not config_json:
        return None

    data: dict = json.loads(config_json)

    if adapter_type not in FORECAST_PROVIDER_CONFIG_TYPE_MAP:
        raise ForecastProviderConfigurationError(
            f"Error reading ForecastProvider configuration. Invalid type '{adapter_type}'"
        )

    config_class: Optional[type[ForecastProviderConfig]] = FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(adapter_type)
    if not config_class:
        raise ForecastProviderConfigurationError(
            f"Error creating ForecastProvider configuration. Type '{adapter_type}'"
        )

    config_instance = config_class.from_dict(data)
    if not isinstance(config_instance, ForecastProviderConfig):
        raise ForecastProviderConfigurationError(
            f"Deserialized config is not of type ForecastProviderConfig for adapter type {adapter_type}."
        )
    return config_instance


@event.listens_for(ForecastProvider, "load")
def _receive_forecast_provider_load(target: ForecastProvider, context) -> None:
    """Event listener that deserializes config after loading from database."""
    if target.config and isinstance(target.config, str):
        target.config = _deserialize_forecast_provider_config(target.adapter_type, target.config)


# Define the forecast_providers table using imperative style
forecast_providers_table = Table(
    "forecast_providers",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False),
    Column("config", ForecastProviderConfigType, nullable=True),
    Column("external_service_id", String, nullable=True),
)

# Map ForecastProvider
mapper_registry.map_imperatively(
    ForecastProvider,
    forecast_providers_table,
)
