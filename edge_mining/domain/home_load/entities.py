"""Collection of Entities for the Home Consumption Analytics domain of the Edge Mining application."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import Entity, EntityId
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter, LoadDeviceCategory
from edge_mining.shared.interfaces.config import HomeForecastProviderConfig


@dataclass
class LoadDevice(Entity):
    """Entity for a load device."""

    name: str = ""  # e.g., "Dishwasher", "EV Charger"
    category: LoadDeviceCategory = LoadDeviceCategory.OCCASIONAL
    enabled: bool = True  # Whether the device is active in the system

    home_forecast_provider_id: Optional[EntityId] = None  # Home load forecast provider to be used


@dataclass
class EnergyLoadForecastProvider(Entity):
    """Entity for a energy load forecast provider."""

    name: str = ""
    adapter_type: EnergyLoadForecastProviderAdapter = EnergyLoadForecastProviderAdapter.DUMMY
    config: Optional[HomeForecastProviderConfig] = None
    external_service_id: Optional[EntityId] = None
