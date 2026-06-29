"""
Home Assistant API adapter (Implementation of Port)
for the climate monitoring of Edge Mining Application using the Home Assistant API.
"""

from datetime import datetime, timezone
from typing import Optional, cast

from edge_mining.adapters.infrastructure.homeassistant.homeassistant_api import (
    ServiceHomeAssistantAPI,
)
from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateZone
from edge_mining.domain.climate.exceptions import ClimateMonitorConfigurationError, ClimateMonitorError
from edge_mining.domain.climate.ports import ClimateMonitorPort
from edge_mining.domain.climate.value_objects import ClimateZoneReading
from edge_mining.domain.common import EntityId
from edge_mining.shared.adapter_configs.climate import ClimateMonitorHomeAssistantConfig
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import ClimateMonitorAdapterFactory
from edge_mining.shared.logging.port import LoggerPort


class HomeAssistantAPIClimateMonitorFactory(ClimateMonitorAdapterFactory):
    """Factory for creating Home Assistant API climate monitor adapters."""

    def __init__(self):
        self._climate_zone: Optional[ClimateZone] = None

    def from_climate_zone(self, climate_zone: ClimateZone) -> None:
        """Set the climate zone for the factory."""
        self._climate_zone = climate_zone

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> ClimateMonitorPort:
        if not external_service:
            raise ClimateMonitorError("HomeAssistantAPI Service is required for climate monitoring.")
        if not external_service.external_service_type == ExternalServiceAdapter.HOME_ASSISTANT_API:
            raise ClimateMonitorError("External service must be of type HomeAssistantAPI.")
        if not isinstance(config, ClimateMonitorHomeAssistantConfig):
            raise ClimateMonitorConfigurationError(
                "Invalid configuration type. Expected ClimateMonitorHomeAssistantConfig."
            )

        climate_config: ClimateMonitorHomeAssistantConfig = config
        if not climate_config.is_valid(ClimateMonitorAdapter.HOME_ASSISTANT_API):
            raise ClimateMonitorConfigurationError(
                "Invalid climate monitor configuration: entity_temperature is required."
            )

        service_home_assistant_api = cast(ServiceHomeAssistantAPI, external_service)

        builder = HomeAssistantAPIClimateMonitorBuilder(home_assistant=service_home_assistant_api, logger=logger)
        builder.set_temperature_entity(climate_config.entity_temperature, climate_config.unit_temperature)

        if climate_config.entity_humidity:
            builder.set_humidity_entity(climate_config.entity_humidity)

        if self._climate_zone:
            builder.set_zone_info(self._climate_zone.id, self._climate_zone.name)

        return builder.build()


class HomeAssistantAPIClimateMonitorBuilder:
    """Builder for constructing HomeAssistantAPIClimateMonitor instances."""

    def __init__(self, home_assistant: ServiceHomeAssistantAPI, logger: Optional[LoggerPort]):
        self.home_assistant: ServiceHomeAssistantAPI = home_assistant
        self.logger: Optional[LoggerPort] = logger
        self.entity_temperature: str = ""
        self.unit_temperature: str = "°C"
        self.entity_humidity: str = ""
        self.zone_id: Optional[EntityId] = None
        self.zone_name: str = ""

    def set_temperature_entity(self, entity_id: str, unit: str = "°C") -> "HomeAssistantAPIClimateMonitorBuilder":
        """Set the Home Assistant entity ID for temperature reading."""
        self.entity_temperature = entity_id
        self.unit_temperature = unit
        return self

    def set_humidity_entity(self, entity_id: str) -> "HomeAssistantAPIClimateMonitorBuilder":
        """Set the Home Assistant entity ID for humidity reading."""
        self.entity_humidity = entity_id
        return self

    def set_zone_info(self, zone_id: EntityId, zone_name: str) -> "HomeAssistantAPIClimateMonitorBuilder":
        """Set the climate zone info for reading context."""
        self.zone_id = zone_id
        self.zone_name = zone_name
        return self

    def build(self) -> "HomeAssistantAPIClimateMonitor":
        """Build the climate monitor adapter instance."""
        if not self.entity_temperature:
            raise ClimateMonitorConfigurationError("Temperature entity is required to build climate monitor.")
        return HomeAssistantAPIClimateMonitor(
            home_assistant=self.home_assistant,
            logger=self.logger,
            entity_temperature=self.entity_temperature,
            unit_temperature=self.unit_temperature,
            entity_humidity=self.entity_humidity,
            zone_id=self.zone_id,
            zone_name=self.zone_name,
        )


class HomeAssistantAPIClimateMonitor(ClimateMonitorPort):
    """
    Home Assistant API implementation of ClimateMonitorPort.
    Retrieves temperature and humidity from HA entities.
    """

    def __init__(
        self,
        home_assistant: ServiceHomeAssistantAPI,
        logger: Optional[LoggerPort],
        entity_temperature: str,
        unit_temperature: str = "°C",
        entity_humidity: str = "",
        zone_id: Optional[EntityId] = None,
        zone_name: str = "",
    ):
        super().__init__(climate_monitor_type=ClimateMonitorAdapter.HOME_ASSISTANT_API)
        self.home_assistant = home_assistant
        self.logger = logger
        self.entity_temperature = entity_temperature
        self.unit_temperature = unit_temperature
        self.entity_humidity = entity_humidity
        self.zone_id = zone_id
        self.zone_name = zone_name

    async def get_climate_reading(self) -> Optional[ClimateZoneReading]:
        """
        Get current climate reading from Home Assistant.
        Returns a ClimateZoneReading with temperature and optionally humidity.
        """
        try:
            # Read temperature
            state_temp, _ = await self.home_assistant.get_entity_state(self.entity_temperature)
            if state_temp is None or state_temp in ("unavailable", "unknown"):
                if self.logger:
                    self.logger.warning(
                        f"Climate monitor: temperature entity '{self.entity_temperature}' returned state: {state_temp}"
                    )
                return None

            temperature = self._parse_temperature(state_temp)
            if temperature is None:
                return None

            # Read humidity (optional)
            humidity: Optional[float] = None
            if self.entity_humidity:
                state_hum, _ = await self.home_assistant.get_entity_state(self.entity_humidity)
                if state_hum and state_hum not in ("unavailable", "unknown"):
                    humidity = self._parse_humidity(state_hum)

            return ClimateZoneReading(
                zone_id=self.zone_id,
                zone_name=self.zone_name,
                temperature_celsius=temperature,
                humidity=humidity,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Climate monitor error reading from HA: {e}")
            return None

    def _parse_temperature(self, state: str) -> Optional[float]:
        """Parse temperature value from HA state string."""
        try:
            value = float(state)
            # Convert to Celsius if needed
            if self.unit_temperature.upper() in ("°F", "F"):
                value = (value - 32) * 5 / 9
            elif self.unit_temperature.upper() in ("K",):
                value = value - 273.15
            return round(value, 2)
        except (ValueError, TypeError):
            if self.logger:
                self.logger.error(
                    f"Climate monitor: unable to parse temperature '{state}' from entity '{self.entity_temperature}'"
                )
            return None

    def _parse_humidity(self, state: str) -> Optional[float]:
        """Parse humidity percentage from HA state string."""
        try:
            value = float(state)
            if 0 <= value <= 100:
                return round(value, 1)
            if self.logger:
                self.logger.warning(f"Climate monitor: humidity value {value}% out of range [0-100]")
            return None
        except (ValueError, TypeError):
            if self.logger:
                self.logger.error(
                    f"Climate monitor: unable to parse humidity '{state}' from entity '{self.entity_humidity}'"
                )
            return None
