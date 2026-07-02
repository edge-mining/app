"""Collection of adapters configuration for the climate domain of the Edge Mining application."""

from dataclasses import asdict, dataclass, field

from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.shared.interfaces.config import ClimateMonitorConfig


@dataclass(frozen=True)
class ClimateMonitorDummyConfig(ClimateMonitorConfig):
    """
    Climate monitor configuration for the Dummy adapter.
    Simulates temperature/humidity readings within configurable ranges.
    """

    min_temperature: float = field(default=18.0)
    max_temperature: float = field(default=26.0)
    min_humidity: float = field(default=30.0)
    max_humidity: float = field(default=70.0)

    def is_valid(self, adapter_type: ClimateMonitorAdapter) -> bool:
        """Check if the configuration is valid for the given adapter type."""
        return adapter_type == ClimateMonitorAdapter.DUMMY

    def to_dict(self) -> dict:
        """Converts the configuration object into a serializable dictionary"""
        return {**asdict(self)}

    @classmethod
    def from_dict(cls, data: dict) -> "ClimateMonitorDummyConfig":
        """Create a configuration object from a dictionary"""
        return ClimateMonitorDummyConfig(
            min_temperature=float(data.get("min_temperature", 18.0)),
            max_temperature=float(data.get("max_temperature", 26.0)),
            min_humidity=float(data.get("min_humidity", 30.0)),
            max_humidity=float(data.get("max_humidity", 70.0)),
        )


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
