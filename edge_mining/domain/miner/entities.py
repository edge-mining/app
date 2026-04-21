"""Collection of Entities for the Mining Device Management domain of the Edge Mining application."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import Entity, EntityId
from edge_mining.domain.miner.common import MinerControllerAdapter
from edge_mining.shared.interfaces.config import MinerControllerConfig


@dataclass
class MinerController(Entity):
    """Entity for a miner controller."""

    name: str = ""
    adapter_type: MinerControllerAdapter = MinerControllerAdapter.DUMMY  # Default to dummy controller
    config: Optional[MinerControllerConfig] = None
    external_service_id: Optional[EntityId] = None
