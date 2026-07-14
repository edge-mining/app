from unittest.mock import AsyncMock, MagicMock

import pytest

from edge_mining.adapters.domain.forecast.providers.home_assistant_api import (
    HomeAssistantForecastProviderFactory,
)
from edge_mining.shared.adapter_configs.forecast import ForecastProviderHomeAssistantConfig
from edge_mining.shared.external_services.common import ExternalServiceAdapter


@pytest.mark.asyncio
async def test_factory_accepts_partial_entity_configuration():
    home_assistant = MagicMock()
    home_assistant.external_service_type = ExternalServiceAdapter.HOME_ASSISTANT_API
    home_assistant.get_entity_state = AsyncMock(return_value=("1.5", {}))
    home_assistant.parse_energy.return_value = 1.5
    config = ForecastProviderHomeAssistantConfig(
        entity_forecast_energy_today="sensor.solar_forecast_today",
    )

    provider = HomeAssistantForecastProviderFactory().create(
        config=config,
        logger=None,
        external_service=home_assistant,
    )

    assert provider.entity_forecast_energy_today == "sensor.solar_forecast_today"
    assert provider.entity_forecast_power_actual_h is None
    assert provider.entity_forecast_energy_actual_h is None

    forecast = await provider.get_forecast()

    assert len(forecast.intervals) == 1
    home_assistant.get_entity_state.assert_awaited_once_with("sensor.solar_forecast_today")
