"""Validation schemas for home load domain."""

import uuid
from datetime import datetime
from typing import Dict, Optional, Union, cast

from pydantic import BaseModel, Field, field_serializer, field_validator

from edge_mining.domain.common import EntityId, Timestamp, Watts
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import HomeForecastProviderAdapter
from edge_mining.domain.home_load.entities import HomeForecastProvider, LoadDevice
from edge_mining.domain.home_load.value_objects import ConsumptionForecast
from edge_mining.shared.adapter_configs.home_load import HomeForecastProviderDummyConfig
from edge_mining.shared.adapter_maps.home_load import HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import HomeForecastProviderConfig


class ConsumptionForecastSchema(BaseModel):
    """Schema for ConsumptionForecast value object."""

    predicted_watts: Dict[datetime, float] = Field(default_factory=dict, description="Predicted power consumption")
    generated_at: datetime = Field(..., description="When this forecast was generated")

    @field_validator("predicted_watts")
    @classmethod
    def validate_predicted_watts(cls, v: Dict[datetime, float]) -> Dict[datetime, float]:
        """Validate predicted watts values are non-negative."""
        for _, watts in v.items():
            if watts < 0:
                raise ValueError(f"Power consumption cannot be negative: {watts}")
        return v

    @classmethod
    def from_model(cls, consumption_forecast: ConsumptionForecast) -> "ConsumptionForecastSchema":
        """Create schema from domain model."""
        # Convert domain model to schema format
        predicted_watts_dict = {}
        for timestamp, watts in consumption_forecast.predicted_watts.items():
            predicted_watts_dict[cast(datetime, timestamp)] = float(watts)

        return cls(
            predicted_watts=predicted_watts_dict,
            generated_at=consumption_forecast.generated_at,
        )

    def to_model(self) -> ConsumptionForecast:
        """Convert schema to domain model."""
        # Convert schema format to domain model
        predicted_watts_domain = {}
        for timestamp, watts in self.predicted_watts.items():
            predicted_watts_domain[Timestamp(timestamp)] = Watts(watts)

        return ConsumptionForecast(
            predicted_watts=predicted_watts_domain,
            generated_at=Timestamp(self.generated_at),
        )


