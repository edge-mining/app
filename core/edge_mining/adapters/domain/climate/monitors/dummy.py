"""
Dummy adapter (Implementation of Port) that simulates
the climate monitoring of Edge Mining Application.
Generates random but plausible temperature and humidity readings.
"""

import random
from datetime import datetime, timezone
from typing import Optional

from edge_mining.domain.climate.entities import ClimateZone
from edge_mining.domain.climate.ports import ClimateMonitorPort
from edge_mining.domain.climate.value_objects import ClimateZoneReading
from edge_mining.domain.common import EntityId
from edge_mining.shared.adapter_configs.climate import ClimateMonitorDummyConfig
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.factories import ClimateMonitorAdapterFactory
from edge_mining.shared.logging.port import LoggerPort


class DummyClimateMonitor(ClimateMonitorPort):
    """Generates plausible fake climate data (temperature + humidity)."""

    def __init__(
        self,
        zone_id: Optional[EntityId] = None,
        zone_name: str = "",
        min_temperature: float = 18.0,
        max_temperature: float = 26.0,
        min_humidity: float = 30.0,
        max_humidity: float = 70.0,
        logger: Optional[LoggerPort] = None,
    ):
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.min_temperature = min_temperature
        self.max_temperature = max_temperature
        self.min_humidity = min_humidity
        self.max_humidity = max_humidity
        self.logger = logger

    async def get_climate_reading(self) -> Optional[ClimateZoneReading]:
        """Generate a random climate reading within configured ranges."""
        temperature = round(random.uniform(self.min_temperature, self.max_temperature), 1)
        humidity = round(random.uniform(self.min_humidity, self.max_humidity), 1)

        reading = ClimateZoneReading(
            zone_id=self.zone_id,
            zone_name=self.zone_name,
            temperature_celsius=temperature,
            humidity=humidity,
            timestamp=datetime.now(timezone.utc),
        )

        if self.logger:
            self.logger.debug(f"DummyClimateMonitor [{self.zone_name}]: " f"Temp={temperature}°C, Humidity={humidity}%")

        return reading


class DummyClimateMonitorFactory(ClimateMonitorAdapterFactory):
    """Factory for creating Dummy climate monitor adapters."""

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
        if not isinstance(config, ClimateMonitorDummyConfig):
            # Use defaults if no config provided
            config = ClimateMonitorDummyConfig()

        zone_id = self._climate_zone.id if self._climate_zone else None
        zone_name = self._climate_zone.name if self._climate_zone else "Unknown"

        return DummyClimateMonitor(
            zone_id=zone_id,
            zone_name=zone_name,
            min_temperature=config.min_temperature,
            max_temperature=config.max_temperature,
            min_humidity=config.min_humidity,
            max_humidity=config.max_humidity,
            logger=logger,
        )
