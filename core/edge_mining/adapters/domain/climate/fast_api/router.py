"""API Router for climate domain"""

import uuid
from typing import Annotated, Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException

from edge_mining.adapters.domain.climate.schemas import (
    CLIMATE_MONITOR_CONFIG_SCHEMA_MAP,
    ClimateMonitorCreateSchema,
    ClimateMonitorSchema,
    ClimateMonitorUpdateSchema,
    ClimateZoneCreateSchema,
    ClimateZoneReadingSchema,
    ClimateZoneSchema,
    ClimateZoneUpdateSchema,
)
from edge_mining.adapters.infrastructure.api.setup import (
    get_adapter_service,
    get_config_service,
)
from edge_mining.application.interfaces import (
    AdapterServiceInterface,
    ConfigurationServiceInterface,
)
from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateMonitor, ClimateZone
from edge_mining.domain.climate.exceptions import (
    ClimateMonitorAlreadyExistsError,
    ClimateMonitorConfigurationError,
    ClimateMonitorNotFoundError,
    ClimateZoneAlreadyExistsError,
    ClimateZoneNotFoundError,
)
from edge_mining.domain.common import EntityId
from edge_mining.shared.adapter_maps.climate import (
    CLIMATE_MONITOR_CONFIG_TYPE_MAP,
    CLIMATE_MONITOR_TYPE_EXTERNAL_SERVICE_MAP,
)
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.interfaces.config import ClimateMonitorConfig, Configuration

router = APIRouter()


# --- Climate Zones ---


@router.get("/climate-zones", response_model=List[ClimateZoneSchema])
async def get_climate_zones_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[ClimateZoneSchema]:
    """Get a list of all configured climate zones."""
    try:
        zones = config_service.list_climate_zones()
        return [ClimateZoneSchema.from_model(zone) for zone in zones]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/climate-zones/{zone_id}", response_model=ClimateZoneSchema)
