"""
Dummy adapter (Implementation of Port) that simulates
a miner performance tracker for Edge Mining Application
"""

import random
from typing import List, Optional

from edge_mining.domain.common import EntityId
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.performance.common import PayoutFrequency, Satoshi
from edge_mining.domain.performance.exceptions import (
    MiningPerformanceTrackerConfigurationError,
)
from edge_mining.domain.performance.ports import MiningPerformanceTrackerPort
from edge_mining.domain.performance.value_objects import (
    MiningReward,
    PayoutSchedule,
    PoolStats,
    PoolWorkerStats,
)
from edge_mining.shared.adapter_configs.performance import (
    MiningPerformanceTrackerDummyConfig,
)
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import (
    MiningPerformanceTrackerAdapterFactory,
)
from edge_mining.shared.logging.port import LoggerPort


class DummyMiningPerformanceTracker(MiningPerformanceTrackerPort):
    """Dummy implementation of the MiningPerformanceTrackerPort."""

    def __init__(
        self,
        config: Optional[MiningPerformanceTrackerDummyConfig] = None,
        logger: Optional[LoggerPort] = None,
    ):
        self._config = config or MiningPerformanceTrackerDummyConfig()
        self._logger = logger

    async def get_current_hashrate(self, miner_ids: List[EntityId]) -> Optional[HashRate]:
        if self._logger:
            self._logger.debug(f"DummyMiningPerformanceTracker: simulating hashrate for {len(miner_ids)} miners")
        return HashRate(value=random.uniform(90.0, 110.0), unit="TH/s")

    async def get_recent_rewards(self, miner_id: Optional[EntityId] = None, limit: int = 10) -> List[MiningReward]:
        if self._logger:
            self._logger.debug(f"DummyMiningPerformanceTracker: simulating rewards for {miner_id} (limit={limit})")
        return []

    async def get_pool_stats(self) -> Optional[PoolStats]:
        return PoolStats(
            current_hashrate=HashRate(value=random.uniform(90.0, 110.0), unit="TH/s"),
            average_hashrate_24h=HashRate(value=random.uniform(85.0, 105.0), unit="TH/s"),
            average_hashrate_7d=HashRate(value=random.uniform(80.0, 100.0), unit="TH/s"),
            unpaid_balance=Satoshi(0),
            estimated_next_payout=Satoshi(0),
            workers=[],
        )

    async def get_worker_stats(self, miner_ids: List[EntityId]) -> List[PoolWorkerStats]:
        return [
            PoolWorkerStats(
                worker_name=str(miner_id),
                hashrate=HashRate(value=random.uniform(90.0, 110.0), unit="TH/s"),
            )
            for miner_id in miner_ids
        ]

    async def get_payout_schedule(self) -> Optional[PayoutSchedule]:
        return PayoutSchedule(frequency=PayoutFrequency.UNKNOWN)


class DummyMiningPerformanceTrackerFactory(MiningPerformanceTrackerAdapterFactory):
    """Factory for the DummyMiningPerformanceTracker."""

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> MiningPerformanceTrackerPort:
        if config is not None and not isinstance(config, MiningPerformanceTrackerDummyConfig):
            raise MiningPerformanceTrackerConfigurationError(
                "Invalid configuration type for Dummy mining performance tracker. "
                "Expected MiningPerformanceTrackerDummyConfig."
            )
        return DummyMiningPerformanceTracker(config=config, logger=logger)
