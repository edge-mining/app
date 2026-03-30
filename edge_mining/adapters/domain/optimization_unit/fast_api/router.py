"""API Router for optimization unit domain."""

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from edge_mining.adapters.domain.optimization_unit.schemas import (
    EnergyOptimizationUnitCreateSchema,
    EnergyOptimizationUnitSchema,
    EnergyOptimizationUnitUpdateSchema,
)
from edge_mining.adapters.domain.policy.schemas import DecisionalContextSchema

# Import dependency injection setup functions
from edge_mining.adapters.infrastructure.api.setup import get_config_service, get_optimization_service
from edge_mining.application.interfaces import ConfigurationServiceInterface, OptimizationServiceInterface
from edge_mining.domain.common import EntityId
from edge_mining.domain.optimization_unit.aggregate_roots import EnergyOptimizationUnit
from edge_mining.domain.optimization_unit.exceptions import (
    OptimizationUnitAlreadyExistsError,
    OptimizationUnitConfigurationError,
    OptimizationUnitNotFoundError,
)

router = APIRouter()


@router.get("/optimization-units", response_model=List[EnergyOptimizationUnitSchema])
async def get_optimization_units_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[EnergyOptimizationUnitSchema]:
    """Get a list of all configured optimization units."""
    try:
        optimization_units: List[EnergyOptimizationUnit] = config_service.list_optimization_units()

        # Convert to optimization unit schema
        optimization_unit_schemas: List[EnergyOptimizationUnitSchema] = []

        for optimization_unit in optimization_units:
            optimization_unit_schemas.append(EnergyOptimizationUnitSchema.from_model(optimization_unit))

        return optimization_unit_schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/optimization-units", response_model=EnergyOptimizationUnitSchema)