class LoadDeviceSchema(BaseModel):
    """Schema for LoadDevice entity with complete validation."""

    id: str = Field(..., description="Unique identifier for the load device")
    name: str = Field(default="", description="Load device name")
    type: str = Field(default="", description="Type of load device (e.g., Appliance, Heating)")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that id is a valid UUID string."""
        try:
            uuid.UUID(v)
            return v
        except ValueError as e:
            raise ValueError(f"Invalid UUID format: {v}") from e

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate device name."""
        if not v.strip():
            raise ValueError("Device name cannot be empty")
        return v.strip()

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate device type."""
        if not v.strip():
            raise ValueError("Device type cannot be empty")
        return v.strip()

    @classmethod
    def from_model(cls, load_device: LoadDevice) -> "LoadDeviceSchema":
        """Create schema from domain model."""
        return cls(
            id=str(load_device.id),
            name=load_device.name,
            type=load_device.type,
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return value

    def to_model(self) -> LoadDevice:
        """Convert schema to domain model."""
        return LoadDevice(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            type=self.type,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class LoadDeviceCreateSchema(BaseModel):
    """Schema for creating a new load device."""

    name: str = Field(default="", description="Load device name")
    type: str = Field(default="", description="Type of load device")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate device name."""
        if not v.strip():
            raise ValueError("Device name cannot be empty")
        return v.strip()

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate device type."""
        if not v.strip():
            raise ValueError("Device type cannot be empty")
        return v.strip()

    def to_model(self) -> LoadDevice:
        """Convert schema to domain model."""
        return LoadDevice(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            type=self.type,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class LoadDeviceUpdateSchema(BaseModel):
    """Schema for updating an existing load device."""

    name: str = Field(default="", description="Load device name")
    type: str = Field(default="", description="Type of load device")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate device name."""
        if not v.strip():
            raise ValueError("Device name cannot be empty")
        return v.strip()

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate device type."""
        if not v.strip():
            raise ValueError("Device type cannot be empty")
        return v.strip()

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class HomeLoadsProfileSchema(BaseModel):
    """Schema for HomeLoadsProfile aggregate root."""

    id: str = Field(..., description="Unique identifier for the home loads profile")
    name: str = Field(default="Default Home Profile", description="Profile name")
    devices: Dict[str, LoadDeviceSchema] = Field(default_factory=dict, description="Load devices in this profile")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that id is a valid UUID string."""
        try:
            uuid.UUID(v)
            return v
        except ValueError as e:
            raise ValueError(f"Invalid UUID format: {v}") from e

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate profile name."""
        if not v.strip():
            raise ValueError("Profile name cannot be empty")
        return v.strip()

    @classmethod
    def from_model(cls, profile: HomeLoadsProfile) -> "HomeLoadsProfileSchema":
        """Create schema from domain model."""
        devices_schema = {}
        for device_id, device in profile.devices.items():
            devices_schema[str(device_id)] = LoadDeviceSchema.from_model(device)

        return cls(
            id=str(profile.id),
            name=profile.name,
            devices=devices_schema,
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return value

    def to_model(self) -> HomeLoadsProfile:
        """Convert schema to domain model."""
        devices_domain = {}
        for device_id_str, device_schema in self.devices.items():
            device_id = EntityId(uuid.UUID(device_id_str))
            devices_domain[device_id] = device_schema.to_model()

        return HomeLoadsProfile(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            devices=devices_domain,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class HomeLoadsProfileCreateSchema(BaseModel):
    """Schema for creating a new home loads profile."""

    name: str = Field(default="Default Home Profile", description="Profile name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate profile name."""
        if not v.strip():
            raise ValueError("Profile name cannot be empty")
        return v.strip()

    def to_model(self) -> HomeLoadsProfile:
        """Convert schema to domain model."""
        return HomeLoadsProfile(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            devices={},
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class HomeLoadsProfileUpdateSchema(BaseModel):
    """Schema for updating an existing home loads profile."""

    name: str = Field(default="", description="Profile name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate profile name."""
        if not v.strip():
            raise ValueError("Profile name cannot be empty")
        return v.strip()

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class HomeForecastProviderSchema(BaseModel):
    """Schema for HomeForecastProvider entity with complete validation."""

    id: str = Field(..., description="Unique identifier for the home forecast provider")
    name: str = Field(default="", description="Home forecast provider name")
    adapter_type: HomeForecastProviderAdapter = Field(
        default=HomeForecastProviderAdapter.DUMMY, description="Type of home forecast provider adapter"
    )
    config: dict = Field(default={}, description="Home forecast provider configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that id is a valid UUID string."""
        try:
            uuid.UUID(v)
            return v
        except ValueError as e:
            raise ValueError(f"Invalid UUID format: {v}") from e

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate provider name."""
        if not v.strip():
            raise ValueError("Provider name cannot be empty")
        return v.strip()

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> HomeForecastProviderAdapter:
        """Validate that adapter_type is a recognized HomeForecastProviderAdapter."""
        adapter_values = [adapter.value for adapter in HomeForecastProviderAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return HomeForecastProviderAdapter(v)

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that external_service_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("external_service_id must be a valid UUID string") from exc
        return v

    @classmethod
    def from_model(cls, provider: HomeForecastProvider) -> "HomeForecastProviderSchema":
        """Create schema from domain model."""
        config_dict = {}
        if provider.config:
            config_dict = provider.config.to_dict()

        return cls(
            id=str(provider.id),
            name=provider.name,
            adapter_type=provider.adapter_type,
            config=config_dict,
            external_service_id=str(provider.external_service_id) if provider.external_service_id else None,
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return value

    @field_serializer("external_service_id")
    def serialize_external_service_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize external service id field."""
        return value

    def to_model(self) -> HomeForecastProvider:
        """Convert schema to domain model."""
        configuration: Optional[HomeForecastProviderConfig] = None
        if self.config:
            config_type = HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(self.adapter_type)
            if config_type:
                configuration = cast(HomeForecastProviderConfig, config_type.from_dict(self.config))

        return HomeForecastProvider(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            adapter_type=self.adapter_type,
            config=configuration,
            external_service_id=EntityId(uuid.UUID(self.external_service_id)) if self.external_service_id else None,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            uuid.UUID: str,
            HomeForecastProviderAdapter: lambda v: v.value,
        }


class HomeForecastProviderCreateSchema(BaseModel):
    """Schema for creating a new home forecast provider."""

    name: str = Field(default="", description="Home forecast provider name")
    adapter_type: HomeForecastProviderAdapter = Field(
        default=HomeForecastProviderAdapter.DUMMY, description="Type of home forecast provider adapter"
    )
    config: Optional[dict] = Field(default=None, description="Home forecast provider configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate provider name."""
        if not v.strip():
            raise ValueError("Provider name cannot be empty")
        return v.strip()

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> HomeForecastProviderAdapter:
        """Validate that adapter_type is a recognized HomeForecastProviderAdapter."""
        adapter_values = [adapter.value for adapter in HomeForecastProviderAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return HomeForecastProviderAdapter(v)

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that external_service_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("external_service_id must be a valid UUID string") from exc
        return v

    def to_model(self) -> HomeForecastProvider:
        """Convert schema to domain model."""
        configuration: Optional[HomeForecastProviderConfig] = None
        if self.config:
            config_type = HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(self.adapter_type)
            if config_type:
                configuration = cast(HomeForecastProviderConfig, config_type.from_dict(self.config))

        return HomeForecastProvider(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            adapter_type=self.adapter_type,
            config=configuration,
            external_service_id=EntityId(uuid.UUID(self.external_service_id)) if self.external_service_id else None,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            uuid.UUID: str,
            HomeForecastProviderAdapter: lambda v: v.value,
        }


class HomeForecastProviderUpdateSchema(BaseModel):
    """Schema for updating an existing home forecast provider."""

    name: str = Field(default="", description="Home forecast provider name")
    config: Optional[dict] = Field(default=None, description="Home forecast provider configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate provider name."""
        if not v.strip():
            raise ValueError("Provider name cannot be empty")
        return v.strip()

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that external_service_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("external_service_id must be a valid UUID string") from exc
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


class HomeForecastProviderDummyConfigSchema(BaseModel):
    """Schema for Dummy HomeForecastProviderConfig."""

    load_power_max: float = Field(default=500.0, ge=0, description="Maximum load power in Watts")

    @field_validator("load_power_max")
    @classmethod
    def validate_load_power_max(cls, v: float) -> float:
        """Validate load power max is non-negative."""
        if v < 0:
            raise ValueError("Maximum load power cannot be negative")
        return v

    def to_model(self) -> HomeForecastProviderDummyConfig:
        """Convert schema to domain model."""
        return HomeForecastProviderDummyConfig(load_power_max=self.load_power_max)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


HOME_FORECAST_PROVIDER_CONFIG_SCHEMA_MAP: Dict[
    type[HomeForecastProviderConfig],
    Union[type[HomeForecastProviderDummyConfigSchema]],
] = {
    HomeForecastProviderDummyConfig: HomeForecastProviderDummyConfigSchema,
}
