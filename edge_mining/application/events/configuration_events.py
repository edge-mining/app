"""Configuration domain events."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import DomainEvent, EntityId


@dataclass
class ConfigurationUpdatedEvent(DomainEvent):
    """Event emitted when a configuration is created, updated, or removed.

    Generic application event: does not carry the modified entity's data,
    but only the information needed to invalidate the adapters' cache.
    """

    entity_type: str = ""  # "energy_monitor", "miner_controller", "notifier", etc.
    entity_id: Optional[EntityId] = None
    action: str = ""  # "created" | "updated" | "removed"
