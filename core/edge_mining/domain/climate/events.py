"""Climate domain events."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.climate.value_objects import EnvironmentStateSnapshot
from edge_mining.domain.common import DomainEvent, EntityId


@dataclass
class EnvironmentStateUpdatedEvent(DomainEvent):
    """Event emitted when a new environment state reading is captured."""

    climate_zone_id: Optional[EntityId] = None
    climate_zone_name: str = ""
    environment_state: Optional[EnvironmentStateSnapshot] = None
