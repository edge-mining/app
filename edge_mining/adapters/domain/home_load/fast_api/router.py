"""API Router for home load domain."""

import uuid
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from edge_mining.adapters.domain.home_load.schemas import (
    ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_SCHEMA_MAP,
    ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_SCHEMA_MAP,
    EnergyLoadForecastProviderCreateSchema,
    EnergyLoadForecastProviderSchema,
    EnergyLoadForecastProviderUpdateSchema,
    EnergyLoadHistoryProviderCreateSchema,
    EnergyLoadHistoryProviderSchema,
    EnergyLoadHistoryProviderUpdateSchema,
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
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter, EnergyLoadHistoryProviderAdapter
from edge_mining.domain.home_load.entities import EnergyLoadForecastProvider, EnergyLoadHistoryProvider, LoadDevice
from edge_mining.domain.home_load.exceptions import (
    EnergyLoadForecastProviderAlreadyExistsError,
    EnergyLoadForecastProviderConfigurationError,
    EnergyLoadForecastProviderNotFoundError,
    EnergyLoadHistoryProviderAlreadyExistsError,
    EnergyLoadHistoryProviderConfigurationError,
    EnergyLoadHistoryProviderNotFoundError,
    HomeLoadsProfileAddDeviceError,
    HomeLoadsProfileAlreadyExistsError,
    HomeLoadsProfileDeviceNotFoundError,
    HomeLoadsProfileNotFoundError,
    HomeLoadsProfileRemoveDeviceError,
)
from edge_mining.shared.adapter_maps.home_load import (
    ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP,
    ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_TYPE_MAP,
)
from edge_mining.shared.interfaces.config import EnergyLoadForecastProviderConfig, EnergyLoadHistoryProviderConfig

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
        deleted_profile = config_service.remove_home_loads_profile(profile_id)
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
        forecast_provider_id = (
            EntityId(uuid.UUID(device_update.energy_load_forecast_provider_id))
            if device_update.energy_load_forecast_provider_id
            else device.energy_load_forecast_provider_id
        )
        history_provider_id = (
            EntityId(uuid.UUID(device_update.energy_load_history_provider_id))
            if device_update.energy_load_history_provider_id
            else device.energy_load_history_provider_id
        )
        new_device = LoadDevice(
            id=device.id,
            name=device_update.name or device.name,
            category=device_update.category,
            enabled=device_update.enabled,
            energy_load_forecast_provider_id=forecast_provider_id,
            energy_load_history_provider_id=history_provider_id,
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
        providers = config_service.list_energy_load_forecast_providers()
        return [EnergyLoadForecastProviderSchema.from_model(p) for p in providers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/energy-load-forecast-providers", response_model=EnergyLoadForecastProviderSchema)
async def add_energy_load_forecast_provider(
    provider_data: EnergyLoadForecastProviderCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyLoadForecastProviderSchema:
    """Add a new energy load forecast provider."""
    try:
        provider_to_add: EnergyLoadForecastProvider = provider_data.to_model()

        if provider_to_add.config is None:
            raise EnergyLoadForecastProviderConfigurationError(
                "Energy Load Forecast provider configuration should be set"
            )

        added = config_service.add_energy_load_forecast_provider(provider_to_add)
        return EnergyLoadForecastProviderSchema.from_model(added)

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
        provider = config_service.get_energy_load_forecast_provider(provider_id)
        if provider is None:
            raise EnergyLoadForecastProviderNotFoundError(
                f"Energy Load Forecast Provider with ID {provider_id} not found"
            )
        return EnergyLoadForecastProviderSchema.from_model(provider)
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
        existing = config_service.get_energy_load_forecast_provider(provider_id)
        if existing is None:
            raise EnergyLoadForecastProviderNotFoundError(
                f"Energy Load Forecast Provider with ID {provider_id} not found"
            )
        existing.name = provider_update.name or existing.name
        if provider_update.config is not None and existing.adapter_type:
            config_type = ENERGY_LOAD_FORECAST_PROVIDER_CONFIG_TYPE_MAP.get(existing.adapter_type)
            if config_type:
                existing.config = config_type.from_dict(provider_update.config)
        if provider_update.external_service_id is not None:
            existing.external_service_id = EntityId(uuid.UUID(provider_update.external_service_id))
        updated = config_service.update_energy_load_forecast_provider(existing)
        return EnergyLoadForecastProviderSchema.from_model(updated)
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
        removed = config_service.remove_energy_load_forecast_provider(provider_id)
        return EnergyLoadForecastProviderSchema.from_model(removed)
    except EnergyLoadForecastProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Energy Load History Provider endpoints ---


@router.get("/energy-load-history-providers", response_model=List[EnergyLoadHistoryProviderSchema])
async def get_energy_load_history_providers_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[EnergyLoadHistoryProviderSchema]:
    """Get a list of all energy load history providers."""
    try:
        providers = config_service.list_energy_load_history_providers()
        return [EnergyLoadHistoryProviderSchema.from_model(p) for p in providers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/energy-load-history-providers", response_model=EnergyLoadHistoryProviderSchema)
async def add_energy_load_history_provider(
    provider_data: EnergyLoadHistoryProviderCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyLoadHistoryProviderSchema:
    """Add a new energy load history provider."""
    try:
        provider_to_add: EnergyLoadHistoryProvider = provider_data.to_model()
        added = config_service.add_energy_load_history_provider(provider_to_add)
        return EnergyLoadHistoryProviderSchema.from_model(added)
    except EnergyLoadHistoryProviderAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except EnergyLoadHistoryProviderConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/energy-load-history-providers/types", response_model=List[EnergyLoadHistoryProviderAdapter])
async def get_energy_load_history_provider_types() -> List[EnergyLoadHistoryProviderAdapter]:
    """Get a list of available energy load history provider types."""
    try:
        return [EnergyLoadHistoryProviderAdapter(adapter.value) for adapter in EnergyLoadHistoryProviderAdapter]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/energy-load-history-providers/types/{adapter_type}/config-schema",
    response_model=Dict[str, Any],
)
async def get_energy_load_history_provider_config_schema(
    adapter_type: EnergyLoadHistoryProviderAdapter,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Dict[str, Any]:
    """Get the configuration schema for a specific energy load history provider type."""
    try:
        try:
            provider_adapter = EnergyLoadHistoryProviderAdapter(adapter_type.value)
        except ValueError as e:
            raise ValueError(f"Invalid energy load history provider adapter type: {adapter_type}") from e

        provider_config_type: Optional[type[EnergyLoadHistoryProviderConfig]] = (
            ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_TYPE_MAP.get(provider_adapter)
        )

        if provider_config_type is None:
            return {}  # Some adapters (e.g. DUMMY) have no configuration

        schema_class = ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_SCHEMA_MAP.get(provider_config_type)
        if schema_class is None:
            raise EnergyLoadHistoryProviderConfigurationError(
                f"No schema found for configuration class {provider_config_type}"
            )

        return schema_class.model_json_schema()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/energy-load-history-providers/{provider_id}", response_model=EnergyLoadHistoryProviderSchema)
async def get_energy_load_history_provider(
    provider_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyLoadHistoryProviderSchema:
    """Get details of a specific energy load history provider."""
    try:
        provider = config_service.get_energy_load_history_provider(provider_id)
        if provider is None:
            raise EnergyLoadHistoryProviderNotFoundError(
                f"Energy Load History Provider with ID {provider_id} not found"
            )
        return EnergyLoadHistoryProviderSchema.from_model(provider)
    except EnergyLoadHistoryProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/energy-load-history-providers/{provider_id}", response_model=EnergyLoadHistoryProviderSchema)
async def update_energy_load_history_provider(
    provider_id: EntityId,
    provider_update: EnergyLoadHistoryProviderUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyLoadHistoryProviderSchema:
    """Update an existing energy load history provider."""
    try:
        existing = config_service.get_energy_load_history_provider(provider_id)
        if existing is None:
            raise EnergyLoadHistoryProviderNotFoundError(
                f"Energy Load History Provider with ID {provider_id} not found"
            )
        existing.name = provider_update.name or existing.name
        if provider_update.config is not None and existing.adapter_type:
            config_type = ENERGY_LOAD_HISTORY_PROVIDER_CONFIG_TYPE_MAP.get(existing.adapter_type)
            if config_type:
                existing.config = config_type.from_dict(provider_update.config)
        if provider_update.external_service_id is not None:
            existing.external_service_id = EntityId(uuid.UUID(provider_update.external_service_id))
        updated = config_service.update_energy_load_history_provider(existing)
        return EnergyLoadHistoryProviderSchema.from_model(updated)
    except EnergyLoadHistoryProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/energy-load-history-providers/{provider_id}", response_model=EnergyLoadHistoryProviderSchema)
async def delete_energy_load_history_provider(
    provider_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyLoadHistoryProviderSchema:
    """Remove an energy load history provider."""
    try:
        removed = config_service.remove_energy_load_history_provider(provider_id)
        return EnergyLoadHistoryProviderSchema.from_model(removed)
    except EnergyLoadHistoryProviderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
