"""SQLAlchemy ORM mappings for ExternalService entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

All tables and mappings use the shared metadata and mapper registry from
the sqlalchemy.registry module, which are available as module-level singletons.
"""

import json
from typing import Optional

from sqlalchemy import Column, String, Table, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.common import ConfigurationType
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
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
    if target.config and isinstance(target.config, str):
        target.config = _deserialize_external_service_config(target.adapter_type, target.config)


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
