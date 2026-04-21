"""API Router for home load domain."""

from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from edge_mining.adapters.domain.home_load.schemas import (
    HOME_FORECAST_PROVIDER_CONFIG_SCHEMA_MAP,
    HomeForecastProviderCreateSchema,
    HomeForecastProviderSchema,
    HomeForecastProviderUpdateSchema,
    HomeLoadsProfileSchema,
    LoadDeviceCreateSchema,
    LoadDeviceSchema,
    LoadDeviceUpdateSchema,
)

# Import dependency injection setup functions
from edge_mining.adapters.infrastructure.api.setup import get_config_service
from edge_mining.application.interfaces import ConfigurationServiceInterface
from edge_mining.domain.common import EntityId
from edge_mining.domain.home_load.aggregate_roots import HomeLoadsProfile
from edge_mining.domain.home_load.common import HomeForecastProviderAdapter
from edge_mining.domain.home_load.entities import HomeForecastProvider, LoadDevice
from edge_mining.domain.home_load.exceptions import (
    HomeForecastProviderAlreadyExistsError,
    HomeForecastProviderConfigurationError,
    HomeForecastProviderNotFoundError,
    HomeLoadsProfileAddDeviceError,
    HomeLoadsProfileAlreadyExistsError,
    HomeLoadsProfileDeviceNotFoundError,
    HomeLoadsProfileNotFoundError,
    HomeLoadsProfileRemoveDeviceError,
)
from edge_mining.shared.adapter_maps.home_load import HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import HomeForecastProviderConfig

router = APIRouter()


# Home Loads Profile endpoints
@router.get("/home-loads-profiles", response_model=List[HomeLoadsProfileSchema])
async def get_home_loads_profiles_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[HomeLoadsProfileSchema]:
    """Get a list of all home loads profiles."""
    try:
        profiles: List[HomeLoadsProfile] = config_service.list_home_loads_profiles()

        # Convert to home loads profile schema
        profile_schemas: List[HomeLoadsProfileSchema] = []

        for profile in profiles:
            profile_schemas.append(HomeLoadsProfileSchema.from_model(profile))

        return profile_schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/home-loads-profiles", response_model=HomeLoadsProfileSchema)
