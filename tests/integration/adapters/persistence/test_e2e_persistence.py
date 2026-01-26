"""End-to-end integration tests for SQLAlchemy persistence layer.

These tests verify the complete flow: database initialization → migrations →
CRUD operations → value object persistence → querying across entities.
"""

import uuid

import pytest
from sqlalchemy import inspect

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


class TestEndToEndPersistenceFlow:
    """End-to-end tests for complete persistence scenarios."""

    @pytest.fixture
    def repositories(self, sqlalchemy_repo: BaseSQLAlchemyRepository):
        """Create all energy repositories."""
        return {
            "energy_source": SqlAlchemyEnergySourceRepository(db=sqlalchemy_repo),
            "energy_monitor": SqlAlchemyEnergyMonitorRepository(db=sqlalchemy_repo),
        }

    def test_complete_solar_system_setup(self, repositories):
        """Test creating a complete solar energy system with monitor and source."""
        source_repo = repositories["energy_source"]
        monitor_repo = repositories["energy_monitor"]

        # Step 1: Create and persist an energy monitor
        config = EnergyMonitorDummySolarConfig()
        energy_monitor = EnergyMonitor(
            name="Solar Panel Monitor",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=config,
        )
        monitor_repo.add(energy_monitor)

        # Step 2: Create an energy source with battery and grid
        battery = Battery(nominal_capacity=WattHours(20000.0))
        grid = Grid(contracted_power=Watts(5000.0))

        energy_source = EnergySource(
            name="Rooftop Solar Array",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(10000.0),
        )
        energy_source.connect_to_storage(battery)
        energy_source.connect_to_grid(grid)
        energy_source.use_energy_monitor(energy_monitor.id)

        source_repo.add(energy_source)

        # Step 3: Retrieve and verify the complete setup
        retrieved_source = source_repo.get_by_id(energy_source.id)
        retrieved_monitor = monitor_repo.get_by_id(energy_monitor.id)

        # Verify energy source
        assert retrieved_source is not None
        assert retrieved_source.name == "Rooftop Solar Array"
        assert retrieved_source.type == EnergySourceType.SOLAR
        assert float(retrieved_source.nominal_power_max) == 10000.0

        # Verify battery
        assert retrieved_source.storage is not None
        assert isinstance(retrieved_source.storage, Battery)
        assert float(retrieved_source.storage.nominal_capacity) == 20000.0

        # Verify grid
        assert retrieved_source.grid is not None
        assert isinstance(retrieved_source.grid, Grid)
        assert float(retrieved_source.grid.contracted_power) == 5000.0

        # Verify monitor reference (compare as strings since energy_monitor.id may be string after persistence)
        assert str(retrieved_source.energy_monitor_id) == str(energy_monitor.id)

        # Verify monitor
        assert retrieved_monitor is not None
        assert retrieved_monitor.name == "Solar Panel Monitor"
        assert retrieved_monitor.adapter_type == EnergyMonitorAdapter.DUMMY_SOLAR

    def test_multiple_sources_single_monitor(self, repositories):
        """Test scenario with multiple energy sources sharing one monitor."""
        source_repo = repositories["energy_source"]
        monitor_repo = repositories["energy_monitor"]

        # Create one monitor
        config = EnergyMonitorDummySolarConfig()
        monitor = EnergyMonitor(
            name="Shared Monitor",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=config,
        )
        monitor_repo.add(monitor)

        # Create multiple energy sources using the same monitor
        source1 = EnergySource(
            name="Solar Panel 1",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(5000.0),
        )
        source1.use_energy_monitor(monitor.id)

        source2 = EnergySource(
            name="Solar Panel 2",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(3000.0),
        )
        source2.use_energy_monitor(monitor.id)

        source_repo.add(source1)
        source_repo.add(source2)

        # Retrieve all sources
        all_sources = source_repo.get_all()

        # Filter sources using our monitor (compare as strings)
        monitor_id_str = str(monitor.id)
        sources_with_monitor = [s for s in all_sources if str(s.energy_monitor_id) == monitor_id_str]
        assert len(sources_with_monitor) == 2

        names = {s.name for s in sources_with_monitor}
        assert "Solar Panel 1" in names
        assert "Solar Panel 2" in names

    def test_update_and_retrieve_complex_changes(self, repositories):
        """Test updating complex nested value objects."""
        source_repo = repositories["energy_source"]

        # Create initial source with battery
        initial_battery = Battery(nominal_capacity=WattHours(10000.0))
        energy_source = EnergySource(
            name="Evolving System",
            type=EnergySourceType.WIND,  # Use WIND instead of non-existent HYBRID
            nominal_power_max=Watts(6000.0),
        )
        energy_source.connect_to_storage(initial_battery)
        source_repo.add(energy_source)

        # Update: change battery capacity
        new_battery = Battery(nominal_capacity=WattHours(25000.0))
        energy_source.disconnect_from_storage()
        energy_source.connect_to_storage(new_battery)

        # Add grid connection
        grid = Grid(contracted_power=Watts(4000.0))
        energy_source.connect_to_grid(grid)

        # Update power rating
        energy_source.nominal_power_max = Watts(8000.0)

        source_repo.update(energy_source)

        # Retrieve and verify all changes
        retrieved = source_repo.get_by_id(energy_source.id)
        assert retrieved is not None
        assert float(retrieved.storage.nominal_capacity) == 25000.0
        assert retrieved.grid is not None
        assert float(retrieved.grid.contracted_power) == 4000.0
        assert float(retrieved.nominal_power_max) == 8000.0

    def test_delete_and_orphan_references(self, repositories):
        """Test deleting entities and handling orphaned references."""
        source_repo = repositories["energy_source"]
        monitor_repo = repositories["energy_monitor"]

        # Create monitor and source
        config = EnergyMonitorDummySolarConfig()
        monitor = EnergyMonitor(
            name="Temporary Monitor",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=config,
        )
        monitor_repo.add(monitor)

        energy_source = EnergySource(
            name="Temporary Source",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(3000.0),
        )
        energy_source.use_energy_monitor(monitor.id)
        source_repo.add(energy_source)

        # Delete monitor (source will have orphaned reference)
        monitor_repo.remove(monitor.id)

        # Source should still exist but with dangling reference (compare as strings)
        retrieved_source = source_repo.get_by_id(energy_source.id)
        assert retrieved_source is not None
        assert str(retrieved_source.energy_monitor_id) == str(monitor.id)  # Reference still exists

        # Monitor should be gone
        retrieved_monitor = monitor_repo.get_by_id(monitor.id)
        assert retrieved_monitor is None

    def test_batch_operations(self, repositories):
        """Test batch creation and retrieval of multiple entities."""
        source_repo = repositories["energy_source"]

        # Create multiple diverse energy sources
        sources = [
            EnergySource(
                name=f"Solar Array {i}",
                type=EnergySourceType.SOLAR,
                nominal_power_max=Watts(1000.0 * i),
            )
            for i in range(1, 6)
        ]

        # Add batteries to some
        for i, source in enumerate(sources):
            if i % 2 == 0:
                battery = Battery(nominal_capacity=WattHours(5000.0 * (i + 1)))
                source.connect_to_storage(battery)

        # Persist all
        for source in sources:
            source_repo.add(source)

        # Retrieve all and verify
        all_sources = source_repo.get_all()
        assert len(all_sources) >= 5

        # Verify specific sources
        retrieved_ids = {str(s.id) for s in all_sources}
        for source in sources:
            assert str(source.id) in retrieved_ids

    def test_value_object_edge_cases(self, repositories):
        """Test edge cases for value objects (zero values, very large values)."""
        source_repo = repositories["energy_source"]

        # Create source with edge case values
        energy_source = EnergySource(
            name="Edge Case System",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(0.0),  # Zero power
        )

        # Very large battery
        huge_battery = Battery(nominal_capacity=WattHours(1000000.0))
        energy_source.connect_to_storage(huge_battery)

        # Small grid
        tiny_grid = Grid(contracted_power=Watts(0.1))
        energy_source.connect_to_grid(tiny_grid)

        source_repo.add(energy_source)

        # Retrieve and verify edge cases handled correctly
        retrieved = source_repo.get_by_id(energy_source.id)
        assert retrieved is not None
        assert float(retrieved.nominal_power_max) == 0.0
        assert float(retrieved.storage.nominal_capacity) == 1000000.0
        assert float(retrieved.grid.contracted_power) == 0.1

    def test_schema_consistency_after_operations(self, sqlalchemy_repo: BaseSQLAlchemyRepository, repositories):
        """Test that schema remains consistent after various operations."""
        source_repo = repositories["energy_source"]

        # Perform various operations
        source = EnergySource(
            name="Consistency Test",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(5000.0),
        )
        source_repo.add(source)

        source.name = "Updated Name"
        source_repo.update(source)

        source_repo.remove(source.id)

        # Verify schema integrity
        inspector = inspect(sqlalchemy_repo._engine)
        tables = inspector.get_table_names()

        # Core tables should still exist
        assert "energy_sources" in tables
        assert "energy_monitors" in tables

        # Columns should be intact
        columns = {col["name"] for col in inspector.get_columns("energy_sources")}
        assert "id" in columns
        assert "storage" in columns
        assert "grid" in columns

    def test_concurrent_repository_sessions(self, sqlalchemy_repo: BaseSQLAlchemyRepository):
        """Test that multiple repository instances can work with the same database."""
        # Create two separate repository instances
        repo1 = SqlAlchemyEnergySourceRepository(db=sqlalchemy_repo)
        repo2 = SqlAlchemyEnergySourceRepository(db=sqlalchemy_repo)

        # Add via repo1
        source = EnergySource(
            name="Shared Source",
            type=EnergySourceType.SOLAR,
            nominal_power_max=Watts(4000.0),
        )
        repo1.add(source)

        # Retrieve via repo2
        retrieved = repo2.get_by_id(source.id)
        assert retrieved is not None
        assert retrieved.name == "Shared Source"

        # Update via repo2
        retrieved.name = "Updated via Repo2"
        repo2.update(retrieved)

        # Verify via repo1
        final = repo1.get_by_id(source.id)
        assert final is not None
        assert final.name == "Updated via Repo2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
