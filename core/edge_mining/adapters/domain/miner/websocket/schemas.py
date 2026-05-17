"""WebSocket event schemas for the Miner domain."""

from typing import Optional

from pydantic import BaseModel, Field


class MinerStateChangedSchema(BaseModel):
    """WebSocket schema for MinerStateChangedEvent."""

    miner_id: Optional[str] = Field(None, description="ID of the miner")
    miner_name: str = Field(default="", description="Name of the miner")
    old_status: Optional[str] = Field(None, description="Previous miner status")
    new_status: Optional[str] = Field(None, description="New miner status")
