"""
Home Assistant API Energy Load History adapter (Implementation of Port)
for the energy home loads domain of Edge Mining Application
"""

from datetime import timedelta
from typing import List, Optional, cast

from edge_mining.adapters.infrastructure.homeassistant.homeassistant_api import (
    ServiceHomeAssistantAPI,
)
from edge_mining.adapters.infrastructure.homeassistant.models import EntityHistory
from edge_mining.adapters.infrastructure.homeassistant.utils import EntityState
from edge_mining.domain.common import Timestamp, WattHours, Watts
from edge_mining.domain.home_load.common import EnergyLoadHistoryProviderAdapter
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
    """
    Factory for creating HomeAssistantAPIEnergyLoadHistoryProvider instances.
    """

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> "HomeAssistantAPIEnergyLoadHistoryProvider":
        """Creates a HomeAssistantAPIEnergyLoadHistoryProvider instance."""

        # Needs to have the Home Assistant API service as external_service
        if not external_service:
            raise EnergyLoadHistoryProviderError("External service is required for EnergyLoadHistoryProviderAdapter.")

        if not external_service.external_service_type == ExternalServiceAdapter.HOME_ASSISTANT_API:
            raise EnergyLoadHistoryProviderError("External service must be of type Home Assistant API")

        if not isinstance(config, EnergyLoadHistoryProviderHomeAssistantAPIConfig):
            raise EnergyLoadHistoryProviderConfigurationError(
                "Invalid configuration type for HomeAssistantAPI energy load history provider. "
                "Expected EnergyLoadHistoryProviderHomeAssistantAPIConfig."
            )

        # Get the config from the energy load history provider config
        energy_load_history_provider_config: EnergyLoadHistoryProviderHomeAssistantAPIConfig = config
        service_home_assistant_api = cast(ServiceHomeAssistantAPI, external_service)

        # In that case the builder is not required because the adapter has only a few parameters
        # that can be passed directly from the config.
        # If in the future more complex logic is required to create the adapter, a builder can be introduced.
        return HomeAssistantAPIEnergyLoadHistoryProvider(
            home_assistant=service_home_assistant_api,
            entity_power=energy_load_history_provider_config.entity_power,
            logger=logger,
        )


