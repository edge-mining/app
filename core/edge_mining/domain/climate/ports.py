"""Collection of Ports for the Climate domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import List, Optional

from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateMonitor, ClimateZone
from edge_mining.domain.climate.value_objects import EnvironmentStateSnapshot
from edge_mining.domain.common import EntityId


class ClimateMonitorPort(ABC):
    """Port for the Climate Monitor."""

    def __init__(self, climate_monitor_type: ClimateMonitorAdapter):
        """Initialize the Climate Monitor."""
        self.climate_monitor_type = climate_monitor_type

    @abstractmethod
    async def get_environment_state(self) -> Optional[EnvironmentStateSnapshot]:
        """Fetches the latest environment readings from the sensor."""
        raise NotImplementedError


class ClimateZoneRepository(ABC):
    """Port for the Climate Zone Repository."""

    @abstractmethod
    def add(self, climate_zone: ClimateZone) -> None:
        """Adds a new climate zone to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, climate_zone_id: EntityId) -> Optional[ClimateZone]:
        """Retrieves a climate zone by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[ClimateZone]:
        """Retrieves all climate zones from the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, climate_zone: ClimateZone) -> None:
        """Updates a climate zone in the repository."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, climate_zone_id: EntityId) -> None:
        """Removes a climate zone from the repository."""
        raise NotImplementedError


class ClimateMonitorRepository(ABC):
    """Port for the Climate Monitor Repository."""

    @abstractmethod
    def add(self, climate_monitor: ClimateMonitor) -> None:
        """Adds a new climate monitor to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, climate_monitor_id: EntityId) -> Optional[ClimateMonitor]:
        """Retrieves a climate monitor by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[ClimateMonitor]:
        """Retrieves all climate monitors from the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, climate_monitor: ClimateMonitor) -> None:
        """Updates a climate monitor in the repository."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, climate_monitor_id: EntityId) -> None:
        """Removes a climate monitor from the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_external_service_id(self, external_service_id: EntityId) -> List[ClimateMonitor]:
        """Retrieves climate monitors by external service ID."""
        raise NotImplementedError
