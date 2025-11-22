"""Validation schemas for external services."""

import uuid
from typing import Dict, Optional, Union, cast

from pydantic import BaseModel, Field, field_serializer, field_validator

# from edge_mining.adapters.domain.energy.schemas import EnergyMonitorSchema
# from edge_mining.adapters.domain.forecast.schemas import ForecastProviderSchema
# from edge_mining.adapters.domain.home_load.schemas import HomeForecastProviderSchema
# from edge_mining.adapters.domain.miner.schemas import MinerControllerSchema
# from edge_mining.adapters.domain.notification.schemas import NotifierSchema
from edge_mining.domain.common import EntityId

# from edge_mining.domain.energy.entities import EnergyMonitor
# from edge_mining.domain.forecast.entities import ForecastProvider
# from edge_mining.domain.home_load.entities import HomeForecastProvider
# from edge_mining.domain.miner.entities import MinerController
# from edge_mining.domain.notification.entities import Notifier
from edge_mining.shared.adapter_configs.external_services import ExternalServiceHomeAssistantConfig
from edge_mining.shared.adapter_maps.external_services import EXTERNAL_SERVICE_CONFIG_TYPE_MAP
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.external_services.entities import ExternalService

# from edge_mining.shared.external_services.value_objects import (
#     ExternalServiceLinkedEntities,
# )
from edge_mining.shared.interfaces.config import ExternalServiceConfig


class ExternalServiceSchema(BaseModel):
    """Schema for ExternalService entity with complete validation."""

    id: str = Field(..., description="Unique identifier for the external service")
    name: str = Field(default="", description="External service name")
    adapter_type: ExternalServiceAdapter = Field(
        default=ExternalServiceAdapter.HOME_ASSISTANT_API, description="Type of external service adapter"
    )
    config: Optional[dict] = Field(default={}, description="External service configuration")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that the id is a valid EntityId."""
        try:
            EntityId(uuid.UUID(v))
        except ValueError as e:
            raise ValueError(f"Invalid external service id: {e}") from e
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate external service name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> ExternalServiceAdapter:
        """Validate that adapter_type is a recognized ExternalServiceAdapter."""
        adapter_values = [adapter.value for adapter in ExternalServiceAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return ExternalServiceAdapter(v)

    @field_serializer("id")
    def serialize_id(self, id_value: EntityId) -> str:
        """Serialize EntityId to string."""
        return str(id_value)

    def to_model(self) -> ExternalService:
        """Convert ExternalServiceSchema to ExternalService domain entity."""
        configuration: Optional[ExternalServiceConfig] = None
        if self.config:
            config_class = EXTERNAL_SERVICE_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(ExternalServiceConfig, config_class.from_dict(self.config))

        return ExternalService(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            adapter_type=self.adapter_type,
            config=configuration,
        )

    @classmethod
    def from_model(cls, service: ExternalService) -> "ExternalServiceSchema":
        """Create ExternalServiceSchema from an ExternalService domain entity."""
        return cls(
            id=str(service.id),
            name=service.name,
            adapter_type=service.adapter_type,
            config=service.config.to_dict() if service.config else {},
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            EntityId: str,
            ExternalServiceAdapter: lambda v: v.value,
        }


class ExternalServiceCreateSchema(BaseModel):
    """Schema for creating a new external service."""

    name: str = Field(..., description="External service name")
    adapter_type: ExternalServiceAdapter = Field(
        default=ExternalServiceAdapter.HOME_ASSISTANT_API, description="Type of external service adapter"
    )
    config: Optional[dict] = Field(default=None, description="External service configuration")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate external service name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> ExternalServiceAdapter:
        """Validate that adapter_type is a recognized ExternalServiceAdapter."""
        adapter_values = [adapter.value for adapter in ExternalServiceAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return ExternalServiceAdapter(v)

    def to_model(self) -> ExternalService:
        """Convert ExternalServiceCreateSchema to ExternalService domain entity."""
        configuration: Optional[ExternalServiceConfig] = None
        if self.config:
            config_class = EXTERNAL_SERVICE_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(ExternalServiceConfig, config_class.from_dict(self.config))

        return ExternalService(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            adapter_type=self.adapter_type,
            config=configuration,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            EntityId: str,
            ExternalServiceAdapter: lambda v: v.value,
        }


class ExternalServiceUpdateSchema(BaseModel):
    """Schema for updating an existing external service."""

    name: str = Field(default="", description="External service name")
    config: Optional[dict] = Field(default=None, description="External service configuration")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate external service name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


# class ExternalServiceLinkedEntitiesSchema(BaseModel):
#     """Schema for ExternalServiceLinkedEntities value object."""

#     miner_controllers: List[MinerControllerSchema]
#     energy_monitors: List[EnergyMonitorSchema]
#     forecast_providers: List[ForecastProviderSchema]
#     home_forecast_providers: List[HomeForecastProviderSchema]
#     notifiers: List[NotifierSchema]

#     def to_model(self) -> ExternalServiceLinkedEntities:
#         """Convert schema to ExternalServiceLinkedEntities domain value object."""
#         return ExternalServiceLinkedEntities(
#             miner_controllers=[cast(MinerController, item.to_model()) for item in self.miner_controllers],
#             energy_monitors=[cast(EnergyMonitor, item.to_model()) for item in self.energy_monitors],
#             forecast_providers=[cast(ForecastProvider, item.to_model()) for item in self.forecast_providers],
#             home_forecast_providers=[
#                 cast(HomeForecastProvider, item.to_model()) for item in self.home_forecast_providers
#             ],
#             notifiers=[cast(Notifier, item.to_model()) for item in self.notifiers],
#         )


class ExternalServiceHomeAssistantConfigSchema(BaseModel):
    """
    Schema for Home Assistant external service configuration.
    It encapsulates the configuration parameters to connect to a Home Assistant instance.
    """

    url: str = Field(..., description="URL of the Home Assistant instance")
    token: str = Field(..., description="Long-lived access token for Home Assistant API")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that the URL is not empty and is a valid URL format."""
        v = v.strip()
        if not v:
            raise ValueError("URL must not be empty")
        # Basic URL format validation
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Validate that the token is not empty."""
        v = v.strip()
        if not v:
            raise ValueError("Token must not be empty")
        return v

    def to_model(self) -> ExternalServiceConfig:
        """Convert schema to ExternalServiceConfig domain entity."""
        return ExternalServiceHomeAssistantConfig(
            url=self.url,
            token=self.token,
        )

    @classmethod
    def from_model(cls, config: ExternalServiceConfig) -> "ExternalServiceHomeAssistantConfigSchema":
        """Create schema from an ExternalServiceConfig domain entity."""
        if not isinstance(config, ExternalServiceHomeAssistantConfig):
            raise ValueError("Invalid config type for Home Assistant configuration schema")
        return cls(
            url=config.url,
            token=config.token,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


EXTERNAL_SERVICE_CONFIG_SCHEMA_MAP: Dict[
    type[ExternalServiceConfig], Union[type[ExternalServiceHomeAssistantConfigSchema]]
] = {ExternalServiceHomeAssistantConfig: ExternalServiceHomeAssistantConfigSchema}
