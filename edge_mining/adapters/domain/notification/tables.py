"""SQLAlchemy ORM mappings for Notification domain entities.

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
from typing import Optional

from sqlalchemy import Column, ForeignKey, String, Table, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.common import ConfigurationType
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.common import EntityId
from edge_mining.domain.notification.common import NotificationAdapter
from edge_mining.domain.notification.entities import Notifier
from edge_mining.domain.notification.exceptions import NotifierConfigurationError
from edge_mining.shared.adapter_maps.notification import NOTIFIER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import NotificationConfig


class NotifierConfigType(ConfigurationType):
    """SQLAlchemy type for NotificationConfig serialization.

    Inherits from ConfigurationType to handle JSON serialization/deserialization.
    """


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

    # Convert foreign keys to EntityId
    # NOTE: SQLAlchemy returns strings for UUID columns that need conversion to EntityId
    if hasattr(target, "external_service_id") and target.external_service_id is not None:
        if isinstance(target.external_service_id, str):  # type: ignore
            target.external_service_id = EntityId(uuid.UUID(target.external_service_id))  # type: ignore

    # Convert adapter_type string to enum if needed
    if isinstance(target.adapter_type, str):
        try:
            target.adapter_type = NotificationAdapter(target.adapter_type)
        except ValueError:
            # If conversion fails, leave as string (will fail in config deserialization)
            pass

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
    Column("external_service_id", String, ForeignKey("external_services.id"), nullable=True),
)

# Map Notifier
mapper_registry.map_imperatively(
    Notifier,
    notifiers_table,
)
