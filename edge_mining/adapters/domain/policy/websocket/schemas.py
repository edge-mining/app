"""WebSocket event schemas for the Policy domain."""

from typing import List, Optional

from pydantic import BaseModel, Field

from edge_mining.adapters.domain.policy.schemas import DecisionalContextSchema


class DecisionalContextUpdatedSchema(BaseModel):
    """WebSocket schema for DecisionalContextUpdatedEvent."""

    optimization_unit_id: Optional[str] = Field(None, description="ID of the optimization unit")
    optimization_unit_name: str = Field(default="", description="Name of the optimization unit")
    context: Optional[DecisionalContextSchema] = Field(None, description="Decisional context data")
    target_miner_ids: List[str] = Field(default_factory=list, description="IDs of target miners")
