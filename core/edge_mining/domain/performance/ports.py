"""Collection of Ports for the Mining Performance Analysis domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import List, Optional

from edge_mining.domain.common import EntityId
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.value_objects import (
    MiningReward,
    PayoutSchedule,
    PoolStats,
    PoolWorkerStats,
)


class MiningPerformanceTrackerPort(ABC):
    """Port for the Mining Performance Tracker."""

    @abstractmethod
    async def get_current_hashrate(self, miner_ids: List[EntityId]) -> Optional[HashRate]:
        """Gets the current hashrate from the pool or devices."""
        raise NotImplementedError

    @abstractmethod
    async def get_recent_rewards(self, miner_id: Optional[EntityId] = None, limit: int = 10) -> List[MiningReward]:
        """Gets recent mining rewards."""
        raise NotImplementedError

    @abstractmethod
    async def get_pool_stats(self) -> Optional[PoolStats]:
        """Gets account-level pool statistics (hashrate aggregates, balance, payout)."""
        raise NotImplementedError

    @abstractmethod
    async def get_worker_stats(self, miner_ids: List[EntityId]) -> List[PoolWorkerStats]:
        """Gets per-worker statistics as reported by the pool."""
        raise NotImplementedError

    @abstractmethod
    async def get_payout_schedule(self) -> Optional[PayoutSchedule]:
        """Gets the payout policy advertised by the pool, if known."""
        raise NotImplementedError


class MiningPerformanceTrackerRepository(ABC):
    """Port for the Mining Performance Tracker Repository."""

    @abstractmethod
    def add(self, tracker: MiningPerformanceTracker) -> None:
        """Adds a new mining performance tracker to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, tracker_id: EntityId) -> Optional[MiningPerformanceTracker]:
        """Retrieves a mining performance tracker by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[MiningPerformanceTracker]:
        """Retrieves all mining performance trackers from the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, tracker: MiningPerformanceTracker) -> None:
        """Updates a mining performance tracker in the repository."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, tracker_id: EntityId) -> None:
        """Removes a mining performance tracker from the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_external_service_id(self, external_service_id: EntityId) -> List[MiningPerformanceTracker]:
        """
        Retrieves a list of mining performance trackers
        by its associated external service ID.
        """
        raise NotImplementedError
