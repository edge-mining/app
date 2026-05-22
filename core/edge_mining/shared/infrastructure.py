"""Shared objects for infrastructure layer of Edge Mining application."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from edge_mining.application.interfaces import (
    MinerActionServiceInterface,
    AdapterServiceInterface,
    ConfigurationServiceInterface,
    EventBusInterface,
    HomeLoadHistoryServiceInterface,
    LoadForecastTrainingServiceInterface,
    OptimizationServiceInterface,
)
from edge_mining.domain.climate.ports import ClimateMonitorRepository, ClimateZoneRepository
from edge_mining.domain.energy.ports import (
    EnergyMonitorRepository,
    EnergySourceRepository,
)
from edge_mining.domain.forecast.ports import ForecastProviderRepository
from edge_mining.domain.home_load.ports import (
    EnergyLoadForecastProviderRepository,
    EnergyLoadHistoryProviderRepository,
    EnergyLoadHistoryRepository,
    HomeLoadsProfileRepository,
    LoadConsumptionModelRepository,
)
from edge_mining.domain.miner.ports import MinerControllerRepository, MinerRepository
from edge_mining.domain.notification.ports import NotifierRepository
from edge_mining.domain.optimization_unit.ports import EnergyOptimizationUnitRepository
from edge_mining.domain.performance.ports import MiningPerformanceTrackerRepository
from edge_mining.domain.policy.ports import OptimizationPolicyRepository
from edge_mining.shared.external_services.ports import ExternalServiceRepository
from edge_mining.shared.settings.ports import SettingsRepository


class ApplicationMode(str, Enum):
    """Application run mode."""

    STANDARD = "standard"
    CLI = "cli"


@dataclass(frozen=True)
class PersistenceSettings:
    """Persistence reporitory adapters"""

    energy_source_repo: EnergySourceRepository
    energy_monitor_repo: EnergyMonitorRepository
    miner_repo: MinerRepository
    miner_controller_repo: MinerControllerRepository
    forecast_provider_repo: ForecastProviderRepository
    home_profile_repo: HomeLoadsProfileRepository
    energy_load_forecast_provider_repo: EnergyLoadForecastProviderRepository
    energy_load_history_provider_repo: EnergyLoadHistoryProviderRepository
    home_load_history_repo: EnergyLoadHistoryRepository
    load_consumption_model_repo: LoadConsumptionModelRepository
    policy_repo: OptimizationPolicyRepository
    mining_performance_tracker_repo: MiningPerformanceTrackerRepository
    optimization_unit_repo: EnergyOptimizationUnitRepository
    notifier_repo: NotifierRepository
    external_service_repo: ExternalServiceRepository
    settings_repo: SettingsRepository
    climate_zone_repo: ClimateZoneRepository
    climate_monitor_repo: ClimateMonitorRepository


@dataclass(frozen=True)
class Services:
    """Service layer adapters"""

    adapter_service: AdapterServiceInterface
    optimization_service: OptimizationServiceInterface
    miner_action_service: MinerActionServiceInterface
    configuration_service: ConfigurationServiceInterface
    home_load_history_service: HomeLoadHistoryServiceInterface
    load_forecast_training_service: Optional[LoadForecastTrainingServiceInterface]
    event_bus: EventBusInterface
