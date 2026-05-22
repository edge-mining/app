"""Collection of Value Objects for the Climate domain of the Edge Mining application."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from edge_mining.domain.common import ValueObject


@dataclass(frozen=True)
class EnvironmentStateSnapshot(ValueObject):
    """Value Object representing a point-in-time environment state reading."""

    temperature_celsius: float = 0.0
    humidity: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
