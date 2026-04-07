"""Common types for application-level events."""

from enum import Enum


class ConfigurationUpdatedEventType(Enum):
    """Enum for the different types of configuration updates."""

    ENERGY_MONITOR = "energy_monitor"
    MINER_CONTROLLER = "miner_controller"
    NOTIFIER = "notifier"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = ""


class ConfigurationAction(Enum):
    """Enum for the possible actions on a configuration entity."""

    CREATED = "created"
    UPDATED = "updated"
    REMOVED = "removed"
    UNKNOWN = ""
