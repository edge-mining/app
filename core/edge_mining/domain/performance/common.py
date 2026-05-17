"""Collection of Common Objects for the Mining Performance Analysis domain of the Edge Mining application."""

from enum import Enum
from typing import NewType

from edge_mining.domain.common import AdapterType

# Using Satoshi as the unit for rewards
Satoshi = NewType("Satoshi", int)


class MiningPerformanceTrackerAdapter(AdapterType):
    """Types of mining performance tracker adapter."""

    DUMMY = "dummy"
    OCEAN = "ocean"
    BRAIINS_POOL = "braiins_pool"


class PayoutFrequency(str, Enum):
    """How often a pool issues payouts."""

    UNKNOWN = "unknown"
    PER_BLOCK = "per_block"
    HOURLY = "hourly"
    DAILY = "daily"
    THRESHOLD = "threshold"
