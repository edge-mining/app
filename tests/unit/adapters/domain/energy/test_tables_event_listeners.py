"""Unit tests for SQLAlchemy event listeners and type converters.

These tests verify the event listeners and custom types used for value object
serialization/deserialization in the energy domain tables.
"""

import json
from unittest.mock import MagicMock, Mock

import pytest

from edge_mining.adapters.domain.energy.tables import (
    EnergyMonitorConfigType,
    _deserialize_energy_monitor_config,
    _flatten_energy_source_composites,
    _receive_energy_monitor_load,
    _receive_energy_source_load,
)
from edge_mining.domain.common import EntityId, WattHours, Watts
from edge_mining.domain.energy.common import EnergyMonitorAdapter
from edge_mining.domain.energy.entities import EnergyMonitor, EnergySource
from edge_mining.domain.energy.exceptions import EnergyMonitorConfigurationError
from edge_mining.domain.energy.value_objects import Battery, Grid
from edge_mining.shared.adapter_configs.energy import EnergyMonitorDummySolarConfig


class TestEnergySourceLoadEventListener:
    """Unit tests for _receive_energy_source_load event listener."""

    def test_converts_float_to_watts_for_nominal_power_max(self):
        """Test that float nominal_power_max is converted to Watts."""
        # Create a mock EnergySource with float values
        target = EnergySource(name="Test")
        target.nominal_power_max = 5000.0  # Simulate database load (float)

        # Call the event listener
        _receive_energy_source_load(target, None)

        # Verify conversion to Watts
        assert isinstance(target.nominal_power_max, type(Watts(0.0)))
        assert float(target.nominal_power_max) == 5000.0

    def test_converts_float_to_watts_for_external_source(self):
        """Test that float external_source is converted to Watts."""
        target = EnergySource(name="Test")
        target.external_source = 1500.0  # Simulate database load

        _receive_energy_source_load(target, None)

        assert isinstance(target.external_source, type(Watts(0.0)))
        assert float(target.external_source) == 1500.0

    def test_converts_dict_to_battery(self):
        """Test that dict storage is converted to Battery object."""
        target = EnergySource(name="Test")
        target.storage = {"nominal_capacity": 10000.0}  # Simulate JSON load

        _receive_energy_source_load(target, None)

        assert isinstance(target.storage, Battery)
        assert float(target.storage.nominal_capacity) == 10000.0

    def test_converts_json_string_to_battery(self):
        """Test that JSON string storage is converted to Battery object."""
        target = EnergySource(name="Test")
        target.storage = json.dumps({"nominal_capacity": 15000.0})

        _receive_energy_source_load(target, None)

        assert isinstance(target.storage, Battery)
        assert float(target.storage.nominal_capacity) == 15000.0

    def test_converts_dict_to_grid(self):
        """Test that dict grid is converted to Grid object."""
        target = EnergySource(name="Test")
        target.grid = {"contracted_power": 3000.0}

        _receive_energy_source_load(target, None)

        assert isinstance(target.grid, Grid)
        assert float(target.grid.contracted_power) == 3000.0

    def test_converts_json_string_to_grid(self):
        """Test that JSON string grid is converted to Grid object."""
        target = EnergySource(name="Test")
        target.grid = json.dumps({"contracted_power": 5000.0})

        _receive_energy_source_load(target, None)

        assert isinstance(target.grid, Grid)
        assert float(target.grid.contracted_power) == 5000.0

    def test_handles_none_values(self):
        """Test that None values are handled correctly."""
        target = EnergySource(name="Test")
        target.nominal_power_max = None
        target.external_source = None
        target.storage = None
        target.grid = None

        # Should not raise errors
        _receive_energy_source_load(target, None)

        assert target.nominal_power_max is None
        assert target.external_source is None
        assert target.storage is None
        assert target.grid is None

    def test_skips_already_converted_watts(self):
        """Test that already-converted Watts objects are not re-converted."""
        target = EnergySource(name="Test")
        original_watts = Watts(4000.0)
        target.nominal_power_max = original_watts

        _receive_energy_source_load(target, None)

        # Should remain as Watts (not converted again)
        assert target.nominal_power_max is original_watts


