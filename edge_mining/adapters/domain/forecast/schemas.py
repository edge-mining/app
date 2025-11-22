"""Validation schemas for forecast domain."""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, cast

from pydantic import BaseModel, Field, field_serializer, field_validator

from edge_mining.domain.common import EntityId, Timestamp, WattHours, Watts
from edge_mining.domain.forecast.aggregate_root import Forecast
from edge_mining.domain.forecast.common import ForecastProviderAdapter
from edge_mining.domain.forecast.entities import ForecastProvider
from edge_mining.domain.forecast.value_objects import ForecastInterval, ForecastPowerPoint
from edge_mining.shared.adapter_configs.forecast import (
    ForecastProviderDummySolarConfig,
    ForecastProviderHomeAssistantConfig,
)
from edge_mining.shared.adapter_maps.forecast import FORECAST_PROVIDER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import ForecastProviderConfig


class ForecastPowerPointSchema(BaseModel):
    """Schema for ForecastPowerPoint value object."""

    timestamp: datetime = Field(..., description="Timestamp for the power prediction")
    power: float = Field(..., ge=0, description="Predicted power output in Watts")

    @field_validator("power")
    @classmethod
    def validate_power(cls, v: float) -> float:
        """Validate power is non-negative."""
        if v < 0:
            raise ValueError("power must be non-negative")
        return v

    @classmethod
    def from_model(cls, power_point: ForecastPowerPoint) -> "ForecastPowerPointSchema":
        """Create ForecastPowerPointSchema from ForecastPowerPoint value object."""
        return cls(
            timestamp=power_point.timestamp,
            power=float(power_point.power),
        )

    def to_model(self) -> ForecastPowerPoint:
        """Convert ForecastPowerPointSchema to ForecastPowerPoint value object."""
        return ForecastPowerPoint(
            timestamp=Timestamp(self.timestamp),
            power=Watts(self.power),
        )


class ForecastIntervalSchema(BaseModel):
    """Schema for ForecastInterval value object."""

    start: datetime = Field(..., description="Start timestamp of the forecast interval")
    end: datetime = Field(..., description="End timestamp of the forecast interval")
    energy: Optional[float] = Field(default=None, ge=0, description="Total energy expected in WattHours")
    energy_remaining: Optional[float] = Field(default=None, ge=0, description="Remaining energy in WattHours")
    power_points: List[ForecastPowerPointSchema] = Field(
        default_factory=list, description="Power predictions within interval"
    )

    @field_validator("energy", "energy_remaining")
    @classmethod
    def validate_energy(cls, v: Optional[float]) -> Optional[float]:
        """Validate energy values are non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("energy values must be non-negative")
        return v

    @classmethod
    def from_model(cls, interval: ForecastInterval) -> "ForecastIntervalSchema":
        """Create ForecastIntervalSchema from ForecastInterval value object."""
        return cls(
            start=interval.start,
            end=interval.end,
            energy=float(interval.energy) if interval.energy is not None else None,
            energy_remaining=float(interval.energy_remaining) if interval.energy_remaining is not None else None,
            power_points=[ForecastPowerPointSchema.from_model(pp) for pp in interval.power_points],
        )

    def to_model(self) -> ForecastInterval:
        """Convert ForecastIntervalSchema to ForecastInterval value object."""
        return ForecastInterval(
            start=Timestamp(self.start),
            end=Timestamp(self.end),
            energy=WattHours(self.energy) if self.energy is not None else None,
            energy_remaining=WattHours(self.energy_remaining) if self.energy_remaining is not None else None,
            power_points=[pp.to_model() for pp in self.power_points],
        )


class ForecastSchema(BaseModel):
    """Schema for Forecast aggregate root."""

    id: str = Field(..., description="Unique identifier for the forecast")
    timestamp: datetime = Field(..., description="When this forecast was generated or last updated")
    intervals: List[ForecastIntervalSchema] = Field(default_factory=list, description="Forecast intervals")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that id is a valid UUID string."""
        try:
            uuid.UUID(v)
        except ValueError as exc:
            raise ValueError("id must be a valid UUID string") from exc
        return v

    @classmethod
    def from_model(cls, forecast: Forecast) -> "ForecastSchema":
        """Create ForecastSchema from Forecast aggregate root."""
        return cls(
            id=str(forecast.id),
            timestamp=forecast.timestamp,
            intervals=[ForecastIntervalSchema.from_model(interval) for interval in forecast.intervals],
        )

    def to_model(self) -> Forecast:
        """Convert ForecastSchema to Forecast aggregate root."""
        return Forecast(
            id=EntityId(uuid.UUID(self.id)),
            timestamp=Timestamp(self.timestamp),
            intervals=[interval.to_model() for interval in self.intervals],
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return str(value)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
            timedelta: lambda v: v.total_seconds(),
        }


