"""
This service is responsible for creating and managing adapters for the application.
"""

from typing import Dict, List, Optional, Union

from edge_mining.adapters.domain.energy.monitors.dummy_solar import DummySolarEnergyMonitorFactory
from edge_mining.adapters.domain.energy.monitors.home_assistant_api import HomeAssistantAPIEnergyMonitorFactory
from edge_mining.adapters.domain.forecast.providers.dummy_solar import DummyForecastProviderFactory
from edge_mining.adapters.domain.forecast.providers.home_assistant_api import HomeAssistantForecastProviderFactory
from edge_mining.adapters.domain.home_load.forecast_providers.dummy import DummyEnergyLoadForecastProviderFactory
from edge_mining.adapters.domain.home_load.forecast_providers.naive_last_hour import (
    NaiveLastHourForecastProviderFactory,
)
from edge_mining.adapters.domain.home_load.forecast_providers.seasonal_baseline import (
    SeasonalBaselineForecastProviderFactory,
)
from edge_mining.adapters.domain.home_load.forecast_providers.statsmodels_hw import (
    StatsmodelsForecastProviderFactory,
)
from edge_mining.adapters.domain.home_load.forecast_providers.xgboost_provider import (
    XGBoostForecastProviderFactory,
)
from edge_mining.adapters.domain.home_load.history_providers.dummy import DummyEnergyLoadHistoryProvider
from edge_mining.adapters.domain.miner.controllers.dummy import DummyMinerController
from edge_mining.adapters.domain.miner.controllers.generic_socket_home_assistant_api import (
    GenericSocketHomeAssistantAPIMinerControllerAdapterFactory,
)
from edge_mining.adapters.domain.miner.controllers.pyasic import PyASICMinerControllerAdapterFactory
from edge_mining.adapters.domain.notification.notifiers.dummy import DummyNotifier
from edge_mining.adapters.domain.notification.notifiers.telegram import TelegramNotifierFactory
from edge_mining.adapters.domain.performance.trackers.dummy import DummyMiningPerformanceTracker
from edge_mining.adapters.infrastructure.homeassistant.homeassistant_api import ServiceHomeAssistantAPIFactory
from edge_mining.adapters.infrastructure.rule_engine.factory import RuleEngineFactory
from edge_mining.application.events.common import ConfigurationUpdatedEventType
from edge_mining.application.events.configuration_events import ConfigurationUpdatedEvent
from edge_mining.application.interfaces import AdapterServiceInterface, EventBusInterface
from edge_mining.domain.common import EntityId
from edge_mining.domain.energy.common import EnergyMonitorAdapter
from edge_mining.domain.energy.entities import EnergyMonitor, EnergySource
from edge_mining.domain.energy.ports import EnergyMonitorPort, EnergyMonitorRepository
from edge_mining.domain.forecast.common import ForecastProviderAdapter
from edge_mining.domain.forecast.entities import ForecastProvider
from edge_mining.domain.forecast.ports import ForecastProviderPort, ForecastProviderRepository
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter, EnergyLoadHistoryProviderAdapter
from edge_mining.domain.home_load.entities import EnergyLoadForecastProvider, EnergyLoadHistoryProvider
from edge_mining.domain.home_load.ports import (
    EnergyLoadForecastProviderPort,
    EnergyLoadForecastProviderRepository,
    EnergyLoadHistoryProviderPort,
    EnergyLoadHistoryProviderRepository,
    EnergyLoadHistoryRepository,
    LoadConsumptionModelRepository,
)
from edge_mining.domain.miner.aggregate_roots import Miner
from edge_mining.domain.miner.common import MinerControllerAdapter, MinerFeatureType
from edge_mining.domain.miner.entities import MinerController
from edge_mining.domain.miner.ports import MinerControllerRepository, MinerFeaturePort, MinerRepository
from edge_mining.domain.miner.value_objects import MinerFeature
from edge_mining.domain.notification.common import NotificationAdapter
from edge_mining.domain.notification.entities import Notifier
from edge_mining.domain.notification.ports import NotificationPort, NotifierRepository
from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.ports import MiningPerformanceTrackerPort, MiningPerformanceTrackerRepository
from edge_mining.domain.policy.common import RuleEngineType
from edge_mining.domain.policy.services import RuleEngine
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.external_services.entities import ExternalService
from edge_mining.shared.external_services.ports import ExternalServicePort, ExternalServiceRepository
from edge_mining.shared.interfaces.factories import (
    EnergyLoadForecastAdapterFactory,
    EnergyMonitorAdapterFactory,
    ExternalServiceFactory,
    ForecastAdapterFactory,
    MinerControllerAdapterFactory,
)
from edge_mining.shared.logging.port import LoggerPort


