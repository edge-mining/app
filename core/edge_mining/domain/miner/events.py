"""Miner domain events."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import DomainEvent, EntityId
from edge_mining.domain.miner.common import MinerStatus


@dataclass
class MinerStateChangedEvent(DomainEvent):
    """Event emitted when a miner changes state (started/stopped)."""

    miner_id: Optional[EntityId] = None
    miner_name: str = ""
    old_status: Optional[MinerStatus] = None
    new_status: Optional[MinerStatus] = None
