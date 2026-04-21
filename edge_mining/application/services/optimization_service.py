"""
The Optimization Runner Service is responsible for running the optimization process.
It is responsible for:
- Evaluating the policy
- Getting the current energy state
- Getting the forecast
- Executing the decision
"""

import asyncio
from typing import Dict, List, Optional

from edge_mining.application.interfaces import (
    AdapterServiceInterface,
    EventBusInterface,
    OptimizationServiceInterface,
    SunFactoryInterface,
)
from edge_mining.domain.common import EntityId
from edge_mining.domain.energy.entities import EnergySource
from edge_mining.domain.energy.events import EnergyStateSnapshotUpdatedEvent
from edge_mining.domain.energy.ports import EnergyMonitorPort, EnergySourceRepository
from edge_mining.domain.energy.value_objects import EnergyStateSnapshot
from edge_mining.domain.forecast.aggregate_root import Forecast
from edge_mining.domain.forecast.ports import ForecastProviderPort
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.ports import HomeForecastProviderPort, HomeLoadsProfileRepository
from edge_mining.domain.home_load.value_objects import ConsumptionForecast
from edge_mining.domain.miner.aggregate_roots import Miner
from edge_mining.domain.miner.common import MinerFeatureType, MinerStatus
from edge_mining.domain.miner.events import MinerStateChangedEvent
from edge_mining.domain.miner.exceptions import MinerError
from edge_mining.domain.miner.ports import (
    HashboardMonitorPort,
    HashrateMonitorPort,
    InternalFanSpeedMonitorPort,
    MinerFeaturePort,
    MinerRepository,
    MiningControlPort,
    OperationalMonitorPort,
    PowerControlPort,
    PowerMonitorPort,
    StatusMonitorPort,
)
from edge_mining.domain.miner.value_objects import HashRate, MinerStateSnapshot
from edge_mining.domain.notification.ports import NotificationPort
from edge_mining.domain.optimization_unit.aggregate_roots import EnergyOptimizationUnit
from edge_mining.domain.optimization_unit.events import RuleEngagedEvent
from edge_mining.domain.optimization_unit.exceptions import OptimizationUnitNotFoundError
from edge_mining.domain.optimization_unit.ports import EnergyOptimizationUnitRepository
from edge_mining.domain.performance.ports import MiningPerformanceTrackerPort
from edge_mining.domain.policy.aggregate_roots import OptimizationPolicy
from edge_mining.domain.policy.common import MiningDecision
from edge_mining.domain.policy.entities import AutomationRule
from edge_mining.domain.policy.events import DecisionalContextUpdatedEvent
from edge_mining.domain.policy.exceptions import PolicyError, RuleEngineError, RuleEvaluationError, RuleLoadError
from edge_mining.domain.policy.ports import OptimizationPolicyRepository
from edge_mining.domain.policy.services import RuleEngine
from edge_mining.domain.policy.value_objects import DecisionalContext, Sun
from edge_mining.shared.logging.port import LoggerPort


