"""Collection of Common Objects for the Mining Device Management domain of the Edge Mining application."""

from enum import Enum

from edge_mining.domain.common import AdapterType


class MinerStatus(Enum):
    """Enum for the different miner statuses."""

    UNKNOWN = "unknown"
    OFF = "off"
    ON = "on"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"


class MinerFeatureType(Enum):
    """Types of features that a miner can support, provided by controllers."""

    # Monitoring (read-only)
    HASHRATE_MONITORING = "hashrate_monitoring"
    POWER_MONITORING = "power_monitoring"
    STATUS_MONITORING = "status_monitoring"
    HASHBOARD_MONITORING = "hashboard_monitoring"
    INLET_TEMPERATURE_MONITORING = "inlet_temperature_monitoring"
    OUTLET_TEMPERATURE_MONITORING = "outlet_temperature_monitoring"
    FAN_SPEED_INTERNAL_MONITORING = "fan_speed_internal_monitoring"
    FAN_SPEED_EXTERNAL_MONITORING = "fan_speed_external_monitoring"
    OPERATIONAL_MONITORING = "operational_monitoring"

    # Control (write)
    MINING_CONTROL = "mining_control"
    POWER_CONTROL = "power_control"
    INTERNAL_FAN_CONTROL = "internal_fan_control"
    EXTERNAL_FAN_CONTROL = "external_fan_control"

    # Info
    MAX_POWER_DETECTION = "max_power_detection"
    MAX_HASHRATE_DETECTION = "max_hashrate_detection"
    DEVICE_INFO_DETECTION = "device_info_detection"


class MinerControllerAdapter(AdapterType):
    """Types of miner controller adapter."""

    DUMMY = "dummy"
    GENERIC_SOCKET_HOME_ASSISTANT_API = "generic_socket_home_assistant_api"
    PYASIC = "pyasic"


class MinerControllerProtocol(Enum):
    """Types of miner controller protocols."""

    WEB = "web"
    RPC = "rpc"
    SSH = "ssh"
