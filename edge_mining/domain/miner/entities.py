"""Collection of Entities for the Mining Device Management domain of the Edge Mining application."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import Entity, EntityId, Watts
from edge_mining.domain.miner.common import MinerControllerAdapter
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.shared.interfaces.config import MinerControllerConfig


@dataclass
class Miner(Entity):
    """Entity for a miner.

    Represents the physical mining asset and its intrinsic (static) properties.
    Runtime operational state (status, current hash rate, current power consumption)
    is captured separately in MinerStateSnapshot.
    """

    name: str = ""
    model: Optional[str] = None
    hash_rate_max: Optional[HashRate] = None  # Max hash rate for the miner
    power_consumption_max: Optional[Watts] = None  # Max power consumption for the miner
    active: bool = True  # Is the miner active in the system?

    controller_id: Optional[EntityId] = None  # Controller for the miner

    def activate(self):
        """Activate the miner."""
        self.active = True
        print(f"Domain: Miner {self.id} activated")

    def deactivate(self):
        """Deactivate the miner."""
        self.active = False
        print(f"Domain: Miner {self.id} deactivated")


@dataclass
class MinerController(Entity):
    """Entity for a miner controller."""

    name: str = ""
    adapter_type: MinerControllerAdapter = MinerControllerAdapter.DUMMY  # Default to dummy controller
    config: Optional[MinerControllerConfig] = None
    external_service_id: Optional[EntityId] = None
