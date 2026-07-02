"""Climate domain events."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.climate.value_objects import ClimateZoneReading
from edge_mining.domain.common import DomainEvent, EntityId


@dataclass
class ClimateStateUpdatedEvent(DomainEvent):
    """Event emitted when a new climate reading is captured."""

    climate_zone_id: Optional[EntityId] = None
    climate_zone_name: str = ""
    climate_reading: Optional[ClimateZoneReading] = None
