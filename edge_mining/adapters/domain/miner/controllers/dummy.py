"""Dummy adapter (Implementation of Feature Ports) that simulates a miner for Edge Mining Application"""

import random
from typing import List, Optional

from edge_mining.domain.common import Watts
from edge_mining.domain.miner.common import MinerStatus
from edge_mining.domain.miner.ports import (
    BoardTemperatureMonitorPort,
    ChipTemperatureMonitorPort,
    DeviceInfoPort,
    ExternalFanControlPort,
    ExternalFanSpeedMonitorPort,
    FrequencyMonitorPort,
    HashrateMonitorPort,
    InletTemperatureMonitorPort,
    InternalFanControlPort,
    InternalFanSpeedMonitorPort,
    MiningControlPort,
    OutletTemperatureMonitorPort,
    PowerControlPort,
    PowerMonitorPort,
    StatusMonitorPort,
    VoltageMonitorPort,
)
from edge_mining.domain.miner.value_objects import FanSpeed, Frequency, HashRate, MinerInfo, Temperature, Voltage
from edge_mining.shared.logging.port import LoggerPort


class DummyMinerController(
    HashrateMonitorPort,
    PowerMonitorPort,
    StatusMonitorPort,
    ChipTemperatureMonitorPort,
    BoardTemperatureMonitorPort,
    InletTemperatureMonitorPort,
    OutletTemperatureMonitorPort,
    InternalFanSpeedMonitorPort,
    ExternalFanSpeedMonitorPort,
    VoltageMonitorPort,
    FrequencyMonitorPort,
    MiningControlPort,
    PowerControlPort,
    InternalFanControlPort,
    ExternalFanControlPort,
    DeviceInfoPort,
):
    """Simulates miner control without real hardware.

    Implements all 16 feature ports for testing and development.
    """

    def __init__(
        self,
        initial_status: MinerStatus = MinerStatus.UNKNOWN,
        power_max: Optional[Watts] = None,
        hashrate_max: Optional[HashRate] = None,
        logger: Optional[LoggerPort] = None,
    ):
        self._status = initial_status
        self._power_max = power_max or Watts(3200.0)
        self._hashrate_max = hashrate_max or HashRate(90, "TH/s")
        self.logger = logger

        self._power: Watts = Watts(0.0)
        self._internal_fan_speed: float = 0.0
        self._external_fan_speed: float = 0.0

    # --- DeviceInfoPort ---

    async def get_device_info(self) -> Optional[MinerInfo]:
        """Gets the device information of the miner."""
        if self.logger:
            self.logger.debug("DummyController: Fetching device info...")

        # Simulate some dummy device info
        model = "DummyMiner X1"
        serial_number = "DMX1-01}"
        firmware_version = "1.0.0"
        mac_address = "00:11:22:33:10:99"
        hostname = "edgemining-dummyminer"

        info = MinerInfo(
            model=model,
            serial_number=serial_number,
            firmware_version=firmware_version,
            mac_address=mac_address,
            hostname=hostname,
        )

        if self.logger:
            self.logger.debug(f"DummyController: Device info fetched: {info}")

        return info

    # --- MiningControlPort ---

    async def start_miner(self) -> bool:
        """Start the miner."""
        if self.logger:
            self.logger.debug(f"DummyController: Received START (current: {self._status.name})")
        if self._status != MinerStatus.ON:
            self._status = MinerStatus.STARTING
            if self.logger:
                self.logger.debug("DummyController: Setting status to STARTING")
        return True

    async def stop_miner(self) -> bool:
        """Stop the miner."""
        if self.logger:
            self.logger.debug(f"DummyController: Received STOP (current: {self._status.name})")
        if self._status == MinerStatus.ON:
            self._status = MinerStatus.STOPPING
            if self.logger:
                self.logger.debug("DummyController: Setting status to STOPPING")
        return True

    # --- StatusMonitorPort ---

    async def get_miner_status(self) -> MinerStatus:
        """Get the status of the miner."""
        if self._status == MinerStatus.STARTING:
            if random.random() < 0.8:
                if self.logger:
                    self.logger.debug("DummyController: Simulating finished starting -> ON")
                self._status = MinerStatus.ON
            else:
                if self.logger:
                    self.logger.debug("DummyController: Simulating still STARTING")

        elif self._status == MinerStatus.STOPPING:
            if random.random() < 0.9:
                if self.logger:
                    self.logger.debug("DummyController: Simulating finished stopping -> OFF")
                self._status = MinerStatus.OFF
            else:
                if self.logger:
                    self.logger.debug("DummyController: Simulating still STOPPING")

        status = self._status
        if self.logger:
            self.logger.debug(f"DummyController: Reporting status {status.name}")
        return status

    # --- PowerMonitorPort ---

    async def get_miner_power(self) -> Optional[Watts]:
        """Get the power of the miner."""
        status = self._status
        if status == MinerStatus.ON:
            power = Watts(random.uniform(500, self._power_max))
            if self.logger:
                self.logger.debug(f"DummyController: Reporting power {power:.0f}W")
        elif status == MinerStatus.STARTING:
            power = Watts(random.uniform(10, 200))
            if self.logger:
                self.logger.debug(f"DummyController: Reporting power {power:.0f}W")
        else:
            if self.logger:
                self.logger.debug(f"DummyController: Reporting power 0W (status: {status.name})")
            power = Watts(0.0)

        self._power = power
        return power

    # --- HashrateMonitorPort ---

    async def get_miner_hashrate(self) -> Optional[HashRate]:
        """Get the hash rate of the miner."""
        status = self._status
        if status == MinerStatus.ON:
            hash_rate = HashRate(
                value=random.uniform(0, self._hashrate_max.value),
                unit=self._hashrate_max.unit,
            )
            if self.logger:
                self.logger.debug(f"DummyController: Reporting hash rate {hash_rate.value:.2f} {hash_rate.unit}")
            return hash_rate
        else:
            if self.logger:
                self.logger.debug(f"DummyController: Reporting hash rate 0 (status: {status.name})")
            return HashRate(value=0.0, unit="TH/s")

    # --- ChipTemperatureMonitorPort ---

    async def get_chip_temperature(self) -> Optional[Temperature]:
        """Get simulated chip temperature."""
        if self._status == MinerStatus.ON:
            temp = Temperature(value=round(random.uniform(55.0, 85.0), 1))
        elif self._status in (MinerStatus.STARTING, MinerStatus.STOPPING):
            temp = Temperature(value=round(random.uniform(30.0, 55.0), 1))
        else:
            temp = Temperature(value=round(random.uniform(20.0, 30.0), 1))
        if self.logger:
            self.logger.debug(f"DummyController: Reporting chip temperature {temp.value}{temp.unit}")
        return temp

    # --- BoardTemperatureMonitorPort ---

    async def get_board_temperature(self) -> Optional[Temperature]:
        """Get simulated board temperature."""
        if self._status == MinerStatus.ON:
            temp = Temperature(value=round(random.uniform(45.0, 70.0), 1))
        elif self._status in (MinerStatus.STARTING, MinerStatus.STOPPING):
            temp = Temperature(value=round(random.uniform(25.0, 45.0), 1))
        else:
            temp = Temperature(value=round(random.uniform(18.0, 28.0), 1))
        if self.logger:
            self.logger.debug(f"DummyController: Reporting board temperature {temp.value}{temp.unit}")
        return temp

    # --- InletTemperatureMonitorPort ---

    async def get_inlet_temperature(self) -> Optional[Temperature]:
        """Get simulated inlet air temperature."""
        temp = Temperature(value=round(random.uniform(18.0, 35.0), 1))
        if self.logger:
            self.logger.debug(f"DummyController: Reporting inlet temperature {temp.value}{temp.unit}")
        return temp

    # --- OutletTemperatureMonitorPort ---

    async def get_outlet_temperature(self) -> Optional[Temperature]:
        """Get simulated outlet air temperature."""
        if self._status == MinerStatus.ON:
            temp = Temperature(value=round(random.uniform(40.0, 65.0), 1))
        else:
            temp = Temperature(value=round(random.uniform(18.0, 30.0), 1))
        if self.logger:
            self.logger.debug(f"DummyController: Reporting outlet temperature {temp.value}{temp.unit}")
        return temp

    # --- InternalFanSpeedMonitorPort ---

    async def get_internal_fan_speed(self) -> List[FanSpeed]:
        """Get simulated internal fan speed."""
        if self._status == MinerStatus.ON:
            rpm = random.uniform(3000.0, 6000.0)
        elif self._status in (MinerStatus.STARTING, MinerStatus.STOPPING):
            rpm = random.uniform(1000.0, 3000.0)
        else:
            rpm = 0.0
        fan = FanSpeed(value=round(rpm, 0))
        if self.logger:
            self.logger.debug(f"DummyController: Reporting internal fan speed {fan.value} {fan.unit}")
        return [fan]

    # --- ExternalFanSpeedMonitorPort ---

    async def get_external_fan_speed(self) -> Optional[FanSpeed]:
        """Get simulated external fan speed."""
        if self._external_fan_speed > 0:
            rpm = self._external_fan_speed * 60.0  # percent to RPM approximation
        else:
            rpm = 0.0
        fan = FanSpeed(value=round(rpm, 0))
        if self.logger:
            self.logger.debug(f"DummyController: Reporting external fan speed {fan.value} {fan.unit}")
        return fan

    # --- VoltageMonitorPort ---

    async def get_voltage(self) -> Optional[Voltage]:
        """Get simulated voltage."""
        if self._status == MinerStatus.ON:
            v = Voltage(value=round(random.uniform(11.8, 12.6), 2))
        elif self._status in (MinerStatus.STARTING, MinerStatus.STOPPING):
            v = Voltage(value=round(random.uniform(11.0, 12.0), 2))
        else:
            v = Voltage(value=0.0)
        if self.logger:
            self.logger.debug(f"DummyController: Reporting voltage {v.value}{v.unit}")
        return v

    # --- FrequencyMonitorPort ---

    async def get_frequency(self) -> Optional[Frequency]:
        """Get simulated chip frequency."""
        if self._status == MinerStatus.ON:
            f = Frequency(value=round(random.uniform(400.0, 650.0), 1))
        else:
            f = Frequency(value=0.0)
        if self.logger:
            self.logger.debug(f"DummyController: Reporting frequency {f.value} {f.unit}")
        return f

    # --- PowerControlPort ---

    async def power_on(self) -> bool:
        """Simulate hard power on."""
        if self.logger:
            self.logger.debug(f"DummyController: Received POWER ON (current: {self._status.name})")
        if self._status in (MinerStatus.OFF, MinerStatus.UNKNOWN):
            self._status = MinerStatus.STARTING
        return True

    async def power_off(self) -> bool:
        """Simulate hard power off."""
        if self.logger:
            self.logger.debug(f"DummyController: Received POWER OFF (current: {self._status.name})")
        self._status = MinerStatus.OFF
        return True

    # --- InternalFanControlPort ---

    async def set_internal_fan_speed(self, speed_percent: float) -> bool:
        """Simulate setting internal fan speed."""
        if self.logger:
            self.logger.debug(f"DummyController: Setting internal fan speed to {speed_percent:.0f}%")
        self._internal_fan_speed = max(0.0, min(100.0, speed_percent))
        return True

    # --- ExternalFanControlPort ---

    async def set_external_fan_speed(self, speed_percent: float) -> bool:
        """Simulate setting external fan speed."""
        if self.logger:
            self.logger.debug(f"DummyController: Setting external fan speed to {speed_percent:.0f}%")
        self._external_fan_speed = max(0.0, min(100.0, speed_percent))
        return True
