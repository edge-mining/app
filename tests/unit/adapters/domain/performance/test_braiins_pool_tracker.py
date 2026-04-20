"""Unit tests for the Braiins Pool mining performance tracker adapter."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from edge_mining.adapters.domain.performance.trackers.braiins_pool import (
    BraiinsPoolMiningPerformanceTracker,
    BraiinsPoolMiningPerformanceTrackerFactory,
)
from edge_mining.domain.common import EntityId
from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.domain.performance.exceptions import (
    MiningPerformanceTrackerConfigurationError,
    MiningPoolAuthError,
    MiningPoolRateLimitedError,
    MiningPoolResponseError,
    MiningPoolUnreachableError,
)
from edge_mining.shared.adapter_configs.performance import (
    MiningPerformanceTrackerBraiinsPoolConfig,
)


@pytest.fixture
def config() -> MiningPerformanceTrackerBraiinsPoolConfig:
    return MiningPerformanceTrackerBraiinsPoolConfig(
        api_token="test-token",
        api_base_url="https://pool.braiins.com",
        request_timeout_seconds=5,
    )


@pytest.fixture
def tracker(config) -> BraiinsPoolMiningPerformanceTracker:
    return BraiinsPoolMiningPerformanceTracker(config=config)


def _patched_get(tracker: BraiinsPoolMiningPerformanceTracker, mapping: Dict[str, Any]):
    async def fake_get(path: str) -> Dict[str, Any]:
        if path not in mapping:
            raise AssertionError(f"Unexpected path requested by adapter: {path}")
        value = mapping[path]
        if isinstance(value, Exception):
            raise value
        return value

    return patch.object(tracker, "_get", side_effect=fake_get)


@pytest.mark.asyncio
async def test_get_current_hashrate_converts_ghs_to_ths(tracker: BraiinsPoolMiningPerformanceTracker):
    payload = {"hash_rate_5m": 150_000.0, "hash_rate_unit": "Gh/s"}  # 150_000 Gh/s = 150 TH/s
    with _patched_get(tracker, {"/accounts/profile/json/btc": payload}):
        result = await tracker.get_current_hashrate(miner_ids=[])

    assert result is not None
    assert result.unit == "TH/s"
    assert result.value == pytest.approx(150.0, rel=1e-6)


@pytest.mark.asyncio
async def test_get_current_hashrate_defaults_unit_to_ghs(tracker: BraiinsPoolMiningPerformanceTracker):
    payload = {"hash_rate_5m": 1000.0}  # no unit → default to Gh/s → 1.0 TH/s
    with _patched_get(tracker, {"/accounts/profile/json/btc": payload}):
        result = await tracker.get_current_hashrate(miner_ids=[])
    assert result is not None
    assert result.value == pytest.approx(1.0, rel=1e-6)


@pytest.mark.asyncio
async def test_get_current_hashrate_returns_none_on_auth_error(tracker: BraiinsPoolMiningPerformanceTracker):
    with _patched_get(tracker, {"/accounts/profile/json/btc": MiningPoolAuthError("bad token")}):
        result = await tracker.get_current_hashrate(miner_ids=[])
    assert result is None


@pytest.mark.asyncio
async def test_get_worker_stats_parses_dict_style_workers(tracker: BraiinsPoolMiningPerformanceTracker):
    payload = {
        "hash_rate_unit": "Gh/s",
        "workers": {
            "rig01": {"hash_rate_5m": 50_000.0, "last_share": 1_700_000_000, "state": "OK"},
            "rig02": {"hash_rate_5m": 25_000.0, "last_share": 1_699_999_000},
        },
    }
    with _patched_get(tracker, {"/accounts/workers/json/btc": payload}):
        workers = await tracker.get_worker_stats(miner_ids=[])

    assert len(workers) == 2
    by_name = {w.worker_name: w for w in workers}
    assert by_name["rig01"].hashrate is not None
    assert by_name["rig01"].hashrate.value == pytest.approx(50.0, rel=1e-6)
    assert by_name["rig01"].last_share_at is not None
    assert by_name["rig02"].hashrate is not None
    assert by_name["rig02"].hashrate.value == pytest.approx(25.0, rel=1e-6)


@pytest.mark.asyncio
async def test_get_worker_stats_parses_list_style_workers(tracker: BraiinsPoolMiningPerformanceTracker):
    payload = {
        "hash_rate_unit": "Gh/s",
        "workers": [
            {"worker_name": "rig01", "hash_rate_5m": 10_000.0},
            {"worker_name": "rig02", "hash_rate_5m": 5_000.0},
        ],
    }
    with _patched_get(tracker, {"/accounts/workers/json/btc": payload}):
        workers = await tracker.get_worker_stats(miner_ids=[])

    assert len(workers) == 2
    assert {w.worker_name for w in workers} == {"rig01", "rig02"}


@pytest.mark.asyncio
async def test_get_pool_stats_merges_profile_and_workers(tracker: BraiinsPoolMiningPerformanceTracker):
    profile = {
        "hash_rate_unit": "Gh/s",
        "hash_rate_5m": 100_000.0,
        "hash_rate_24h": 90_000.0,
        "hash_rate_7d": 80_000.0,
        "unconfirmed_reward": "0.00012345",
        "estimated_reward": "0.00023456",
    }
    workers_payload = {
        "hash_rate_unit": "Gh/s",
        "workers": [{"worker_name": "rig01", "hash_rate_5m": 100_000.0}],
    }
    with _patched_get(
        tracker,
        {
            "/accounts/profile/json/btc": profile,
            "/accounts/workers/json/btc": workers_payload,
        },
    ):
        stats = await tracker.get_pool_stats()

    assert stats is not None
    assert stats.current_hashrate is not None
    assert stats.current_hashrate.value == pytest.approx(100.0, rel=1e-6)
    assert stats.average_hashrate_24h is not None
    assert stats.average_hashrate_24h.value == pytest.approx(90.0, rel=1e-6)
    assert stats.unpaid_balance == 12345
    assert stats.estimated_next_payout == 23456
    assert len(stats.workers) == 1
    assert stats.workers[0].worker_name == "rig01"


@pytest.mark.asyncio
async def test_get_pool_stats_returns_none_when_profile_unreachable(tracker):
    with _patched_get(
        tracker,
        {"/accounts/profile/json/btc": MiningPoolUnreachableError("nope")},
    ):
        stats = await tracker.get_pool_stats()
    assert stats is None


@pytest.mark.asyncio
async def test_get_recent_rewards_converts_btc_string_to_sats(tracker: BraiinsPoolMiningPerformanceTracker):
    payload = {
        "daily_rewards": [
            {"date": "2026-01-10", "total_reward": "0.00010000"},
            {"date": "2026-01-11", "total_reward": "0.00020000"},
            {"date": "2026-01-12", "total_reward": "0.00030000"},
        ]
    }
    with _patched_get(tracker, {"/accounts/rewards/json/btc": payload}):
        rewards = await tracker.get_recent_rewards(miner_id=EntityId("any"), limit=2)

    assert len(rewards) == 2
    # Sorted descending, so 30000 sat then 20000 sat
    assert rewards[0].amount == 30_000
    assert rewards[1].amount == 20_000


@pytest.mark.asyncio
async def test_get_recent_rewards_returns_empty_on_auth_error(tracker):
    with _patched_get(tracker, {"/accounts/rewards/json/btc": MiningPoolAuthError("nope")}):
        rewards = await tracker.get_recent_rewards()
    assert rewards == []


@pytest.mark.asyncio
async def test_get_payout_schedule_includes_threshold(tracker: BraiinsPoolMiningPerformanceTracker):
    profile = {"payout_threshold": "0.01"}
    with _patched_get(tracker, {"/accounts/profile/json/btc": profile}):
        schedule = await tracker.get_payout_schedule()
    assert schedule is not None
    assert schedule.frequency.value == "threshold"
    assert schedule.threshold == 1_000_000


@pytest.mark.asyncio
async def test_get_payout_schedule_fallback_on_error(tracker):
    with _patched_get(tracker, {"/accounts/profile/json/btc": MiningPoolUnreachableError("nope")}):
        schedule = await tracker.get_payout_schedule()
    assert schedule is not None
    assert schedule.frequency.value == "threshold"
    assert schedule.threshold is None


# --- HTTP-level error mapping --------------------------------------------------


class _FakeResponse:
    def __init__(
        self,
        status: int,
        payload: Any = None,
        raise_json: Exception = None,
        headers: dict = None,
    ):
        self.status = status
        self._payload = payload
        self._raise_json = raise_json
        self.headers = headers or {}

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
        self.seen_headers: List[dict] = []

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, url: str, headers: dict = None):
        if headers is not None:
            self.seen_headers.append(dict(headers))
        if self._on_get is not None:
            raise self._on_get
        return self._response


@pytest.mark.asyncio
async def test_http_401_raises_auth_error(tracker: BraiinsPoolMiningPerformanceTracker):
    fake_response = _FakeResponse(status=401, payload={"error": "unauthorized"})

    def _session_factory(*_args, **_kwargs):
        return _FakeSession(response=fake_response)

    with patch("aiohttp.ClientSession", _session_factory):
        with pytest.raises(MiningPoolAuthError):
            await tracker._get("/accounts/profile/json/btc")


@pytest.mark.asyncio
async def test_http_5xx_raises_unreachable(tracker: BraiinsPoolMiningPerformanceTracker):
    fake_response = _FakeResponse(status=503, payload={})

    def _session_factory(*_args, **_kwargs):
        return _FakeSession(response=fake_response)

    with patch("aiohttp.ClientSession", _session_factory):
        with pytest.raises(MiningPoolUnreachableError):
            await tracker._get("/accounts/profile/json/btc")


@pytest.mark.asyncio
async def test_http_timeout_raises_unreachable(tracker: BraiinsPoolMiningPerformanceTracker):
    import asyncio

    def _session_factory(*_args, **_kwargs):
        return _FakeSession(on_get=asyncio.TimeoutError())

    with patch("aiohttp.ClientSession", _session_factory):
        with pytest.raises(MiningPoolUnreachableError):
            await tracker._get("/accounts/profile/json/btc")


@pytest.mark.asyncio
async def test_http_429_raises_rate_limited_with_retry_after(
    tracker: BraiinsPoolMiningPerformanceTracker,
):
    fake_response = _FakeResponse(status=429, payload={}, headers={"Retry-After": "15"})

    def _session_factory(*_args, **_kwargs):
        return _FakeSession(response=fake_response)

    with patch("aiohttp.ClientSession", _session_factory):
        with pytest.raises(MiningPoolRateLimitedError) as exc_info:
            await tracker._get("/accounts/profile/json/btc")

    assert exc_info.value.retry_after == pytest.approx(15.0)


@pytest.mark.asyncio
async def test_http_429_takes_priority_over_auth_even_when_authenticated(
    tracker: BraiinsPoolMiningPerformanceTracker,
):
    # An authenticated endpoint can still be throttled; 429 must win over 401/403 mapping.
    fake_response = _FakeResponse(status=429, payload={}, headers={})

    def _session_factory(*_args, **_kwargs):
        return _FakeSession(response=fake_response)

    with patch("aiohttp.ClientSession", _session_factory):
        with pytest.raises(MiningPoolRateLimitedError):
            await tracker._get("/accounts/profile/json/btc")


@pytest.mark.asyncio
async def test_http_unwraps_btc_envelope(tracker: BraiinsPoolMiningPerformanceTracker):
    fake_response = _FakeResponse(status=200, payload={"btc": {"hash_rate_5m": 42.0}})

    def _session_factory(*_args, **_kwargs):
        return _FakeSession(response=fake_response)

    with patch("aiohttp.ClientSession", _session_factory):
        result = await tracker._get("/accounts/profile/json/btc")
    assert result == {"hash_rate_5m": 42.0}


@pytest.mark.asyncio
async def test_http_sends_auth_header(tracker: BraiinsPoolMiningPerformanceTracker):
    fake_response = _FakeResponse(status=200, payload={"btc": {}})
    sessions: List[_FakeSession] = []

    def _session_factory(*_args, **_kwargs):
        session = _FakeSession(response=fake_response)
        sessions.append(session)
        return session

    with patch("aiohttp.ClientSession", _session_factory):
        await tracker._get("/accounts/profile/json/btc")

    assert sessions, "Session was not created"
    assert sessions[0].seen_headers, "No headers were sent"
    assert sessions[0].seen_headers[0].get("Pool-Auth-Token") == "test-token"


# --- Factory ------------------------------------------------------------------


def test_factory_rejects_wrong_config_type():
    factory = BraiinsPoolMiningPerformanceTrackerFactory()
    with pytest.raises(MiningPerformanceTrackerConfigurationError):
        factory.create(config=None, logger=None, external_service=None)


def test_factory_rejects_empty_token():
    factory = BraiinsPoolMiningPerformanceTrackerFactory()
    bad_config = MiningPerformanceTrackerBraiinsPoolConfig(api_token="  ")
    with pytest.raises(MiningPerformanceTrackerConfigurationError):
        factory.create(config=bad_config, logger=None, external_service=None)


def test_factory_returns_braiins_adapter(config):
    factory = BraiinsPoolMiningPerformanceTrackerFactory()
    adapter = factory.create(config=config, logger=None, external_service=None)
    assert isinstance(adapter, BraiinsPoolMiningPerformanceTracker)


def test_config_is_valid_for_braiins_adapter_type(config):
    assert config.is_valid(MiningPerformanceTrackerAdapter.BRAIINS_POOL) is True
    assert config.is_valid(MiningPerformanceTrackerAdapter.OCEAN) is False


def test_config_invalid_when_token_empty():
    bad = MiningPerformanceTrackerBraiinsPoolConfig(api_token="")
    assert bad.is_valid(MiningPerformanceTrackerAdapter.BRAIINS_POOL) is False


def test_config_round_trip():
    original = MiningPerformanceTrackerBraiinsPoolConfig(
        api_token="abc",
        api_base_url="https://example.test",
        request_timeout_seconds=7,
    )
    restored = MiningPerformanceTrackerBraiinsPoolConfig.from_dict(original.to_dict())
    assert restored == original


# --- Parsing helpers ----------------------------------------------------------


def test_btc_string_to_sats_handles_floats_and_strings():
    from edge_mining.adapters.domain.performance.trackers.braiins_pool import _btc_string_to_sats

    assert _btc_string_to_sats("0.00000001") == 1
    assert _btc_string_to_sats(0.5) == 50_000_000
    assert _btc_string_to_sats(None) is None
    assert _btc_string_to_sats("not-a-number") is None


def test_parse_timestamp_handles_unix_and_iso():
    from edge_mining.adapters.domain.performance.trackers.braiins_pool import _parse_timestamp

    assert _parse_timestamp(1_700_000_000) == datetime(2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc)
    assert _parse_timestamp("2023-11-14T22:13:20+00:00") == datetime(
        2023, 11, 14, 22, 13, 20, tzinfo=timezone.utc
    )
    assert _parse_timestamp(None) is None


def test_hashrate_unit_mapping_handles_all_units():
    from edge_mining.adapters.domain.performance.trackers.braiins_pool import _hashrate_from_value

    assert _hashrate_from_value(1, "H/s").value == pytest.approx(1e-12)
    assert _hashrate_from_value(1, "Gh/s").value == pytest.approx(1e-3)
    assert _hashrate_from_value(1, "TH/s").value == pytest.approx(1.0)
    assert _hashrate_from_value(1, "Ph/s").value == pytest.approx(1e3)
    assert _hashrate_from_value(None, "Gh/s") is None


@pytest.mark.asyncio
async def test_response_body_not_json_raises_response_error(tracker: BraiinsPoolMiningPerformanceTracker):
    fake_response = _FakeResponse(status=200, raise_json=ValueError("not json"))

    def _session_factory(*_args, **_kwargs):
        return _FakeSession(response=fake_response)

    with patch("aiohttp.ClientSession", _session_factory):
        with pytest.raises(MiningPoolResponseError):
            await tracker._get("/accounts/profile/json/btc")
