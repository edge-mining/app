"""Shared base class for mining performance trackers.

Provides per-method TTL caching and exponential backoff with jitter around
HTTP 429 rate-limit responses. Adapters declare their own ``TTL_MAP`` so that
polling frequency can be tuned to each pool's data freshness semantics.

On rate-limit events the base implements a *stale-while-error* strategy:
if a stale cached value exists for the requested key it is returned, otherwise
the underlying :class:`MiningPoolRateLimitedError` is re-raised.
"""

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, ClassVar, Dict, Optional, Tuple, TypeVar

from edge_mining.domain.performance.exceptions import MiningPoolRateLimitedError
from edge_mining.shared.logging.port import LoggerPort

T = TypeVar("T")

# Backoff schedule (seconds). Applied in order; after the last slot is consumed
# the rate-limit error is propagated to the caller.
_BACKOFF_SCHEDULE_SECONDS: Tuple[float, ...] = (5.0, 10.0, 20.0, 40.0, 80.0)

# Jitter is a multiplicative factor applied to each delay: uniform(0.8, 1.2).
_JITTER_FRACTION: float = 0.2


@dataclass
class _CacheEntry:
    """A cached value and the timestamp when it was stored (monotonic seconds)."""

    value: Any
    stored_at: float


class CachedRateLimitedTrackerBase:
    """Base class that wraps pool API calls with caching and backoff.

    Subclasses must set :attr:`TTL_MAP` to declare how long each logical method
    key's response can be cached. Keys are free-form strings chosen by the
    subclass (typically the port method name, e.g. ``"current_hashrate"``).

    A subclass that has not declared a key in :attr:`TTL_MAP` uses
    :attr:`DEFAULT_TTL_SECONDS` (``60`` by default).
    """

    TTL_MAP: ClassVar[Dict[str, int]] = {}
    DEFAULT_TTL_SECONDS: ClassVar[int] = 60

    def __init__(self, logger: Optional[LoggerPort] = None) -> None:
        self._cache: Dict[Tuple[str, Tuple[Any, ...]], _CacheEntry] = {}
        self._cache_logger = logger

    def _ttl_for(self, key: str) -> int:
        """Return the TTL (seconds) for a cache key, falling back to the default."""
        return self.TTL_MAP.get(key, self.DEFAULT_TTL_SECONDS)

    async def _cached_call(
        self,
        key: str,
        fetch: Callable[[], Awaitable[T]],
        args: Tuple[Any, ...] = (),
    ) -> T:
        """Run ``fetch`` with per-key TTL caching and 429 backoff.

        If a fresh cached value exists (inside TTL) it is returned without
        invoking the fetch. On :class:`MiningPoolRateLimitedError` a stale cache
        hit — if any — is returned as a fallback. All other exceptions are
        propagated unchanged.
        """
        cache_key = (key, args)
        now = time.monotonic()
        ttl = self._ttl_for(key)

        cached = self._cache.get(cache_key)
        if cached is not None and (now - cached.stored_at) < ttl:
            return cached.value  # type: ignore[no-any-return]

        try:
            value = await self._with_backoff(fetch)
        except MiningPoolRateLimitedError:
            if cached is not None:
                if self._cache_logger:
                    self._cache_logger.warning(
                        f"Rate-limited on '{key}': serving stale cached value " f"({int(now - cached.stored_at)}s old)."
                    )
                return cached.value  # type: ignore[no-any-return]
            raise

        self._cache[cache_key] = _CacheEntry(value=value, stored_at=time.monotonic())
        return value

    async def _with_backoff(self, fetch: Callable[[], Awaitable[T]]) -> T:
        """Retry ``fetch`` on 429 with 5/10/20/40/80s + jitter, max 5 attempts."""
        last_error: Optional[MiningPoolRateLimitedError] = None
        for attempt, base_delay in enumerate(_BACKOFF_SCHEDULE_SECONDS):
            try:
                return await fetch()
            except MiningPoolRateLimitedError as exc:
                last_error = exc
                delay = self._resolve_delay(exc, base_delay)
                if self._cache_logger:
                    self._cache_logger.warning(
                        f"Rate-limited by pool API (attempt {attempt + 1}/"
                        f"{len(_BACKOFF_SCHEDULE_SECONDS)}); retrying in {delay:.1f}s."
                    )
                await asyncio.sleep(delay)
        # All retries exhausted — propagate the last rate-limit error.
        raise last_error if last_error else MiningPoolRateLimitedError("Rate limit retries exhausted")

    @staticmethod
    def _resolve_delay(exc: MiningPoolRateLimitedError, base_delay: float) -> float:
        """Respect ``Retry-After`` hint if larger than the scheduled delay; always jitter."""
        delay = max(base_delay, exc.retry_after or 0.0)
        jitter = random.uniform(1.0 - _JITTER_FRACTION, 1.0 + _JITTER_FRACTION)
        return delay * jitter

    def _invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate either a single key (all argument combinations) or the whole cache."""
        if key is None:
            self._cache.clear()
            return
        to_delete = [k for k in self._cache if k[0] == key]
        for k in to_delete:
            del self._cache[k]
