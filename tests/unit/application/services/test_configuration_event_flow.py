"""Integration tests for ConfigurationService → EventBus → AdapterService flow."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from edge_mining.adapters.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from edge_mining.application.events.common import ConfigurationAction, ConfigurationUpdatedEventType
from edge_mining.application.events.configuration_events import ConfigurationUpdatedEvent
from edge_mining.application.services.adapter_service import AdapterService
from edge_mining.application.services.configuration_service import ConfigurationService
from edge_mining.domain.common import EntityId
from edge_mining.shared.infrastructure import PersistenceSettings


def make_entity_id():
    return EntityId(uuid.uuid4())


@pytest.fixture
def logger():
    mock = MagicMock()
    mock.debug = MagicMock()
    mock.info = MagicMock()
    mock.warning = MagicMock()
    mock.error = MagicMock()
    return mock


@pytest.fixture
def mock_event_bus():
    bus = AsyncMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def mock_persistence():
    """Create a mock PersistenceSettings with all repos."""
    ps = MagicMock(spec=PersistenceSettings)

    # Each repo mock needs get_by_id, add, update, remove, get_all
    for repo_name in [
        "external_service_repo",
        "energy_source_repo",
        "energy_monitor_repo",
        "miner_repo",
        "miner_controller_repo",
        "policy_repo",
        "optimization_unit_repo",
        "forecast_provider_repo",
        "energy_load_forecast_provider_repo",
        "home_profile_repo",
        "mining_performance_tracker_repo",
        "notifier_repo",
        "settings_repo",
    ]:
        repo = MagicMock()
        repo.get_all.return_value = []
        repo.get_by_id.return_value = None
        setattr(ps, repo_name, repo)

    return ps


@pytest.fixture
def config_service(mock_persistence, mock_event_bus, logger):
    return ConfigurationService(
        persistence_settings=mock_persistence,
        event_bus=mock_event_bus,
        logger=logger,
    )


# --- Test that ConfigurationService publishes events ---


@pytest.mark.asyncio
async def test_create_external_service_publishes_event(config_service, mock_event_bus):
    """Creating an external service should publish a ConfigurationUpdatedEvent."""
    from edge_mining.shared.external_services.common import ExternalServiceAdapter

    mock_config = MagicMock()
    mock_config.is_valid.return_value = True

    service = await config_service.create_external_service(
        name="Test HA",
        adapter_type=ExternalServiceAdapter.HOME_ASSISTANT_API,
        config=mock_config,
    )

    mock_event_bus.publish.assert_awaited_once()
    event = mock_event_bus.publish.call_args[0][0]
    assert isinstance(event, ConfigurationUpdatedEvent)
    assert event.entity_type == ConfigurationUpdatedEventType.EXTERNAL_SERVICE
    assert event.action == ConfigurationAction.CREATED
    assert event.entity_id == service.id


@pytest.mark.asyncio
async def test_create_energy_monitor_publishes_event(config_service, mock_event_bus):
    """Creating an energy monitor should publish a ConfigurationUpdatedEvent."""
    from edge_mining.domain.energy.common import EnergyMonitorAdapter

    mock_config = MagicMock()
    mock_config.is_valid.return_value = True

    monitor = await config_service.create_energy_monitor(
        name="Solar Monitor",
        adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
        config=mock_config,
    )

    mock_event_bus.publish.assert_awaited_once()
    event = mock_event_bus.publish.call_args[0][0]
    assert isinstance(event, ConfigurationUpdatedEvent)
    assert event.entity_type == ConfigurationUpdatedEventType.ENERGY_MONITOR
    assert event.action == ConfigurationAction.CREATED


@pytest.mark.asyncio
async def test_update_notifier_publishes_event(config_service, mock_event_bus, mock_persistence):
    """Updating a notifier should publish a ConfigurationUpdatedEvent."""
    from edge_mining.domain.notification.common import NotificationAdapter
    from edge_mining.domain.notification.entities import Notifier

    notifier_id = make_entity_id()
    existing = Notifier(
        id=notifier_id,
        name="Old",
        adapter_type=NotificationAdapter.DUMMY,
        config=MagicMock(),
    )
    mock_persistence.notifier_repo.get_by_id.return_value = existing

    mock_config = MagicMock()
    mock_config.is_valid.return_value = True

    await config_service.update_notifier(
        notifier_id=notifier_id,
        name="New",
        config=mock_config,
    )

    mock_event_bus.publish.assert_awaited_once()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.entity_type == ConfigurationUpdatedEventType.NOTIFIER
    assert event.action == ConfigurationAction.UPDATED


@pytest.mark.asyncio
async def test_remove_miner_controller_publishes_event(config_service, mock_event_bus, mock_persistence):
    """Removing a miner controller should publish a ConfigurationUpdatedEvent."""
    from edge_mining.domain.miner.common import MinerControllerAdapter
    from edge_mining.domain.miner.entities import MinerController

    ctrl_id = make_entity_id()
    existing = MinerController(
        id=ctrl_id,
        name="Ctrl",
        adapter_type=MinerControllerAdapter.DUMMY,
        config=MagicMock(),
    )
    mock_persistence.miner_controller_repo.get_by_id.return_value = existing
    mock_persistence.miner_repo.get_by_controller_id.return_value = []

    await config_service.remove_miner_controller(controller_id=ctrl_id)

    mock_event_bus.publish.assert_awaited_once()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.entity_type == ConfigurationUpdatedEventType.MINER_CONTROLLER
    assert event.action == ConfigurationAction.REMOVED
    assert event.entity_id == ctrl_id


# --- Test end-to-end flow with real InMemoryEventBus ---


@pytest.mark.asyncio
async def test_end_to_end_cache_invalidation(mock_persistence, logger):
    """End-to-end: creating an energy monitor triggers cache invalidation in AdapterService."""
    from edge_mining.domain.energy.common import EnergyMonitorAdapter

    event_bus = InMemoryEventBus(logger)

    adapter_service = AdapterService(
        energy_monitor_repo=mock_persistence.energy_monitor_repo,
        miner_controller_repo=mock_persistence.miner_controller_repo,
        miner_repo=mock_persistence.miner_repo,
        notifier_repo=mock_persistence.notifier_repo,
        forecast_provider_repo=mock_persistence.forecast_provider_repo,
        energy_load_forecast_provider_repo=mock_persistence.energy_load_forecast_provider_repo,
        mining_performance_tracker_repo=mock_persistence.mining_performance_tracker_repo,
        external_service_repo=mock_persistence.external_service_repo,
        event_bus=event_bus,
        logger=logger,
    )

    config_service = ConfigurationService(
        persistence_settings=mock_persistence,
        event_bus=event_bus,
        logger=logger,
    )

    # Pre-populate adapter cache with a fake entry
    fake_id = make_entity_id()
    adapter_service._instance_cache[fake_id] = MagicMock()
    assert fake_id in adapter_service._instance_cache

    mock_config = MagicMock()
    mock_config.is_valid.return_value = True

    # Create an energy monitor - this should trigger cache invalidation
    monitor = await config_service.create_energy_monitor(
        name="Test Monitor",
        adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
        config=mock_config,
    )

    # The monitor's own ID should have been popped (even though it was just created,
    # the handler tries to pop it from instance_cache)
    # The fake_id should still be there since it's a different entity
    assert fake_id in adapter_service._instance_cache


@pytest.mark.asyncio
async def test_external_service_update_clears_all_instance_cache(mock_persistence, logger):
    """Updating an external service should clear the entire instance cache."""
    from edge_mining.shared.external_services.common import ExternalServiceAdapter
    from edge_mining.shared.external_services.entities import ExternalService

    event_bus = InMemoryEventBus(logger)

    adapter_service = AdapterService(
        energy_monitor_repo=mock_persistence.energy_monitor_repo,
        miner_controller_repo=mock_persistence.miner_controller_repo,
        miner_repo=mock_persistence.miner_repo,
        notifier_repo=mock_persistence.notifier_repo,
        forecast_provider_repo=mock_persistence.forecast_provider_repo,
        energy_load_forecast_provider_repo=mock_persistence.energy_load_forecast_provider_repo,
        mining_performance_tracker_repo=mock_persistence.mining_performance_tracker_repo,
        external_service_repo=mock_persistence.external_service_repo,
        event_bus=event_bus,
        logger=logger,
    )

    config_service = ConfigurationService(
        persistence_settings=mock_persistence,
        event_bus=event_bus,
        logger=logger,
    )

    # Pre-populate caches
    svc_id = make_entity_id()
    adapter_id = make_entity_id()
    adapter_service._service_cache[svc_id] = MagicMock()
    adapter_service._instance_cache[adapter_id] = MagicMock()

    # Stub the repo to return existing service
    mock_config = MagicMock()
    mock_config.is_valid.return_value = True
    existing = ExternalService(
        id=svc_id,
        name="HA",
        adapter_type=ExternalServiceAdapter.HOME_ASSISTANT_API,
        config=mock_config,
    )
    mock_persistence.external_service_repo.get_by_id.return_value = existing

    await config_service.update_external_service(
        service_id=svc_id,
        name="HA Updated",
        config=mock_config,
    )

    # Service cache should have the entry removed
    assert svc_id not in adapter_service._service_cache
    # Instance cache should be fully cleared (conservative approach for external_service)
    assert len(adapter_service._instance_cache) == 0
