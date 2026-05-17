"""API Router for the mining performance tracker domain."""

import uuid
from typing import Annotated, Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query

from edge_mining.adapters.domain.performance.schemas import (
    MINING_PERFORMANCE_TRACKER_CONFIG_SCHEMA_MAP,
    MiningPerformanceTrackerCreateSchema,
    MiningPerformanceTrackerSchema,
    MiningPerformanceTrackerUpdateSchema,
    MiningRewardSchema,
    PayoutScheduleSchema,
    PoolStatsSchema,
    PoolWorkerStatsSchema,
)
from edge_mining.adapters.infrastructure.api.setup import (
    get_adapter_service,
    get_config_service,
)
from edge_mining.application.interfaces import (
    AdapterServiceInterface,
    ConfigurationServiceInterface,
)
from edge_mining.domain.common import EntityId
from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.exceptions import (
    MiningPerformanceTrackerAlreadyExistsError,
    MiningPerformanceTrackerConfigurationError,
    MiningPerformanceTrackerNotFoundError,
    MiningPoolAuthError,
    MiningPoolRateLimitedError,
    MiningPoolResponseError,
    MiningPoolUnreachableError,
)
from edge_mining.shared.external_services.common import ExternalServiceAdapter
from edge_mining.shared.interfaces.config import (
    Configuration,
    MiningPerformanceTrackerConfig,
)

router = APIRouter()


