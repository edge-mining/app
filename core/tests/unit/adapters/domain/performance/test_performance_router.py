"""Endpoint tests for the mining performance tracker API router."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from edge_mining.adapters.domain.performance.fast_api.router import router
from edge_mining.adapters.infrastructure.api.setup import (
    get_adapter_service,
    get_config_service,
)
from edge_mining.domain.common import EntityId
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.performance.common import (
    MiningPerformanceTrackerAdapter,
    PayoutFrequency,
    Satoshi,
)
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.exceptions import (
    MiningPerformanceTrackerNotFoundError,
    MiningPoolAuthError,
    MiningPoolUnreachableError,
)
from edge_mining.domain.performance.value_objects import (
    MiningReward,
    PayoutSchedule,
    PoolStats,
    PoolWorkerStats,
)
from edge_mining.shared.adapter_configs.performance import (
    MiningPerformanceTrackerBraiinsPoolConfig,
    MiningPerformanceTrackerDummyConfig,
    MiningPerformanceTrackerOceanConfig,
)


def _make_client(
    *,
    config_service: MagicMock,
    adapter_service: MagicMock,
) -> TestClient:
    """Build a FastAPI TestClient with the tracker router and DI overrides."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_config_service] = lambda: config_service
    app.dependency_overrides[get_adapter_service] = lambda: adapter_service
    return TestClient(app)


@pytest.fixture
def config_service() -> MagicMock:
    """Provide a mocked ConfigurationServiceInterface."""
    return MagicMock()


@pytest.fixture
def adapter_service() -> MagicMock:
    """Provide a mocked AdapterServiceInterface."""
    return MagicMock()


@pytest.fixture
def client(config_service: MagicMock, adapter_service: MagicMock) -> TestClient:
    """Provide a TestClient wired to the mocked services."""
    return _make_client(config_service=config_service, adapter_service=adapter_service)


@pytest.fixture
def dummy_tracker() -> MiningPerformanceTracker:
    """Build a dummy tracker entity usable across tests."""
    return MiningPerformanceTracker(
        id=EntityId(uuid.uuid4()),
        name="Dummy",
        adapter_type=MiningPerformanceTrackerAdapter.DUMMY,
        config=MiningPerformanceTrackerDummyConfig(message="hello"),
        external_service_id=None,
    )


# -- List ---------------------------------------------------------------------


def test_list_returns_all_trackers(client: TestClient, config_service: MagicMock, dummy_tracker) -> None:
    """GET /mining-performance-trackers returns the list of configured trackers."""
    config_service.list_mining_performance_trackers.return_value = [dummy_tracker]

    response = client.get("/api/v1/mining-performance-trackers")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(dummy_tracker.id)
    assert body[0]["adapter_type"] == MiningPerformanceTrackerAdapter.DUMMY.value


# -- Types / config-schema / external-services --------------------------------


def test_types_lists_all_adapter_types(client: TestClient) -> None:
    """GET /mining-performance-trackers/types enumerates known adapters."""
    response = client.get("/api/v1/mining-performance-trackers/types")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {a.value for a in MiningPerformanceTrackerAdapter}


def test_config_schema_returns_json_schema(client: TestClient, config_service: MagicMock) -> None:
    """GET .../types/{adapter}/config-schema returns the Pydantic JSON schema."""
    config_service.get_mining_performance_tracker_config_by_type.return_value = MiningPerformanceTrackerOceanConfig

    response = client.get(
        f"/api/v1/mining-performance-trackers/types/{MiningPerformanceTrackerAdapter.OCEAN.value}/config-schema"
    )

    assert response.status_code == 200
    schema = response.json()
    assert "properties" in schema
    assert "bitcoin_address" in schema["properties"]


def test_config_schema_unknown_type_returns_500(client: TestClient, config_service: MagicMock) -> None:
    """If no config class is registered for an adapter type, the endpoint returns 500."""
    config_service.get_mining_performance_tracker_config_by_type.return_value = None

    response = client.get(
        f"/api/v1/mining-performance-trackers/types/{MiningPerformanceTrackerAdapter.DUMMY.value}/config-schema"
    )
    assert response.status_code == 500


def test_external_services_returns_adapter_or_none(client: TestClient, config_service: MagicMock) -> None:
    """GET .../types/{adapter}/external-services returns the compatible external service (None here)."""
    config_service.get_mining_performance_tracker_external_service_adapter.return_value = None

    response = client.get(
        f"/api/v1/mining-performance-trackers/types/{MiningPerformanceTrackerAdapter.DUMMY.value}/external-services"
    )
    assert response.status_code == 200
    assert response.json() is None


# -- Detail -------------------------------------------------------------------


