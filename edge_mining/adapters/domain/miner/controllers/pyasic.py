"""
pyasic adapter (Implementation of Feature Ports)
that controls a miner via pyasic.
"""

from typing import Dict, List, Optional, Tuple, cast

import pyasic
from pyasic import AnyMiner
from pyasic.device.algorithm.hashrate import AlgoHashRate
from pyasic.rpc.base import BaseMinerRPCAPI
from pyasic.ssh.base import BaseSSH
from pyasic.web.base import BaseWebAPI

from edge_mining.domain.common import Watts
from edge_mining.domain.miner.aggregate_roots import Miner
from edge_mining.domain.miner.common import MinerControllerProtocol, MinerStatus
from edge_mining.domain.miner.exceptions import MinerControllerConfigurationError
from edge_mining.domain.miner.ports import (
    DeviceInfoPort,
    HashboardMonitorPort,
    HashrateMonitorPort,
    InletTemperatureMonitorPort,
    InternalFanControlPort,
    InternalFanSpeedMonitorPort,
    MaxHashrateDetectionPort,
    MaxPowerDetectionPort,
    MiningControlPort,
    OperationalMonitorPort,
    OutletTemperatureMonitorPort,
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
from edge_mining.shared.adapter_configs.miner import MinerControllerPyASICConfig
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import MinerControllerAdapterFactory
from edge_mining.shared.logging.port import LoggerPort


class PyASICMinerControllerAdapterFactory(MinerControllerAdapterFactory):
    """
    Create a factory for pyasic Miner Controller Adapter.
    This factory is used to create instances of the adapter.
    """

    def __init__(self):
        self._miner: Optional[Miner] = None

    def from_miner(self, miner: Miner):
        """Set the miner for this controller."""
        self._miner = miner

    def create(
        self,
        config: Optional[Configuration] = None,
        logger: Optional[LoggerPort] = None,
        external_service: Optional[ExternalServicePort] = None,
    ) -> "PyASICMinerController":
        """Create a miner controller adapter instance."""

        if not isinstance(config, MinerControllerPyASICConfig):
            raise MinerControllerConfigurationError("Invalid configuration for pyasic Miner Controller.")

        # Get the config from the provided configuration
        miner_controller_configuration: MinerControllerPyASICConfig = config

        return PyASICMinerController(
            ip=miner_controller_configuration.ip,
            protocol=miner_controller_configuration.protocol,
            port=miner_controller_configuration.port,
            username=miner_controller_configuration.username,
            password=miner_controller_configuration.password,
            logger=logger,
        )


class PyASICMinerController(
    HashrateMonitorPort,
    PowerMonitorPort,
    StatusMonitorPort,
    HashboardMonitorPort,
    InletTemperatureMonitorPort,
    OutletTemperatureMonitorPort,
    InternalFanSpeedMonitorPort,
    MiningControlPort,
    InternalFanControlPort,
    DeviceInfoPort,
    MaxPowerDetectionPort,
    MaxHashrateDetectionPort,
    OperationalMonitorPort,
):
    """Controls a miner via pyasic. Implements multiple feature ports."""

    def __init__(
        self,
        ip: str,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        protocol: Optional[MinerControllerProtocol] = None,
        logger: Optional[LoggerPort] = None,
    ):
        self.logger = logger

        self.ip = ip
        self.password = password
        self.port = port
        self.username = username
        self.protocol = protocol

        self._miner: Optional[AnyMiner] = None

        self._log_configuration()

    def _log_configuration(self):
        if self.logger:
            self.logger.debug(
                f"PyASIC Controller configured: IP={self.ip}, protocol={self.protocol}, "
                f"port={self.port}, username={self.username}, pwd={'***' if self.password else None}"
            )

    async def _get_miner(self) -> None:
        """Retrieve the pyasic miner instance."""
        if self._miner is None:
            try:
                miner = await pyasic.get_miner(self.ip)
                if miner is not None:
                    self._miner = cast(AnyMiner, miner)

                    # Set additional parameters like protocol, password,port
                    if self.protocol == MinerControllerProtocol.RPC:
                        if isinstance(self._miner.rpc, BaseMinerRPCAPI):
                            if self.port:
                                self._miner.rpc.port = self.port
                            if self.password:
                                self._miner.rpc.pwd = self.password
                        else:
                            if self.logger:
                                self.logger.error("Unknown PyASIC Miner Controller RPC Protocol")
                    elif self.protocol == MinerControllerProtocol.WEB:
                        if isinstance(self._miner.web, BaseWebAPI):
                            if self.port:
                                self._miner.web.port = self.port
                            if self.password:
                                self._miner.web.pwd = self.password
                            if self.username:
                                self._miner.web.username = self.username
                        else:
                            if self.logger:
                                self.logger.error("Unknown PyASIC Miner Controller Web Protocol")
                    elif self.protocol == MinerControllerProtocol.SSH:
                        if isinstance(self._miner.ssh, BaseSSH):
                            if self.port:
                                self._miner.ssh.port = self.port
                            if self.password:
                                self._miner.ssh.pwd = self.password
                            if self.username:
                                self._miner.ssh.username = self.username
                        else:
                            if self.logger:
                                self.logger.error("Unknown PyASIC Miner Controller SSH Protocol")
                    else:
                        if self.logger:
                            self.logger.error(f"Unknown PyASIC Miner Controller Protocol: {self.protocol}")

                    if self.logger:
                        self.logger.debug(
                            f"Miner identified: type={type(self._miner).__name__}, "
                            f"model={self._miner.raw_model}, firmware={self._miner.firmware}, "
                            f"rpc={type(self._miner.rpc).__name__ if self._miner.rpc else None}, "
                            f"web={type(self._miner.web).__name__ if self._miner.web else None}, "
                            f"ssh={type(self._miner.ssh).__name__ if self._miner.ssh else None}, "
                            f"expected_hashboards={self._miner.expected_hashboards}"
                        )
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to retrieve miner instance from {self.ip}: {e}")

    # --- DeviceInfoDetectionPort ---

    async def get_device_info(self) -> Optional[MinerInfo]:
        """Gets the device identification information of the miner, if available."""

        if self.logger:
            self.logger.debug(f"Fetching model from {self.ip}...")

        await self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return None

        hashboard_count = self._miner.expected_hashboards
        chip_count = self._miner.expected_chips
        fan_count = self._miner.expected_fans

        serial_number = await self._miner.get_serial_number()
        mac_address = await self._miner.get_mac()
        model = await self._miner.get_model()
        firmware_version = await self._miner.get_fw_ver()
        hostname = await self._miner.get_hostname()

        return MinerInfo(
            model=str(model) if model is not None else None,
            serial_number=str(serial_number) if serial_number is not None else None,
            firmware_version=str(firmware_version) if firmware_version is not None else None,
            mac_address=str(mac_address) if mac_address is not None else None,
            hostname=str(hostname) if hostname is not None else None,
            hashboard_count=int(hashboard_count) if hashboard_count is not None else None,
            chip_count=int(chip_count) if chip_count is not None else None,
            fan_count=int(fan_count) if fan_count is not None else None,
        )

    # --- MaxPowerDetectionPort ---

    async def get_max_power(self) -> Optional[Watts]:
        """Gets the maximum power consumption of the miner, if available."""

        if self.logger:
            self.logger.debug(f"Fetching max power from {self.ip}...")

        await self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return None

        miner = self._miner
        wattage = await miner.get_wattage_limit()
        if wattage is None:
            if self.logger:
                self.logger.debug(f"Failed to fetch max power from {self.ip}...")
            return None
        max_power_watts = Watts(wattage)

        if self.logger:
            self.logger.debug(f"Max power fetched: {max_power_watts}")

        return max_power_watts

    # --- MaxHashrateDetectionPort ---

    async def get_max_hashrate(self) -> Optional[HashRate]:
        """Gets the maximum hash rate of the miner, if available."""

        if self.logger:
            self.logger.debug(f"Fetching max hash rate from {self.ip}...")

        await self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return None

        miner = self._miner
        hashrate = await miner.get_expected_hashrate()
        if hashrate is None:
            if self.logger:
                self.logger.debug(f"Failed to fetch max hash rate from {self.ip}...")
            return None
        normalized_value, normalized_unit = self._normalize_hashrate_unit(
            value=float(hashrate),
            unit=str(hashrate.unit),
        )
        max_hashrate = HashRate(value=normalized_value, unit=normalized_unit)

        if self.logger:
            self.logger.debug(f"Max hash rate fetched: {max_hashrate}")

        return max_hashrate

    # --- HashrateMonitorPort ---

    async def get_hashrate(self) -> Optional[HashRate]:
        """Gets the current hash rate, if available."""

        if self.logger:
            self.logger.debug(f"Fetching hashrate from {self.ip}...")

        await self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return None

        miner = self._miner
        hashrate: Optional[AlgoHashRate] = await miner.get_hashrate()
        if hashrate is None:
            if self.logger:
                self.logger.debug(f"Failed to fetch hashrate from {self.ip}...")
            return None
        normalized_value, normalized_unit = self._normalize_hashrate_unit(
            value=float(hashrate),
            unit=str(hashrate.unit),
        )
        real_hashrate = HashRate(value=normalized_value, unit=normalized_unit)

        if self.logger:
            self.logger.debug(f"Hashrate fetched: {real_hashrate}")

        return real_hashrate

    # --- PowerMonitorPort ---

    async def get_power(self) -> Optional[Watts]:
        """Gets the current power consumption, if available."""
        if self.logger:
            self.logger.debug(f"Fetching power consumption from {self.ip}...")

        await self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return None

        miner = self._miner
        wattage = await miner.get_wattage()
        if wattage is None:
            if self.logger:
                self.logger.debug(f"Failed to fetch power consumption from {self.ip}...")
            return None
        power_watts = Watts(wattage)

        if self.logger:
            self.logger.debug(f"Power consumption fetched: {power_watts}")

        return power_watts

    # --- StatusMonitorPort ---

    async def get_status(self) -> MinerStatus:
        """Gets the current operational status of the miner."""
        if self.logger:
            self.logger.debug(f"Fetching miner status from {self.ip}...")

        await self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return MinerStatus.UNKNOWN

        miner = self._miner
        mining_state = await miner.is_mining()

        # Map the bool result from is_mining() to MinerStatus
        state_map: Dict[Optional[bool], MinerStatus] = {
            True: MinerStatus.ON,
            False: MinerStatus.OFF,
            None: MinerStatus.UNKNOWN,
        }

        # If miner status is not provided, we can try to derive it
        if mining_state is None:
            if self.logger:
                self.logger.debug("Mining state is not provided, deriving miner status...")
            derived_state = await self._derive_miner_status()
            miner_status = state_map.get(derived_state, MinerStatus.UNKNOWN)
        else:
            miner_status = state_map.get(mining_state, MinerStatus.UNKNOWN)

        if self.logger:
            self.logger.debug(f"Miner status fetched: {miner_status}")

        return miner_status

    # --- OperationalMonitorPort ---

    async def get_blocks_found(self) -> Optional[int]:
        """Gets the total number of blocks found by the miner."""
        await self._get_miner()
        if not self._miner or not self._miner.rpc:
            return None
        try:
            summary = await self._miner.rpc.send_command("summary")

            blocks_found = summary.get("SUMMARY", [{}])[0].get("Found Blocks")
            return blocks_found if blocks_found is not None else None
        except Exception:
            return None

    async def get_system_uptime(self) -> Optional[int]:
        """Gets the system uptime in seconds."""
        await self._get_miner()
        if not self._miner or not self._miner.rpc:
            return None
        try:
            summary = await self._miner.rpc.send_command("summary")
            elapsed = summary.get("SUMMARY", [{}])[0].get("Elapsed")
            return int(elapsed) if elapsed is not None else None
        except Exception:
            return None

    # --- HashboardMonitorPort ---

    async def get_hashboards(self) -> List[HashboardSnapshot]:
        """Gets the current state of all hashboards."""
        if self.logger:
            self.logger.debug(f"Fetching hashboard data from {self.ip}...")

        await self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return []

        miner = self._miner
        hashboards = await miner.get_hashboards()

        if self.logger:
            self.logger.debug(
                f"pyasic get_hashboards() returned {len(hashboards)} boards. "
                f"Raw data: {[(hb.slot, hb.chip_temp, hb.temp, hb.voltage, hb.hashrate) for hb in hashboards]}"
            )

        # Fallback: if get_hashboards() returns empty (e.g. expected_hashboards is None),
        # query the RPC directly and build HashBoard objects from raw data.
        if not hashboards:
            if self.logger:
                self.logger.debug(f"get_hashboards() returned empty for {self.ip}, trying RPC fallback...")
            hashboards = await self._fetch_hashboards_fallback(miner)

        if not hashboards:
            if self.logger:
                self.logger.debug(f"No hashboard data available from {self.ip}")
            return []

        # Supplement missing voltage/frequency from devdetails RPC
        # pyasic's _get_hashboards() only extracts Chips from devdetails,
        # but BOSer firmware also reports Voltage and Frequency there.
        devdetails_extra = await self._fetch_devdetails_extra(miner)

        snapshots: List[HashboardSnapshot] = []
        for idx, hb in enumerate(hashboards):
            chip_temp = Temperature(value=float(hb.chip_temp)) if hb.chip_temp is not None else None
            board_temp = Temperature(value=float(hb.temp)) if hb.temp is not None else None

            hb_hashrate = None
            if hb.hashrate is not None:
                hr_val, hr_unit = self._normalize_hashrate_unit(
                    value=float(hb.hashrate),
                    unit=str(hb.hashrate.unit) if hasattr(hb.hashrate, "unit") else "TH/s",
                )
                hb_hashrate = HashRate(value=hr_val, unit=hr_unit)

            hb_voltage = Voltage(value=round(float(hb.voltage), 2)) if hb.voltage is not None else None
            hb_frequency: Optional[Frequency] = None

            # Fill voltage/frequency from devdetails if pyasic didn't provide them
            if idx < len(devdetails_extra):
                extra = devdetails_extra[idx]
                if hb_voltage is None and extra.get("voltage") is not None:
                    hb_voltage = Voltage(value=round(float(extra["voltage"]), 2))
                if extra.get("frequency") is not None:
                    hb_frequency = Frequency(value=float(extra["frequency"]))

            snapshots.append(
                HashboardSnapshot(
                    index=idx,
                    chip_temperature=chip_temp,
                    board_temperature=board_temp,
                    voltage=hb_voltage,
                    frequency=hb_frequency,
                    hash_rate=hb_hashrate,
                    nominal_hash_rate=None,
                    hash_rate_error=None,
                )
            )

        if self.logger:
            self.logger.debug(f"Hashboard data fetched: {len(snapshots)} boards from {self.ip}")

        return snapshots

    # --- InletTemperatureMonitorPort ---

    async def get_inlet_temperature(self) -> Optional[Temperature]:
        """Gets the current inlet air temperature, if available."""
        if self.logger:
            self.logger.debug(f"Fetching inlet temperature from {self.ip}...")

        await self._get_miner()

        if not self._miner:
            return None

        miner = self._miner
        data = await miner.get_data()
        if data is None or data.env_temp is None:
            return None

        return Temperature(value=float(data.env_temp))

    # --- OutletTemperatureMonitorPort ---

    async def get_outlet_temperature(self) -> Optional[Temperature]:
        """Gets the current outlet air temperature, if available."""
        if self.logger:
            self.logger.debug(f"Fetching outlet temperature from {self.ip}...")

        # pyasic does not typically provide separate outlet temperature
        # Some miners expose this through env_temp or specific board data
        return None

    # --- InternalFanSpeedMonitorPort ---

    async def get_internal_fan_speed(self) -> List[FanSpeed]:
        """Gets the current internal fan speed, if available."""
        miner_fans: List[FanSpeed] = []

        if self.logger:
            self.logger.debug(f"Fetching internal fan speed from {self.ip}...")

        await self._get_miner()

        if not self._miner:
            return []

        miner = self._miner
        fans = await miner.get_fans()
        if fans is None:
            return []

        for fan in fans:
            if fan.speed is not None:
                miner_fans.append(FanSpeed(value=float(fan.speed)))

        return miner_fans

    # --- MiningControlPort ---

    async def start_mining(self) -> bool:
        """Attempts to start mining. Returns True on success."""
        if self.logger:
            self.logger.debug(f"Sending start command to miner at {self.ip}...")

        await self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return False

        miner = self._miner
        success = await miner.resume_mining()

        if self.logger:
            self.logger.debug(f"Start command sent. Success: {success}")

        return success or False

    async def stop_mining(self) -> bool:
        """Attempts to stop mining. Returns True on success."""
        if self.logger:
            self.logger.debug(f"Sending stop command to miner at {self.ip}...")

        await self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return False

        miner = self._miner
        success = await miner.stop_mining()

        if self.logger:
            self.logger.debug(f"Stop command sent. Success: {success}")

        return success or False

    # --- InternalFanControlPort ---

    async def set_internal_fan_speed(self, speed_percent: float) -> bool:
        """Sets internal fan speed as a percentage (0-100). Returns True on success."""
        if self.logger:
            self.logger.debug(f"Setting internal fan speed to {speed_percent}% on {self.ip}...")

        await self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return False

        miner = self._miner
        try:
            success = await miner.set_fan_speed(int(speed_percent))
            if self.logger:
                self.logger.debug(f"Fan speed set. Success: {success}")
            return success or False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to set fan speed on {self.ip}: {e}")
            return False

    # --- Private helpers ---

    async def _fetch_devdetails_extra(self, miner: AnyMiner) -> List[dict]:
        """Fetch Voltage and Frequency from devdetails RPC.

        pyasic's _get_hashboards() only extracts Chips from devdetails,
        but some firmwares (e.g. BOSer) also report Voltage and Frequency.
        Returns a list of dicts (one per board, positional order) with
        'voltage' and 'frequency' keys.
        """
        if miner.rpc is None:
            return []

        try:
            rpc_data = await miner.rpc.send_command("devdetails")
        except Exception as e:
            if self.logger:
                self.logger.debug(f"devdetails RPC failed: {e}")
            return []

        details = rpc_data.get("DEVDETAILS", [])
        if not details:
            return []

        # Sort by ID and extract voltage/frequency by positional index
        sorted_details = sorted(details, key=lambda d: d.get("ID", 0))
        result = []
        for d in sorted_details:
            result.append(
                {
                    "voltage": d.get("Voltage"),
                    "frequency": d.get("Frequency"),
                }
            )

        if self.logger:
            self.logger.debug(f"devdetails extra: {result}")

        return result

    async def _fetch_hashboards_fallback(self, miner: AnyMiner) -> list:
        """Fallback: fetch hashboard data directly when get_hashboards() returns empty.

        This handles cases where pyasic's expected_hashboards is None (e.g., unrecognized
        miner model/firmware combination), causing get_hashboards() to return [].
        Tries gRPC first (BOSer), then RPC (BOSMiner/legacy), building HashBoard objects
        from the raw response.
        """
        if self.logger:
            self.logger.debug(
                f"Fallback check: miner.web={miner.web}, "
                f"type={type(miner.web).__name__ if miner.web else None}, "
                f"has get_hashboards={hasattr(miner.web, 'get_hashboards') if miner.web else False}, "
                f"miner type={type(miner).__name__}"
            )

        # --- Try gRPC (BOSer firmware) ---
        grpc_result = await self._try_grpc_hashboards(miner)
        if grpc_result is not None:
            return grpc_result

        # --- Try Luci web overview (BOSMinerWebAPI) ---
        luci_result = await self._try_luci_hashboards(miner)
        if luci_result is not None:
            return luci_result

        # --- Try RPC (BOSMiner / legacy firmware) ---
        rpc_result = await self._try_rpc_hashboards(miner)
        if rpc_result is not None:
            return rpc_result

        if self.logger:
            self.logger.debug("No RPC or web interface available for fallback")
        return []

    async def _try_grpc_hashboards(self, miner: AnyMiner) -> Optional[list]:
        """Try fetching hashboard data via gRPC. Returns None if not available."""
        from pyasic.data import HashBoard

        web_api = miner.web

        # If the current web class doesn't support get_hashboards,
        # try BOSerWebAPI directly (handles pyasic misidentifying BOSer as BOSMiner)
        if web_api is None or not hasattr(web_api, "get_hashboards"):
            try:
                from pyasic.web.braiins_os.boser import BOSerWebAPI

                web_api = BOSerWebAPI(str(miner.ip))
                if self.logger:
                    self.logger.debug(f"Created direct BOSerWebAPI for {self.ip}")
            except ImportError:
                return None

        try:
            grpc_data = await web_api.get_hashboards()
            if self.logger:
                self.logger.debug(f"gRPC fallback raw response: {grpc_data}")
        except Exception as e:
            if self.logger:
                self.logger.debug(f"gRPC fallback failed: {e}")
            return None

        if not grpc_data or not grpc_data.get("hashboards"):
            return None

        grpc_boards = sorted(grpc_data["hashboards"], key=lambda x: int(x.get("id", 0)))
        hashboards = []
        for idx, board in enumerate(grpc_boards):
            hb = HashBoard(slot=idx, expected_chips=miner.expected_chips)
            hb.missing = False

            if board.get("boardTemp") is not None:
                hb.temp = int(board["boardTemp"]["degreeC"])
            if board.get("highestChipTemp") is not None:
                hb.chip_temp = int(board["highestChipTemp"]["temperature"]["degreeC"])
            if board.get("chipsCount") is not None:
                hb.chips = board["chipsCount"]
            if board.get("serialNumber") is not None:
                hb.serial_number = board["serialNumber"]
            if board.get("stats") is not None:
                try:
                    real_hr = board["stats"]["realHashrate"]["last5S"]
                    if real_hr and real_hr.get("gigahashPerSecond") is not None:
                        hb.hashrate = miner.algo.hashrate(
                            rate=float(real_hr["gigahashPerSecond"]),
                            unit=miner.algo.unit.GH,
                        )
                except (KeyError, TypeError):
                    pass
            hashboards.append(hb)

        if self.logger:
            self.logger.debug(f"gRPC fallback: found {len(hashboards)} hashboards from {self.ip}")
        return hashboards

    async def _try_luci_hashboards(self, miner: AnyMiner) -> Optional[list]:
        """Try fetching hashboard data via Luci web API (get_api_status).

        The get_api_status endpoint returns all RPC data in one call, including
        temps, devs, devdetails, fans, and summary. This is the most complete
        data source on BOSer firmware when gRPC is unavailable.
        """
        from pyasic.data import HashBoard

        if miner.web is None or not hasattr(miner.web, "get_api_status"):
            return None

        # Ensure web credentials are set (override defaults if controller has credentials)
        if self.password:
            miner.web.pwd = self.password
        if self.username:
            miner.web.username = self.username

        try:
            api_status = await miner.web.get_api_status()
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Luci get_api_status failed: {e}")
            return None

        if not api_status or not isinstance(api_status, dict):
            return None

        # Parse temps from api_status (may be "Not ready" on old firmware)
        temps_list: list = []
        try:
            temps_data = api_status["temps"][0]
            if temps_data.get("TEMPS"):
                for board in temps_data["TEMPS"]:
                    temps_list.append(
                        {
                            "chip_temp": round(board["Chip"]) if board.get("Chip") is not None else None,
                            "board_temp": round(board["Board"]) if board.get("Board") is not None else None,
                        }
                    )
            else:
                status_info = temps_data.get("STATUS", [{}])[0]
                if self.logger:
                    self.logger.debug(
                        f"Luci temps not available: {status_info.get('Msg', 'unknown')} "
                        f"(code {status_info.get('Code', '?')})"
                    )
        except (KeyError, IndexError, TypeError):
            pass

        # Parse devs from api_status
        devs_list: list = []
        try:
            for dev in api_status["devs"][0]["DEVS"]:
                devs_list.append({"mhs": dev.get("MHS 1m") or dev.get("MHS 5m") or dev.get("MHS av")})
        except (KeyError, IndexError, TypeError):
            pass

        # Parse devdetails from api_status for voltage and frequency
        details_list: list = []
        try:
            for detail in api_status["devdetails"][0]["DEVDETAILS"]:
                details_list.append(
                    {
                        "voltage": detail.get("Voltage"),
                        "frequency": detail.get("Frequency"),
                    }
                )
        except (KeyError, IndexError, TypeError):
            pass

        board_count = max(len(temps_list), len(devs_list), len(details_list))
        if board_count == 0:
            return None

        hashboards = []
        for idx in range(board_count):
            hb = HashBoard(slot=idx, expected_chips=miner.expected_chips)
            hb.missing = False

            if idx < len(temps_list):
                t = temps_list[idx]
                if t.get("chip_temp") is not None:
                    hb.chip_temp = t["chip_temp"]
                if t.get("board_temp") is not None:
                    hb.temp = t["board_temp"]

            if idx < len(devs_list):
                dev = devs_list[idx]
                mhs = dev.get("mhs")
                if mhs is not None:
                    hb.hashrate = miner.algo.hashrate(rate=mhs, unit=miner.algo.unit.MH)

            if idx < len(details_list):
                d = details_list[idx]
                if d.get("voltage") is not None:
                    hb.voltage = round(float(d["voltage"]), 2)

            hashboards.append(hb)

        if self.logger:
            self.logger.debug(f"Luci api_status: found {len(hashboards)} hashboards from {self.ip}")
        return hashboards

    async def _try_rpc_hashboards(self, miner: AnyMiner) -> Optional[list]:
        """Try fetching hashboard data via RPC. Returns None if not available."""
        from pyasic.data import HashBoard

        if miner.rpc is None:
            return None

        try:
            rpc_data = await miner.rpc.multicommand("temps", "devdetails", "devs", "stats")
        except Exception as e:
            if self.logger:
                self.logger.debug(f"RPC fallback multicommand failed: {e}")
            return None

        if self.logger:
            self.logger.debug(f"RPC fallback raw response keys: {list(rpc_data.keys())}")

        # Parse temps by positional index (BOSMiner firmware)
        temps_list: list = []
        try:
            for board in rpc_data["temps"][0]["TEMPS"]:
                temps_list.append(
                    {
                        "chip_temp": round(board["Chip"]) if board.get("Chip") is not None else None,
                        "board_temp": round(board["Board"]) if board.get("Board") is not None else None,
                    }
                )
        except (KeyError, IndexError, TypeError):
            pass

        # Parse temps from stats if temps command didn't return data (BOSer firmware).
        # The stats response contains temperature fields like temp_chip_N, temp_board_N, temp2_N, etc.
        if not temps_list:
            try:
                stats_entries = rpc_data["stats"][0]["STATS"]
                if self.logger:
                    self.logger.debug(f"RPC stats entries: {stats_entries}")
                for stat in stats_entries:
                    # Look for per-chain temperature keys found in various CGMiner-based firmwares
                    # Common patterns: temp_chip_1..N, temp_board_1..N, temp2_1..N, temp_1..N
                    chain_idx = 0
                    while True:
                        chain_num = chain_idx + 1
                        chip_temp = None
                        board_temp = None

                        # Try various known key patterns for chip temperature
                        for key in [f"temp_chip_{chain_num}", f"temp2_{chain_num}", f"temp{chain_num}"]:
                            val = stat.get(key)
                            if val is not None and float(val) > 0:
                                chip_temp = round(float(val))
                                break

                        # Try various known key patterns for board temperature
                        for key in [f"temp_board_{chain_num}", f"temp_pcb_{chain_num}", f"temp{chain_num}"]:
                            val = stat.get(key)
                            if val is not None and float(val) > 0:
                                # Avoid using the same key for both if chip_temp already used it
                                if board_temp is None:
                                    board_temp = round(float(val))

                        if chip_temp is None and board_temp is None:
                            break
                        temps_list.append({"chip_temp": chip_temp, "board_temp": board_temp})
                        chain_idx += 1
            except (KeyError, IndexError, TypeError):
                pass

        # Parse devdetails by positional index
        details_list: list = []
        try:
            for detail in rpc_data["devdetails"][0]["DEVDETAILS"]:
                details_list.append(
                    {
                        "chips": detail.get("Chips"),
                        "voltage": detail.get("Voltage"),
                        "frequency": detail.get("Frequency"),
                    }
                )
        except (KeyError, IndexError, TypeError):
            pass

        # Parse devs by positional index
        devs_list: list = []
        try:
            for dev in rpc_data["devs"][0]["DEVS"]:
                devs_list.append({"mhs": dev.get("MHS 1m") or dev.get("MHS 5m") or dev.get("MHS av")})
        except (KeyError, IndexError, TypeError):
            pass

        board_count = max(len(temps_list), len(details_list), len(devs_list))
        if board_count == 0:
            return None

        hashboards = []
        for idx in range(board_count):
            hb = HashBoard(slot=idx, expected_chips=miner.expected_chips)
            hb.missing = False

            if idx < len(temps_list):
                t = temps_list[idx]
                if t.get("chip_temp") is not None:
                    hb.chip_temp = t["chip_temp"]
                if t.get("board_temp") is not None:
                    hb.temp = t["board_temp"]

            if idx < len(details_list):
                d = details_list[idx]
                if d.get("chips") is not None:
                    hb.chips = d["chips"]
                if d.get("voltage") is not None:
                    hb.voltage = round(float(d["voltage"]), 2)

            if idx < len(devs_list):
                dev = devs_list[idx]
                mhs = dev.get("mhs")
                if mhs is not None:
                    hb.hashrate = miner.algo.hashrate(rate=mhs, unit=miner.algo.unit.MH)

            hashboards.append(hb)

        if self.logger:
            self.logger.debug(f"RPC fallback: found {len(hashboards)} hashboards from {self.ip}")
        return hashboards

    async def _derive_miner_status(self) -> Optional[bool]:
        """Derives the miner status based on hashrate and power consumption.

        Returns True if miner is ON (both hashrate > 0 and power > IDLE_WATTAGE_THRESHOLD),
        False if miner is OFF, or None if status cannot be determined.

        The IDLE_WATTAGE_THRESHOLD is set to a low value (1W) to distinguish between
        truly off (near 0W) and on (consuming power, even for low-power miners like Bitaxe).
        """
        IDLE_WATTAGE_THRESHOLD = 1  # Low threshold to work with low-power miners (e.g., Bitaxe ~13W)

        hashrate: Optional[HashRate] = await self.get_hashrate()
        wattage: Optional[Watts] = await self.get_power()

        if self.logger:
            self.logger.debug(
                f"_derive_miner_status: hashrate={hashrate}, wattage={wattage}W (threshold: {IDLE_WATTAGE_THRESHOLD}W)"
            )

        # Miner is ON only if BOTH conditions are met:
        # 1. Producing hashrate (hashrate > 0)
        # 2. Consuming power above idle threshold (wattage > IDLE_WATTAGE_THRESHOLD)
        has_hashrate = hashrate is not None and hashrate.value > 0
        has_power_consumption = wattage is not None and wattage > IDLE_WATTAGE_THRESHOLD

        if has_hashrate and has_power_consumption:
            return True

        # If we have both values but conditions aren't met, miner is OFF
        if hashrate is not None and wattage is not None:
            return False

        # Can't determine status - missing hashrate or power data
        return None

    def _normalize_hashrate_unit(
        self,
        value: float,
        unit: str,
        reference_unit: Optional[str] = None,
        decimals: int = 2,
    ) -> Tuple[float, str]:
        """Normalize a hashrate to the most suitable unit.

        If `reference_unit` is provided and recognized, the value is converted to that unit.
        Otherwise, it will be scaled to a human-friendly unit (e.g. 1000 H/s -> 1 KH/s).
        """

        unit = unit.strip()
        reference_unit = reference_unit.strip() if reference_unit else None

        # Decimal scaling is used for hashrates (k=1000).
        factors_to_hs = {
            "H/s": 1.0,
            "KH/s": 1e3,
            "MH/s": 1e6,
            "GH/s": 1e9,
            "TH/s": 1e12,
            "PH/s": 1e15,
            "EH/s": 1e18,
        }

        if unit not in factors_to_hs:
            return (round(value, decimals) if decimals is not None else value), unit

        # Convert input to H/s
        value_hs = value * factors_to_hs[unit]

        # Convert to a specific reference unit if requested
        if reference_unit and reference_unit in factors_to_hs:
            converted = value_hs / factors_to_hs[reference_unit]
            return (round(converted, decimals) if decimals is not None else converted), reference_unit

        # Choose the most suitable unit (keep value in [1, 1000) when possible)
        ordered_units = ["H/s", "KH/s", "MH/s", "GH/s", "TH/s", "PH/s", "EH/s"]
        abs_value_hs = abs(value_hs)
        chosen_unit = "H/s"

        for candidate_unit in ordered_units:
            candidate_value = abs_value_hs / factors_to_hs[candidate_unit]
            chosen_unit = candidate_unit
            if candidate_value < 1000:
                break

        converted = value_hs / factors_to_hs[chosen_unit]
        return (round(converted, decimals) if decimals is not None else converted), chosen_unit
