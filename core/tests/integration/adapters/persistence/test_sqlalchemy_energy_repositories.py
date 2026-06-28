"""Integration tests for SQLAlchemy Energy repositories.

These tests verify that the SQLAlchemy repositories correctly persist and retrieve
domain entities with their value objects (Battery, Grid, Watts) using the imperative
mapping and event listeners defined in tables.py.
"""

import uuid

import pytest

from edge_mining.adapters.domain.energy.repositories import (
    SqlAlchemyEnergyMonitorRepository,
    SqlAlchemyEnergySourceRepository,
)
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.base import BaseSQLAlchemyRepository
from edge_mining.domain.common import EntityId, WattHours, Watts
from edge_mining.domain.energy.common import EnergyMonitorAdapter, EnergySourceType
from edge_mining.domain.energy.entities import EnergyMonitor, EnergySource
from edge_mining.domain.energy.value_objects import Battery, Grid
from edge_mining.shared.adapter_configs.energy import EnergyMonitorDummySolarConfig


class TestSqlAlchemyEnergySourceRepository:
    """Integration tests for SqlAlchemyEnergySourceRepository.

    These tests verify CRUD operations and value object persistence.
    """

    @pytest.fixture
    def repository(self, sqlalchemy_repo: BaseSQLAlchemyRepository) -> SqlAlchemyEnergySourceRepository:
        """Create an EnergySource repository instance."""
        return SqlAlchemyEnergySourceRepository(db=sqlalchemy_repo)

    def test_add_and_get_simple_energy_source(self, repository: SqlAlchemyEnergySourceRepository):
        """Test adding and retrieving a simple energy source."""
        # Create a simple energy source
        energy_source = EnergySource(
            name="Solar Panel System",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(6000.0),
        )
        original_id = energy_source.id

        # Add to repository
        repository.add(energy_source)

        # Retrieve and verify
        retrieved = repository.get_by_id(original_id)
        assert retrieved is not None
        assert retrieved.id == original_id
        assert retrieved.name == "Solar Panel System"
        assert retrieved.type == EnergySourceType.SOLAR
        assert isinstance(retrieved.nominal_power_max, type(Watts(0.0)))
        assert float(retrieved.nominal_power_max) == 6000.0

    def test_add_energy_source_with_battery(self, repository: SqlAlchemyEnergySourceRepository):
        """Test adding energy source with Battery value object."""
        battery = Battery(nominal_capacity=WattHours(10000.0))
        energy_source = EnergySource(
            name="Solar with Storage",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(5000.0),
        )
        energy_source.connect_to_storage(battery)

        repository.add(energy_source)

        # Retrieve and verify battery is correctly deserialized
        retrieved = repository.get_by_id(energy_source.id)
        assert retrieved is not None
        assert retrieved.storage is not None
        assert isinstance(retrieved.storage, Battery)
        assert float(retrieved.storage.nominal_capacity) == 10000.0

    def test_add_energy_source_with_grid(self, repository: SqlAlchemyEnergySourceRepository):
        """Test adding energy source with Grid value object."""
        grid = Grid(contracted_power=Watts(3000.0))
        energy_source = EnergySource(
            name="Solar with Grid",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(5000.0),
        )
        energy_source.connect_to_grid(grid)

        repository.add(energy_source)

        # Retrieve and verify grid is correctly deserialized
        retrieved = repository.get_by_id(energy_source.id)
        assert retrieved is not None
        assert retrieved.grid is not None
        assert isinstance(retrieved.grid, Grid)
        assert float(retrieved.grid.contracted_power) == 3000.0

    def test_add_energy_source_with_all_value_objects(self, repository: SqlAlchemyEnergySourceRepository):
        """Test adding energy source with all value objects (Battery, Grid, external_source)."""
        battery = Battery(nominal_capacity=WattHours(20000.0))
        grid = Grid(contracted_power=Watts(5000.0))

        energy_source = EnergySource(
            name="Complete Solar System",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(8000.0),
        )
        energy_source.connect_to_storage(battery)
        energy_source.connect_to_grid(grid)
        energy_source.external_source = Watts(1000.0)

        repository.add(energy_source)

        # Retrieve and verify all value objects
        retrieved = repository.get_by_id(energy_source.id)
        assert retrieved is not None
        assert retrieved.storage is not None
        assert float(retrieved.storage.nominal_capacity) == 20000.0
        assert retrieved.grid is not None
        assert float(retrieved.grid.contracted_power) == 5000.0
        assert retrieved.external_source is not None
        assert float(retrieved.external_source) == 1000.0

    def test_get_all(self, repository: SqlAlchemyEnergySourceRepository):
        """Test retrieving all energy sources."""
        # Add multiple energy sources
        source1 = EnergySource(name="Solar 1", type=EnergySourceType.SOLAR, nominal_power_max=Watts(3000.0))
        source2 = EnergySource(name="Wind 1", type=EnergySourceType.WIND, nominal_power_max=Watts(2000.0))
        source3 = EnergySource(name="Hydro 1", type=EnergySourceType.HYDROELECTRIC, nominal_power_max=Watts(5000.0))

        repository.add(source1)
        repository.add(source2)
        repository.add(source3)

        # Retrieve all
        all_sources = repository.get_all()
        assert len(all_sources) == 3

        names = {source.name for source in all_sources}
        assert "Solar 1" in names
        assert "Wind 1" in names
        assert "Hydro 1" in names

    def test_update_energy_source(self, repository: SqlAlchemyEnergySourceRepository):
        """Test updating an energy source."""
        energy_source = EnergySource(
            name="Original Name",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(3000.0),
        )
        repository.add(energy_source)

        # Update properties
        energy_source.name = "Updated Name"
        energy_source.nominal_power_max = Watts(4000.0)
        battery = Battery(nominal_capacity=WattHours(15000.0))
        energy_source.connect_to_storage(battery)

        repository.update(energy_source)

        # Retrieve and verify updates
        retrieved = repository.get_by_id(energy_source.id)
        assert retrieved is not None
        assert retrieved.name == "Updated Name"
        assert float(retrieved.nominal_power_max) == 4000.0
        assert retrieved.storage is not None
        assert float(retrieved.storage.nominal_capacity) == 15000.0

    def test_update_removes_optional_value_objects(self, repository: SqlAlchemyEnergySourceRepository):
        """Test that updating can remove optional value objects (set to None)."""
        battery = Battery(nominal_capacity=WattHours(10000.0))
        energy_source = EnergySource(
            name="Solar with Battery",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(5000.0),
        )
        energy_source.connect_to_storage(battery)
        repository.add(energy_source)

        # Disconnect battery
        energy_source.disconnect_from_storage()
        repository.update(energy_source)

        # Verify battery is removed
        retrieved = repository.get_by_id(energy_source.id)
        assert retrieved is not None
        assert retrieved.storage is None

    def test_remove_energy_source(self, repository: SqlAlchemyEnergySourceRepository):
        """Test removing an energy source."""
        energy_source = EnergySource(
            name="To Be Removed",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(2000.0),
        )
        repository.add(energy_source)

        # Verify it exists
        assert repository.get_by_id(energy_source.id) is not None

        # Remove
        repository.remove(energy_source.id)

        # Verify it's gone
        assert repository.get_by_id(energy_source.id) is None

    def test_get_by_id_nonexistent(self, repository: SqlAlchemyEnergySourceRepository):
        """Test getting a nonexistent energy source returns None."""
        fake_id = EntityId(uuid.uuid4())
        result = repository.get_by_id(fake_id)
        assert result is None

    def test_persistence_of_watts_value_objects(self, repository: SqlAlchemyEnergySourceRepository):
        """Test that Watts value objects are correctly persisted as floats and reconstructed."""
        energy_source = EnergySource(
            name="Watts Test",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(7500.5),
        )
        energy_source.external_source = Watts(1250.75)

        repository.add(energy_source)

        # Retrieve and verify Watts types are restored
        retrieved = repository.get_by_id(energy_source.id)
        assert retrieved is not None
        assert isinstance(retrieved.nominal_power_max, type(Watts(0.0)))
        assert float(retrieved.nominal_power_max) == 7500.5
        assert isinstance(retrieved.external_source, type(Watts(0.0)))
        assert float(retrieved.external_source) == 1250.75