async def get_climate_zone_details(
    zone_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ClimateZoneSchema:
    """Get details for a specific climate zone."""
    try:
        zone: Optional[ClimateZone] = config_service.get_climate_zone(zone_id)
        if zone is None:
            raise ClimateZoneNotFoundError(f"Climate zone with ID {zone_id} not found")
        return ClimateZoneSchema.from_model(zone)
    except ClimateZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate zone not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/climate-zones", response_model=ClimateZoneSchema)
async def add_climate_zone(
    zone_schema: ClimateZoneCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ClimateZoneSchema:
    """Add a new climate zone."""
    try:
        zone_to_add: ClimateZone = zone_schema.to_model()
        new_zone = await config_service.create_climate_zone(
            name=zone_to_add.name,
            area_sqm=zone_to_add.area_sqm,
            climate_monitor_id=zone_to_add.climate_monitor_id,
        )
        return ClimateZoneSchema.from_model(new_zone)
    except ClimateZoneAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/climate-zones/{zone_id}", response_model=ClimateZoneSchema)
async def update_climate_zone(
    zone_id: EntityId,
    zone_update: ClimateZoneUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ClimateZoneSchema:
    """Update a climate zone's details."""
    try:
        zone = config_service.get_climate_zone(zone_id)
        if zone is None:
            raise ClimateZoneNotFoundError(f"Climate zone with ID {zone_id} not found")

        updated_zone = await config_service.update_climate_zone(
            zone_id=zone.id,
            name=zone_update.name if zone_update.name is not None else zone.name,
            area_sqm=zone_update.area_sqm if zone_update.area_sqm is not None else zone.area_sqm,
            temperature_schedule=(
                [s.to_model() for s in zone_update.temperature_schedule]
                if zone_update.temperature_schedule is not None
                else None
            ),
            hysteresis_celsius=zone_update.hysteresis_celsius,
            default_target_temperature=zone_update.default_target_temperature,
        )
        return ClimateZoneSchema.from_model(updated_zone)
    except ClimateZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate zone not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/climate-zones/{zone_id}", response_model=ClimateZoneSchema)
async def remove_climate_zone(
    zone_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ClimateZoneSchema:
    """Remove a climate zone."""
    try:
        deleted_zone = await config_service.delete_climate_zone(zone_id)
        return ClimateZoneSchema.from_model(deleted_zone)
    except ClimateZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate zone not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/climate-zones/{zone_id}/reading", response_model=Optional[ClimateZoneReadingSchema])
async def get_climate_zone_reading(
    zone_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
    adapter_service: Annotated[AdapterServiceInterface, Depends(get_adapter_service)],
) -> Optional[ClimateZoneReadingSchema]:
    """Get the current climate reading for a zone."""
    try:
        zone = config_service.get_climate_zone(zone_id)
        if zone is None:
            raise ClimateZoneNotFoundError(f"Climate zone with ID {zone_id} not found")

        monitor_port = await adapter_service.get_climate_monitor(zone)
        if monitor_port is None:
            raise HTTPException(status_code=404, detail="No climate monitor configured for this zone")

        reading = await monitor_port.get_climate_reading()
        if reading is None:
            return None
        return ClimateZoneReadingSchema.from_model(reading)
    except ClimateZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate zone not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Climate Monitors ---


@router.get("/climate-monitors", response_model=List[ClimateMonitorSchema])
async def get_climate_monitors_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[ClimateMonitorSchema]:
    """Get a list of all configured climate monitors."""
    try:
        monitors = config_service.list_climate_monitors()
        return [ClimateMonitorSchema.from_model(monitor) for monitor in monitors]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/climate-monitors/types", response_model=List[ClimateMonitorAdapter])
async def get_climate_monitor_types() -> List[ClimateMonitorAdapter]:
    """Get a list of available climate monitor types."""
    try:
        return [ClimateMonitorAdapter(adapter.value) for adapter in ClimateMonitorAdapter]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/climate-monitors/types/{adapter_type}/config-schema", response_model=Dict[str, Any])
async def get_climate_monitor_config_schema(
    adapter_type: ClimateMonitorAdapter,
) -> Dict[str, Any]:
    """Get the configuration schema for a specific climate monitor type."""
    try:
        config_class = CLIMATE_MONITOR_CONFIG_TYPE_MAP.get(adapter_type, None)
        if config_class is None:
            raise ClimateMonitorConfigurationError(f"No configuration class found for adapter type {adapter_type}")

        schema_class = CLIMATE_MONITOR_CONFIG_SCHEMA_MAP.get(config_class, None)
        if schema_class is None:
            raise ClimateMonitorConfigurationError(f"No schema found for configuration class {config_class}")

        return schema_class.model_json_schema()
    except ClimateMonitorConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/climate-monitors/types/{adapter_type}/external-services", response_model=Optional[ExternalServiceAdapter])
async def get_climate_monitor_type_external_service(
    adapter_type: ClimateMonitorAdapter,
) -> Optional[ExternalServiceAdapter]:
    """Get the required external service type for a specific climate monitor type."""
    try:
        return CLIMATE_MONITOR_TYPE_EXTERNAL_SERVICE_MAP.get(adapter_type, None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/climate-monitors/{monitor_id}", response_model=ClimateMonitorSchema)
async def get_climate_monitor_details(
    monitor_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ClimateMonitorSchema:
    """Get details for a specific climate monitor."""
    try:
        monitor: Optional[ClimateMonitor] = config_service.get_climate_monitor(monitor_id)
        if monitor is None:
            raise ClimateMonitorNotFoundError(f"Climate monitor with ID {monitor_id} not found")
        return ClimateMonitorSchema.from_model(monitor)
    except ClimateMonitorNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate monitor not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/climate-monitors", response_model=ClimateMonitorSchema)
async def add_climate_monitor(
    monitor_schema: ClimateMonitorCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ClimateMonitorSchema:
    """Add a new climate monitor."""
    try:
        monitor_to_add: ClimateMonitor = monitor_schema.to_model()
        if monitor_to_add.config is None:
            raise ClimateMonitorConfigurationError("Climate monitor configuration should be set")

        new_monitor = await config_service.create_climate_monitor(
            name=monitor_to_add.name,
            adapter_type=monitor_to_add.adapter_type,
            config=monitor_to_add.config,
            external_service_id=monitor_to_add.external_service_id,
        )
        return ClimateMonitorSchema.from_model(new_monitor)
    except ClimateMonitorAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ClimateMonitorConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/climate-monitors/{monitor_id}", response_model=ClimateMonitorSchema)
async def update_climate_monitor(
    monitor_id: EntityId,
    monitor_update: ClimateMonitorUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ClimateMonitorSchema:
    """Update a climate monitor's details."""
    try:
        monitor = config_service.get_climate_monitor(monitor_id)
        if monitor is None:
            raise ClimateMonitorNotFoundError(f"Climate monitor with ID {monitor_id} not found")

        configuration: Optional[Configuration] = None
        if monitor_update.config:
            config_cls = CLIMATE_MONITOR_CONFIG_TYPE_MAP.get(monitor.adapter_type, None)
            if config_cls is None:
                raise ClimateMonitorConfigurationError(
                    f"No configuration class found for adapter type {monitor.adapter_type}"
                )
            configuration = config_cls.from_dict(monitor_update.config)

        external_service_id: Optional[EntityId] = None
        if monitor_update.external_service_id:
            external_service_id = EntityId(uuid.UUID(monitor_update.external_service_id))

        updated_monitor = await config_service.update_climate_monitor(
            climate_monitor_id=monitor.id,
            name=monitor_update.name if monitor_update.name is not None else monitor.name,
            config=cast(ClimateMonitorConfig, configuration) if configuration else monitor.config,
            external_service_id=external_service_id
            if monitor_update.external_service_id
            else monitor.external_service_id,
        )
        return ClimateMonitorSchema.from_model(updated_monitor)
    except ClimateMonitorNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate monitor not found") from e
    except ClimateMonitorConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/climate-monitors/{monitor_id}", response_model=ClimateMonitorSchema)
async def remove_climate_monitor(
    monitor_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ClimateMonitorSchema:
    """Remove a climate monitor."""
    try:
        deleted_monitor = await config_service.delete_climate_monitor(monitor_id)
        return ClimateMonitorSchema.from_model(deleted_monitor)
    except ClimateMonitorNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate monitor not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/climate-monitors/{monitor_id}/check", response_model=Dict[str, str])
async def check_climate_monitor(
    monitor_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Dict[str, str]:
    """Check a climate monitor connection by performing a test reading."""
    try:
        result = await config_service.check_climate_monitor(monitor_id)
        if result:
            return {"status": "success", "message": "Climate monitor is operational"}
        else:
            return {"status": "failed", "message": "Climate monitor check failed"}
    except ClimateMonitorNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate monitor not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Linking ---


@router.post("/climate-zones/{zone_id}/monitor/{monitor_id}", response_model=ClimateZoneSchema)
async def link_climate_monitor_to_zone(
    zone_id: EntityId,
    monitor_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ClimateZoneSchema:
    """Link a climate monitor to a climate zone."""
    try:
        updated_zone = await config_service.set_climate_monitor_to_zone(zone_id, monitor_id)
        return ClimateZoneSchema.from_model(updated_zone)
    except ClimateZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate zone not found") from e
    except ClimateMonitorNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate monitor not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/climate-zones/{zone_id}/monitor", response_model=ClimateZoneSchema)
async def unlink_climate_monitor_from_zone(
    zone_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> ClimateZoneSchema:
    """Unlink the climate monitor from a climate zone."""
    try:
        updated_zone = await config_service.unlink_climate_monitor_from_zone(zone_id)
        return ClimateZoneSchema.from_model(updated_zone)
    except ClimateZoneNotFoundError as e:
        raise HTTPException(status_code=404, detail="Climate zone not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
