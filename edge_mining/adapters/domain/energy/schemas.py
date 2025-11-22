"""Validation schemas for energy domain."""

import uuid
from typing import Dict, Optional, Union, cast

from pydantic import BaseModel, Field, field_serializer, field_validator

from edge_mining.domain.common import EntityId, WattHours, Watts
from edge_mining.domain.energy.common import EnergyMonitorAdapter, EnergySourceType
from edge_mining.domain.energy.entities import EnergyMonitor, EnergySource
from edge_mining.domain.energy.value_objects import Battery, Grid
from edge_mining.shared.adapter_configs.energy import EnergyMonitorDummySolarConfig, EnergyMonitorHomeAssistantConfig
from edge_mining.shared.adapter_maps.energy import ENERGY_MONITOR_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import EnergyMonitorConfig


class BatterySchema(BaseModel):
    """Schema for Battery value object."""

    nominal_capacity: float = Field(..., ge=0, description="Battery nominal capacity in Wh")

    @field_validator("nominal_capacity")
    @classmethod
    def validate_nominal_capacity(cls, v: float) -> float:
        """Validate nominal capacity is positive."""
        if v < 0:
            raise ValueError("Nominal capacity must be zero or positive")
        return v

    def to_model(self) -> Battery:
        """Convert BatterySchema to Battery domain value object."""
        return Battery(nominal_capacity=WattHours(self.nominal_capacity))


class GridSchema(BaseModel):
    """Schema for Grid value object."""

    contracted_power: float = Field(..., ge=0, description="Grid contracted power in Watts")

    @field_validator("contracted_power")
    @classmethod
    def validate_contracted_power(cls, v: float) -> float:
        """Validate contracted power is positive."""
        if v < 0:
            raise ValueError("Contracted power must be zero or positive")
        return v

    def to_model(self) -> Grid:
        """Convert GridSchema to Grid domain value object."""
        return Grid(contracted_power=Watts(self.contracted_power))


class EnergySourceSchema(BaseModel):
    """Schema for EnergySource entity with complete validation."""

    id: str = Field(..., description="Unique identifier for the energy source")
    name: str = Field(default="", description="Energy source name")
    type: EnergySourceType = Field(default=EnergySourceType.SOLAR, description="Type of energy source")
    nominal_power_max: Optional[float] = Field(default=None, ge=0, description="Maximum nominal power in Watts")
    storage: Optional[BatterySchema] = Field(default=None, description="Battery storage configuration")
    grid: Optional[GridSchema] = Field(default=None, description="Grid connection configuration")
    external_source: Optional[float] = Field(default=None, ge=0, description="External source power in Watts")
    energy_monitor_id: Optional[str] = Field(default=None, description="ID of the associated energy monitor")
    forecast_provider_id: Optional[str] = Field(default=None, description="ID of the associated forecast provider")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that the id is a valid EntityId."""
        try:
            EntityId(uuid.UUID(v))
        except ValueError as e:
            raise ValueError(f"Invalid energy source id: {e}") from e
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate energy source name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> EnergySourceType:
        """Validate that type is a recognized EnergySourceType."""
        adapter_values = [adapter.value for adapter in EnergySourceType]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return EnergySourceType(v)

    @field_validator("energy_monitor_id")
    @classmethod
    def validate_energy_monitor_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate energy monitor ID."""
        if v is not None:
            try:
                EntityId(uuid.UUID(v))
            except ValueError as e:
                raise ValueError(f"Invalid energy monitor id: {e}") from e
        return v

    @field_validator("forecast_provider_id")
    @classmethod
    def validate_forecast_provider_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate forecast provider ID."""
        if v is not None:
            try:
                EntityId(uuid.UUID(v))
            except ValueError as e:
                raise ValueError(f"Invalid forecast provider id: {e}") from e
        return v

    @field_validator("nominal_power_max")
    @classmethod
    def validate_nominal_power_max(cls, v: Optional[float]) -> Optional[float]:
        """Validate nominal power max is positive."""
        if v is not None and v < 0:
            raise ValueError("Nominal power max must be zero or positive")
        return v

    @field_validator("external_source")
    @classmethod
    def validate_external_source(cls, v: Optional[float]) -> Optional[float]:
        """Validate external source power is positive."""
        if v is not None and v < 0:
            raise ValueError("External source power must be zero or positive")
        return v

    @classmethod
    def from_model(cls, energy_source: EnergySource) -> "EnergySourceSchema":
        """Create EnergySourceSchema from an EnergySource domain entity."""
        return cls(
            id=str(energy_source.id),
            name=energy_source.name,
            type=energy_source.type,
            nominal_power_max=float(energy_source.nominal_power_max) if energy_source.nominal_power_max else None,
            storage=(
                BatterySchema(nominal_capacity=float(energy_source.storage.nominal_capacity))
                if energy_source.storage
                else None
            ),
            grid=(
                GridSchema(contracted_power=float(energy_source.grid.contracted_power)) if energy_source.grid else None
            ),
            external_source=float(energy_source.external_source) if energy_source.external_source else None,
            energy_monitor_id=str(energy_source.energy_monitor_id) if energy_source.energy_monitor_id else None,
            forecast_provider_id=(
                str(energy_source.forecast_provider_id) if energy_source.forecast_provider_id else None
            ),
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize EntityId to string."""
        return str(value)

    @field_serializer("energy_monitor_id")
    def serialize_energy_monitor_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize energy monitor ID to string."""
        return str(value) if value else None

    @field_serializer("forecast_provider_id")
    def serialize_forecast_provider_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize forecast provider ID to string."""
        return str(value) if value else None

    def to_model(self) -> EnergySource:
        """Convert EnergySourceSchema back to EnergySource domain model instance."""
        return EnergySource(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            type=self.type,
            nominal_power_max=Watts(self.nominal_power_max) if self.nominal_power_max is not None else None,
            storage=self.storage.to_model() if self.storage else None,
            grid=self.grid.to_model() if self.grid else None,
            external_source=Watts(self.external_source) if self.external_source is not None else None,
            energy_monitor_id=EntityId(uuid.UUID(self.energy_monitor_id)) if self.energy_monitor_id else None,
            forecast_provider_id=EntityId(uuid.UUID(self.forecast_provider_id)) if self.forecast_provider_id else None,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            uuid.UUID: str,
            EnergySourceType: lambda v: v.value,
        }


