"""
Generic socket Home Assistant API adapter (Implementation of Port)
that controls a miner via Home Assistant's entities  of a smart socket.
"""

from typing import Dict, Optional, cast

from edge_mining.adapters.infrastructure.homeassistant.homeassistant_api import (
    ServiceHomeAssistantAPI,
)
from edge_mining.domain.common import Watts
from edge_mining.domain.miner.common import MinerStatus
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.exceptions import MinerControllerConfigurationError, MinerControllerError
from edge_mining.domain.miner.ports import MinerControlPort
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.shared.adapter_configs.miner import MinerControllerGenericSocketHomeAssistantAPIConfig
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import MinerControllerAdapterFactory
from edge_mining.shared.logging.port import LoggerPort


class GenericSocketHomeAssistantAPIMinerControllerAdapterFactory(MinerControllerAdapterFactory):
    """
    Create a factory for Generic Socket Home Assistant API Miner Controller Adapter.
    This factory is used to create instances of the adapter.
    """

    def __init__(self):
        self._miner: Optional[Miner] = None

    def from_miner(self, miner: Miner):
        """Set the miner for this controller."""
        self._miner = miner

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> MinerControlPort:
        """Create an miner controller adapter instance."""

        # Needs to have the Home Assistant API service as external_service
        if not external_service:
            raise MinerControllerError(
                "HomeAssistantAPI Service is required for Generic Socket Home Assistant API Miner Controller."
            )

        if not external_service.external_service_type == ExternalServiceAdapter.HOME_ASSISTANT_API:
            raise MinerControllerError("External service must be of type HomeAssistantAPI")

        if not isinstance(config, MinerControllerGenericSocketHomeAssistantAPIConfig):
            raise MinerControllerConfigurationError(
                "Invalid configuration for Generic Socket Home Assistant API Miner Controller."
            )

        # Get the config from the provided configuration
        miner_controller_configuration: MinerControllerGenericSocketHomeAssistantAPIConfig = config

        service_home_assistant_api = cast(ServiceHomeAssistantAPI, external_service)

        return GenericSocketHomeAssistantAPIMinerController(
            home_assistant=service_home_assistant_api,
            entity_switch=miner_controller_configuration.entity_switch,
            entity_power=miner_controller_configuration.entity_power,
            unit_power=miner_controller_configuration.unit_power,
            logger=logger,
        )


class GenericSocketHomeAssistantAPIMinerController(MinerControlPort):
    """Controls a miner via Home Assistant's entities of a smart socket."""

    def __init__(
        self,
        home_assistant: ServiceHomeAssistantAPI,
        entity_switch: str,
        entity_power: str,
        unit_power: str = "W",
        logger: Optional[LoggerPort] = None,
    ):
        # Initialize the HomeAssistant API Service
        self.home_assistant = home_assistant
        self.logger = logger

        self.entity_switch = entity_switch
        self.entity_power = entity_power
        self.unit_power = unit_power.lower()

        self._log_configuration()

    def _log_configuration(self):
        if self.logger:
            self.logger.debug(
                f"Entities Configured: Switch={self.entity_switch}, Power={self.entity_power}, Unit={self.unit_power}"
            )

    async def get_model(self) -> Optional[str]:
        """Gets the model of the miner."""

        if self.logger:
            self.logger.debug("Retrieving miner model for Home Assistant Generic Socket is not supported...")

        return None

    async def get_miner_hashrate(self) -> Optional[HashRate]:
        """
        Gets the current hash rate, if available.
        This implementation does not provides hash rate information.
        """
        return None

    async def get_miner_power(self) -> Optional[Watts]:
        """Gets the current power consumption, if available."""
        if self.logger:
            self.logger.debug("Fetching power consumption from Home Assistant...")

        state_power, _ = await self.home_assistant.get_entity_state(self.entity_power)
        power_watts = self.home_assistant.parse_power(
            state_power,
            self.unit_power,
            self.entity_power or "N/A",
        )

        if self.logger:
            self.logger.debug(f"Power consumption fetched: {power_watts}")

        return power_watts

    async def get_miner_status(self) -> MinerStatus:
        """Gets the current operational status of the miner."""
        if self.logger:
            self.logger.debug("Fetching miner status from Home Assistant...")

        state_switch, _ = await self.home_assistant.get_entity_state(self.entity_switch)
        state_status = self.home_assistant.parse_bool(state_switch, self.entity_switch or "N/A")

        state_map: Dict[Optional[bool], MinerStatus] = {
            True: MinerStatus.ON,
            False: MinerStatus.OFF,
            None: MinerStatus.UNKNOWN,
        }

        miner_status = state_map.get(state_status, MinerStatus.UNKNOWN)

        if self.logger:
            self.logger.debug(f"Miner status fetched: {miner_status}")

        return miner_status

    async def stop_miner(self) -> bool:
        """Attempts to stop the specified miner. Returns True on success request."""
        if self.logger:
            self.logger.debug("Sending stop command to miner via Home Assistant...")

        success = await self.home_assistant.set_entity_state(
            self.entity_switch,
            str(False),
        )

        if self.logger:
            self.logger.debug(f"Stop command sent. Success: {success}")

        return success

    async def start_miner(self) -> bool:
        """Attempts to start the miner. Returns True on success request."""
        if self.logger:
            self.logger.debug("Sending start command to miner via Home Assistant...")

        success = await self.home_assistant.set_entity_state(
            self.entity_switch,
            str(True),
        )

        if self.logger:
            self.logger.debug(f"Start command sent. Success: {success}")

        return success
