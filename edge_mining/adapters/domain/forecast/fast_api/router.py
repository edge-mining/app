"""API Router for forecast domain."""

import uuid
from typing import Annotated, Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException

from edge_mining.adapters.domain.forecast.schemas import (
    FORECAST_PROVIDER_CONFIG_SCHEMA_MAP,
    ForecastProviderCreateSchema,
    ForecastProviderSchema,
    ForecastProviderUpdateSchema,
)

# Import dependency injection setup functions
from edge_mining.adapters.infrastructure.api.setup import get_config_service
from edge_mining.application.interfaces import ConfigurationServiceInterface
from edge_mining.domain.common import EntityId
from edge_mining.domain.forecast.common import ForecastProviderAdapter
from edge_mining.domain.forecast.entities import ForecastProvider
from edge_mining.domain.forecast.exceptions import (
    ForecastProviderAlreadyExistsError,
    ForecastProviderConfigurationError,
    ForecastProviderNotFoundError,
)
from edge_mining.shared.adapter_maps.forecast import FORECAST_PROVIDER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import Configuration, ForecastProviderConfig

router = APIRouter()


@router.get("/forecast-providers", response_model=List[ForecastProviderSchema])
async def get_forecast_providers_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[ForecastProviderSchema]:
    """Get a list of all forecast providers."""
    try:
        forecast_providers: List[ForecastProvider] = config_service.list_forecast_providers()

        # Convert to forecast provider schema
        forecast_provider_schemas: List[ForecastProviderSchema] = []

        for forecast_provider in forecast_providers:
            forecast_provider_schemas.append(ForecastProviderSchema.from_model(forecast_provider))

        return forecast_provider_schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/forecast-providers", response_model=ForecastProviderSchema)
async def add_forecast_provider(
    forecast_provider_data: ForecastProviderCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ForecastProviderSchema:
    """Add a new forecast provider."""
    try:
        # Convert to domain model
        forecast_provider_to_add: ForecastProvider = forecast_provider_data.to_model()

        if forecast_provider_to_add.config is None:
            raise ForecastProviderConfigurationError("Forecast provider configuration should be set")

        # Add the forecast provider
        created_provider = config_service.create_forecast_provider(
            name=forecast_provider_to_add.name,
            adapter_type=forecast_provider_to_add.adapter_type,
            config=forecast_provider_to_add.config,
            external_service_id=forecast_provider_to_add.external_service_id,
        )

        response = ForecastProviderSchema.from_model(created_provider)
        return response
    except ForecastProviderAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ForecastProviderConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/forecast-providers/types", response_model=List[ForecastProviderAdapter])
async def get_forecast_provider_types() -> List[ForecastProviderAdapter]:
    """Get a list of available forecast provider types."""
    try:
        return [ForecastProviderAdapter(adapter.value) for adapter in ForecastProviderAdapter]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/forecast-providers/types/{adapter_type}/config-schema",
    response_model=Dict[str, Any],
)
async def get_forecast_provider_config_schema(
    adapter_type: ForecastProviderAdapter,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Dict[str, Any]:
    """Get the configuration schema for a specific forecast provider type."""
    try:
        try:
            forecast_adapter = ForecastProviderAdapter(adapter_type)
        except ValueError as e:
            raise ValueError(f"Invalid forecast provider adapter type: {adapter_type}") from e

        # Get the corresponding configuration class for the adapter type
        forecast_config_type: Optional[type[ForecastProviderConfig]] = FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(
            forecast_adapter, None
        )

        if forecast_config_type is None:
            raise ForecastProviderConfigurationError(f"No configuration class found for adapter type {adapter_type}")

        # Map the configuration class to its corresponding schema
        forecast_config_schema = FORECAST_PROVIDER_CONFIG_SCHEMA_MAP.get(forecast_config_type, None)

        if forecast_config_schema is None:
            raise ForecastProviderConfigurationError(f"No schema found for configuration class {forecast_config_type}")

        return forecast_config_schema.model_json_schema()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/forecast-providers/{provider_id}", response_model=ForecastProviderSchema)
async def get_forecast_provider(
    provider_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ForecastProviderSchema:
    """Get details of a specific forecast provider."""
    try:
        forecast_provider = config_service.get_forecast_provider(provider_id)

        if forecast_provider is None:
            raise ForecastProviderNotFoundError(f"Forecast Provider with ID {provider_id} not found")

        return ForecastProviderSchema.from_model(forecast_provider)
    except ForecastProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/forecast-providers/{provider_id}", response_model=ForecastProviderSchema)
async def update_forecast_provider(
    provider_id: EntityId,
    forecast_provider_update: ForecastProviderUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ForecastProviderSchema:
    """Update an existing forecast provider."""
    try:
        forecast_provider = config_service.get_forecast_provider(provider_id)

        if forecast_provider is None:
            raise ForecastProviderNotFoundError(f"Forecast Provider with ID {provider_id} not found")

        configuration: Optional[Configuration] = None
        if forecast_provider_update.config:
            config_cls = FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(forecast_provider.adapter_type, None)
            if config_cls is None:
                raise ForecastProviderConfigurationError(
                    f"No configuration class found for adapter type {forecast_provider.adapter_type}"
                )
            configuration = config_cls.from_dict(forecast_provider_update.config)

        external_service_id: Optional[EntityId] = None
        if forecast_provider_update.external_service_id:
            external_service_id = EntityId(uuid.UUID(forecast_provider_update.external_service_id))

        # Update the forecast provider
        updated_provider = config_service.update_forecast_provider(
            provider_id=provider_id,
            name=forecast_provider_update.name or "",
            adapter_type=forecast_provider.adapter_type,
            config=cast(ForecastProviderConfig, configuration),
            external_service_id=external_service_id,
        )

        response = ForecastProviderSchema.from_model(updated_provider)

        return response
    except ForecastProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/forecast-providers/{provider_id}", response_model=ForecastProviderSchema)
async def delete_forecast_provider(
    provider_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ForecastProviderSchema:
    """Remove a forecast provider."""
    try:
        deleted_provider = config_service.remove_forecast_provider(provider_id)

        response = ForecastProviderSchema.from_model(deleted_provider)

        return response
    except ForecastProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail="Forecast Provider not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
