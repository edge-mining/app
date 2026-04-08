"""Action service for miners, energy, and optimizations."""

from typing import List, Optional

from edge_mining.application.interfaces import AdapterServiceInterface, EventBusInterface, MinerActionServiceInterface
from edge_mining.domain.common import EntityId, Watts
from edge_mining.domain.miner.common import MinerStatus
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.events import MinerStateChangedEvent
from edge_mining.domain.miner.exceptions import (
    MinerControllerConfigurationError,
    MinerControllerNotFoundError,
    MinerNotActiveError,
    MinerNotFoundError,
)
from edge_mining.domain.miner.ports import MinerRepository
from edge_mining.domain.miner.value_objects import HashRate, MinerStateSnapshot
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

        # Get the miner controller from the adapter service
        miner_controller = await self.adapter_service.get_miner_controller(miner)

        if not miner_controller:
            raise MinerControllerConfigurationError(f"Miner controller for miner {miner_id} is not configured.")

        # Get the current state
        current_status = await miner_controller.get_miner_status()

        # Update model if available and it has changed (static config update)
        current_model = await miner_controller.get_model()
        if current_model and miner.model != current_model:
            miner.model = current_model
            self.miner_repo.update(miner)

        success = await miner_controller.start_miner()

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

        # Get the miner controller from the adapter service
        miner_controller = await self.adapter_service.get_miner_controller(miner)

        if not miner_controller:
            raise MinerControllerConfigurationError(f"Miner controller for miner {miner_id} is not configured.")

        # Get the current state
        current_status = await miner_controller.get_miner_status()

        # Update model if available and it has changed (static config update)
        current_model = await miner_controller.get_model()
        if current_model and miner.model != current_model:
            miner.model = current_model
            self.miner_repo.update(miner)

        success = await miner_controller.stop_miner()

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

        # Get the miner controller from the adapter service
        miner_controller = await self.adapter_service.get_miner_controller(miner)

        if not miner_controller:
            raise MinerControllerConfigurationError(f"Miner controller for miner {miner_id} is not configured.")

        current_power = await miner_controller.get_miner_power()

        return current_power

    async def get_miner_hashrate(self, miner_id: EntityId) -> Optional[HashRate]:
        """Gets the current hash rate of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting hash rate for miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        # Get the miner controller from the adapter service
        miner_controller = await self.adapter_service.get_miner_controller(miner)

        if not miner_controller:
            raise MinerControllerConfigurationError(f"Miner controller for miner {miner_id} is not configured.")

        current_hashrate = await miner_controller.get_miner_hashrate()

        # Update model if available and it has changed (static config update)
        current_model = await miner_controller.get_model()
        if current_model and miner.model != current_model:
            miner.model = current_model
            self.miner_repo.update(miner)

        return current_hashrate

    async def get_miner_status(self, miner_id: EntityId) -> MinerStateSnapshot:
        """Gets the current status of the specified miner as a state snapshot."""
        if self.logger:
            self.logger.info(f"Getting status for miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        # Get the miner controller from the adapter service
        miner_controller = await self.adapter_service.get_miner_controller(miner)

        if not miner_controller:
            raise MinerControllerConfigurationError(f"Miner controller for miner {miner_id} is not configured.")

        # Query current state from controller
        current_status = await miner_controller.get_miner_status()
        current_hashrate = await miner_controller.get_miner_hashrate()
        current_power = await miner_controller.get_miner_power()

        # Update model if available and it has changed (static config update)
        current_model = await miner_controller.get_model()
        if current_model and miner.model != current_model:
            miner.model = current_model
            self.miner_repo.update(miner)

        return MinerStateSnapshot(
            status=current_status,
            hash_rate=current_hashrate,
            power_consumption=current_power,
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

                # Get the miner controller from the adapter service
                miner_controller = await self.adapter_service.get_miner_controller(miner)

                if not miner_controller:
                    if self.logger:
                        self.logger.warning(
                            f"Miner controller for miner {miner.id} ({miner.name}) is not configured. Skipping."
                        )
                    error_count += 1
                    continue

                # Query current state from controller (for logging purposes)
                current_status = await miner_controller.get_miner_status()
                current_hashrate = await miner_controller.get_miner_hashrate()
                current_power = await miner_controller.get_miner_power()

                # Update model if available and it has changed (static config update)
                current_model = await miner_controller.get_model()
                if current_model and miner.model != current_model:
                    miner.model = current_model
                    self.miner_repo.update(miner)

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

        # Create a temporary miner to hold the details retrieved from the controller
        temp_miner = Miner(
            name="Unknown",
            model="Unknown",
            hash_rate_max=None,
            power_consumption_max=None,
            controller_id=controller_id,
            active=True,
        )

        # Get the miner controller from the adapter service
        miner_controller = await self.adapter_service.get_miner_controller(temp_miner)

        if not miner_controller:
            raise MinerControllerNotFoundError(f"Controller with ID {controller_id} not found.")

        # Retrieve details from the controller
        current_status = await miner_controller.get_miner_status()
        current_hashrate = await miner_controller.get_miner_hashrate()
        current_power = await miner_controller.get_miner_power()

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
        )

        if self.logger:
            self.logger.debug(f"Retrieved miner details for controller {controller_id}")

        return snapshot