class EnergySourceCreateSchema(BaseModel):
    """Schema for creating a new energy source."""

    name: str = Field(default="", description="Energy source name")
    type: EnergySourceType = Field(default=EnergySourceType.SOLAR, description="Type of energy source")
    nominal_power_max: Optional[float] = Field(default=None, ge=0, description="Maximum nominal power in Watts")
    storage: Optional[BatterySchema] = Field(default=None, description="Battery storage configuration")
    grid: Optional[GridSchema] = Field(default=None, description="Grid connection configuration")
    external_source: Optional[float] = Field(default=None, ge=0, description="External source power in Watts")
    energy_monitor_id: Optional[str] = Field(default=None, description="ID of the associated energy monitor")
    forecast_provider_id: Optional[str] = Field(default=None, description="ID of the associated forecast provider")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate energy source name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> EnergySourceType:
        """Validate that type is a recognized EnergySourceType."""
        adapter_values = [adapter.value for adapter in EnergySourceType]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return EnergySourceType(v)

    @field_validator("energy_monitor_id")
    @classmethod
    def validate_energy_monitor_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate energy monitor ID."""
        if v is not None:
            try:
                EntityId(uuid.UUID(v))
            except ValueError as e:
                raise ValueError(f"Invalid energy monitor id: {e}") from e
        return v

    @field_validator("forecast_provider_id")
    @classmethod
    def validate_forecast_provider_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate forecast provider ID."""
        if v is not None:
            try:
                EntityId(uuid.UUID(v))
            except ValueError as e:
                raise ValueError(f"Invalid forecast provider id: {e}") from e
        return v

    @field_validator("nominal_power_max")
    @classmethod
    def validate_nominal_power_max(cls, v: Optional[float]) -> Optional[float]:
        """Validate nominal power max is positive."""
        if v is not None and v < 0:
            raise ValueError("Nominal power max must be zero or positive")
        return v

    @field_validator("external_source")
    @classmethod
    def validate_external_source(cls, v: Optional[float]) -> Optional[float]:
        """Validate external source power is positive."""
        if v is not None and v < 0:
            raise ValueError("External source power must be zero or positive")
        return v

    def to_model(self) -> EnergySource:
        """Convert EnergySourceCreateSchema to an EnergySource domain model instance."""
        return EnergySource(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            type=self.type,
            nominal_power_max=Watts(self.nominal_power_max) if self.nominal_power_max is not None else None,
            storage=self.storage.to_model() if self.storage else None,
            grid=self.grid.to_model() if self.grid else None,
            external_source=Watts(self.external_source) if self.external_source is not None else None,
            energy_monitor_id=EntityId(uuid.UUID(self.energy_monitor_id)) if self.energy_monitor_id else None,
            forecast_provider_id=EntityId(uuid.UUID(self.forecast_provider_id)) if self.forecast_provider_id else None,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            uuid.UUID: str,
            EnergySourceType: lambda v: v.value,
        }


