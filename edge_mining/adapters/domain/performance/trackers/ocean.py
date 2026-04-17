"""
Ocean.xyz adapter (Implementation of Port) that fetches mining performance
data from the Ocean pool public REST API.

Reference: https://api.ocean.xyz
The pool identifies users by their payout Bitcoin address; no API token is
required to read public per-user statistics.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from edge_mining.domain.common import EntityId, Timestamp
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.performance.common import PayoutFrequency, Satoshi
from edge_mining.domain.performance.exceptions import (
    MiningPerformanceTrackerConfigurationError,
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
    MiningPerformanceTrackerOceanConfig,
)
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import (
    MiningPerformanceTrackerAdapterFactory,
)
from edge_mining.shared.logging.port import LoggerPort

# Conversion factor: Ocean returns hashrate in H/s, the domain uses TH/s.
_HS_TO_THS = 1e-12


def _hashrate_from_hs(value: Any) -> Optional[HashRate]:
    """Convert a raw H/s value (possibly as a string) into a HashRate in TH/s."""
    if value is None:
        return None
    try:
        hs = float(value)
    except (TypeError, ValueError):
        return None
    return HashRate(value=hs * _HS_TO_THS, unit="TH/s")


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


class OceanMiningPerformanceTracker(MiningPerformanceTrackerPort):
    """Adapter that talks to the Ocean.xyz public REST API."""

    def __init__(
        self,
        config: MiningPerformanceTrackerOceanConfig,
        logger: Optional[LoggerPort] = None,
    ):
        self._config = config
        self._logger = logger

    async def _get(self, path: str) -> Dict[str, Any]:
        """
        Perform an HTTP GET against the Ocean API and unwrap the `result`
        envelope. Raises domain exceptions on transport or response errors.
        """
        import aiohttp

        url = f"{self._config.api_base_url.rstrip('/')}{path}"
        timeout = aiohttp.ClientTimeout(total=self._config.request_timeout_seconds)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status >= 500:
                        raise MiningPoolUnreachableError(f"Ocean API returned status {response.status} for {path}")
                    try:
                        payload = await response.json(content_type=None)
                    except Exception as exc:  # noqa: BLE001 - intentionally broad
                        raise MiningPoolResponseError(f"Ocean API returned non-JSON body for {path}: {exc}") from exc

                    if response.status >= 400:
                        raise MiningPoolResponseError(f"Ocean API HTTP {response.status} for {path}: {payload}")
        except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
            raise MiningPoolUnreachableError(f"Ocean API unreachable ({path}): {exc}") from exc

        if not isinstance(payload, dict):
            raise MiningPoolResponseError(f"Ocean API returned unexpected payload for {path}: {payload!r}")

        if "error" in payload and payload.get("error"):
            raise MiningPoolResponseError(f"Ocean API error for {path}: {payload['error']}")

        result = payload.get("result", payload)
        if not isinstance(result, dict):
            return {"_raw": result}
        return result

    async def get_current_hashrate(self, miner_ids: List[EntityId]) -> Optional[HashRate]:
        """Return the current account-level hashrate from `/v1/user_hashrate/{btc}`."""
        try:
            data = await self._get(f"/v1/user_hashrate/{self._config.bitcoin_address}")
        except MiningPoolUnreachableError as exc:
            if self._logger:
                self._logger.warning(f"Ocean: cannot fetch current hashrate: {exc}")
            return None

        raw = data.get("hashrate_300s") or data.get("hashrate_60s") or data.get("hashrate_1h")
        return _hashrate_from_hs(raw)

    async def get_recent_rewards(self, miner_id: Optional[EntityId] = None, limit: int = 10) -> List[MiningReward]:
        """Return recent earnings derived from `/v1/earnpay/{btc}/{from_ts}`."""
        # Use a reasonable look-back window proportional to the requested limit
        # (Ocean pays out roughly per block for active miners — ~30 days is wide enough).
        from_ts = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())
        try:
            data = await self._get(f"/v1/earnpay/{self._config.bitcoin_address}/{from_ts}")
        except MiningPoolUnreachableError as exc:
            if self._logger:
                self._logger.warning(f"Ocean: cannot fetch recent rewards: {exc}")
            return []

        entries = data.get("earnings") or data.get("payouts") or data.get("_raw") or []
        if not isinstance(entries, list):
            return []

        rewards: List[MiningReward] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            amount_raw = entry.get("amount_sat") or entry.get("satoshi") or entry.get("amount")
            try:
                amount = Satoshi(int(amount_raw)) if amount_raw is not None else None
            except (TypeError, ValueError):
                amount = None
            if amount is None:
                continue
            ts = _parse_timestamp(entry.get("timestamp") or entry.get("ts") or entry.get("time"))
            rewards.append(MiningReward(amount=amount, timestamp=ts) if ts is not None else MiningReward(amount=amount))

        rewards.sort(key=lambda r: r.timestamp, reverse=True)
        return rewards[:limit]

    async def get_pool_stats(self) -> Optional[PoolStats]:
        """Combine `/v1/user_hashrate` and `/v1/user_hashrate_full` into a PoolStats VO."""
        try:
            summary = await self._get(f"/v1/user_hashrate/{self._config.bitcoin_address}")
        except MiningPoolUnreachableError as exc:
            if self._logger:
                self._logger.warning(f"Ocean: cannot fetch pool stats summary: {exc}")
            return None

        try:
            full = await self._get(f"/v1/user_hashrate_full/{self._config.bitcoin_address}")
        except MiningPoolUnreachableError as exc:
            if self._logger:
                self._logger.warning(f"Ocean: cannot fetch pool worker details: {exc}")
            full = {}

        workers_raw = full.get("workers") if isinstance(full, dict) else None
        workers: List[PoolWorkerStats] = []
        if isinstance(workers_raw, list):
            workers = [w for w in (self._build_worker_stats(w) for w in workers_raw) if w is not None]

        unpaid = summary.get("unpaid_balance_sat") or summary.get("unpaid_balance")
        try:
            unpaid_sats = Satoshi(int(unpaid)) if unpaid is not None else None
        except (TypeError, ValueError):
            unpaid_sats = None

        return PoolStats(
            current_hashrate=_hashrate_from_hs(summary.get("hashrate_300s")),
            average_hashrate_24h=_hashrate_from_hs(summary.get("hashrate_24h") or summary.get("hashrate_1d")),
            average_hashrate_7d=_hashrate_from_hs(summary.get("hashrate_7d")),
            unpaid_balance=unpaid_sats,
            estimated_next_payout=None,
            workers=workers,
        )

    async def get_worker_stats(self, miner_ids: List[EntityId]) -> List[PoolWorkerStats]:
        """Fetch per-worker statistics from `/v1/user_hashrate_full/{btc}`."""
        try:
            data = await self._get(f"/v1/user_hashrate_full/{self._config.bitcoin_address}")
        except MiningPoolUnreachableError as exc:
            if self._logger:
                self._logger.warning(f"Ocean: cannot fetch worker stats: {exc}")
            return []

        workers_raw = data.get("workers")
        if not isinstance(workers_raw, list):
            return []

        return [w for w in (self._build_worker_stats(w) for w in workers_raw) if w is not None]

    async def get_payout_schedule(self) -> Optional[PayoutSchedule]:
        """Ocean pays out per block when a payout threshold is reached."""
        return PayoutSchedule(frequency=PayoutFrequency.THRESHOLD)

    @staticmethod
    def _build_worker_stats(worker: Any) -> Optional[PoolWorkerStats]:
        if not isinstance(worker, dict):
            return None
        name = worker.get("name") or worker.get("worker_name") or worker.get("worker")
        if not name:
            return None
        return PoolWorkerStats(
            worker_name=str(name),
            hashrate=_hashrate_from_hs(worker.get("hashrate_300s") or worker.get("hashrate")),
            last_share_at=_parse_timestamp(worker.get("last_share") or worker.get("last_share_at")),
            valid_shares=_safe_int(worker.get("valid_shares")),
            stale_shares=_safe_int(worker.get("stale_shares")),
            rejected_shares=_safe_int(worker.get("rejected_shares")),
        )


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class OceanMiningPerformanceTrackerFactory(MiningPerformanceTrackerAdapterFactory):
    """Factory for the Ocean.xyz mining performance tracker adapter."""

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> MiningPerformanceTrackerPort:
        if not isinstance(config, MiningPerformanceTrackerOceanConfig):
            raise MiningPerformanceTrackerConfigurationError(
                "Invalid configuration type for Ocean mining performance tracker. "
                "Expected MiningPerformanceTrackerOceanConfig."
            )
        if not config.bitcoin_address or not config.bitcoin_address.strip():
            raise MiningPerformanceTrackerConfigurationError(
                "Ocean mining performance tracker requires a non-empty bitcoin_address."
            )
        return OceanMiningPerformanceTracker(config=config, logger=logger)
