"""SQLAlchemy ORM mappings for Forecast domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

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

from sqlalchemy import Column, ForeignKey, String, Table, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.common import ConfigurationType
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.common import EntityId
from edge_mining.domain.forecast.common import ForecastProviderAdapter
from edge_mining.domain.forecast.entities import ForecastProvider
from edge_mining.domain.forecast.exceptions import ForecastProviderConfigurationError
from edge_mining.shared.adapter_maps.forecast import FORECAST_PROVIDER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import ForecastProviderConfig


class ForecastProviderConfigType(ConfigurationType):
    """SQLAlchemy type for ForecastProviderConfig serialization.

    Inherits from ConfigurationType to handle JSON serialization/deserialization.
    """


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
    """Event listener that deserializes config after loading from database.

    Args:
        target: The ForecastProvider instance being loaded
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
            target.adapter_type = ForecastProviderAdapter(target.adapter_type)
        except ValueError:
            # If conversion fails, leave as string (will fail in config deserialization)
            pass

    if target.config and isinstance(target.config, str):
        target.config = _deserialize_forecast_provider_config(target.adapter_type, target.config)


@event.listens_for(ForecastProvider, "before_insert")
@event.listens_for(ForecastProvider, "before_update")
def _flatten_forecast_provider_composites(mapper, connection, target: Any) -> None:
    """Convert enum attributes to primitive values before persisting."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, ForecastProviderAdapter):
            target.adapter_type = target.adapter_type.value


@event.listens_for(ForecastProvider, "after_insert")
@event.listens_for(ForecastProvider, "after_update")
def _restore_forecast_provider_composites(mapper, connection, target: Any) -> None:
    """Restore enum attributes after persist operations."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, str):
            try:
                target.adapter_type = ForecastProviderAdapter(target.adapter_type)
            except ValueError:
                pass


# Define the forecast_providers table using imperative style
forecast_providers_table = Table(
    "forecast_providers",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False),
    Column("config", ForecastProviderConfigType, nullable=True),
    Column("external_service_id", String, ForeignKey("external_services.id"), nullable=True),
)

# Map ForecastProvider
mapper_registry.map_imperatively(
    ForecastProvider,
    forecast_providers_table,
)
