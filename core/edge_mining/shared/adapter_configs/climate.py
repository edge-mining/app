"""Collection of adapters configuration for the climate domain of the Edge Mining application."""

from dataclasses import asdict, dataclass, field

from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.shared.interfaces.config import ClimateMonitorConfig


@dataclass(frozen=True)
class ClimateMonitorHomeAssistantConfig(ClimateMonitorConfig):
    """
    Climate monitor configuration for Home Assistant API.
    Encapsulates the entity IDs to retrieve climate data from Home Assistant.
    """

    entity_temperature: str = field(default="")
    entity_humidity: str = field(default="")
    unit_temperature: str = field(default="°C")

    def is_valid(self, adapter_type: ClimateMonitorAdapter) -> bool:
        """Check if the configuration is valid for the given adapter type."""
        if adapter_type != ClimateMonitorAdapter.HOME_ASSISTANT_API:
            return False
        # At least temperature entity is required
        return bool(self.entity_temperature)

    def to_dict(self) -> dict:
        """Converts the configuration object into a serializable dictionary"""
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict) -> "ClimateMonitorHomeAssistantConfig":
        """Create a configuration object from a dictionary"""
        return ClimateMonitorHomeAssistantConfig(
            entity_temperature=data.get("entity_temperature", ""),
            entity_humidity=data.get("entity_humidity", ""),
            unit_temperature=data.get("unit_temperature", "°C"),
        )
