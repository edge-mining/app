"""Unit tests for HomeLoadHistoryService.get_device_history."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from edge_mining.application.services.home_load_history_service import HomeLoadHistoryService
from edge_mining.domain.common import EntityId, Timestamp, Watts
from edge_mining.domain.home_load.value_objects import HomeLoadPowerPoint


@pytest.fixture
def mock_home_loads_repo():
    return MagicMock()


@pytest.fixture
def mock_history_repo():
    return MagicMock()


@pytest.fixture
def mock_adapter_service():
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
def service(mock_home_loads_repo, mock_history_repo, mock_adapter_service, logger):
    return HomeLoadHistoryService(
        home_loads_repo=mock_home_loads_repo,
        home_load_history_repo=mock_history_repo,
        adapter_service=mock_adapter_service,
        event_bus=None,
        logger=logger,
    )


class TestGetDeviceHistory:
    def test_returns_power_points_from_repo(self, service, mock_history_repo):
        device_id = EntityId(uuid.uuid4())
        now = datetime.now()
        start = Timestamp(now - timedelta(hours=24))
        end = Timestamp(now)

        expected_points = [
            HomeLoadPowerPoint(timestamp=Timestamp(now - timedelta(hours=2)), power=Watts(100.0)),
            HomeLoadPowerPoint(timestamp=Timestamp(now - timedelta(hours=1)), power=Watts(150.0)),
        ]
        mock_history_repo.get_power_points.return_value = expected_points

        result = service.get_device_history(device_id, start, end)

        assert result == expected_points
        mock_history_repo.get_power_points.assert_called_once_with(device_id, start, end)

    def test_returns_empty_list_when_no_data(self, service, mock_history_repo):
        device_id = EntityId(uuid.uuid4())
        now = datetime.now()
        start = Timestamp(now - timedelta(hours=24))
        end = Timestamp(now)

        mock_history_repo.get_power_points.return_value = []

        result = service.get_device_history(device_id, start, end)

        assert result == []
        mock_history_repo.get_power_points.assert_called_once_with(device_id, start, end)
