"""Collection of utility for Home Assistant integration."""

from enum import Enum
from typing import Dict


class SwitchDomain(Enum):
    """Enum for the different switch domains in Home Assistant."""

    SWITCH = "switch"
    LIGHT = "light"
    FAN = "fan"


class TurnService(Enum):
    """Enum for the different services in Home Assistant."""

    TURN_ON = "turn_on"
    TURN_OFF = "turn_off"


class EntityState(Enum):
    """Enum for the different states of an entity."""

    ON = "on"
    OFF = "off"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


STATE_SERVICE_MAP: Dict[str, TurnService] = {
    "on": TurnService.TURN_ON,
    "true": TurnService.TURN_ON,
    "1": TurnService.TURN_ON,
    "off": TurnService.TURN_OFF,
    "false": TurnService.TURN_OFF,
    "0": TurnService.TURN_OFF,
}

SWITCH_STATE_MAP: Dict[str, bool] = {
    "on": True,
    "true": True,
    "1": True,
    "off": False,
    "false": False,
    "0": False,
}