class OptimizationService(OptimizationServiceInterface):
    """Service for the optimization process."""

    def __init__(
        self,
        optimization_unit_repo: EnergyOptimizationUnitRepository,
        energy_source_repo: EnergySourceRepository,
        policy_repo: OptimizationPolicyRepository,
        miner_repo: MinerRepository,
        home_loads_repo: HomeLoadsProfileRepository,
        adapter_service: AdapterServiceInterface,
        sun_factory: SunFactoryInterface,
        event_bus: Optional[EventBusInterface] = None,
        logger: Optional[LoggerPort] = None,
    ):
        # Domains

        # Repositories
        self.optimization_unit_repo = optimization_unit_repo
        self.energy_source_repo = energy_source_repo
        self.policy_repo = policy_repo
        self.miner_repo = miner_repo
        self.home_loads_repo = home_loads_repo

        # Infrastructure
        self.sun_factory = sun_factory
        self.adapter_service = adapter_service
        self._event_bus = event_bus
        self.logger = logger

    async def _notify_unit(self, notifiers: List[NotificationPort], title: str, message: str):
        """Notify the unit."""
        if not notifiers:
            return

        for notifier in notifiers:
            try:
                success = await notifier.send_notification(title, message)
                if not success:
                    if self.logger:
                        self.logger.warning(f"Notifier {type(notifier).__name__} reported failure for: {title}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to send notification via {type(notifier).__name__}: {e}")

    async def test_rules(self, rules: List[AutomationRule], decisional_context: DecisionalContext) -> bool:
        """Test a specific automation rule against a given context."""
        # Create the rule engine instance
        rule_engine = self.adapter_service.get_rule_engine()
        if not rule_engine:
            if self.logger:
                self.logger.error("Rule engine not available. Cannot process policy.")
            raise RuleEngineError("Rule engine not available. Cannot process policy.")

        if not rules:
            if self.logger:
                self.logger.error("No rules provided for testing.")
            raise RuleLoadError("No rules provided for testing.")

        # Check if at least one rule is enabled
        active_rules = any([rule.enabled for rule in rules])
        if not active_rules:
            if self.logger:
                self.logger.error("At least one rule must be enabled.")
            raise RuleEvaluationError("At least one rule must be enabled.")

        # Load rules into rule engine
        rule_engine.load_rules(rules)

        # Evaluate the rules in the rule engine
        return rule_engine.evaluate(decisional_context)

    async def get_decisional_context(self, optimization_unit_id: EntityId) -> Optional[DecisionalContext]:
        """Get the decisional context for a specific optimization unit."""
        optimization_unit = self.optimization_unit_repo.get_by_id(optimization_unit_id)
        if not optimization_unit:
            if self.logger:
                self.logger.error(f"Optimization unit ID {optimization_unit_id} not found.")
            raise OptimizationUnitNotFoundError(f"Optimization unit ID {optimization_unit_id} not found.")

        # --- Energy Source  ---
        energy_source: Optional[EnergySource] = None
        if optimization_unit.energy_source_id:
            energy_source = self.energy_source_repo.get_by_id(optimization_unit.energy_source_id)
        if not energy_source:
            if self.logger:
                self.logger.error(
                    f"Energy source for optimization unit '{optimization_unit.name}' "
                    f"(Config ID: {optimization_unit.energy_source_id}) not found "
                    f"or failed to initialize. Skipping optimization unit."
                )

        # --- Energy Monitor ---
        energy_monitor: Optional[EnergyMonitorPort] = None
        if energy_source and energy_source.energy_monitor_id:
            energy_monitor = await self.adapter_service.get_energy_monitor(energy_source)
            if not energy_monitor:
                if self.logger:
                    self.logger.error(
                        f"Energy monitor for energy source '{energy_source.name}' "
                        f"(Config ID: {energy_source.energy_monitor_id}) not found. "
                        f"Skipping optimization unit."
                    )

        # --- Forecast Provider ---
        forecast_provider: Optional[ForecastProviderPort] = None
        if energy_source and energy_source.forecast_provider_id:
            forecast_provider = await self.adapter_service.get_forecast_provider(energy_source)
            # Forecast is optional, so log a warning if it's missing but continue
            if not forecast_provider:
                if self.logger:
                    self.logger.warning(
                        f"Forecast provider for energy source '{energy_source.name}' "
                        f"(Config ID: {energy_source.forecast_provider_id}) not found. "
                        f"Skipping optimization unit."
                    )

        # --- Home Loads ---
        home_loads_profile: Optional[HomeLoadsProfile] = None
        if optimization_unit.home_loads_profile:
            profile = self.home_loads_repo.get_by_id(optimization_unit.home_loads_profile)
            if profile:
                home_loads_profile = profile

        # --- Home Loads Forecast Provider ---
        home_forecast_providers: Dict[EntityId, HomeForecastProviderPort] = {}
        if home_loads_profile and home_loads_profile.devices:
            for load_device in home_loads_profile.devices:
                if load_device.home_forecast_provider_id:
                    home_forecast_provider = self.adapter_service.get_home_load_forecast_provider(
                        load_device.home_forecast_provider_id
                    )
                    # Home forecast provider is optional, so log a warning if it's missing but
                    # continue
                    if not home_forecast_provider:
                        if self.logger:
                            self.logger.warning(
                                f"Home forecast provider for "
                                f"load device '{load_device.name}' of"
                                f"optimization unit '{optimization_unit.name}' "
                                f"(Config ID: {optimization_unit.home_forecast_provider_id}) "
                                "not found. Skipping forecast provider."
                            )

                    if home_forecast_provider:
                        home_forecast_providers[load_device.id] = home_forecast_provider

        # --- Energy State ---
        if energy_source and energy_monitor:
            try:
                energy_state: Optional[EnergyStateSnapshot] = None
                energy_state = await energy_monitor.get_current_energy_state()
                if not energy_state:
                    if self.logger:
                        self.logger.error(
                            f"Could not retrieve energy state for optimization unit '{optimization_unit.name}'. "
                            "Skipping."
                        )
                # Publish energy state snapshot event
                if self._event_bus:
                    await self._event_bus.publish(
                        EnergyStateSnapshotUpdatedEvent(
                            optimization_unit_id=optimization_unit.id,
                            optimization_unit_name=optimization_unit.name,
                            energy_source_id=energy_source.id,
                            energy_state_snapshot=energy_state,
                        )
                    )
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        f"Error getting energy state for optimization unit '{optimization_unit.name}': {e}"
                    )

        # --- Solar Forecast ---
        forecast_data: Optional[Forecast] = None
        if forecast_provider:
            try:
                forecast_data = await forecast_provider.get_forecast()
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        f"Error getting solar forecast for optimization unit '{optimization_unit.name}': {e}"
                    )

        # --- Home Load Forecast ---
        home_load_forecast: Optional[ConsumptionForecast] = None
        if home_forecast_provider:
            try:
                # TODO: Provide parameters if needed
                home_load_forecast = home_forecast_provider.get_home_consumption_forecast()
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        f"Error getting home load forecast for optimization unit '{optimization_unit.name}': {e}"
                    )
        else:
            if self.logger:
                self.logger.info(
                    f"No home load forecast provider configured for optimization unit '{optimization_unit.name}'."
                )

        # --- Target Miners ---
        # Process only the first enabled miner in the optimization unit
        if not optimization_unit.target_miner_ids:
            if self.logger:
                self.logger.info(f"No target miners configured for optimization unit '{optimization_unit.name}'.")
        else:
            miner_ids = optimization_unit.target_miner_ids

            miner: Optional[Miner] = None
            miner_state: Optional[MinerStateSnapshot] = None
            for miner_id in miner_ids:
                # --- Miner ---
                miner = self.miner_repo.get_by_id(miner_id)
                if not miner:
                    if self.logger:
                        self.logger.error(
                            f"Miner {miner_id} in optimization unit '{optimization_unit.name}' not found in repository."
                        )
                    continue  # Try next miner if available

                if not miner.active:
                    if self.logger:
                        self.logger.warning(
                            f"Miner {miner_id} in optimization unit '{optimization_unit.name}' is not active. Skipping miner."
                        )
                    continue  # Try next miner if available

                if not miner.get_controller_ids():
                    if self.logger:
                        self.logger.warning(
                            f"Miner {miner_id} in optimization unit '{optimization_unit.name}' has no controllers. Skipping miner."
                        )
                    continue  # Try next miner if available

                # --- Query current state via feature ports ---
                status_port = await self.adapter_service.get_miner_feature_port(
                    miner, MinerFeatureType.STATUS_MONITORING
                )
                if not status_port or not isinstance(status_port, StatusMonitorPort):
                    if self.logger:
                        self.logger.error(f"No status monitor port for miner {miner_id}. Skipping.")
                    continue

                current_status = await status_port.get_status()

                operational_port = await self.adapter_service.get_miner_feature_port(
                    miner, MinerFeatureType.OPERATIONAL_MONITORING
                )
                blocks_found = None
                system_uptime = None
                if operational_port and isinstance(operational_port, OperationalMonitorPort):
                    blocks_found = await operational_port.get_blocks_found()
                    system_uptime = await operational_port.get_system_uptime()

                hashrate_port = await self.adapter_service.get_miner_feature_port(
                    miner, MinerFeatureType.HASHRATE_MONITORING
                )
                current_hashrate = None
                if hashrate_port and isinstance(hashrate_port, HashrateMonitorPort):
                    current_hashrate = await hashrate_port.get_hashrate()

                power_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.POWER_MONITORING)
                current_power = None
                if power_port and isinstance(power_port, PowerMonitorPort):
                    current_power = await power_port.get_power()

                hashboard_port = await self.adapter_service.get_miner_feature_port(
                    miner, MinerFeatureType.HASHBOARD_MONITORING
                )
                current_hashboards = []
                if hashboard_port and isinstance(hashboard_port, HashboardMonitorPort):
                    current_hashboards = await hashboard_port.get_hashboards()

                internal_fan_port = await self.adapter_service.get_miner_feature_port(
                    miner, MinerFeatureType.FAN_SPEED_INTERNAL_MONITORING
                )
                internal_fan_speed = []
                if internal_fan_port and isinstance(internal_fan_port, InternalFanSpeedMonitorPort):
                    internal_fan_speed = await internal_fan_port.get_internal_fan_speed()

                # Build the miner state snapshot
                miner_state = MinerStateSnapshot(
                    status=current_status,
                    hash_rate=current_hashrate,
                    power_consumption=current_power,
                    hashboards=current_hashboards,
                    internal_fan_speed=internal_fan_speed,
                    blocks_found=blocks_found,
                    system_uptime=system_uptime,
                )

                break  # We found a valid miner and controller, we can stop looking for more miners

        # --- Mining Performance Tracker ---
        tracker_current_hashrate: Optional[HashRate] = None
        mining_performance_tracker: Optional[MiningPerformanceTrackerPort] = None
        if optimization_unit.performance_tracker_id:
            mining_performance_tracker = await self.adapter_service.get_mining_performance_tracker(
                optimization_unit.performance_tracker_id
            )
        # Mining performance tracker is optional, so log a warning if it's missing
        # but continue
        if not mining_performance_tracker:
            if self.logger:
                self.logger.warning(
                    f"Mining performance tracker for optimization unit "
                    f"'{optimization_unit.name}' "
                    f"(Config ID: {optimization_unit.performance_tracker_id}) not found. "
                    f"Skipping mining performance tracker."
                )
        else:
            # --- Mining Performance Tracker ---
            if optimization_unit.target_miner_ids and mining_performance_tracker:
                try:
                    # TODO: Provide parameters if needed
                    miner_ids = optimization_unit.target_miner_ids
                    tracker_current_hashrate = mining_performance_tracker.get_current_hashrate(miner_ids=miner_ids)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(
                            f"Error getting mining performance tracker "
                            f"for optimization unit '{optimization_unit.name}': {e}"
                        )
                    tracker_current_hashrate = None

        # Creates the Sun object for the current date.
        sun: Sun = self.sun_factory.create_sun_for_date()

        # Create the decisional context without the miner yet,
        # as we will add it later after fetching the miner status.
        # This allows us to have a single context for the unit.
        # The context will be updated for each miner in the unit.
        context = DecisionalContext(
            energy_source=energy_source,
            energy_state=energy_state,
            forecast=forecast_data,
            home_load_forecast=home_load_forecast,
            tracker_current_hashrate=tracker_current_hashrate,
            sun=sun,
            miner=miner,
            miner_state=miner_state,
        )

        # Publish decisional context event
        if self._event_bus:
            await self._event_bus.publish(
                DecisionalContextUpdatedEvent(
                    optimization_unit_id=optimization_unit.id,
                    optimization_unit_name=optimization_unit.name,
                    context=context,
                    target_miner_ids=list(optimization_unit.target_miner_ids),
                )
            )

        return context

    async def run_all_enabled_units(self):
        """Run the optimization process for all enabled units."""
        if self.logger:
            self.logger.debug("Starting optimization run for all enabled units...")

        enabled_units = self.optimization_unit_repo.get_all_enabled()

        if not enabled_units:
            if self.logger:
                self.logger.debug("No enabled energy optimization units found.")
            return

        unit_tasks = [self._process_unit(unit) for unit in enabled_units]
        # Don't stop for an error in a unit
        await asyncio.gather(*unit_tasks, return_exceptions=False)

        if self.logger:
            self.logger.debug(f"Optimization run for all units finished. {len(enabled_units)} units processed.")

    async def _process_unit(self, optimization_unit: EnergyOptimizationUnit):
        if self.logger:
            self.logger.debug(f"Processing Optimization Unit: '{optimization_unit.name}' (ID: {optimization_unit.id})")

        # --- Notifiers ---
        unit_notifiers: List[NotificationPort] = []
        try:
            unit_notifiers = await self.adapter_service.get_notifiers(optimization_unit.notifier_ids)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting notifiers for optimization unit '{optimization_unit.name}': {e}")

        # --- Policy ---
        if not optimization_unit.policy_id:
            if self.logger:
                self.logger.warning(f"Optimization unit '{optimization_unit.name}' has no policy assigned. Skipping.")
            return
        policy: Optional[OptimizationPolicy] = None
        policy = self.policy_repo.get_by_id(optimization_unit.policy_id)
        if not policy:
            if self.logger:
                self.logger.error(
                    f"Policy ID {optimization_unit.policy_id} for optimization unit "
                    f"'{optimization_unit.name}' not found. Skipping."
                )
            return
        else:
            if self.logger:
                self.logger.debug(f"Optimization unit '{optimization_unit.name}' > Using policy '{policy.name}'.")

        # --- Energy Source  ---
        energy_source: Optional[EnergySource] = None
        if optimization_unit.energy_source_id:
            energy_source = self.energy_source_repo.get_by_id(optimization_unit.energy_source_id)
        if not energy_source:
            if self.logger:
                self.logger.error(
                    f"Energy source for optimization unit '{optimization_unit.name}' "
                    f"(Config ID: {optimization_unit.energy_source_id}) not found "
                    f"or failed to initialize. Skipping optimization unit."
                )
            await self._notify_unit(
                unit_notifiers,
                f"Optimizer Error ({optimization_unit.name})",
                "Energy source unavailable.",
            )
            return
        else:
            if self.logger:
                self.logger.debug(
                    f"Optimization unit '{optimization_unit.name}' > Using energy source '{energy_source.name}'."
                )

        # --- Energy Monitor ---
        energy_monitor: Optional[EnergyMonitorPort] = None
        if energy_source.energy_monitor_id:
            try:
                energy_monitor = await self.adapter_service.get_energy_monitor(energy_source)
            except Exception as e:
                if self.logger:
                    self.logger.critical(f"Error getting energy monitor for energy source '{energy_source.name}': {e}")
        if not energy_monitor:
            if self.logger:
                self.logger.error(
                    f"Energy monitor for energy source '{energy_source.name}' "
                    f"(Config ID: {energy_source.energy_monitor_id}) not found. "
                    f"Skipping optimization unit."
                )
            await self._notify_unit(
                unit_notifiers,
                f"Optimizer Error ({optimization_unit.name})",
                "Energy monitor unavailable.",
            )
            return

        # --- Forecast Provider ---
        forecast_provider: Optional[ForecastProviderPort] = None
        if energy_source.forecast_provider_id:
            try:
                forecast_provider = await self.adapter_service.get_forecast_provider(energy_source)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error getting forecast provider for energy source '{energy_source.name}': {e}")
        # Forecast is optional, so log a warning if it's missing but continue
        if not forecast_provider:
            if self.logger:
                self.logger.warning(
                    f"Forecast provider for energy source '{energy_source.name}' "
                    f"(Config ID: {energy_source.forecast_provider_id}) not found. "
                    f"Skipping optimization unit."
                )

        # --- Home Forecast Provider ---
        home_forecast_provider: Optional[HomeForecastProviderPort] = None
        if optimization_unit.home_forecast_provider_id:
            try:
                home_forecast_provider = self.adapter_service.get_home_load_forecast_provider(
                    optimization_unit.home_forecast_provider_id
                )
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        f"Error getting home forecast provider for optimization unit '{optimization_unit.name}': {e}"
                    )
        # Home forecast provider is optional, so log a warning if it's missing but
        # continue
        if not home_forecast_provider:
            if self.logger:
                self.logger.warning(
                    f"Home forecast provider for "
                    f"optimization unit '{optimization_unit.name}' "
                    f"(Config ID: {optimization_unit.home_forecast_provider_id}) "
                    "not found. Skipping forecast provider."
                )

        # --- Mining Performance Tracker ---
        mining_performance_tracker: Optional[MiningPerformanceTrackerPort] = None
        if optimization_unit.performance_tracker_id:
            try:
                mining_performance_tracker = await self.adapter_service.get_mining_performance_tracker(
                    optimization_unit.performance_tracker_id
                )
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        "Error getting mining performance tracker "
                        f"for optimization unit '{optimization_unit.name}': {e}"
                    )
        # Mining performance tracker is optional, so log a warning if it's missing
        # but continue
        if not mining_performance_tracker:
            if self.logger:
                self.logger.warning(
                    f"Mining performance tracker for optimization unit "
                    f"'{optimization_unit.name}' "
                    f"(Config ID: {optimization_unit.performance_tracker_id}) not found. "
                    f"Skipping mining performance tracker."
                )

        # --- Energy State ---
        try:
            energy_state: Optional[EnergyStateSnapshot] = None
            energy_state = await energy_monitor.get_current_energy_state()
            if not energy_state:
                if self.logger:
                    self.logger.error(
                        f"Could not retrieve energy state for optimization unit '{optimization_unit.name}'. Skipping."
                    )
                await self._notify_unit(
                    unit_notifiers,
                    f"Optimizer Error ({optimization_unit.name})",
                    "Failed to retrieve energy state.",
                )
                return

            # Publish energy state snapshot event
            if self._event_bus:
                await self._event_bus.publish(
                    EnergyStateSnapshotUpdatedEvent(
                        optimization_unit_id=optimization_unit.id,
                        optimization_unit_name=optimization_unit.name,
                        energy_source_id=energy_source.id,
                        energy_state_snapshot=energy_state,
                    )
                )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting energy state for optimization unit '{optimization_unit.name}': {e}")
            await self._notify_unit(
                unit_notifiers,
                f"Optimizer Error ({optimization_unit.name})",
                f"Energy state error: {e}",
            )
            return

        # --- Solar Forecast ---
        forecast_data: Optional[Forecast] = None
        if forecast_provider:
            try:
                # Assuming the forecast provider needs parameters from its config,
                # or that the resolver has already injected them. If specific parameters
                # are needed for the optimization unit (e.g. lat/lon), they should be
                # part of the adapter's config or passed here if the resolver doesn't handle them.
                # For now, assuming the resolver provides a ready-to-use adapter.
                # (the configuration has already done outside of the edge mining application)

                forecast_data = await forecast_provider.get_forecast()
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        f"Error getting solar forecast for optimization unit '{optimization_unit.name}': {e}"
                    )
        else:
            if self.logger:
                self.logger.debug(
                    f"No solar forecast provider configured for optimization unit '{optimization_unit.name}'."
                )

        # --- Home Load Forecast ---
        home_load_forecast: Optional[ConsumptionForecast] = None
        if home_forecast_provider:
            try:
                # TODO: Provide parameters if needed
                home_load_forecast = home_forecast_provider.get_home_consumption_forecast()
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        f"Error getting home load forecast for optimization unit '{optimization_unit.name}': {e}"
                    )
        else:
            if self.logger:
                self.logger.debug(
                    f"No home load forecast provider configured for optimization unit '{optimization_unit.name}'."
                )

        # --- Target Miners ---
        # Process each target miner in this optimization unit
        if not optimization_unit.target_miner_ids:
            if self.logger:
                self.logger.debug(f"No target miners configured for optimization unit '{optimization_unit.name}'.")
            return

        # --- Mining Performance Tracker ---
        tracker_current_hashrate: Optional[HashRate] = None
        if mining_performance_tracker:
            try:
                # TODO: Provide parameters if needed
                miner_ids = optimization_unit.target_miner_ids
                tracker_current_hashrate = mining_performance_tracker.get_current_hashrate(miner_ids=miner_ids)
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        f"Error getting mining performance tracker "
                        f"for optimization unit '{optimization_unit.name}': {e}"
                    )
                tracker_current_hashrate = None

        # Creates the Sun object for the current date.
        sun: Sun = self.sun_factory.create_sun_for_date()

        # Create the decisional context without the miner yet,
        # as we will add it later after fetching the miner status.
        # This allows us to have a single context for the unit.
        # The context will be updated for each miner in the unit.
        context = DecisionalContext(
            energy_source=energy_source,
            energy_state=energy_state,
            forecast=forecast_data,
            home_load_forecast=home_load_forecast,
            tracker_current_hashrate=tracker_current_hashrate,
            sun=sun,
        )

        # Publish decisional context event
        if self._event_bus:
            await self._event_bus.publish(
                DecisionalContextUpdatedEvent(
                    optimization_unit_id=optimization_unit.id,
                    optimization_unit_name=optimization_unit.name,
                    context=context,
                    target_miner_ids=list(optimization_unit.target_miner_ids),
                )
            )

        # TODO: should we manage miners singularly or together?
        # TODO: should we serialize the miner process or run them in parallel?
        # For now, we will run them in parallel, but I imagine that is not the best approach
        # for tracking the energy used for each miner.
        miner_processing_tasks = []
        for miner_id in optimization_unit.target_miner_ids:
            miner_processing_tasks.append(
                self._process_single_miner_in_unit(
                    optimization_unit=optimization_unit,
                    policy=policy,
                    context=context,
                    miner_id=miner_id,
                    notifiers=unit_notifiers,
                )
            )
        await asyncio.gather(*miner_processing_tasks, return_exceptions=False)

        if self.logger:
            self.logger.debug(
                f"Finished processing for optimization unit '{optimization_unit.name}'. "
                f"{len(miner_processing_tasks)} miners controlled."
            )

    async def _process_single_miner_in_unit(
        self,
        optimization_unit: EnergyOptimizationUnit,
        policy: OptimizationPolicy,
        context: DecisionalContext,
        miner_id: EntityId,
        notifiers: List[NotificationPort],
    ):
        # --- Miner ---
        miner: Optional[Miner] = None
        miner = self.miner_repo.get_by_id(miner_id)
        if not miner:
            if self.logger:
                self.logger.error(
                    f"Miner {miner_id} in optimization unit '{optimization_unit.name}' not found in repository."
                )
            message = f"Miner {miner_id} not found in optimization unit '{optimization_unit.name}'."
            await self._notify_unit(
                notifiers,
                f"Optimizer Error ({optimization_unit.name})",
                message,
            )
            return

        # --- Miner Controller (via feature ports) ---
        status_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.STATUS_MONITORING)
        if not status_port or not isinstance(status_port, StatusMonitorPort):
            if self.logger:
                self.logger.error(f"No status monitor available for miner {miner_id}. Cannot control miner.")
            await self._notify_unit(
                notifiers,
                f"Optimizer Error ({optimization_unit.name} / {miner_id})",
                "Status monitor unavailable.",
            )
            return

        mining_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.MINING_CONTROL)

        if not mining_port:
            if self.logger:
                self.logger.error(
                    f"No mining control port available "
                    f"for miner {miner_id} in optimization unit "
                    f"'{optimization_unit.name}'. Cannot control miner."
                )
            await self._notify_unit(
                notifiers,
                f"Optimizer Error ({optimization_unit.name} / {miner_id})",
                "Miner controller unavailable.",
            )
            return

        # Get current status and make decision
        try:
            # Query current state via feature ports
            current_status = await status_port.get_status()

            operational_port = await self.adapter_service.get_miner_feature_port(
                miner, MinerFeatureType.OPERATIONAL_MONITORING
            )
            blocks_found = None
            system_uptime = None
            if operational_port and isinstance(operational_port, OperationalMonitorPort):
                blocks_found = await operational_port.get_blocks_found()
                system_uptime = await operational_port.get_system_uptime()

            hashrate_port = await self.adapter_service.get_miner_feature_port(
                miner, MinerFeatureType.HASHRATE_MONITORING
            )
            current_hashrate = None
            if hashrate_port and isinstance(hashrate_port, HashrateMonitorPort):
                current_hashrate = await hashrate_port.get_hashrate()

            power_port = await self.adapter_service.get_miner_feature_port(miner, MinerFeatureType.POWER_MONITORING)
            current_power = None
            if power_port and isinstance(power_port, PowerMonitorPort):
                current_power = await power_port.get_power()

            # Build the miner state snapshot
            miner_state = MinerStateSnapshot(
                status=current_status,
                hash_rate=current_hashrate,
                power_consumption=current_power,
                blocks_found=blocks_found,
                system_uptime=system_uptime,
            )

            # Creates a copy of the context with the miner included, so that the policy
            # can access miner-specific data, without modifying the original context.
            # This is important to keep the context consistent across all miners in
            # the unit.
            decisional_context = DecisionalContext(
                energy_source=context.energy_source,
                energy_state=context.energy_state,
                forecast=context.forecast,
                home_load_forecast=context.home_load_forecast,
                tracker_current_hashrate=context.tracker_current_hashrate,
                sun=context.sun,
                miner=miner,  # Static config
                miner_state=miner_state,  # Runtime state snapshot
            )

            # Create the rule engine instance
            rule_engine: Optional[RuleEngine] = None
            try:
                rule_engine = self.adapter_service.get_rule_engine()
            except Exception as e:
                if self.logger:
                    self.logger.critical(f"Error getting rule engine: {e}")
            if not rule_engine:
                if self.logger:
                    self.logger.error(
                        f"Rule engine not available for optimization unit "
                        f"'{optimization_unit.name}'. Cannot process policy."
                    )
                await self._notify_unit(
                    notifiers,
                    f"Optimizer Error ({optimization_unit.name} / {miner_id})",
                    "Rule engine unavailable.",
                )
                return

            decision = policy.decide_next_action(decisional_context=decisional_context, rule_engine=rule_engine)
            if self.logger:
                self.logger.info(
                    f"Optimization unit '{optimization_unit.name}', "
                    f"Miner {miner_id}: Status={current_status.name}, "
                    f"Policy='{policy.name}', Decision={decision.name}"
                )

            # Publish rule engaged event
            if self._event_bus:
                await self._event_bus.publish(
                    RuleEngagedEvent(
                        optimization_unit_id=optimization_unit.id,
                        optimization_unit_name=optimization_unit.name,
                        policy_id=policy.id,
                        policy_name=policy.name,
                        miner_id=miner_id,
                        decision=decision,
                        miner_status=current_status.name,
                    )
                )

            await self._execute_miner_decision(
                mining_port,
                status_port,
                miner_id,
                decision,
                current_status,
                notifiers,
                optimization_unit.name,
            )

        except (MinerError, PolicyError) as e:
            if self.logger:
                self.logger.error(
                    f"Domain error processing miner {miner_id} in optimization unit '{optimization_unit.name}': {e}"
                )
            await self._notify_unit(
                notifiers,
                f"Optimizer Error ({optimization_unit.name} / {miner_id})",
                f"Domain error: {e}",
            )
        except Exception as e:  # Other exceptions (e.g. IO from the controller)
            if self.logger:
                if self.logger:
                    self.logger.error(
                        f"Unexpected error processing miner {miner_id} "
                        f"in optimization unit '{optimization_unit.name}': {e}"
                    )
            await self._notify_unit(
                notifiers,
                f"Optimizer Error ({optimization_unit.name} / {miner_id})",
                f"Runtime error: {e}",
            )

    async def _execute_miner_decision(
        self,
        mining_port: MinerFeaturePort,
        status_port: StatusMonitorPort,
        miner_id: EntityId,
        decision: MiningDecision,
        current_status: MinerStatus,
        notifiers: List[NotificationPort],
        unit_name: str,
    ):
        action_taken = False
        success = False
        message_suffix = f" (Optimization Unit: {unit_name})"

        if decision == MiningDecision.START_MINING and current_status != MinerStatus.ON:
            if self.logger:
                self.logger.info(f"Executing START for miner {miner_id} via {type(mining_port).__name__}")
            if isinstance(mining_port, MiningControlPort):
                success = await mining_port.start_mining()
            elif isinstance(mining_port, PowerControlPort):
                success = await mining_port.power_on()
            action_taken = True
            if success:
                await self._notify_unit(
                    notifiers,
                    f"Miner Started: {miner_id}",
                    f"Miner {miner_id} was started." + message_suffix,
                )
            else:
                await self._notify_unit(
                    notifiers,
                    f"Miner Start Failed: {miner_id}",
                    f"Attempt to start miner {miner_id} failed." + message_suffix,
                )

        elif decision == MiningDecision.STOP_MINING and current_status == MinerStatus.ON:
            if self.logger:
                self.logger.info(f"Executing STOP for miner {miner_id} via {type(mining_port).__name__}")
            if isinstance(mining_port, MiningControlPort):
                success = await mining_port.stop_mining()
            elif isinstance(mining_port, PowerControlPort):
                success = await mining_port.power_off()
            action_taken = True
            if success:
                await self._notify_unit(
                    notifiers,
                    f"Miner Stopped: {miner_id}",
                    f"Miner {miner_id} was stopped." + message_suffix,
                )
            else:
                await self._notify_unit(
                    notifiers,
                    f"Miner Stop Failed: {miner_id}",
                    f"Attempt to stop miner {miner_id} failed." + message_suffix,
                )

        if action_taken:
            if not success:
                if self.logger:
                    self.logger.error(
                        f"Command {decision.name} for miner {miner_id} failed using controller {type(mining_port).__name__}."
                    )
            else:
                miner = self.miner_repo.get_by_id(miner_id)

                # Get new miner state to publish in the event
                new_status = await status_port.get_status()

                # Publish miner state changed event
                if self._event_bus:
                    await self._event_bus.publish(
                        MinerStateChangedEvent(
                            miner_id=miner_id,
                            miner_name=miner.name if miner else "",
                            old_status=current_status,
                            new_status=new_status,
                        )
                    )
        else:
            if self.logger:
                self.logger.debug(
                    f"No action taken for miner {miner_id} (Decision: {decision.name}, "
                    f"Current Status: {current_status.name})."
                )