class HomeAssistantAPIEnergyLoadHistoryProvider(EnergyLoadHistoryProviderPort):
    """
    Fetches energy load history values from a Home Assistant API instance via its REST API.
    """

    def __init__(
        self,
        entity_power: str,
        home_assistant: ServiceHomeAssistantAPI,
        history_repo: EnergyLoadHistoryRepository,
        logger: Optional[LoggerPort] = None,
    ):
        # Initialize the HomeAssistant API Service
        super().__init__(provider_type=EnergyLoadHistoryProviderAdapter.HOME_ASSISTANT_API, history_repo=history_repo)
        self.home_assistant = home_assistant
        self.logger = logger

        if not entity_power or entity_power.strip() == "":
            raise EnergyLoadHistoryProviderConfigurationError("Power entity must be provided and cannot be empty.")

        self.entity_power = entity_power

        if self.logger:
            self.logger.debug(f"Entities Configured:Power History='{entity_power}'")

    def get_history(self, start: Timestamp, end: Timestamp) -> List[HomeLoadEnergyInterval]:
        """Retrieves a list of consumption intervals from the repository."""
        if self.logger:
            self.logger.debug("Fetching history energy data from Home Assistant...")

        home_load_energy_intervals: List[HomeLoadEnergyInterval] = []

        # First, get the home load power data points from the repository.
        # If not available or history data are too old, fetch from Home Assistant API.
        load_power_points: List[HomeLoadPowerPoint] = self.history_repo.get_power_points_by_time_range(start, end)
        if not load_power_points:
            if self.logger:
                self.logger.debug(
                    f"No power data points found in repository for range {start} - {end}. "
                    f"Fetching from Home Assistant API..."
                )
            load_power_points = self._fetch_power_data_points_from_home_assistant(start, end)

            # Store fetched power points into the repository for future use
            if load_power_points:
                self.history_repo.add_power_points(load_power_points)
                if self.logger:
                    self.logger.debug(f"Stored {len(load_power_points)} power data points into the repository.")
            else:
                if self.logger:
                    self.logger.debug("No power data points fetched from Home Assistant API.")
        else:
            # Get le latest timestamp of the retrieved power points
            latest = max(point.timestamp for point in load_power_points)
            now = Timestamp.now()

            if self.logger:
                self.logger.debug(
                    f"Retrieved {len(load_power_points)} power data points from repository for range {start} - {latest}."
                )

            if latest - now > timedelta(minutes=5):
                if self.logger:
                    self.logger.debug(
                        f"Power data points are outdated (latest: {latest}, now: {now}). "
                        f"Fetching latest data from Home Assistant API..."
                    )
                # Fetch only the missing data points from Home Assistant API
                fetched_power_points = self._fetch_power_data_points_from_home_assistant(latest, end)

                if fetched_power_points:
                    # Append the newly fetched points to the existing list
                    load_power_points.extend(fetched_power_points)
                    # Store fetched power points into the repository for future use
                    self.history_repo.add_power_points(fetched_power_points)
                    if self.logger:
                        self.logger.debug(
                            f"Fetched and stored {len(fetched_power_points)} new power data points into the repository."
                        )
                else:
                    if self.logger:
                        self.logger.debug("No new power data points fetched from Home Assistant API.")

        # Group power points into 1-hour intervals
        home_load_energy_intervals = self._group_power_points_into_intervals(
            power_points=load_power_points, start=start, end=end
        )

        return home_load_energy_intervals

    def _fetch_power_data_points_from_home_assistant(
        self, start: Timestamp, end: Timestamp
    ) -> List[HomeLoadPowerPoint]:
        """
        Fetches power data points from Home Assistant API for the specified time range.
        """
        entity_history: Optional[EntityHistory] = self.home_assistant.get_entity_history(self.entity_power, start, end)

        if not entity_history:
            if self.logger:
                self.logger.error(f"No history data found for entity '{self.entity_power}'")
            return []

        load_power_points: List[HomeLoadPowerPoint] = []
        for power_data_point in entity_history.history:
            # Skip invalid or unavailable data points retrieved from Home Assistant
            if power_data_point.value is None or power_data_point.value.lower() in [
                EntityState.UNAVAILABLE.value,
                EntityState.UNKNOWN.value,
            ]:
                if self.logger:
                    self.logger.error(f"Invalid power data point value '{power_data_point.value}'. Skipping.")
                continue

            # If entity unit is not set, assume "W"
            if power_data_point.unit is None:
                power_data_point.unit = "W"

            parsed_power = self.home_assistant.parse_power(
                power_data_point.value, power_data_point.unit, self.entity_power or "N/A"
            )

            if parsed_power is None:
                if self.logger:
                    self.logger.error(
                        f"Failed to parse power data point value '{power_data_point.value}' "
                        f"for entity '{self.entity_power}'. Skipping."
                    )
                continue

            load_power_points.append(
                HomeLoadPowerPoint(timestamp=Timestamp(power_data_point.timestamp), power=Watts(parsed_power))
            )

        return load_power_points

    def _group_power_points_into_intervals(
        self, power_points: List[HomeLoadPowerPoint], start: Optional[Timestamp] = None, end: Optional[Timestamp] = None
    ) -> List[HomeLoadEnergyInterval]:
        """
        Groups power points into 1-hour intervals and creates HomeLoadEnergyInterval instances.
        """

        # The current implementation calculates one-hour steps starting from the timestamp of the first data point.
        # This approach ensures that all data is processed in contiguous blocks.
        #
        # Another approach could be to align intervals to the top of the hour (e.g., 00:00-01:00, 01:00-02:00, etc.)
        # creating fixed hourly slots, but it might leave some data points at the beginning or end outside of any
        # interval if they don't fall neatly into a fixed hour.
        if not power_points:
            return []

        intervals: List[HomeLoadEnergyInterval] = []

        # Sort power points by timestamp to ensure correct ordering
        sorted_points = sorted(power_points, key=lambda p: p.timestamp)

        # If start or end are not provided, derive them from the power points
        if start is None:
            start = sorted_points[0].timestamp
        if end is None:
            end = sorted_points[-1].timestamp

        # Check that start is before end
        if start >= end:
            raise ValueError("Start timestamp must be before end timestamp.")

        # Create 1-hour intervals from start to end
        current_start = start
        while current_start < end:
            current_end = current_start + timedelta(hours=1)

            # Don't exceed the end boundary
            if current_end > end:
                current_end = end

            # Filter power points that fall within this interval
            interval_points = [point for point in sorted_points if current_start <= point.timestamp < current_end]

            # Create the interval using the factory method
            if interval_points:
                interval = HomeLoadEnergyInterval.create_from_power_points(
                    start=current_start,
                    end=current_end,
                    power_points=interval_points,
                )
                intervals.append(interval)
            else:
                # Create an empty interval with no power points and zero energy
                interval = HomeLoadEnergyInterval(
                    start=current_start,
                    end=current_end,
                    energy=WattHours(0.0),
                    power_points=[],
                )
                intervals.append(interval)

            # Move to the next hour
            current_start = current_end

        return intervals