@router.get("/mining-performance-trackers", response_model=List[MiningPerformanceTrackerSchema])
async def get_mining_performance_trackers_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[MiningPerformanceTrackerSchema]:
    """Get a list of all configured mining performance trackers."""
    try:
        trackers = config_service.list_mining_performance_trackers()
        return [MiningPerformanceTrackerSchema.from_model(t) for t in trackers]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/mining-performance-trackers/types",
    response_model=List[MiningPerformanceTrackerAdapter],
)
async def get_mining_performance_tracker_types() -> List[MiningPerformanceTrackerAdapter]:
    """Get a list of available mining performance tracker types."""
    try:
        return [MiningPerformanceTrackerAdapter(a.value) for a in MiningPerformanceTrackerAdapter]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/mining-performance-trackers/types/{adapter_type}/config-schema",
    response_model=Dict[str, Any],
)
async def get_mining_performance_tracker_config_schema(
    adapter_type: MiningPerformanceTrackerAdapter,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Dict[str, Any]:
    """Get the configuration JSON schema for a specific tracker type."""
    try:
        try:
            tracker_adapter = MiningPerformanceTrackerAdapter(adapter_type)
        except ValueError as e:
            raise ValueError(f"Invalid mining performance tracker adapter type: {adapter_type}") from e

        config_type: Optional[type[MiningPerformanceTrackerConfig]] = (
            config_service.get_mining_performance_tracker_config_by_type(tracker_adapter)
        )
        if config_type is None:
            raise MiningPerformanceTrackerConfigurationError(
                f"No configuration class found for adapter type {adapter_type}"
            )

        schema_cls = MINING_PERFORMANCE_TRACKER_CONFIG_SCHEMA_MAP.get(config_type, None)
        if schema_cls is None:
            raise MiningPerformanceTrackerConfigurationError(f"No schema found for configuration class {config_type}")

        return schema_cls.model_json_schema()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/mining-performance-trackers/types/{adapter_type}/external-services",
    response_model=Optional[ExternalServiceAdapter],
)
async def get_mining_performance_tracker_external_service_types(
    adapter_type: MiningPerformanceTrackerAdapter,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> Optional[ExternalServiceAdapter]:
    """Get the compatible external service adapter for a specific tracker type, if any."""
    try:
        return config_service.get_mining_performance_tracker_external_service_adapter(adapter_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/mining-performance-trackers/{tracker_id}",
    response_model=MiningPerformanceTrackerSchema,
)
async def get_mining_performance_tracker_details(
    tracker_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> MiningPerformanceTrackerSchema:
    """Get details for a specific mining performance tracker."""
    try:
        tracker: Optional[MiningPerformanceTracker] = config_service.get_mining_performance_tracker(tracker_id)
        if tracker is None:
            raise MiningPerformanceTrackerNotFoundError(f"Mining performance tracker {tracker_id} not found")
        return MiningPerformanceTrackerSchema.from_model(tracker)
    except MiningPerformanceTrackerNotFoundError as e:
        raise HTTPException(status_code=404, detail="Mining performance tracker not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/mining-performance-trackers", response_model=MiningPerformanceTrackerSchema)
async def add_mining_performance_tracker(
    tracker_schema: MiningPerformanceTrackerCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> MiningPerformanceTrackerSchema:
    """Add a new mining performance tracker."""
    try:
        tracker_to_add: MiningPerformanceTracker = tracker_schema.to_model()

        if tracker_to_add.config is None:
            raise MiningPerformanceTrackerConfigurationError("Mining performance tracker configuration should be set")

        new_tracker = await config_service.add_mining_performance_tracker(
            name=tracker_to_add.name,
            adapter_type=tracker_to_add.adapter_type,
            config=tracker_to_add.config,
            external_service_id=tracker_to_add.external_service_id,
        )
        return MiningPerformanceTrackerSchema.from_model(new_tracker)
    except MiningPerformanceTrackerAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except MiningPerformanceTrackerConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put(
    "/mining-performance-trackers/{tracker_id}",
    response_model=MiningPerformanceTrackerSchema,
)
async def update_mining_performance_tracker(
    tracker_id: EntityId,
    tracker_update: MiningPerformanceTrackerUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> MiningPerformanceTrackerSchema:
    """Update a mining performance tracker's details."""
    try:
        tracker = config_service.get_mining_performance_tracker(tracker_id)
        if tracker is None:
            raise MiningPerformanceTrackerNotFoundError(f"Mining performance tracker {tracker_id} not found")

        configuration: Optional[Configuration] = None
        if tracker_update.config:
            config_cls = config_service.get_mining_performance_tracker_config_by_type(tracker.adapter_type)
            if config_cls is None:
                raise MiningPerformanceTrackerConfigurationError(
                    f"No configuration class found for adapter type {tracker.adapter_type}"
                )
            configuration = config_cls.from_dict(tracker_update.config)

        external_service_id: Optional[EntityId] = None
        if tracker_update.external_service_id:
            external_service_id = EntityId(uuid.UUID(tracker_update.external_service_id))

        updated_tracker = await config_service.update_mining_performance_tracker(
            tracker_id=tracker.id,
            name=tracker_update.name or "",
            config=cast(MiningPerformanceTrackerConfig, configuration),
            external_service_id=external_service_id,
        )
        return MiningPerformanceTrackerSchema.from_model(updated_tracker)
    except MiningPerformanceTrackerNotFoundError as e:
        raise HTTPException(status_code=404, detail="Mining performance tracker not found") from e
    except MiningPerformanceTrackerConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete(
    "/mining-performance-trackers/{tracker_id}",
    response_model=MiningPerformanceTrackerSchema,
)
async def remove_mining_performance_tracker(
    tracker_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> MiningPerformanceTrackerSchema:
    """Remove a mining performance tracker."""
    try:
        deleted = await config_service.remove_mining_performance_tracker(tracker_id)
        return MiningPerformanceTrackerSchema.from_model(deleted)
    except MiningPerformanceTrackerNotFoundError as e:
        raise HTTPException(status_code=404, detail="Mining performance tracker not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/mining-performance-trackers/{tracker_id}/test",
    response_model=Dict[str, str],
)
async def test_mining_performance_tracker(
    tracker_id: EntityId,
    adapter_service: Annotated[AdapterServiceInterface, Depends(get_adapter_service)],
) -> Dict[str, str]:
    """Test connectivity to a mining performance tracker by fetching payout schedule."""
    try:
        tracker_port = await adapter_service.get_mining_performance_tracker(tracker_id)
        if tracker_port is None:
            raise MiningPerformanceTrackerNotFoundError(f"Mining performance tracker {tracker_id} not found")

        await tracker_port.get_payout_schedule()
        return {"status": "success", "message": "Mining performance tracker reachable"}
    except MiningPerformanceTrackerNotFoundError as e:
        raise HTTPException(status_code=404, detail="Mining performance tracker not found") from e
    except MiningPoolRateLimitedError as e:
        headers = {"Retry-After": str(int(e.retry_after))} if e.retry_after else None
        raise HTTPException(status_code=429, detail=f"Pool rate-limited: {str(e)}", headers=headers) from e
    except MiningPoolAuthError as e:
        raise HTTPException(status_code=401, detail=f"Pool authentication failed: {str(e)}") from e
    except MiningPoolUnreachableError as e:
        raise HTTPException(status_code=503, detail=f"Pool unreachable: {str(e)}") from e
    except MiningPoolResponseError as e:
        raise HTTPException(status_code=502, detail=f"Pool returned invalid response: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test tracker: {str(e)}") from e


@router.get(
    "/mining-performance-trackers/{tracker_id}/stats",
    response_model=PoolStatsSchema,
)
async def get_mining_performance_tracker_stats(
    tracker_id: EntityId,
    adapter_service: Annotated[AdapterServiceInterface, Depends(get_adapter_service)],
) -> PoolStatsSchema:
    """Get live pool statistics for a mining performance tracker."""
    try:
        tracker_port = await adapter_service.get_mining_performance_tracker(tracker_id)
        if tracker_port is None:
            raise MiningPerformanceTrackerNotFoundError(f"Mining performance tracker {tracker_id} not found")

        stats = await tracker_port.get_pool_stats()
        if stats is None:
            raise HTTPException(status_code=502, detail="Pool returned no statistics")

        return PoolStatsSchema.from_model(stats)
    except HTTPException:
        raise
    except MiningPerformanceTrackerNotFoundError as e:
        raise HTTPException(status_code=404, detail="Mining performance tracker not found") from e
    except MiningPoolRateLimitedError as e:
        headers = {"Retry-After": str(int(e.retry_after))} if e.retry_after else None
        raise HTTPException(status_code=429, detail=f"Pool rate-limited: {str(e)}", headers=headers) from e
    except MiningPoolAuthError as e:
        raise HTTPException(status_code=401, detail=f"Pool authentication failed: {str(e)}") from e
    except MiningPoolUnreachableError as e:
        raise HTTPException(status_code=503, detail=f"Pool unreachable: {str(e)}") from e
    except MiningPoolResponseError as e:
        raise HTTPException(status_code=502, detail=f"Pool returned invalid response: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}") from e


@router.get(
    "/mining-performance-trackers/{tracker_id}/workers",
    response_model=List[PoolWorkerStatsSchema],
)
async def get_mining_performance_tracker_workers(
    tracker_id: EntityId,
    adapter_service: Annotated[AdapterServiceInterface, Depends(get_adapter_service)],
) -> List[PoolWorkerStatsSchema]:
    """Get live per-worker statistics for a mining performance tracker."""
    try:
        tracker_port = await adapter_service.get_mining_performance_tracker(tracker_id)
        if tracker_port is None:
            raise MiningPerformanceTrackerNotFoundError(f"Mining performance tracker {tracker_id} not found")

        workers = await tracker_port.get_worker_stats([])
        return [PoolWorkerStatsSchema.from_model(w) for w in workers]
    except MiningPerformanceTrackerNotFoundError as e:
        raise HTTPException(status_code=404, detail="Mining performance tracker not found") from e
    except MiningPoolRateLimitedError as e:
        headers = {"Retry-After": str(int(e.retry_after))} if e.retry_after else None
        raise HTTPException(status_code=429, detail=f"Pool rate-limited: {str(e)}", headers=headers) from e
    except MiningPoolAuthError as e:
        raise HTTPException(status_code=401, detail=f"Pool authentication failed: {str(e)}") from e
    except MiningPoolUnreachableError as e:
        raise HTTPException(status_code=503, detail=f"Pool unreachable: {str(e)}") from e
    except MiningPoolResponseError as e:
        raise HTTPException(status_code=502, detail=f"Pool returned invalid response: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch workers: {str(e)}") from e


@router.get(
    "/mining-performance-trackers/{tracker_id}/rewards",
    response_model=List[MiningRewardSchema],
)
async def get_mining_performance_tracker_rewards(
    tracker_id: EntityId,
    adapter_service: Annotated[AdapterServiceInterface, Depends(get_adapter_service)],
    limit: int = Query(default=10, ge=1, le=500, description="Maximum number of rewards to return"),
) -> List[MiningRewardSchema]:
    """Get recent rewards for a mining performance tracker (live passthrough)."""
    try:
        tracker_port = await adapter_service.get_mining_performance_tracker(tracker_id)
        if tracker_port is None:
            raise MiningPerformanceTrackerNotFoundError(f"Mining performance tracker {tracker_id} not found")

        rewards = await tracker_port.get_recent_rewards(limit=limit)
        return [MiningRewardSchema.from_model(r) for r in rewards]
    except MiningPerformanceTrackerNotFoundError as e:
        raise HTTPException(status_code=404, detail="Mining performance tracker not found") from e
    except MiningPoolRateLimitedError as e:
        headers = {"Retry-After": str(int(e.retry_after))} if e.retry_after else None
        raise HTTPException(status_code=429, detail=f"Pool rate-limited: {str(e)}", headers=headers) from e
    except MiningPoolAuthError as e:
        raise HTTPException(status_code=401, detail=f"Pool authentication failed: {str(e)}") from e
    except MiningPoolUnreachableError as e:
        raise HTTPException(status_code=503, detail=f"Pool unreachable: {str(e)}") from e
    except MiningPoolResponseError as e:
        raise HTTPException(status_code=502, detail=f"Pool returned invalid response: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch rewards: {str(e)}") from e


@router.get(
    "/mining-performance-trackers/{tracker_id}/payout-schedule",
    response_model=PayoutScheduleSchema,
)
async def get_mining_performance_tracker_payout_schedule(
    tracker_id: EntityId,
    adapter_service: Annotated[AdapterServiceInterface, Depends(get_adapter_service)],
) -> PayoutScheduleSchema:
    """Get the payout schedule for a mining performance tracker."""
    try:
        tracker_port = await adapter_service.get_mining_performance_tracker(tracker_id)
        if tracker_port is None:
            raise MiningPerformanceTrackerNotFoundError(f"Mining performance tracker {tracker_id} not found")

        schedule = await tracker_port.get_payout_schedule()
        if schedule is None:
            raise HTTPException(status_code=502, detail="Pool returned no payout schedule")

        return PayoutScheduleSchema.from_model(schedule)
    except HTTPException:
        raise
    except MiningPerformanceTrackerNotFoundError as e:
        raise HTTPException(status_code=404, detail="Mining performance tracker not found") from e
    except MiningPoolRateLimitedError as e:
        headers = {"Retry-After": str(int(e.retry_after))} if e.retry_after else None
        raise HTTPException(status_code=429, detail=f"Pool rate-limited: {str(e)}", headers=headers) from e
    except MiningPoolAuthError as e:
        raise HTTPException(status_code=401, detail=f"Pool authentication failed: {str(e)}") from e
    except MiningPoolUnreachableError as e:
        raise HTTPException(status_code=503, detail=f"Pool unreachable: {str(e)}") from e
    except MiningPoolResponseError as e:
        raise HTTPException(status_code=502, detail=f"Pool returned invalid response: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch payout schedule: {str(e)}") from e
