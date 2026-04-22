"""Collection of Ports for the Home Consumption Analytics domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import List, Optional

from edge_mining.domain.common import EntityId, Timestamp
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter, EnergyLoadHistoryProviderAdapter
from edge_mining.domain.home_load.entities import EnergyLoadForecastProvider
from edge_mining.domain.home_load.value_objects import HomeLoadEnergyInterval, HomeLoadPowerPoint, LoadEnergyConsumption


class EnergyLoadHistoryRepository(ABC):
    """Port for the Energy Load History Repository that operates on HomeLoadPowerPoint data."""

    @abstractmethod
    def add_power_point(self, power_point: HomeLoadPowerPoint) -> None:
        """Adds a single power point to the repository."""
        raise NotImplementedError

    @abstractmethod
    def add_power_points(self, power_points: List[HomeLoadPowerPoint]) -> None:
        """Adds multiple power points to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_power_points_by_time_range(self, start: Timestamp, end: Timestamp) -> List[HomeLoadPowerPoint]:
        """Retrieves all power points within a specific time range."""
        raise NotImplementedError

    @abstractmethod
    def remove_power_points_before(self, timestamp: Timestamp) -> None:
        """Removes all power points before the specified timestamp (for data retention)."""
        raise NotImplementedError

    @abstractmethod
    def remove_power_points_by_time_range(self, start: Timestamp, end: Timestamp) -> None:
        """Removes all power points within a specific time range."""
        raise NotImplementedError


class EnergyLoadHistoryProviderPort(ABC):
    """Port for retrieving historical energy load consumption data."""

    def __init__(self, provider_type: EnergyLoadHistoryProviderAdapter, history_repo: EnergyLoadHistoryRepository):
        """Initialize the EnergyLoadHistory Provider."""
        self.provider_type = provider_type
        self.history_repo = history_repo

    @abstractmethod
    def get_history(self, start: Timestamp, end: Timestamp) -> List[HomeLoadEnergyInterval]:
        """Retrieves a list of consumption intervals from a data source."""
        raise NotImplementedError


class EnergyLoadForecastProviderPort(ABC):
    """Port for the Energy Load Forecast Provider."""

    def __init__(self, forecast_provider_type: EnergyLoadForecastProviderAdapter):
        """Initialize the EnergyLoadForecast Provider."""
        self.forecast_provider_type = forecast_provider_type

    @abstractmethod
    def get_consumption_forecast(
        self, consumption_history: LoadEnergyConsumption, hours_ahead: int = 3
    ) -> Optional[LoadEnergyConsumption]:
        """Provide an aggregated forecast of load energy consumption based on the given history."""
        raise NotImplementedError


class HomeLoadsProfileRepository(ABC):
    """Port for the Home Loads Profile Repository."""

    @abstractmethod
    def add(self, profile: HomeLoadsProfile) -> None:
        """Adds a new home loads profile to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, profile_id: EntityId) -> Optional[HomeLoadsProfile]:
        """Retrieves an home loads profile by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[HomeLoadsProfile]:
        """Retrieves all home loads profiles in the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, profile: HomeLoadsProfile) -> None:
        """Updates the state of an existing home loads profile in the repository."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, profile_id: EntityId) -> None:
        """Removes an home loads profile from the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_energy_load_forecast_provider_id(self, provider_id: EntityId) -> List[HomeLoadsProfile]:
        """Retrieves profiles whose LoadDevices reference the given energy load forecast provider."""
        raise NotImplementedError


class EnergyLoadForecastProviderRepository(ABC):
    """Port for the Energy Load Forecast Provider Repository."""

    @abstractmethod
    def add(self, energy_load_forecast_provider: EnergyLoadForecastProvider) -> None:
        """Adds a new energy load forecast provider to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, energy_load_forecast_provider_id: EntityId) -> Optional[EnergyLoadForecastProvider]:
        """Retrieves an energy load forecast provider by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[EnergyLoadForecastProvider]:
        """Retrieves all energy load forecast providers in the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, energy_load_forecast_provider: EnergyLoadForecastProvider) -> None:
        """Updates the state of an existing energy load forecast provider in the repository."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, energy_load_forecast_provider_id: EntityId) -> None:
        """Removes an energy load forecast provider from the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_external_service_id(self, external_service_id: EntityId) -> List[EnergyLoadForecastProvider]:
        """
        Retrieves all energy load forecast providers associated with a specific external service ID.
        """
        raise NotImplementedError


class EnergyLoadHistoryProviderRepository(ABC):
    """Port for the Energy Load History Provider Repository."""

    @abstractmethod
    def add(self, energy_load_history_provider: EnergyLoadHistoryProviderPort) -> None:
        """Adds a new energy load history provider to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, energy_load_history_provider_id: EntityId) -> Optional[EnergyLoadHistoryProviderPort]:
        """Retrieves an energy load history provider by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[EnergyLoadHistoryProviderPort]:
        """Retrieves all energy load history providers in the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, energy_load_history_provider: EnergyLoadHistoryProviderPort) -> None:
        """Updates the state of an existing energy load history provider in the repository."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, energy_load_history_provider_id: EntityId) -> None:
        """Removes an energy load history provider from the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_external_service_id(self, external_service_id: EntityId) -> List[EnergyLoadHistoryProviderPort]:
        """
        Retrieves all energy load history providers associated with a specific external service ID.
        """
        raise NotImplementedError
