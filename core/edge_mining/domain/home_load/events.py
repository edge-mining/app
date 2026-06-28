"""Home load domain events."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import DomainEvent, EntityId


@dataclass
class LoadConsumptionHistoryCollectedEvent(DomainEvent):
    """Event emitted after collecting power points for a device."""

    device_id: Optional[EntityId] = None
    device_name: str = ""
    points_collected: int = 0


@dataclass
class LoadConsumptionHistoryPurgedEvent(DomainEvent):
    """Event emitted after purging old power points for a device."""

    device_id: Optional[EntityId] = None
    device_name: str = ""
    points_purged: int = 0
