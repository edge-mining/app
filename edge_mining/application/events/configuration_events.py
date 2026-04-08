"""Configuration application events."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.application.events.common import ConfigurationAction, ConfigurationUpdatedEventType
from edge_mining.domain.common import DomainEvent, EntityId


@dataclass
class ConfigurationUpdatedEvent(DomainEvent):
    """Event emitted when a configuration is created, updated, or removed.

    Application-level event: does not carry the modified entity's data,
    but only the information needed to invalidate the adapters' cache.
    """

    entity_type: ConfigurationUpdatedEventType = ConfigurationUpdatedEventType.UNKNOWN
    entity_id: Optional[EntityId] = None
    action: ConfigurationAction = ConfigurationAction.UNKNOWN