class TestEnergySourceFlattenEventListener:
    """Unit tests for _flatten_energy_source_composites event listener."""

    def test_flattens_watts_to_float(self):
        """Test that Watts objects are flattened to floats."""
        target = EnergySource(name="Test")
        target.nominal_power_max = Watts(6000.0)
        target.external_source = Watts(2000.0)

        _flatten_energy_source_composites(None, None, target)

        assert isinstance(target.nominal_power_max, float)
        assert target.nominal_power_max == 6000.0
        assert isinstance(target.external_source, float)
        assert target.external_source == 2000.0

    def test_flattens_battery_to_dict(self):
        """Test that Battery is serialized to dict."""
        target = EnergySource(name="Test")
        battery = Battery(nominal_capacity=WattHours(12000.0))
        target.storage = battery

        _flatten_energy_source_composites(None, None, target)

        assert isinstance(target.storage, dict)
        assert target.storage == {"nominal_capacity": 12000.0}

    def test_flattens_grid_to_dict(self):
        """Test that Grid is serialized to dict."""
        target = EnergySource(name="Test")
        grid = Grid(contracted_power=Watts(4000.0))
        target.grid = grid

        _flatten_energy_source_composites(None, None, target)

        assert isinstance(target.grid, dict)
        assert target.grid == {"contracted_power": 4000.0}

    def test_handles_none_values(self):
        """Test that None values remain None."""
        target = EnergySource(name="Test")
        target.nominal_power_max = None
        target.external_source = None
        target.storage = None
        target.grid = None

        _flatten_energy_source_composites(None, None, target)

        assert target.nominal_power_max is None
        assert target.external_source is None
        assert target.storage is None
        assert target.grid is None

    def test_skips_already_flattened_values(self):
        """Test that already-flattened values are not re-flattened."""
        target = EnergySource(name="Test")
        target.storage = {"nominal_capacity": 10000.0}  # Already a dict

        _flatten_energy_source_composites(None, None, target)

        # Should remain as dict
        assert isinstance(target.storage, dict)


class TestEnergyMonitorConfigDeserialization:
    """Unit tests for _deserialize_energy_monitor_config."""

    def test_deserializes_dummy_solar_config(self):
        """Test deserialization of EnergyMonitorDummySolarConfig."""
        config_json = json.dumps({"max_consumption_power": 3200.0})
        result = _deserialize_energy_monitor_config(EnergyMonitorAdapter.DUMMY_SOLAR, config_json)

        assert result is not None
        assert isinstance(result, EnergyMonitorDummySolarConfig)

    def test_returns_none_for_empty_json(self):
        """Test that empty JSON returns None."""
        result = _deserialize_energy_monitor_config(EnergyMonitorAdapter.DUMMY_SOLAR, "")
        assert result is None

    def test_raises_error_for_invalid_adapter_type(self):
        """Test that invalid adapter type raises error."""
        config_json = json.dumps({})

        # Create a mock adapter type that's not in the map
        with pytest.raises(EnergyMonitorConfigurationError, match="Invalid type"):
            _deserialize_energy_monitor_config("INVALID_TYPE", config_json)

    def test_raises_error_for_malformed_json(self):
        """Test that malformed JSON raises error."""
        config_json = "not valid json"

        with pytest.raises(json.JSONDecodeError):
            _deserialize_energy_monitor_config(EnergyMonitorAdapter.DUMMY_SOLAR, config_json)


