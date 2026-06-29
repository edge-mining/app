"""Unit tests for home load API endpoints: device history, training trigger, models list."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from edge_mining.adapters.domain.home_load.fast_api.router import router
from edge_mining.adapters.infrastructure.api.setup import (
    get_config_service,
    get_home_load_history_service,
    get_load_forecast_training_service,
)
from edge_mining.domain.common import EntityId, Timestamp, Watts
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.entities import LoadConsumptionModel, LoadDevice
from edge_mining.domain.home_load.value_objects import HomeLoadPowerPoint, LoadTrainingResult


# --- Fixtures ---


@pytest.fixture
def device_id() -> EntityId:
    return EntityId(uuid.uuid4())


@pytest.fixture
def profile_id() -> EntityId:
    return EntityId(uuid.uuid4())


@pytest.fixture
def profile_with_device(profile_id, device_id) -> HomeLoadsProfile:
    device = LoadDevice(id=device_id, name="Dishwasher", enabled=True)
    return HomeLoadsProfile(id=profile_id, name="Test Home", devices=[device])


@pytest.fixture
def mock_config_service(profile_with_device):
    svc = MagicMock()
    svc.get_home_loads_profile.return_value = profile_with_device
    return svc


@pytest.fixture
def mock_history_service():
    return MagicMock()


@pytest.fixture
def mock_training_service():
    svc = AsyncMock()
    svc.get_models = MagicMock(return_value=[])
    return svc


@pytest.fixture
def client(mock_config_service, mock_history_service, mock_training_service):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    app.dependency_overrides[get_config_service] = lambda: mock_config_service
    app.dependency_overrides[get_home_load_history_service] = lambda: mock_history_service
    app.dependency_overrides[get_load_forecast_training_service] = lambda: mock_training_service

    return TestClient(app)


# --- Device History Endpoint Tests ---


class TestGetDeviceHistory:
    def test_returns_power_points(self, client, mock_history_service, profile_id, device_id):
        now = datetime.now()
        points = [
            HomeLoadPowerPoint(timestamp=Timestamp(now - timedelta(hours=1)), power=Watts(100.0)),
            HomeLoadPowerPoint(timestamp=Timestamp(now), power=Watts(200.0)),
        ]
        mock_history_service.get_device_history.return_value = points

        start = (now - timedelta(hours=2)).isoformat()
        end = now.isoformat()
        response = client.get(
            f"/api/v1/home-loads-profiles/{profile_id}/devices/{device_id}/history",
            params={"start": start, "end": end},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["power"] == 100.0
        assert data[1]["power"] == 200.0

    def test_returns_empty_list(self, client, mock_history_service, profile_id, device_id):
        mock_history_service.get_device_history.return_value = []
        now = datetime.now()

        response = client.get(
            f"/api/v1/home-loads-profiles/{profile_id}/devices/{device_id}/history",
            params={"start": (now - timedelta(hours=1)).isoformat(), "end": now.isoformat()},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_profile_not_found(self, client, mock_config_service):
        mock_config_service.get_home_loads_profile.return_value = None
        unknown_profile = uuid.uuid4()
        device = uuid.uuid4()
        now = datetime.now()

        response = client.get(
            f"/api/v1/home-loads-profiles/{unknown_profile}/devices/{device}/history",
            params={"start": (now - timedelta(hours=1)).isoformat(), "end": now.isoformat()},
        )

        assert response.status_code == 404

    def test_device_not_found(self, client, profile_id):
        unknown_device = uuid.uuid4()
        now = datetime.now()

        response = client.get(
            f"/api/v1/home-loads-profiles/{profile_id}/devices/{unknown_device}/history",
            params={"start": (now - timedelta(hours=1)).isoformat(), "end": now.isoformat()},
        )

        assert response.status_code == 404


# --- Training Trigger Endpoint Tests ---


class TestTriggerTrainingAll:
    def test_trigger_training_all_success(self, client, mock_training_service):
        mock_training_service.train_all = AsyncMock()

        response = client.post("/api/v1/training/trigger")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_trigger_training_all_with_weeks_lookback(self, client, mock_training_service):
        mock_training_service.train_all = AsyncMock()

        response = client.post("/api/v1/training/trigger", params={"weeks_lookback": 4})

        assert response.status_code == 200


class TestTriggerTrainingDevice:
    def test_trigger_device_training_success(self, client, mock_training_service, profile_id, device_id):
        mock_training_service.train_device = AsyncMock(
            return_value=LoadTrainingResult(
                device_name="Dishwasher",
                status="trained",
                best_adapter=EnergyLoadForecastProviderAdapter.XGBOOST,
                best_mae=42.0,
                samples_used=120,
            )
        )

        response = client.post(
            f"/api/v1/home-loads-profiles/{profile_id}/devices/{device_id}/training/trigger",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "trained"
        assert "Dishwasher" in data["detail"]

    def test_trigger_device_training_skipped_reports_reason(self, client, mock_training_service, profile_id, device_id):
        mock_training_service.train_device = AsyncMock(
            return_value=LoadTrainingResult(
                device_name="Dishwasher",
                status="skipped",
                reason="insufficient history (10 points, need at least 96)",
            )
        )

        response = client.post(
            f"/api/v1/home-loads-profiles/{profile_id}/devices/{device_id}/training/trigger",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "skipped"
        assert "insufficient history" in data["detail"]

    def test_trigger_device_training_profile_not_found(self, client, mock_config_service):
        mock_config_service.get_home_loads_profile.return_value = None
        unknown = uuid.uuid4()
        device = uuid.uuid4()

        response = client.post(
            f"/api/v1/home-loads-profiles/{unknown}/devices/{device}/training/trigger",
        )

        assert response.status_code == 404

    def test_trigger_device_training_device_not_found(self, client, profile_id):
        unknown_device = uuid.uuid4()

        response = client.post(
            f"/api/v1/home-loads-profiles/{profile_id}/devices/{unknown_device}/training/trigger",
        )

        assert response.status_code == 404


# --- Training Models List Endpoint Tests ---


class TestGetTrainingModels:
    def test_list_models_empty(self, client, mock_training_service):
        mock_training_service.get_models.return_value = []

        response = client.get("/api/v1/training/models")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_models_returns_data(self, client, mock_training_service, device_id):
        model = LoadConsumptionModel(
            device_id=device_id,
            adapter_type=EnergyLoadForecastProviderAdapter.STATSMODELS,
            trained_at=datetime.now(),
            mae=1.5,
            rmse=2.0,
            samples_used=100,
            is_active=True,
        )
        mock_training_service.get_models.return_value = [model]

        response = client.get("/api/v1/training/models")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["mae"] == 1.5
        assert data[0]["is_active"] is True
        assert data[0]["device_id"] == str(device_id)

    def test_list_models_filtered_by_device(self, client, mock_training_service, device_id):
        mock_training_service.get_models.return_value = []

        response = client.get("/api/v1/training/models", params={"device_id": str(device_id)})

        assert response.status_code == 200
        mock_training_service.get_models.assert_called_once()

    def test_list_models_invalid_device_id(self, client):
        response = client.get("/api/v1/training/models", params={"device_id": "not-a-uuid"})

        assert response.status_code == 400
