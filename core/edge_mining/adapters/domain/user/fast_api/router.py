"""API Router for the system settings domain."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from edge_mining.adapters.domain.user.schemas import SystemConfigurationSchema
from edge_mining.adapters.infrastructure.api.setup import get_config_service
from edge_mining.application.interfaces import ConfigurationServiceInterface
from edge_mining.domain.exceptions import ConfigurationError

router = APIRouter()


@router.get("/system/settings", response_model=SystemConfigurationSchema)
async def get_system_settings(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> SystemConfigurationSchema:
    """Get the current system configuration."""
    try:
        configuration = config_service.get_system_configuration()
        return SystemConfigurationSchema.from_model(configuration)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/system/settings", response_model=SystemConfigurationSchema)
async def update_system_settings(
    payload: SystemConfigurationSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> SystemConfigurationSchema:
    """Update the system configuration."""
    try:
        configuration = await config_service.update_system_configuration(payload.to_model())
        return SystemConfigurationSchema.from_model(configuration)
    except ConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