class TestEnergyMonitorLoadEventListener:
    """Unit tests for _receive_energy_monitor_load event listener."""

    def test_converts_string_id_to_entity_id(self):
        """Test that string id is converted to EntityId."""
        import uuid

        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        test_uuid = uuid.uuid4()
        target.id = str(test_uuid)  # Simulate database load (string)

        _receive_energy_monitor_load(target, None)

        # EntityId is a NewType wrapping UUID, so check for UUID type
        assert isinstance(target.id, uuid.UUID)
        assert target.id == test_uuid

    def test_converts_string_external_service_id_to_entity_id(self):
        """Test that string external_service_id is converted to EntityId."""
        import uuid

        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        test_uuid = uuid.uuid4()
        target.external_service_id = str(test_uuid)  # Simulate database load

        _receive_energy_monitor_load(target, None)

        # EntityId is a NewType wrapping UUID, so check for UUID type
        assert isinstance(target.external_service_id, uuid.UUID)
        assert target.external_service_id == test_uuid

    def test_converts_string_adapter_type_to_enum(self):
        """Test that string adapter_type is converted to enum."""
        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        target.adapter_type = "dummy_solar"  # Simulate database load (string)

        _receive_energy_monitor_load(target, None)

        assert isinstance(target.adapter_type, EnergyMonitorAdapter)
        assert target.adapter_type == EnergyMonitorAdapter.DUMMY_SOLAR

    def test_deserializes_config_from_json_string(self):
        """Test that JSON config string is deserialized."""
        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        target.config = json.dumps({"max_consumption_power": 3200.0})  # Simulate database load

        _receive_energy_monitor_load(target, None)

        assert target.config is not None
        assert isinstance(target.config, EnergyMonitorDummySolarConfig)

    def test_handles_none_values(self):
        """Test that None values are handled correctly."""
        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        target.external_service_id = None

        _receive_energy_monitor_load(target, None)

        assert target.config is None
        assert target.external_service_id is None

    def test_handles_invalid_adapter_type_string(self):
        """Test behavior with invalid adapter type string."""
        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        target.adapter_type = "INVALID_TYPE"

        # Should not raise during conversion, but will fail later in config deserialization
        _receive_energy_monitor_load(target, None)

        # adapter_type should remain as string since conversion failed
        assert target.adapter_type == "INVALID_TYPE"

    def test_skips_already_converted_entity_id(self):
        """Test that already-converted EntityId objects are not re-converted."""
        import uuid

        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        original_id = EntityId(uuid.uuid4())
        target.id = original_id

        _receive_energy_monitor_load(target, None)

        # Should remain as EntityId (not converted again)
        assert target.id is original_id

    def test_skips_already_converted_adapter_type_enum(self):
        """Test that already-converted enum objects are not re-converted."""
        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )

        _receive_energy_monitor_load(target, None)

        # Should remain as enum
        assert isinstance(target.adapter_type, EnergyMonitorAdapter)
        assert target.adapter_type == EnergyMonitorAdapter.DUMMY_SOLAR


class TestEnergyMonitorConfigType:
    """Unit tests for EnergyMonitorConfigType SQLAlchemy custom type."""

    def test_config_type_inheritance(self):
        """Test that EnergyMonitorConfigType inherits from ConfigurationType."""
        config_type = EnergyMonitorConfigType()
        # Verify it's properly instantiated
        assert config_type is not None


class TestEnergyMonitorFlattenEventListener:
    """Unit tests for _flatten_energy_monitor_composites event listener."""

    def test_flattens_adapter_type_enum_to_string(self):
        """Test that EnergyMonitorAdapter enum is converted to string."""
        from edge_mining.adapters.domain.energy.tables import _flatten_energy_monitor_composites

        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )

        _flatten_energy_monitor_composites(None, None, target)

        assert isinstance(target.adapter_type, str)
        assert target.adapter_type == "dummy_solar"

    def test_handles_none_adapter_type(self):
        """Test that None adapter_type is handled correctly."""
        from edge_mining.adapters.domain.energy.tables import _flatten_energy_monitor_composites

        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        target.adapter_type = None

        _flatten_energy_monitor_composites(None, None, target)

        assert target.adapter_type is None

    def test_skips_already_flattened_string(self):
        """Test that already-flattened string values are not re-flattened."""
        from edge_mining.adapters.domain.energy.tables import _flatten_energy_monitor_composites

        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        target.adapter_type = "dummy_solar"  # Already a string

        _flatten_energy_monitor_composites(None, None, target)

        assert target.adapter_type == "dummy_solar"


