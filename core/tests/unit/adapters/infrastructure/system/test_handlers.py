"""Unit tests for the SystemConfigurationHandler."""

from unittest.mock import MagicMock

import pytest

from edge_mining.adapters.infrastructure.system.handlers import SystemConfigurationHandler
from edge_mining.domain.user.events import SystemConfigurationUpdated
from edge_mining.domain.user.value_objects import SystemConfiguration
from edge_mining.shared import timezone as tz


@pytest.mark.asyncio
async def test_applies_timezone_and_reconfigures_sun_factory():
    sun_factory = MagicMock()
    handler = SystemConfigurationHandler(sun_factory=sun_factory, logger=MagicMock())

    tz.set_timezone("UTC")
    config = SystemConfiguration(
        timezone="America/New_York",
        latitude=40.0,
        longitude=-74.0,
        scheduler_interval_seconds=15,
    )

    await handler.on_system_configuration_updated(SystemConfigurationUpdated(configuration=config))

    assert str(tz.get_timezone()) == "America/New_York"
    sun_factory.reconfigure.assert_called_once_with(latitude=40.0, longitude=-74.0, timezone="America/New_York")


@pytest.mark.asyncio
async def test_ignores_event_without_configuration():
    sun_factory = MagicMock()
    handler = SystemConfigurationHandler(sun_factory=sun_factory, logger=MagicMock())

    await handler.on_system_configuration_updated(SystemConfigurationUpdated(configuration=None))

    sun_factory.reconfigure.assert_not_called()
