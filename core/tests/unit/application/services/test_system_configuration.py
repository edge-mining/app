"""Unit tests for the system configuration management in ConfigurationService."""

from unittest.mock import MagicMock

import pytest

from edge_mining.adapters.domain.user.repositories import InMemorySettingsRepository
from edge_mining.adapters.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from edge_mining.application.services.configuration_service import ConfigurationService
from edge_mining.domain.exceptions import ConfigurationError
from edge_mining.domain.user.events import SystemConfigurationUpdated
from edge_mining.domain.user.value_objects import SystemConfiguration


@pytest.fixture
def logger():
    return MagicMock()


@pytest.fixture
def event_bus(logger):
    return InMemoryEventBus(logger)


@pytest.fixture
def config_service(logger, event_bus):
    persistence = MagicMock()
    persistence.settings_repo = InMemorySettingsRepository()
    return ConfigurationService(persistence_settings=persistence, event_bus=event_bus, logger=logger)


class TestGetSystemConfiguration:
    def test_returns_defaults_when_empty(self, config_service):
        config = config_service.get_system_configuration()
        assert config == SystemConfiguration()


class TestUpdateSystemConfiguration:
    @pytest.mark.asyncio
    async def test_persists_and_returns_configuration(self, config_service):
        new_config = SystemConfiguration(
            timezone="America/New_York",
            latitude=40.0,
            longitude=-74.0,
            scheduler_interval_seconds=15,
        )
        result = await config_service.update_system_configuration(new_config)

        assert result == new_config
        assert config_service.get_system_configuration() == new_config

    @pytest.mark.asyncio
    async def test_publishes_event(self, config_service, event_bus):
        received = []

        async def collect(event: SystemConfigurationUpdated) -> None:
            received.append(event)

        event_bus.subscribe(SystemConfigurationUpdated, collect, blocking=True)

        new_config = SystemConfiguration(timezone="UTC", scheduler_interval_seconds=30)
        await config_service.update_system_configuration(new_config)

        assert len(received) == 1
        assert received[0].configuration == new_config

    @pytest.mark.asyncio
    async def test_rejects_invalid_timezone(self, config_service):
        with pytest.raises(ConfigurationError):
            await config_service.update_system_configuration(SystemConfiguration(timezone="Not/AZone"))

    @pytest.mark.asyncio
    @pytest.mark.parametrize("latitude", [-91.0, 91.0])
    async def test_rejects_out_of_range_latitude(self, config_service, latitude):
        with pytest.raises(ConfigurationError):
            await config_service.update_system_configuration(SystemConfiguration(latitude=latitude))

    @pytest.mark.asyncio
    async def test_rejects_non_positive_interval(self, config_service):
        with pytest.raises(ConfigurationError):
            await config_service.update_system_configuration(SystemConfiguration(scheduler_interval_seconds=0))
