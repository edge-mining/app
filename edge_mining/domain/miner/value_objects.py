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
class HashboardSnapshot(ValueObject):
    """Value Object representing a snapshot of a single hashboard's state.

    Aggregates per-board metrics: temperatures, electrical parameters, and hashrate data.
    """

    index: int
    chip_temperature: Optional[Temperature] = None
    board_temperature: Optional[Temperature] = None
    voltage: Optional[Voltage] = None
    frequency: Optional[Frequency] = None
    hash_rate: Optional[HashRate] = None
    nominal_hash_rate: Optional[HashRate] = None
    hash_rate_error: Optional[HashRate] = None


@dataclass(frozen=True)
class MinerStateSnapshot(ValueObject):
    """Value Object representing a snapshot of a miner's operational state at a given moment.

    This is used by the Rule Engine, Policy Rules, and the DecisionalContext
    for decision-making. It has no repository — it is created on-the-fly
    from controller data.

    Per-board data (chip/board temperature, voltage, frequency) is in hashboards.
    Convenience properties (max_chip_temperature, max_board_temperature) are provided
    for rule engine access without iterating boards.
    """

    status: MinerStatus = MinerStatus.UNKNOWN
    hash_rate: Optional[HashRate] = None
    power_consumption: Optional[Watts] = None
    inlet_temperature: Optional[Temperature] = None
    outlet_temperature: Optional[Temperature] = None
    internal_fan_speed: List[FanSpeed] = field(default_factory=list)
    external_fan_speed: Optional[FanSpeed] = None
    hashboards: List[HashboardSnapshot] = field(default_factory=list)
    blocks_found: Optional[int] = None
    system_uptime: Optional[int] = None  # seconds

    @property
    def max_chip_temperature(self) -> Optional[Temperature]:
        """Returns the maximum chip temperature across all hashboards."""
        temps = [hb.chip_temperature for hb in self.hashboards if hb.chip_temperature is not None]
        return max(temps, key=lambda t: t.value) if temps else None

    @property
    def max_board_temperature(self) -> Optional[Temperature]:
        """Returns the maximum board temperature across all hashboards."""
        temps = [hb.board_temperature for hb in self.hashboards if hb.board_temperature is not None]
        return max(temps, key=lambda t: t.value) if temps else None

    @property
    def avg_chip_temperature(self) -> Optional[Temperature]:
        """Returns the average chip temperature across all hashboards."""
        temps = [hb.chip_temperature for hb in self.hashboards if hb.chip_temperature is not None]
        if not temps:
            return None
        avg = round(sum(t.value for t in temps) / len(temps), 1)
        return Temperature(value=avg, unit=temps[0].unit)

    @property
    def avg_board_temperature(self) -> Optional[Temperature]:
        """Returns the average board temperature across all hashboards."""
        temps = [hb.board_temperature for hb in self.hashboards if hb.board_temperature is not None]
        if not temps:
            return None
        avg = round(sum(t.value for t in temps) / len(temps), 1)
        return Temperature(value=avg, unit=temps[0].unit)
