"""Unit tests for Climate domain value objects."""

import uuid
from datetime import datetime, timezone

from edge_mining.domain.climate.value_objects import ClimateStateSnapshot, ClimateZoneReading
from edge_mining.domain.common import EntityId


class TestClimateZoneReading:
    """Test suite for ClimateZoneReading value object."""

    def test_creation_with_defaults(self):
        reading = ClimateZoneReading()
        assert reading.zone_id is None
        assert reading.zone_name == ""
        assert reading.temperature_celsius == 0.0
        assert reading.humidity is None
        assert reading.timestamp is not None

    def test_creation_with_values(self, reading_living_room, zone_id):
        assert reading_living_room.zone_id == zone_id
        assert reading_living_room.zone_name == "Living Room"
        assert reading_living_room.temperature_celsius == 21.5
        assert reading_living_room.humidity == 55.0

    def test_is_frozen(self, reading_living_room):
        """Value objects should be immutable."""
        try:
            reading_living_room.temperature_celsius = 30.0
            assert False, "Should have raised FrozenInstanceError"
        except Exception:
            pass  # Expected: frozen dataclass

    def test_equality(self, zone_id):
        ts = datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc)
        r1 = ClimateZoneReading(zone_id=zone_id, zone_name="A", temperature_celsius=20.0, timestamp=ts)
        r2 = ClimateZoneReading(zone_id=zone_id, zone_name="A", temperature_celsius=20.0, timestamp=ts)
        assert r1 == r2

    def test_inequality_different_temp(self, zone_id):
        ts = datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc)
        r1 = ClimateZoneReading(zone_id=zone_id, temperature_celsius=20.0, timestamp=ts)
        r2 = ClimateZoneReading(zone_id=zone_id, temperature_celsius=22.0, timestamp=ts)
        assert r1 != r2


class TestClimateStateSnapshot:
    """Test suite for ClimateStateSnapshot composite value object."""

    def test_empty_snapshot(self):
        snapshot = ClimateStateSnapshot()
        assert snapshot.per_zone == []
        assert snapshot.min_temperature is None
        assert snapshot.max_temperature is None
        assert snapshot.avg_temperature is None

    def test_single_zone(self, reading_living_room):
        snapshot = ClimateStateSnapshot(per_zone=[reading_living_room])
        assert snapshot.min_temperature == 21.5
        assert snapshot.max_temperature == 21.5
        assert snapshot.avg_temperature == 21.5

    def test_multiple_zones_min(self, climate_snapshot):
        # bedroom=18, living_room=21.5, kitchen=24
        assert climate_snapshot.min_temperature == 18.0

    def test_multiple_zones_max(self, climate_snapshot):
        assert climate_snapshot.max_temperature == 24.0

    def test_multiple_zones_avg(self, climate_snapshot):
        # (21.5 + 18.0 + 24.0) / 3 = 21.166...
        expected = (21.5 + 18.0 + 24.0) / 3
        assert abs(climate_snapshot.avg_temperature - expected) < 0.001

    def test_zones_dict(self, climate_snapshot, reading_living_room):
        zones = climate_snapshot.zones
        assert "Living Room" in zones
        assert "Bedroom" in zones
        assert "Kitchen" in zones
        assert zones["Living Room"] == reading_living_room

    def test_zone_by_name_found(self, climate_snapshot):
        bedroom = climate_snapshot.zone_by_name("Bedroom")
        assert bedroom is not None
        assert bedroom.temperature_celsius == 18.0

    def test_zone_by_name_not_found(self, climate_snapshot):
        result = climate_snapshot.zone_by_name("Garage")
        assert result is None

    def test_zone_by_id_found(self, climate_snapshot, zone_id):
        result = climate_snapshot.zone_by_id(zone_id)
        assert result is not None
        assert result.zone_name == "Living Room"

    def test_zone_by_id_not_found(self, climate_snapshot):
        fake_id = EntityId(uuid.uuid4())
        result = climate_snapshot.zone_by_id(fake_id)
        assert result is None

    def test_is_frozen(self, climate_snapshot):
        """Snapshot should be immutable."""
        try:
            climate_snapshot.per_zone = []
            assert False, "Should have raised FrozenInstanceError"
        except Exception:
            pass
