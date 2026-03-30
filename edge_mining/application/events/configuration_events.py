"""Configuration domain events."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

from edge_mining.domain.common import DomainEvent, EntityId


class ConfigurationUpdatedEventType(Enum):
    """Enum for the different types of configuration updates."""

    ENERGY_MONITOR = "energy_monitor"
    MINER_CONTROLLER = "miner_controller"
    NOTIFIER = "notifier"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = ""


@dataclass
class ConfigurationUpdatedEvent(DomainEvent):
    """Event emitted when a configuration is created, updated, or removed.

    Generic application event: does not carry the modified entity's data,
    but only the information needed to invalidate the adapters' cache.
    """

    entity_type: ConfigurationUpdatedEventType = ConfigurationUpdatedEventType.UNKNOWN
    entity_id: Optional[EntityId] = None
    action: str = ""  # "created" | "updated" | "removed"