async def add_home_loads_profile(
    profile_name: str,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> HomeLoadsProfileSchema:
    """Add a new home loads profile."""
    try:
        # Add the profile
        added_profile = config_service.add_home_loads_profile(profile_name)

        # For now, return the created profile
        return HomeLoadsProfileSchema.from_model(added_profile)
    except HomeLoadsProfileAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/home-loads-profiles/{profile_id}", response_model=HomeLoadsProfileSchema)
async def get_home_loads_profile(
    profile_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> HomeLoadsProfileSchema:
    """Get details of a specific home loads profile."""
    try:
        profile = config_service.get_home_loads_profile(profile_id)

        if profile is None:
            raise HomeLoadsProfileNotFoundError(f"Home Loads Profile with ID {profile_id} not found")
        return HomeLoadsProfileSchema.from_model(profile)
    except HomeLoadsProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/home-loads-profiles/{profile_id}", response_model=HomeLoadsProfileSchema)
async def update_home_loads_profile(
    profile_id: EntityId,
    profile_new_name: str,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> HomeLoadsProfileSchema:
    """Update an existing home loads profile."""
    try:
        profile = config_service.update_home_loads_profile(profile_id, profile_new_name)
        if profile is None:
            raise HomeLoadsProfileNotFoundError(f"Home Loads Profile with ID {profile_id} not found")
        response = HomeLoadsProfileSchema.from_model(profile)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/home-loads-profiles/{profile_id}", response_model=HomeLoadsProfileSchema)
async def delete_home_loads_profile(
    profile_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> HomeLoadsProfileSchema:
    """Remove a home loads profile."""
    try:
        deleted_profile = config_service.delete_home_loads_profile(profile_id)
        response = HomeLoadsProfileSchema.from_model(deleted_profile)
        return response
    except HomeLoadsProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# Load Device endpoints
@router.get("/home-loads-profiles/{profile_id}/devices", response_model=List[LoadDeviceSchema])
async def get_load_devices_list(
    profile_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[LoadDeviceSchema]:
    """Get a list of all load devices in a profile."""
    try:
        profile = config_service.get_home_loads_profile(profile_id)

        if profile is None:
            raise HomeLoadsProfileNotFoundError(f"Home Loads Profile with ID {profile_id} not found")

        devices: List[LoadDeviceSchema] = []
        for device in profile.devices:
            devices.append(LoadDeviceSchema.from_model(device))

        return devices
    except HomeLoadsProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/home-loads-profiles/{profile_id}/devices", response_model=LoadDeviceSchema)
async def add_load_device(
    profile_id: EntityId,
    device_data: LoadDeviceCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> LoadDeviceSchema:
    """Add a new load device to a profile."""
    try:
        # Convert to domain model
        device_to_add: LoadDevice = device_data.to_model()

        added_device = config_service.add_load_device_to_profile(profile_id=profile_id, load_device=device_to_add)

        if added_device is None:
            raise HomeLoadsProfileAddDeviceError(f"Failed to add load device to profile {profile_id}")

        return LoadDeviceSchema.from_model(added_device)
    except HomeLoadsProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HomeLoadsProfileAddDeviceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/home-loads-profiles/{profile_id}/devices/{device_id}", response_model=LoadDeviceSchema)
async def get_load_device(
    profile_id: EntityId,
    device_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> LoadDeviceSchema:
    """Get details of a specific load device."""
    try:
        profile = config_service.get_home_loads_profile(profile_id)

        if profile is None:
            raise HomeLoadsProfileNotFoundError(f"Home Loads Profile with ID {profile_id} not found")

        # Find the specific device
        device = next((d for d in profile.devices if d.id == device_id), None)

        if device is None:
            raise HomeLoadsProfileDeviceNotFoundError(
                f"Load Device with ID {device_id} not found in Home Loads Profile {profile_id}"
            )
        return LoadDeviceSchema.from_model(device)
    except HomeLoadsProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HomeLoadsProfileDeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/home-loads-profiles/{profile_id}/devices/{device_id}", response_model=LoadDeviceSchema)
async def update_load_device(
    profile_id: EntityId,
    device_id: EntityId,
    device_update: LoadDeviceUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> LoadDeviceSchema:
    """Update an existing load device."""
    try:
        profile = config_service.get_home_loads_profile(profile_id)

        if profile is None:
            raise HomeLoadsProfileNotFoundError(f"Home Loads Profile with ID {profile_id} not found")

        # Find the specific device
        device = next((d for d in profile.devices if d.id == device_id), None)

        if device is None:
            raise HomeLoadsProfileDeviceNotFoundError(
                f"Load Device with ID {device_id} not found in Home Loads Profile {profile_id}"
            )

        # Remove the old device
        deleted_device = config_service.remove_load_device_from_profile(profile_id, device_id)

        if deleted_device is None:
            raise HomeLoadsProfileRemoveDeviceError(
                f"Failed to remove existing load device with ID {device_id} from profile {profile_id}"
            )

        # Add the updated device
        provider_id = EntityId(device.home_forecast_provider_id) if device.home_forecast_provider_id else None
        new_device = LoadDevice(id=device.id, name=device.name, type=device.type, home_forecast_provider_id=provider_id)

        device_added = config_service.add_load_device_to_profile(
            profile_id=profile_id,
            load_device=new_device,
        )

        if device_added is None:
            raise HomeLoadsProfileAddDeviceError(f"Failed to add updated load device to profile {profile_id}")

        return LoadDeviceSchema.from_model(device_added)
    except HomeLoadsProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HomeLoadsProfileDeviceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HomeLoadsProfileRemoveDeviceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HomeLoadsProfileAddDeviceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/home-loads-profiles/{profile_id}/devices/{device_id}", response_model=LoadDeviceSchema)
async def delete_load_device(
    profile_id: EntityId,
    device_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> LoadDeviceSchema:
    """Remove a load device from a profile."""
    try:
        delete_load_device = config_service.remove_load_device_from_profile(profile_id, device_id)

        if delete_load_device is None:
            raise HomeLoadsProfileRemoveDeviceError(
                f"Failed to remove load device with ID {device_id} from profile {profile_id}"
            )
        response = LoadDeviceSchema.from_model(delete_load_device)
        return response
    except HomeLoadsProfileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HomeLoadsProfileRemoveDeviceError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# Home Forecast Provider endpoints
@router.get("/home-forecast-providers", response_model=List[HomeForecastProviderSchema])
async def get_home_forecast_providers_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[HomeForecastProviderSchema]:
    """Get a list of all home forecast providers."""
    try:
        # This would need to be implemented in the configuration service
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/home-forecast-providers", response_model=HomeForecastProviderSchema)
async def add_home_forecast_provider(
    provider_data: HomeForecastProviderCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> HomeForecastProviderSchema:
    """Add a new home forecast provider."""
    try:
        # Convert to domain model
        provider_to_add: HomeForecastProvider = provider_data.to_model()

        if provider_to_add.config is None:
            raise HomeForecastProviderConfigurationError("Home Forecast provider configuration should be set")

        # TODO: Add the provider (this would need to be implemented in the configuration service)

        return HomeForecastProviderSchema.from_model(provider_to_add)

    except HomeForecastProviderAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HomeForecastProviderConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/home-forecast-providers/types", response_model=List[HomeForecastProviderAdapter])
async def get_home_forecast_provider_types() -> List[HomeForecastProviderAdapter]:
    """Get a list of available home forecast provider types."""
    try:
        return [HomeForecastProviderAdapter(adapter.value) for adapter in HomeForecastProviderAdapter]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/home-forecast-providers/types/{adapter_type}/config-schema",
    response_model=Dict[str, Any],
)
async def get_home_forecast_provider_config_schema(
    adapter_type: HomeForecastProviderAdapter,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Dict[str, Any]:
    """Get the configuration schema for a specific home forecast provider type."""
    try:
        try:
            home_forecast_adapter = HomeForecastProviderAdapter(adapter_type.value)
        except ValueError as e:
            raise ValueError(f"Invalid home forecast provider adapter type: {adapter_type}") from e

        # Get the corresponding configuration class for the adapter type
        home_forecast_config_type: Optional[type[HomeForecastProviderConfig]] = (
            HOME_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(home_forecast_adapter)
        )

        if home_forecast_config_type is None:
            raise HomeForecastProviderConfigurationError(
                f"No configuration class found for adapter type {adapter_type}"
            )

        # Get the corresponding schema class
        schema_class = HOME_FORECAST_PROVIDER_CONFIG_SCHEMA_MAP.get(home_forecast_config_type)
        if schema_class is None:
            raise HomeForecastProviderConfigurationError(
                f"No schema found for configuration class {home_forecast_config_type}"
            )

        # Return the JSON schema
        return schema_class.model_json_schema()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/home-forecast-providers/{provider_id}", response_model=HomeForecastProviderSchema)
async def get_home_forecast_provider(
    provider_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> HomeForecastProviderSchema:
    """Get details of a specific home forecast provider."""
    try:
        # This would need to be implemented in the configuration service
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except HomeForecastProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/home-forecast-providers/{provider_id}", response_model=HomeForecastProviderSchema)
async def update_home_forecast_provider(
    provider_id: EntityId,
    provider_update: HomeForecastProviderUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> HomeForecastProviderSchema:
    """Update an existing home forecast provider."""
    try:
        # This would need to be implemented in the configuration service
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except HomeForecastProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/home-forecast-providers/{provider_id}", response_model=HomeForecastProviderSchema)
async def delete_home_forecast_provider(
    provider_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> HomeForecastProviderSchema:
    """Remove a home forecast provider."""
    try:
        # This would need to be implemented in the configuration service
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except HomeForecastProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
