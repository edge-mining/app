"""Action service for miners, energy, and optimizations."""

from typing import List, Optional

from edge_mining.application.interfaces import AdapterServiceInterface, EventBusInterface, MinerActionServiceInterface
from edge_mining.domain.common import EntityId, Watts
from edge_mining.domain.miner.aggregate_roots import Miner
from edge_mining.domain.miner.common import MinerFeatureType, MinerStatus
from edge_mining.domain.miner.events import MinerStateChangedEvent
from edge_mining.domain.miner.exceptions import (
    MinerControllerConfigurationError,
    MinerNotActiveError,
    MinerNotFoundError,
)
from edge_mining.domain.miner.ports import (
    DeviceInfoPort,
    HashboardMonitorPort,
    HashrateMonitorPort,
    InternalFanSpeedMonitorPort,
    MaxHashrateDetectionPort,
    MaxPowerDetectionPort,
    MinerRepository,
    MiningControlPort,
    OperationalMonitorPort,
    PowerControlPort,
    PowerMonitorPort,
    StatusMonitorPort,
)
from edge_mining.domain.miner.value_objects import HashRate, MinerFeature, MinerInfo, MinerLimit, MinerStateSnapshot
from edge_mining.domain.notification.ports import NotificationPort
from edge_mining.shared.logging.port import LoggerPort


