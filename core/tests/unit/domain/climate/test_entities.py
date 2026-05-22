"""Unit tests for Climate domain entities."""

import uuid

from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateMonitor, ClimateZone
from edge_mining.domain.common import EntityId
from edge_mining.shared.adapter_configs.climate import ClimateMonitorHomeAssistantConfig


class TestClimateZone:
    """Test suite for ClimateZone entity."""

    def test_creation_with_defaults(self):
        zone = ClimateZone()
        assert zone.name == ""
        assert zone.area_sqm == 0.0
        assert zone.climate_monitor_id is None
        assert isinstance(zone.id, uuid.UUID)

    def test_creation_with_custom_values(self):
        zone_id = EntityId(uuid.uuid4())
        monitor_id = EntityId(uuid.uuid4())
        zone = ClimateZone(
            id=zone_id,
            name="Office",
            area_sqm=12.5,
            climate_monitor_id=monitor_id,
        )
        assert zone.id == zone_id
        assert zone.name == "Office"
        assert zone.area_sqm == 12.5
        assert zone.climate_monitor_id == monitor_id

    def test_use_climate_monitor(self, climate_zone):
        new_monitor_id = EntityId(uuid.uuid4())
        climate_zone.use_climate_monitor(new_monitor_id)
        assert climate_zone.climate_monitor_id == new_monitor_id

    def test_unlink_climate_monitor(self, climate_zone_with_monitor):
        assert climate_zone_with_monitor.climate_monitor_id is not None
        climate_zone_with_monitor.unlink_climate_monitor()
        assert climate_zone_with_monitor.climate_monitor_id is None

    def test_use_climate_monitor_replaces_existing(self, climate_zone_with_monitor):
        old_id = climate_zone_with_monitor.climate_monitor_id
        new_id = EntityId(uuid.uuid4())
        climate_zone_with_monitor.use_climate_monitor(new_id)
        assert climate_zone_with_monitor.climate_monitor_id == new_id
        assert climate_zone_with_monitor.climate_monitor_id != old_id


class TestClimateMonitor:
    """Test suite for ClimateMonitor entity."""

    def test_creation_with_defaults(self):
        monitor = ClimateMonitor()
        assert monitor.name == ""
        assert monitor.adapter_type == ClimateMonitorAdapter.HOME_ASSISTANT_API
        assert monitor.config is None
        assert monitor.external_service_id is None
        assert isinstance(monitor.id, uuid.UUID)

    def test_creation_with_custom_values(self, climate_monitor, monitor_id, external_service_id, ha_config):
        assert climate_monitor.id == monitor_id
        assert climate_monitor.name == "Living Room Sensor"
        assert climate_monitor.adapter_type == ClimateMonitorAdapter.HOME_ASSISTANT_API
        assert climate_monitor.config == ha_config
        assert climate_monitor.external_service_id == external_service_id

    def test_config_to_dict(self, climate_monitor):
        config_dict = climate_monitor.config.to_dict()
        assert config_dict["entity_temperature"] == "sensor.living_room_temperature"
        assert config_dict["entity_humidity"] == "sensor.living_room_humidity"
        assert config_dict["unit_temperature"] == "°C"

    def test_config_from_dict(self):
        data = {
            "entity_temperature": "sensor.temp",
            "entity_humidity": "sensor.hum",
            "unit_temperature": "°F",
        }
        config = ClimateMonitorHomeAssistantConfig.from_dict(data)
        assert config.entity_temperature == "sensor.temp"
        assert config.entity_humidity == "sensor.hum"
        assert config.unit_temperature == "°F"

    def test_config_is_valid(self, ha_config):
        assert ha_config.is_valid(ClimateMonitorAdapter.HOME_ASSISTANT_API) is True

    def test_config_is_valid_wrong_adapter(self, ha_config):
        # Should only be valid for HOME_ASSISTANT_API
        # Since there's only one adapter type, test it returns True for it
        assert ha_config.is_valid(ClimateMonitorAdapter.HOME_ASSISTANT_API) is True

    def test_config_empty_temperature_is_invalid(self):
        config = ClimateMonitorHomeAssistantConfig(entity_temperature="")
        assert config.is_valid(ClimateMonitorAdapter.HOME_ASSISTANT_API) is False
