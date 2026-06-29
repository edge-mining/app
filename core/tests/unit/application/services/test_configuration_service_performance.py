"""Unit tests for Mining Performance Tracker CRUD on ConfigurationService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from edge_mining.application.events.common import (
    ConfigurationAction,
    ConfigurationUpdatedEventType,
)
from edge_mining.application.events.configuration_events import ConfigurationUpdatedEvent
from edge_mining.application.services.configuration_service import ConfigurationService
from edge_mining.domain.common import EntityId
from edge_mining.domain.optimization_unit.aggregate_roots import EnergyOptimizationUnit
from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.exceptions import (
    MiningPerformanceTrackerConfigurationError,
    MiningPerformanceTrackerNotFoundError,
)
from edge_mining.shared.adapter_configs.performance import (
    MiningPerformanceTrackerBraiinsPoolConfig,
    MiningPerformanceTrackerDummyConfig,
    MiningPerformanceTrackerOceanConfig,
)
from edge_mining.shared.infrastructure import PersistenceSettings


def make_entity_id() -> EntityId:
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
    ps = MagicMock(spec=PersistenceSettings)
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
        "energy_load_history_provider_repo",
        "home_profile_repo",
        "mining_performance_tracker_repo",
        "notifier_repo",
        "settings_repo",
        "climate_zone_repo",
        "climate_monitor_repo",
    ]:
        repo = MagicMock()
        repo.get_all.return_value = []
        repo.get_by_id.return_value = None
        setattr(ps, repo_name, repo)
    return ps


@pytest.fixture
def service(mock_persistence, mock_event_bus, logger):
    return ConfigurationService(
        persistence_settings=mock_persistence,
        event_bus=mock_event_bus,
        logger=logger,
    )


# --- add ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_dummy_tracker_persists_and_publishes_event(service, mock_persistence, mock_event_bus):
    config = MiningPerformanceTrackerDummyConfig()

    tracker = await service.add_mining_performance_tracker(
        name="dummy-1",
        adapter_type=MiningPerformanceTrackerAdapter.DUMMY,
        config=config,
    )

    assert isinstance(tracker, MiningPerformanceTracker)
    assert tracker.name == "dummy-1"
    assert tracker.adapter_type == MiningPerformanceTrackerAdapter.DUMMY
    assert tracker.config == config

    mock_persistence.mining_performance_tracker_repo.add.assert_called_once_with(tracker)
    mock_event_bus.publish.assert_awaited_once()
    event = mock_event_bus.publish.call_args[0][0]
    assert isinstance(event, ConfigurationUpdatedEvent)
    assert event.entity_type == ConfigurationUpdatedEventType.MINING_PERFORMANCE_TRACKER
    assert event.action == ConfigurationAction.CREATED
    assert event.entity_id == tracker.id


@pytest.mark.asyncio
async def test_add_ocean_tracker_with_valid_config(service, mock_persistence):
    config = MiningPerformanceTrackerOceanConfig(bitcoin_address="bc1qabc")

    tracker = await service.add_mining_performance_tracker(
        name="ocean-1",
        adapter_type=MiningPerformanceTrackerAdapter.OCEAN,
        config=config,
    )
    assert tracker.adapter_type == MiningPerformanceTrackerAdapter.OCEAN
    mock_persistence.mining_performance_tracker_repo.add.assert_called_once()


@pytest.mark.asyncio
async def test_add_rejects_invalid_config(service, mock_event_bus):
    # Ocean config with empty address is invalid
    bad = MiningPerformanceTrackerOceanConfig(bitcoin_address="")

    with pytest.raises(MiningPerformanceTrackerConfigurationError):
        await service.add_mining_performance_tracker(
            name="bad",
            adapter_type=MiningPerformanceTrackerAdapter.OCEAN,
            config=bad,
        )

    mock_event_bus.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_rejects_none_config(service):
    with pytest.raises(MiningPerformanceTrackerConfigurationError):
        await service.add_mining_performance_tracker(
            name="missing-config",
            adapter_type=MiningPerformanceTrackerAdapter.DUMMY,
            config=None,
        )


@pytest.mark.asyncio
async def test_add_rejects_wrong_adapter_config_pairing(service):
    # Pass a Dummy config with the Ocean adapter type: is_valid returns False
    wrong = MiningPerformanceTrackerDummyConfig()
    with pytest.raises(MiningPerformanceTrackerConfigurationError):
        await service.add_mining_performance_tracker(
            name="cross",
            adapter_type=MiningPerformanceTrackerAdapter.OCEAN,
            config=wrong,
        )


# --- get / list ---------------------------------------------------------------


def test_get_returns_tracker_when_present(service, mock_persistence):
    tracker_id = make_entity_id()
    tracker = MiningPerformanceTracker(
        id=tracker_id,
        name="t1",
        adapter_type=MiningPerformanceTrackerAdapter.DUMMY,
        config=MiningPerformanceTrackerDummyConfig(),
    )
    mock_persistence.mining_performance_tracker_repo.get_by_id.return_value = tracker

    assert service.get_mining_performance_tracker(tracker_id) is tracker


def test_get_raises_when_missing(service, mock_persistence):
    mock_persistence.mining_performance_tracker_repo.get_by_id.return_value = None
    with pytest.raises(MiningPerformanceTrackerNotFoundError):
        service.get_mining_performance_tracker(make_entity_id())


def test_list_delegates_to_repo(service, mock_persistence):
    sample = [MiningPerformanceTracker(name="a"), MiningPerformanceTracker(name="b")]
    mock_persistence.mining_performance_tracker_repo.get_all.return_value = sample

    assert service.list_mining_performance_trackers() == sample


# --- update -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_changes_fields_and_publishes(service, mock_persistence, mock_event_bus):
    tracker_id = make_entity_id()
    tracker = MiningPerformanceTracker(
        id=tracker_id,
        name="old",
        adapter_type=MiningPerformanceTrackerAdapter.OCEAN,
        config=MiningPerformanceTrackerOceanConfig(bitcoin_address="bc1qold"),
    )
    mock_persistence.mining_performance_tracker_repo.get_by_id.return_value = tracker

    new_config = MiningPerformanceTrackerOceanConfig(bitcoin_address="bc1qnew")
    updated = await service.update_mining_performance_tracker(
        tracker_id=tracker_id,
        name="new",
        config=new_config,
    )

    assert updated.name == "new"
    assert updated.config is new_config
    mock_persistence.mining_performance_tracker_repo.update.assert_called_once_with(tracker)

    mock_event_bus.publish.assert_awaited_once()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.entity_type == ConfigurationUpdatedEventType.MINING_PERFORMANCE_TRACKER
    assert event.action == ConfigurationAction.UPDATED
    assert event.entity_id == tracker_id


@pytest.mark.asyncio
async def test_update_missing_tracker_raises(service, mock_persistence):
    mock_persistence.mining_performance_tracker_repo.get_by_id.return_value = None
    with pytest.raises(MiningPerformanceTrackerNotFoundError):
        await service.update_mining_performance_tracker(
            tracker_id=make_entity_id(),
            name="x",
            config=MiningPerformanceTrackerDummyConfig(),
        )


# --- remove + unlink ----------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_unlinks_from_optimization_units_and_publishes(service, mock_persistence, mock_event_bus):
    tracker_id = make_entity_id()
    other_tracker_id = make_entity_id()
    tracker = MiningPerformanceTracker(
        id=tracker_id,
        name="to-remove",
        adapter_type=MiningPerformanceTrackerAdapter.DUMMY,
        config=MiningPerformanceTrackerDummyConfig(),
    )
    unit_linked = EnergyOptimizationUnit(name="linked")
    unit_linked.performance_tracker_id = tracker_id
    unit_other = EnergyOptimizationUnit(name="other")
    unit_other.performance_tracker_id = other_tracker_id
    unit_none = EnergyOptimizationUnit(name="none")

    mock_persistence.mining_performance_tracker_repo.get_by_id.return_value = tracker
    mock_persistence.optimization_unit_repo.get_all.return_value = [unit_linked, unit_other, unit_none]

    removed = await service.remove_mining_performance_tracker(tracker_id)

    assert removed is tracker
    assert unit_linked.performance_tracker_id is None
    assert unit_other.performance_tracker_id == other_tracker_id
    assert unit_none.performance_tracker_id is None
    mock_persistence.optimization_unit_repo.update.assert_called_once_with(unit_linked)
    mock_persistence.mining_performance_tracker_repo.remove.assert_called_once_with(tracker_id)

    mock_event_bus.publish.assert_awaited_once()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.entity_type == ConfigurationUpdatedEventType.MINING_PERFORMANCE_TRACKER
    assert event.action == ConfigurationAction.REMOVED
    assert event.entity_id == tracker_id


@pytest.mark.asyncio
async def test_remove_missing_tracker_raises(service, mock_persistence):
    mock_persistence.mining_performance_tracker_repo.get_by_id.return_value = None
    with pytest.raises(MiningPerformanceTrackerNotFoundError):
        await service.remove_mining_performance_tracker(make_entity_id())


@pytest.mark.asyncio
async def test_unlink_updates_only_linked_units(service, mock_persistence):
    tracker_id = make_entity_id()
    unit_a = EnergyOptimizationUnit(name="a")
    unit_a.performance_tracker_id = tracker_id
    unit_b = EnergyOptimizationUnit(name="b")
    unit_b.performance_tracker_id = None
    mock_persistence.optimization_unit_repo.get_all.return_value = [unit_a, unit_b]

    await service.unlink_mining_performance_tracker(tracker_id)

    assert unit_a.performance_tracker_id is None
    assert unit_b.performance_tracker_id is None
    mock_persistence.optimization_unit_repo.update.assert_called_once_with(unit_a)


# --- check --------------------------------------------------------------------


def test_check_accepts_valid_tracker(service):
    tracker = MiningPerformanceTracker(
        name="ok",
        adapter_type=MiningPerformanceTrackerAdapter.OCEAN,
        config=MiningPerformanceTrackerOceanConfig(bitcoin_address="bc1qok"),
    )
    assert service.check_mining_performance_tracker(tracker) is True


def test_check_rejects_missing_config(service):
    tracker = MiningPerformanceTracker(
        name="bad",
        adapter_type=MiningPerformanceTrackerAdapter.DUMMY,
        config=None,
    )
    with pytest.raises(MiningPerformanceTrackerConfigurationError):
        service.check_mining_performance_tracker(tracker)


def test_check_rejects_missing_external_service(service, mock_persistence):
    mock_persistence.external_service_repo.get_by_id.return_value = None
    tracker = MiningPerformanceTracker(
        name="bad",
        adapter_type=MiningPerformanceTrackerAdapter.DUMMY,
        config=MiningPerformanceTrackerDummyConfig(),
        external_service_id=make_entity_id(),
    )
    from edge_mining.shared.external_services.exceptions import ExternalServiceNotFoundError

    with pytest.raises(ExternalServiceNotFoundError):
        service.check_mining_performance_tracker(tracker)


# --- helpers ------------------------------------------------------------------


def test_get_config_by_type_returns_registered_class(service):
    result = service.get_mining_performance_tracker_config_by_type(MiningPerformanceTrackerAdapter.OCEAN)
    assert result is MiningPerformanceTrackerOceanConfig


def test_get_config_by_type_for_braiins(service):
    result = service.get_mining_performance_tracker_config_by_type(MiningPerformanceTrackerAdapter.BRAIINS_POOL)
    assert result is MiningPerformanceTrackerBraiinsPoolConfig


def test_external_service_adapter_is_none_for_all_current_trackers(service):
    for adapter_type in MiningPerformanceTrackerAdapter:
        assert service.get_mining_performance_tracker_external_service_adapter(adapter_type) is None
