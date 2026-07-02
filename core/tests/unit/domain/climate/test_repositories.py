"""Unit tests for InMemory Climate repositories."""

import uuid

import pytest

from edge_mining.adapters.domain.climate.repositories import (
    InMemoryClimateMonitorRepository,
    InMemoryClimateZoneRepository,
)
from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateMonitor, ClimateZone
from edge_mining.domain.climate.exceptions import (
    ClimateMonitorAlreadyExistsError,
    ClimateMonitorNotFoundError,
    ClimateZoneAlreadyExistsError,
    ClimateZoneNotFoundError,
)
from edge_mining.domain.common import EntityId


@pytest.fixture
def zone_repo() -> InMemoryClimateZoneRepository:
    return InMemoryClimateZoneRepository()


@pytest.fixture
def monitor_repo() -> InMemoryClimateMonitorRepository:
    return InMemoryClimateMonitorRepository()


def _make_zone(name: str = "Test Zone", area: float = 20.0) -> ClimateZone:
    return ClimateZone(id=EntityId(uuid.uuid4()), name=name, area_sqm=area)


def _make_monitor(name: str = "Test Monitor", ext_svc_id: EntityId = None) -> ClimateMonitor:
    return ClimateMonitor(
        id=EntityId(uuid.uuid4()),
        name=name,
        adapter_type=ClimateMonitorAdapter.HOME_ASSISTANT_API,
        external_service_id=ext_svc_id,
    )


class TestInMemoryClimateZoneRepository:
    """Tests for InMemoryClimateZoneRepository."""

    def test_add_and_get_by_id(self, zone_repo):
        zone = _make_zone()
        zone_repo.add(zone)
        result = zone_repo.get_by_id(zone.id)
        assert result is not None
        assert result.id == zone.id
        assert result.name == "Test Zone"

    def test_get_by_id_not_found(self, zone_repo):
        result = zone_repo.get_by_id(EntityId(uuid.uuid4()))
        assert result is None

    def test_get_all_empty(self, zone_repo):
        assert zone_repo.get_all() == []

    def test_get_all_multiple(self, zone_repo):
        z1 = _make_zone("Zone A")
        z2 = _make_zone("Zone B")
        zone_repo.add(z1)
        zone_repo.add(z2)
        result = zone_repo.get_all()
        assert len(result) == 2

    def test_update(self, zone_repo):
        zone = _make_zone()
        zone_repo.add(zone)
        zone.name = "Updated Name"
        zone_repo.update(zone)
        result = zone_repo.get_by_id(zone.id)
        assert result.name == "Updated Name"

    def test_update_not_found(self, zone_repo):
        zone = _make_zone()
        with pytest.raises(ClimateZoneNotFoundError):
            zone_repo.update(zone)

    def test_remove(self, zone_repo):
        zone = _make_zone()
        zone_repo.add(zone)
        zone_repo.remove(zone.id)
        assert zone_repo.get_by_id(zone.id) is None

    def test_remove_not_found(self, zone_repo):
        with pytest.raises(ClimateZoneNotFoundError):
            zone_repo.remove(EntityId(uuid.uuid4()))

    def test_add_duplicate_raises(self, zone_repo):
        zone = _make_zone()
        zone_repo.add(zone)
        with pytest.raises(ClimateZoneAlreadyExistsError):
            zone_repo.add(zone)

    def test_returns_deep_copies(self, zone_repo):
        zone = _make_zone()
        zone_repo.add(zone)
        result = zone_repo.get_by_id(zone.id)
        result.name = "Mutated"
        original = zone_repo.get_by_id(zone.id)
        assert original.name == "Test Zone"


class TestInMemoryClimateMonitorRepository:
    """Tests for InMemoryClimateMonitorRepository."""

    def test_add_and_get_by_id(self, monitor_repo):
        monitor = _make_monitor()
        monitor_repo.add(monitor)
        result = monitor_repo.get_by_id(monitor.id)
        assert result is not None
        assert result.id == monitor.id

    def test_get_by_id_not_found(self, monitor_repo):
        result = monitor_repo.get_by_id(EntityId(uuid.uuid4()))
        assert result is None

    def test_get_all_empty(self, monitor_repo):
        assert monitor_repo.get_all() == []

    def test_get_all_multiple(self, monitor_repo):
        m1 = _make_monitor("Monitor A")
        m2 = _make_monitor("Monitor B")
        monitor_repo.add(m1)
        monitor_repo.add(m2)
        assert len(monitor_repo.get_all()) == 2

    def test_update(self, monitor_repo):
        monitor = _make_monitor()
        monitor_repo.add(monitor)
        monitor.name = "Updated"
        monitor_repo.update(monitor)
        result = monitor_repo.get_by_id(monitor.id)
        assert result.name == "Updated"

    def test_update_not_found(self, monitor_repo):
        monitor = _make_monitor()
        with pytest.raises(ClimateMonitorNotFoundError):
            monitor_repo.update(monitor)

    def test_remove(self, monitor_repo):
        monitor = _make_monitor()
        monitor_repo.add(monitor)
        monitor_repo.remove(monitor.id)
        assert monitor_repo.get_by_id(monitor.id) is None

    def test_remove_not_found(self, monitor_repo):
        with pytest.raises(ClimateMonitorNotFoundError):
            monitor_repo.remove(EntityId(uuid.uuid4()))

    def test_add_duplicate_raises(self, monitor_repo):
        monitor = _make_monitor()
        monitor_repo.add(monitor)
        with pytest.raises(ClimateMonitorAlreadyExistsError):
            monitor_repo.add(monitor)

    def test_get_by_external_service_id(self, monitor_repo):
        ext_id = EntityId(uuid.uuid4())
        m1 = _make_monitor("M1", ext_svc_id=ext_id)
        m2 = _make_monitor("M2", ext_svc_id=ext_id)
        m3 = _make_monitor("M3", ext_svc_id=EntityId(uuid.uuid4()))
        monitor_repo.add(m1)
        monitor_repo.add(m2)
        monitor_repo.add(m3)
        results = monitor_repo.get_by_external_service_id(ext_id)
        assert len(results) == 2
        assert all(r.external_service_id == ext_id for r in results)

    def test_get_by_external_service_id_empty(self, monitor_repo):
        results = monitor_repo.get_by_external_service_id(EntityId(uuid.uuid4()))
        assert results == []

    def test_returns_deep_copies(self, monitor_repo):
        monitor = _make_monitor()
        monitor_repo.add(monitor)
        result = monitor_repo.get_by_id(monitor.id)
        result.name = "Mutated"
        original = monitor_repo.get_by_id(monitor.id)
        assert original.name == "Test Monitor"
