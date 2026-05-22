"""Collection of Value Objects for the Climate domain of the Edge Mining application."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from edge_mining.domain.common import EntityId, ValueObject


@dataclass(frozen=True)
class ClimateZoneReading(ValueObject):
    """Value Object representing a point-in-time environment reading for a single zone."""

    zone_id: Optional[EntityId] = None
    zone_name: str = ""
    temperature_celsius: float = 0.0
    humidity: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ClimateStateSnapshot(ValueObject):
    """Unified climate view for the DecisionalContext.

    Carries per-zone readings and exposes aggregate properties.
    Exposes ``zones`` as a name-indexed mapping for readable rule paths
    (e.g., ``climate.zones.bedroom.temperature_celsius``).
    """

    per_zone: List[ClimateZoneReading] = field(default_factory=list)

    @property
    def zones(self) -> Dict[str, ClimateZoneReading]:
        """Zone-name-indexed map for rule engine path navigation."""
        return {z.zone_name: z for z in self.per_zone}

    def zone_by_name(self, name: str) -> Optional[ClimateZoneReading]:
        """Lookup by zone name."""
        return self.zones.get(name)

    def zone_by_id(self, zone_id: EntityId) -> Optional[ClimateZoneReading]:
        """Lookup by zone id."""
        return next((z for z in self.per_zone if z.zone_id == zone_id), None)

    @property
    def min_temperature(self) -> Optional[float]:
        """Minimum temperature across all zones."""
        if not self.per_zone:
            return None
        return min(z.temperature_celsius for z in self.per_zone)

    @property
    def max_temperature(self) -> Optional[float]:
        """Maximum temperature across all zones."""
        if not self.per_zone:
            return None
        return max(z.temperature_celsius for z in self.per_zone)

    @property
    def avg_temperature(self) -> Optional[float]:
        """Average temperature across all zones."""
        if not self.per_zone:
            return None
        return sum(z.temperature_celsius for z in self.per_zone) / len(self.per_zone)
