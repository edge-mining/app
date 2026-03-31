"""Optimization domain events."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import DomainEvent, EntityId
from edge_mining.domain.policy.common import MiningDecision


@dataclass
class RuleEngagedEvent(DomainEvent):
    """Event emitted when a policy rule produces a mining decision."""

    optimization_unit_id: Optional[EntityId] = None
    optimization_unit_name: str = ""
    policy_id: Optional[EntityId] = None
    policy_name: str = ""
    miner_id: Optional[EntityId] = None
    decision: Optional[MiningDecision] = None
    miner_status: str = ""
