"""
Home Assistant API Energy Load History adapter (Implementation of Port)
for the energy home loads domain of Edge Mining Application.

The adapter is device-scoped: each instance is bound at construction time to a
single ``LoadDevice`` via its ``device_id``. History is fetched from Home
Assistant and opportunistically cached into the ``EnergyLoadHistoryRepository``
for that device.
"""

from datetime import datetime, timedelta
from typing import List, Optional, cast

from edge_mining.adapters.domain.home_load.history_providers.helpers import group_power_points_into_intervals
from edge_mining.adapters.infrastructure.homeassistant.homeassistant_api import (
    ServiceHomeAssistantAPI,
)
from edge_mining.adapters.infrastructure.homeassistant.models import EntityHistory
from edge_mining.adapters.infrastructure.homeassistant.utils import EntityState
from edge_mining.domain.common import EntityId, Timestamp, Watts
from edge_mining.domain.home_load.common import EnergyLoadHistoryProviderAdapter
from edge_mining.domain.home_load.entities import LoadDevice
from edge_mining.domain.home_load.exceptions import (
    EnergyLoadHistoryProviderConfigurationError,
    EnergyLoadHistoryProviderError,
)
from edge_mining.domain.home_load.ports import EnergyLoadHistoryProviderPort, EnergyLoadHistoryRepository
from edge_mining.domain.home_load.value_objects import HomeLoadEnergyInterval, HomeLoadPowerPoint
from edge_mining.shared.adapter_configs.home_load import (
    EnergyLoadHistoryProviderHomeAssistantAPIConfig,
)
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import EnergyLoadHistoryAdapterFactory
from edge_mining.shared.logging.port import LoggerPort


class HomeAssistantAPIEnergyLoadHistoryProviderFactory(EnergyLoadHistoryAdapterFactory):
    """Factory for ``HomeAssistantAPIEnergyLoadHistoryProvider`` instances.

    The infrastructure repository is injected at factory construction time
    (one repo serves all devices). ``from_load_device`` binds the device-scope
    before ``create`` is called.
    """

    def __init__(self, history_repo: EnergyLoadHistoryRepository):
        self._history_repo = history_repo
        self._load_device: Optional[LoadDevice] = None

    def from_load_device(self, load_device: LoadDevice) -> None:
        """Bind the factory to the LoadDevice this adapter will serve."""
        self._load_device = load_device

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> "HomeAssistantAPIEnergyLoadHistoryProvider":
        """Build a device-scoped Home Assistant API history adapter."""
        if self._load_device is None:
            raise EnergyLoadHistoryProviderConfigurationError(
                "from_load_device(...) must be called before create(...)."
            )

        if not external_service:
            raise EnergyLoadHistoryProviderError("External service is required for EnergyLoadHistoryProviderAdapter.")

        if external_service.external_service_type != ExternalServiceAdapter.HOME_ASSISTANT_API:
            raise EnergyLoadHistoryProviderError("External service must be of type Home Assistant API")

        if not isinstance(config, EnergyLoadHistoryProviderHomeAssistantAPIConfig):
            raise EnergyLoadHistoryProviderConfigurationError(
                "Invalid configuration type for HomeAssistantAPI energy load history provider. "
                "Expected EnergyLoadHistoryProviderHomeAssistantAPIConfig."
            )

        service_home_assistant_api = cast(ServiceHomeAssistantAPI, external_service)

        return HomeAssistantAPIEnergyLoadHistoryProvider(
            device_id=self._load_device.id,
            entity_power=config.entity_power,
            home_assistant=service_home_assistant_api,
            history_repo=self._history_repo,
            logger=logger,
        )