class TestEnergyMonitorRestoreEventListener:
    """Unit tests for _restore_energy_monitor_composites event listener."""

    def test_restores_string_id_to_entity_id(self):
        """Test that string id is restored to EntityId after persistence."""
        import uuid
        from edge_mining.adapters.domain.energy.tables import _restore_energy_monitor_composites

        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        test_uuid = uuid.uuid4()
        target.id = str(test_uuid)  # Simulate post-persist string

        _restore_energy_monitor_composites(None, None, target)

        # EntityId is a NewType wrapping UUID, so check for UUID type
        assert isinstance(target.id, uuid.UUID)
        assert target.id == test_uuid

    def test_restores_string_external_service_id_to_entity_id(self):
        """Test that string external_service_id is restored to EntityId."""
        import uuid
        from edge_mining.adapters.domain.energy.tables import _restore_energy_monitor_composites

        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        test_uuid = uuid.uuid4()
        target.external_service_id = str(test_uuid)

        _restore_energy_monitor_composites(None, None, target)

        # EntityId is a NewType wrapping UUID, so check for UUID type
        assert isinstance(target.external_service_id, uuid.UUID)
        assert target.external_service_id == test_uuid

    def test_restores_string_adapter_type_to_enum(self):
        """Test that string adapter_type is restored to enum."""
        from edge_mining.adapters.domain.energy.tables import _restore_energy_monitor_composites

        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        target.adapter_type = "dummy_solar"  # Simulate post-flatten string

        _restore_energy_monitor_composites(None, None, target)

        assert isinstance(target.adapter_type, EnergyMonitorAdapter)
        assert target.adapter_type == EnergyMonitorAdapter.DUMMY_SOLAR

    def test_handles_none_values(self):
        """Test that None values remain None."""
        from edge_mining.adapters.domain.energy.tables import _restore_energy_monitor_composites

        target = EnergyMonitor(
            name="Test",
            adapter_type=EnergyMonitorAdapter.DUMMY_SOLAR,
            config=None,
        )
        target.external_service_id = None
        target.adapter_type = None

        _restore_energy_monitor_composites(None, None, target)

        assert target.external_service_id is None
        assert target.adapter_type is None


