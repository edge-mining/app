"""Collection of Entities for the Home Consumption Analytics domain of the Edge Mining application."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from edge_mining.domain.common import Entity, EntityId
from edge_mining.domain.home_load.common import (
    EnergyLoadForecastProviderAdapter,
    EnergyLoadHistoryProviderAdapter,
    LoadDeviceCategory,
)
from edge_mining.shared.interfaces.config import EnergyLoadForecastProviderConfig, EnergyLoadHistoryProviderConfig


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
    config: Optional[EnergyLoadHistoryProviderConfig] = None
    external_service_id: Optional[EntityId] = None


@dataclass
class LoadConsumptionModel(Entity):
    """Entity for a trained ML model used by ML-based forecast providers.

    Stores model metadata and serialized weights. The forecast provider
    adapter loads the model from this entity instead of re-training on
    every forecast call.
    """

    device_id: Optional[EntityId] = None  # None = aggregate model for all devices
    adapter_type: EnergyLoadForecastProviderAdapter = EnergyLoadForecastProviderAdapter.STATSMODELS
    trained_at: Optional[datetime] = None
    mae: Optional[float] = None  # mean absolute error on holdout
    rmse: Optional[float] = None  # root mean squared error on holdout
    samples_used: int = 0  # number of training samples
    is_active: bool = False  # promoted to production
    model_bytes: Optional[bytes] = field(default=None, repr=False)  # serialized model (pickle/joblib)
    tuning_params: Optional[dict] = field(default=None)  # best hyperparameters from Optuna tuning
    backtest_mae: Optional[float] = None  # MAE from rolling-window backtesting
    backtest_rmse: Optional[float] = None  # RMSE from rolling-window backtesting
    backtest_folds: int = 0  # number of folds used in backtesting