class HomeAssistantAPIEnergyLoadHistoryProvider(EnergyLoadHistoryProviderPort):
    """Fetches energy load history for one LoadDevice from a Home Assistant instance.

    Caches raw power points in the injected ``EnergyLoadHistoryRepository``
    (infrastructure dependency — not part of the port contract) to avoid
    re-hitting Home Assistant for already-observed windows.
    """

    _CACHE_STALENESS = timedelta(minutes=5)

    def __init__(
        self,
        device_id: EntityId,
        entity_power: str,
        home_assistant: ServiceHomeAssistantAPI,
        history_repo: EnergyLoadHistoryRepository,
        logger: Optional[LoggerPort] = None,
    ):
        super().__init__(
            device_id=device_id,
            provider_type=EnergyLoadHistoryProviderAdapter.HOME_ASSISTANT_API,
        )
        self._home_assistant = home_assistant
        self._history_repo = history_repo
        self._logger = logger

        if not entity_power or entity_power.strip() == "":
            raise EnergyLoadHistoryProviderConfigurationError("Power entity must be provided and cannot be empty.")
        self._entity_power = entity_power

        if self._logger:
            self._logger.debug(f"HA history adapter bound to device {device_id} (entity='{entity_power}')")

    async def get_power_points(self, start: Timestamp, end: Timestamp) -> List[HomeLoadPowerPoint]:
        """Return power points for the bound device in [start, end).

        Hits the cache first; fetches missing or stale tail from Home Assistant.
        """
        if start >= end:
            return []

        cached = self._history_repo.get_power_points(self.device_id, start, end)

        latest_cached: Optional[Timestamp] = max((p.timestamp for p in cached), default=None)
        now_ts = Timestamp(datetime.now())

        if latest_cached is None:
            fetched = await self._fetch_from_home_assistant(start, end)
            if fetched:
                self._history_repo.add_power_points(self.device_id, fetched)
            return sorted(fetched, key=lambda p: p.timestamp)

        if now_ts - latest_cached > self._CACHE_STALENESS and latest_cached < end:
            if self._logger:
                self._logger.debug(
                    f"Cache tail stale for device {self.device_id}: "
                    f"latest={latest_cached}, now={now_ts}. Fetching incremental."
                )
            tail = await self._fetch_from_home_assistant(latest_cached, end)
            if tail:
                self._history_repo.add_power_points(self.device_id, tail)
                cached.extend(tail)

        return sorted(cached, key=lambda p: p.timestamp)

    async def get_history(self, start: Timestamp, end: Timestamp) -> List[HomeLoadEnergyInterval]:
        """Return 1-hour consumption intervals for the bound device in [start, end)."""
        if self._logger:
            self._logger.debug(f"Computing 1h intervals for device {self.device_id} in [{start}, {end}).")
        power_points = await self.get_power_points(start, end)
        return group_power_points_into_intervals(power_points, start=start, end=end)

    async def _fetch_from_home_assistant(self, start: Timestamp, end: Timestamp) -> List[HomeLoadPowerPoint]:
        """Fetch raw power points from Home Assistant REST API."""
        entity_history: Optional[EntityHistory] = await self._home_assistant.get_entity_history(
            self._entity_power, start, end
        )
        if not entity_history:
            if self._logger:
                self._logger.error(f"No history data found for entity '{self._entity_power}'")
            return []

        points: List[HomeLoadPowerPoint] = []
        for raw in entity_history.history:
            if raw.value is None or raw.value.lower() in (
                EntityState.UNAVAILABLE.value,
                EntityState.UNKNOWN.value,
            ):
                if self._logger:
                    self._logger.error(f"Invalid power data point '{raw.value}'. Skipping.")
                continue

            unit = raw.unit or "W"
            parsed = self._home_assistant.parse_power(raw.value, unit, self._entity_power or "N/A")
            if parsed is None:
                if self._logger:
                    self._logger.error(f"Failed to parse power '{raw.value}' for '{self._entity_power}'. Skipping.")
                continue

            points.append(HomeLoadPowerPoint(timestamp=Timestamp(raw.timestamp), power=Watts(parsed)))

        return points