class EnergySourceUpdateSchema(BaseModel):
    """Schema for updating an existing energy source."""

    name: str = Field(default="", description="Energy source name")
    type: EnergySourceType = Field(default=EnergySourceType.SOLAR, description="Type of energy source")
    nominal_power_max: Optional[float] = Field(default=None, ge=0, description="Maximum nominal power in Watts")
    storage: Optional[BatterySchema] = Field(default=None, description="Battery storage configuration")
    grid: Optional[GridSchema] = Field(default=None, description="Grid connection configuration")
    external_source: Optional[float] = Field(default=None, ge=0, description="External source power in Watts")
    energy_monitor_id: Optional[str] = Field(default=None, description="ID of the associated energy monitor")
    forecast_provider_id: Optional[str] = Field(default=None, description="ID of the associated forecast provider")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate energy source name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("energy_monitor_id")
    @classmethod
    def validate_energy_monitor_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate energy monitor ID."""
        if v is not None:
            try:
                EntityId(uuid.UUID(v))
            except ValueError as e:
                raise ValueError(f"Invalid energy monitor id: {e}") from e
        return v

    @field_validator("forecast_provider_id")
    @classmethod
    def validate_forecast_provider_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate forecast provider ID."""
        if v is not None:
            try:
                EntityId(uuid.UUID(v))
            except ValueError as e:
                raise ValueError(f"Invalid forecast provider id: {e}") from e
        return v

    @field_validator("nominal_power_max")
    @classmethod
    def validate_nominal_power_max(cls, v: Optional[float]) -> Optional[float]:
        """Validate nominal power max is positive."""
        if v is not None and v < 0:
            raise ValueError("Nominal power max must be zero or positive")
        return v

    @field_validator("external_source")
    @classmethod
    def validate_external_source(cls, v: Optional[float]) -> Optional[float]:
        """Validate external source power is positive."""
        if v is not None and v < 0:
            raise ValueError("External source power must be zero or positive")
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            uuid.UUID: str,
            EnergySourceType: lambda v: v.value,
        }


