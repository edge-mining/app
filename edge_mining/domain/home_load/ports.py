"""Collection of Ports for the Home Consumption Analytics domain of the Edge Mining application."""

from abc import ABC, abstractmethod
from typing import List, Optional

from edge_mining.domain.common import EntityId, Timestamp
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter, EnergyLoadHistoryProviderAdapter
from edge_mining.domain.home_load.entities import (
    EnergyLoadForecastProvider,
    EnergyLoadHistoryProvider,
    LoadConsumptionModel,
)
from edge_mining.domain.home_load.value_objects import HomeLoadEnergyInterval, HomeLoadPowerPoint, LoadEnergyConsumption


class EnergyLoadHistoryRepository(ABC):
    """Port for device-scoped persistence of HomeLoadPowerPoint time series.

    Every operation is scoped to a single ``LoadDevice`` via its ``device_id``:
    the repository supports multiple devices as independent, per-key streams.
    """

    @abstractmethod
    def add_power_point(self, device_id: EntityId, power_point: HomeLoadPowerPoint) -> None:
        """Append a single power point for the given device."""
        raise NotImplementedError

    @abstractmethod
    def add_power_points(self, device_id: EntityId, power_points: List[HomeLoadPowerPoint]) -> None:
        """Append multiple power points for the given device in one batch."""
        raise NotImplementedError

    @abstractmethod
    def get_power_points(self, device_id: EntityId, start: Timestamp, end: Timestamp) -> List[HomeLoadPowerPoint]:
        """Retrieve power points for ``device_id`` within the window [start, end)."""
        raise NotImplementedError

    @abstractmethod
    def get_latest_timestamp(self, device_id: EntityId) -> Optional[Timestamp]:
        """Return the newest timestamp stored for ``device_id``, or None if empty.

        Used by ingestion pipelines to resume fetching from the last known point
        and by the rule engine to evaluate staleness.
        """
        raise NotImplementedError

    @abstractmethod
    def purge_before(self, device_id: EntityId, timestamp: Timestamp) -> int:
        """Delete all power points for ``device_id`` with timestamp < ``timestamp``.

        Returns the number of rows deleted (useful for retention metrics).
        """
        raise NotImplementedError

    @abstractmethod
    def remove_power_points_by_time_range(self, device_id: EntityId, start: Timestamp, end: Timestamp) -> None:
        """Remove all power points for ``device_id`` within the window [start, end)."""
        raise NotImplementedError


class EnergyLoadHistoryProviderPort(ABC):
    """Port for retrieving historical energy load consumption data for a single device.

    The port is device-scoped: each provider instance is bound at construction
    time to the ``LoadDevice`` it covers. The underlying persistence (cache or
    local repo) is an infrastructure concern of the concrete adapter — it is
    NOT exposed on the port contract, so domain code can rely on history
    providers without knowing whether they cache, stream or query live.
    """

    def __init__(self, device_id: EntityId, provider_type: EnergyLoadHistoryProviderAdapter):
        """Initialize the EnergyLoadHistory Provider bound to ``device_id``."""
        self.device_id = device_id
        self.provider_type = provider_type

    @abstractmethod
    async def get_power_points(self, start: Timestamp, end: Timestamp) -> List[HomeLoadPowerPoint]:
        """Retrieve raw power points for this device in the window [start, end)."""
        raise NotImplementedError

    @abstractmethod
    async def get_history(self, start: Timestamp, end: Timestamp) -> List[HomeLoadEnergyInterval]:
        """Retrieve consumption intervals (typically 1h buckets) for this device."""
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
    def add(self, energy_load_history_provider: EnergyLoadHistoryProvider) -> None:
        """Adds a new energy load history provider to the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, energy_load_history_provider_id: EntityId) -> Optional[EnergyLoadHistoryProvider]:
        """Retrieves an energy load history provider by its ID."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[EnergyLoadHistoryProvider]:
        """Retrieves all energy load history providers in the repository."""
        raise NotImplementedError

    @abstractmethod
    def update(self, energy_load_history_provider: EnergyLoadHistoryProvider) -> None:
        """Updates the state of an existing energy load history provider."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, energy_load_history_provider_id: EntityId) -> None:
        """Removes an energy load history provider from the repository."""
        raise NotImplementedError

    @abstractmethod
    def get_by_external_service_id(self, external_service_id: EntityId) -> List[EnergyLoadHistoryProvider]:
        """Retrieves all energy load history providers linked to a specific external service."""
        raise NotImplementedError


class LoadConsumptionModelRepository(ABC):
    """Port for persistence of trained LoadConsumptionModel instances."""

    @abstractmethod
    def add(self, model: LoadConsumptionModel) -> None:
        """Persist a newly trained model."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, model_id: EntityId) -> Optional[LoadConsumptionModel]:
        """Retrieve a model by ID."""
        raise NotImplementedError

    @abstractmethod
    def get_active_model(
        self,
        adapter_type: EnergyLoadForecastProviderAdapter,
        device_id: Optional[EntityId] = None,
    ) -> Optional[LoadConsumptionModel]:
        """Retrieve the currently active (promoted) model for a given adapter type and device."""
        raise NotImplementedError

    @abstractmethod
    def update(self, model: LoadConsumptionModel) -> None:
        """Update an existing model (e.g. promote to active)."""
        raise NotImplementedError

    @abstractmethod
    def remove(self, model_id: EntityId) -> None:
        """Remove a model."""
        raise NotImplementedError
