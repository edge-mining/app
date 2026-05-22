"""Validation schemas for climate domain."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, cast

from pydantic import BaseModel, Field, field_serializer, field_validator

from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateMonitor, ClimateZone
from edge_mining.domain.climate.value_objects import ClimateStateSnapshot, ClimateZoneReading
from edge_mining.domain.common import EntityId
from edge_mining.shared.adapter_configs.climate import ClimateMonitorHomeAssistantConfig
from edge_mining.shared.adapter_maps.climate import CLIMATE_MONITOR_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import ClimateMonitorConfig


# --- ClimateZone Schemas ---


class ClimateZoneSchema(BaseModel):
    """Schema for ClimateZone entity."""

    id: str = Field(...)
    name: str = Field(default="")
    area_sqm: Optional[float] = Field(default=None, ge=0)
    climate_monitor_id: Optional[str] = Field(default=None)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        try:
            EntityId(uuid.UUID(v))
        except ValueError as e:
            raise ValueError(f"Invalid climate zone id: {e}") from e
        return v

    @classmethod
    def from_model(cls, climate_zone: ClimateZone) -> "ClimateZoneSchema":
        return cls(
            id=str(climate_zone.id),
            name=climate_zone.name,
            area_sqm=climate_zone.area_sqm,
            climate_monitor_id=str(climate_zone.climate_monitor_id) if climate_zone.climate_monitor_id else None,
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        return str(value)

    @field_serializer("climate_monitor_id")
    def serialize_climate_monitor_id(self, value: Optional[str]) -> Optional[str]:
        return str(value) if value else None

    def to_model(self) -> ClimateZone:
        return ClimateZone(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            area_sqm=self.area_sqm,
            climate_monitor_id=EntityId(uuid.UUID(self.climate_monitor_id)) if self.climate_monitor_id else None,
        )

    class Config:
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {uuid.UUID: str}


class ClimateZoneCreateSchema(BaseModel):
    """Schema for creating a new climate zone."""

    name: str = Field(default="")
    area_sqm: Optional[float] = Field(default=None, ge=0)
    climate_monitor_id: Optional[str] = Field(default=None)

    def to_model(self) -> ClimateZone:
        return ClimateZone(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            area_sqm=self.area_sqm,
            climate_monitor_id=EntityId(uuid.UUID(self.climate_monitor_id)) if self.climate_monitor_id else None,
        )

    class Config:
        use_enum_values = True
        validate_assignment = True


class ClimateZoneUpdateSchema(BaseModel):
    """Schema for updating an existing climate zone."""

    name: Optional[str] = Field(default=None)
    area_sqm: Optional[float] = Field(default=None, ge=0)

    class Config:
        use_enum_values = True
        validate_assignment = True


# --- ClimateMonitor Schemas ---


class ClimateMonitorSchema(BaseModel):
    """Schema for ClimateMonitor entity."""

    id: str = Field(...)
    name: str = Field(default="")
    adapter_type: ClimateMonitorAdapter = Field(default=ClimateMonitorAdapter.HOME_ASSISTANT_API)
    config: Optional[dict] = Field(default=None)
    external_service_id: Optional[str] = Field(default=None)

    @classmethod
    def from_model(cls, climate_monitor: ClimateMonitor) -> "ClimateMonitorSchema":
        return cls(
            id=str(climate_monitor.id),
            name=climate_monitor.name,
            adapter_type=climate_monitor.adapter_type,
            config=climate_monitor.config.to_dict() if climate_monitor.config else None,
            external_service_id=(
                str(climate_monitor.external_service_id) if climate_monitor.external_service_id else None
            ),
        )

    def to_model(self) -> ClimateMonitor:
        configuration: Optional[ClimateMonitorConfig] = None
        if self.config:
            config_class = CLIMATE_MONITOR_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(ClimateMonitorConfig, config_class.from_dict(self.config))
        return ClimateMonitor(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            adapter_type=self.adapter_type,
            config=configuration,
            external_service_id=(EntityId(uuid.UUID(self.external_service_id)) if self.external_service_id else None),
        )

    class Config:
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {uuid.UUID: str, ClimateMonitorAdapter: lambda v: v.value}


class ClimateMonitorCreateSchema(BaseModel):
    """Schema for creating a new climate monitor."""

    name: str = Field(default="")
    adapter_type: ClimateMonitorAdapter = Field(default=ClimateMonitorAdapter.HOME_ASSISTANT_API)
    config: Optional[dict] = Field(default=None)
    external_service_id: Optional[str] = Field(default=None)

    def to_model(self) -> ClimateMonitor:
        configuration: Optional[ClimateMonitorConfig] = None
        if self.config:
            config_class = CLIMATE_MONITOR_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(ClimateMonitorConfig, config_class.from_dict(self.config))
        else:
            if self.adapter_type:
                config_class = CLIMATE_MONITOR_CONFIG_TYPE_MAP.get(self.adapter_type, None)
                if config_class:
                    configuration = cast(ClimateMonitorConfig, config_class())
        return ClimateMonitor(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            adapter_type=self.adapter_type,
            config=configuration,
            external_service_id=(EntityId(uuid.UUID(self.external_service_id)) if self.external_service_id else None),
        )

    class Config:
        use_enum_values = True
        validate_assignment = True
        json_encoders = {uuid.UUID: str, ClimateMonitorAdapter: lambda v: v.value}


class ClimateMonitorUpdateSchema(BaseModel):
    """Schema for updating an existing climate monitor."""

    name: Optional[str] = Field(default=None)
    config: Optional[dict] = Field(default=None)
    external_service_id: Optional[str] = Field(default=None)

    class Config:
        use_enum_values = True
        validate_assignment = True


# --- Config Schemas ---


class ClimateMonitorHomeAssistantConfigSchema(BaseModel):
    """Schema for Home Assistant climate monitor configuration."""

    entity_temperature: str = Field(..., description="HA entity ID for temperature sensor")
    entity_humidity: str = Field(default="", description="HA entity ID for humidity sensor (optional)")
    unit_temperature: str = Field(default="°C", description="Temperature unit (°C, °F, K)")

    def to_model(self) -> ClimateMonitorHomeAssistantConfig:
        return ClimateMonitorHomeAssistantConfig(
            entity_temperature=self.entity_temperature,
            entity_humidity=self.entity_humidity,
            unit_temperature=self.unit_temperature,
        )


CLIMATE_MONITOR_CONFIG_SCHEMA_MAP: Dict[
    type[ClimateMonitorConfig],
    Union[type[ClimateMonitorHomeAssistantConfigSchema]],
] = {
    ClimateMonitorHomeAssistantConfig: ClimateMonitorHomeAssistantConfigSchema,
}


# --- Reading Schemas ---


class ClimateZoneReadingSchema(BaseModel):
    """Schema for ClimateZoneReading value object."""

    zone_id: Optional[str] = Field(default=None)
    zone_name: str = Field(default="")
    temperature_celsius: float = Field(...)
    humidity: Optional[float] = Field(default=None, ge=0, le=100)
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_model(cls, reading: ClimateZoneReading) -> "ClimateZoneReadingSchema":
        return cls(
            zone_id=str(reading.zone_id) if reading.zone_id else None,
            zone_name=reading.zone_name,
            temperature_celsius=reading.temperature_celsius,
            humidity=reading.humidity,
            timestamp=reading.timestamp,
        )


class ClimateStateSnapshotSchema(BaseModel):
    """Schema for ClimateStateSnapshot value object."""

    per_zone: List[ClimateZoneReadingSchema] = Field(default_factory=list)
    avg_temperature: Optional[float] = Field(default=None)
    min_temperature: Optional[float] = Field(default=None)
    max_temperature: Optional[float] = Field(default=None)

    @classmethod
    def from_model(cls, snapshot: ClimateStateSnapshot) -> "ClimateStateSnapshotSchema":
        return cls(
            per_zone=[ClimateZoneReadingSchema.from_model(r) for r in snapshot.per_zone],
            avg_temperature=snapshot.avg_temperature,
            min_temperature=snapshot.min_temperature,
            max_temperature=snapshot.max_temperature,
        )
