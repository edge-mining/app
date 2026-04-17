"""Unit tests for the Ocean.xyz mining performance tracker adapter."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from edge_mining.adapters.domain.performance.trackers.ocean import (
    OceanMiningPerformanceTracker,
    OceanMiningPerformanceTrackerFactory,
)
from edge_mining.domain.common import EntityId
from edge_mining.domain.performance.exceptions import (
    MiningPerformanceTrackerConfigurationError,
    MiningPoolResponseError,
    MiningPoolUnreachableError,
)
from edge_mining.shared.adapter_configs.performance import (
    MiningPerformanceTrackerOceanConfig,
)


@pytest.fixture
def config() -> MiningPerformanceTrackerOceanConfig:
    return MiningPerformanceTrackerOceanConfig(
        bitcoin_address="bc1qexampleexampleexampleexampleexampleexample",
        api_base_url="https://api.ocean.xyz",
        request_timeout_seconds=5,
    )


@pytest.fixture
def tracker(config) -> OceanMiningPerformanceTracker:
    return OceanMiningPerformanceTracker(config=config)


def _patched_get(tracker: OceanMiningPerformanceTracker, mapping: Dict[str, Any]):
    """Patch tracker._get to return canned payloads keyed by path."""

    async def fake_get(path: str) -> Dict[str, Any]:
        if path not in mapping:
            raise AssertionError(f"Unexpected path requested by adapter: {path}")
        value = mapping[path]
        if isinstance(value, Exception):
            raise value
        return value

    return patch.object(tracker, "_get", side_effect=fake_get)


@pytest.mark.asyncio
async def test_get_current_hashrate_returns_ths_from_hs(tracker: OceanMiningPerformanceTracker):
    payload = {"hashrate_300s": 1.5e14}  # 150 TH/s in H/s
    with _patched_get(
        tracker,
        {f"/v1/user_hashrate/{tracker._config.bitcoin_address}": payload},
    ):
        result = await tracker.get_current_hashrate(miner_ids=[])

    assert result is not None
    assert result.unit == "TH/s"
    assert result.value == pytest.approx(150.0, rel=1e-6)


@pytest.mark.asyncio
async def test_get_current_hashrate_returns_none_on_unreachable(tracker: OceanMiningPerformanceTracker):
    with _patched_get(
        tracker,
        {f"/v1/user_hashrate/{tracker._config.bitcoin_address}": MiningPoolUnreachableError("boom")},
    ):
        result = await tracker.get_current_hashrate(miner_ids=[])
    assert result is None


@pytest.mark.asyncio
async def test_get_worker_stats_parses_workers(tracker: OceanMiningPerformanceTracker):
    payload = {
        "workers": [
            {
                "name": "rig01",
                "hashrate_300s": 5e13,
                "last_share": 1_700_000_000,
                "valid_shares": 42,
                "stale_shares": 1,
                "rejected_shares": 0,
            },
            {"name": "rig02", "hashrate": "2.5e13"},
        ]
    }
    with _patched_get(
        tracker,
        {f"/v1/user_hashrate_full/{tracker._config.bitcoin_address}": payload},
    ):
        workers = await tracker.get_worker_stats(miner_ids=[])

    assert len(workers) == 2
    assert workers[0].worker_name == "rig01"
    assert workers[0].hashrate is not None
    assert workers[0].hashrate.value == pytest.approx(50.0, rel=1e-6)
    assert workers[0].valid_shares == 42
    assert workers[0].last_share_at is not None
    assert workers[0].last_share_at.tzinfo is not None
    assert workers[1].worker_name == "rig02"
    assert workers[1].hashrate is not None
    assert workers[1].hashrate.value == pytest.approx(25.0, rel=1e-6)


@pytest.mark.asyncio
async def test_get_pool_stats_combines_summary_and_workers(tracker: OceanMiningPerformanceTracker):
    summary = {
        "hashrate_300s": 1e14,
        "hashrate_24h": 9e13,
        "hashrate_7d": 8e13,
        "unpaid_balance_sat": 12345,
    }
    full = {"workers": [{"name": "rig01", "hashrate_300s": 1e14}]}
    addr = tracker._config.bitcoin_address
    with _patched_get(
        tracker,
        {
            f"/v1/user_hashrate/{addr}": summary,
            f"/v1/user_hashrate_full/{addr}": full,
        },
    ):
        stats = await tracker.get_pool_stats()

    assert stats is not None
    assert stats.current_hashrate is not None
    assert stats.current_hashrate.value == pytest.approx(100.0, rel=1e-6)
    assert stats.average_hashrate_24h is not None
    assert stats.average_hashrate_24h.value == pytest.approx(90.0, rel=1e-6)
    assert stats.average_hashrate_7d is not None
    assert stats.average_hashrate_7d.value == pytest.approx(80.0, rel=1e-6)
    assert stats.unpaid_balance == 12345
    assert len(stats.workers) == 1
    assert stats.workers[0].worker_name == "rig01"


@pytest.mark.asyncio
async def test_get_pool_stats_returns_none_when_summary_unreachable(tracker: OceanMiningPerformanceTracker):
    addr = tracker._config.bitcoin_address
    with _patched_get(
        tracker,
        {f"/v1/user_hashrate/{addr}": MiningPoolUnreachableError("nope")},
    ):
        stats = await tracker.get_pool_stats()
    assert stats is None


@pytest.mark.asyncio
async def test_get_recent_rewards_sorted_and_limited(tracker: OceanMiningPerformanceTracker):
    addr = tracker._config.bitcoin_address
    payload = {
        "earnings": [
            {"amount_sat": 100, "timestamp": 1_700_000_000},
            {"amount_sat": 200, "timestamp": 1_700_000_500},
            {"amount_sat": 300, "timestamp": 1_700_001_000},
        ]
    }

    captured_paths: List[str] = []

    async def fake_get(path: str) -> Dict[str, Any]:
        captured_paths.append(path)
        return payload

    with patch.object(tracker, "_get", side_effect=fake_get):
        rewards = await tracker.get_recent_rewards(miner_id=EntityId("any"), limit=2)

    assert len(captured_paths) == 1
    assert captured_paths[0].startswith(f"/v1/earnpay/{addr}/")
    assert len(rewards) == 2
    # Sorted by timestamp descending (most recent first)
    assert rewards[0].amount == 300
    assert rewards[1].amount == 200


@pytest.mark.asyncio
async def test_get_recent_rewards_returns_empty_on_unreachable(tracker: OceanMiningPerformanceTracker):
    async def fake_get(path: str) -> Dict[str, Any]:
        raise MiningPoolUnreachableError("net down")

    with patch.object(tracker, "_get", side_effect=fake_get):
        rewards = await tracker.get_recent_rewards()
    assert rewards == []


@pytest.mark.asyncio
async def test_get_payout_schedule_is_threshold(tracker: OceanMiningPerformanceTracker):
    schedule = await tracker.get_payout_schedule()
    assert schedule is not None
    assert schedule.frequency.value == "threshold"


# --- HTTP-level error mapping --------------------------------------------------


class _FakeResponse:
    def __init__(self, status: int, payload: Any = None, raise_json: Exception = None):
        self.status = status
        self._payload = payload
        self._raise_json = raise_json

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def json(self, content_type=None):
        if self._raise_json is not None:
            raise self._raise_json
        return self._payload


class _FakeSession:
    def __init__(self, response: _FakeResponse = None, on_get: Exception = None):
        self._response = response
        self._on_get = on_get

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str):
        if self._on_get is not None:
            raise self._on_get
        return self._response


@pytest.mark.asyncio
async def test_http_5xx_raises_unreachable(tracker: OceanMiningPerformanceTracker):
    fake_response = _FakeResponse(status=503, payload={})

    def _session_factory(*_args, **_kwargs):
        return _FakeSession(response=fake_response)

    with patch("aiohttp.ClientSession", _session_factory):
        with pytest.raises(MiningPoolUnreachableError):
            await tracker._get("/v1/user_hashrate/whatever")


@pytest.mark.asyncio
async def test_http_error_envelope_raises_response_error(tracker: OceanMiningPerformanceTracker):
    fake_response = _FakeResponse(status=200, payload={"error": "address not found"})

    def _session_factory(*_args, **_kwargs):
        return _FakeSession(response=fake_response)

    with patch("aiohttp.ClientSession", _session_factory):
        with pytest.raises(MiningPoolResponseError):
            await tracker._get("/v1/user_hashrate/whatever")


@pytest.mark.asyncio
async def test_http_timeout_raises_unreachable(tracker: OceanMiningPerformanceTracker):
    import asyncio

    def _session_factory(*_args, **_kwargs):
        return _FakeSession(on_get=asyncio.TimeoutError())

    with patch("aiohttp.ClientSession", _session_factory):
        with pytest.raises(MiningPoolUnreachableError):
            await tracker._get("/v1/user_hashrate/whatever")


# --- Factory ------------------------------------------------------------------


def test_factory_rejects_wrong_config_type():
    factory = OceanMiningPerformanceTrackerFactory()
    with pytest.raises(MiningPerformanceTrackerConfigurationError):
        factory.create(config=None, logger=None, external_service=None)


def test_factory_rejects_empty_address():
    factory = OceanMiningPerformanceTrackerFactory()
    bad_config = MiningPerformanceTrackerOceanConfig(bitcoin_address="   ")
    with pytest.raises(MiningPerformanceTrackerConfigurationError):
        factory.create(config=bad_config, logger=None, external_service=None)


def test_factory_returns_ocean_adapter(config):
    factory = OceanMiningPerformanceTrackerFactory()
    adapter = factory.create(config=config, logger=None, external_service=None)
    assert isinstance(adapter, OceanMiningPerformanceTracker)


def test_config_is_valid_for_ocean_adapter_type(config):
    from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter

    assert config.is_valid(MiningPerformanceTrackerAdapter.OCEAN) is True
    assert config.is_valid(MiningPerformanceTrackerAdapter.DUMMY) is False


def test_config_invalid_when_address_empty():
    from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter

    bad = MiningPerformanceTrackerOceanConfig(bitcoin_address="")
    assert bad.is_valid(MiningPerformanceTrackerAdapter.OCEAN) is False


def test_config_round_trip():
    original = MiningPerformanceTrackerOceanConfig(
        bitcoin_address="bc1qabc",
        api_base_url="https://example.test",
        request_timeout_seconds=7,
    )
    restored = MiningPerformanceTrackerOceanConfig.from_dict(original.to_dict())
    assert restored == original


# Sanity check: parsing helpers used internally.
def test_parse_timestamp_handles_unix_seconds():
    from edge_mining.adapters.domain.performance.trackers.ocean import _parse_timestamp

    ts = _parse_timestamp(1_700_000_000)
    assert ts is not None
    assert ts == datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)


def test_hashrate_from_hs_handles_string_value():
    from edge_mining.adapters.domain.performance.trackers.ocean import _hashrate_from_hs

    hr = _hashrate_from_hs("1.0e14")
    assert hr is not None
    assert hr.value == pytest.approx(100.0, rel=1e-6)
    assert hr.unit == "TH/s"
