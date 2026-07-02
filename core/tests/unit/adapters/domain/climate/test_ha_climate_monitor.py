"""Unit tests for HomeAssistantAPIClimateMonitor adapter."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from edge_mining.adapters.domain.climate.monitors.home_assistant_api import (
    HomeAssistantAPIClimateMonitor,
    HomeAssistantAPIClimateMonitorBuilder,
    HomeAssistantAPIClimateMonitorFactory,
)
from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateZone
from edge_mining.domain.climate.exceptions import ClimateMonitorConfigurationError, ClimateMonitorError
from edge_mining.domain.common import EntityId
from edge_mining.shared.adapter_configs.climate import ClimateMonitorHomeAssistantConfig
from edge_mining.shared.external_services.common import ExternalServiceAdapter


@pytest.fixture
def mock_ha_service():
    """Mock ServiceHomeAssistantAPI."""
    service = AsyncMock()
    service.external_service_type = ExternalServiceAdapter.HOME_ASSISTANT_API
    return service


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def zone() -> ClimateZone:
    return ClimateZone(
        id=EntityId(uuid.uuid4()),
        name="Test Room",
        area_sqm=20.0,
    )


class TestHomeAssistantAPIClimateMonitor:
    """Tests for the HA climate monitor adapter."""

    @pytest.mark.asyncio
    async def test_get_reading_success(self, mock_ha_service, mock_logger):
        mock_ha_service.get_entity_state = AsyncMock(
            side_effect=[
                ("21.5", "°C"),  # temperature
                ("55.0", "%"),  # humidity
            ]
        )

        monitor = HomeAssistantAPIClimateMonitor(
            home_assistant=mock_ha_service,
            logger=mock_logger,
            entity_temperature="sensor.temp",
            entity_humidity="sensor.hum",
            zone_id=EntityId(uuid.uuid4()),
            zone_name="Living Room",
        )

        reading = await monitor.get_climate_reading()
        assert reading is not None
        assert reading.temperature_celsius == 21.5
        assert reading.humidity == 55.0
        assert reading.zone_name == "Living Room"

    @pytest.mark.asyncio
    async def test_get_reading_temperature_only(self, mock_ha_service, mock_logger):
        mock_ha_service.get_entity_state = AsyncMock(return_value=("19.8", "°C"))

        monitor = HomeAssistantAPIClimateMonitor(
            home_assistant=mock_ha_service,
            logger=mock_logger,
            entity_temperature="sensor.temp",
            entity_humidity="",  # no humidity entity
            zone_name="Bedroom",
        )

        reading = await monitor.get_climate_reading()
        assert reading is not None
        assert reading.temperature_celsius == 19.8
        assert reading.humidity is None

    @pytest.mark.asyncio
    async def test_get_reading_unavailable_returns_none(self, mock_ha_service, mock_logger):
        mock_ha_service.get_entity_state = AsyncMock(return_value=("unavailable", None))

        monitor = HomeAssistantAPIClimateMonitor(
            home_assistant=mock_ha_service,
            logger=mock_logger,
            entity_temperature="sensor.temp",
        )

        reading = await monitor.get_climate_reading()
        assert reading is None

    @pytest.mark.asyncio
    async def test_get_reading_unknown_returns_none(self, mock_ha_service, mock_logger):
        mock_ha_service.get_entity_state = AsyncMock(return_value=("unknown", None))

        monitor = HomeAssistantAPIClimateMonitor(
            home_assistant=mock_ha_service,
            logger=mock_logger,
            entity_temperature="sensor.temp",
        )

        reading = await monitor.get_climate_reading()
        assert reading is None

    @pytest.mark.asyncio
    async def test_get_reading_non_numeric_returns_none(self, mock_ha_service, mock_logger):
        mock_ha_service.get_entity_state = AsyncMock(return_value=("not_a_number", "°C"))

        monitor = HomeAssistantAPIClimateMonitor(
            home_assistant=mock_ha_service,
            logger=mock_logger,
            entity_temperature="sensor.temp",
        )

        reading = await monitor.get_climate_reading()
        assert reading is None

    @pytest.mark.asyncio
    async def test_get_reading_fahrenheit_conversion(self, mock_ha_service, mock_logger):
        # 68°F = 20°C
        mock_ha_service.get_entity_state = AsyncMock(return_value=("68", "°F"))

        monitor = HomeAssistantAPIClimateMonitor(
            home_assistant=mock_ha_service,
            logger=mock_logger,
            entity_temperature="sensor.temp",
            unit_temperature="°F",
        )

        reading = await monitor.get_climate_reading()
        assert reading is not None
        assert abs(reading.temperature_celsius - 20.0) < 0.01

    @pytest.mark.asyncio
    async def test_get_reading_exception_returns_none(self, mock_ha_service, mock_logger):
        mock_ha_service.get_entity_state = AsyncMock(side_effect=Exception("Connection error"))

        monitor = HomeAssistantAPIClimateMonitor(
            home_assistant=mock_ha_service,
            logger=mock_logger,
            entity_temperature="sensor.temp",
        )

        reading = await monitor.get_climate_reading()
        assert reading is None

    @pytest.mark.asyncio
    async def test_humidity_out_of_range_ignored(self, mock_ha_service, mock_logger):
        mock_ha_service.get_entity_state = AsyncMock(
            side_effect=[
                ("20.0", "°C"),  # temperature
                ("150.0", "%"),  # humidity out of range
            ]
        )

        monitor = HomeAssistantAPIClimateMonitor(
            home_assistant=mock_ha_service,
            logger=mock_logger,
            entity_temperature="sensor.temp",
            entity_humidity="sensor.hum",
        )

        reading = await monitor.get_climate_reading()
        assert reading is not None
        assert reading.temperature_celsius == 20.0
        assert reading.humidity is None


class TestHomeAssistantAPIClimateMonitorBuilder:
    """Tests for the builder."""

    def test_build_success(self, mock_ha_service, mock_logger):
        builder = HomeAssistantAPIClimateMonitorBuilder(home_assistant=mock_ha_service, logger=mock_logger)
        builder.set_temperature_entity("sensor.temp")
        monitor = builder.build()
        assert isinstance(monitor, HomeAssistantAPIClimateMonitor)

    def test_build_without_temperature_raises(self, mock_ha_service, mock_logger):
        builder = HomeAssistantAPIClimateMonitorBuilder(home_assistant=mock_ha_service, logger=mock_logger)
        with pytest.raises(ClimateMonitorConfigurationError):
            builder.build()

    def test_builder_fluent_api(self, mock_ha_service, mock_logger):
        zone_id = EntityId(uuid.uuid4())
        builder = HomeAssistantAPIClimateMonitorBuilder(home_assistant=mock_ha_service, logger=mock_logger)
        result = (
            builder.set_temperature_entity("sensor.temp", "°C")
            .set_humidity_entity("sensor.hum")
            .set_zone_info(zone_id, "Office")
        )
        assert result is builder  # fluent pattern returns self


class TestHomeAssistantAPIClimateMonitorFactory:
    """Tests for the factory."""

    def test_create_success(self, mock_ha_service, mock_logger, zone):
        config = ClimateMonitorHomeAssistantConfig(
            entity_temperature="sensor.temp",
            entity_humidity="sensor.hum",
        )
        factory = HomeAssistantAPIClimateMonitorFactory()
        factory.from_climate_zone(zone)
        monitor = factory.create(config=config, logger=mock_logger, external_service=mock_ha_service)
        assert isinstance(monitor, HomeAssistantAPIClimateMonitor)

    def test_create_without_external_service_raises(self, mock_logger, zone):
        config = ClimateMonitorHomeAssistantConfig(entity_temperature="sensor.temp")
        factory = HomeAssistantAPIClimateMonitorFactory()
        factory.from_climate_zone(zone)
        with pytest.raises(ClimateMonitorError, match="required"):
            factory.create(config=config, logger=mock_logger, external_service=None)

    def test_create_wrong_service_type_raises(self, mock_logger, zone):
        config = ClimateMonitorHomeAssistantConfig(entity_temperature="sensor.temp")
        wrong_service = AsyncMock()
        wrong_service.external_service_type = "mqtt"
        factory = HomeAssistantAPIClimateMonitorFactory()
        factory.from_climate_zone(zone)
        with pytest.raises(ClimateMonitorError, match="HomeAssistantAPI"):
            factory.create(config=config, logger=mock_logger, external_service=wrong_service)

    def test_create_invalid_config_raises(self, mock_ha_service, mock_logger, zone):
        config = ClimateMonitorHomeAssistantConfig(entity_temperature="")  # invalid
        factory = HomeAssistantAPIClimateMonitorFactory()
        factory.from_climate_zone(zone)
        with pytest.raises(ClimateMonitorConfigurationError):
            factory.create(config=config, logger=mock_logger, external_service=mock_ha_service)

    def test_create_wrong_config_type_raises(self, mock_ha_service, mock_logger, zone):
        factory = HomeAssistantAPIClimateMonitorFactory()
        factory.from_climate_zone(zone)
        with pytest.raises(ClimateMonitorConfigurationError):
            factory.create(config=MagicMock(), logger=mock_logger, external_service=mock_ha_service)
