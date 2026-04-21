"""
Collection of adapters maps for the home load forecast domain
of the Edge Mining application.
"""

from typing import Dict, Optional

from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.shared.adapter_configs.home_load import EnergyLoadForecastProviderDummyConfig
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.interfaces.config import EnergyLoadForecastProviderConfig

ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP: Dict[
    EnergyLoadForecastProviderAdapter, Optional[type[EnergyLoadForecastProviderConfig]]
] = {EnergyLoadForecastProviderAdapter.DUMMY: EnergyLoadForecastProviderDummyConfig}

ENERGY_LOAD_FORECAST_PROVIDER_EXTERNAL_SERVICE_MAP: Dict[
    EnergyLoadForecastProviderAdapter, Optional[ExternalServiceAdapter]
] = {
    EnergyLoadForecastProviderAdapter.DUMMY: None  # Dummy does not use an external service
}
