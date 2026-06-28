"""
Collection of adapters maps for the miner domain
of the Edge Mining application.
"""

from typing import Dict, Optional

from edge_mining.domain.miner.common import MinerControllerAdapter
from edge_mining.shared.adapter_configs.miner import (
    MinerControllerDummyConfig,
    MinerControllerGenericSocketHomeAssistantAPIConfig,
    MinerControllerPyASICConfig,
)
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.interfaces.config import MinerControllerConfig

MINER_CONTROLLER_CONFIG_TYPE_MAP: Dict[MinerControllerAdapter, Optional[type[MinerControllerConfig]]] = {
    MinerControllerAdapter.DUMMY: MinerControllerDummyConfig,
    MinerControllerAdapter.PYASIC: MinerControllerPyASICConfig,
    MinerControllerAdapter.GENERIC_SOCKET_HOME_ASSISTANT_API: MinerControllerGenericSocketHomeAssistantAPIConfig,
}

MINER_CONTROLLER_TYPE_EXTERNAL_SERVICE_MAP: Dict[MinerControllerAdapter, Optional[ExternalServiceAdapter]] = {
    MinerControllerAdapter.DUMMY: None,  # Dummy does not use an external service
    MinerControllerAdapter.PYASIC: None,  # PyASIC does not use an external service
    MinerControllerAdapter.GENERIC_SOCKET_HOME_ASSISTANT_API: ExternalServiceAdapter.HOME_ASSISTANT_API,
}
