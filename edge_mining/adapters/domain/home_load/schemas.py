"""Validation schemas for home load domain."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, cast

from pydantic import BaseModel, Field, computed_field, field_serializer, field_validator

from edge_mining.domain.common import EntityId, Timestamp, WattHours
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import (
    EnergyLoadForecastProviderAdapter,
    EnergyLoadHistoryProviderAdapter,
    LoadDeviceCategory,
)
from edge_mining.domain.home_load.entities import (
    EnergyLoadForecastProvider,
    EnergyLoadHistoryProvider,
    LoadConsumptionModel,
    LoadDevice,
)
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    HomeLoadsConsumption,
    LoadDeviceConsumption,
    LoadEnergyConsumption,
)
from edge_mining.shared.adapter_configs.home_load import (
    EnergyLoadForecastProviderDummyConfig,
    EnergyLoadForecastProviderNaiveLastHourConfig,
    EnergyLoadForecastProviderNaivePersistenceConfig,
    EnergyLoadForecastProviderSeasonalBaselineConfig,
    EnergyLoadForecastProviderStatsmodelsConfig,
    EnergyLoadForecastProviderXGBoostConfig,
    EnergyLoadHistoryProviderHomeAssistantAPIConfig,
)
from edge_mining.shared.adapter_maps.home_load import (
    ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP,
    ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_TYPE_MAP,
)
from edge_mining.shared.interfaces.config import EnergyLoadForecastProviderConfig, EnergyLoadHistoryProviderConfig


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
                    energy=None if interval_schema.energy is None else WattHours(interval_schema.energy),
                )
            )

        return LoadEnergyConsumption(
            timestamp=Timestamp(self.timestamp),
            intervals=intervals,
        )


class LoadDeviceConsumptionSchema(BaseModel):
    """Schema for LoadDeviceConsumption value object (device-bound history + forecast)."""

    device_id: str = Field(..., description="Device UUID")
    device_name: str = Field(..., description="Device unique name within profile")
    device_category: LoadDeviceCategory = Field(..., description="Device category")
    history: LoadEnergyConsumptionSchema = Field(
        default_factory=lambda: LoadEnergyConsumptionSchema(timestamp=datetime.now(), intervals=[]),
        description="Measured consumption time series.",
    )
    forecast: LoadEnergyConsumptionSchema = Field(
        default_factory=lambda: LoadEnergyConsumptionSchema(timestamp=datetime.now(), intervals=[]),
        description="Predicted consumption time series.",
    )

    @classmethod
    def from_model(cls, consumption: LoadDeviceConsumption) -> "LoadDeviceConsumptionSchema":
        return cls(
            device_id=str(consumption.device_id),
            device_name=consumption.device_name,
            device_category=consumption.device_category,
            history=LoadEnergyConsumptionSchema.from_model(consumption.history),
            forecast=LoadEnergyConsumptionSchema.from_model(consumption.forecast),
        )

    def to_model(self) -> LoadDeviceConsumption:
        return LoadDeviceConsumption(
            device_id=EntityId(uuid.UUID(self.device_id)),
            device_name=self.device_name,
            device_category=self.device_category,
            history=self.history.to_model(),
            forecast=self.forecast.to_model(),
        )


class HomeLoadsConsumptionSchema(BaseModel):
    """Schema for HomeLoadsConsumption value object (unified household view)."""

    per_device: List[LoadDeviceConsumptionSchema] = Field(default_factory=list)
    total_history: LoadEnergyConsumptionSchema = Field(
        default_factory=lambda: LoadEnergyConsumptionSchema(timestamp=datetime.now(), intervals=[]),
        description="Aggregated household history.",
    )
    total_forecast: LoadEnergyConsumptionSchema = Field(
        default_factory=lambda: LoadEnergyConsumptionSchema(timestamp=datetime.now(), intervals=[]),
        description="Aggregated household forecast.",
    )

    @classmethod
    def from_model(cls, consumption: HomeLoadsConsumption) -> "HomeLoadsConsumptionSchema":
        return cls(
            per_device=[LoadDeviceConsumptionSchema.from_model(d) for d in consumption.per_device],
            total_history=LoadEnergyConsumptionSchema.from_model(consumption.total_history),
            total_forecast=LoadEnergyConsumptionSchema.from_model(consumption.total_forecast),
        )

    def to_model(self) -> HomeLoadsConsumption:
        return HomeLoadsConsumption(
            per_device=[d.to_model() for d in self.per_device],
            total_history=self.total_history.to_model(),
            total_forecast=self.total_forecast.to_model(),
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
    energy_load_history_provider_id: Optional[str] = Field(
        default=None, description="ID of the energy load history provider associated with this load device"
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

    @field_validator("energy_load_forecast_provider_id", "energy_load_history_provider_id")
    @classmethod
    def validate_provider_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that provider ID is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("Provider ID must be a valid UUID string") from exc
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
            energy_load_history_provider_id=(
                str(load_device.energy_load_history_provider_id)
                if load_device.energy_load_history_provider_id
                else None
            ),
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return value

    @field_serializer("energy_load_forecast_provider_id", "energy_load_history_provider_id")
    def serialize_provider_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize provider ID field."""
        return value

    def to_model(self) -> LoadDevice:
        """Convert schema to domain model."""
        forecast_provider_id = (
            EntityId(uuid.UUID(self.energy_load_forecast_provider_id))
            if self.energy_load_forecast_provider_id
            else None
        )
        history_provider_id = (
            EntityId(uuid.UUID(self.energy_load_history_provider_id)) if self.energy_load_history_provider_id else None
        )
        return LoadDevice(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            category=LoadDeviceCategory(self.category) if isinstance(self.category, str) else self.category,
            enabled=self.enabled,
            energy_load_forecast_provider_id=forecast_provider_id,
            energy_load_history_provider_id=history_provider_id,
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
    energy_load_history_provider_id: Optional[str] = Field(
        default=None, description="ID of the energy load history provider associated with this load device"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate device name."""
        if not v.strip():
            raise ValueError("Device name cannot be empty")
        return v.strip()

    @field_validator("energy_load_forecast_provider_id", "energy_load_history_provider_id")
    @classmethod
    def validate_provider_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that provider ID is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("Provider ID must be a valid UUID string") from exc
        return v

    @field_serializer("energy_load_forecast_provider_id", "energy_load_history_provider_id")
    def serialize_provider_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize provider ID field."""
        return value

    def to_model(self) -> LoadDevice:
        """Convert schema to domain model."""
        forecast_provider_id = (
            EntityId(uuid.UUID(self.energy_load_forecast_provider_id))
            if self.energy_load_forecast_provider_id
            else None
        )
        history_provider_id = (
            EntityId(uuid.UUID(self.energy_load_history_provider_id)) if self.energy_load_history_provider_id else None
        )
        return LoadDevice(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            category=LoadDeviceCategory(self.category) if isinstance(self.category, str) else self.category,
            enabled=self.enabled,
            energy_load_forecast_provider_id=forecast_provider_id,
            energy_load_history_provider_id=history_provider_id,
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
    energy_load_history_provider_id: Optional[str] = Field(
        default=None, description="ID of the energy load history provider associated with this load device"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate device name."""
        if not v.strip():
            raise ValueError("Device name cannot be empty")
        return v.strip()

    @field_validator("energy_load_forecast_provider_id", "energy_load_history_provider_id")
    @classmethod
    def validate_provider_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that provider ID is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("Provider ID must be a valid UUID string") from exc
        return v

    @field_serializer("energy_load_forecast_provider_id", "energy_load_history_provider_id")
    def serialize_provider_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize provider ID field."""
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

    @computed_field  # type: ignore[prop-decorator]
    @property
    def min_required_history_hours(self) -> int:
        """Minimum hours of historical data the provider needs to produce a forecast."""
        adapter = self.adapter_type
        cfg = self.config or {}

        if adapter == EnergyLoadForecastProviderAdapter.NAIVE_LAST_HOUR:
            return 1
        if adapter == EnergyLoadForecastProviderAdapter.NAIVE_PERSISTENCE:
            delta_days = int(cfg.get("delta_days", 1))
            return delta_days * 24
        if adapter == EnergyLoadForecastProviderAdapter.STATSMODELS:
            seasonal_periods = int(cfg.get("seasonal_periods", 24))
            return seasonal_periods * 2
        if adapter == EnergyLoadForecastProviderAdapter.XGBOOST:
            hours_ahead = int(cfg.get("hours_ahead", 3))
            return 168 + 48 + hours_ahead
        return 0

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


class EnergyLoadForecastProviderNaiveLastHourConfigSchema(BaseModel):
    """Schema for NaiveLastHour EnergyLoadForecastProviderConfig."""

    hours_ahead: int = Field(default=3, ge=1, le=72, description="Number of hours to forecast ahead")

    def to_model(self) -> EnergyLoadForecastProviderNaiveLastHourConfig:
        """Convert schema to domain model."""
        return EnergyLoadForecastProviderNaiveLastHourConfig(hours_ahead=self.hours_ahead)

    class Config:
        use_enum_values = True
        validate_assignment = True


class EnergyLoadForecastProviderNaivePersistenceConfigSchema(BaseModel):
    """Schema for NaivePersistence EnergyLoadForecastProviderConfig."""

    hours_ahead: int = Field(default=24, ge=1, le=72, description="Number of hours to forecast ahead")
    delta_days: int = Field(default=1, ge=1, le=7, description="Number of days back to use as reference")

    def to_model(self) -> EnergyLoadForecastProviderNaivePersistenceConfig:
        """Convert schema to domain model."""
        return EnergyLoadForecastProviderNaivePersistenceConfig(
            hours_ahead=self.hours_ahead,
            delta_days=self.delta_days,
        )

    class Config:
        use_enum_values = True
        validate_assignment = True


class EnergyLoadForecastProviderSeasonalBaselineConfigSchema(BaseModel):
    """Schema for SeasonalBaseline EnergyLoadForecastProviderConfig."""

    hours_ahead: int = Field(default=3, ge=1, le=72, description="Number of hours to forecast ahead")
    weeks_lookback: int = Field(default=4, ge=1, le=52, description="Number of weeks of history to use for profiling")

    def to_model(self) -> EnergyLoadForecastProviderSeasonalBaselineConfig:
        """Convert schema to domain model."""
        return EnergyLoadForecastProviderSeasonalBaselineConfig(
            hours_ahead=self.hours_ahead,
            weeks_lookback=self.weeks_lookback,
        )

    class Config:
        use_enum_values = True
        validate_assignment = True


class EnergyLoadForecastProviderStatsmodelsConfigSchema(BaseModel):
    """Schema for Statsmodels EnergyLoadForecastProviderConfig."""

    hours_ahead: int = Field(default=3, ge=1, le=72, description="Number of hours to forecast ahead")
    weeks_lookback: int = Field(default=8, ge=1, le=52, description="Weeks of history for training")
    method: str = Field(default="hw", description="Statsmodels method: 'hw' (Holt-Winters) or 'sarima'")
    seasonal_periods: int = Field(default=24, ge=1, le=168, description="Hours in a seasonal cycle")

    def to_model(self) -> EnergyLoadForecastProviderStatsmodelsConfig:
        """Convert schema to domain model."""
        return EnergyLoadForecastProviderStatsmodelsConfig(
            hours_ahead=self.hours_ahead,
            weeks_lookback=self.weeks_lookback,
            method=self.method,
            seasonal_periods=self.seasonal_periods,
        )

    class Config:
        use_enum_values = True
        validate_assignment = True


class EnergyLoadForecastProviderXGBoostConfigSchema(BaseModel):
    """Schema for XGBoost EnergyLoadForecastProviderConfig."""

    hours_ahead: int = Field(default=3, ge=1, le=72, description="Number of hours to forecast ahead")
    weeks_lookback: int = Field(default=8, ge=1, le=52, description="Weeks of history for training")
    n_estimators: int = Field(default=100, ge=10, le=1000, description="Number of boosting rounds")
    max_depth: int = Field(default=6, ge=1, le=15, description="Maximum tree depth")
    learning_rate: float = Field(default=0.1, gt=0.0, le=1.0, description="Learning rate")

    def to_model(self) -> EnergyLoadForecastProviderXGBoostConfig:
        """Convert schema to domain model."""
        return EnergyLoadForecastProviderXGBoostConfig(
            hours_ahead=self.hours_ahead,
            weeks_lookback=self.weeks_lookback,
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
        )

    class Config:
        use_enum_values = True
        validate_assignment = True


ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_SCHEMA_MAP: Dict[
    type[EnergyLoadForecastProviderConfig],
    Union[
        type[EnergyLoadForecastProviderDummyConfigSchema],
        type[EnergyLoadForecastProviderNaiveLastHourConfigSchema],
        type[EnergyLoadForecastProviderNaivePersistenceConfigSchema],
        type[EnergyLoadForecastProviderSeasonalBaselineConfigSchema],
        type[EnergyLoadForecastProviderStatsmodelsConfigSchema],
        type[EnergyLoadForecastProviderXGBoostConfigSchema],
    ],
] = {
    EnergyLoadForecastProviderDummyConfig: EnergyLoadForecastProviderDummyConfigSchema,
    EnergyLoadForecastProviderNaiveLastHourConfig: EnergyLoadForecastProviderNaiveLastHourConfigSchema,
    EnergyLoadForecastProviderNaivePersistenceConfig: EnergyLoadForecastProviderNaivePersistenceConfigSchema,
    EnergyLoadForecastProviderSeasonalBaselineConfig: EnergyLoadForecastProviderSeasonalBaselineConfigSchema,
    EnergyLoadForecastProviderStatsmodelsConfig: EnergyLoadForecastProviderStatsmodelsConfigSchema,
    EnergyLoadForecastProviderXGBoostConfig: EnergyLoadForecastProviderXGBoostConfigSchema,
}


# --- Energy Load History Provider Schemas ---


class EnergyLoadHistoryProviderSchema(BaseModel):
    """Schema for EnergyLoadHistoryProvider entity."""

    id: str = Field(..., description="Unique identifier for the energy load history provider")
    name: str = Field(default="", description="Energy load history provider name")
    adapter_type: EnergyLoadHistoryProviderAdapter = Field(
        default=EnergyLoadHistoryProviderAdapter.DUMMY,
        description="Type of energy load history provider adapter",
    )
    config: Optional[dict] = Field(default=None, description="Energy load history provider configuration")
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
    def validate_adapter_type(cls, v: str) -> EnergyLoadHistoryProviderAdapter:
        """Validate that adapter_type is a recognized EnergyLoadHistoryProviderAdapter."""
        adapter_values = [adapter.value for adapter in EnergyLoadHistoryProviderAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return EnergyLoadHistoryProviderAdapter(v)

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
    def from_model(cls, provider: EnergyLoadHistoryProvider) -> "EnergyLoadHistoryProviderSchema":
        """Create schema from domain model."""
        config_dict = None
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

    def to_model(self) -> EnergyLoadHistoryProvider:
        """Convert schema to domain model."""
        configuration: Optional[EnergyLoadHistoryProviderConfig] = None
        if self.config:
            config_type = ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_TYPE_MAP.get(self.adapter_type)
            if config_type:
                configuration = cast(EnergyLoadHistoryProviderConfig, config_type.from_dict(self.config))

        return EnergyLoadHistoryProvider(
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
            EnergyLoadHistoryProviderAdapter: lambda v: v.value,
        }


class EnergyLoadHistoryProviderCreateSchema(BaseModel):
    """Schema for creating a new energy load history provider."""

    name: str = Field(default="", description="Energy load history provider name")
    adapter_type: EnergyLoadHistoryProviderAdapter = Field(
        default=EnergyLoadHistoryProviderAdapter.DUMMY,
        description="Type of energy load history provider adapter",
    )
    config: Optional[dict] = Field(default=None, description="Energy load history provider configuration")
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
    def validate_adapter_type(cls, v: str) -> EnergyLoadHistoryProviderAdapter:
        """Validate that adapter_type is a recognized EnergyLoadHistoryProviderAdapter."""
        adapter_values = [adapter.value for adapter in EnergyLoadHistoryProviderAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return EnergyLoadHistoryProviderAdapter(v)

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

    def to_model(self) -> EnergyLoadHistoryProvider:
        """Convert schema to domain model."""
        configuration: Optional[EnergyLoadHistoryProviderConfig] = None
        if self.config:
            config_type = ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_TYPE_MAP.get(self.adapter_type)
            if config_type:
                configuration = cast(EnergyLoadHistoryProviderConfig, config_type.from_dict(self.config))

        return EnergyLoadHistoryProvider(
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
            EnergyLoadHistoryProviderAdapter: lambda v: v.value,
        }


class EnergyLoadHistoryProviderUpdateSchema(BaseModel):
    """Schema for updating an existing energy load history provider."""

    name: str = Field(default="", description="Energy load history provider name")
    config: Optional[dict] = Field(default=None, description="Energy load history provider configuration")
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


class EnergyLoadHistoryProviderHomeAssistantAPIConfigSchema(BaseModel):
    """Schema for HomeAssistantAPI EnergyLoadHistoryProviderConfig."""

    entity_power: str = Field(default="", description="Home Assistant entity ID for power sensor")
    unit_power: str = Field(default="W", description="Unit of power measurement")

    @field_validator("entity_power")
    @classmethod
    def validate_entity_power(cls, v: str) -> str:
        """Validate entity_power is not empty."""
        if not v.strip():
            raise ValueError("entity_power cannot be empty")
        return v.strip()

    def to_model(self) -> EnergyLoadHistoryProviderHomeAssistantAPIConfig:
        """Convert schema to domain model."""
        return EnergyLoadHistoryProviderHomeAssistantAPIConfig(
            entity_power=self.entity_power, unit_power=self.unit_power
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_SCHEMA_MAP: Dict[
    type[EnergyLoadHistoryProviderConfig],
    Union[type[EnergyLoadHistoryProviderHomeAssistantAPIConfigSchema]],
] = {
    EnergyLoadHistoryProviderHomeAssistantAPIConfig: EnergyLoadHistoryProviderHomeAssistantAPIConfigSchema,
}


class HomeLoadPowerPointSchema(BaseModel):
    """Schema for HomeLoadPowerPoint value object."""

    timestamp: datetime = Field(..., description="Measurement timestamp")
    power: float = Field(..., description="Power in watts")

    @classmethod
    def from_model(cls, point: HomeLoadPowerPoint) -> "HomeLoadPowerPointSchema":
        return cls(
            timestamp=cast(datetime, point.timestamp),
            power=float(point.power),
        )


class LoadConsumptionModelSchema(BaseModel):
    """Schema for LoadConsumptionModel entity (without serialized model bytes)."""

    id: str = Field(..., description="Model unique identifier")
    device_id: Optional[str] = Field(default=None, description="Device this model was trained for")
    adapter_type: EnergyLoadForecastProviderAdapter = Field(..., description="ML adapter type")
    trained_at: Optional[datetime] = Field(default=None, description="Training timestamp")
    mae: Optional[float] = Field(default=None, description="Mean absolute error on holdout")
    rmse: Optional[float] = Field(default=None, description="Root mean squared error on holdout")
    samples_used: int = Field(default=0, description="Number of training samples")
    is_active: bool = Field(default=False, description="Whether the model is currently active")

    @classmethod
    def from_model(cls, model: LoadConsumptionModel) -> "LoadConsumptionModelSchema":
        return cls(
            id=str(model.id),
            device_id=str(model.device_id) if model.device_id else None,
            adapter_type=model.adapter_type,
            trained_at=model.trained_at,
            mae=model.mae,
            rmse=model.rmse,
            samples_used=model.samples_used,
            is_active=model.is_active,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
