"""Collection of Value Objects for the User Settings domain of the Edge Mining application."""

from dataclasses import dataclass

from edge_mining.domain.common import ValueObject


@dataclass(frozen=True)
class SystemConfiguration(ValueObject):
    """Value Object for the user-editable system configuration."""

    timezone: str = "Europe/Rome"
    latitude: float = 41.9028  # Rome
    longitude: float = 12.4964  # Rome
    scheduler_interval_seconds: int = 5
