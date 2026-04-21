"""Collection of Entities for the Home Consumption Analytics domain of the Edge Mining application."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import Entity, EntityId
from edge_mining.domain.home_load.common import (
    EnergyLoadForecastProviderAdapter,
    EnergyLoadHistoryProviderAdapter,
    LoadDeviceCategory,
)
from edge_mining.shared.interfaces.config import EnergyLoadForecastProviderConfig


@dataclass
class LoadDevice(Entity):
    """Entity for a load device."""

    name: str = ""  # e.g., "Dishwasher", "EV Charger"
    category: LoadDeviceCategory = LoadDeviceCategory.OCCASIONAL
    enabled: bool = True  # Whether the device is active in the system

    energy_load_forecast_provider_id: Optional[EntityId] = None  # Energy load forecast provider to be used
    energy_load_history_provider_id: Optional[EntityId] = None  # Energy load history provider to be used


@dataclass
class EnergyLoadForecastProvider(Entity):
    """Entity for a energy load forecast provider."""

    name: str = ""
    adapter_type: EnergyLoadForecastProviderAdapter = EnergyLoadForecastProviderAdapter.DUMMY
    config: Optional[EnergyLoadForecastProviderConfig] = None
    external_service_id: Optional[EntityId] = None


@dataclass
class EnergyLoadHistoryProvider(Entity):
    """Entity for an energy load history provider."""

    name: str = ""
    adapter_type: EnergyLoadHistoryProviderAdapter = EnergyLoadHistoryProviderAdapter.DUMMY
    config: Optional[EnergyLoadForecastProviderConfig] = None
    external_service_id: Optional[EntityId] = None
