"""API Router for energy domain."""

import uuid
from typing import Annotated, Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException

from edge_mining.adapters.domain.energy.schemas import (
    ENERGY_MONITOR_CONFIG_SCHEMA_MAP,
    EnergyMonitorCreateSchema,
    EnergyMonitorSchema,
    EnergyMonitorUpdateSchema,
    EnergySourceCreateSchema,
    EnergySourceSchema,
    EnergySourceUpdateSchema,
)

# Import dependency injection setup functions
from edge_mining.adapters.infrastructure.api.setup import get_config_service
from edge_mining.application.interfaces import ConfigurationServiceInterface
from edge_mining.domain.common import EntityId, Watts
from edge_mining.domain.energy.common import EnergyMonitorAdapter, EnergySourceType
from edge_mining.domain.energy.entities import EnergyMonitor, EnergySource
from edge_mining.domain.energy.exceptions import (
    EnergyMonitorAlreadyExistsError,
    EnergyMonitorConfigurationError,
    EnergyMonitorNotFoundError,
    EnergySourceAlreadyExistsError,
    EnergySourceConfigurationError,
    EnergySourceNotFoundError,
)
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.interfaces.config import Configuration, EnergyMonitorConfig

router = APIRouter()


@router.get("/energy-sources", response_model=List[EnergySourceSchema])
async def get_energy_sources_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[EnergySourceSchema]:
    """Get a list of all energy sources."""
    try:
        energy_sources: List[EnergySource] = config_service.list_energy_sources()

        # Convert to energy source schema
        energy_source_schemas: List[EnergySourceSchema] = []

        for energy_source in energy_sources:
            energy_source_schemas.append(EnergySourceSchema.from_model(energy_source))

        return energy_source_schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/energy-sources", response_model=EnergySourceSchema)
