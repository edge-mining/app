"""Unit tests for LoadForecastModelTrainingService.train_device and get_models."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from edge_mining.application.services.load_forecast_training_service import LoadForecastModelTrainingService
from edge_mining.domain.common import EntityId
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.entities import LoadConsumptionModel, LoadDevice


@pytest.fixture
def mock_home_loads_repo():
    return MagicMock()


@pytest.fixture
def mock_history_repo():
    return MagicMock()


@pytest.fixture
def mock_model_repo():
    return MagicMock()


@pytest.fixture
def logger():
    mock = MagicMock()
    mock.debug = MagicMock()
    mock.info = MagicMock()
    mock.warning = MagicMock()
    mock.error = MagicMock()
    return mock


@pytest.fixture
def service(mock_home_loads_repo, mock_history_repo, mock_model_repo, logger):
    return LoadForecastModelTrainingService(
        home_loads_repo=mock_home_loads_repo,
        history_repo=mock_history_repo,
        model_repo=mock_model_repo,
        logger=logger,
    )


@pytest.fixture
def device_id() -> EntityId:
    return EntityId(uuid.uuid4())


@pytest.fixture
def profile_with_device(device_id):
    device = LoadDevice(id=device_id, name="Dishwasher", enabled=True)
    profile = HomeLoadsProfile(name="Test Home", devices=[device])
    return profile


class TestTrainDevice:
    @pytest.mark.asyncio
    async def test_train_device_calls_train_for_device(
        self, service, mock_home_loads_repo, device_id, profile_with_device
    ):
        mock_home_loads_repo.get_all.return_value = [profile_with_device]

        with patch.object(service, "_train_for_device", new_callable=AsyncMock) as mock_train:
            await service.train_device(device_id)
            mock_train.assert_awaited_once_with(device_id, "Dishwasher", 8)

    @pytest.mark.asyncio
    async def test_train_device_with_custom_lookback(
        self, service, mock_home_loads_repo, device_id, profile_with_device
    ):
        mock_home_loads_repo.get_all.return_value = [profile_with_device]

        with patch.object(service, "_train_for_device", new_callable=AsyncMock) as mock_train:
            await service.train_device(device_id, weeks_lookback=4)
            mock_train.assert_awaited_once_with(device_id, "Dishwasher", 4)

    @pytest.mark.asyncio
    async def test_train_device_unknown_device_skips(self, service, mock_home_loads_repo, logger):
        mock_home_loads_repo.get_all.return_value = []
        unknown_id = EntityId(uuid.uuid4())

        with patch.object(service, "_train_for_device", new_callable=AsyncMock) as mock_train:
            await service.train_device(unknown_id)
            mock_train.assert_not_awaited()
            logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_train_device_finds_device_across_profiles(self, service, mock_home_loads_repo, device_id):
        device = LoadDevice(id=device_id, name="Target", enabled=True)
        profile1 = HomeLoadsProfile(name="Home 1", devices=[])
        profile2 = HomeLoadsProfile(name="Home 2", devices=[device])
        mock_home_loads_repo.get_all.return_value = [profile1, profile2]

        with patch.object(service, "_train_for_device", new_callable=AsyncMock) as mock_train:
            await service.train_device(device_id)
            mock_train.assert_awaited_once_with(device_id, "Target", 8)


class TestGetModels:
    def test_get_models_delegates_to_repo(self, service, mock_model_repo):
        expected = [
            LoadConsumptionModel(
                adapter_type=EnergyLoadForecastProviderAdapter.STATSMODELS,
                mae=1.0,
                is_active=True,
            )
        ]
        mock_model_repo.get_all.return_value = expected

        result = service.get_models()

        assert result == expected
        mock_model_repo.get_all.assert_called_once_with(None)

    def test_get_models_with_device_filter(self, service, mock_model_repo, device_id):
        mock_model_repo.get_all.return_value = []

        service.get_models(device_id=device_id)

        mock_model_repo.get_all.assert_called_once_with(device_id)
