"""Mining Performance Analysis domain events."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import DomainEvent, EntityId
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.performance.value_objects import MiningReward


@dataclass
class RewardReceivedEvent(DomainEvent):
    """Event emitted when a new mining reward is observed by a tracker."""

    tracker_id: Optional[EntityId] = None
    miner_id: Optional[EntityId] = None
    reward: Optional[MiningReward] = None


@dataclass
class HashrateDropDetectedEvent(DomainEvent):
    """Event emitted when the observed pool-side hashrate falls under a threshold."""

    tracker_id: Optional[EntityId] = None
    miner_id: Optional[EntityId] = None
    expected: Optional[HashRate] = None
    actual: Optional[HashRate] = None
