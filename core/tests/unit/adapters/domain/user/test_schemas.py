"""Unit tests for the system settings Pydantic schemas."""

import pytest
from pydantic import ValidationError

from edge_mining.adapters.domain.user.schemas import SystemConfigurationSchema
from edge_mining.domain.user.value_objects import SystemConfiguration


class TestSystemConfigurationSchema:
    """Tests for SystemConfiguration schema round-trips and validation."""

    def test_from_model(self):
        config = SystemConfiguration(
            timezone="America/New_York",
            latitude=40.0,
            longitude=-74.0,
            scheduler_interval_seconds=15,
        )
        schema = SystemConfigurationSchema.from_model(config)
        assert schema.timezone == "America/New_York"
        assert schema.latitude == 40.0
        assert schema.longitude == -74.0
        assert schema.scheduler_interval_seconds == 15

    def test_to_model(self):
        schema = SystemConfigurationSchema(
            timezone="Europe/Rome",
            latitude=41.9028,
            longitude=12.4964,
            scheduler_interval_seconds=5,
        )
        model = schema.to_model()
        assert isinstance(model, SystemConfiguration)
        assert model.timezone == "Europe/Rome"
        assert model.scheduler_interval_seconds == 5

    def test_invalid_timezone_is_rejected(self):
        with pytest.raises(ValidationError):
            SystemConfigurationSchema(timezone="Not/AZone")

    @pytest.mark.parametrize("latitude", [-91.0, 91.0])
    def test_out_of_range_latitude_is_rejected(self, latitude):
        with pytest.raises(ValidationError):
            SystemConfigurationSchema(latitude=latitude)

    @pytest.mark.parametrize("longitude", [-181.0, 181.0])
    def test_out_of_range_longitude_is_rejected(self, longitude):
        with pytest.raises(ValidationError):
            SystemConfigurationSchema(longitude=longitude)

    def test_non_positive_interval_is_rejected(self):
        with pytest.raises(ValidationError):
            SystemConfigurationSchema(scheduler_interval_seconds=0)