class AdapterService(AdapterServiceInterface):
    """
    This service is responsible for creating and managing adapters for the application.
    """

    def __init__(
        self,
        energy_monitor_repo: EnergyMonitorRepository,
        miner_controller_repo: MinerControllerRepository,
        miner_repo: MinerRepository,
        notifier_repo: NotifierRepository,
        forecast_provider_repo: ForecastProviderRepository,
        mining_performance_tracker_repo: MiningPerformanceTrackerRepository,
        energy_load_forecast_provider_repo: EnergyLoadForecastProviderRepository,
        energy_load_history_provider_repo: EnergyLoadHistoryProviderRepository,
        home_load_history_repo: EnergyLoadHistoryRepository,
        external_service_repo: ExternalServiceRepository,
        event_bus: EventBusInterface,
        logger: Optional[LoggerPort] = None,
        load_consumption_model_repo: Optional[LoadConsumptionModelRepository] = None,
    ):
        self.energy_monitor_repo = energy_monitor_repo
        self.miner_controller_repo = miner_controller_repo
        self.miner_repo = miner_repo
        self.notifier_repo = notifier_repo
        self.forecast_provider_repo = forecast_provider_repo
        self.mining_performance_tracker_repo = mining_performance_tracker_repo
        self.energy_load_forecast_provider_repo = energy_load_forecast_provider_repo
        self.energy_load_history_provider_repo = energy_load_history_provider_repo
        self.home_load_history_repo = home_load_history_repo
        self.external_service_repo = external_service_repo
        self.load_consumption_model_repo = load_consumption_model_repo
        # Cache for already created instances
        self._instance_cache: Dict[
            EntityId,
            Optional[
                Union[
                    EnergyMonitorPort,
                    MinerFeaturePort,
                    NotificationPort,
                    ForecastProviderPort,
                    EnergyLoadForecastProviderPort,
                    EnergyLoadHistoryProviderPort,
                    MiningPerformanceTrackerPort,
                ]
            ],
        ] = {}
        # Cache for already created external services
        self._service_cache: Dict[EntityId, ExternalServicePort] = {}

        self.logger = logger

        self._subscribe_events(event_bus)

    def _subscribe_events(self, event_bus: EventBusInterface) -> None:
        """Register all event subscriptions for this service."""
        event_bus.subscribe(
            ConfigurationUpdatedEvent,
            self.on_configuration_updated,
            blocking=True,
        )

    async def _initialize_external_service(self, external_service: ExternalService) -> Optional[ExternalServicePort]:
        """Initialize an external service"""
        # If the external service already exists, we use it
        if external_service.id in self._service_cache:
            if self.logger:
                self.logger.debug(
                    f"Returning cached instance "
                    f"for external service ID {external_service.id} "
                    f"(Type: {external_service.adapter_type})"
                )
            return self._service_cache[external_service.id]

        try:
            external_service_factory: Optional[ExternalServiceFactory] = None

            if external_service.adapter_type == ExternalServiceAdapter.HOME_ASSISTANT_API:
                # --- Home Assistant API ---

                external_service_factory = ServiceHomeAssistantAPIFactory()
            else:
                raise ValueError(f"Unsupported external service type: {external_service.adapter_type}")

            instance_service = external_service_factory.create(config=external_service.config, logger=self.logger)

            # Connect to the external service asynchronously
            await instance_service.connect()

            self._service_cache[external_service.id] = instance_service
            return instance_service
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to initialize External Service '{external_service.name}' "
                    f"(Type: {external_service.adapter_type}): {e}"
                )
            return None

    async def _initialize_energy_monitor_adapter(
        self, energy_source: EnergySource, energy_monitor: EnergyMonitor
    ) -> Optional[EnergyMonitorPort]:
        """Initialize an energy monitor adapter."""
        # If the adapter has already been created, we use it.
        if energy_monitor.id in self._instance_cache:
            if self.logger:
                self.logger.debug(
                    f"Returning cached adapter instance "
                    f"for energy monitor ID {energy_monitor.id} "
                    f"(Type: {energy_monitor.adapter_type})"
                )

            cached_instance = self._instance_cache[energy_monitor.id]

            if not cached_instance:
                # If the cached instance is None, we return it
                # to indicate that the adapter was not initialized.
                if self.logger:
                    self.logger.warning(
                        f"Cached instance for energy monitor ID {energy_monitor.id} is None. Reinitializing adapter."
                    )
                return None

            # Check if the cached instance is of the correct type
            if not isinstance(cached_instance, EnergyMonitorPort):
                if self.logger:
                    self.logger.warning(
                        f"Cached instance for energy monitor ID {energy_monitor.id} "
                        f"is not of type EnergyMonitorPort. Reinitializing adapter."
                    )
                return None

            # If the cached instance is valid, we return it
            return cached_instance

        # Retrieve the external service associated to the energy monitor
        external_service: Optional[ExternalServicePort] = None
        if energy_monitor.external_service_id:
            external_service = await self.get_external_service(energy_monitor.external_service_id)
            if not external_service:
                raise ValueError(
                    "Unable to load external service "
                    f"{energy_monitor.external_service_id} "
                    f"for energy monitor {energy_monitor.name}"
                )

        try:
            energy_monitor_adapter_factory: Optional[EnergyMonitorAdapterFactory] = None

            if energy_monitor.adapter_type == EnergyMonitorAdapter.DUMMY_SOLAR:
                # --- Dummy Solar ---
                if not energy_source:
                    raise ValueError("EnergySource is required for DummySolar energy monitor.")

                energy_monitor_adapter_factory = DummySolarEnergyMonitorFactory()

                # Set energy source as reference
                energy_monitor_adapter_factory.from_energy_source(energy_source)
            elif energy_monitor.adapter_type == EnergyMonitorAdapter.HOME_ASSISTANT_API:
                # --- Home Assistant API ---
                if not energy_monitor.config:
                    raise ValueError("EnergyMonitor config is required for HomeAssistantAPI energy monitor.")

                energy_monitor_adapter_factory = HomeAssistantAPIEnergyMonitorFactory()
                # Actually HomeAssistantAPI Energy Monitor
                # does not needs an energy source as reference
            else:
                raise ValueError(f"Unsupported energy monitor adapter type: {energy_monitor.adapter_type}")

            instance = energy_monitor_adapter_factory.create(
                config=energy_monitor.config,
                logger=self.logger,
                external_service=external_service,
            )

            self._instance_cache[energy_monitor.id] = instance
            return instance
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to initialize adapter '{energy_monitor.name}' "
                    f"(Type: {energy_monitor.adapter_type}) using factory: {e}"
                )
            return None

    async def _initialize_miner_controller_adapter(
        self, miner: Miner, miner_controller: MinerController
    ) -> Optional[MinerFeaturePort]:
        """Initialize a miner controller adapter."""
        # If the adapter has already been created, we use it.
        if miner_controller.id in self._instance_cache:
            if self.logger:
                self.logger.debug(
                    f"Returning cached adapter instance "
                    f"for miner controller ID {miner_controller.id} "
                    f"(Type: {miner_controller.adapter_type})"
                )

            cached_instance = self._instance_cache[miner_controller.id]
            if not cached_instance:
                if self.logger:
                    self.logger.warning(
                        f"Cached instance for miner controller ID {miner_controller.id} "
                        f"is None. Reinitializing adapter."
                    )
                return None

            if not isinstance(cached_instance, MinerFeaturePort):
                if self.logger:
                    self.logger.warning(
                        f"Cached instance for miner controller ID {miner_controller.id} "
                        f"is not of type MinerFeaturePort. Reinitializing adapter."
                    )
                return None

            return cached_instance

        # Retrieve the external service associated to the miner controller
        external_service: Optional[ExternalServicePort] = None
        if miner_controller.external_service_id:
            external_service = await self.get_external_service(miner_controller.external_service_id)
            if not external_service:
                raise ValueError(
                    f"Unable to load external service {miner_controller.external_service_id} "
                    f"for miner controller {miner_controller.name}"
                )

        try:
            miner_controller_factory: Optional[MinerControllerAdapterFactory] = None
            instance: Optional[MinerFeaturePort] = None

            if miner_controller.adapter_type == MinerControllerAdapter.DUMMY:
                if miner.power_consumption_max is None or miner.hash_rate_max is None:
                    raise ValueError(
                        "Miner power consumption max and hash rate max are required for DummyMinerController."
                    )
                # --- Dummy Controller ---
                instance = DummyMinerController(
                    power_max=miner.power_consumption_max,
                    hashrate_max=miner.hash_rate_max,
                    logger=self.logger,
                )
            elif miner_controller.adapter_type == MinerControllerAdapter.GENERIC_SOCKET_HOME_ASSISTANT_API:
                # --- Generic Socket Home Assistant API Controller ---
                miner_controller_factory = GenericSocketHomeAssistantAPIMinerControllerAdapterFactory()

                miner_controller_factory.from_miner(miner)

                instance = miner_controller_factory.create(
                    config=miner_controller.config,
                    logger=self.logger,
                    external_service=external_service,
                )
            elif miner_controller.adapter_type == MinerControllerAdapter.PYASIC:
                # --- PyASIC Controller ---
                miner_controller_factory = PyASICMinerControllerAdapterFactory()

                miner_controller_factory.from_miner(miner)

                instance = miner_controller_factory.create(
                    config=miner_controller.config,
                    logger=self.logger,
                    external_service=external_service,
                )
            else:
                raise ValueError(f"Unsupported miner controller adapter type: {miner_controller.adapter_type}")

            self._instance_cache[miner_controller.id] = instance
            return instance
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to initialize adapter '{miner_controller.name}' "
                    f"(Type: {miner_controller.adapter_type}) using factory: {e}"
                )
            return None

    async def _initialize_notifier_adapter(self, notifier: Notifier) -> Optional[NotificationPort]:
        """Initialize a notifier adapter."""
        # If the adapter has already been created, we use it.
        if notifier.id in self._instance_cache:
            if self.logger:
                self.logger.debug(
                    f"Returning cached adapter instance for notifier ID {notifier.id} (Type: {notifier.adapter_type})"
                )

            cached_instance = self._instance_cache[notifier.id]

            if not cached_instance:
                # If the cached instance is None, we return it
                # to indicate that the adapter was not initialized.
                if self.logger:
                    self.logger.warning(
                        f"Cached instance for notifier ID {notifier.id} is None. Reinitializing adapter."
                    )
                return None

            # Check if the cached instance is of the correct type
            if not isinstance(cached_instance, NotificationPort):
                if self.logger:
                    self.logger.warning(
                        f"Cached instance for notifier ID {notifier.id} "
                        f"is not of type NotificationPort. Reinitializing adapter."
                    )
                return None

            # If the cached instance is valid, we return it
            return cached_instance

        # Retrieve the external service associated to the notifier
        external_service: Optional[ExternalServicePort] = None
        if notifier.external_service_id:
            external_service = await self.get_external_service(notifier.external_service_id)
            if not external_service:
                raise ValueError(
                    f"Unable to load external service {notifier.external_service_id} for notifier {notifier.name}"
                )
        try:
            instance: Optional[NotificationPort] = None

            if notifier.adapter_type == NotificationAdapter.DUMMY:
                # --- Dummy Notifier ---
                instance = DummyNotifier()
            elif notifier.adapter_type == NotificationAdapter.TELEGRAM:
                # --- Telegram Notifier ---
                instance = TelegramNotifierFactory().create(
                    config=notifier.config,
                    logger=self.logger,
                    external_service=external_service,
                )
            else:
                raise ValueError(f"Unsupported notifier adapter type: {notifier.adapter_type}")

            self._instance_cache[notifier.id] = instance
            return instance
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to initialize adapter '{notifier.name}' (Type: {notifier.adapter_type}) using factory: {e}"
                )
            return None

    async def _initialize_forecast_provider_adapter(
        self, energy_source: EnergySource, forecast_provider: ForecastProvider
    ) -> Optional[ForecastProviderPort]:
        """Initialize a forecast provider adapter."""
        # If the adapter has already been created, we use it.
        if forecast_provider.id in self._instance_cache:
            if self.logger:
                self.logger.debug(
                    f"Returning cached adapter instance "
                    f"for forecast provider ID {forecast_provider.id} "
                    f"(Type: {forecast_provider.adapter_type})"
                )
            cached_instance = self._instance_cache[forecast_provider.id]

            if not cached_instance:
                # If the cached instance is None, we return it
                # to indicate that the adapter was not initialized.
                if self.logger:
                    self.logger.warning(
                        "Cached instance for forecast provider "
                        f"ID {forecast_provider.id} "
                        f"is None. Reinitializing adapter."
                    )
                return None

            # Check if the cached instance is of the correct type
            if not isinstance(cached_instance, ForecastProviderPort):
                if self.logger:
                    self.logger.warning(
                        "Cached instance for forecast provider "
                        f"ID {forecast_provider.id} "
                        f"is not of type ForecastProviderPort. Reinitializing adapter."
                    )
                return None

            # If the cached instance is valid, we return it
            return cached_instance

        # Retrieve the external service associated to the forecast provider
        if forecast_provider.external_service_id:
            external_service = await self.get_external_service(forecast_provider.external_service_id)
            if not external_service:
                raise ValueError(
                    f"Unable to load external service {forecast_provider.external_service_id} "
                    f"for forecast provider {forecast_provider.name}"
                )

        try:
            forecast_provider_adapter_factory: Optional[ForecastAdapterFactory] = None

            if forecast_provider.adapter_type == ForecastProviderAdapter.DUMMY_SOLAR:
                # --- Dummy Forecast Provider ---
                if not energy_source:
                    raise ValueError("EnergySource is required for DummySolar forecast provider.")

                forecast_provider_adapter_factory = DummyForecastProviderFactory()

                # Set energy source as reference
                forecast_provider_adapter_factory.from_energy_source(energy_source)
            elif forecast_provider.adapter_type == ForecastProviderAdapter.HOME_ASSISTANT_API:
                # --- Home Assistant API Forecast Provider ---
                if not forecast_provider.config:
                    raise ValueError("ForecastProvider config is required for HomeAssistantAPI forecast provider.")

                forecast_provider_adapter_factory = HomeAssistantForecastProviderFactory()
            else:
                raise ValueError(f"Unsupported forecast provider adapter type: {forecast_provider.adapter_type}")

            instance = forecast_provider_adapter_factory.create(
                config=forecast_provider.config,
                logger=self.logger,
                external_service=external_service,
            )

            self._instance_cache[forecast_provider.id] = instance
            return instance
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to initialize adapter '{forecast_provider.name}' "
                    f"(Type: {forecast_provider.adapter_type}) using factory: {e}"
                )
            return None

    def _initialize_energy_load_forecast_provider_adapter(
        self, energy_load_forecast_provider: EnergyLoadForecastProvider
    ) -> Optional[EnergyLoadForecastProviderPort]:
        """Initialize a home forecast provider adapter."""
        # If the adapter has already been created, we use it.
        if energy_load_forecast_provider.id in self._instance_cache:
            if self.logger:
                self.logger.debug(
                    f"Returning cached adapter instance "
                    f"for home forecast provider ID {energy_load_forecast_provider.id} "
                    f"(Type: {energy_load_forecast_provider.adapter_type})"
                )
            cached_instance = self._instance_cache[energy_load_forecast_provider.id]

            if not cached_instance:
                # If the cached instance is None, we return it
                # to indicate that the adapter was not initialized.
                if self.logger:
                    self.logger.warning(
                        f"Cached instance for home forecast provider ID "
                        f"{energy_load_forecast_provider.id} is None. Reinitializing adapter."
                    )
                return None

            # Check if the cached instance is of the correct type
            if not isinstance(cached_instance, EnergyLoadForecastProviderPort):
                if self.logger:
                    self.logger.warning(
                        f"Cached instance for home forecast provider ID "
                        f"{energy_load_forecast_provider.id} is not of type EnergyLoadForecastProviderPort. "
                        "Reinitializing adapter."
                    )
                return None

            # If the cached instance is valid, we return it
            return cached_instance

        try:
            factory: Optional[EnergyLoadForecastAdapterFactory] = None

            if energy_load_forecast_provider.adapter_type == EnergyLoadForecastProviderAdapter.DUMMY:
                factory = DummyEnergyLoadForecastProviderFactory()
            elif energy_load_forecast_provider.adapter_type == EnergyLoadForecastProviderAdapter.NAIVE_LAST_HOUR:
                factory = NaiveLastHourForecastProviderFactory()
            elif energy_load_forecast_provider.adapter_type == EnergyLoadForecastProviderAdapter.SEASONAL_BASELINE:
                factory = SeasonalBaselineForecastProviderFactory()
            elif energy_load_forecast_provider.adapter_type == EnergyLoadForecastProviderAdapter.STATSMODELS:
                factory = StatsmodelsForecastProviderFactory(model_repo=self.load_consumption_model_repo)
            elif energy_load_forecast_provider.adapter_type == EnergyLoadForecastProviderAdapter.XGBOOST:
                factory = XGBoostForecastProviderFactory(model_repo=self.load_consumption_model_repo)
            else:
                raise ValueError(
                    f"Unsupported home forecast provider adapter type: {energy_load_forecast_provider.adapter_type}"
                )

            instance = factory.create(
                config=energy_load_forecast_provider.config,
                logger=self.logger,
                external_service=None,
            )

            self._instance_cache[energy_load_forecast_provider.id] = instance
            return instance
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to initialize adapter '{energy_load_forecast_provider.name}' "
                    f"(Type: {energy_load_forecast_provider.adapter_type}) using factory: {e}"
                )
            return None

    async def _initialize_mining_performance_tracker_adapter(
        self, tracker: MiningPerformanceTracker
    ) -> Optional[MiningPerformanceTrackerPort]:
        """Initialize a mining performance tracker adapter."""
        # If the adapter has already been created, we use it.
        if tracker.id in self._instance_cache:
            if self.logger:
                self.logger.debug(
                    f"Returning cached adapter instance "
                    f"for mining performance tracker ID {tracker.id} "
                    f"(Type: {tracker.adapter_type})"
                )
            cached_instance = self._instance_cache[tracker.id]

            if not cached_instance:
                # If the cached instance is None, we return it
                # to indicate that the adapter was not initialized.
                if self.logger:
                    self.logger.warning(
                        f"Cached instance for mining performance tracker ID {tracker.id} "
                        f"is None. Reinitializing adapter."
                    )
                return None

            # Check if the cached instance is of the correct type
            if not isinstance(cached_instance, MiningPerformanceTrackerPort):
                if self.logger:
                    self.logger.warning(
                        f"Cached instance for mining performance tracker ID {tracker.id} "
                        f"is not of type MiningPerformanceTrackerPort. Reinitializing adapter."
                    )
                return None

            # If the cached instance is valid, we return it
            return cached_instance

        # Retrieve the external service associated to the energy monitor
        if tracker.external_service_id:
            external_service = await self.get_external_service(tracker.external_service_id)
            if not external_service:
                raise ValueError(
                    f"Unable to load external service {tracker.external_service_id} "
                    f"for mining performance tracker {tracker.name}"
                )

        try:
            instance: Optional[MiningPerformanceTrackerPort] = None

            # No configuration is needed for the dummy tracker.
            # We instantiate it directly using DummyMiningPerformanceTracker.
            # In the future, if we may have other types of trackers
            # that require different initialization logic, we can use
            # a factory pattern similar to the other adapters.

            if tracker.adapter_type == MiningPerformanceTrackerAdapter.DUMMY:
                # --- Dummy Tracker ---

                instance = DummyMiningPerformanceTracker()
            else:
                raise ValueError(f"Unsupported mining performance tracker adapter type: {tracker.adapter_type}")

            self._instance_cache[tracker.id] = instance
            return instance
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to initialize adapter '{tracker.name}' (Type: {tracker.adapter_type}) using factory: {e}"
                )
            return None

    async def get_energy_monitor(self, energy_source: EnergySource) -> Optional[EnergyMonitorPort]:
        """Get an energy monitor adapter instance."""
        if not energy_source.energy_monitor_id:
            if self.logger:
                self.logger.error(f"EnergySource {energy_source.name} does not have an associated EnergyMonitor ID.")
            return None
        energy_monitor = self.energy_monitor_repo.get_by_id(energy_source.energy_monitor_id)
        if not energy_monitor:
            if self.logger:
                self.logger.error(
                    f"EnergyMonitor ID {energy_source.energy_monitor_id} not found or not an EnergyMonitor."
                )
            return None
        return await self._initialize_energy_monitor_adapter(energy_source, energy_monitor)

    async def get_miner_controller_adapter(self, miner: Miner, controller_id: EntityId) -> Optional[MinerFeaturePort]:
        """Get a miner controller adapter instance for a specific controller."""
        miner_controller = self.miner_controller_repo.get_by_id(controller_id)
        if not miner_controller:
            if self.logger:
                self.logger.error(f"Miner Controller ID {controller_id} not found.")
            return None
        return await self._initialize_miner_controller_adapter(miner, miner_controller)

    async def sync_miner_features(self, miner: Miner) -> bool:
        """Reconcile stored features with what controllers actually support.

        For each controller associated with the miner, discovers which features
        the adapter supports and adds missing ones / removes stale ones.
        Returns True if any changes were made (and persisted).
        """
        changed = False
        controller_ids = miner.get_controller_ids()

        for controller_id in controller_ids:
            adapter = await self.get_miner_controller_adapter(miner, controller_id)
            if not adapter:
                continue

            supported = set(adapter.__class__.get_supported_features())
            stored = {f.feature_type for f in miner.get_features_by_controller(controller_id)}

            # Add missing features
            for feature_type in supported - stored:
                feature = MinerFeature(
                    feature_type=feature_type,
                    controller_id=controller_id,
                    priority=50,
                    enabled=True,
                )
                try:
                    miner.add_feature(feature)
                    changed = True
                except ValueError:
                    pass

            # Remove stale features (stored but no longer supported)
            for feature_type in stored - supported:
                miner.remove_feature(feature_type, controller_id)
                changed = True

        if changed:
            self.miner_repo.update(miner)
            if self.logger:
                self.logger.info(f"Reconciled features for miner {miner.name}.")

        return changed

    async def get_miner_feature_port(self, miner: Miner, feature_type: MinerFeatureType) -> Optional[MinerFeaturePort]:
        """Get the adapter implementing the highest-priority active feature for a miner.

        Resolves the active MinerFeature for the given feature_type, retrieves
        the associated controller adapter, and verifies it supports the feature.
        If the feature is not found, triggers a one-time reconciliation to catch
        features added or removed by code changes.
        """
        active_feature = miner.get_active_feature(feature_type)

        # Lazy reconciliation: if feature not found, sync and retry once
        if not active_feature:
            reconciled = await self.sync_miner_features(miner)
            if reconciled:
                active_feature = miner.get_active_feature(feature_type)

        if not active_feature:
            if self.logger:
                self.logger.debug(f"No active feature of type {feature_type.value} for miner {miner.name}.")
            return None

        adapter = await self.get_miner_controller_adapter(miner, active_feature.controller_id)
        if not adapter:
            return None

        # Verify the adapter actually supports the requested feature type
        supported = adapter.__class__.get_supported_features()
        if feature_type not in supported:
            if self.logger:
                self.logger.error(
                    f"Adapter for controller {active_feature.controller_id} "
                    f"does not support feature {feature_type.value}."
                )
            return None

        return adapter

    async def get_all_notifiers(self) -> List[NotificationPort]:
        """Get all notifier adapter instances"""
        notifier_instances = []
        notifiers = self.notifier_repo.get_all()
        if not notifiers or not len(notifiers) > 0:
            if self.logger:
                self.logger.error("Notifiers not configured.")
            return []

        for notifier in notifiers:
            instance = await self._initialize_notifier_adapter(notifier)
            if instance:
                notifier_instances.append(instance)
            else:
                if self.logger:
                    self.logger.warning(f"Notifier ID {notifier.id} not found or not a Notification category.")
        return notifier_instances

    async def get_notifier(self, notifier_id: EntityId) -> Optional[NotificationPort]:
        """Get a specific notifier adapter instance by ID."""
        notifier = self.notifier_repo.get_by_id(notifier_id)
        if not notifier:
            if self.logger:
                self.logger.error(f"Notifier ID {notifier_id} not found or not a Notifier.")
            return None
        return await self._initialize_notifier_adapter(notifier)

    async def get_notifiers(self, notifier_ids: List[EntityId]) -> List[NotificationPort]:
        """Get a list of specific notifier adapter instances by IDs."""
        notifier_instances: List[NotificationPort] = []
        for notifier_id in notifier_ids:
            notifier = self.notifier_repo.get_by_id(notifier_id)
            if not notifier:
                if self.logger:
                    self.logger.error(f"Notifier ID {notifier_id} not found or not a Notifier.")
                continue

            instance = await self._initialize_notifier_adapter(notifier)
            if instance:
                notifier_instances.append(instance)
            else:
                if self.logger:
                    self.logger.warning(f"Notifier ID {notifier.id} not found or not a Notification category.")
        return notifier_instances

    async def get_forecast_provider(self, energy_source: EnergySource) -> Optional[ForecastProviderPort]:
        """Get a forecast provider adapter instance."""
        if not energy_source.forecast_provider_id:
            if self.logger:
                self.logger.error(f"EnergySource {energy_source.name} does not have an associated ForecastProvider ID.")
            return None
        forecast_provider = self.forecast_provider_repo.get_by_id(energy_source.forecast_provider_id)
        if not forecast_provider:
            if self.logger:
                self.logger.error(
                    f"Forecast Provider ID {energy_source.forecast_provider_id} not found or not a Forecast Provider."
                )
            return None
        return await self._initialize_forecast_provider_adapter(energy_source, forecast_provider)

    def get_home_load_forecast_provider(
        self, energy_load_forecast_provider_id: EntityId
    ) -> Optional[EnergyLoadForecastProviderPort]:
        """Get an home load forecast provider adapter instance."""
        energy_load_forecast_provider = self.energy_load_forecast_provider_repo.get_by_id(
            energy_load_forecast_provider_id
        )
        if not energy_load_forecast_provider:
            if self.logger:
                self.logger.error(
                    f"Home Forecast Provider ID {energy_load_forecast_provider_id} not found or not a Home Forecast Provider."
                )
            return None
        return self._initialize_energy_load_forecast_provider_adapter(energy_load_forecast_provider)

    def _initialize_energy_load_history_provider_adapter(
        self, energy_load_history_provider: EnergyLoadHistoryProvider, device_id: EntityId
    ) -> Optional[EnergyLoadHistoryProviderPort]:
        """Initialize an energy load history provider adapter."""
        cache_key = energy_load_history_provider.id
        if cache_key in self._instance_cache:
            cached_instance = self._instance_cache[cache_key]
            if cached_instance and isinstance(cached_instance, EnergyLoadHistoryProviderPort):
                return cached_instance
            return None

        try:
            instance: Optional[EnergyLoadHistoryProviderPort] = None

            if energy_load_history_provider.adapter_type == EnergyLoadHistoryProviderAdapter.DUMMY:
                instance = DummyEnergyLoadHistoryProvider(
                    device_id=device_id,
                    history_repo=self.home_load_history_repo,
                    logger=self.logger,
                )
            else:
                raise ValueError(
                    f"Unsupported energy load history provider adapter type: "
                    f"{energy_load_history_provider.adapter_type}"
                )

            self._instance_cache[cache_key] = instance
            return instance
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to initialize adapter '{energy_load_history_provider.name}' "
                    f"(Type: {energy_load_history_provider.adapter_type}): {e}"
                )
            return None

    def get_home_load_history_provider(
        self, energy_load_history_provider_id: EntityId, device_id: EntityId
    ) -> Optional[EnergyLoadHistoryProviderPort]:
        """Get an energy load history provider adapter instance."""
        energy_load_history_provider = self.energy_load_history_provider_repo.get_by_id(energy_load_history_provider_id)
        if not energy_load_history_provider:
            if self.logger:
                self.logger.error(f"Home History Provider ID {energy_load_history_provider_id} not found.")
            return None
        return self._initialize_energy_load_history_provider_adapter(energy_load_history_provider, device_id)

    async def get_mining_performance_tracker(self, tracker_id: EntityId) -> Optional[MiningPerformanceTrackerPort]:
        """Get a mining performance tracker adapter instance."""
        tracker = self.mining_performance_tracker_repo.get_by_id(tracker_id)
        if not tracker:
            if self.logger:
                self.logger.error(
                    f"Mining Performance Tracker ID {tracker_id} not found or not a Mining Performance Tracker."
                )
            return None
        return await self._initialize_mining_performance_tracker_adapter(tracker)

    async def get_external_service(self, external_service_id: EntityId) -> Optional[ExternalServicePort]:
        """Get a specific external service instance by ID."""
        external_service = self.external_service_repo.get_by_id(external_service_id)
        if not external_service:
            if self.logger:
                self.logger.error(f"External Service ID {external_service_id} not found or not an External Service.")
            return None
        return await self._initialize_external_service(external_service)

    def get_rule_engine(self) -> Optional[RuleEngine]:
        """Creates a new Rule Engine instance."""
        try:
            # For now, we default to the 'custom' engine.
            # This could be driven by configuration in the future.
            factory = RuleEngineFactory()
            engine = factory.create(engine_type=RuleEngineType.CUSTOM, logger=self.logger)
            return engine
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create RuleEngine instance: {e}")
            return None

    def clear_all_adapters(self):
        """Clear adapter cache"""
        if self.logger:
            self.logger.info("Clearing all adapters.")
        self._instance_cache = {}  # Reset the cache

    def remove_adapter(self, entity_id: EntityId):
        """Remove a specific adapter from the cache."""
        if entity_id in self._instance_cache:
            del self._instance_cache[entity_id]
            if self.logger:
                self.logger.info(f"Removed adapter with ID {entity_id} from cache.")
        else:
            if self.logger:
                self.logger.warning(f"No adapter found with ID {entity_id} to remove.")

    def clear_all_services(self):
        """Clear external services cache"""
        if self.logger:
            self.logger.info("Clearing all external services.")
        self._service_cache = {}  # Reset the cache

    def remove_service(self, external_service_id: EntityId):
        """Remove a specific external service from the cache."""
        if external_service_id in self._service_cache:
            del self._service_cache[external_service_id]
            if self.logger:
                self.logger.info(f"Removed external service with ID {external_service_id} from cache.")
        else:
            if self.logger:
                self.logger.warning(f"No external service found with ID {external_service_id} to remove.")

    async def on_configuration_updated(self, event: ConfigurationUpdatedEvent) -> None:
        """Handler for cache invalidation when a configuration changes."""
        if self.logger:
            self.logger.debug(f"Cache invalidation: {event.entity_type} {event.entity_id} ({event.action})")

        if event.entity_id is None:
            return

        if event.entity_type == ConfigurationUpdatedEventType.EXTERNAL_SERVICE:
            # Invalidate the external service AND all adapters that may depend on it
            self._service_cache.pop(event.entity_id, None)
            self._instance_cache.clear()
        else:
            # Invalidate the specific adapter
            self._instance_cache.pop(event.entity_id, None)
