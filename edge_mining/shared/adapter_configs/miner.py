"""
Collection of adapters configuration for the miner domain
of the Edge Mining application.
"""

from dataclasses import asdict, dataclass, field

from edge_mining.domain.miner.common import MinerControllerAdapter
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.shared.interfaces.config import MinerControllerConfig


@dataclass(frozen=True)
class MinerControllerDummyConfig(MinerControllerConfig):
    """
    Miner controller configuration. It encapsulate the configuration parameters
    to control a miner with dummy controller.
    """

    initial_status: str = field(default="UNKNOWN")
    power_max: float = field(default=3200.0)
    hashrate_max: HashRate = field(default=HashRate(90, "TH/s"))

    def is_valid(self, adapter_type: MinerControllerAdapter) -> bool:
        """
        Check if the configuration is valid for the given adapter type.
        For Dummy Miner Controller, it is always valid.
        """
        return adapter_type == MinerControllerAdapter.DUMMY

    def to_dict(self) -> dict:
        """Converts the configuration object into a serializable dictionary"""
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        """Create a configuration object from a dictionary"""
        hashrate_max = HashRate(90, "TH/s")
        if "hashrate_max" in data:
            hashrate_dict: dict = data.get("hashrate_max")
            hashrate_max = HashRate(
                value=hashrate_dict.get("value", 90),
                unit=hashrate_dict.get("unit", "TH/s"),
            )
        return MinerControllerDummyConfig(
            initial_status=data.get("initial_status", "UNKNOWN"),
            power_max=data.get("power_max", 3200.0),
            hashrate_max=hashrate_max,
        )


@dataclass(frozen=True)
class MinerControllerGenericSocketHomeAssistantAPIConfig(MinerControllerConfig):
    """
    Miner controller configuration. It encapsulate the configuration parameters
    to control a miner via Home Assistant's entities of a smart socket.
    """

    entity_switch: str = field(default="switch.miner_socket")
    entity_power: str = field(default="sensor.miner_power")
    unit_power: str = field(default="W")

    def is_valid(self, adapter_type: MinerControllerAdapter) -> bool:
        """
        Check if the configuration is valid for the given adapter type.
        For Generic Socket Home Assistant API Miner Controller,
        it is valid if the adapter type matches.
        """
        return adapter_type == MinerControllerAdapter.GENERIC_SOCKET_HOME_ASSISTANT_API

    def to_dict(self) -> dict:
        """Converts the configuration object into a serializable dictionary"""
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        """Create a configuration object from a dictionary"""
        return cls(**data)
