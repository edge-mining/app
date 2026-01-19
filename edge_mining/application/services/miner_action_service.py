"""Action service for miners, energy, and optimizations."""

from typing import List, Optional

from edge_mining.application.interfaces import AdapterServiceInterface, MinerActionServiceInterface
from edge_mining.domain.common import EntityId, Watts
from edge_mining.domain.miner.common import MinerStatus
from edge_mining.domain.miner.entities import Miner
from edge_mining.domain.miner.exceptions import MinerControllerConfigurationError, MinerNotFoundError
from edge_mining.domain.miner.ports import MinerRepository
from edge_mining.domain.miner.value_objects import HashRate
from edge_mining.domain.notification.ports import NotificationPort
from edge_mining.shared.logging.port import LoggerPort


class MinerActionService(MinerActionServiceInterface):
    """Handles actions on miners"""

    def __init__(
        self,
        adapter_service: AdapterServiceInterface,
        miner_repo: MinerRepository,
        logger: Optional[LoggerPort] = None,
    ):
        # Services
        self.adapter_service = adapter_service

        # Domains
        self.miner_repo = miner_repo

        # Infrastructure
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

        # Get the miner controller from the adapter service
        miner_controller = self.adapter_service.get_miner_controller(miner)

        if not miner_controller:
            raise MinerControllerConfigurationError(f"Miner controller for miner {miner_id} is not configured.")

        # Update miner status using controller
        current_status = miner_controller.get_miner_status()
        current_hashrate = miner_controller.get_miner_hashrate()
        current_power = miner_controller.get_miner_power()
        miner.update_status(current_status, current_hashrate, current_power)

        # Persist the observed state
        self.miner_repo.update(miner)

        success = miner_controller.start_miner()

        if success:
            if self.logger:
                self.logger.info(f"Miner {miner.id} ({miner.name}) started successfully.")

            # Update domain state
            miner.turn_on()
            self.miner_repo.update(miner)
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

        # Get the miner controller from the adapter service
        miner_controller = self.adapter_service.get_miner_controller(miner)

        if not miner_controller:
            raise MinerControllerConfigurationError(f"Miner controller for miner {miner_id} is not configured.")

        # Update miner status using controller
        current_status = miner_controller.get_miner_status()
        current_hashrate = miner_controller.get_miner_hashrate()
        current_power = miner_controller.get_miner_power()
        miner.update_status(current_status, current_hashrate, current_power)

        # Persist the observed state
        self.miner_repo.update(miner)

        success = miner_controller.stop_miner()

        if success:
            if self.logger:
                self.logger.info(f"Miner {miner.id} ({miner.name}) stopped successfully.")

            # Update domain state
            miner.turn_off()
            self.miner_repo.update(miner)
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

    def get_miner_consumption(self, miner_id: EntityId) -> Optional[Watts]:
        """Gets the current power consumption of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting power consumption for miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        # Get the miner controller from the adapter service
        miner_controller = self.adapter_service.get_miner_controller(miner)

        if not miner_controller:
            raise MinerControllerConfigurationError(f"Miner controller for miner {miner_id} is not configured.")

        # Update miner status using controller
        current_status = miner_controller.get_miner_status()
        current_power = miner_controller.get_miner_power()
        miner.update_status(new_status=current_status, power=current_power)

        # Persist the observed state
        self.miner_repo.update(miner)

        return current_power

    def get_miner_hashrate(self, miner_id: EntityId) -> Optional[HashRate]:
        """Gets the current hash rate of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting hash rate for miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        # Get the miner controller from the adapter service
        miner_controller = self.adapter_service.get_miner_controller(miner)

        if not miner_controller:
            raise MinerControllerConfigurationError(f"Miner controller for miner {miner_id} is not configured.")

        # Update miner status using controller
        current_status = miner_controller.get_miner_status()
        current_hashrate = miner_controller.get_miner_hashrate()
        miner.update_status(new_status=current_status, hash_rate=current_hashrate)

        # Persist the observed state
        self.miner_repo.update(miner)

        return current_hashrate

    async def get_miner_status(self, miner_id: EntityId) -> MinerStatus:
        """Gets the current status of the specified miner."""
        if self.logger:
            self.logger.info(f"Getting status for miner {miner_id}")

        miner: Optional[Miner] = self.miner_repo.get_by_id(miner_id)

        if not miner:
            raise MinerNotFoundError(f"Miner with ID {miner_id} not found.")

        # Get the miner controller from the adapter service
        miner_controller = self.adapter_service.get_miner_controller(miner)

        if not miner_controller:
            raise MinerControllerConfigurationError(f"Miner controller for miner {miner_id} is not configured.")

        # Update miner status using controller
        current_status = miner_controller.get_miner_status()
        current_hashrate = miner_controller.get_miner_hashrate()
        current_power = miner_controller.get_miner_power()
        miner.update_status(current_status, current_hashrate, current_power)

        # Persist the observed state
        self.miner_repo.update(miner)

        return current_status

    async def sync_all_miners(self, include_inactive: bool = False) -> None:
        """Synchronizes the status of all miners from their controllers.

        This method retrieves all miners from the repository and updates their
        status by querying their respective controllers. Miners without a configured
        controller or with errors are logged but do not block the synchronization
        of other miners.

        This is typically called during application startup to ensure the system
        state reflects the actual hardware state.
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
                miner_controller = self.adapter_service.get_miner_controller(miner)

                if not miner_controller:
                    if self.logger:
                        self.logger.warning(
                            f"Miner controller for miner {miner.id} ({miner.name}) is not configured. Skipping."
                        )
                    error_count += 1
                    continue

                # Update miner status using controller
                current_status = miner_controller.get_miner_status()
                current_hashrate = miner_controller.get_miner_hashrate()
                current_power = miner_controller.get_miner_power()
                miner.update_status(current_status, current_hashrate, current_power)

                # Persist the observed state
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
