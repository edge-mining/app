"""Collection of Ports for the Home Consumption Analytics domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import List, Optional

from edge_mining.domain.common import EntityId, Timestamp
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import EnergyLoadHistoryProviderAdapter, HomeForecastProviderAdapter
from edge_mining.domain.home_load.entities import HomeForecastProvider
from edge_mining.domain.home_load.value_objects import ConsumptionForecast, HomeLoadEnergyInterval


class EnergyLoadHistoryProviderPort(ABC):
    """Port for retrieving historical energy load consumption data."""

    def __init__(self, provider_type: EnergyLoadHistoryProviderAdapter):
        """Initialize the EnergyLoadHistory Provider."""
        self.provider_type = provider_type

    @abstractmethod
    def get_history(self, start: Timestamp, end: Timestamp) -> List[HomeLoadEnergyInterval]:
        """Retrieves a list of consumption intervals from a data source."""
        raise NotImplementedError


class HomeForecastProviderPort(ABC):
    """Port for the Home Forecast Provider."""

    def __init__(self, provider_type: HomeForecastProviderAdapter):
        """Initialize the HomeForecast Provider."""
        self.provider_type = provider_type

    @abstractmethod
    def get_home_consumption_forecast(self, hours_ahead: int = 3) -> Optional[ConsumptionForecast]:
        """Provides an aggregated forecast of home energy consumption for the specified period."""
        raise NotImplementedError


class HomeLoadsProfileRepository(ABC):
    """Port for the Home Loads Profile Repository."""

    @abstractmethod
    def get_profile(
        self,
    ) -> Optional[HomeLoadsProfile]:  # Assuming single profile for now
        """Get the home loads profile."""
        raise NotImplementedError

    @abstractmethod
    def save_profile(self, profile: HomeLoadsProfile) -> None:
        """Save the home loads profile."""
        raise NotImplementedError


class HomeForecastProviderRepository(ABC):
    """Port for the Home Forecast Provider Repository."""

    @abstractmethod
    def add(self, home_forecast_provider: HomeForecastProvider) -> None:
        """Adds a new home forecast provider to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, home_forecast_provider_id: EntityId) -> Optional[HomeForecastProvider]:
        """Retrieves a home forecast provider by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[HomeForecastProvider]:
        """Retrieves all home forecast providers in the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, home_forecast_provider: HomeForecastProvider) -> None:
        """Updates the state of an existing home forecast provider in the repository."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, home_forecast_provider_id: EntityId) -> None:
        """Removes a home forecast provider from the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_external_service_id(self, external_service_id: EntityId) -> List[HomeForecastProvider]:
        """
        Retrieves all home forecast providers associated with a specific external service ID.
        """
        raise NotImplementedError