async def add_optimization_unit(
    optimization_unit_data: EnergyOptimizationUnitCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Add a new optimization unit."""
    try:
        # Convert to domain model
        optimization_unit_to_add: EnergyOptimizationUnit = optimization_unit_data.to_model()

        # Add the optimization unit
        created_unit = await config_service.create_optimization_unit(
            name=optimization_unit_to_add.name,
            description=optimization_unit_to_add.description,
            policy_id=optimization_unit_to_add.policy_id,
            target_miner_ids=optimization_unit_to_add.target_miner_ids,
            energy_source_id=optimization_unit_to_add.energy_source_id,
            home_forecast_provider_id=optimization_unit_to_add.home_forecast_provider_id,
            performance_tracker_id=optimization_unit_to_add.performance_tracker_id,
            notifier_ids=optimization_unit_to_add.notifier_ids,
        )

        if created_unit is None:
            raise HTTPException(status_code=500, detail="Failed to create optimization unit")

        response = EnergyOptimizationUnitSchema.from_model(created_unit)
        return response
    except OptimizationUnitAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except OptimizationUnitConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/optimization-units/{unit_id}", response_model=EnergyOptimizationUnitSchema)
async def get_optimization_unit(
    unit_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Get details of a specific optimization unit."""
    try:
        optimization_unit: Optional[EnergyOptimizationUnit] = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        return EnergyOptimizationUnitSchema.from_model(optimization_unit)
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/optimization-units/{unit_id}", response_model=EnergyOptimizationUnitSchema)
async def update_optimization_unit(
    unit_id: EntityId,
    optimization_unit_update: EnergyOptimizationUnitUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Update an existing optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        # Parse entity IDs
        policy_id: Optional[EntityId] = None
        if optimization_unit_update.policy_id:
            policy_id = EntityId(uuid.UUID(optimization_unit_update.policy_id))

        target_miner_ids: List[EntityId] = []
        if optimization_unit_update.target_miner_ids:
            target_miner_ids = [EntityId(uuid.UUID(miner_id)) for miner_id in optimization_unit_update.target_miner_ids]

        energy_source_id: Optional[EntityId] = None
        if optimization_unit_update.energy_source_id:
            energy_source_id = EntityId(uuid.UUID(optimization_unit_update.energy_source_id))

        home_forecast_provider_id: Optional[EntityId] = None
        if optimization_unit_update.home_forecast_provider_id:
            home_forecast_provider_id = EntityId(uuid.UUID(optimization_unit_update.home_forecast_provider_id))

        performance_tracker_id: Optional[EntityId] = None
        if optimization_unit_update.performance_tracker_id:
            performance_tracker_id = EntityId(uuid.UUID(optimization_unit_update.performance_tracker_id))

        notifier_ids: List[EntityId] = []
        if optimization_unit_update.notifier_ids:
            notifier_ids = [EntityId(uuid.UUID(notifier_id)) for notifier_id in optimization_unit_update.notifier_ids]

        # Update the optimization unit
        updated_unit = await config_service.update_optimization_unit(
            unit_id=unit_id,
            name=optimization_unit_update.name or "",
            description=optimization_unit_update.description,
            policy_id=policy_id,
            target_miner_ids=target_miner_ids,
            energy_source_id=energy_source_id,
            home_forecast_provider_id=home_forecast_provider_id,
            performance_tracker_id=performance_tracker_id,
            notifier_ids=notifier_ids,
        )

        response = EnergyOptimizationUnitSchema.from_model(updated_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/optimization-units/{unit_id}", response_model=EnergyOptimizationUnitSchema)
async def delete_optimization_unit(
    unit_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Remove an optimization unit."""
    try:
        deleted_unit = await config_service.remove_optimization_unit(unit_id)

        response = EnergyOptimizationUnitSchema.from_model(deleted_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/optimization-units/{unit_id}/enable", response_model=EnergyOptimizationUnitSchema)
async def enable_optimization_unit(
    unit_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Enable an optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        enabled_unit = await config_service.activate_optimization_unit(unit_id)

        response = EnergyOptimizationUnitSchema.from_model(enabled_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except OptimizationUnitConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/optimization-units/{unit_id}/disable", response_model=EnergyOptimizationUnitSchema)
async def disable_optimization_unit(
    unit_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Disable an optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        disabled_unit = await config_service.deactivate_optimization_unit(unit_id)

        response = EnergyOptimizationUnitSchema.from_model(disabled_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/optimization-units/{unit_id}/energy-source", response_model=EnergyOptimizationUnitSchema)
async def assign_energy_source(
    unit_id: EntityId,
    energy_source_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Assign an energy source to an optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        updated_unit = await config_service.assign_energy_source_to_optimization_unit(unit_id, energy_source_id)

        response = EnergyOptimizationUnitSchema.from_model(updated_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/optimization-units/{unit_id}/policy", response_model=EnergyOptimizationUnitSchema)
async def assign_policy(
    unit_id: EntityId,
    policy_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Assign an optimization policy to an optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        updated_unit = await config_service.assign_policy_to_optimization_unit(unit_id, policy_id)

        response = EnergyOptimizationUnitSchema.from_model(updated_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/optimization-units/{unit_id}/miners", response_model=EnergyOptimizationUnitSchema)
async def assign_miners(
    unit_id: EntityId,
    miner_ids: List[EntityId],
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Assign target miners to an optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        updated_unit = await config_service.assign_miners_to_optimization_unit(unit_id, miner_ids)

        response = EnergyOptimizationUnitSchema.from_model(updated_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/optimization-units/{unit_id}/miners/single", response_model=EnergyOptimizationUnitSchema)
async def add_target_miner(
    unit_id: EntityId,
    miner_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Add a single target miner to an optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        updated_unit = await config_service.add_miner_to_optimization_unit(unit_id, miner_id)

        response = EnergyOptimizationUnitSchema.from_model(updated_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/optimization-units/{unit_id}/miners/{miner_id}", response_model=EnergyOptimizationUnitSchema)
async def remove_target_miner(
    unit_id: EntityId,
    miner_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Remove a target miner from an optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        updated_unit = await config_service.remove_miner_from_optimization_unit(unit_id, miner_id)

        response = EnergyOptimizationUnitSchema.from_model(updated_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/optimization-units/{unit_id}/notifiers", response_model=EnergyOptimizationUnitSchema)
async def assign_notifiers(
    unit_id: EntityId,
    notifier_ids: List[EntityId],
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Assign notifiers to an optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        updated_unit = await config_service.assign_notifiers_to_optimization_unit(unit_id, notifier_ids)

        response = EnergyOptimizationUnitSchema.from_model(updated_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/optimization-units/{unit_id}/notifiers/single", response_model=EnergyOptimizationUnitSchema)
async def add_notifier(
    unit_id: EntityId,
    notifier_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Add a single notifier to an optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        updated_unit = await config_service.add_notifier_to_optimization_unit(unit_id, notifier_id)

        response = EnergyOptimizationUnitSchema.from_model(updated_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/optimization-units/{unit_id}/notifiers/{notifier_id}", response_model=EnergyOptimizationUnitSchema)
async def remove_notifier(
    unit_id: EntityId,
    notifier_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> EnergyOptimizationUnitSchema:
    """Remove a notifier from an optimization unit."""
    try:
        optimization_unit = config_service.get_optimization_unit(unit_id)

        if optimization_unit is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        updated_unit = await config_service.remove_notifier_from_optimization_unit(unit_id, notifier_id)

        response = EnergyOptimizationUnitSchema.from_model(updated_unit)

        return response
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail="Optimization Unit not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/optimization-units/{unit_id}/decisional-context", response_model=DecisionalContextSchema)
async def get_decisional_context(
    unit_id: EntityId,
    optimization_service: Annotated[OptimizationServiceInterface, Depends(get_optimization_service)],
) -> DecisionalContextSchema:
    """Get the current decisional context for an optimization unit."""
    try:
        context = optimization_service.get_decisional_context(unit_id)

        if context is None:
            raise OptimizationUnitNotFoundError(f"Optimization Unit with ID {unit_id} not found")

        return DecisionalContextSchema.from_model(context)
    except OptimizationUnitNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