def test_get_details_returns_tracker(client: TestClient, config_service: MagicMock, dummy_tracker) -> None:
    """GET /mining-performance-trackers/{id} returns tracker details."""
    config_service.get_mining_performance_tracker.return_value = dummy_tracker

    response = client.get(f"/api/v1/mining-performance-trackers/{dummy_tracker.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(dummy_tracker.id)


def test_get_details_missing_returns_404(client: TestClient, config_service: MagicMock) -> None:
    """GET /mining-performance-trackers/{id} returns 404 when the tracker is missing."""
    config_service.get_mining_performance_tracker.return_value = None

    tracker_id = uuid.uuid4()
    response = client.get(f"/api/v1/mining-performance-trackers/{tracker_id}")
    assert response.status_code == 404


# -- Create -------------------------------------------------------------------


def test_create_tracker_accepts_dummy_config(client: TestClient, config_service: MagicMock, dummy_tracker) -> None:
    """POST /mining-performance-trackers creates a tracker and returns its schema."""
    config_service.add_mining_performance_tracker = AsyncMock(return_value=dummy_tracker)

    payload = {
        "name": "dummy-1",
        "adapter_type": MiningPerformanceTrackerAdapter.DUMMY.value,
        "config": {"message": "hi"},
        "external_service_id": None,
    }

    response = client.post("/api/v1/mining-performance-trackers", json=payload)

    assert response.status_code == 200
    config_service.add_mining_performance_tracker.assert_awaited_once()
    assert response.json()["id"] == str(dummy_tracker.id)


def test_create_tracker_rejects_missing_config(client: TestClient) -> None:
    """POST /mining-performance-trackers rejects a payload without configuration."""
    payload = {
        "name": "dummy-1",
        "adapter_type": MiningPerformanceTrackerAdapter.DUMMY.value,
        "config": None,
        "external_service_id": None,
    }
    response = client.post("/api/v1/mining-performance-trackers", json=payload)
    assert response.status_code == 400


def test_create_tracker_rejects_invalid_adapter_type(client: TestClient) -> None:
    """POST /mining-performance-trackers rejects an unknown adapter type."""
    payload = {
        "name": "bogus",
        "adapter_type": "not-a-real-adapter",
        "config": {"message": "hi"},
    }
    response = client.post("/api/v1/mining-performance-trackers", json=payload)
    assert response.status_code == 422


# -- Update -------------------------------------------------------------------


def test_update_tracker_persists_new_config(client: TestClient, config_service: MagicMock, dummy_tracker) -> None:
    """PUT /mining-performance-trackers/{id} updates a tracker's configuration."""
    config_service.get_mining_performance_tracker.return_value = dummy_tracker
    config_service.get_mining_performance_tracker_config_by_type.return_value = MiningPerformanceTrackerDummyConfig
    updated = MiningPerformanceTracker(
        id=dummy_tracker.id,
        name="renamed",
        adapter_type=MiningPerformanceTrackerAdapter.DUMMY,
        config=MiningPerformanceTrackerDummyConfig(message="updated"),
    )
    config_service.update_mining_performance_tracker = AsyncMock(return_value=updated)

    response = client.put(
        f"/api/v1/mining-performance-trackers/{dummy_tracker.id}",
        json={"name": "renamed", "config": {"message": "updated"}},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "renamed"
    config_service.update_mining_performance_tracker.assert_awaited_once()


def test_update_missing_tracker_returns_404(client: TestClient, config_service: MagicMock) -> None:
    """PUT /mining-performance-trackers/{id} returns 404 when the tracker is missing."""
    config_service.get_mining_performance_tracker.return_value = None

    response = client.put(
        f"/api/v1/mining-performance-trackers/{uuid.uuid4()}",
        json={"name": "renamed"},
    )
    assert response.status_code == 404


# -- Remove -------------------------------------------------------------------


def test_remove_tracker_returns_deleted_schema(client: TestClient, config_service: MagicMock, dummy_tracker) -> None:
    """DELETE /mining-performance-trackers/{id} returns the removed tracker."""
    config_service.remove_mining_performance_tracker = AsyncMock(return_value=dummy_tracker)

    response = client.delete(f"/api/v1/mining-performance-trackers/{dummy_tracker.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(dummy_tracker.id)


def test_remove_missing_tracker_returns_404(client: TestClient, config_service: MagicMock) -> None:
    """DELETE returns 404 when the tracker cannot be found."""
    config_service.remove_mining_performance_tracker = AsyncMock(
        side_effect=MiningPerformanceTrackerNotFoundError("missing")
    )

    response = client.delete(f"/api/v1/mining-performance-trackers/{uuid.uuid4()}")
    assert response.status_code == 404


# -- Test / stats / workers / rewards / payout-schedule -----------------------


class _FakeTrackerPort:
    """Minimal fake tracker port for adapter_service overrides."""

    def __init__(
        self,
        *,
        hashrate_payload: Optional[HashRate] = None,
        stats: Optional[PoolStats] = None,
        workers: Optional[List[PoolWorkerStats]] = None,
        rewards: Optional[List[MiningReward]] = None,
        payout_schedule: Optional[PayoutSchedule] = None,
        raises: Optional[Exception] = None,
    ) -> None:
        self._hashrate = hashrate_payload
        self._stats = stats
        self._workers = workers or []
        self._rewards = rewards or []
        self._schedule = payout_schedule
        self._raises = raises

    async def get_current_hashrate(self, miner_ids):  # noqa: D401
        """Return the canned hashrate."""
        if self._raises:
            raise self._raises
        return self._hashrate

    async def get_pool_stats(self):  # noqa: D401
        """Return the canned pool stats."""
        if self._raises:
            raise self._raises
        return self._stats

    async def get_worker_stats(self, miner_ids):  # noqa: D401
        """Return the canned workers list."""
        if self._raises:
            raise self._raises
        return self._workers

    async def get_recent_rewards(self, miner_id=None, limit=10):  # noqa: D401
        """Return the canned rewards list (respecting limit)."""
        if self._raises:
            raise self._raises
        return self._rewards[:limit]

    async def get_payout_schedule(self):  # noqa: D401
        """Return the canned payout schedule."""
        if self._raises:
            raise self._raises
        return self._schedule


def test_test_tracker_reports_success(client: TestClient, adapter_service: MagicMock) -> None:
    """POST /{id}/test returns success when the tracker is reachable."""
    adapter_service.get_mining_performance_tracker = AsyncMock(
        return_value=_FakeTrackerPort(payout_schedule=PayoutSchedule(frequency=PayoutFrequency.DAILY))
    )
    response = client.post(f"/api/v1/mining-performance-trackers/{uuid.uuid4()}/test")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_test_tracker_maps_auth_error_to_401(client: TestClient, adapter_service: MagicMock) -> None:
    """POST /{id}/test maps MiningPoolAuthError to HTTP 401."""
    adapter_service.get_mining_performance_tracker = AsyncMock(
        return_value=_FakeTrackerPort(raises=MiningPoolAuthError("bad token"))
    )
    response = client.post(f"/api/v1/mining-performance-trackers/{uuid.uuid4()}/test")
    assert response.status_code == 401


def test_test_tracker_maps_unreachable_to_503(client: TestClient, adapter_service: MagicMock) -> None:
    """POST /{id}/test maps MiningPoolUnreachableError to HTTP 503."""
    adapter_service.get_mining_performance_tracker = AsyncMock(
        return_value=_FakeTrackerPort(raises=MiningPoolUnreachableError("timeout"))
    )
    response = client.post(f"/api/v1/mining-performance-trackers/{uuid.uuid4()}/test")
    assert response.status_code == 503


def test_test_tracker_unknown_returns_404(client: TestClient, adapter_service: MagicMock) -> None:
    """POST /{id}/test returns 404 when no tracker port is available."""
    adapter_service.get_mining_performance_tracker = AsyncMock(return_value=None)
    response = client.post(f"/api/v1/mining-performance-trackers/{uuid.uuid4()}/test")
    assert response.status_code == 404


def test_stats_endpoint_returns_pool_stats(client: TestClient, adapter_service: MagicMock) -> None:
    """GET /{id}/stats returns the serialized pool statistics."""
    stats = PoolStats(
        current_hashrate=HashRate(value=12.5, unit="TH/s"),
        average_hashrate_24h=HashRate(value=11.0, unit="TH/s"),
        unpaid_balance=Satoshi(42_000),
        estimated_next_payout=Satoshi(10_000),
        workers=[
            PoolWorkerStats(
                worker_name="rig1",
                hashrate=HashRate(value=6.0, unit="TH/s"),
                valid_shares=100,
            )
        ],
    )
    adapter_service.get_mining_performance_tracker = AsyncMock(return_value=_FakeTrackerPort(stats=stats))

    response = client.get(f"/api/v1/mining-performance-trackers/{uuid.uuid4()}/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["current_hashrate"]["value"] == 12.5
    assert body["unpaid_balance"] == 42_000
    assert len(body["workers"]) == 1
    assert body["workers"][0]["worker_name"] == "rig1"


def test_stats_endpoint_when_port_returns_none(client: TestClient, adapter_service: MagicMock) -> None:
    """GET /{id}/stats maps a None pool response to HTTP 502."""
    adapter_service.get_mining_performance_tracker = AsyncMock(return_value=_FakeTrackerPort(stats=None))
    response = client.get(f"/api/v1/mining-performance-trackers/{uuid.uuid4()}/stats")
    assert response.status_code == 502


def test_workers_endpoint_returns_worker_stats(client: TestClient, adapter_service: MagicMock) -> None:
    """GET /{id}/workers returns the list of worker statistics."""
    workers = [
        PoolWorkerStats(worker_name="w1", valid_shares=10),
        PoolWorkerStats(worker_name="w2", valid_shares=20),
    ]
    adapter_service.get_mining_performance_tracker = AsyncMock(return_value=_FakeTrackerPort(workers=workers))
    response = client.get(f"/api/v1/mining-performance-trackers/{uuid.uuid4()}/workers")
    assert response.status_code == 200
    body = response.json()
    assert [w["worker_name"] for w in body] == ["w1", "w2"]


def test_rewards_endpoint_respects_limit(client: TestClient, adapter_service: MagicMock) -> None:
    """GET /{id}/rewards returns rewards honoring the limit query parameter."""
    now = datetime.now(timezone.utc)
    rewards = [MiningReward(amount=Satoshi(i * 1000), timestamp=now) for i in range(1, 6)]
    adapter_service.get_mining_performance_tracker = AsyncMock(return_value=_FakeTrackerPort(rewards=rewards))

    response = client.get(
        f"/api/v1/mining-performance-trackers/{uuid.uuid4()}/rewards",
        params={"limit": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert body[0]["amount"] == 1000


def test_payout_schedule_endpoint_returns_schema(client: TestClient, adapter_service: MagicMock) -> None:
    """GET /{id}/payout-schedule returns the payout schedule schema."""
    schedule = PayoutSchedule(frequency=PayoutFrequency.THRESHOLD, threshold=Satoshi(100_000))
    adapter_service.get_mining_performance_tracker = AsyncMock(return_value=_FakeTrackerPort(payout_schedule=schedule))
    response = client.get(f"/api/v1/mining-performance-trackers/{uuid.uuid4()}/payout-schedule")
    assert response.status_code == 200
    body = response.json()
    assert body["frequency"] == PayoutFrequency.THRESHOLD.value
    assert body["threshold"] == 100_000


# -- Schema round-trip --------------------------------------------------------


def test_ocean_config_schema_json_schema_surface() -> None:
    """Ocean config schema exposes required/optional fields via model_json_schema()."""
    from edge_mining.adapters.domain.performance.schemas import (
        OceanMiningPerformanceTrackerConfigSchema,
    )

    schema = OceanMiningPerformanceTrackerConfigSchema.model_json_schema()
    assert "bitcoin_address" in schema["properties"]
    assert "api_base_url" in schema["properties"]
    assert "bitcoin_address" in schema["required"]


def test_braiins_config_schema_json_schema_surface() -> None:
    """Braiins config schema exposes required/optional fields via model_json_schema()."""
    from edge_mining.adapters.domain.performance.schemas import (
        BraiinsPoolMiningPerformanceTrackerConfigSchema,
    )

    schema = BraiinsPoolMiningPerformanceTrackerConfigSchema.model_json_schema()
    assert "api_token" in schema["properties"]
    assert "api_token" in schema["required"]


def test_tracker_schema_from_model_roundtrip() -> None:
    """MiningPerformanceTrackerSchema round-trips through from_model/to_model."""
    from edge_mining.adapters.domain.performance.schemas import (
        MiningPerformanceTrackerSchema,
    )

    tracker = MiningPerformanceTracker(
        id=EntityId(uuid.uuid4()),
        name="ocean",
        adapter_type=MiningPerformanceTrackerAdapter.OCEAN,
        config=MiningPerformanceTrackerOceanConfig(bitcoin_address="bc1qtest"),
    )
    schema = MiningPerformanceTrackerSchema.from_model(tracker)
    rebuilt = schema.to_model()
    assert rebuilt.id == tracker.id
    assert rebuilt.adapter_type == tracker.adapter_type
    assert isinstance(rebuilt.config, MiningPerformanceTrackerOceanConfig)
    assert rebuilt.config.bitcoin_address == "bc1qtest"


def test_braiins_tracker_schema_roundtrip() -> None:
    """Round-trip the Braiins tracker schema through from_model/to_model."""
    from edge_mining.adapters.domain.performance.schemas import (
        MiningPerformanceTrackerSchema,
    )

    tracker = MiningPerformanceTracker(
        id=EntityId(uuid.uuid4()),
        name="braiins",
        adapter_type=MiningPerformanceTrackerAdapter.BRAIINS_POOL,
        config=MiningPerformanceTrackerBraiinsPoolConfig(api_token="tok"),
    )
    schema = MiningPerformanceTrackerSchema.from_model(tracker)
    rebuilt = schema.to_model()
    assert isinstance(rebuilt.config, MiningPerformanceTrackerBraiinsPoolConfig)
    assert rebuilt.config.api_token == "tok"