class ForecastProviderSchema(BaseModel):
    """Schema for ForecastProvider entity with complete validation."""

    id: str = Field(..., description="Unique identifier for the forecast provider")
    name: str = Field(default="", description="Forecast provider name")
    adapter_type: ForecastProviderAdapter = Field(
        default=ForecastProviderAdapter.DUMMY_SOLAR, description="Type of forecast provider adapter"
    )
    config: dict = Field(default={}, description="Forecast provider configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that id is a valid UUID string."""
        try:
            uuid.UUID(v)
        except ValueError as exc:
            raise ValueError("id must be a valid UUID string") from exc
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate forecast provider name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> ForecastProviderAdapter:
        """Validate that adapter_type is a recognized ForecastProviderAdapter."""
        adapter_values = [adapter.value for adapter in ForecastProviderAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return ForecastProviderAdapter(v)

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
    def from_model(cls, forecast_provider: ForecastProvider) -> "ForecastProviderSchema":
        """Create ForecastProviderSchema from a ForecastProvider domain model instance."""
        return cls(
            id=str(forecast_provider.id),
            name=forecast_provider.name,
            adapter_type=forecast_provider.adapter_type,
            config=forecast_provider.config.to_dict() if forecast_provider.config else {},
            external_service_id=(
                str(forecast_provider.external_service_id) if forecast_provider.external_service_id else None
            ),
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return str(value)

    @field_serializer("external_service_id")
    def serialize_external_service_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize external_service_id field."""
        return str(value) if value is not None else None

    def to_model(self) -> ForecastProvider:
        """Convert ForecastProviderSchema to ForecastProvider domain model instance."""
        configuration: Optional[ForecastProviderConfig] = None
        if self.config:
            config_class = FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(ForecastProviderConfig, config_class.from_dict(self.config))

        return ForecastProvider(
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
            ForecastProviderAdapter: lambda v: v.value,
        }


class ForecastProviderCreateSchema(BaseModel):
    """Schema for creating a new forecast provider."""

    name: str = Field(default="", description="Forecast provider name")
    adapter_type: ForecastProviderAdapter = Field(
        default=ForecastProviderAdapter.DUMMY_SOLAR, description="Type of forecast provider adapter"
    )
    config: Optional[dict] = Field(default=None, description="Forecast provider configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate forecast provider name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> ForecastProviderAdapter:
        """Validate that adapter_type is a recognized ForecastProviderAdapter."""
        adapter_values = [adapter.value for adapter in ForecastProviderAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return ForecastProviderAdapter(v)

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

    def to_model(self) -> ForecastProvider:
        """Convert ForecastProviderCreateSchema to a ForecastProvider domain model instance."""
        configuration: Optional[ForecastProviderConfig] = None
        if self.config:
            config_class = FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(ForecastProviderConfig, config_class.from_dict(self.config))

        return ForecastProvider(
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
            ForecastProviderAdapter: lambda v: v.value,
        }


class ForecastProviderUpdateSchema(BaseModel):
    """Schema for updating an existing forecast provider."""

    name: str = Field(default="", description="Forecast provider name")
    config: Optional[dict] = Field(default=None, description="Forecast provider configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate forecast provider name."""
        v = v.strip()
        if not v:
            v = ""
        return v

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
        json_encoders = {
            uuid.UUID: str,
        }


class ForecastProviderDummySolarConfigSchema(BaseModel):
    """Schema for Dummy Solar ForecastProviderConfig."""

    latitude: float = Field(default=41.90, description="Latitude for solar calculations")
    longitude: float = Field(default=12.49, description="Longitude for solar calculations")
    capacity_kwp: float = Field(default=0.0, ge=0, description="Solar panel capacity in kWp")
    efficiency_percent: float = Field(default=80.0, ge=0, le=100, description="Solar panel efficiency percentage")
    production_start_hour: int = Field(default=6, ge=0, le=23, description="Hour when production starts (0-23)")
    production_end_hour: int = Field(default=20, ge=0, le=23, description="Hour when production ends (0-23)")

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Validate latitude is within valid range."""
        if not -90 <= v <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Validate longitude is within valid range."""
        if not -180 <= v <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return v

    @field_validator("capacity_kwp")
    @classmethod
    def validate_capacity_kwp(cls, v: float) -> float:
        """Validate capacity is non-negative."""
        if v < 0:
            raise ValueError("capacity_kwp must be non-negative")
        return v

    @field_validator("efficiency_percent")
    @classmethod
    def validate_efficiency_percent(cls, v: float) -> float:
        """Validate efficiency is between 0 and 100."""
        if not 0 <= v <= 100:
            raise ValueError("efficiency_percent must be between 0 and 100")
        return v

    @field_validator("production_start_hour", "production_end_hour")
    @classmethod
    def validate_hour(cls, v: int) -> int:
        """Validate hour is between 0 and 23."""
        if not 0 <= v <= 23:
            raise ValueError("hour must be between 0 and 23")
        return v

    def to_model(self) -> ForecastProviderDummySolarConfig:
        """Convert schema to ForecastProviderDummySolarConfig adapter configuration model instance."""
        return ForecastProviderDummySolarConfig(
            latitude=self.latitude,
            longitude=self.longitude,
            capacity_kwp=self.capacity_kwp,
            efficiency_percent=self.efficiency_percent,
            production_start_hour=self.production_start_hour,
            production_end_hour=self.production_end_hour,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


class ForecastProviderHomeAssistantConfigSchema(BaseModel):
    """Schema for Home Assistant ForecastProviderConfig."""

    entity_forecast_power_actual_h: str = Field(
        default="", description="Home Assistant power forecast actual hour entity"
    )
    entity_forecast_power_next_1h: str = Field(default="", description="Home Assistant power forecast next 1h entity")
    entity_forecast_power_next_12h: str = Field(default="", description="Home Assistant power forecast next 12h entity")
    entity_forecast_power_next_24h: str = Field(default="", description="Home Assistant power forecast next 24h entity")
    entity_forecast_energy_actual_h: str = Field(
        default="", description="Home Assistant energy forecast actual hour entity"
    )
    entity_forecast_energy_next_1h: str = Field(default="", description="Home Assistant energy forecast next 1h entity")
    entity_forecast_energy_today: str = Field(default="", description="Home Assistant energy forecast today entity")
    entity_forecast_energy_tomorrow: str = Field(
        default="", description="Home Assistant energy forecast tomorrow entity"
    )
    entity_forecast_energy_remaining_today: str = Field(
        default="", description="Home Assistant energy forecast remaining today entity"
    )
    unit_forecast_power_actual_h: str = Field(default="W", description="Power forecast actual hour unit")
    unit_forecast_power_next_1h: str = Field(default="W", description="Power forecast next 1h unit")
    unit_forecast_power_next_12h: str = Field(default="W", description="Power forecast next 12h unit")
    unit_forecast_power_next_24h: str = Field(default="W", description="Power forecast next 24h unit")
    unit_forecast_energy_actual_h: str = Field(default="kWh", description="Energy forecast actual hour unit")
    unit_forecast_energy_next_1h: str = Field(default="kWh", description="Energy forecast next 1h unit")
    unit_forecast_energy_today: str = Field(default="kWh", description="Energy forecast today unit")
    unit_forecast_energy_tomorrow: str = Field(default="kWh", description="Energy forecast tomorrow unit")
    unit_forecast_energy_remaining_today: str = Field(default="kWh", description="Energy forecast remaining today unit")

    def to_model(self) -> ForecastProviderHomeAssistantConfig:
        """Convert schema to ForecastProviderHomeAssistantConfig adapter configuration model instance."""
        return ForecastProviderHomeAssistantConfig(
            entity_forecast_power_actual_h=self.entity_forecast_power_actual_h,
            entity_forecast_power_next_1h=self.entity_forecast_power_next_1h,
            entity_forecast_power_next_12h=self.entity_forecast_power_next_12h,
            entity_forecast_power_next_24h=self.entity_forecast_power_next_24h,
            entity_forecast_energy_actual_h=self.entity_forecast_energy_actual_h,
            entity_forecast_energy_next_1h=self.entity_forecast_energy_next_1h,
            entity_forecast_energy_today=self.entity_forecast_energy_today,
            entity_forecast_energy_tomorrow=self.entity_forecast_energy_tomorrow,
            entity_forecast_energy_remaining_today=self.entity_forecast_energy_remaining_today,
            unit_forecast_power_actual_h=self.unit_forecast_power_actual_h,
            unit_forecast_power_next_1h=self.unit_forecast_power_next_1h,
            unit_forecast_power_next_12h=self.unit_forecast_power_next_12h,
            unit_forecast_power_next_24h=self.unit_forecast_power_next_24h,
            unit_forecast_energy_actual_h=self.unit_forecast_energy_actual_h,
            unit_forecast_energy_next_1h=self.unit_forecast_energy_next_1h,
            unit_forecast_energy_today=self.unit_forecast_energy_today,
            unit_forecast_energy_tomorrow=self.unit_forecast_energy_tomorrow,
            unit_forecast_energy_remaining_today=self.unit_forecast_energy_remaining_today,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


FORECAST_PROVIDER_CONFIG_SCHEMA_MAP: Dict[
    type[ForecastProviderConfig],
    Union[type[ForecastProviderDummySolarConfigSchema], type[ForecastProviderHomeAssistantConfigSchema]],
] = {
    ForecastProviderDummySolarConfig: ForecastProviderDummySolarConfigSchema,
    ForecastProviderHomeAssistantConfig: ForecastProviderHomeAssistantConfigSchema,
}
