"""Collection of Entities for the Climate domain of the Edge Mining application."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.common import Entity, EntityId
from edge_mining.shared.interfaces.config import ClimateMonitorConfig


@dataclass
class ClimateZone(Entity):
    """Entity for a climate zone (room/area to be heated)."""

    name: str = ""
    area_sqm: float = 0.0
    climate_monitor_id: Optional[EntityId] = None

    def use_climate_monitor(self, climate_monitor_id: EntityId):
        """Assign a climate monitor to this zone."""
        self.climate_monitor_id = climate_monitor_id

    def unlink_climate_monitor(self):
        """Remove the climate monitor from this zone."""
        self.climate_monitor_id = None


@dataclass
class ClimateMonitor(Entity):
    """Entity for a climate monitor (temperature sensor adapter)."""

    name: str = ""
    adapter_type: ClimateMonitorAdapter = ClimateMonitorAdapter.HOME_ASSISTANT_API
    config: Optional[ClimateMonitorConfig] = None
    external_service_id: Optional[EntityId] = None
