"""API Router for external services domain"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException

# Import dependency injection setup functions
from edge_mining.adapters.infrastructure.api.setup import get_adapter_service, get_config_service
from edge_mining.adapters.infrastructure.external_services.schemas import (
    EXTERNAL_SERVICE_CONFIG_SCHEMA_MAP,
    ExternalServiceCreateSchema,
    ExternalServiceSchema,
    ExternalServiceStatusEnum,
    ExternalServiceStatusSchema,
    ExternalServiceUpdateSchema,
)
from edge_mining.application.interfaces import (
    AdapterServiceInterface,
    ConfigurationServiceInterface,
)
from edge_mining.domain.common import EntityId
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.external_services.entities import ExternalService
from edge_mining.shared.external_services.exceptions import (
    ExternalServiceAlreadyExistsError,
    ExternalServiceConfigurationError,
    ExternalServiceNotFoundError,
)
from edge_mining.shared.interfaces.config import Configuration, ExternalServiceConfig

router = APIRouter()


@router.get("/external-services", response_model=List[ExternalServiceSchema])
async def get_external_services_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[ExternalServiceSchema]:
    """Get a list of all external services"""
    try:
        external_services: List[ExternalService] = config_service.list_external_services()

        # Convert to external service schema
        external_service_schemas: List[ExternalServiceSchema] = []

        for external_service in external_services:
            external_service_schemas.append(ExternalServiceSchema.from_model(external_service))

        return external_service_schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/external-services", response_model=ExternalServiceSchema)
async def add_external_service(
    external_service_data: ExternalServiceCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ExternalServiceSchema:
    """Add a new external service"""
    try:
        # Convert to domain model
        external_service_to_add: ExternalService = external_service_data.to_model()

        if external_service_to_add.config is None:
            raise ExternalServiceConfigurationError("External service configuration should be set")

        # Add the external service
        created_service = config_service.create_external_service(
            name=external_service_to_add.name,
            adapter_type=external_service_to_add.adapter_type,
            config=external_service_to_add.config,
        )

        response = ExternalServiceSchema.from_model(created_service)
        return response
    except ExternalServiceAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ExternalServiceConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/external-services/types", response_model=List[ExternalServiceAdapter])
async def get_external_service_types() -> List[ExternalServiceAdapter]:
    """Get a list of available external service types"""
    try:
        return [ExternalServiceAdapter(adapter.value) for adapter in ExternalServiceAdapter]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/external-services/types/{adapter_type}/config-schema",
    response_model=Dict[str, Any],
)
async def get_external_service_config_schema(
    adapter_type: ExternalServiceAdapter,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Dict[str, Any]:
    """Get the configuration schema for a specific external service type"""
    try:
        try:
            external_service_adapter = ExternalServiceAdapter(adapter_type)
        except ValueError as e:
            raise ValueError(f"Invalid external service adapter type: {adapter_type}") from e

        # Get the corresponding configuration class for the adapter type
        external_service_config_type: Optional[type[ExternalServiceConfig]] = (
            config_service.get_external_service_config_by_type(external_service_adapter)
        )

        if external_service_config_type is None:
            raise ValueError(f"No configuration class found for adapter type {adapter_type}")

        # Map the configuration class to its corresponding schema
        external_service_config_schema = EXTERNAL_SERVICE_CONFIG_SCHEMA_MAP.get(external_service_config_type, None)

        if external_service_config_schema is None:
            raise ValueError(f"No schema found for external service config class: {external_service_config_type}")

        return external_service_config_schema.model_json_schema()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/external-services/{service_id}", response_model=ExternalServiceSchema)
async def get_external_service(
    service_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ExternalServiceSchema:
    """Get details of a specific external service"""
    try:
        external_service = config_service.get_external_service(service_id)

        if external_service is None:
            raise ExternalServiceNotFoundError(f"External service with id {service_id} not found")

        return ExternalServiceSchema.from_model(external_service)
    except ExternalServiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/external-services/{service_id}", response_model=ExternalServiceSchema)
async def update_external_service(
    service_id: EntityId,
    external_service_update: ExternalServiceUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ExternalServiceSchema:
    """Update an existing external service"""
    try:
        external_service = config_service.get_external_service(service_id)

        if external_service is None:
            raise ExternalServiceNotFoundError(f"External service with id {service_id} not found")

        configuration: Optional[Configuration] = None
        if external_service_update.config:
            configuration = ExternalServiceConfig.from_dict(external_service_update.config)

        # Update the external service
        updated_service = config_service.update_external_service(
            service_id=service_id,
            name=external_service_update.name or "",
            config=cast(ExternalServiceConfig, configuration),
        )

        response = ExternalServiceSchema.from_model(updated_service)

        return response
    except ExternalServiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/external-services/{service_id}", response_model=ExternalServiceSchema)
async def delete_external_service(
    service_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ExternalServiceSchema:
    """Remove an external service."""
    try:
        deleted_service = config_service.remove_external_service(service_id)

        response = ExternalServiceSchema.from_model(deleted_service)

        return response
    except ExternalServiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/external-services/{service_id}/status", response_model=ExternalServiceStatusSchema)
async def get_external_service_status(
    service_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
    adapter_service: Annotated[AdapterServiceInterface, Depends(get_adapter_service)],
) -> ExternalServiceStatusSchema:
    """Get the connection status of a specific external service"""
    try:
        external_service_adapter = adapter_service.get_external_service(service_id)

        if external_service_adapter is None:
            raise ExternalServiceNotFoundError(f"External service with id {service_id} not found")

        external_service = config_service.get_external_service(service_id)
        if external_service is None:
            raise ExternalServiceNotFoundError(f"External service with id {service_id} not found")

        try:
            is_connected = external_service_adapter.is_connected()
            status = ExternalServiceStatusEnum.CONNECTED if is_connected else ExternalServiceStatusEnum.DISCONNECTED
            error_message = None
        except Exception as e:
            status = ExternalServiceStatusEnum.DISCONNECTED
            error_message = str(e)

        return ExternalServiceStatusSchema(
            name=external_service.name,
            status=status,
            last_check=datetime.now(),
            error_message=error_message,
        )
    except ExternalServiceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
