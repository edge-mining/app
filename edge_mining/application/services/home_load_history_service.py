"""Service for collecting and purging home load consumption history."""

from datetime import datetime, timedelta
from typing import List, Optional

from edge_mining.application.interfaces import (
    AdapterServiceInterface,
    EventBusInterface,
    HomeLoadHistoryServiceInterface,
)
from edge_mining.domain.common import EntityId, Timestamp
from edge_mining.domain.home_load.events import (
    LoadConsumptionHistoryCollectedEvent,
    LoadConsumptionHistoryPurgedEvent,
)
from edge_mining.domain.home_load.ports import (
    EnergyLoadHistoryRepository,
    HomeLoadsProfileRepository,
)
from edge_mining.domain.home_load.value_objects import HomeLoadPowerPoint
from edge_mining.shared.logging.port import LoggerPort


class HomeLoadHistoryService(HomeLoadHistoryServiceInterface):
    """Collects power-point data from history providers and manages retention."""

    def __init__(
        self,
        home_loads_repo: HomeLoadsProfileRepository,
        home_load_history_repo: EnergyLoadHistoryRepository,
        adapter_service: AdapterServiceInterface,
        event_bus: Optional[EventBusInterface] = None,
        logger: Optional[LoggerPort] = None,
    ):
        self.home_loads_repo = home_loads_repo
        self.home_load_history_repo = home_load_history_repo
        self.adapter_service = adapter_service
        self._event_bus = event_bus
        self.logger = logger

    async def collect_all(self) -> None:
        """Collect power points from all history providers for all enabled devices.

        For each enabled LoadDevice that has an energy_load_history_provider_id,
        fetches new power points since the last known timestamp (delta ingestion)
        and persists them in the history repository.
        """
        profiles = self.home_loads_repo.get_all()
        if not profiles:
            if self.logger:
                self.logger.debug("No home load profiles found. Skipping history collection.")
            return

        for profile in profiles:
            for device in profile.devices:
                if not device.enabled:
                    continue
                if not device.energy_load_history_provider_id:
                    continue
                await self._collect_for_device(
                    device_id=device.id,
                    device_name=device.name,
                    provider_id=device.energy_load_history_provider_id,
                )

    async def _collect_for_device(
        self,
        device_id: EntityId,
        device_name: str,
        provider_id: EntityId,
    ) -> None:
        """Collect power points for a single device from its history provider."""
        history_provider = await self.adapter_service.get_home_load_history_provider(provider_id, device_id)
        if not history_provider:
            if self.logger:
                self.logger.warning(f"History provider {provider_id} not found for device '{device_name}'. Skipping.")
            return

        now = Timestamp(datetime.now())
        last_ts = self.home_load_history_repo.get_latest_timestamp(device_id)
        if last_ts is not None:
            start = last_ts
        else:
            # First collection: fetch last 24 hours
            start = Timestamp(now - timedelta(hours=24))

        try:
            power_points = await history_provider.get_power_points(start, now)
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Error fetching power points for device '{device_name}' " f"from provider {provider_id}: {e}"
                )
            return

        if not power_points:
            return

        self.home_load_history_repo.add_power_points(device_id, power_points)
        if self.logger:
            self.logger.debug(f"Collected {len(power_points)} power points for device '{device_name}'.")

        if self._event_bus:
            await self._event_bus.publish(
                LoadConsumptionHistoryCollectedEvent(
                    device_id=device_id,
                    device_name=device_name,
                    points_collected=len(power_points),
                )
            )

    async def purge_all(self, retention_days: int = 90) -> None:
        """Purge power points older than retention_days for all devices.

        Iterates all profiles and their devices, purging historical data that
        exceeds the retention window.
        """
        cutoff = Timestamp(datetime.now() - timedelta(days=retention_days))
        profiles = self.home_loads_repo.get_all()
        if not profiles:
            return

        for profile in profiles:
            for device in profile.devices:
                try:
                    purged = self.home_load_history_repo.purge_before(device.id, cutoff)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error purging history for device '{device.name}': {e}")
                    continue

                if purged > 0:
                    if self.logger:
                        self.logger.debug(
                            f"Purged {purged} power points for device '{device.name}' "
                            f"(older than {retention_days} days)."
                        )
                    if self._event_bus:
                        await self._event_bus.publish(
                            LoadConsumptionHistoryPurgedEvent(
                                device_id=device.id,
                                device_name=device.name,
                                points_purged=purged,
                            )
                        )

    def get_device_history(self, device_id: EntityId, start: Timestamp, end: Timestamp) -> List[HomeLoadPowerPoint]:
        """Retrieve stored power points for a device in a time window."""
        return self.home_load_history_repo.get_power_points(device_id, start, end)

    def clear_device_history(self, device_id: EntityId) -> int:
        """Delete all stored power points for a device."""
        removed = self.home_load_history_repo.clear_device_history(device_id)
        if self.logger:
            self.logger.info(f"Cleared {removed} power points for device {device_id}.")
        return removed

    async def collect_devices(self, device_ids: List[EntityId]) -> None:
        """Collect power points for the specified devices only."""
        profiles = self.home_loads_repo.get_all()
        if not profiles:
            return

        target_ids = set(device_ids)
        for profile in profiles:
            for device in profile.devices:
                if device.id not in target_ids:
                    continue
                if not device.energy_load_history_provider_id:
                    if self.logger:
                        self.logger.warning(f"Device '{device.name}' has no history provider configured. Skipping.")
                    continue
                await self._collect_for_device(
                    device_id=device.id,
                    device_name=device.name,
                    provider_id=device.energy_load_history_provider_id,
                )
