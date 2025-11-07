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
from edge_mining.domain.home_load.ports import EnergyLoadHistoryProviderPort
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
        home_assistant: ServiceHomeAssistantAPI,
        entity_power: str,
        logger: Optional[LoggerPort] = None,
    ):
        # Initialize the HomeAssistant API Service
        super().__init__(provider_type=EnergyLoadHistoryProviderAdapter.HOME_ASSISTANT_API)
        self.home_assistant = home_assistant
        self.logger = logger

        if not entity_power or entity_power.strip() == "":
            raise EnergyLoadHistoryProviderConfigurationError("Power entity must be provided and cannot be empty.")

        self.entity_power = entity_power

        if self.logger:
            self.logger.debug(f"Entities Configured:Power History='{entity_power}'")

    def get_history(self, start: Timestamp, end: Timestamp) -> List[HomeLoadEnergyInterval]:
        """Retrieves a list of consumption intervals from a data source."""
        if self.logger:
            self.logger.debug("Fetching history energy data from Home Assistant...")

        home_load_energy_intervals: List[HomeLoadEnergyInterval] = []

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

        # Group power points into 1-hour intervals
        home_load_energy_intervals = self._group_power_points_into_intervals(
            power_points=load_power_points, start=start, end=end
        )

        return home_load_energy_intervals

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
