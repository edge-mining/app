"""
Collection of adapters maps for the performace tracker domain
of the Edge Mining application.
"""

from typing import Dict, Optional

from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.shared.adapter_configs.performance import (
    MiningPerformanceTrackerBraiinsPoolConfig,
    MiningPerformanceTrackerDummyConfig,
    MiningPerformanceTrackerOceanConfig,
)
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.interfaces.config import MiningPerformanceTrackerConfig

MINING_PERFORMANCE_TRACKER_CONFIG_TYPE_MAP: Dict[
    MiningPerformanceTrackerAdapter, Optional[type[MiningPerformanceTrackerConfig]]
] = {
    MiningPerformanceTrackerAdapter.DUMMY: MiningPerformanceTrackerDummyConfig,
    MiningPerformanceTrackerAdapter.OCEAN: MiningPerformanceTrackerOceanConfig,
    MiningPerformanceTrackerAdapter.BRAIINS_POOL: MiningPerformanceTrackerBraiinsPoolConfig,
}

MINING_PERFORMANCE_TRACKER_TYPE_EXTERNAL_SERVICE_MAP: Dict[
    MiningPerformanceTrackerAdapter, Optional[ExternalServiceAdapter]
] = {
    MiningPerformanceTrackerAdapter.DUMMY: None,
    MiningPerformanceTrackerAdapter.OCEAN: None,
    MiningPerformanceTrackerAdapter.BRAIINS_POOL: None,
}
