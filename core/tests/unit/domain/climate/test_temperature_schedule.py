"""Tests for temperature schedule, target resolution, and hysteresis."""

from datetime import time

import pytest

from edge_mining.domain.climate.entities import ClimateZone
from edge_mining.domain.climate.value_objects import ClimateZoneReading, TemperatureSlot
from edge_mining.domain.common import EntityId

import uuid


class TestTemperatureSlot:
    """Tests for TemperatureSlot value object."""

    def test_create_slot(self):
        slot = TemperatureSlot(
            start_time=time(8, 0),
            end_time=time(22, 0),
            target_temperature=21.0,
        )
        assert slot.start_time == time(8, 0)
        assert slot.end_time == time(22, 0)
        assert slot.target_temperature == 21.0

    def test_slot_is_frozen(self):
        slot = TemperatureSlot(
            start_time=time(8, 0),
            end_time=time(22, 0),
            target_temperature=21.0,
        )
        with pytest.raises(Exception):
            slot.target_temperature = 22.0  # type: ignore

    def test_slot_equality(self):
        slot1 = TemperatureSlot(start_time=time(8, 0), end_time=time(22, 0), target_temperature=21.0)
        slot2 = TemperatureSlot(start_time=time(8, 0), end_time=time(22, 0), target_temperature=21.0)
        assert slot1 == slot2

    def test_slot_default_values(self):
        slot = TemperatureSlot()
        assert slot.start_time == time(0, 0)
        assert slot.end_time == time(0, 0)
        assert slot.target_temperature == 20.0


class TestClimateZoneResolveTarget:
    """Tests for ClimateZone.resolve_target_temperature()."""

    def test_time_in_normal_slot(self):
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[
                TemperatureSlot(start_time=time(8, 0), end_time=time(22, 0), target_temperature=21.0),
            ],
        )
        assert zone.resolve_target_temperature(time(12, 0)) == 21.0

    def test_time_at_slot_start(self):
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[
                TemperatureSlot(start_time=time(8, 0), end_time=time(22, 0), target_temperature=21.0),
            ],
        )
        assert zone.resolve_target_temperature(time(8, 0)) == 21.0

    def test_time_at_slot_end_excluded(self):
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[
                TemperatureSlot(start_time=time(8, 0), end_time=time(22, 0), target_temperature=21.0),
            ],
            default_target_temperature=18.0,
        )
        # end_time is exclusive
        assert zone.resolve_target_temperature(time(22, 0)) == 18.0

    def test_time_outside_slot_uses_default(self):
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[
                TemperatureSlot(start_time=time(8, 0), end_time=time(22, 0), target_temperature=21.0),
            ],
            default_target_temperature=18.0,
        )
        assert zone.resolve_target_temperature(time(3, 0)) == 18.0

    def test_time_outside_slot_no_default_returns_none(self):
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[
                TemperatureSlot(start_time=time(8, 0), end_time=time(22, 0), target_temperature=21.0),
            ],
            default_target_temperature=None,
        )
        assert zone.resolve_target_temperature(time(3, 0)) is None

    def test_cross_midnight_slot_late_night(self):
        """22:00→06:00 slot, checking at 23:00 → should match."""
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[
                TemperatureSlot(start_time=time(22, 0), end_time=time(6, 0), target_temperature=18.0),
            ],
        )
        assert zone.resolve_target_temperature(time(23, 0)) == 18.0

    def test_cross_midnight_slot_early_morning(self):
        """22:00→06:00 slot, checking at 03:00 → should match."""
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[
                TemperatureSlot(start_time=time(22, 0), end_time=time(6, 0), target_temperature=18.0),
            ],
        )
        assert zone.resolve_target_temperature(time(3, 0)) == 18.0

    def test_cross_midnight_slot_midday_no_match(self):
        """22:00→06:00 slot, checking at 12:00 → should NOT match."""
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[
                TemperatureSlot(start_time=time(22, 0), end_time=time(6, 0), target_temperature=18.0),
            ],
            default_target_temperature=21.0,
        )
        assert zone.resolve_target_temperature(time(12, 0)) == 21.0

    def test_multiple_slots_first_match(self):
        """Multiple slots, first match wins."""
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[
                TemperatureSlot(start_time=time(8, 0), end_time=time(12, 0), target_temperature=20.0),
                TemperatureSlot(start_time=time(12, 0), end_time=time(22, 0), target_temperature=22.0),
                TemperatureSlot(start_time=time(22, 0), end_time=time(8, 0), target_temperature=18.0),
            ],
        )
        assert zone.resolve_target_temperature(time(10, 0)) == 20.0
        assert zone.resolve_target_temperature(time(15, 0)) == 22.0
        assert zone.resolve_target_temperature(time(23, 0)) == 18.0
        assert zone.resolve_target_temperature(time(2, 0)) == 18.0

    def test_empty_schedule_uses_default(self):
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[],
            default_target_temperature=20.0,
        )
        assert zone.resolve_target_temperature(time(12, 0)) == 20.0

    def test_empty_schedule_no_default_returns_none(self):
        zone = ClimateZone(
            id=EntityId(uuid.uuid4()),
            name="Room",
            temperature_schedule=[],
            default_target_temperature=None,
        )
        assert zone.resolve_target_temperature(time(12, 0)) is None


class TestClimateZoneReadingWithTarget:
    """Tests for ClimateZoneReading with target temperature fields."""

    def test_reading_with_target(self):
        reading = ClimateZoneReading(
            zone_name="Bedroom",
            temperature_celsius=19.5,
            target_temperature=21.0,
            hysteresis_celsius=0.5,
        )
        assert reading.target_temperature == 21.0
        assert reading.hysteresis_celsius == 0.5

    def test_reading_without_target(self):
        reading = ClimateZoneReading(
            zone_name="Bedroom",
            temperature_celsius=19.5,
        )
        assert reading.target_temperature is None
        assert reading.hysteresis_celsius is None

    def test_reading_is_frozen(self):
        reading = ClimateZoneReading(
            zone_name="Bedroom",
            temperature_celsius=19.5,
            target_temperature=21.0,
        )
        with pytest.raises(Exception):
            reading.target_temperature = 22.0  # type: ignore


class TestClimateZoneHysteresis:
    """Tests for hysteresis configuration on ClimateZone."""

    def test_default_hysteresis(self):
        zone = ClimateZone(id=EntityId(uuid.uuid4()), name="Room")
        assert zone.hysteresis_celsius == 0.5

    def test_custom_hysteresis(self):
        zone = ClimateZone(id=EntityId(uuid.uuid4()), name="Room", hysteresis_celsius=1.0)
        assert zone.hysteresis_celsius == 1.0
