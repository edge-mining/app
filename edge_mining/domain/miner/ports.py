"""Collection of Ports for the Mining Device Management domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import ClassVar, List, Optional

from edge_mining.domain.common import EntityId, Watts
from edge_mining.domain.miner.aggregate_roots import Miner
from edge_mining.domain.miner.common import MinerFeatureType, MinerStatus
from edge_mining.domain.miner.entities import MinerController
from edge_mining.domain.miner.value_objects import (
    FanSpeed,
    Frequency,
    HashRate,
    Temperature,
    Voltage,
)

# --- Feature Ports ---


class MinerFeaturePort(ABC):
    """Base port for all miner feature ports.

    Each concrete port declares its feature_type as a ClassVar.
    Adapters declare their capabilities by implementing these ports via multiple inheritance.
    Feature discovery is introspective via MRO.
    """

    feature_type: ClassVar[MinerFeatureType]

    @classmethod
    def get_supported_features(cls) -> List[MinerFeatureType]:
        """Introspect MRO to discover all supported feature types.

        Walks the class hierarchy and collects feature_type from each
        MinerFeaturePort subclass that declares one.
        """
        features = []
        for base in cls.__mro__:
            if (
                base is not MinerFeaturePort
                and isinstance(base, type)
                and issubclass(base, MinerFeaturePort)
                and "feature_type" in base.__dict__
            ):
                features.append(base.feature_type)
        return features


# --- Monitoring Ports (read-only) ---


class HashrateMonitorPort(MinerFeaturePort):
    """Port for monitoring miner hashrate."""

    feature_type = MinerFeatureType.HASHRATE_MONITORING

    @abstractmethod
    def get_hashrate(self) -> Optional[HashRate]:
        """Gets the current hash rate, if available."""
        raise NotImplementedError


class PowerMonitorPort(MinerFeaturePort):
    """Port for monitoring miner power consumption."""

    feature_type = MinerFeatureType.POWER_MONITORING

    @abstractmethod
    def get_power(self) -> Optional[Watts]:
        """Gets the current power consumption, if available."""
        raise NotImplementedError


class StatusMonitorPort(MinerFeaturePort):
    """Port for monitoring miner operational status."""

    feature_type = MinerFeatureType.STATUS_MONITORING

    @abstractmethod
    def get_status(self) -> MinerStatus:
        """Gets the current operational status of the miner."""
        raise NotImplementedError


class ChipTemperatureMonitorPort(MinerFeaturePort):
    """Port for monitoring ASIC chip temperature."""

    feature_type = MinerFeatureType.CHIP_TEMPERATURE_MONITORING

    @abstractmethod
    def get_chip_temperature(self) -> Optional[Temperature]:
        """Gets the current chip temperature, if available."""
        raise NotImplementedError


class BoardTemperatureMonitorPort(MinerFeaturePort):
    """Port for monitoring board temperature."""

    feature_type = MinerFeatureType.BOARD_TEMPERATURE_MONITORING

    @abstractmethod
    def get_board_temperature(self) -> Optional[Temperature]:
        """Gets the current board temperature, if available."""
        raise NotImplementedError


class InletTemperatureMonitorPort(MinerFeaturePort):
    """Port for monitoring inlet air temperature."""

    feature_type = MinerFeatureType.INLET_TEMPERATURE_MONITORING

    @abstractmethod
    def get_inlet_temperature(self) -> Optional[Temperature]:
        """Gets the current inlet air temperature, if available."""
        raise NotImplementedError


class OutletTemperatureMonitorPort(MinerFeaturePort):
    """Port for monitoring outlet air temperature."""

    feature_type = MinerFeatureType.OUTLET_TEMPERATURE_MONITORING

    @abstractmethod
    def get_outlet_temperature(self) -> Optional[Temperature]:
        """Gets the current outlet air temperature, if available."""
        raise NotImplementedError


class InternalFanSpeedMonitorPort(MinerFeaturePort):
    """Port for monitoring internal fan speed."""

    feature_type = MinerFeatureType.FAN_SPEED_INTERNAL_MONITORING

    @abstractmethod
    def get_internal_fan_speed(self) -> Optional[FanSpeed]:
        """Gets the current internal fan speed, if available."""
        raise NotImplementedError


class ExternalFanSpeedMonitorPort(MinerFeaturePort):
    """Port for monitoring external fan speed."""

    feature_type = MinerFeatureType.FAN_SPEED_EXTERNAL_MONITORING

    @abstractmethod
    def get_external_fan_speed(self) -> Optional[FanSpeed]:
        """Gets the current external fan speed, if available."""
        raise NotImplementedError


class VoltageMonitorPort(MinerFeaturePort):
    """Port for monitoring miner voltage."""

    feature_type = MinerFeatureType.VOLTAGE_MONITORING

    @abstractmethod
    def get_voltage(self) -> Optional[Voltage]:
        """Gets the current voltage, if available."""
        raise NotImplementedError


class FrequencyMonitorPort(MinerFeaturePort):
    """Port for monitoring chip operating frequency."""

    feature_type = MinerFeatureType.FREQUENCY_MONITORING

    @abstractmethod
    def get_frequency(self) -> Optional[Frequency]:
        """Gets the current chip operating frequency, if available."""
        raise NotImplementedError


# --- Control Ports (write) ---


class MiningControlPort(MinerFeaturePort):
    """Port for software-level mining start/stop control."""

    feature_type = MinerFeatureType.MINING_CONTROL

    @abstractmethod
    def start_mining(self) -> bool:
        """Attempts to start mining. Returns True on success."""
        raise NotImplementedError

    @abstractmethod
    def stop_mining(self) -> bool:
        """Attempts to stop mining. Returns True on success."""
        raise NotImplementedError


class PowerControlPort(MinerFeaturePort):
    """Port for hard power on/off control (e.g., smart plug)."""

    feature_type = MinerFeatureType.POWER_CONTROL

    @abstractmethod
    def power_on(self) -> bool:
        """Attempts to power on the miner. Returns True on success."""
        raise NotImplementedError

    @abstractmethod
    def power_off(self) -> bool:
        """Attempts to power off the miner. Returns True on success."""
        raise NotImplementedError


class InternalFanControlPort(MinerFeaturePort):
    """Port for controlling internal fan speed via firmware."""

    feature_type = MinerFeatureType.INTERNAL_FAN_CONTROL

    @abstractmethod
    def set_internal_fan_speed(self, speed_percent: float) -> bool:
        """Sets internal fan speed as a percentage (0-100). Returns True on success."""
        raise NotImplementedError


class ExternalFanControlPort(MinerFeaturePort):
    """Port for controlling external fan speed (e.g., ESPHome devices)."""

    feature_type = MinerFeatureType.EXTERNAL_FAN_CONTROL

    @abstractmethod
    def set_external_fan_speed(self, speed_percent: float) -> bool:
        """Sets external fan speed as a percentage (0-100). Returns True on success."""
        raise NotImplementedError


# --- Info Ports ---


class ModelDetectionPort(MinerFeaturePort):
    """Port for detecting miner hardware model."""

    feature_type = MinerFeatureType.MODEL_DETECTION

    @abstractmethod
    def get_model(self) -> Optional[str]:
        """Gets the model of the miner, if available."""
        raise NotImplementedError


# --- Repository Ports ---


class MinerRepository(ABC):
    """Port for the Miner Repository."""

    @abstractmethod
    def add(self, miner: Miner) -> None:
        """Adds a new miner to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, miner_id: EntityId) -> Optional[Miner]:
        """Retrieves a miner by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[Miner]:
        """Retrieves all miners in the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, miner: Miner) -> None:
        """Updates the state of an existing miner in the repository."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, miner_id: EntityId) -> None:
        """Removes a miner from the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_controller_id(self, controller_id: EntityId) -> List[Miner]:
        """Retrieves a list of miners that have at least one feature provided by the given controller."""
        raise NotImplementedError


class MinerControllerRepository(ABC):
    """Port for the Miner Controller Repository."""

    @abstractmethod
    def add(self, miner_controller: MinerController) -> None:
        """Adds a new miner controller to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, miner_controller_id: EntityId) -> Optional[MinerController]:
        """Retrieves a miner controller by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[MinerController]:
        """Retrieves all miner controllers in the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, miner_controller: MinerController) -> None:
        """Updates the state of an existing miner controller in the repository."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, miner_controller_id: EntityId) -> None:
        """Removes a miner controller from the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_external_service_id(self, external_service_id: EntityId) -> List[MinerController]:
        """Retrieves a list of miner controllers by its associated external service ID."""
        raise NotImplementedError
