"""Unit tests for OptimizationUnit climate zone management."""

import uuid

from edge_mining.domain.common import EntityId
from edge_mining.domain.optimization_unit.aggregate_roots import EnergyOptimizationUnit


class TestOptimizationUnitClimateZones:
    """Tests for climate_zone_ids management on EnergyOptimizationUnit."""

    def test_default_empty_climate_zone_ids(self):
        unit = EnergyOptimizationUnit(name="Test Unit")
        assert unit.climate_zone_ids == []

    def test_add_climate_zone(self):
        unit = EnergyOptimizationUnit(name="Test Unit")
        zone_id = EntityId(uuid.uuid4())
        unit.add_climate_zone(zone_id)
        assert zone_id in unit.climate_zone_ids
        assert len(unit.climate_zone_ids) == 1

    def test_add_climate_zone_idempotent(self):
        unit = EnergyOptimizationUnit(name="Test Unit")
        zone_id = EntityId(uuid.uuid4())
        unit.add_climate_zone(zone_id)
        unit.add_climate_zone(zone_id)  # duplicate
        assert len(unit.climate_zone_ids) == 1

    def test_add_multiple_climate_zones(self):
        unit = EnergyOptimizationUnit(name="Test Unit")
        z1 = EntityId(uuid.uuid4())
        z2 = EntityId(uuid.uuid4())
        z3 = EntityId(uuid.uuid4())
        unit.add_climate_zone(z1)
        unit.add_climate_zone(z2)
        unit.add_climate_zone(z3)
        assert len(unit.climate_zone_ids) == 3

    def test_remove_climate_zone(self):
        unit = EnergyOptimizationUnit(name="Test Unit")
        zone_id = EntityId(uuid.uuid4())
        unit.add_climate_zone(zone_id)
        unit.remove_climate_zone(zone_id)
        assert zone_id not in unit.climate_zone_ids
        assert len(unit.climate_zone_ids) == 0

    def test_remove_climate_zone_not_present(self):
        """Removing a non-existent zone should not raise."""
        unit = EnergyOptimizationUnit(name="Test Unit")
        zone_id = EntityId(uuid.uuid4())
        unit.remove_climate_zone(zone_id)  # Should not raise
        assert len(unit.climate_zone_ids) == 0

    def test_remove_one_keeps_others(self):
        unit = EnergyOptimizationUnit(name="Test Unit")
        z1 = EntityId(uuid.uuid4())
        z2 = EntityId(uuid.uuid4())
        unit.add_climate_zone(z1)
        unit.add_climate_zone(z2)
        unit.remove_climate_zone(z1)
        assert z1 not in unit.climate_zone_ids
        assert z2 in unit.climate_zone_ids
        assert len(unit.climate_zone_ids) == 1
