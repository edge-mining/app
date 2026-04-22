"""
Collection of adapters configuration for the home load forecast domain
of the Edge Mining application.
"""

from dataclasses import asdict, dataclass, field

from edge_mining.domain.home_load.common import (
    EnergyLoadForecastProviderAdapter,
    EnergyLoadHistoryProviderAdapter,
)
from edge_mining.shared.interfaces.config import (
    EnergyLoadForecastProviderConfig,
    EnergyLoadHistoryProviderConfig,
)


@dataclass(frozen=True)
class EnergyLoadForecastProviderDummyConfig(EnergyLoadForecastProviderConfig):
    """
    Energy Load Forecast provider configuration. It encapsulate the configuration parameters
    to retrieve home forecast data from a dummy provider.
    """

    load_power_max: float = field(default=500.0)

    def is_valid(self, adapter_type: EnergyLoadForecastProviderAdapter) -> bool:
        """
        Check if the configuration is valid for the given adapter type.
        For Dummy Energy Load Forecast, it is always valid.
        """
        return adapter_type == EnergyLoadForecastProviderAdapter.DUMMY

    def to_dict(self) -> dict:
        """Converts the configuration object into a serializable dictionary"""
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        """Create a configuration object from a dictionary"""
        return cls(**data)


@dataclass(frozen=True)
class EnergyLoadForecastProviderNaiveLastHourConfig(EnergyLoadForecastProviderConfig):
    """Configuration for NaiveLastHour forecast provider."""

    hours_ahead: int = field(default=3)

    def is_valid(self, adapter_type: EnergyLoadForecastProviderAdapter) -> bool:
        return adapter_type == EnergyLoadForecastProviderAdapter.NAIVE_LAST_HOUR

    def to_dict(self) -> dict:
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass(frozen=True)
class EnergyLoadForecastProviderSeasonalBaselineConfig(EnergyLoadForecastProviderConfig):
    """Configuration for SeasonalBaseline forecast provider."""

    hours_ahead: int = field(default=3)
    weeks_lookback: int = field(default=4)

    def is_valid(self, adapter_type: EnergyLoadForecastProviderAdapter) -> bool:
        return adapter_type == EnergyLoadForecastProviderAdapter.SEASONAL_BASELINE

    def to_dict(self) -> dict:
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass(frozen=True)
class EnergyLoadForecastProviderStatsmodelsConfig(EnergyLoadForecastProviderConfig):
    """Configuration for Statsmodels (Holt-Winters / SARIMA) forecast provider."""

    hours_ahead: int = field(default=3)
    weeks_lookback: int = field(default=8)
    method: str = field(default="hw")  # "hw" (Holt-Winters) or "sarima"
    seasonal_periods: int = field(default=24)  # hours in a seasonal cycle

    def is_valid(self, adapter_type: EnergyLoadForecastProviderAdapter) -> bool:
        return adapter_type == EnergyLoadForecastProviderAdapter.STATSMODELS

    def to_dict(self) -> dict:
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass(frozen=True)
class EnergyLoadForecastProviderXGBoostConfig(EnergyLoadForecastProviderConfig):
    """Configuration for XGBoost forecast provider."""

    hours_ahead: int = field(default=3)
    weeks_lookback: int = field(default=8)
    n_estimators: int = field(default=100)
    max_depth: int = field(default=6)
    learning_rate: float = field(default=0.1)

    def is_valid(self, adapter_type: EnergyLoadForecastProviderAdapter) -> bool:
        return adapter_type == EnergyLoadForecastProviderAdapter.XGBOOST

    def to_dict(self) -> dict:
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass(frozen=True)
class EnergyLoadHistoryProviderHomeAssistantAPIConfig(EnergyLoadHistoryProviderConfig):
    """
    Energy Load History provider configuration. It encapsulate the configuration parameters
    to retrieve historical energy load data from Home Assistant API.
    """

    entity_power: str = field(default="")
    unit_power: str = field(default="W")

    def is_valid(self, adapter_type: EnergyLoadHistoryProviderAdapter) -> bool:
        """
        Check if the configuration is valid for the given adapter type.
        For Home Assistant API, it is always valid.
        """
        return adapter_type == EnergyLoadHistoryProviderAdapter.HOME_ASSISTANT_API

    def to_dict(self) -> dict:
        """Converts the configuration object into a serializable dictionary"""
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict):
        """Create a configuration object from a dictionary"""
        return cls(**data)
