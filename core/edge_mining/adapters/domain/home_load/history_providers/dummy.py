"""Dummy adapter that serves cached power points from the history repository."""

from typing import List, Optional

from edge_mining.adapters.domain.home_load.history_providers.helpers import group_power_points_into_intervals
from edge_mining.domain.common import EntityId, Timestamp
from edge_mining.domain.home_load.common import EnergyLoadHistoryProviderAdapter
from edge_mining.domain.home_load.ports import EnergyLoadHistoryProviderPort, EnergyLoadHistoryRepository
from edge_mining.domain.home_load.value_objects import HomeLoadEnergyInterval, HomeLoadPowerPoint
from edge_mining.shared.logging.port import LoggerPort


class DummyEnergyLoadHistoryProvider(EnergyLoadHistoryProviderPort):
    """Dummy history provider that reads directly from the history repository.

    No external fetching — it just serves whatever has already been ingested
    into the repo for the bound device. Useful for testing and as a fallback.
    """

    def __init__(
        self,
        device_id: EntityId,
        history_repo: EnergyLoadHistoryRepository,
        logger: Optional[LoggerPort] = None,
    ):
        super().__init__(device_id=device_id, provider_type=EnergyLoadHistoryProviderAdapter.DUMMY)
        self._history_repo = history_repo
        self._logger = logger

    async def get_power_points(
        self, start: Timestamp, end: Timestamp, force_refresh: bool = False
    ) -> List[HomeLoadPowerPoint]:
        """Return cached power points for this device in [start, end).

        ``force_refresh`` has no effect here: the dummy provider has no upstream
        source to re-fetch from, it only serves what is already in the repo.
        """
        if self._logger:
            self._logger.debug(f"DummyEnergyLoadHistoryProvider: get_power_points({self.device_id}, [{start}, {end}))")
        return self._history_repo.get_power_points(self.device_id, start, end)

    async def get_history(self, start: Timestamp, end: Timestamp) -> List[HomeLoadEnergyInterval]:
        """Return 1-hour consumption intervals for this device in [start, end)."""
        if self._logger:
            self._logger.debug(f"DummyEnergyLoadHistoryProvider: get_history({self.device_id}, [{start}, {end}))")
        power_points = await self.get_power_points(start, end)
        return group_power_points_into_intervals(power_points, start=start, end=end)
