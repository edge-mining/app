"""Dummy adapter (Implementation of Feature Ports) that simulates a miner for Edge Mining Application"""

import random
from typing import List, Optional

from edge_mining.domain.common import Watts
from edge_mining.domain.miner.common import MinerStatus
from edge_mining.domain.miner.ports import (
    DeviceInfoPort,
    ExternalFanControlPort,
    ExternalFanSpeedMonitorPort,
    HashboardMonitorPort,
    HashrateMonitorPort,
    InletTemperatureMonitorPort,
    InternalFanControlPort,
    InternalFanSpeedMonitorPort,
    MiningControlPort,
    OperationalMonitorPort,
    OutletTemperatureMonitorPort,
    PowerControlPort,
    PowerMonitorPort,
    StatusMonitorPort,
)
from edge_mining.domain.miner.value_objects import (
    FanSpeed,
    Frequency,
    HashboardSnapshot,
    HashRate,
    MinerInfo,
    Temperature,
    Voltage,
)
from edge_mining.shared.logging.port import LoggerPort


class DummyMinerController(
    HashrateMonitorPort,
    PowerMonitorPort,
    StatusMonitorPort,
    HashboardMonitorPort,
    InletTemperatureMonitorPort,
    OutletTemperatureMonitorPort,
    InternalFanSpeedMonitorPort,
    ExternalFanSpeedMonitorPort,
    MiningControlPort,
    PowerControlPort,
    InternalFanControlPort,
    ExternalFanControlPort,
    DeviceInfoPort,
    OperationalMonitorPort,
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
        firmware_type = "Stock"
        firmware_version = "1.0.0"
        mac_address = "00:11:22:33:10:99"
        hostname = "edgemining-dummyminer"

        info = MinerInfo(
            model=model,
            serial_number=serial_number,
            firmware_type=firmware_type,
            firmware_version=firmware_version,
            mac_address=mac_address,
            hostname=hostname,
        )

        if self.logger:
            self.logger.debug(f"DummyController: Device info fetched: {info}")

        return info

    # --- MiningControlPort ---

    async def start_mining(self) -> bool:
        """Start the miner."""
        if self.logger:
            self.logger.debug(f"DummyController: Received START (current: {self._status.name})")
        if self._status != MinerStatus.ON:
            self._status = MinerStatus.STARTING
            if self.logger:
                self.logger.debug("DummyController: Setting status to STARTING")
        return True

    async def stop_mining(self) -> bool:
        """Stop the miner."""
        if self.logger:
            self.logger.debug(f"DummyController: Received STOP (current: {self._status.name})")
        if self._status == MinerStatus.ON:
            self._status = MinerStatus.STOPPING
            if self.logger:
                self.logger.debug("DummyController: Setting status to STOPPING")
        return True

    # --- StatusMonitorPort ---

    async def get_status(self) -> MinerStatus:
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

    async def get_blocks_found(self) -> Optional[int]:
        """Gets the total number of blocks found."""
        return 0

    async def get_system_uptime(self) -> Optional[int]:
        """Gets the system uptime in seconds."""
        return 3600

    # --- PowerMonitorPort ---

    async def get_power(self) -> Optional[Watts]:
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

    async def get_hashrate(self) -> Optional[HashRate]:
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

    # --- HashboardMonitorPort ---

    async def get_hashboards(self) -> List[HashboardSnapshot]:
        """Get simulated hashboard data."""
        num_boards = 3
        snapshots: List[HashboardSnapshot] = []
        for i in range(num_boards):
            if self._status == MinerStatus.ON:
                chip_temp = Temperature(value=round(random.uniform(55.0, 85.0), 1))
                board_temp = Temperature(value=round(random.uniform(45.0, 70.0), 1))
                voltage = Voltage(value=round(random.uniform(11.8, 12.6), 2))
                frequency = Frequency(value=round(random.uniform(400.0, 650.0), 1))
                hr_value = round(random.uniform(0, self._hashrate_max.value / num_boards), 2)
                nominal_hr = round(self._hashrate_max.value / num_boards, 2)
                hash_rate = HashRate(value=hr_value, unit=self._hashrate_max.unit)
                nominal_hash_rate = HashRate(value=nominal_hr, unit=self._hashrate_max.unit)
                error_val = round(nominal_hr - hr_value, 4)
                hash_rate_error = HashRate(value=error_val, unit=self._hashrate_max.unit)
            elif self._status in (MinerStatus.STARTING, MinerStatus.STOPPING):
                chip_temp = Temperature(value=round(random.uniform(30.0, 55.0), 1))
                board_temp = Temperature(value=round(random.uniform(25.0, 45.0), 1))
                voltage = Voltage(value=round(random.uniform(11.0, 12.0), 2))
                frequency = Frequency(value=0.0)
                hash_rate = HashRate(value=0.0, unit=self._hashrate_max.unit)
                nominal_hash_rate = None
                hash_rate_error = None
            else:
                chip_temp = Temperature(value=round(random.uniform(20.0, 30.0), 1))
                board_temp = Temperature(value=round(random.uniform(18.0, 28.0), 1))
                voltage = Voltage(value=0.0)
                frequency = Frequency(value=0.0)
                hash_rate = HashRate(value=0.0, unit=self._hashrate_max.unit)
                nominal_hash_rate = None
                hash_rate_error = None

            snapshots.append(
                HashboardSnapshot(
                    index=i,
                    chip_temperature=chip_temp,
                    board_temperature=board_temp,
                    voltage=voltage,
                    frequency=frequency,
                    hash_rate=hash_rate,
                    nominal_hash_rate=nominal_hash_rate,
                    hash_rate_error=hash_rate_error,
                )
            )

        if self.logger:
            self.logger.debug(f"DummyController: Reporting {len(snapshots)} hashboards")
        return snapshots

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
