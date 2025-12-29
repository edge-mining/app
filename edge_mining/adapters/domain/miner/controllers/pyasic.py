"""
pyasic adapter (Implementation of Port)
that controls a miner via pyasic.
"""

from typing import Dict, Optional, Tuple, cast

import pyasic
from pyasic import AnyMiner
from pyasic.device.algorithm.hashrate import AlgoHashRate
from pyasic.rpc.base import BaseMinerRPCAPI
from pyasic.ssh.base import BaseSSH
from pyasic.web.base import BaseWebAPI

from edge_mining.adapters.utils import run_async_func
from edge_mining.domain.common import Watts
from edge_mining.domain.miner.common import MinerControllerProtocol, MinerStatus
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.exceptions import MinerControllerConfigurationError
from edge_mining.domain.miner.ports import MinerControlPort
from edge_mining.domain.miner.value_objects import HashRate
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
    ) -> MinerControlPort:
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


class PyASICMinerController(MinerControlPort):
    """Controls a miner via pyasic."""

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
            self.logger.debug(f"Entities Configured: IP={self.ip}")

    def _get_miner(self) -> None:
        """Retrieve the pyasic miner instance."""
        if self._miner is None:
            try:
                miner = run_async_func(pyasic.get_miner(self.ip))
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
                        self.logger.debug(f"Successfully retrieved miner instance from {self.ip}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to retrieve miner instance from {self.ip}: {e}")

    def get_miner_hashrate(self) -> Optional[HashRate]:
        """
        Gets the current hash rate, if available.
        """

        if self.logger:
            self.logger.debug(f"Fetching hashrate from from {self.ip}...")

        # Get pyasic miner instance
        self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return None

        miner = self._miner
        hashrate: Optional[AlgoHashRate] = run_async_func(miner.get_hashrate())
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

    def get_miner_power(self) -> Optional[Watts]:
        """Gets the current power consumption, if available."""
        if self.logger:
            self.logger.debug(f"Fetching power consumption from from {self.ip}...")

        # Get pyasic miner instance
        self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return None

        miner = self._miner
        wattage = run_async_func(miner.get_wattage())
        if wattage is None:
            if self.logger:
                self.logger.debug(f"Failed to fetch power consumption from {self.ip}...")
            return None
        power_watts = Watts(wattage)

        if self.logger:
            self.logger.debug(f"Power consumption fetched: {power_watts}")

        return power_watts

    def get_miner_status(self) -> MinerStatus:
        """Gets the current operational status of the miner."""
        if self.logger:
            self.logger.debug(f"Fetching miner status from {self.ip}...")

        # Get pyasic miner instance
        self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return MinerStatus.UNKNOWN

        miner = self._miner
        mining_state = run_async_func(miner.is_mining())

        # If miner status is not provided, we can try to derive it
        if mining_state is None:
            if self.logger:
                self.logger.debug("Mining state is not provided, deriving miner status...")
            mining_state = self._derive_miner_status()

        state_map: Dict[Optional[bool], MinerStatus] = {
            True: MinerStatus.ON,
            False: MinerStatus.OFF,
            None: MinerStatus.UNKNOWN,
        }

        miner_status = state_map.get(mining_state, MinerStatus.UNKNOWN)

        if self.logger:
            self.logger.debug(f"Miner status fetched: {miner_status}")

        return miner_status

    def stop_miner(self) -> bool:
        """Attempts to stop the specified miner. Returns True on success request."""
        if self.logger:
            self.logger.debug(f"Sending stop command to miner at {self.ip}...")

        # Get pyasic miner instance
        self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return False

        miner = self._miner
        success = run_async_func(miner.stop_mining())

        if self.logger:
            self.logger.debug(f"Stop command sent. Success: {success}")

        return success or False

    def start_miner(self) -> bool:
        """Attempts to start the miner. Returns True on success request."""
        if self.logger:
            self.logger.debug(f"Sending start command to miner at {self.ip}...")

        # Get pyasic miner instance
        self._get_miner()

        if not self._miner:
            if self.logger:
                self.logger.error(f"Failed to retrieve miner instance from {self.ip}...")
            return False

        miner = self._miner
        success = run_async_func(miner.resume_mining())

        if self.logger:
            self.logger.debug(f"Start command sent. Success: {success}")

        return success or False

    def _derive_miner_status(self) -> MinerStatus:
        """Derives the miner status based on hashrate and power consumption."""

        # We should to consider fans and mainboard power draw when checking power consumption
        IDLE_WATTAGE_THRESHOLD = 100  # Watts
        hashrate: Optional[HashRate] = self.get_miner_hashrate()
        wattage: Optional[Watts] = self.get_miner_power()

        producing_hashrate = hashrate is not None and hashrate.value > 0
        consuming_power = wattage is not None and wattage > IDLE_WATTAGE_THRESHOLD

        if producing_hashrate and consuming_power:
            miner_status = MinerStatus.ON
        else:
            miner_status = MinerStatus.OFF

        return miner_status

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