class EnergyMonitorSchema(BaseModel):
    """Schema for EnergyMonitor entity with complete validation."""

    id: str = Field(..., description="Unique identifier for the energy monitor")
    name: str = Field(default="", description="Energy monitor name")
    adapter_type: EnergyMonitorAdapter = Field(
        default=EnergyMonitorAdapter.DUMMY_SOLAR, description="Type of energy monitor adapter"
    )
    config: Optional[dict] = Field(default=None, description="Energy monitor configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that the id is a valid EntityId."""
        try:
            EntityId(uuid.UUID(v))
        except ValueError as e:
            raise ValueError(f"Invalid energy monitor id: {e}") from e
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate energy monitor name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> EnergyMonitorAdapter:
        """Validate that adapter_type is a recognized EnergyMonitorAdapter."""
        adapter_values = [adapter.value for adapter in EnergyMonitorAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return EnergyMonitorAdapter(v)

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate external service ID."""
        if v is not None:
            try:
                EntityId(uuid.UUID(v))
            except ValueError as e:
                raise ValueError(f"Invalid external service id: {e}") from e
        return v

    @classmethod
    def from_model(cls, energy_monitor: EnergyMonitor) -> "EnergyMonitorSchema":
        """Create EnergyMonitorSchema from an EnergyMonitor domain entity."""
        return cls(
            id=str(energy_monitor.id),
            name=energy_monitor.name,
            adapter_type=energy_monitor.adapter_type,
            config=energy_monitor.config.to_dict() if energy_monitor.config else None,
            external_service_id=str(energy_monitor.external_service_id) if energy_monitor.external_service_id else None,
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize EntityId to string."""
        return str(value)

    @field_serializer("external_service_id")
    def serialize_external_service_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize external service ID to string."""
        return str(value) if value else None

    def to_model(self) -> EnergyMonitor:
        """Convert EnergyMonitorSchema to EnergyMonitor domain entity."""
        configuration: Optional[EnergyMonitorConfig] = None
        if self.config:
            config_class = ENERGY_MONITOR_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(EnergyMonitorConfig, config_class.from_dict(self.config))

        return EnergyMonitor(
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
            EnergyMonitorAdapter: lambda v: v.value,
        }


class EnergyMonitorCreateSchema(BaseModel):
    """Schema for creating a new energy monitor."""

    name: str = Field(default="", description="Energy monitor name")
    adapter_type: EnergyMonitorAdapter = Field(
        default=EnergyMonitorAdapter.DUMMY_SOLAR, description="Type of energy monitor adapter"
    )
    config: Optional[dict] = Field(default=None, description="Energy monitor configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate energy monitor name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> EnergyMonitorAdapter:
        """Validate that adapter_type is a recognized EnergyMonitorAdapter."""
        adapter_values = [adapter.value for adapter in EnergyMonitorAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return EnergyMonitorAdapter(v)

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate external service ID."""
        if v is not None:
            try:
                EntityId(uuid.UUID(v))
            except ValueError as e:
                raise ValueError(f"Invalid external service id: {e}") from e
        return v

    def to_model(self) -> EnergyMonitor:
        """Convert EnergyMonitorCreateSchema to EnergyMonitor domain entity."""
        configuration: Optional[EnergyMonitorConfig] = None
        if self.config:
            config_class = ENERGY_MONITOR_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(EnergyMonitorConfig, config_class.from_dict(self.config))

        return EnergyMonitor(
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
            EnergyMonitorAdapter: lambda v: v.value,
        }


class EnergyMonitorUpdateSchema(BaseModel):
    """Schema for updating an existing energy monitor."""

    name: str = Field(default="", description="Energy monitor name")
    config: Optional[dict] = Field(default=None, description="Energy monitor configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate energy monitor name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate external service ID."""
        if v is not None:
            try:
                EntityId(uuid.UUID(v))
            except ValueError as e:
                raise ValueError(f"Invalid external service id: {e}") from e
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


class EnergyMonitorDummySolarConfigSchema(BaseModel):
    """Schema for Dummy Solar EnergyMonitorConfig."""

    max_consumption_power: float = Field(default=3200.0, description="Maximum consumption power in Watts")

    @field_validator("max_consumption_power")
    @classmethod
    def validate_max_consumption_power(cls, v: float) -> float:
        """Validate max consumption power is positive."""
        if v < 0:
            raise ValueError("Max consumption power must be zero or positive")
        return v

    def to_model(self) -> EnergyMonitorDummySolarConfig:
        """Convert schema to EnergyMonitorDummySolarConfig domain entity."""
        return EnergyMonitorDummySolarConfig(
            max_consumption_power=Watts(self.max_consumption_power),
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


class EnergyMonitorHomeAssistantConfigSchema(BaseModel):
    """Schema for Home Assistant EnergyMonitorConfig."""

    entity_production: str = Field(..., description="Home Assistant production entity")
    entity_consumption: str = Field(..., description="Home Assistant consumption entity")
    entity_grid: str = Field(default="", description="Home Assistant grid entity")
    entity_battery_soc: str = Field(default="", description="Home Assistant battery SOC entity")
    entity_battery_power: str = Field(default="", description="Home Assistant battery power entity")
    entity_battery_remaining_capacity: str = Field(
        default="", description="Home Assistant battery remaining capacity entity"
    )
    unit_production: str = Field(default="W", description="Production unit")
    unit_consumption: str = Field(default="W", description="Consumption unit")
    unit_grid: str = Field(default="W", description="Grid unit")
    unit_battery_power: str = Field(default="W", description="Battery power unit")
    unit_battery_remaining_capacity: str = Field(default="Wh", description="Battery remaining capacity unit")
    grid_positive_export: bool = Field(default=False, description="Grid positive export direction")
    battery_positive_charge: bool = Field(default=True, description="Battery positive charge direction")

    @field_validator("entity_production", "entity_consumption")
    @classmethod
    def validate_required_entities(cls, v: str) -> str:
        """Validate that required entities are not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Required entity must not be empty")
        return v

    def to_model(self) -> EnergyMonitorHomeAssistantConfig:
        """Convert schema to EnergyMonitorHomeAssistantConfig domain entity."""
        return EnergyMonitorHomeAssistantConfig(
            entity_production=self.entity_production,
            entity_consumption=self.entity_consumption,
            entity_grid=self.entity_grid,
            entity_battery_soc=self.entity_battery_soc,
            entity_battery_power=self.entity_battery_power,
            entity_battery_remaining_capacity=self.entity_battery_remaining_capacity,
            unit_production=self.unit_production,
            unit_consumption=self.unit_consumption,
            unit_grid=self.unit_grid,
            unit_battery_power=self.unit_battery_power,
            unit_battery_remaining_capacity=self.unit_battery_remaining_capacity,
            grid_positive_export=self.grid_positive_export,
            battery_positive_charge=self.battery_positive_charge,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


ENERGY_MONITOR_CONFIG_SCHEMA_MAP: Dict[
    type[EnergyMonitorConfig],
    Union[type[EnergyMonitorDummySolarConfigSchema], type[EnergyMonitorHomeAssistantConfigSchema]],
] = {
    EnergyMonitorDummySolarConfig: EnergyMonitorDummySolarConfigSchema,
    EnergyMonitorHomeAssistantConfig: EnergyMonitorHomeAssistantConfigSchema,
}
