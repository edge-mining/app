"""Validation schemas for home load domain."""

import uuid
from datetime import datetime
from typing import Dict, Optional, Union, cast

from pydantic import BaseModel, Field, field_serializer, field_validator

from edge_mining.domain.common import EntityId, Timestamp, Watts
from edge_mining.domain.home_load.common import HomeForecastProviderAdapter
from edge_mining.domain.home_load.entities import HomeForecastProvider
from edge_mining.domain.home_load.value_objects import ConsumptionForecast
from edge_mining.shared.adapter_configs.home_load import HomeForecastProviderDummyConfig
from edge_mining.shared.adapter_maps.home_load import HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import HomeForecastProviderConfig


class ConsumptionForecastSchema(BaseModel):
    """Schema for ConsumptionForecast value object."""

    predicted_watts: Dict[str, float] = Field(
        default_factory=dict, description="Predicted consumption watts by timestamp (ISO format keys)"
    )
    generated_at: datetime = Field(default_factory=datetime.now, description="When the forecast was generated")

    @classmethod
    def from_model(cls, forecast: ConsumptionForecast) -> "ConsumptionForecastSchema":
        """Create schema from ConsumptionForecast value object."""
        # Convert Timestamp keys to ISO string and Watts values to float
        predicted_watts_dict = {ts.isoformat(): float(watts) for ts, watts in forecast.predicted_watts.items()}
        return cls(
            predicted_watts=predicted_watts_dict,
            generated_at=forecast.generated_at,
        )

    def to_model(self) -> ConsumptionForecast:
        """Convert schema to ConsumptionForecast value object."""
        # Convert ISO string keys back to Timestamp and float values to Watts
        predicted_watts_dict = {
            Timestamp(datetime.fromisoformat(ts)): Watts(watts) for ts, watts in self.predicted_watts.items()
        }
        return ConsumptionForecast(
            predicted_watts=predicted_watts_dict,
            generated_at=Timestamp(self.generated_at),
        )


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
        except ValueError as exc:
            raise ValueError("id must be a valid UUID string") from exc
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate home forecast provider name."""
        v = v.strip()
        if not v:
            v = ""
        return v

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
    def from_model(cls, home_forecast_provider: HomeForecastProvider) -> "HomeForecastProviderSchema":
        """Create HomeForecastProviderSchema from a HomeForecastProvider domain model instance."""
        return cls(
            id=str(home_forecast_provider.id),
            name=home_forecast_provider.name,
            adapter_type=home_forecast_provider.adapter_type,
            config=home_forecast_provider.config.to_dict() if home_forecast_provider.config else {},
            external_service_id=(
                str(home_forecast_provider.external_service_id) if home_forecast_provider.external_service_id else None
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

    def to_model(self) -> HomeForecastProvider:
        """Convert HomeForecastProviderSchema to HomeForecastProvider domain model instance."""
        configuration: Optional[HomeForecastProviderConfig] = None
        if self.config:
            config_class = HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(HomeForecastProviderConfig, config_class.from_dict(self.config))

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
        """Validate home forecast provider name."""
        v = v.strip()
        if not v:
            v = ""
        return v

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
        """Convert HomeForecastProviderCreateSchema to a HomeForecastProvider domain model instance."""
        configuration: Optional[HomeForecastProviderConfig] = None
        if self.config:
            config_class = HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(HomeForecastProviderConfig, config_class.from_dict(self.config))

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
        """Validate home forecast provider name."""
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


class HomeForecastProviderDummyConfigSchema(BaseModel):
    """Schema for Dummy Home Forecast Provider Config."""

    load_power_max: float = Field(default=500.0, ge=0, description="Maximum load power in Watts")

    @field_validator("load_power_max")
    @classmethod
    def validate_load_power_max(cls, v: float) -> float:
        """Validate load_power_max is non-negative."""
        if v < 0:
            raise ValueError("load_power_max must be non-negative")
        return v

    def to_model(self) -> HomeForecastProviderDummyConfig:
        """Convert schema to HomeForecastProviderDummyConfig adapter configuration model instance."""
        return HomeForecastProviderDummyConfig(
            load_power_max=self.load_power_max,
        )

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