class MinerActionService(MinerActionServiceInterface):
    """Handles actions on miners"""

    def __init__(
        self,
        adapter_service: AdapterServiceInterface,
        miner_repo: MinerRepository,
        event_bus: Optional[EventBusInterface] = None,
        logger: Optional[LoggerPort] = None,
    ):
        # Services
        self.adapter_service = adapter_service

        # Domains
        self.miner_repo = miner_repo

        # Infrastructure
        self._event_bus = event_bus
        self.logger = logger

    @staticmethod
    def _temp_miner_for_controller(controller_id: EntityId) -> Miner:
        """Build a throwaway miner exposing every feature for a single controller.

        Used to query a controller directly (info, limits, details) before a real
        miner has been persisted, so the adapter service can resolve its ports.
        """
        temp_features = [MinerFeature(feature_type=ft, controller_id=controller_id) for ft in MinerFeatureType]
        return Miner(
            name="Unknown",
            model="Unknown",
            hash_rate_max=None,
            power_consumption_max=None,
            active=True,
            features=temp_features,
        )

    async def _read_miner_info(self, miner: Miner) -> Optional[MinerInfo]:
        """Read device information for a miner via its DeviceInfoPort."""
        port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.DEVICE_INFO_DETECTION)
        if not port or not isinstance(port, DeviceInfoPort):
            raise MinerControllerConfigurationError(f"No device info port available for miner {miner.name}.")

        return await port.get_device_info()

    async def _read_miner_limits(self, miner: Miner) -> Optional[MinerLimit]:
        """Read max power / max hash rate for a miner via its detection ports."""
        # --- Retrieve max power limit ---
        max_power = None
        power_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.MAX_POWER_DETECTION)
        if power_port and isinstance(power_port, MaxPowerDetectionPort):
            max_power = await power_port.get_max_power()
        else:
            if self.logger:
                self.logger.warning(f"No max power detection port available for miner {miner.name}. Returning None.")

        # --- Retrieve max hash rate limit ---
        max_hash_rate = None
        hashrate_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.HASHRATE_MONITORING)
        if hashrate_port and isinstance(hashrate_port, MaxHashrateDetectionPort):
            max_hash_rate = await hashrate_port.get_max_hashrate()
        else:
            if self.logger:
                self.logger.warning(f"No hashrate monitor port available for miner {miner.name}. Returning None.")

        return MinerLimit(max_power=max_power, max_hash_rate=max_hash_rate) if max_power or max_hash_rate else None

    async def get_miner_info(self, miner_id: EntityId) -> Optional[MinerInfo]:
        """Gets the information of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting info for miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        return await self._read_miner_info(miner)

    async def get_miner_limits(self, miner_id: EntityId) -> Optional[MinerLimit]:
        """Gets the limits of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting limits for miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        return await self._read_miner_limits(miner)

    async def get_controller_info(self, controller_id: EntityId) -> Optional[MinerInfo]:
        """Gets device information directly from a controller, without a persisted miner."""
        if self.logger:
            self.logger.info(f"Getting info from controller {controller_id}")

        return await self._read_miner_info(self._temp_miner_for_controller(controller_id))

    async def get_controller_limits(self, controller_id: EntityId) -> Optional[MinerLimit]:
        """Gets max power / max hash rate directly from a controller, without a persisted miner."""
        if self.logger:
            self.logger.info(f"Getting limits from controller {controller_id}")

        return await self._read_miner_limits(self._temp_miner_for_controller(controller_id))

    async def _notify(self, notifiers: List[NotificationPort], title: str, message: str):
        """Sends a notification using the configured notifiers."""

        for notifier in notifiers:
            if notifier:
                try:
                    await notifier.send_notification(title, message)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Failed to send notification: {e}")

    # --- Miner Actions ---
    async def start_miner(self, miner_id: EntityId, notifiers: Optional[List[NotificationPort]] = None) -> bool:
        """Starts the specified miner."""
        if self.logger:
            self.logger.info(f"Starting miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        if not miner.active:
            raise MinerNotActiveError(f"Miner {miner_id} is not active and cannot be started.")

        # Try MINING_CONTROL first, then POWER_CONTROL as fallback
        mining_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.MINING_CONTROL)
        power_ctrl_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.POWER_CONTROL)

        if not mining_port and not power_ctrl_port:
            raise MinerControllerConfigurationError(f"No mining or power control available for miner {miner_id}.")

        # Get current status
        status_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.STATUS_MONITORING)
        current_status = MinerStatus.UNKNOWN
        if status_port and isinstance(status_port, StatusMonitorPort):
            current_status = await status_port.get_status()

        success = False
        if mining_port and isinstance(mining_port, MiningControlPort):
            success = await mining_port.start_mining()
        elif power_ctrl_port and isinstance(power_ctrl_port, PowerControlPort):
            success = await power_ctrl_port.power_on()

        if success:
            if self.logger:
                self.logger.info(f"Miner {miner.id} ({miner.name}) started successfully.")

            # Publish miner state changed event
            if self._event_bus:
                await self._event_bus.publish(
                    MinerStateChangedEvent(
                        miner_id=miner.id,
                        miner_name=miner.name,
                        old_status=current_status,
                        new_status=MinerStatus.ON,
                    )
                )

            if notifiers:
                await self._notify(
                    notifiers,
                    "Edge Mining Info",
                    f"Miner {miner.id} ({miner.name}) started.",
                )
        else:
            if self.logger:
                self.logger.error(f"Failed to start miner {miner.id} ({miner.name}).")

        return success

    async def stop_miner(self, miner_id: EntityId, notifiers: Optional[List[NotificationPort]] = None) -> bool:
        """Stops the specified miner."""
        if self.logger:
            self.logger.info(f"Stopping miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        if not miner.active:
            raise MinerNotActiveError(f"Miner {miner_id} is not active and cannot be stopped.")

        # Try MINING_CONTROL first, then POWER_CONTROL as fallback
        mining_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.MINING_CONTROL)
        power_ctrl_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.POWER_CONTROL)

        if not mining_port and not power_ctrl_port:
            raise MinerControllerConfigurationError(f"No mining or power control available for miner {miner_id}.")

        # Get current status
        status_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.STATUS_MONITORING)
        current_status = MinerStatus.UNKNOWN
        if status_port and isinstance(status_port, StatusMonitorPort):
            current_status = await status_port.get_status()

        success = False
        if mining_port and isinstance(mining_port, MiningControlPort):
            success = await mining_port.stop_mining()
        elif power_ctrl_port and isinstance(power_ctrl_port, PowerControlPort):
            success = await power_ctrl_port.power_off()

        if success:
            if self.logger:
                self.logger.info(f"Miner {miner.id} ({miner.name}) stopped successfully.")

            # Publish miner state changed event
            if self._event_bus:
                await self._event_bus.publish(
                    MinerStateChangedEvent(
                        miner_id=miner.id,
                        miner_name=miner.name,
                        old_status=current_status,
                        new_status=MinerStatus.OFF,
                    )
                )

            if notifiers:
                await self._notify(
                    notifiers,
                    "Edge Mining Info",
                    f"Miner {miner.id} ({miner.name}) stopped.",
                )
        else:
            if self.logger:
                self.logger.error(f"Failed to stop miner {miner.id} ({miner.name}).")

        return success

    async def get_miner_consumption(self, miner_id: EntityId) -> Optional[Watts]:
        """Gets the current power consumption of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting power consumption for miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.POWER_MONITORING)
        if not port or not isinstance(port, PowerMonitorPort):
            raise MinerControllerConfigurationError(f"No power monitor available for miner {miner_id}.")

        return await port.get_power()

    async def get_miner_hashrate(self, miner_id: EntityId) -> Optional[HashRate]:
        """Gets the current hash rate of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting hash rate for miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.HASHRATE_MONITORING)
        if not port or not isinstance(port, HashrateMonitorPort):
            raise MinerControllerConfigurationError(f"No hashrate monitor available for miner {miner_id}.")

        return await port.get_hashrate()

    async def get_miner_status(self, miner_id: EntityId) -> MinerStateSnapshot:
        """Gets the current status of the specified miner as a state snapshot."""
        if self.logger:
            self.logger.info(f"Getting status for miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        # Query individual feature ports
        status_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.STATUS_MONITORING)
        current_status = MinerStatus.UNKNOWN
        if status_port and isinstance(status_port, StatusMonitorPort):
            current_status = await status_port.get_status()

        hashrate_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.HASHRATE_MONITORING)
        current_hashrate = None
        if hashrate_port and isinstance(hashrate_port, HashrateMonitorPort):
            current_hashrate = await hashrate_port.get_hashrate()

        power_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.POWER_MONITORING)
        current_power = None
        if power_port and isinstance(power_port, PowerMonitorPort):
            current_power = await power_port.get_power()

        hashboard_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.HASHBOARD_MONITORING)
        current_hashboards = []
        if hashboard_port and isinstance(hashboard_port, HashboardMonitorPort):
            current_hashboards = await hashboard_port.get_hashboards()

        internal_fan_port = await self.adapter_service.get_miner_feature_port(
            miner, MinerFeatureType.FAN_SPEED_INTERNAL_MONITORING
        )
        internal_fan_speed = []
        if internal_fan_port and isinstance(internal_fan_port, InternalFanSpeedMonitorPort):
            internal_fan_speed = await internal_fan_port.get_internal_fan_speed()

        operational_port = await self.adapter_service.get_miner_feature_port(
            miner, MinerFeatureType.OPERATIONAL_MONITORING
        )
        blocks_found = None
        system_uptime = None
        if operational_port and isinstance(operational_port, OperationalMonitorPort):
            blocks_found = await operational_port.get_blocks_found()
            system_uptime = await operational_port.get_system_uptime()

        return MinerStateSnapshot(
            status=current_status,
            hash_rate=current_hashrate,
            power_consumption=current_power,
            hashboards=current_hashboards,
            internal_fan_speed=internal_fan_speed,
            blocks_found=blocks_found,
            system_uptime=system_uptime,
        )

    async def sync_all_miners(self, include_inactive: bool = False) -> None:
        """Synchronizes the status of all miners from their controllers.

        This method retrieves all miners from the repository and queries their
        respective controllers. Miners without a configured controller or with
        errors are logged but do not block the synchronization of other miners.

        Static configuration (model) is updated if detected from the controller.
        Runtime state (status, hashrate, power) is not persisted — it is
        captured in MinerStateSnapshot as needed by consumers.
        """
        if self.logger:
            self.logger.info("Starting synchronization of all miners status...")

        miners: List[Miner] = self.miner_repo.get_all()
        if not include_inactive:
            miners = [miner for miner in miners if miner.active]

        if not miners:
            if self.logger:
                self.logger.warning("No miners found in the repository.")
            return

        synced_count = 0
        error_count = 0

        for miner in miners:
            try:
                if self.logger:
                    self.logger.debug(f"Syncing status for miner {miner.id} ({miner.name})...")

                status_port = await self.adapter_service.get_miner_feature_port(
                    miner, MinerFeatureType.STATUS_MONITORING
                )
                if not status_port or not isinstance(status_port, StatusMonitorPort):
                    if self.logger:
                        self.logger.warning(f"No status monitor for miner {miner.id} ({miner.name}). Skipping.")
                    error_count += 1
                    continue

                current_status = await status_port.get_status()

                hashrate_port = await self.adapter_service.get_miner_feature_port(
                    miner, MinerFeatureType.HASHRATE_MONITORING
                )
                current_hashrate = None
                if hashrate_port and isinstance(hashrate_port, HashrateMonitorPort):
                    current_hashrate = await hashrate_port.get_hashrate()

                power_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.POWER_MONITORING)
                current_power = None
                if power_port and isinstance(power_port, PowerMonitorPort):
                    current_power = await power_port.get_power()

                synced_count += 1

                if self.logger:
                    self.logger.debug(
                        f"Miner {miner.id} ({miner.name}) synced: status={current_status.name}, "
                        f"power={current_power}W, hashrate={current_hashrate}"
                    )

            except MinerControllerConfigurationError as e:
                if self.logger:
                    self.logger.warning(f"Configuration error for miner {miner.id} ({miner.name}): {e}")
                error_count += 1
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error syncing miner {miner.id} ({miner.name}): {e}")
                error_count += 1

        if self.logger:
            self.logger.info(f"Miners status synchronization completed: {synced_count} synced, {error_count} errors.")

    async def get_miner_details_from_controller(self, controller_id: EntityId) -> MinerStateSnapshot:
        """Get details of a miner from its controller as a state snapshot."""
        if self.logger:
            self.logger.info(f"Getting miner details from controller {controller_id}")

        # Create a temporary miner with features for all possible feature types
        # so the adapter service can resolve the controller
        temp_miner = self._temp_miner_for_controller(controller_id)

        # Query via feature ports
        status_port = await self.adapter_service.get_miner_feature_port(temp_miner, MinerFeatureType.STATUS_MONITORING)
        current_status = MinerStatus.UNKNOWN
        if status_port and isinstance(status_port, StatusMonitorPort):
            current_status = await status_port.get_status()

        operational_port = await self.adapter_service.get_miner_feature_port(
            temp_miner, MinerFeatureType.OPERATIONAL_MONITORING
        )
        blocks_found = None
        system_uptime = None
        if operational_port and isinstance(operational_port, OperationalMonitorPort):
            blocks_found = await operational_port.get_blocks_found()
            system_uptime = await operational_port.get_system_uptime()

        hashrate_port = await self.adapter_service.get_miner_feature_port(
            temp_miner, MinerFeatureType.HASHRATE_MONITORING
        )
        current_hashrate = None
        if hashrate_port and isinstance(hashrate_port, HashrateMonitorPort):
            current_hashrate = await hashrate_port.get_hashrate()

        power_port = await self.adapter_service.get_miner_feature_port(temp_miner, MinerFeatureType.POWER_MONITORING)
        current_power = None
        if power_port and isinstance(power_port, PowerMonitorPort):
            current_power = await power_port.get_power()

        temperature_port = await self.adapter_service.get_miner_feature_port(
            temp_miner, MinerFeatureType.HASHBOARD_MONITORING
        )
        current_hashboards = []
        if temperature_port and isinstance(temperature_port, HashboardMonitorPort):
            current_hashboards = await temperature_port.get_hashboards()

        internal_fan_port = await self.adapter_service.get_miner_feature_port(
            temp_miner, MinerFeatureType.FAN_SPEED_INTERNAL_MONITORING
        )
        internal_fan_speed = []
        if internal_fan_port and isinstance(internal_fan_port, InternalFanSpeedMonitorPort):
            internal_fan_speed = await internal_fan_port.get_internal_fan_speed()

        has_no_details = all(
            (
                current_status == MinerStatus.UNKNOWN,
                current_hashrate is None,
                current_power is None,
            )
        )

        if has_no_details:
            if self.logger:
                self.logger.warning(
                    "No details retrieved from controller "
                    f"{controller_id}. Check controller connectivity and configuration."
                )
            raise MinerControllerConfigurationError(
                "Failed to retrieve details from controller "
                f"{controller_id}. Check controller connectivity and configuration."
            )

        snapshot = MinerStateSnapshot(
            status=current_status,
            hash_rate=current_hashrate,
            power_consumption=current_power,
            hashboards=current_hashboards,
            internal_fan_speed=internal_fan_speed,
            blocks_found=blocks_found,
            system_uptime=system_uptime,
        )

        if self.logger:
            self.logger.debug(f"Retrieved miner details for controller {controller_id}")

        return snapshot