class TestSqlAlchemyEnergyMonitorRepository:
    """Integration tests for SqlAlchemyEnergyMonitorRepository.

    These tests verify CRUD operations and config serialization/deserialization.
    """

    @pytest.fixture
    def repository(self, sqlalchemy_repo: BaseSQLAlchemyRepository) -> SqlAlchemyEnergyMonitorRepository:
        """Create an EnergyMonitor repository instance."""
        return SqlAlchemyEnergyMonitorRepository(db=sqlalchemy_repo)

    def test_add_and_get_energy_monitor(self, repository: SqlAlchemyEnergyMonitorRepository):
        """Test adding and retrieving an energy monitor."""
        config = EnergyMonitorDummySolarConfig()
        energy_monitor = EnergyMonitor(
            name="Test Monitor",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=config,
        )
        original_id = energy_monitor.id

        repository.add(energy_monitor)

        # Retrieve and verify
        retrieved = repository.get_by_id(original_id)
        assert retrieved is not None
        assert retrieved.id == original_id
        assert retrieved.name == "Test Monitor"
        assert retrieved.adapter_type == EnergyMonitorAdapter.DUMMY_SOLAR
        assert retrieved.config is not None
        assert isinstance(retrieved.config, EnergyMonitorDummySolarConfig)

    def test_add_energy_monitor_without_config(self, repository: SqlAlchemyEnergyMonitorRepository):
        """Test adding energy monitor without config (None)."""
        energy_monitor = EnergyMonitor(
            name="No Config Monitor",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )

        repository.add(energy_monitor)

        # Retrieve and verify
        retrieved = repository.get_by_id(energy_monitor.id)
        assert retrieved is not None
        assert retrieved.config is None

    def test_get_all(self, repository: SqlAlchemyEnergyMonitorRepository):
        """Test retrieving all energy monitors."""
        config1 = EnergyMonitorDummySolarConfig()
        config2 = EnergyMonitorDummySolarConfig()

        monitor1 = EnergyMonitor(name="Monitor 1", adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR, config=config1)
        monitor2 = EnergyMonitor(name="Monitor 2", adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR, config=config2)

        repository.add(monitor1)
        repository.add(monitor2)

        all_monitors = repository.get_all()
        assert len(all_monitors) == 2

        names = {monitor.name for monitor in all_monitors}
        assert "Monitor 1" in names
        assert "Monitor 2" in names

    def test_update_energy_monitor(self, repository: SqlAlchemyEnergyMonitorRepository):
        """Test updating an energy monitor."""
        config = EnergyMonitorDummySolarConfig()
        energy_monitor = EnergyMonitor(
            name="Original Monitor",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=config,
        )
        repository.add(energy_monitor)

        # Update properties
        energy_monitor.name = "Updated Monitor"
        repository.update(energy_monitor)

        # Retrieve and verify
        retrieved = repository.get_by_id(energy_monitor.id)
        assert retrieved is not None
        assert retrieved.name == "Updated Monitor"

    def test_remove_energy_monitor(self, repository: SqlAlchemyEnergyMonitorRepository):
        """Test removing an energy monitor."""
        config = EnergyMonitorDummySolarConfig()
        energy_monitor = EnergyMonitor(
            name="To Be Removed",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=config,
        )
        repository.add(energy_monitor)

        # Verify it exists
        assert repository.get_by_id(energy_monitor.id) is not None

        # Remove
        repository.remove(energy_monitor.id)

        # Verify it's gone
        assert repository.get_by_id(energy_monitor.id) is None

    def test_get_by_external_service_id(self, repository: SqlAlchemyEnergyMonitorRepository):
        """Test retrieving energy monitors by external service ID."""
        external_service_id = EntityId(uuid.uuid4())
        other_service_id = EntityId(uuid.uuid4())

        config = EnergyMonitorDummySolarConfig()

        # Create monitors with same external service ID
        monitor1 = EnergyMonitor(
            name="Monitor 1",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=config,
            external_service_id=external_service_id,
        )
        monitor2 = EnergyMonitor(
            name="Monitor 2",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=config,
            external_service_id=external_service_id,
        )
        monitor3 = EnergyMonitor(
            name="Monitor 3",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=config,
            external_service_id=other_service_id,
        )

        repository.add(monitor1)
        repository.add(monitor2)
        repository.add(monitor3)

        # Get by external service ID
        monitors = repository.get_by_external_service_id(external_service_id)
        assert len(monitors) == 2

        names = {monitor.name for monitor in monitors}
        assert "Monitor 1" in names
        assert "Monitor 2" in names
        assert "Monitor 3" not in names

    def test_config_serialization_round_trip(self, repository: SqlAlchemyEnergyMonitorRepository):
        """Test that config objects survive serialization round trip."""
        config = EnergyMonitorDummySolarConfig()
        energy_monitor = EnergyMonitor(
            name="Config Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=config,
        )

        repository.add(energy_monitor)

        # Retrieve and verify config type is preserved
        retrieved = repository.get_by_id(energy_monitor.id)
        assert retrieved is not None
        assert retrieved.config is not None
        assert type(retrieved.config) == type(config)
        assert isinstance(retrieved.config, EnergyMonitorDummySolarConfig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
