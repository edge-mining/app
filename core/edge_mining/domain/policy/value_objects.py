"""Collection of Value Objects for the Energy Optimization domain of the Edge Mining application."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from edge_mining.domain.common import ValueObject
from edge_mining.domain.energy.entities import EnergySource
from edge_mining.domain.energy.value_objects import EnergyStateSnapshot
from edge_mining.domain.forecast.aggregate_root import Forecast
from edge_mining.domain.forecast.value_objects import Sun
from edge_mining.domain.home_load.value_objects import HomeLoadsConsumption
from edge_mining.domain.miner.aggregate_roots import Miner
from edge_mining.domain.miner.value_objects import MinerStateSnapshot
from edge_mining.domain.performance.value_objects import MiningPerformanceSnapshot


@dataclass(frozen=True)
class DecisionalContext(ValueObject):
    """Value Object for the context of a mining decision."""

    energy_source: Optional[EnergySource]
    energy_state: Optional[EnergyStateSnapshot]

    forecast: Optional[Forecast]

    home_load: Optional[HomeLoadsConsumption] = None

    mining_performance: Optional[MiningPerformanceSnapshot] = None

    sun: Optional[Sun] = field(default=None)

    miner: Optional[Miner] = field(default=None)
    miner_state: Optional[MinerStateSnapshot] = field(default=None)
    timestamp: datetime = field(default_factory=datetime.now)
