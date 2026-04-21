"""SQLAlchemy ORM mappings for ExternalService entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

All tables and mappings use the shared metadata and mapper registry from
the sqlalchemy.registry module, which are available as module-level singletons.

⚠️  DEVELOPER WARNING ⚠️
═══════════════════════════════════════════════════════════════════════════════
ANY SCHEMA CHANGE (adding/removing/modifying tables or columns) REQUIRES an
Alembic migration. Do NOT modify this file without creating a migration:

  python scripts/migrate.py create "Description of your change"

For detailed instructions, see: docs/ALEMBIC_MIGRATIONS.md
For a step-by-step example, see: docs/MIGRATION_EXAMPLE.md
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import uuid
from typing import Any, Optional

from sqlalchemy import Column, String, Table, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.common import ConfigurationType
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.common import EntityId
from edge_mining.shared.adapter_maps.external_services import EXTERNAL_SERVICE_CONFIG_TYPE_MAP
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.external_services.entities import ExternalService
from edge_mining.shared.external_services.exceptions import ExternalServiceConfigurationError
from edge_mining.shared.interfaces.config import ExternalServiceConfig


class ExternalServiceConfigType(ConfigurationType):
    """SQLAlchemy type for ExternalServiceConfig serialization.

    Inherits from ConfigurationType to handle JSON serialization/deserialization.
    """


def _deserialize_external_service_config(
    adapter_type: ExternalServiceAdapter, config_json: str
) -> Optional[ExternalServiceConfig]:
    """Deserialize JSON string to ExternalServiceConfig based on adapter type."""
    if not config_json:
        return None

    data: dict = json.loads(config_json)

    if adapter_type not in EXTERNAL_SERVICE_CONFIG_TYPE_MAP:
        raise ExternalServiceConfigurationError(
            f"Error reading ExternalService configuration. Invalid type '{adapter_type}'"
        )

    config_class: Optional[type[ExternalServiceConfig]] = EXTERNAL_SERVICE_CONFIG_TYPE_MAP.get(adapter_type)
    if not config_class:
        raise ExternalServiceConfigurationError(f"Error creating ExternalService configuration. Type '{adapter_type}'")

    config_instance = config_class.from_dict(data)
    if not isinstance(config_instance, ExternalServiceConfig):
        raise ExternalServiceConfigurationError(
            f"Deserialized config is not of type ExternalServiceConfig for adapter type {adapter_type}."
        )
    return config_instance


@event.listens_for(ExternalService, "load")
def _receive_external_service_load(target: ExternalService, context) -> None:
    """Event listener that deserializes config after loading from database."""
    # Convert id string to EntityId if needed
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore[arg-type,misc]
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore[assignment]

    # Convert adapter_type from string to enum if necessary
    if isinstance(target.adapter_type, str):
        try:
            target.adapter_type = ExternalServiceAdapter(target.adapter_type)
        except ValueError:
            pass

    if target.config and isinstance(target.config, str):
        target.config = _deserialize_external_service_config(target.adapter_type, target.config)


@event.listens_for(ExternalService, "before_insert")
@event.listens_for(ExternalService, "before_update")
def _flatten_external_service_composites(mapper, connection, target: Any) -> None:
    """Convert enum attributes to primitive values before persisting."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, ExternalServiceAdapter):
            target.adapter_type = target.adapter_type.value


@event.listens_for(ExternalService, "after_insert")
@event.listens_for(ExternalService, "after_update")
def _restore_external_service_composites(mapper, connection, target: Any) -> None:
    """Restore enum attributes after persist operations."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, str):
            try:
                target.adapter_type = ExternalServiceAdapter(target.adapter_type)
            except ValueError:
                pass


# Define the external_services table using imperative style
external_services_table = Table(
    "external_services",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False),
    Column("config", ExternalServiceConfigType, nullable=True),
)

# Map ExternalService
mapper_registry.map_imperatively(
    ExternalService,
    external_services_table,
)
