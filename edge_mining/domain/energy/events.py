"""Energy domain events."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import DomainEvent, EntityId
from edge_mining.domain.energy.value_objects import EnergyStateSnapshot


@dataclass
class EnergyStateSnapshotUpdatedEvent(DomainEvent):
    """Event emitted when a new energy state snapshot is read."""

    optimization_unit_id: Optional[EntityId] = None
    optimization_unit_name: str = ""
    energy_source_id: Optional[EntityId] = None
    energy_state_snapshot: Optional[EnergyStateSnapshot] = None
