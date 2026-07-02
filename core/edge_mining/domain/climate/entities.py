"""Collection of Entities for the Climate domain of the Edge Mining application."""

from dataclasses import dataclass, field
from datetime import time
from typing import List, Optional

from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.value_objects import TemperatureSlot
from edge_mining.domain.common import Entity, EntityId
from edge_mining.shared.interfaces.config import ClimateMonitorConfig


@dataclass
class ClimateZone(Entity):
    """Entity for a climate zone (room/area to be heated)."""

    name: str = ""
    area_sqm: float = 0.0
    climate_monitor_id: Optional[EntityId] = None
    temperature_schedule: List[TemperatureSlot] = field(default_factory=list)
    hysteresis_celsius: float = 0.5
    default_target_temperature: Optional[float] = None

    def use_climate_monitor(self, climate_monitor_id: EntityId):
        """Assign a climate monitor to this zone."""
        self.climate_monitor_id = climate_monitor_id

    def unlink_climate_monitor(self):
        """Remove the climate monitor from this zone."""
        self.climate_monitor_id = None

    def resolve_target_temperature(self, current_time: time) -> Optional[float]:
        """Resolve the current target temperature from the schedule.

        Iterates through schedule slots and returns the target of the first
        matching slot. If no slot matches, returns ``default_target_temperature``.
        """
        for slot in self.temperature_schedule:
            if self._time_in_slot(current_time, slot):
                return slot.target_temperature
        return self.default_target_temperature

    @staticmethod
    def _time_in_slot(current: time, slot: TemperatureSlot) -> bool:
        """Check if current time falls within a slot (supports cross-midnight)."""
        if slot.start_time <= slot.end_time:
            # Normal slot (e.g. 08:00 → 22:00)
            return slot.start_time <= current < slot.end_time
        else:
            # Cross-midnight slot (e.g. 22:00 → 06:00)
            return current >= slot.start_time or current < slot.end_time


@dataclass
class ClimateMonitor(Entity):
    """Entity for a climate monitor (temperature sensor adapter)."""

    name: str = ""
    adapter_type: ClimateMonitorAdapter = ClimateMonitorAdapter.HOME_ASSISTANT_API
    config: Optional[ClimateMonitorConfig] = None
    external_service_id: Optional[EntityId] = None