async def add_energy_source(
    energy_source_data: EnergySourceCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergySourceSchema:
    """Add a new energy source."""
    try:
        # Convert to domain model
        energy_source_to_add: EnergySource = energy_source_data.to_model()

        # Add the energy source
        created_source = await config_service.create_energy_source(
            name=energy_source_to_add.name,
            source_type=energy_source_to_add.type,
            nominal_power_max=energy_source_to_add.nominal_power_max,
            storage=energy_source_to_add.storage,
            grid=energy_source_to_add.grid,
            external_source=energy_source_to_add.external_source,
            energy_monitor_id=energy_source_to_add.energy_monitor_id,
            forecast_provider_id=energy_source_to_add.forecast_provider_id,
        )

        response = EnergySourceSchema.from_model(created_source)
        return response
    except EnergySourceAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except EnergySourceConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/energy-sources/types", response_model=List[EnergySourceType])
async def get_energy_source_types() -> List[EnergySourceType]:
    """Get a list of available energy source types."""
    try:
        return [EnergySourceType(source_type.value) for source_type in EnergySourceType]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/energy-sources/{source_id}", response_model=EnergySourceSchema)
async def get_energy_source(
    source_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergySourceSchema:
    """Get details of a specific energy source."""
    try:
        energy_source = config_service.get_energy_source(source_id)

        if energy_source is None:
            raise EnergySourceNotFoundError(f"Energy source with id {source_id} not found")

        return EnergySourceSchema.from_model(energy_source)
    except EnergySourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/energy-sources/{source_id}", response_model=EnergySourceSchema)
async def update_energy_source(
    source_id: EntityId,
    energy_source_update: EnergySourceUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergySourceSchema:
    """Update an existing energy source."""
    try:
        energy_source = config_service.get_energy_source(source_id)

        if energy_source is None:
            raise EnergySourceNotFoundError(f"Energy source with id {source_id} not found")

        # Update the energy source
        updated_source = await config_service.update_energy_source(
            source_id=source_id,
            name=energy_source_update.name or "",
            source_type=energy_source_update.type,
            nominal_power_max=Watts(energy_source_update.nominal_power_max)
            if energy_source_update.nominal_power_max is not None
            else None,
            storage=energy_source_update.storage.to_model() if energy_source_update.storage else None,
            grid=energy_source_update.grid.to_model() if energy_source_update.grid else None,
            external_source=Watts(energy_source_update.external_source)
            if energy_source_update.external_source is not None
            else None,
            energy_monitor_id=EntityId(uuid.UUID(energy_source_update.energy_monitor_id)),
            forecast_provider_id=EntityId(uuid.UUID(energy_source_update.forecast_provider_id)),
        )

        response = EnergySourceSchema.from_model(updated_source)

        return response
    except EnergySourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/energy-sources/{source_id}", response_model=EnergySourceSchema)
async def delete_energy_source(
    source_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergySourceSchema:
    """Remove an energy source."""
    try:
        deleted_source = await config_service.remove_energy_source(source_id)

        response = EnergySourceSchema.from_model(deleted_source)

        return response
    except EnergySourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# Energy Monitors endpoints
@router.get("/energy-monitors", response_model=List[EnergyMonitorSchema])
async def get_energy_monitors_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[EnergyMonitorSchema]:
    """Get a list of all energy monitors."""
    try:
        energy_monitors: List[EnergyMonitor] = config_service.list_energy_monitors()

        # Convert to energy monitor schema
        energy_monitor_schemas: List[EnergyMonitorSchema] = []

        for energy_monitor in energy_monitors:
            energy_monitor_schemas.append(EnergyMonitorSchema.from_model(energy_monitor))

        return energy_monitor_schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/energy-monitors", response_model=EnergyMonitorSchema)
async def add_energy_monitor(
    energy_monitor_data: EnergyMonitorCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyMonitorSchema:
    """Add a new energy monitor."""
    try:
        # Convert to domain model
        energy_monitor_to_add: EnergyMonitor = energy_monitor_data.to_model()

        if energy_monitor_to_add.config is None:
            raise EnergyMonitorConfigurationError("Energy monitor configuration should be set")

        # Add the energy monitor
        created_monitor = await config_service.create_energy_monitor(
            name=energy_monitor_to_add.name,
            adapter_type=energy_monitor_to_add.adapter_type,
            config=energy_monitor_to_add.config,
            external_service_id=energy_monitor_to_add.external_service_id,
        )

        response = EnergyMonitorSchema.from_model(created_monitor)
        return response
    except EnergyMonitorAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except EnergyMonitorConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/energy-monitors/types", response_model=List[EnergyMonitorAdapter])
async def get_energy_monitor_types() -> List[EnergyMonitorAdapter]:
    """Get a list of available energy monitor types."""
    try:
        return [EnergyMonitorAdapter(adapter.value) for adapter in EnergyMonitorAdapter]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/energy-monitors/types/{adapter_type}/config-schema",
    response_model=Dict[str, Any],
)
async def get_energy_monitor_config_schema(
    adapter_type: EnergyMonitorAdapter,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Dict[str, Any]:
    """Get the configuration schema for a specific energy monitor type."""
    try:
        try:
            energy_monitor_adapter = EnergyMonitorAdapter(adapter_type)
        except ValueError as e:
            raise ValueError(f"Invalid energy monitor adapter type: {adapter_type}") from e

        # Get the corresponding configuration class for the adapter type
        energy_monitor_config_type: Optional[type[EnergyMonitorConfig]] = (
            config_service.get_energy_monitor_config_by_type(energy_monitor_adapter)
        )

        if energy_monitor_config_type is None:
            raise ValueError(f"No configuration class found for adapter type {adapter_type}")

        # Map the configuration class to its corresponding schema
        energy_monitor_config_schema = ENERGY_MONITOR_CONFIG_SCHEMA_MAP.get(energy_monitor_config_type, None)

        if energy_monitor_config_schema is None:
            raise ValueError(f"No schema found for energy monitor config class: {energy_monitor_config_type}")

        return energy_monitor_config_schema.model_json_schema()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/energy-monitors/types/{adapter_type}/external-services",
    response_model=Optional[ExternalServiceAdapter],
)
async def get_energy_monitor_type_external_service_types(
    adapter_type: EnergyMonitorAdapter,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Optional[ExternalServiceAdapter]:
    """Get a list of compatible external service types for a specific energy monitor type."""
    try:
        needed_external_service = config_service.get_energy_monitor_external_service_adapter(adapter_type)

        return needed_external_service
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/energy-monitors/{monitor_id}", response_model=EnergyMonitorSchema)
async def get_energy_monitor(
    monitor_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyMonitorSchema:
    """Get details of a specific energy monitor."""
    try:
        energy_monitor = config_service.get_energy_monitor(monitor_id)

        if energy_monitor is None:
            raise EnergyMonitorNotFoundError(f"Energy monitor with id {monitor_id} not found")

        return EnergyMonitorSchema.from_model(energy_monitor)
    except EnergyMonitorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/energy-monitors/{monitor_id}", response_model=EnergyMonitorSchema)
async def update_energy_monitor(
    monitor_id: EntityId,
    energy_monitor_update: EnergyMonitorUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyMonitorSchema:
    """Update an existing energy monitor."""
    try:
        energy_monitor = config_service.get_energy_monitor(monitor_id)

        if energy_monitor is None:
            raise EnergyMonitorNotFoundError(f"Energy monitor with id {monitor_id} not found")

        configuration: Optional[Configuration] = None
        if energy_monitor_update.config:
            config_cls = config_service.get_energy_monitor_config_by_type(energy_monitor.adapter_type)
            if config_cls is None:
                raise EnergyMonitorConfigurationError(
                    f"No configuration class found for adapter type {energy_monitor.adapter_type}"
                )
            configuration = config_cls.from_dict(energy_monitor_update.config)

        external_service_id: Optional[EntityId] = None
        if energy_monitor_update.external_service_id:
            external_service_id = EntityId(uuid.UUID(energy_monitor_update.external_service_id))

        # Update the energy monitor
        updated_monitor = await config_service.update_energy_monitor(
            monitor_id=monitor_id,
            name=energy_monitor_update.name or "",
            config=cast(EnergyMonitorConfig, configuration),
            external_service_id=external_service_id,
        )

        response = EnergyMonitorSchema.from_model(updated_monitor)

        return response
    except EnergyMonitorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/energy-monitors/{monitor_id}", response_model=EnergyMonitorSchema)
async def delete_energy_monitor(
    monitor_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyMonitorSchema:
    """Remove an energy monitor."""
    try:
        deleted_monitor = await config_service.remove_energy_monitor(monitor_id)

        response = EnergyMonitorSchema.from_model(deleted_monitor)

        return response
    except EnergyMonitorNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
