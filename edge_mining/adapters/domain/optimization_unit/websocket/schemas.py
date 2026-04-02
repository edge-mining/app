"""WebSocket event schemas for the Optimization Unit domain."""

from typing import Optional

from pydantic import BaseModel, Field


class RuleEngagedSchema(BaseModel):
    """WebSocket schema for RuleEngagedEvent."""

    optimization_unit_id: Optional[str] = Field(None, description="ID of the optimization unit")
    optimization_unit_name: str = Field(default="", description="Name of the optimization unit")
    policy_id: Optional[str] = Field(None, description="ID of the policy")
    policy_name: str = Field(default="", description="Name of the policy")
    miner_id: Optional[str] = Field(None, description="ID of the miner")
    decision: Optional[str] = Field(None, description="Mining decision (start_mining/stop_mining/maintain_state)")
    miner_status: str = Field(default="", description="Current miner status")
