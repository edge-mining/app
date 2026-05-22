"""Shared fixtures for climate domain tests."""

import uuid
from datetime import datetime, timezone

import pytest

from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateMonitor, ClimateZone
from edge_mining.domain.climate.value_objects import ClimateStateSnapshot, ClimateZoneReading
from edge_mining.domain.common import EntityId
from edge_mining.shared.adapter_configs.climate import ClimateMonitorHomeAssistantConfig


@pytest.fixture
def zone_id() -> EntityId:
    return EntityId(uuid.uuid4())


@pytest.fixture
def monitor_id() -> EntityId:
    return EntityId(uuid.uuid4())


@pytest.fixture
def external_service_id() -> EntityId:
    return EntityId(uuid.uuid4())


@pytest.fixture
def climate_zone(zone_id) -> ClimateZone:
    return ClimateZone(
        id=zone_id,
        name="Living Room",
        area_sqm=25.0,
    )


@pytest.fixture
def climate_zone_with_monitor(zone_id, monitor_id) -> ClimateZone:
    return ClimateZone(
        id=zone_id,
        name="Bedroom",
        area_sqm=15.0,
        climate_monitor_id=monitor_id,
    )


@pytest.fixture
def ha_config() -> ClimateMonitorHomeAssistantConfig:
    return ClimateMonitorHomeAssistantConfig(
        entity_temperature="sensor.living_room_temperature",
        entity_humidity="sensor.living_room_humidity",
        unit_temperature="°C",
    )


@pytest.fixture
def climate_monitor(monitor_id, external_service_id, ha_config) -> ClimateMonitor:
    return ClimateMonitor(
        id=monitor_id,
        name="Living Room Sensor",
        adapter_type=ClimateMonitorAdapter.HOME_ASSISTANT_API,
        config=ha_config,
        external_service_id=external_service_id,
    )


@pytest.fixture
def reading_living_room(zone_id) -> ClimateZoneReading:
    return ClimateZoneReading(
        zone_id=zone_id,
        zone_name="Living Room",
        temperature_celsius=21.5,
        humidity=55.0,
        timestamp=datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def reading_bedroom() -> ClimateZoneReading:
    return ClimateZoneReading(
        zone_id=EntityId(uuid.uuid4()),
        zone_name="Bedroom",
        temperature_celsius=18.0,
        humidity=60.0,
        timestamp=datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def reading_kitchen() -> ClimateZoneReading:
    return ClimateZoneReading(
        zone_id=EntityId(uuid.uuid4()),
        zone_name="Kitchen",
        temperature_celsius=24.0,
        humidity=45.0,
        timestamp=datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def climate_snapshot(reading_living_room, reading_bedroom, reading_kitchen) -> ClimateStateSnapshot:
    return ClimateStateSnapshot(per_zone=[reading_living_room, reading_bedroom, reading_kitchen])
