"""
Collection of adapters maps for the home load forecast domain
of the Edge Mining application.
"""

from typing import Dict, Optional

from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter, EnergyLoadHistoryProviderAdapter
from edge_mining.shared.adapter_configs.home_load import (
    EnergyLoadForecastProviderDummyConfig,
    EnergyLoadForecastProviderNaiveLastHourConfig,
    EnergyLoadForecastProviderNaivePersistenceConfig,
    EnergyLoadForecastProviderSeasonalBaselineConfig,
    EnergyLoadForecastProviderStatsmodelsConfig,
    EnergyLoadForecastProviderTypicalProfileConfig,
    EnergyLoadForecastProviderXGBoostConfig,
    EnergyLoadHistoryProviderHomeAssistantAPIConfig,
)
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.interfaces.config import EnergyLoadForecastProviderConfig, EnergyLoadHistoryProviderConfig

ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP: Dict[
    EnergyLoadForecastProviderAdapter, Optional[type[EnergyLoadForecastProviderConfig]]
] = {
    EnergyLoadForecastProviderAdapter.DUMMY: EnergyLoadForecastProviderDummyConfig,
    EnergyLoadForecastProviderAdapter.NAIVE_LAST_HOUR: EnergyLoadForecastProviderNaiveLastHourConfig,
    EnergyLoadForecastProviderAdapter.NAIVE_PERSISTENCE: EnergyLoadForecastProviderNaivePersistenceConfig,
    EnergyLoadForecastProviderAdapter.SEASONAL_BASELINE: EnergyLoadForecastProviderSeasonalBaselineConfig,
    EnergyLoadForecastProviderAdapter.STATSMODELS: EnergyLoadForecastProviderStatsmodelsConfig,
    EnergyLoadForecastProviderAdapter.TYPICAL_PROFILE: EnergyLoadForecastProviderTypicalProfileConfig,
    EnergyLoadForecastProviderAdapter.XGBOOST: EnergyLoadForecastProviderXGBoostConfig,
}

ENERGY_LOAD_FORECAST_PROVIDER_EXTERNAL_SERVICE_MAP: Dict[
    EnergyLoadForecastProviderAdapter, Optional[ExternalServiceAdapter]
] = {
    EnergyLoadForecastProviderAdapter.DUMMY: None,
    EnergyLoadForecastProviderAdapter.NAIVE_LAST_HOUR: None,
    EnergyLoadForecastProviderAdapter.NAIVE_PERSISTENCE: None,
    EnergyLoadForecastProviderAdapter.SEASONAL_BASELINE: None,
    EnergyLoadForecastProviderAdapter.STATSMODELS: None,
    EnergyLoadForecastProviderAdapter.TYPICAL_PROFILE: None,
    EnergyLoadForecastProviderAdapter.XGBOOST: None,
}

ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_TYPE_MAP: Dict[
    EnergyLoadHistoryProviderAdapter, Optional[type[EnergyLoadHistoryProviderConfig]]
] = {
    EnergyLoadHistoryProviderAdapter.DUMMY: None,
    EnergyLoadHistoryProviderAdapter.HOME_ASSISTANT_API: EnergyLoadHistoryProviderHomeAssistantAPIConfig,
}

ENERGY_LOAD_HISTORY_PROVIDER_EXTERNAL_SERVICE_MAP: Dict[
    EnergyLoadHistoryProviderAdapter, Optional[ExternalServiceAdapter]
] = {
    EnergyLoadHistoryProviderAdapter.DUMMY: None,
    EnergyLoadHistoryProviderAdapter.HOME_ASSISTANT_API: ExternalServiceAdapter.HOME_ASSISTANT_API,
}
