"""Collection of adapters maps for the climate domain of the Edge Mining application."""

from typing import Dict, Optional

from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.shared.adapter_configs.climate import (
    ClimateMonitorDummyConfig,
    ClimateMonitorHomeAssistantConfig,
)
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.interfaces.config import ClimateMonitorConfig


CLIMATE_MONITOR_CONFIG_TYPE_MAP: Dict[ClimateMonitorAdapter, Optional[type[ClimateMonitorConfig]]] = {
    ClimateMonitorAdapter.DUMMY: ClimateMonitorDummyConfig,
    ClimateMonitorAdapter.HOME_ASSISTANT_API: ClimateMonitorHomeAssistantConfig,
}

CLIMATE_MONITOR_TYPE_EXTERNAL_SERVICE_MAP: Dict[ClimateMonitorAdapter, Optional[ExternalServiceAdapter]] = {
    ClimateMonitorAdapter.DUMMY: None,
    ClimateMonitorAdapter.HOME_ASSISTANT_API: ExternalServiceAdapter.HOME_ASSISTANT_API,
}
