"""Unit tests for Climate Pydantic schemas."""

import uuid
from datetime import datetime, timezone

from edge_mining.adapters.domain.climate.schemas import (
    ClimateMonitorCreateSchema,
    ClimateMonitorSchema,
    ClimateMonitorUpdateSchema,
    ClimateStateSnapshotSchema,
    ClimateZoneCreateSchema,
    ClimateZoneReadingSchema,
    ClimateZoneSchema,
    ClimateZoneUpdateSchema,
)
from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateMonitor, ClimateZone
from edge_mining.domain.climate.value_objects import ClimateStateSnapshot, ClimateZoneReading
from edge_mining.domain.common import EntityId
from edge_mining.shared.adapter_configs.climate import ClimateMonitorHomeAssistantConfig


class TestClimateZoneSchema:
    """Tests for ClimateZone schema round-trips."""

    def test_from_model(self):
        zone_id = EntityId(uuid.uuid4())
        monitor_id = EntityId(uuid.uuid4())
        zone = ClimateZone(id=zone_id, name="Office", area_sqm=18.5, climate_monitor_id=monitor_id)
        schema = ClimateZoneSchema.from_model(zone)
        assert schema.id == str(zone_id)
        assert schema.name == "Office"
        assert schema.area_sqm == 18.5
        assert schema.climate_monitor_id == str(monitor_id)

    def test_to_model(self):
        zone_id = str(uuid.uuid4())
        schema = ClimateZoneSchema(id=zone_id, name="Garage", area_sqm=30.0, climate_monitor_id=None)
        model = schema.to_model()
        assert str(model.id) == zone_id
        assert model.name == "Garage"
        assert model.area_sqm == 30.0
        assert model.climate_monitor_id is None

    def test_round_trip(self):
        zone = ClimateZone(id=EntityId(uuid.uuid4()), name="Kitchen", area_sqm=12.0)
        schema = ClimateZoneSchema.from_model(zone)
        restored = schema.to_model()
        assert restored.id == zone.id
        assert restored.name == zone.name
        assert restored.area_sqm == zone.area_sqm

    def test_create_schema_generates_id(self):
        schema = ClimateZoneCreateSchema(name="New Zone", area_sqm=20.0)
        model = schema.to_model()
        assert model.id is not None
        assert model.name == "New Zone"
        assert model.area_sqm == 20.0


class TestClimateMonitorSchema:
    """Tests for ClimateMonitor schema round-trips."""

    def test_from_model(self):
        monitor_id = EntityId(uuid.uuid4())
        ext_id = EntityId(uuid.uuid4())
        config = ClimateMonitorHomeAssistantConfig(entity_temperature="sensor.temp")
        monitor = ClimateMonitor(
            id=monitor_id,
            name="Sensor 1",
            adapter_type=ClimateMonitorAdapter.HOME_ASSISTANT_API,
            config=config,
            external_service_id=ext_id,
        )
        schema = ClimateMonitorSchema.from_model(monitor)
        assert schema.id == str(monitor_id)
        assert schema.name == "Sensor 1"
        assert schema.config == {"entity_temperature": "sensor.temp", "entity_humidity": "", "unit_temperature": "°C"}
        assert schema.external_service_id == str(ext_id)

    def test_to_model(self):
        monitor_id = str(uuid.uuid4())
        schema = ClimateMonitorSchema(
            id=monitor_id,
            name="Monitor",
            adapter_type=ClimateMonitorAdapter.HOME_ASSISTANT_API,
            config={"entity_temperature": "sensor.x", "entity_humidity": "", "unit_temperature": "°C"},
            external_service_id=None,
        )
        model = schema.to_model()
        assert str(model.id) == monitor_id
        assert model.name == "Monitor"
        assert model.config is not None
        assert model.config.entity_temperature == "sensor.x"

    def test_round_trip(self):
        config = ClimateMonitorHomeAssistantConfig(entity_temperature="sensor.room", entity_humidity="sensor.hum")
        monitor = ClimateMonitor(
            id=EntityId(uuid.uuid4()),
            name="Room Sensor",
            adapter_type=ClimateMonitorAdapter.HOME_ASSISTANT_API,
            config=config,
        )
        schema = ClimateMonitorSchema.from_model(monitor)
        restored = schema.to_model()
        assert restored.id == monitor.id
        assert restored.name == monitor.name
        assert restored.config.entity_temperature == "sensor.room"
        assert restored.config.entity_humidity == "sensor.hum"

    def test_create_schema_generates_id(self):
        schema = ClimateMonitorCreateSchema(
            name="New Monitor",
            adapter_type=ClimateMonitorAdapter.HOME_ASSISTANT_API,
            config={"entity_temperature": "sensor.new", "entity_humidity": "", "unit_temperature": "°C"},
        )
        model = schema.to_model()
        assert model.id is not None
        assert model.name == "New Monitor"
        assert model.config.entity_temperature == "sensor.new"

    def test_update_schema_partial(self):
        schema = ClimateMonitorUpdateSchema(name="Renamed", config=None, external_service_id=None)
        assert schema.name == "Renamed"
        assert schema.config is None


class TestClimateReadingSchema:
    """Tests for reading/snapshot schemas."""

    def test_reading_from_model(self):
        zone_id = EntityId(uuid.uuid4())
        ts = datetime(2026, 5, 22, 12, 0, 0, tzinfo=timezone.utc)
        reading = ClimateZoneReading(
            zone_id=zone_id, zone_name="Hall", temperature_celsius=22.3, humidity=50.0, timestamp=ts
        )
        schema = ClimateZoneReadingSchema.from_model(reading)
        assert schema.zone_id == str(zone_id)
        assert schema.zone_name == "Hall"
        assert schema.temperature_celsius == 22.3
        assert schema.humidity == 50.0

    def test_snapshot_from_model(self):
        r1 = ClimateZoneReading(zone_name="A", temperature_celsius=18.0)
        r2 = ClimateZoneReading(zone_name="B", temperature_celsius=24.0)
        snapshot = ClimateStateSnapshot(per_zone=[r1, r2])
        schema = ClimateStateSnapshotSchema.from_model(snapshot)
        assert len(schema.per_zone) == 2
        assert schema.min_temperature == 18.0
        assert schema.max_temperature == 24.0
        assert schema.avg_temperature == 21.0