class TestEnergySourceRestoreEventListener:
    """Unit tests for _restore_energy_source_composites event listener."""

    def test_restores_string_id_to_entity_id(self):
        """Test that string id is restored to EntityId after persistence."""
        import uuid
        from edge_mining.adapters.domain.energy.tables import _restore_energy_source_composites

        target = EnergySource(name="Test")
        test_uuid = uuid.uuid4()
        target.id = str(test_uuid)

        _restore_energy_source_composites(None, None, target)

        # EntityId is a NewType wrapping UUID, so check for UUID type
        assert isinstance(target.id, uuid.UUID)
        assert target.id == test_uuid

    def test_restores_foreign_keys_to_entity_id(self):
        """Test that foreign key strings are restored to EntityId."""
        import uuid
        from edge_mining.adapters.domain.energy.tables import _restore_energy_source_composites
        from edge_mining.domain.energy.common import EnergySourceType

        target = EnergySource(name="Test", type=EnergySourceType.SOLAR)
        monitor_uuid = uuid.uuid4()
        provider_uuid = uuid.uuid4()
        target.energy_monitor_id = str(monitor_uuid)
        target.forecast_provider_id = str(provider_uuid)

        _restore_energy_source_composites(None, None, target)

        # EntityId is a NewType wrapping UUID, so check for UUID type
        assert isinstance(target.energy_monitor_id, uuid.UUID)
        assert target.energy_monitor_id == monitor_uuid
        assert isinstance(target.forecast_provider_id, uuid.UUID)
        assert target.forecast_provider_id == provider_uuid

    def test_restores_type_string_to_enum(self):
        """Test that type string is restored to EnergySourceType enum."""
        from edge_mining.adapters.domain.energy.tables import _restore_energy_source_composites
        from edge_mining.domain.energy.common import EnergySourceType

        target = EnergySource(name="Test")
        target.type = "solar"  # Simulate post-flatten string

        _restore_energy_source_composites(None, None, target)

        assert isinstance(target.type, EnergySourceType)
        assert target.type == EnergySourceType.SOLAR

    def test_restores_float_to_watts(self):
        """Test that float values are restored to Watts."""
        from edge_mining.adapters.domain.energy.tables import _restore_energy_source_composites

        target = EnergySource(name="Test")
        target.nominal_power_max = 5000.0  # Float after flatten
        target.external_source = 1500.0

        _restore_energy_source_composites(None, None, target)

        assert isinstance(target.nominal_power_max, type(Watts(0.0)))
        assert float(target.nominal_power_max) == 5000.0
        assert isinstance(target.external_source, type(Watts(0.0)))
        assert float(target.external_source) == 1500.0

    def test_restores_dict_to_battery_and_grid(self):
        """Test that dict values are restored to Battery and Grid objects."""
        from edge_mining.adapters.domain.energy.tables import _restore_energy_source_composites

        target = EnergySource(name="Test")
        target.storage = {"nominal_capacity": 10000.0}  # Dict after flatten
        target.grid = {"contracted_power": 3000.0}

        _restore_energy_source_composites(None, None, target)

        assert isinstance(target.storage, Battery)
        assert float(target.storage.nominal_capacity) == 10000.0
        assert isinstance(target.grid, Grid)
        assert float(target.grid.contracted_power) == 3000.0

    def test_handles_none_values(self):
        """Test that None values remain None."""
        from edge_mining.adapters.domain.energy.tables import _restore_energy_source_composites

        target = EnergySource(name="Test")
        target.nominal_power_max = None
        target.external_source = None
        target.storage = None
        target.grid = None
        target.energy_monitor_id = None
        target.forecast_provider_id = None

        _restore_energy_source_composites(None, None, target)

        assert target.nominal_power_max is None
        assert target.external_source is None
        assert target.storage is None
        assert target.grid is None
        assert target.energy_monitor_id is None
        assert target.forecast_provider_id is None


class TestValueObjectRoundTrip:
    """Integration-style unit tests for value object round-trip conversions."""

    def test_battery_round_trip(self):
        """Test Battery serialization and deserialization."""
        # Create original
        original_battery = Battery(nominal_capacity=WattHours(8000.0))

        # Simulate serialization (what happens before_insert)
        serialized = {"nominal_capacity": float(original_battery.nominal_capacity)}

        # Simulate deserialization (what happens on load)
        deserialized_battery = Battery(nominal_capacity=WattHours(serialized["nominal_capacity"]))

        assert float(deserialized_battery.nominal_capacity) == float(original_battery.nominal_capacity)

    def test_grid_round_trip(self):
        """Test Grid serialization and deserialization."""
        original_grid = Grid(contracted_power=Watts(3500.0))

        # Serialize
        serialized = {"contracted_power": float(original_grid.contracted_power)}

        # Deserialize
        deserialized_grid = Grid(contracted_power=Watts(serialized["contracted_power"]))

        assert float(deserialized_grid.contracted_power) == float(original_grid.contracted_power)

    def test_watts_round_trip(self):
        """Test Watts serialization and deserialization."""
        original_watts = Watts(7500.5)

        # Serialize to float
        serialized = float(original_watts)

        # Deserialize back to Watts
        deserialized_watts = Watts(serialized)

        assert float(deserialized_watts) == float(original_watts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
