"""Collection of Value Objects for the Mining Performance Analysis domain of the Edge Mining application."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from edge_mining.domain.common import Timestamp, ValueObject
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.performance.common import PayoutFrequency, Satoshi


def _utc_now_timestamp() -> Timestamp:
    return Timestamp(datetime.now(timezone.utc))


@dataclass(frozen=True)
class MiningReward(ValueObject):
    """Value Object for a mining reward."""

    amount: Satoshi
    timestamp: Timestamp = field(default_factory=_utc_now_timestamp)


@dataclass(frozen=True)
class PoolWorkerStats(ValueObject):
    """Value Object describing live statistics of a single worker as reported by the pool."""

    worker_name: str
    hashrate: Optional[HashRate] = None
    last_share_at: Optional[Timestamp] = None
    valid_shares: Optional[int] = None
    stale_shares: Optional[int] = None
    rejected_shares: Optional[int] = None


@dataclass(frozen=True)
class PoolStats(ValueObject):
    """Value Object aggregating account-level statistics returned by a mining pool."""

    current_hashrate: Optional[HashRate] = None
    average_hashrate_24h: Optional[HashRate] = None
    average_hashrate_7d: Optional[HashRate] = None
    unpaid_balance: Optional[Satoshi] = None
    estimated_next_payout: Optional[Satoshi] = None
    workers: List[PoolWorkerStats] = field(default_factory=list)
    timestamp: Timestamp = field(default_factory=_utc_now_timestamp)


@dataclass(frozen=True)
class PayoutSchedule(ValueObject):
    """Value Object describing the payout policy advertised by the pool."""

    frequency: PayoutFrequency = PayoutFrequency.UNKNOWN
    threshold: Optional[Satoshi] = None
    next_payout_at: Optional[Timestamp] = None
