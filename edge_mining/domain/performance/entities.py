"""Collection of Entities for the Mining Performance Analysis domain of the Edge Mining application."""

from dataclasses import dataclass, field
from typing import List, Optional

from edge_mining.domain.common import Entity, EntityId, Timestamp, utc_now_timestamp
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.performance.common import (
    MiningPerformanceTrackerAdapter,
    Satoshi,
)
from edge_mining.shared.interfaces.config import MiningPerformanceTrackerConfig


@dataclass
class MiningPerformanceTracker(Entity):
    """Entity for tracking mining performance."""

    name: str = ""
    adapter_type: MiningPerformanceTrackerAdapter = MiningPerformanceTrackerAdapter.DUMMY
    config: Optional[MiningPerformanceTrackerConfig] = None
    external_service_id: Optional[EntityId] = None


@dataclass
class MiningSession(Entity):
    """Entity for a mining session."""

    tracker_id: Optional[EntityId] = None
    miner_ids: List[EntityId] = field(default_factory=list)
    start_time: Timestamp = field(default_factory=utc_now_timestamp)
    end_time: Optional[Timestamp] = None
    total_reward: Optional[Satoshi] = None
    average_hashrate: Optional[HashRate] = None
