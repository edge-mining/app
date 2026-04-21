"""Validation schemas for home load domain."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, cast

from pydantic import BaseModel, Field, field_serializer, field_validator

from edge_mining.domain.common import EntityId, Timestamp, Watts
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter, LoadDeviceCategory
from edge_mining.domain.home_load.entities import EnergyLoadForecastProvider, LoadDevice
from edge_mining.domain.home_load.value_objects import HomeLoadEnergyInterval, LoadEnergyConsumption
from edge_mining.shared.adapter_configs.home_load import EnergyLoadForecastProviderDummyConfig
from edge_mining.shared.adapter_maps.home_load import ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import EnergyLoadForecastProviderConfig


class HomeLoadEnergyIntervalSchema(BaseModel):
    """Schema for HomeLoadEnergyInterval value object."""

    start: datetime = Field(..., description="Interval start timestamp")
    end: datetime = Field(..., description="Interval end timestamp")
    energy: Optional[float] = Field(default=None, description="Energy in watt-hours")
    avg_power: Optional[float] = Field(default=None, description="Average power in watts")


class LoadEnergyConsumptionSchema(BaseModel):
    """Schema for LoadEnergyConsumption value object."""

    timestamp: datetime = Field(..., description="When this consumption data was generated")
    intervals: List[HomeLoadEnergyIntervalSchema] = Field(
        default_factory=list, description="List of consumption intervals"
    )

    @classmethod
    def from_model(cls, consumption: LoadEnergyConsumption) -> "LoadEnergyConsumptionSchema":
        """Create schema from domain model."""
        intervals = [
            HomeLoadEnergyIntervalSchema(
                start=cast(datetime, interval.start),
                end=cast(datetime, interval.end),
                energy=float(interval.energy) if interval.energy is not None else None,
                avg_power=float(interval.avg_power),
            )
            for interval in consumption.intervals
        ]

        return cls(
            timestamp=cast(datetime, consumption.timestamp),
            intervals=intervals,
        )

    def to_model(self) -> LoadEnergyConsumption:
        """Convert schema to domain model."""
        intervals: List[HomeLoadEnergyInterval] = []
        for interval_schema in self.intervals:
            intervals.append(
                HomeLoadEnergyInterval(
                    start=Timestamp(interval_schema.start),
                    end=Timestamp(interval_schema.end),
                    energy=None if interval_schema.energy is None else Watts(interval_schema.energy),
                )
            )

        return LoadEnergyConsumption(
            timestamp=Timestamp(self.timestamp),
            intervals=intervals,
        )


class LoadDeviceSchema(BaseModel):
    """Schema for LoadDevice entity with complete validation."""

    id: str = Field(..., description="Unique identifier for the load device")
    name: str = Field(default="", description="Load device name")
    category: LoadDeviceCategory = Field(
        default=LoadDeviceCategory.OCCASIONAL, description="Category of load device (e.g., controllable, continuous)"
    )
    enabled: bool = Field(default=True, description="Whether the load device is active in the system")
    energy_load_forecast_provider_id: Optional[str] = Field(
        default=None, description="ID of the energy load forecast provider associated with this load device"
    )

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

    @field_validator("energy_load_forecast_provider_id")
    @classmethod
    def validate_energy_load_forecast_provider_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that energy_load_forecast_provider_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("energy_load_forecast_provider_id must be a valid UUID string") from exc
        return v

    @classmethod
    def from_model(cls, load_device: LoadDevice) -> "LoadDeviceSchema":
        """Create schema from domain model."""
        return cls(
            id=str(load_device.id),
            name=load_device.name,
            category=load_device.category,
            enabled=load_device.enabled,
            energy_load_forecast_provider_id=(
                str(load_device.energy_load_forecast_provider_id)
                if load_device.energy_load_forecast_provider_id
                else None
            ),
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return value

    @field_serializer("energy_load_forecast_provider_id")
    def serialize_energy_load_forecast_provider_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize energy_load_forecast_provider_id field."""
        return value

    def to_model(self) -> LoadDevice:
        """Convert schema to domain model."""
        provider_id = (
            EntityId(uuid.UUID(self.energy_load_forecast_provider_id))
            if self.energy_load_forecast_provider_id
            else None
        )
        return LoadDevice(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            category=self.category,
            enabled=self.enabled,
            energy_load_forecast_provider_id=provider_id,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class LoadDeviceCreateSchema(BaseModel):
    """Schema for creating a new load device."""

    name: str = Field(default="", description="Load device name")
    category: LoadDeviceCategory = Field(default=LoadDeviceCategory.OCCASIONAL, description="Category of load device")
    enabled: bool = Field(default=True, description="Whether the load device is active in the system")
    energy_load_forecast_provider_id: Optional[str] = Field(
        default=None, description="ID of the energy load forecast provider associated with this load device"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate device name."""
        if not v.strip():
            raise ValueError("Device name cannot be empty")
        return v.strip()

    @field_validator("energy_load_forecast_provider_id")
    @classmethod
    def validate_energy_load_forecast_provider_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that energy_load_forecast_provider_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("energy_load_forecast_provider_id must be a valid UUID string") from exc
        return v

    @field_serializer("energy_load_forecast_provider_id")
    def serialize_energy_load_forecast_provider_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize energy_load_forecast_provider_id field."""
        return value

    def to_model(self) -> LoadDevice:
        """Convert schema to domain model."""
        provider_id = (
            EntityId(uuid.UUID(self.energy_load_forecast_provider_id))
            if self.energy_load_forecast_provider_id
            else None
        )
        return LoadDevice(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            category=self.category,
            enabled=self.enabled,
            energy_load_forecast_provider_id=provider_id,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class LoadDeviceUpdateSchema(BaseModel):
    """Schema for updating an existing load device."""

    name: str = Field(default="", description="Load device name")
    category: LoadDeviceCategory = Field(default=LoadDeviceCategory.OCCASIONAL, description="Category of load device")
    enabled: bool = Field(default=True, description="Whether the load device is active in the system")
    energy_load_forecast_provider_id: Optional[str] = Field(
        default=None, description="ID of the energy load forecast provider associated with this load device"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate device name."""
        if not v.strip():
            raise ValueError("Device name cannot be empty")
        return v.strip()

    @field_validator("energy_load_forecast_provider_id")
    @classmethod
    def validate_energy_load_forecast_provider_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that energy_load_forecast_provider_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("energy_load_forecast_provider_id must be a valid UUID string") from exc
        return v

    @field_serializer("energy_load_forecast_provider_id")
    def serialize_energy_load_forecast_provider_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize energy_load_forecast_provider_id field."""
        return value

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class HomeLoadsProfileSchema(BaseModel):
    """Schema for HomeLoadsProfile aggregate root."""

    id: str = Field(..., description="Unique identifier for the home loads profile")
    name: str = Field(default="Default Home Profile", description="Profile name")
    devices: List[LoadDeviceSchema] = Field(default_factory=list, description="Load devices in this profile")

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
        devices = []
        for device in profile.devices:
            devices.append(LoadDeviceSchema.from_model(device))

        return cls(
            id=str(profile.id),
            name=profile.name,
            devices=devices,
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return value

    def to_model(self) -> HomeLoadsProfile:
        """Convert schema to domain model."""
        devices = []
        for device_schema in self.devices:
            devices.append(device_schema.to_model())

        return HomeLoadsProfile(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            devices=devices,
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
            devices=[],
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


class EnergyLoadForecastProviderSchema(BaseModel):
    """Schema for EnergyLoadForecastProvider entity with complete validation."""

    id: str = Field(..., description="Unique identifier for the energy load forecast provider")
    name: str = Field(default="", description="Energy load forecast provider name")
    adapter_type: EnergyLoadForecastProviderAdapter = Field(
        default=EnergyLoadForecastProviderAdapter.DUMMY,
        description="Type of energy load forecast provider adapter",
    )
    config: dict = Field(default={}, description="Energy load forecast provider configuration")
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
    def validate_adapter_type(cls, v: str) -> EnergyLoadForecastProviderAdapter:
        """Validate that adapter_type is a recognized EnergyLoadForecastProviderAdapter."""
        adapter_values = [adapter.value for adapter in EnergyLoadForecastProviderAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return EnergyLoadForecastProviderAdapter(v)

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
    def from_model(cls, provider: EnergyLoadForecastProvider) -> "EnergyLoadForecastProviderSchema":
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

    def to_model(self) -> EnergyLoadForecastProvider:
        """Convert schema to domain model."""
        configuration: Optional[EnergyLoadForecastProviderConfig] = None
        if self.config:
            config_type = ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(self.adapter_type)
            if config_type:
                configuration = cast(EnergyLoadForecastProviderConfig, config_type.from_dict(self.config))

        return EnergyLoadForecastProvider(
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
            EnergyLoadForecastProviderAdapter: lambda v: v.value,
        }


class EnergyLoadForecastProviderCreateSchema(BaseModel):
    """Schema for creating a new energy load forecast provider."""

    name: str = Field(default="", description="Energy load forecast provider name")
    adapter_type: EnergyLoadForecastProviderAdapter = Field(
        default=EnergyLoadForecastProviderAdapter.DUMMY,
        description="Type of energy load forecast provider adapter",
    )
    config: Optional[dict] = Field(default=None, description="Energy load forecast provider configuration")
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
    def validate_adapter_type(cls, v: str) -> EnergyLoadForecastProviderAdapter:
        """Validate that adapter_type is a recognized EnergyLoadForecastProviderAdapter."""
        adapter_values = [adapter.value for adapter in EnergyLoadForecastProviderAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return EnergyLoadForecastProviderAdapter(v)

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

    def to_model(self) -> EnergyLoadForecastProvider:
        """Convert schema to domain model."""
        configuration: Optional[EnergyLoadForecastProviderConfig] = None
        if self.config:
            config_type = ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(self.adapter_type)
            if config_type:
                configuration = cast(EnergyLoadForecastProviderConfig, config_type.from_dict(self.config))

        return EnergyLoadForecastProvider(
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
            EnergyLoadForecastProviderAdapter: lambda v: v.value,
        }


class EnergyLoadForecastProviderUpdateSchema(BaseModel):
    """Schema for updating an existing energy load forecast provider."""

    name: str = Field(default="", description="Energy load forecast provider name")
    config: Optional[dict] = Field(default=None, description="Energy load forecast provider configuration")
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


class EnergyLoadForecastProviderDummyConfigSchema(BaseModel):
    """Schema for Dummy EnergyLoadForecastProviderConfig."""

    load_power_max: float = Field(default=500.0, ge=0, description="Maximum load power in Watts")

    @field_validator("load_power_max")
    @classmethod
    def validate_load_power_max(cls, v: float) -> float:
        """Validate load power max is non-negative."""
        if v < 0:
            raise ValueError("Maximum load power cannot be negative")
        return v

    def to_model(self) -> EnergyLoadForecastProviderDummyConfig:
        """Convert schema to domain model."""
        return EnergyLoadForecastProviderDummyConfig(load_power_max=self.load_power_max)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_SCHEMA_MAP: Dict[
    type[EnergyLoadForecastProviderConfig],
    Union[type[EnergyLoadForecastProviderDummyConfigSchema]],
] = {
    EnergyLoadForecastProviderDummyConfig: EnergyLoadForecastProviderDummyConfigSchema,
}
