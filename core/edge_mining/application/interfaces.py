"""Edge Mining Application Interfaces Module"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type

from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateMonitor, ClimateZone
from edge_mining.domain.climate.ports import ClimateMonitorPort
from edge_mining.domain.common import DomainEvent, EntityId, Timestamp, Watts
from edge_mining.domain.energy.common import EnergyMonitorAdapter, EnergySourceType
from edge_mining.domain.energy.entities import EnergyMonitor, EnergySource
from edge_mining.domain.energy.ports import EnergyMonitorPort
from edge_mining.domain.energy.value_objects import Battery, Grid
from edge_mining.domain.forecast.common import ForecastProviderAdapter
from edge_mining.domain.forecast.entities import ForecastProvider
from edge_mining.domain.forecast.ports import ForecastProviderPort
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.entities import (
    EnergyLoadForecastProvider,
    EnergyLoadHistoryProvider,
    LoadConsumptionModel,
    LoadDevice,
)
from edge_mining.domain.home_load.common import (
    EnergyLoadForecastProviderAdapter,
    EnergyLoadHistoryProviderAdapter,
)
from edge_mining.domain.home_load.ports import EnergyLoadForecastProviderPort, EnergyLoadHistoryProviderPort
from edge_mining.domain.home_load.value_objects import HomeLoadPowerPoint, LoadTrainingResult
from edge_mining.domain.miner.aggregate_roots import Miner
from edge_mining.domain.miner.common import MinerControllerAdapter, MinerFeatureType
from edge_mining.domain.miner.entities import MinerController
from edge_mining.domain.miner.ports import MinerFeaturePort
from edge_mining.domain.miner.value_objects import HashRate, MinerInfo, MinerLimit, MinerStateSnapshot
from edge_mining.domain.notification.common import NotificationAdapter
from edge_mining.domain.notification.entities import Notifier
from edge_mining.domain.notification.ports import NotificationPort
from edge_mining.domain.optimization_unit.aggregate_roots import EnergyOptimizationUnit
from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.ports import MiningPerformanceTrackerPort
from edge_mining.domain.policy.aggregate_roots import OptimizationPolicy
from edge_mining.domain.policy.common import RuleType
from edge_mining.domain.policy.entities import AutomationRule
from edge_mining.domain.policy.services import RuleEngine
from edge_mining.domain.policy.value_objects import DecisionalContext, Sun
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.external_services.entities import ExternalService
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.external_services.value_objects import ExternalServiceLinkedEntities
from edge_mining.shared.interfaces.config import ClimateMonitorConfig
from edge_mining.shared.interfaces.config import (
    EnergyMonitorConfig,
    ExternalServiceConfig,
    ForecastProviderConfig,
    MinerControllerConfig,
    MiningPerformanceTrackerConfig,
    NotificationConfig,
)


class AdapterServiceInterface(ABC):
    """Base interface for all adapter services in the Edge Mining application."""

    @abstractmethod
    async def get_energy_monitor(self, energy_source: EnergySource) -> Optional[EnergyMonitorPort]:
        """Get an energy monitor adapter instance."""

    @abstractmethod
    async def get_miner_controller_adapter(self, miner: Miner, controller_id: EntityId) -> Optional[MinerFeaturePort]:
        """Get a miner controller adapter instance for a specific controller."""

    @abstractmethod
    async def build_miner_controller_adapter(
        self, miner: Miner, miner_controller: MinerController
    ) -> Optional[MinerFeaturePort]:
        """Build a fresh (uncached) miner controller adapter from a controller entity."""

    @abstractmethod
    async def get_miner_feature_port(self, miner: Miner, feature_type: MinerFeatureType) -> Optional[MinerFeaturePort]:
        """Get the adapter implementing the highest-priority active feature port for a miner."""

    @abstractmethod
    async def sync_miner_features(self, miner: Miner) -> bool:
        """Reconcile stored features with what controllers actually support.

        Returns True if any changes were made.
        """

    @abstractmethod
    async def get_all_notifiers(self) -> List[NotificationPort]:
        """Get all notifier adapter instances"""

    @abstractmethod
    async def get_notifier(self, notifier_id: EntityId) -> Optional[NotificationPort]:
        """Get a specific notifier adapter instance by ID."""

    @abstractmethod
    async def get_notifiers(self, notifier_ids: List[EntityId]) -> List[NotificationPort]:
        """Get a list of specific notifiers adapter instance by IDs."""

    @abstractmethod
    async def get_forecast_provider(self, energy_source: EnergySource) -> Optional[ForecastProviderPort]:
        """Get a forecast provider adapter instance."""

    @abstractmethod
    def get_home_load_forecast_provider(
        self, energy_load_forecast_provider_id: EntityId
    ) -> Optional[EnergyLoadForecastProviderPort]:
        """Get an home load forecast provider adapter instance."""

    @abstractmethod
    async def get_home_load_history_provider(
        self, energy_load_history_provider_id: EntityId, device_id: EntityId
    ) -> Optional[EnergyLoadHistoryProviderPort]:
        """Get an energy load history provider adapter instance."""

    @abstractmethod
    async def get_mining_performance_tracker(self, tracker_id: EntityId) -> Optional[MiningPerformanceTrackerPort]:
        """Get a mining performance tracker adapter instance."""

    @abstractmethod
    async def get_climate_monitor(self, climate_zone: ClimateZone) -> Optional[ClimateMonitorPort]:
        """Get a climate monitor adapter instance."""

    @abstractmethod
    async def get_external_service(self, external_service_id: EntityId) -> Optional[ExternalServicePort]:
        """Get a specific external service instance by ID."""

    @abstractmethod
    def get_rule_engine(self) -> Optional[RuleEngine]:
        """Get the rule engine instance."""

    @abstractmethod
    def clear_all_adapters(self):
        """Clear adapter cache"""

    @abstractmethod
    def remove_adapter(self, entity_id: EntityId):
        """Remove a specific adapter from the cache."""

    @abstractmethod
    def clear_all_services(self):
        """Clear external services cache"""


class OptimizationServiceInterface(ABC):
    """Base interface for optimization services in the Edge Mining application."""

    @abstractmethod
    async def run_all_enabled_units(self):
        """Run the optimization process for all enabled units."""

    @abstractmethod
    async def test_rules(self, rules: List[AutomationRule], context: DecisionalContext) -> bool:
        """Test a specific automation rule against a given context."""

    @abstractmethod
    async def get_decisional_context(self, optimization_unit_id: EntityId) -> Optional[DecisionalContext]:
        """Get the decisional context for a specific optimization unit."""


class HomeLoadHistoryServiceInterface(ABC):
    """Base interface for home load history ingestion and retention."""

    @abstractmethod
    async def collect_all(self, lookback_hours: int = 24) -> None:
        """Collect power points from all history providers for all enabled devices."""

    @abstractmethod
    async def collect_devices(
        self, device_ids: List[EntityId], lookback_hours: int = 24, force_full_window: bool = True
    ) -> None:
        """Collect power points for the specified devices only."""

    @abstractmethod
    async def purge_all(self, retention_days: int = 90) -> None:
        """Purge power points older than retention_days for all devices."""

    @abstractmethod
    def get_device_history(self, device_id: EntityId, start: Timestamp, end: Timestamp) -> List[HomeLoadPowerPoint]:
        """Retrieve stored power points for a device in a time window."""

    @abstractmethod
    def clear_device_history(self, device_id: EntityId) -> int:
        """Delete all stored power points for a device. Returns the number of rows deleted."""


class LoadForecastTrainingServiceInterface(ABC):
    """Base interface for ML model training and model listing."""

    @abstractmethod
    async def train_all(self, weeks_lookback: int = 8) -> None:
        """Train models for every device that has sufficient history."""

    @abstractmethod
    async def train_device(self, device_id: EntityId, weeks_lookback: int = 8) -> LoadTrainingResult:
        """Train models for a single device and return the outcome."""

    @abstractmethod
    def get_models(self, device_id: Optional[EntityId] = None) -> List[LoadConsumptionModel]:
        """Retrieve trained models, optionally filtered by device."""

    @abstractmethod
    def delete_model(self, model_id: EntityId) -> None:
        """Delete a trained model by ID."""


class MinerActionServiceInterface(ABC):
    """Base interface for miner action services in the Edge Mining application."""

    @abstractmethod
    async def start_miner(self, miner_id: EntityId, notifiers: List[NotificationPort]) -> bool:
        """Start a specific miner."""

    @abstractmethod
    async def stop_miner(self, miner_id: EntityId, notifiers: List[NotificationPort]) -> bool:
        """Stop a specific miner."""

    @abstractmethod
    async def get_miner_consumption(self, miner_id: EntityId) -> Optional[Watts]:
        """Gets the current power consumption of the specified miner."""

    @abstractmethod
    async def get_miner_hashrate(self, miner_id: EntityId) -> Optional[HashRate]:
        """Gets the current hash rate of the specified miner."""

    @abstractmethod
    async def get_miner_status(self, miner_id: EntityId) -> Optional[MinerStateSnapshot]:
        """Gets the current status of the specified miner as a state snapshot."""

    @abstractmethod
    async def get_miner_info(self, miner_id: EntityId) -> Optional[MinerInfo]:
        """Gets the information of the specified miner."""

    @abstractmethod
    async def get_miner_limits(self, miner_id: EntityId) -> Optional[MinerLimit]:
        """Gets the limits of the specified miner."""

    @abstractmethod
    async def sync_all_miners(self, include_inactive: bool = False) -> None:
        """Synchronizes the status of all miners from their controllers."""

    @abstractmethod
    async def get_miner_details_from_controller(self, controller_id: EntityId) -> Optional[MinerStateSnapshot]:
        """Get details of a miner from its controller as a state snapshot."""

    @abstractmethod
    async def get_controller_info(self, controller_id: EntityId) -> Optional[MinerInfo]:
        """Get device information directly from a controller, without a persisted miner."""

    @abstractmethod
    async def get_controller_limits(self, controller_id: EntityId) -> Optional[MinerLimit]:
        """Get max power / max hash rate directly from a controller, without a persisted miner."""

    @abstractmethod
    async def get_controller_supported_features(self, controller_id: EntityId) -> List[MinerFeatureType]:
        """Get the feature types supported by a controller, without requiring a persisted miner."""

    @abstractmethod
    async def test_miner_controller_connection(self, controller: MinerController) -> MinerStateSnapshot:
        """Test the connection of a (possibly unsaved) miner controller and return a state snapshot."""


class ConfigurationServiceInterface(ABC):
    """Base interface for configuration services in the Edge Mining application."""

    # --- Miner Management ---
    @abstractmethod
    async def add_miner(
        self,
        name: str,
        model: Optional[str] = None,
        hash_rate_max: Optional[HashRate] = None,
        power_consumption_max: Optional[Watts] = None,
        active: bool = True,
    ) -> Miner:
        """Add a miner to the system."""

    @abstractmethod
    def get_miner(self, miner_id: EntityId) -> Optional[Miner]:
        """Get a miner by its ID."""

    @abstractmethod
    def list_miners(self) -> List[Miner]:
        """List all miners in the system."""

    @abstractmethod
    async def remove_miner(self, miner_id: EntityId) -> Miner:
        """Remove a miner from the system."""

    @abstractmethod
    async def update_miner(
        self,
        miner_id: EntityId,
        name: str,
        model: Optional[str] = None,
        hash_rate_max: Optional[HashRate] = None,
        power_consumption_max: Optional[Watts] = None,
        active: bool = True,
    ) -> Miner:
        """Update a miner in the system."""

    @abstractmethod
    async def activate_miner(self, miner_id: EntityId) -> Miner:
        """Activate a miner in the system."""

    @abstractmethod
    async def deactivate_miner(self, miner_id: EntityId) -> Miner:
        """Deactivate a miner in the system."""

    @abstractmethod
    def list_miners_by_controller(self, controller_id: EntityId) -> List[Miner]:
        """List all miners associated with a specific controller."""

    @abstractmethod
    def check_miner(self, miner: Miner) -> bool:
        """Check if a miner is valid and can be used."""

    @abstractmethod
    async def add_miner_controller(
        self,
        name: str,
        adapter: MinerControllerAdapter,
        config: MinerControllerConfig,
        external_service_id: Optional[EntityId] = None,
    ) -> MinerController:
        """Add a miner controller to the system."""

    @abstractmethod
    def get_miner_controller(self, controller_id: EntityId) -> Optional[MinerController]:
        """Get a miner controller by its ID."""

    @abstractmethod
    def list_miner_controllers(self) -> List[MinerController]:
        """List all miner controllers in the system."""

    @abstractmethod
    async def unlink_miner_controller(self, miner_controller_id: EntityId) -> None:
        """Unlink a miner controller from all miners."""

    @abstractmethod
    async def remove_miner_controller(self, controller_id: EntityId) -> MinerController:
        """Remove a miner controller from the system."""

    @abstractmethod
    async def update_miner_controller(
        self,
        controller_id: EntityId,
        name: str,
        config: MinerControllerConfig,
        external_service_id: Optional[EntityId] = None,
    ) -> MinerController:
        """
        Update a miner controller in the system.
        This method updates the name and configuration only of an existing miner controller
        and avoid to change the adapter type.
        """

    @abstractmethod
    async def set_miner_controller(self, controller_id: EntityId, miner_id: EntityId) -> None:
        """Associate a controller to a miner, auto-creating features for all supported feature types."""

    @abstractmethod
    async def unlink_controller_from_miner(self, controller_id: EntityId, miner_id: EntityId) -> None:
        """Remove all features provided by a controller from a miner."""

    @abstractmethod
    async def enable_miner_feature(
        self, miner_id: EntityId, controller_id: EntityId, feature_type: MinerFeatureType
    ) -> Miner:
        """Enable a specific feature on a miner."""

    @abstractmethod
    async def disable_miner_feature(
        self, miner_id: EntityId, controller_id: EntityId, feature_type: MinerFeatureType
    ) -> Miner:
        """Disable a specific feature on a miner."""

    @abstractmethod
    async def set_miner_feature_priority(
        self, miner_id: EntityId, controller_id: EntityId, feature_type: MinerFeatureType, priority: int
    ) -> Miner:
        """Set the priority of a specific feature on a miner."""

    @abstractmethod
    def check_miner_controller(self, controller: MinerController) -> bool:
        """Check if a miner controller is valid and can be used."""

    @abstractmethod
    def get_miner_controller_config_by_type(
        self, adapter_type: MinerControllerAdapter
    ) -> Optional[type[MinerControllerConfig]]:
        """Get the configuration class for a specific miner controller adapter type."""

    @abstractmethod
    def get_miner_controller_external_service_adapter(
        self, adapter_type: MinerControllerAdapter
    ) -> Optional[ExternalServiceAdapter]:
        """Get the external service adapter type for a specific miner controller adapter type."""

    # --- Notifier Management ---
    @abstractmethod
    async def add_notifier(
        self,
        name: str,
        adapter_type: NotificationAdapter,
        config: Optional[NotificationConfig],
        external_service_id: Optional[EntityId] = None,
    ) -> Notifier:
        """Add a new notifier."""

    @abstractmethod
    def get_notifier(self, notifier_id: EntityId) -> Optional[Notifier]:
        """Get a notifier by its ID."""

    @abstractmethod
    def list_notifiers(self) -> List[Notifier]:
        """List all notifiers in the system."""

    @abstractmethod
    async def remove_notifier(self, notifier_id: EntityId) -> Notifier:
        """Remove a notifier from the system."""

    @abstractmethod
    async def update_notifier(
        self,
        notifier_id: EntityId,
        name: str,
        config: NotificationConfig,
        external_service_id: Optional[EntityId] = None,
    ) -> Notifier:
        """Update a notifier in the system."""

    @abstractmethod
    def check_notifier(self, notifier: Notifier) -> bool:
        """Check if a notifier is valid and can be used."""

    @abstractmethod
    def get_notifier_config_by_type(self, adapter_type: NotificationAdapter) -> Optional[type[NotificationConfig]]:
        """Get the configuration class for a specific notifier adapter type."""

    @abstractmethod
    def get_notifier_external_service_adapter(
        self, adapter_type: NotificationAdapter
    ) -> Optional[ExternalServiceAdapter]:
        """Get the external service adapter type for a specific notification adapter type."""

    # --- Mining Performance Tracker Management ---
    @abstractmethod
    async def add_mining_performance_tracker(
        self,
        name: str,
        adapter_type: MiningPerformanceTrackerAdapter,
        config: Optional[MiningPerformanceTrackerConfig],
        external_service_id: Optional[EntityId] = None,
    ) -> MiningPerformanceTracker:
        """Add a new mining performance tracker."""

    @abstractmethod
    def get_mining_performance_tracker(self, tracker_id: EntityId) -> Optional[MiningPerformanceTracker]:
        """Get a mining performance tracker by its ID."""

    @abstractmethod
    def list_mining_performance_trackers(self) -> List[MiningPerformanceTracker]:
        """List all mining performance trackers in the system."""

    @abstractmethod
    async def update_mining_performance_tracker(
        self,
        tracker_id: EntityId,
        name: str,
        config: MiningPerformanceTrackerConfig,
        external_service_id: Optional[EntityId] = None,
    ) -> MiningPerformanceTracker:
        """Update a mining performance tracker in the system."""

    @abstractmethod
    async def unlink_mining_performance_tracker(self, tracker_id: EntityId) -> None:
        """Detach a mining performance tracker from any optimization unit that references it."""

    @abstractmethod
    async def remove_mining_performance_tracker(self, tracker_id: EntityId) -> MiningPerformanceTracker:
        """Remove a mining performance tracker from the system."""

    @abstractmethod
    def check_mining_performance_tracker(self, tracker: MiningPerformanceTracker) -> bool:
        """Check if a mining performance tracker is valid and can be used."""

    @abstractmethod
    def get_mining_performance_tracker_config_by_type(
        self, adapter_type: MiningPerformanceTrackerAdapter
    ) -> Optional[type[MiningPerformanceTrackerConfig]]:
        """Get the configuration class for a specific tracker adapter type."""

    @abstractmethod
    def get_mining_performance_tracker_external_service_adapter(
        self, adapter_type: MiningPerformanceTrackerAdapter
    ) -> Optional[ExternalServiceAdapter]:
        """Get the external service adapter type for a specific tracker adapter type."""

    # --- Policy Management ---
    @abstractmethod
    async def create_policy(self, name: str, description: str = "") -> OptimizationPolicy:
        """Create a new policy."""

    @abstractmethod
    def get_policy(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        """Get a policy by its ID."""

    @abstractmethod
    def list_policies(self) -> List[OptimizationPolicy]:
        """List all policies in the system."""

    @abstractmethod
    async def add_rule_to_policy(
        self,
        policy_id: EntityId,
        rule_type: RuleType,
        name: str,
        priority: int,
        conditions: Dict,
        description: str = "",
    ) -> AutomationRule:
        """Add a rule to a policy."""

    @abstractmethod
    def get_policy_rules(self, policy_id: EntityId, rule_type: RuleType) -> List[AutomationRule]:
        """Get all rules of a policy."""

    @abstractmethod
    def get_policy_rule(self, policy_id: EntityId, rule_id: EntityId) -> Optional[AutomationRule]:
        """Get a rule by its ID."""

    @abstractmethod
    async def update_policy_rule(
        self,
        policy_id: EntityId,
        rule_id: EntityId,
        name: str,
        priority: int,
        enabled: bool,
        conditions: Dict,
        description: str = "",
    ) -> AutomationRule:
        """Update a rule in a policy."""

    @abstractmethod
    async def delete_policy_rule(self, policy_id: EntityId, rule_id: EntityId) -> AutomationRule:
        """Delete a rule from a policy."""

    @abstractmethod
    async def enable_policy_rule(self, policy_id: EntityId, rule_id: EntityId) -> AutomationRule:
        """Set a rule as enabled."""

    @abstractmethod
    async def disable_policy_rule(self, policy_id: EntityId, rule_id: EntityId) -> AutomationRule:
        """Set a rule as disabled."""

    @abstractmethod
    async def delete_policy(self, policy_id: EntityId) -> Optional[OptimizationPolicy]:
        """Delete a policy from the system."""

    @abstractmethod
    def check_policy(self, policy_id: EntityId) -> bool:
        """Check if a policy is valid and can be used."""

    @abstractmethod
    async def update_policy(
        self,
        policy_id: EntityId,
        name: str,
        description: str = "",
    ) -> OptimizationPolicy:
        """Update a policy in the system."""

    @abstractmethod
    async def sort_policy_rules(self, policy_id: EntityId) -> None:
        """Sort the rules of a policy by priority."""

    @abstractmethod
    def validate_rule_conditions(self, conditions: Dict) -> tuple[bool, List[str], List[str]]:
        """
        Validate rule conditions structure and semantics.

        Args:
            conditions: Dictionary representing the rule conditions

        Returns:
            Tuple[bool, List[str], List[str]]: (is_valid, syntax_errors, field_errors)
        """

    # --- Optimization Unit Management ---
    @abstractmethod
    async def create_optimization_unit(
        self,
        name: str,
        description: Optional[str] = None,
        is_enabled: bool = False,
        policy_id: Optional[EntityId] = None,
        target_miner_ids: Optional[List[EntityId]] = None,
        energy_source_id: Optional[EntityId] = None,
        performance_tracker_id: Optional[EntityId] = None,
        home_loads_profile_id: Optional[EntityId] = None,
        notifier_ids: Optional[List[EntityId]] = None,
        climate_zone_ids: Optional[List[EntityId]] = None,
    ) -> Optional[EnergyOptimizationUnit]:
        """Create an optimization unit into the system."""

    @abstractmethod
    def get_optimization_unit(self, unit_id: EntityId) -> Optional[EnergyOptimizationUnit]:
        """Get an optimization unit by its ID."""

    @abstractmethod
    def list_optimization_units(self) -> List[EnergyOptimizationUnit]:
        """List all optimization units in the system."""

    @abstractmethod
    def filter_optimization_units(
        self,
        filter_by_miners: Optional[List[EntityId]] = None,
        filter_by_energy_source: Optional[EntityId] = None,
        filter_by_policy: Optional[EntityId] = None,
        filter_by_performance_tracker: Optional[EntityId] = None,
        filter_by_notifiers: Optional[List[EntityId]] = None,
    ) -> List[EnergyOptimizationUnit]:
        """Filter optimization units based on various criteria."""

    @abstractmethod
    async def remove_optimization_unit(self, unit_id: EntityId) -> EnergyOptimizationUnit:
        """Remove an optimization unit from the system."""

    @abstractmethod
    async def update_optimization_unit(
        self,
        unit_id: EntityId,
        name: str,
        description: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        policy_id: Optional[EntityId] = None,
        target_miner_ids: Optional[List[EntityId]] = None,
        energy_source_id: Optional[EntityId] = None,
        performance_tracker_id: Optional[EntityId] = None,
        home_loads_profile_id: Optional[EntityId] = None,
        notifier_ids: Optional[List[EntityId]] = None,
        climate_zone_ids: Optional[List[EntityId]] = None,
    ) -> EnergyOptimizationUnit:
        """Update an optimization unit in the system."""

    @abstractmethod
    async def activate_optimization_unit(self, unit_id: EntityId) -> EnergyOptimizationUnit:
        """Activate an optimization unit in the system."""

    @abstractmethod
    async def deactivate_optimization_unit(self, unit_id: EntityId) -> EnergyOptimizationUnit:
        """Deactivate an optimization unit in the system."""

    @abstractmethod
    async def assign_miners_to_optimization_unit(
        self, unit_id: EntityId, miner_ids: List[EntityId]
    ) -> EnergyOptimizationUnit:
        """Assign target miners to an optimization unit."""

    @abstractmethod
    async def add_miner_to_optimization_unit(self, unit_id: EntityId, miner_id: EntityId) -> EnergyOptimizationUnit:
        """Add a miner to an optimization unit."""

    @abstractmethod
    async def remove_miner_from_optimization_unit(
        self, unit_id: EntityId, miner_id: EntityId
    ) -> EnergyOptimizationUnit:
        """Remove a miner from an optimization unit."""

    @abstractmethod
    async def assign_policy_to_optimization_unit(
        self, unit_id: EntityId, policy_id: EntityId
    ) -> EnergyOptimizationUnit:
        """Assign a policy to an optimization unit."""

    @abstractmethod
    async def assign_energy_source_to_optimization_unit(
        self, unit_id: EntityId, energy_source_id: EntityId
    ) -> EnergyOptimizationUnit:
        """Assign an energy source to an optimization unit."""

    @abstractmethod
    async def assign_performance_tracker_to_optimization_unit(
        self, unit_id: EntityId, performance_tracker_id: EntityId
    ) -> EnergyOptimizationUnit:
        """Assign a performance tracker to an optimization unit."""

    @abstractmethod
    async def assign_home_loads_profile_to_optimization_unit(
        self, unit_id: EntityId, home_loads_profile_id: Optional[EntityId]
    ) -> EnergyOptimizationUnit:
        """Assign a home loads profile to an optimization unit."""

    @abstractmethod
    async def assign_notifiers_to_optimization_unit(
        self, unit_id: EntityId, notifier_ids: List[EntityId]
    ) -> EnergyOptimizationUnit:
        """Assign notifiers to an optimization unit."""

    @abstractmethod
    async def add_notifier_to_optimization_unit(
        self, unit_id: EntityId, notifier_id: EntityId
    ) -> EnergyOptimizationUnit:
        """Add a notifier to an optimization unit."""

    @abstractmethod
    async def remove_notifier_from_optimization_unit(
        self, unit_id: EntityId, notifier_id: EntityId
    ) -> EnergyOptimizationUnit:
        """Remove a notifier from an optimization unit."""

    @abstractmethod
    def check_optimization_unit(self, optimization_unit: EnergyOptimizationUnit, strict: bool = False) -> bool:
        """Check if an optimization unit is valid and can be used."""

    # --- External Service Management ---
    @abstractmethod
    async def create_external_service(
        self,
        name: str,
        adapter_type: ExternalServiceAdapter,
        config: ExternalServiceConfig,
    ) -> ExternalService:
        """Create a new external service."""

    @abstractmethod
    def get_external_service(self, service_id: EntityId) -> Optional[ExternalService]:
        """Get an external service by its ID."""

    @abstractmethod
    def list_external_services(self) -> List[ExternalService]:
        """List all external services in the system."""

    @abstractmethod
    def get_entities_by_external_service(self, service_id: EntityId) -> ExternalServiceLinkedEntities:
        """Get entities associated with this external service"""

    @abstractmethod
    async def unlink_external_service(self, service_id: EntityId) -> None:
        """Remove the association of an external service from all entities."""

    @abstractmethod
    async def remove_external_service(self, service_id: EntityId) -> ExternalService:
        """Remove an external service from the system."""

    @abstractmethod
    async def update_external_service(
        self,
        service_id: EntityId,
        name: str,
        config: ExternalServiceConfig,
    ) -> ExternalService:
        """
        Update an external service in the system.
        This method updates the name and configuration only of an existing external service.
        """

    @abstractmethod
    def check_external_service(self, external_service: ExternalService) -> bool:
        """Check if an external service is valid and can be used."""

    @abstractmethod
    def get_external_service_config_by_type(
        self, adapter_type: ExternalServiceAdapter
    ) -> Optional[type[ExternalServiceConfig]]:
        """Get the configuration class for a specific external service adapter type."""

    # --- Energy Source Management ---
    @abstractmethod
    async def create_energy_source(
        self,
        name: str,
        source_type: EnergySourceType,
        nominal_power_max: Optional[Watts] = None,
        storage: Optional[Battery] = None,
        grid: Optional[Grid] = None,
        external_source: Optional[Watts] = None,
        energy_monitor_id: Optional[EntityId] = None,
        forecast_provider_id: Optional[EntityId] = None,
    ) -> EnergySource:
        """Create a new energy source."""

    @abstractmethod
    def get_energy_source(self, source_id: EntityId) -> Optional[EnergySource]:
        """Get an energy source by its ID."""

    @abstractmethod
    def list_energy_sources(self) -> List[EnergySource]:
        """List all energy sources in the system."""

    @abstractmethod
    async def remove_energy_source(self, source_id: EntityId) -> EnergySource:
        """Remove an energy source from the system."""

    @abstractmethod
    async def update_energy_source(
        self,
        source_id: EntityId,
        name: str,
        source_type: EnergySourceType,
        nominal_power_max: Optional[Watts] = None,
        storage: Optional[Battery] = None,
        grid: Optional[Grid] = None,
        external_source: Optional[Watts] = None,
        energy_monitor_id: Optional[EntityId] = None,
        forecast_provider_id: Optional[EntityId] = None,
    ) -> EnergySource:
        """Update an energy source in the system."""

    @abstractmethod
    def check_energy_source(self, energy_source: EnergySource) -> bool:
        """Check if an energy source is valid and can be used."""

    @abstractmethod
    async def create_energy_monitor(
        self,
        name: str,
        adapter_type: EnergyMonitorAdapter,
        config: EnergyMonitorConfig,
        external_service_id: Optional[EntityId] = None,
    ) -> EnergyMonitor:
        """Create a new energy monitor."""

    @abstractmethod
    def get_energy_monitor(self, monitor_id: EntityId) -> Optional[EnergyMonitor]:
        """Get an energy monitor by its ID."""

    @abstractmethod
    def list_energy_monitors(self) -> List[EnergyMonitor]:
        """List all energy monitors in the system."""

    @abstractmethod
    async def unlink_energy_monitor(self, monitor_id: EntityId) -> None:
        """Unlink an energy monitor from all associated energy sources."""

    @abstractmethod
    async def remove_energy_monitor(self, monitor_id: EntityId) -> EnergyMonitor:
        """Remove an energy monitor from the system."""

    @abstractmethod
    async def update_energy_monitor(
        self,
        monitor_id: EntityId,
        name: str,
        config: EnergyMonitorConfig,
        external_service_id: Optional[EntityId] = None,
    ) -> EnergyMonitor:
        """Update an energy monitor in the system."""

    @abstractmethod
    async def set_energy_monitor_to_energy_source(
        self, energy_source_id: EntityId, energy_monitor_id: EntityId
    ) -> EnergySource:
        """Set an energy monitor to an energy source."""

    @abstractmethod
    async def set_forecast_provider_to_energy_source(
        self, energy_source_id: EntityId, forecast_provider_id: EntityId
    ) -> EnergySource:
        """Set a forecast provider to an energy source."""

    @abstractmethod
    def list_energy_sources_by_monitor(self, monitor_id: EntityId) -> List[EnergySource]:
        """List all energy sources that use a specific energy monitor."""

    @abstractmethod
    def list_energy_sources_by_forecast_provider(self, forecast_provider_id: EntityId) -> List[EnergySource]:
        """List all energy sources that use a specific forecast provider."""

    @abstractmethod
    def check_energy_monitor(self, energy_monitor: EnergyMonitor) -> bool:
        """Check if an energy monitor is valid and can be used."""

    @abstractmethod
    def get_energy_monitor_config_by_type(
        self, adapter_type: EnergyMonitorAdapter
    ) -> Optional[type[EnergyMonitorConfig]]:
        """Get the configuration class for a specific energy monitor adapter type."""

    @abstractmethod
    def get_energy_monitor_external_service_adapter(
        self, adapter_type: EnergyMonitorAdapter
    ) -> Optional[ExternalServiceAdapter]:
        """Get the external service adapter type for a specific energy monitor adapter type."""

    # --- Forecast Provider Management ---
    @abstractmethod
    async def create_forecast_provider(
        self,
        name: str,
        adapter_type: ForecastProviderAdapter,
        config: ForecastProviderConfig,
        external_service_id: Optional[EntityId] = None,
    ) -> ForecastProvider:
        """Create a new forecast provider."""

    @abstractmethod
    def get_forecast_provider(self, provider_id: EntityId) -> Optional[ForecastProvider]:
        """Get a forecast provider by its ID."""

    @abstractmethod
    def list_forecast_providers(self) -> List[ForecastProvider]:
        """List all forecast providers in the system."""

    @abstractmethod
    async def remove_forecast_provider(self, provider_id: EntityId) -> ForecastProvider:
        """Remove a forecast provider from the system."""

    @abstractmethod
    async def update_forecast_provider(
        self,
        provider_id: EntityId,
        name: str,
        adapter_type: ForecastProviderAdapter,
        config: ForecastProviderConfig,
        external_service_id: Optional[EntityId] = None,
    ) -> ForecastProvider:
        """Update a forecast provider in the system."""

    @abstractmethod
    def check_forecast_provider(self, provider: ForecastProvider) -> bool:
        """Check if a forecast provider is valid and can be used."""

    # --- Home loads Management ---
    @abstractmethod
    def add_home_loads_profile(self, name: str) -> HomeLoadsProfile:
        """Add a home loads profile to the system."""

    @abstractmethod
    def get_home_loads_profile(self, profile_id: EntityId) -> Optional[HomeLoadsProfile]:
        """Get a home loads profile by its ID."""

    @abstractmethod
    def list_home_loads_profiles(self) -> List[HomeLoadsProfile]:
        """List all home loads profiles in the system."""

    @abstractmethod
    def remove_home_loads_profile(self, profile_id: EntityId) -> HomeLoadsProfile:
        """Remove a home loads profile from the system. Raises HomeLoadsProfileNotFoundError."""

    @abstractmethod
    def update_home_loads_profile(self, profile_id: EntityId, name: str) -> HomeLoadsProfile:
        """Update a home loads profile in the system. Raises HomeLoadsProfileNotFoundError."""

    @abstractmethod
    def add_load_device_to_profile(self, profile_id: EntityId, load_device: LoadDevice) -> LoadDevice:
        """Add a load device to a home loads profile. Raises HomeLoadsProfileNotFoundError."""

    @abstractmethod
    def remove_load_device_from_profile(
        self,
        profile_id: EntityId,
        device_id: EntityId,
    ) -> LoadDevice:
        """Remove a load device from a home loads profile. Raises on missing profile or device."""

    # --- Energy Load Forecast Provider Management ---
    @abstractmethod
    def add_energy_load_forecast_provider(self, provider: EnergyLoadForecastProvider) -> EnergyLoadForecastProvider:
        """Add a new energy load forecast provider."""

    @abstractmethod
    def get_energy_load_forecast_provider(self, provider_id: EntityId) -> Optional[EnergyLoadForecastProvider]:
        """Get an energy load forecast provider by ID."""

    @abstractmethod
    def list_energy_load_forecast_providers(self) -> List[EnergyLoadForecastProvider]:
        """List all energy load forecast providers."""

    @abstractmethod
    def update_energy_load_forecast_provider(self, provider: EnergyLoadForecastProvider) -> EnergyLoadForecastProvider:
        """Update an existing energy load forecast provider."""

    @abstractmethod
    def remove_energy_load_forecast_provider(self, provider_id: EntityId) -> EnergyLoadForecastProvider:
        """Remove an energy load forecast provider."""

    @abstractmethod
    def get_energy_load_forecast_provider_external_service_adapter(
        self, adapter_type: EnergyLoadForecastProviderAdapter
    ) -> Optional[ExternalServiceAdapter]:
        """Get the external service adapter type for a specific energy load forecast provider adapter type."""

    # --- Energy Load History Provider Management ---
    @abstractmethod
    def add_energy_load_history_provider(self, provider: EnergyLoadHistoryProvider) -> EnergyLoadHistoryProvider:
        """Add a new energy load history provider."""

    @abstractmethod
    def get_energy_load_history_provider(self, provider_id: EntityId) -> Optional[EnergyLoadHistoryProvider]:
        """Get an energy load history provider by ID."""

    @abstractmethod
    def list_energy_load_history_providers(self) -> List[EnergyLoadHistoryProvider]:
        """List all energy load history providers."""

    @abstractmethod
    def update_energy_load_history_provider(self, provider: EnergyLoadHistoryProvider) -> EnergyLoadHistoryProvider:
        """Update an existing energy load history provider."""

    @abstractmethod
    def remove_energy_load_history_provider(self, provider_id: EntityId) -> EnergyLoadHistoryProvider:
        """Remove an energy load history provider."""

    @abstractmethod
    def get_energy_load_history_provider_external_service_adapter(
        self, adapter_type: EnergyLoadHistoryProviderAdapter
    ) -> Optional[ExternalServiceAdapter]:
        """Get the external service adapter type for a specific energy load history provider adapter type."""

    @abstractmethod
    def get_forecast_provider_config_by_type(
        self, adapter_type: ForecastProviderAdapter
    ) -> Optional[type[ForecastProviderConfig]]:
        """Get the configuration class for a specific forecast provider adapter type."""

    @abstractmethod
    def get_forecast_provider_external_service_adapter(
        self, adapter_type: ForecastProviderAdapter
    ) -> Optional[ExternalServiceAdapter]:
        """Get the external service adapter type for a specific forecast provider adapter type."""

    # --- Settings Management ---
    @abstractmethod
    def get_all_settings(self) -> dict:
        """Get all settings."""

    @abstractmethod
    async def update_setting(self, key: str, value: Any) -> None:
        """Update a setting."""

    # --- Climate Zone Management ---

    @abstractmethod
    async def create_climate_zone(
        self, name: str, area_sqm: float, climate_monitor_id: Optional[EntityId] = None
    ) -> ClimateZone:
        """Create a new climate zone."""

    @abstractmethod
    def get_climate_zone(self, zone_id: EntityId) -> Optional[ClimateZone]:
        """Get a climate zone by its ID."""

    @abstractmethod
    def list_climate_zones(self) -> List[ClimateZone]:
        """List all climate zones."""

    @abstractmethod
    async def update_climate_zone(
        self,
        zone_id: EntityId,
        name: str,
        area_sqm: float,
        temperature_schedule: Optional[list] = None,
        hysteresis_celsius: Optional[float] = None,
        default_target_temperature: Optional[float] = None,
    ) -> ClimateZone:
        """Update an existing climate zone."""

    @abstractmethod
    async def delete_climate_zone(self, zone_id: EntityId) -> ClimateZone:
        """Delete a climate zone."""

    @abstractmethod
    async def set_climate_monitor_to_zone(self, zone_id: EntityId, monitor_id: EntityId) -> ClimateZone:
        """Assign a climate monitor to a climate zone."""

    @abstractmethod
    async def unlink_climate_monitor_from_zone(self, zone_id: EntityId) -> ClimateZone:
        """Remove the climate monitor from a climate zone."""

    # --- Climate Monitor Management ---

    @abstractmethod
    async def create_climate_monitor(
        self,
        name: str,
        adapter_type: ClimateMonitorAdapter,
        config: Optional[ClimateMonitorConfig] = None,
        external_service_id: Optional[EntityId] = None,
    ) -> ClimateMonitor:
        """Create a new climate monitor."""

    @abstractmethod
    async def update_climate_monitor(
        self,
        monitor_id: EntityId,
        name: str,
        config: Optional[ClimateMonitorConfig] = None,
        external_service_id: Optional[EntityId] = None,
    ) -> ClimateMonitor:
        """Update an existing climate monitor."""

    @abstractmethod
    async def delete_climate_monitor(self, monitor_id: EntityId) -> ClimateMonitor:
        """Delete a climate monitor."""

    @abstractmethod
    def get_climate_monitor(self, monitor_id: EntityId) -> Optional[ClimateMonitor]:
        """Get a climate monitor by its ID."""

    @abstractmethod
    def list_climate_monitors(self) -> List[ClimateMonitor]:
        """List all climate monitors."""

    @abstractmethod
    def check_climate_monitor(self, climate_monitor: ClimateMonitor) -> bool:
        """Validate a climate monitor configuration."""

    # --- Climate Zone ↔ Optimization Unit ---

    @abstractmethod
    async def add_climate_zone_to_optimization_unit(
        self, unit_id: EntityId, zone_id: EntityId
    ) -> EnergyOptimizationUnit:
        """Add a climate zone to an optimization unit."""

    @abstractmethod
    async def remove_climate_zone_from_optimization_unit(
        self, unit_id: EntityId, zone_id: EntityId
    ) -> EnergyOptimizationUnit:
        """Remove a climate zone from an optimization unit."""


class SunFactoryInterface(ABC):
    """Base interface for Sun factories in the Edge Mining application."""

    @abstractmethod
    def create_sun_for_date(self, for_date: datetime = datetime.now()) -> Sun:
        """Create a Sun object for a specific date."""


class EventBusInterface(ABC):
    """Application interface for the domain event bus."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event. Blocking handlers are executed before returning."""
        ...

    @abstractmethod
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable,
        blocking: bool = True,
    ) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: The class of the event to listen for.
            handler: Async coroutine that receives the event.
            blocking: If True, the publisher waits for the handler to complete.
                      If False, the handler is executed in fire-and-forget mode.
        """
        ...
