"""SQLAlchemy ORM mappings for Notification domain entities.

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
from edge_mining.domain.notification.common import NotificationAdapter
from edge_mining.domain.notification.entities import Notifier
from edge_mining.domain.notification.exceptions import NotifierConfigurationError
from edge_mining.shared.adapter_maps.notification import NOTIFIER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import NotificationConfig


class NotifierConfigType(TypeDecorator):
    """Custom SQLAlchemy type that converts NotificationConfig to/from JSON string.

    This type handles serialization when writing to the database.
    Deserialization is handled by the @event.listens_for decorator on the entity.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[NotificationConfig], dialect) -> Optional[str]:
        """Convert NotificationConfig to JSON string before storing in DB."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value.to_dict())

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Return the JSON string as-is. Actual deserialization happens in the event listener."""
        return value


def _deserialize_notifier_config(adapter_type: NotificationAdapter, config_json: str) -> Optional[NotificationConfig]:
    """Deserialize JSON string to NotificationConfig based on adapter type."""
    if not config_json:
        return None

    data: dict = json.loads(config_json)

    if adapter_type not in NOTIFIER_CONFIG_TYPE_MAP:
        raise NotifierConfigurationError(f"Error reading Notifier configuration. Invalid type '{adapter_type}'")

    config_class: Optional[type[NotificationConfig]] = NOTIFIER_CONFIG_TYPE_MAP.get(adapter_type)
    if not config_class:
        raise NotifierConfigurationError(f"Error creating Notifier configuration. Type '{adapter_type}'")

    config_instance = config_class.from_dict(data)
    if not isinstance(config_instance, NotificationConfig):
        raise NotifierConfigurationError(
            f"Deserialized config is not of type NotificationConfig for adapter type {adapter_type}."
        )
    return config_instance


@event.listens_for(Notifier, "load")
def _receive_notifier_load(target: Notifier, context) -> None:
    """Event listener that deserializes config after loading from database."""
    if target.config and isinstance(target.config, str):
        target.config = _deserialize_notifier_config(target.adapter_type, target.config)


# Define the notifiers table using imperative style
notifiers_table = Table(
    "notifiers",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False),
    Column("config", NotifierConfigType, nullable=True),
    Column("external_service_id", String, nullable=True),
)

# Map Notifier
mapper_registry.map_imperatively(
    Notifier,
    notifiers_table,
)
