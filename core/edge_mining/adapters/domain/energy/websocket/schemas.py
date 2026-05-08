"""WebSocket event schemas for the Energy domain."""

from typing import Optional

from pydantic import BaseModel, Field

from edge_mining.adapters.domain.energy.schemas import EnergyStateSnapshotSchema


class EnergyStateSnapshotUpdatedSchema(BaseModel):
    """WebSocket schema for EnergyStateSnapshotUpdatedEvent."""

    optimization_unit_id: Optional[str] = Field(None, description="ID of the optimization unit")
    optimization_unit_name: str = Field(default="", description="Name of the optimization unit")
    energy_source_id: Optional[str] = Field(None, description="ID of the energy source")
    energy_state_snapshot: Optional[EnergyStateSnapshotSchema] = Field(None, description="Energy state snapshot data")
