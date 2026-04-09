"""Collection of Value Objects for the Mining Device Management domain of the Edge Mining application."""

from dataclasses import dataclass, field
from typing import List, Optional

from edge_mining.domain.common import EntityId, ValueObject, Watts
from edge_mining.domain.miner.common import MinerFeatureType, MinerStatus


@dataclass(frozen=True)
class HashRate(ValueObject):
    """Value Object for a hash rate."""

    value: float  # e.g., TH/s
    unit: str = "TH/s"


@dataclass(frozen=True)
class Temperature(ValueObject):
    """Value Object for a temperature measurement."""

    value: float
    unit: str = "°C"


@dataclass(frozen=True)
class FanSpeed(ValueObject):
    """Value Object for a fan speed measurement."""

    value: float
    unit: str = "RPM"


@dataclass(frozen=True)
class Voltage(ValueObject):
    """Value Object for a voltage measurement."""

    value: float
    unit: str = "V"


@dataclass(frozen=True)
class Frequency(ValueObject):
    """Value Object for a frequency measurement."""

    value: float
    unit: str = "MHz"


@dataclass(frozen=True)
class MinerInfo(ValueObject):
    """Value Object for miner device information."""

    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    hashboard_count: Optional[int] = None
    chip_count: Optional[int] = None
    fan_count: Optional[int] = None


@dataclass(frozen=True)
class MinerFeature(ValueObject):
    """Value Object representing a single capability provided by a controller to a miner.

    Identity is given by the pair (feature_type, controller_id).
    """

    feature_type: MinerFeatureType
    controller_id: EntityId
    priority: int = 50  # 1-100, higher = higher priority
    enabled: bool = True


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
    chip_temperature: Optional[Temperature] = None
    board_temperature: Optional[Temperature] = None
    inlet_temperature: Optional[Temperature] = None
    outlet_temperature: Optional[Temperature] = None
    internal_fan_speed: List[FanSpeed] = field(default_factory=list)
    external_fan_speed: Optional[FanSpeed] = None
    voltage: Optional[Voltage] = None
    frequency: Optional[Frequency] = None
