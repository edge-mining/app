"""Collection of Value Objects for the Mining Device Management domain of the Edge Mining application."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import ValueObject, Watts
from edge_mining.domain.miner.common import MinerStatus


@dataclass(frozen=True)
class HashRate(ValueObject):
    """Value Object for a hash rate."""

    value: float  # e.g., TH/s
    unit: str = "TH/s"


@dataclass(frozen=True)
class MinerStateSnapshot(ValueObject):
    """Value Object representing a snapshot of a miner's operational state at a given moment.

    This is used by the Rule Engine, Policy Rules, and the DecisionalContext
    for decision-making. It has no repository — it is created on-the-fly
    from controller data.
    """

    status: MinerStatus = MinerStatus.UNKNOWN
    hash_rate: Optional[HashRate] = None
    power_consumption: Optional[Watts] = None
