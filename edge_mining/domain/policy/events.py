"""Policy domain events."""

from dataclasses import dataclass, field
from typing import List, Optional

from edge_mining.domain.common import DomainEvent, EntityId
from edge_mining.domain.policy.value_objects import DecisionalContext


@dataclass
class DecisionalContextUpdatedEvent(DomainEvent):
    """Event emitted when a new decisional context is composed for an optimization unit."""

    optimization_unit_id: Optional[EntityId] = None
    optimization_unit_name: str = ""
    context: Optional[DecisionalContext] = None
    target_miner_ids: List[EntityId] = field(default_factory=list)
