"""API Router for home load domain."""

from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from edge_mining.adapters.domain.home_load.schemas import (
    ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_SCHEMA_MAP,
    EnergyLoadForecastProviderCreateSchema,
    EnergyLoadForecastProviderSchema,
    EnergyLoadForecastProviderUpdateSchema,
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
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.entities import EnergyLoadForecastProvider, LoadDevice
from edge_mining.domain.home_load.exceptions import (
    EnergyLoadForecastProviderAlreadyExistsError,
    EnergyLoadForecastProviderConfigurationError,
    EnergyLoadForecastProviderNotFoundError,
    HomeLoadsProfileAddDeviceError,
    HomeLoadsProfileAlreadyExistsError,
    HomeLoadsProfileDeviceNotFoundError,
    HomeLoadsProfileNotFoundError,
    HomeLoadsProfileRemoveDeviceError,
)
from edge_mining.shared.adapter_maps.home_load import ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import EnergyLoadForecastProviderConfig

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
        provider_id = (
            EntityId(device.energy_load_forecast_provider_id) if device.energy_load_forecast_provider_id else None
        )
        new_device = LoadDevice(
            id=device.id,
            name=device_update.name or device.name,
            category=device_update.category,
            enabled=device_update.enabled,
            energy_load_forecast_provider_id=provider_id,
        )

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


# Energy Load Forecast Provider endpoints
@router.get("/energy-load-forecast-providers", response_model=List[EnergyLoadForecastProviderSchema])
async def get_energy_load_forecast_providers_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[EnergyLoadForecastProviderSchema]:
    """Get a list of all energy load forecast providers."""
    try:
        # This would need to be implemented in the configuration service
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/energy-load-forecast-providers", response_model=EnergyLoadForecastProviderSchema)
async def add_energy_load_forecast_provider(
    provider_data: EnergyLoadForecastProviderCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyLoadForecastProviderSchema:
    """Add a new energy load forecast provider."""
    try:
        # Convert to domain model
        provider_to_add: EnergyLoadForecastProvider = provider_data.to_model()

        if provider_to_add.config is None:
            raise EnergyLoadForecastProviderConfigurationError(
                "Energy Load Forecast provider configuration should be set"
            )

        # TODO: Add the provider (this would need to be implemented in the configuration service)

        return EnergyLoadForecastProviderSchema.from_model(provider_to_add)

    except EnergyLoadForecastProviderAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except EnergyLoadForecastProviderConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/energy-load-forecast-providers/types", response_model=List[EnergyLoadForecastProviderAdapter])
async def get_energy_load_forecast_provider_types() -> List[EnergyLoadForecastProviderAdapter]:
    """Get a list of available energy load forecast provider types."""
    try:
        return [EnergyLoadForecastProviderAdapter(adapter.value) for adapter in EnergyLoadForecastProviderAdapter]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/energy-load-forecast-providers/types/{adapter_type}/config-schema",
    response_model=Dict[str, Any],
)
async def get_energy_load_forecast_provider_config_schema(
    adapter_type: EnergyLoadForecastProviderAdapter,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Dict[str, Any]:
    """Get the configuration schema for a specific energy load forecast provider type."""
    try:
        try:
            provider_adapter = EnergyLoadForecastProviderAdapter(adapter_type.value)
        except ValueError as e:
            raise ValueError(f"Invalid energy load forecast provider adapter type: {adapter_type}") from e

        # Get the corresponding configuration class for the adapter type
        provider_config_type: Optional[type[EnergyLoadForecastProviderConfig]] = (
            ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(provider_adapter)
        )

        if provider_config_type is None:
            raise EnergyLoadForecastProviderConfigurationError(
                f"No configuration class found for adapter type {adapter_type}"
            )

        # Get the corresponding schema class
        schema_class = ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_SCHEMA_MAP.get(provider_config_type)
        if schema_class is None:
            raise EnergyLoadForecastProviderConfigurationError(
                f"No schema found for configuration class {provider_config_type}"
            )

        # Return the JSON schema
        return schema_class.model_json_schema()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/energy-load-forecast-providers/{provider_id}", response_model=EnergyLoadForecastProviderSchema)
async def get_energy_load_forecast_provider(
    provider_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyLoadForecastProviderSchema:
    """Get details of a specific energy load forecast provider."""
    try:
        # This would need to be implemented in the configuration service
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except EnergyLoadForecastProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/energy-load-forecast-providers/{provider_id}", response_model=EnergyLoadForecastProviderSchema)
async def update_energy_load_forecast_provider(
    provider_id: EntityId,
    provider_update: EnergyLoadForecastProviderUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyLoadForecastProviderSchema:
    """Update an existing energy load forecast provider."""
    try:
        # This would need to be implemented in the configuration service
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except EnergyLoadForecastProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/energy-load-forecast-providers/{provider_id}", response_model=EnergyLoadForecastProviderSchema)
async def delete_energy_load_forecast_provider(
    provider_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyLoadForecastProviderSchema:
    """Remove an energy load forecast provider."""
    try:
        # This would need to be implemented in the configuration service
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except EnergyLoadForecastProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
