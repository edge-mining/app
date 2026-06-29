"""Unit tests for :class:`CachedRateLimitedTrackerBase`.

Exercises the cache+backoff plumbing shared by mining pool adapters:
per-key TTL caching, 429 retry schedule, stale-while-error fallback and
cache invalidation helpers.
"""

from typing import Any, Awaitable, Callable, ClassVar, Dict, List
from unittest.mock import patch

import pytest

from edge_mining.adapters.domain.performance.trackers._base import (
    CachedRateLimitedTrackerBase,
    _BACKOFF_SCHEDULE_SECONDS,
)
from edge_mining.domain.performance.exceptions import MiningPoolRateLimitedError


class _Tracker(CachedRateLimitedTrackerBase):
    """Concrete subclass used solely to exercise the base class."""

    TTL_MAP: ClassVar[Dict[str, int]] = {"short": 1, "long": 3600}
    DEFAULT_TTL_SECONDS: ClassVar[int] = 30


@pytest.fixture
def tracker() -> _Tracker:
    return _Tracker()


@pytest.fixture(autouse=True)
def _no_sleep():
    """Replace ``asyncio.sleep`` with an immediate no-op for all tests."""

    async def _fast_sleep(_delay: float) -> None:
        return None

    with patch(
        "edge_mining.adapters.domain.performance.trackers._base.asyncio.sleep",
        side_effect=_fast_sleep,
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def _deterministic_jitter():
    """Pin jitter to 1.0 so delay values are predictable."""
    with patch(
        "edge_mining.adapters.domain.performance.trackers._base.random.uniform",
        return_value=1.0,
    ) as mock:
        yield mock


def _counter_fetch(values: List[Any]) -> Callable[[], Awaitable[Any]]:
    """Return an async fetch that yields ``values`` in order, then raises ``StopIteration``."""
    iterator = iter(values)

    async def fetch() -> Any:
        try:
            item = next(iterator)
        except StopIteration as exc:
            raise AssertionError("fetch invoked more times than expected") from exc
        if isinstance(item, Exception):
            raise item
        return item

    return fetch


@pytest.mark.asyncio
async def test_cache_hit_within_ttl_does_not_refetch(tracker: _Tracker) -> None:
    fetch = _counter_fetch([42])
    first = await tracker._cached_call("long", fetch)
    # The fetch iterator only has one value — a second hit proves we served from cache.
    second = await tracker._cached_call("long", fetch)
    assert first == second == 42


@pytest.mark.asyncio
async def test_cache_miss_after_ttl_refetches(tracker: _Tracker) -> None:
    t = [1000.0]

    def now() -> float:
        return t[0]

    with patch(
        "edge_mining.adapters.domain.performance.trackers._base.time.monotonic",
        side_effect=now,
    ):
        fetch = _counter_fetch([1, 2])
        first = await tracker._cached_call("short", fetch)
        assert first == 1
        # Advance time past the 1s TTL → entry is stale, fetch runs again.
        t[0] += 5.0
        second = await tracker._cached_call("short", fetch)
        assert second == 2


@pytest.mark.asyncio
async def test_default_ttl_applies_when_key_not_mapped(tracker: _Tracker) -> None:
    assert tracker._ttl_for("unknown") == _Tracker.DEFAULT_TTL_SECONDS


@pytest.mark.asyncio
async def test_args_distinguish_cache_keys(tracker: _Tracker) -> None:
    async def fetch_10() -> int:
        return 10

    async def fetch_20() -> int:
        return 20

    a = await tracker._cached_call("long", fetch_10, args=(10,))
    b = await tracker._cached_call("long", fetch_20, args=(20,))
    # Same logical key, different args → distinct cache entries.
    assert a == 10 and b == 20


@pytest.mark.asyncio
async def test_with_backoff_retries_exactly_schedule_length(tracker: _Tracker, _no_sleep) -> None:
    fetch = _counter_fetch([MiningPoolRateLimitedError("429")] * len(_BACKOFF_SCHEDULE_SECONDS))

    with pytest.raises(MiningPoolRateLimitedError):
        await tracker._with_backoff(fetch)

    # One sleep per attempt: 5 attempts → 5 sleeps.
    assert _no_sleep.call_count == len(_BACKOFF_SCHEDULE_SECONDS)


@pytest.mark.asyncio
async def test_with_backoff_applies_scheduled_delays(tracker: _Tracker, _no_sleep) -> None:
    fetch = _counter_fetch([MiningPoolRateLimitedError()] * len(_BACKOFF_SCHEDULE_SECONDS))
    with pytest.raises(MiningPoolRateLimitedError):
        await tracker._with_backoff(fetch)

    observed_delays = [call.args[0] for call in _no_sleep.call_args_list]
    assert observed_delays == list(_BACKOFF_SCHEDULE_SECONDS)


@pytest.mark.asyncio
async def test_with_backoff_succeeds_on_later_attempt(tracker: _Tracker, _no_sleep) -> None:
    fetch = _counter_fetch([MiningPoolRateLimitedError(), MiningPoolRateLimitedError(), "ok"])
    result = await tracker._with_backoff(fetch)
    assert result == "ok"
    # Two failed attempts → two sleeps before the success.
    assert _no_sleep.call_count == 2


def test_resolve_delay_honors_retry_after_when_larger() -> None:
    exc = MiningPoolRateLimitedError("x", retry_after=60.0)
    # Jitter is pinned to 1.0 by the autouse fixture.
    assert _Tracker._resolve_delay(exc, base_delay=5.0) == pytest.approx(60.0)


def test_resolve_delay_ignores_retry_after_when_smaller() -> None:
    exc = MiningPoolRateLimitedError("x", retry_after=1.0)
    assert _Tracker._resolve_delay(exc, base_delay=20.0) == pytest.approx(20.0)


def test_resolve_delay_without_retry_after() -> None:
    exc = MiningPoolRateLimitedError("x")
    assert _Tracker._resolve_delay(exc, base_delay=10.0) == pytest.approx(10.0)


@pytest.mark.asyncio
async def test_stale_while_error_serves_cached_value_on_rate_limit(
    tracker: _Tracker,
) -> None:
    t = [1000.0]

    def now() -> float:
        return t[0]

    with patch(
        "edge_mining.adapters.domain.performance.trackers._base.time.monotonic",
        side_effect=now,
    ):
        # First call: populate the cache with a known value.
        fetch_ok = _counter_fetch(["fresh"])
        assert await tracker._cached_call("short", fetch_ok) == "fresh"

        # Advance past TTL so the next call attempts a re-fetch.
        t[0] += 10.0

        # All retries raise 429 → the stale value should be returned.
        fetch_429 = _counter_fetch([MiningPoolRateLimitedError()] * len(_BACKOFF_SCHEDULE_SECONDS))
        result = await tracker._cached_call("short", fetch_429)
        assert result == "fresh"


@pytest.mark.asyncio
async def test_rate_limit_reraises_when_no_cached_value(tracker: _Tracker) -> None:
    fetch = _counter_fetch([MiningPoolRateLimitedError("hard fail")] * len(_BACKOFF_SCHEDULE_SECONDS))
    with pytest.raises(MiningPoolRateLimitedError):
        await tracker._cached_call("short", fetch)


@pytest.mark.asyncio
async def test_non_rate_limit_error_propagates(tracker: _Tracker) -> None:
    class Boom(RuntimeError):
        pass

    async def fetch() -> int:
        raise Boom("kaboom")

    with pytest.raises(Boom):
        await tracker._cached_call("short", fetch)


@pytest.mark.asyncio
async def test_invalidate_cache_single_key(tracker: _Tracker) -> None:
    await tracker._cached_call("long", _counter_fetch([1]))
    await tracker._cached_call("short", _counter_fetch([2]))
    tracker._invalidate_cache("long")
    # "short" survives — a second hit still serves cached value.
    assert await tracker._cached_call("short", _counter_fetch([999])) == 2
    # "long" is gone — fetch runs again.
    assert await tracker._cached_call("long", _counter_fetch([42])) == 42


@pytest.mark.asyncio
async def test_invalidate_cache_clears_all(tracker: _Tracker) -> None:
    await tracker._cached_call("long", _counter_fetch([1]))
    await tracker._cached_call("short", _counter_fetch([2]))
    tracker._invalidate_cache()
    # Both keys had to refetch.
    assert await tracker._cached_call("long", _counter_fetch([10])) == 10
    assert await tracker._cached_call("short", _counter_fetch([20])) == 20
