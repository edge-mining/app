"""
Common classes for the Home Load domain of the Edge Mining application.
"""

from enum import Enum

from edge_mining.domain.common import AdapterType


class LoadDeviceCategory(Enum):
    """
    Categories for load devices based on consumption patterns.

    CONTROLLABLE:
        Programmable loads like washing machines or dishwashers.
        Consumption concentrated in specific time windows, and the loads have predictable patterns
        based on user-selected start times.
    CONTINUOUS:
        Always-on or semi-continuous loads like fridges or boilers.
        Repetitive pattern on hourly/daily basis. They operate almost constantly with activation/deactivation cycles.
    SEASONAL:
        Weather-dependent loads like heating or air conditioning (heating, AC).
        Heavily dependent on season and external temperature.
    OCCASIONAL:
        Infrequent or irregular usage devices (vacuum cleaner, power tools).
    """

    CONTROLLABLE = "controllable"
    CONTINUOUS = "continuous"
    SEASONAL = "seasonal"
    OCCASIONAL = "occasional"


class EnergyLoadForecastProviderAdapter(AdapterType):
    """Types of energy load forecast provider adapter."""

    DUMMY = "dummy"
    NAIVE_LAST_HOUR = "naive_last_hour"
    NAIVE_PERSISTENCE = "naive_persistence"
    SEASONAL_BASELINE = "seasonal_baseline"
    STATSMODELS = "statsmodels"
    XGBOOST = "xgboost"


class EnergyLoadHistoryProviderAdapter(AdapterType):
    """Types of energy load history provider adapter."""

    DUMMY = "dummy"
    HOME_ASSISTANT_API = "home_assistant_api"
