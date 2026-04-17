"""
Braiins Pool adapter (Implementation of Port) that fetches mining performance
data from the Braiins Pool REST API.

Reference: https://pool.braiins.com
Authentication is done via the `Pool-Auth-Token` header carrying a token the user
generates in `Settings > Access Profiles`. All responses are wrapped in a
`{"btc": { ... }}` envelope.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from edge_mining.domain.common import EntityId, Timestamp
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.performance.common import PayoutFrequency, Satoshi
from edge_mining.domain.performance.exceptions import (
    MiningPerformanceTrackerConfigurationError,
    MiningPoolAuthError,
    MiningPoolResponseError,
    MiningPoolUnreachableError,
)
from edge_mining.domain.performance.ports import MiningPerformanceTrackerPort
from edge_mining.domain.performance.value_objects import (
    MiningReward,
    PayoutSchedule,
    PoolStats,
    PoolWorkerStats,
)
from edge_mining.shared.adapter_configs.performance import (
    MiningPerformanceTrackerBraiinsPoolConfig,
)
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import (
    MiningPerformanceTrackerAdapterFactory,
)
from edge_mining.shared.logging.port import LoggerPort

# 1 BTC = 100_000_000 satoshis
_SATS_PER_BTC = 100_000_000

# Multipliers to convert a hash rate value from the unit advertised by Braiins into TH/s.
_UNIT_TO_THS: Dict[str, float] = {
    "h/s": 1e-12,
    "kh/s": 1e-9,
    "mh/s": 1e-6,
    "gh/s": 1e-3,
    "th/s": 1.0,
    "ph/s": 1e3,
    "eh/s": 1e6,
}


def _hashrate_from_value(value: Any, unit: Optional[str]) -> Optional[HashRate]:
    """Convert a Braiins hash rate value (given its unit) into a HashRate in TH/s."""
    if value is None:
        return None
    try:
        raw = float(value)
    except (TypeError, ValueError):
        return None
    factor = _UNIT_TO_THS.get((unit or "gh/s").strip().lower(), _UNIT_TO_THS["gh/s"])
    return HashRate(value=raw * factor, unit="TH/s")


def _btc_string_to_sats(value: Any) -> Optional[Satoshi]:
    """Convert a decimal BTC value (typically a string) into Satoshis."""
    if value is None:
        return None
    try:
        btc = float(value)
    except (TypeError, ValueError):
        return None
    return Satoshi(int(round(btc * _SATS_PER_BTC)))


def _parse_timestamp(value: Any) -> Optional[Timestamp]:
    """Parse a UNIX seconds or ISO 8601 timestamp into a Timestamp."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return Timestamp(datetime.fromtimestamp(float(value), tz=timezone.utc))
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            return Timestamp(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            try:
                return Timestamp(datetime.fromtimestamp(float(value), tz=timezone.utc))
            except (TypeError, ValueError, OverflowError, OSError):
                return None
    return None


class BraiinsPoolMiningPerformanceTracker(MiningPerformanceTrackerPort):
    """Adapter that talks to the Braiins Pool REST API."""

    def __init__(
        self,
        config: MiningPerformanceTrackerBraiinsPoolConfig,
        logger: Optional[LoggerPort] = None,
    ):
        self._config = config
        self._logger = logger

    async def _get(self, path: str) -> Dict[str, Any]:
        """
        Perform an authenticated GET against the Braiins Pool API and unwrap the
        `{"btc": {...}}` envelope. Raises domain exceptions on transport errors.
        """
        import aiohttp

        url = f"{self._config.api_base_url.rstrip('/')}{path}"
        headers = {"Pool-Auth-Token": self._config.api_token}
        timeout = aiohttp.ClientTimeout(total=self._config.request_timeout_seconds)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status in (401, 403):
                        raise MiningPoolAuthError(f"Braiins Pool rejected credentials ({response.status}) for {path}")
                    if response.status >= 500:
                        raise MiningPoolUnreachableError(f"Braiins Pool returned status {response.status} for {path}")
                    try:
                        payload = await response.json(content_type=None)
                    except Exception as exc:  # noqa: BLE001 - intentionally broad
                        raise MiningPoolResponseError(f"Braiins Pool returned non-JSON body for {path}: {exc}") from exc

                    if response.status >= 400:
                        raise MiningPoolResponseError(f"Braiins Pool HTTP {response.status} for {path}: {payload}")
        except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
            raise MiningPoolUnreachableError(f"Braiins Pool unreachable ({path}): {exc}") from exc

        if not isinstance(payload, dict):
            raise MiningPoolResponseError(f"Braiins Pool returned unexpected payload for {path}: {payload!r}")

        data = payload.get("btc", payload)
        if not isinstance(data, dict):
            raise MiningPoolResponseError(f"Braiins Pool returned unexpected btc-envelope for {path}: {data!r}")
        return data

    async def get_current_hashrate(self, miner_ids: List[EntityId]) -> Optional[HashRate]:
        """Return the current account hashrate from `/accounts/profile/json/btc`."""
        try:
            data = await self._get("/accounts/profile/json/btc")
        except (MiningPoolUnreachableError, MiningPoolAuthError) as exc:
            if self._logger:
                self._logger.warning(f"Braiins: cannot fetch current hashrate: {exc}")
            return None

        unit = data.get("hash_rate_unit")
        raw = data.get("hash_rate_5m") or data.get("hash_rate_1h") or data.get("hash_rate_24h")
        return _hashrate_from_value(raw, unit)

    async def get_recent_rewards(self, miner_id: Optional[EntityId] = None, limit: int = 10) -> List[MiningReward]:
        """Return recent daily rewards from `/accounts/rewards/json/btc`."""
        try:
            data = await self._get("/accounts/rewards/json/btc")
        except (MiningPoolUnreachableError, MiningPoolAuthError) as exc:
            if self._logger:
                self._logger.warning(f"Braiins: cannot fetch recent rewards: {exc}")
            return []

        entries = data.get("daily_rewards") or data.get("rewards") or []
        if not isinstance(entries, list):
            return []

        rewards: List[MiningReward] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            amount = _btc_string_to_sats(entry.get("total_reward") or entry.get("reward"))
            if amount is None:
                continue
            ts = _parse_timestamp(entry.get("date") or entry.get("timestamp"))
            rewards.append(MiningReward(amount=amount, timestamp=ts) if ts is not None else MiningReward(amount=amount))

        rewards.sort(key=lambda r: r.timestamp, reverse=True)
        return rewards[:limit]

    async def get_pool_stats(self) -> Optional[PoolStats]:
        """Combine `/accounts/profile/json/btc` and `/accounts/workers/json/btc` into PoolStats."""
        try:
            profile = await self._get("/accounts/profile/json/btc")
        except (MiningPoolUnreachableError, MiningPoolAuthError) as exc:
            if self._logger:
                self._logger.warning(f"Braiins: cannot fetch profile: {exc}")
            return None

        try:
            workers_payload = await self._get("/accounts/workers/json/btc")
        except (MiningPoolUnreachableError, MiningPoolAuthError) as exc:
            if self._logger:
                self._logger.warning(f"Braiins: cannot fetch workers: {exc}")
            workers_payload = {}

        unit = profile.get("hash_rate_unit")
        workers = self._parse_workers(workers_payload.get("workers"), unit)

        return PoolStats(
            current_hashrate=_hashrate_from_value(profile.get("hash_rate_5m"), unit),
            average_hashrate_24h=_hashrate_from_value(profile.get("hash_rate_24h"), unit),
            average_hashrate_7d=_hashrate_from_value(profile.get("hash_rate_7d"), unit),
            unpaid_balance=_btc_string_to_sats(profile.get("unconfirmed_reward")),
            estimated_next_payout=_btc_string_to_sats(profile.get("estimated_reward")),
            workers=workers,
        )

    async def get_worker_stats(self, miner_ids: List[EntityId]) -> List[PoolWorkerStats]:
        """Fetch per-worker statistics from `/accounts/workers/json/btc`."""
        try:
            data = await self._get("/accounts/workers/json/btc")
        except (MiningPoolUnreachableError, MiningPoolAuthError) as exc:
            if self._logger:
                self._logger.warning(f"Braiins: cannot fetch worker stats: {exc}")
            return []

        unit = data.get("hash_rate_unit")
        return self._parse_workers(data.get("workers"), unit)

    async def get_payout_schedule(self) -> Optional[PayoutSchedule]:
        """Return the payout policy derived from the profile (threshold-based)."""
        try:
            profile = await self._get("/accounts/profile/json/btc")
        except (MiningPoolUnreachableError, MiningPoolAuthError) as exc:
            if self._logger:
                self._logger.warning(f"Braiins: cannot fetch payout schedule: {exc}")
            return PayoutSchedule(frequency=PayoutFrequency.THRESHOLD)

        return PayoutSchedule(
            frequency=PayoutFrequency.THRESHOLD,
            threshold=_btc_string_to_sats(profile.get("payout_threshold")),
        )

    @staticmethod
    def _parse_workers(raw_workers: Any, unit: Optional[str]) -> List[PoolWorkerStats]:
        """Parse workers from either a list or a dict keyed by worker name."""
        items: List[tuple] = []
        if isinstance(raw_workers, list):
            items = [(None, w) for w in raw_workers]
        elif isinstance(raw_workers, dict):
            items = list(raw_workers.items())
        else:
            return []

        workers: List[PoolWorkerStats] = []
        for key, worker in items:
            if not isinstance(worker, dict):
                continue
            name = worker.get("worker_name") or worker.get("name") or key
            if not name:
                continue
            workers.append(
                PoolWorkerStats(
                    worker_name=str(name),
                    hashrate=_hashrate_from_value(
                        worker.get("hash_rate_5m") or worker.get("hash_rate"),
                        worker.get("hash_rate_unit") or unit,
                    ),
                    last_share_at=_parse_timestamp(worker.get("last_share") or worker.get("last_share_at")),
                    valid_shares=_safe_int(worker.get("valid_shares")),
                    stale_shares=_safe_int(worker.get("stale_shares")),
                    rejected_shares=_safe_int(worker.get("rejected_shares")),
                )
            )
        return workers


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class BraiinsPoolMiningPerformanceTrackerFactory(MiningPerformanceTrackerAdapterFactory):
    """Factory for the Braiins Pool mining performance tracker adapter."""

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> MiningPerformanceTrackerPort:
        if not isinstance(config, MiningPerformanceTrackerBraiinsPoolConfig):
            raise MiningPerformanceTrackerConfigurationError(
                "Invalid configuration type for Braiins Pool mining performance tracker. "
                "Expected MiningPerformanceTrackerBraiinsPoolConfig."
            )
        if not config.api_token or not config.api_token.strip():
            raise MiningPerformanceTrackerConfigurationError(
                "Braiins Pool mining performance tracker requires a non-empty api_token."
            )
        return BraiinsPoolMiningPerformanceTracker(config=config, logger=logger)
