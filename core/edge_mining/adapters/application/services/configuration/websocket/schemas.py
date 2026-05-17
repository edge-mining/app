"""WebSocket schemas for Configuration events."""

from typing import Optional

from pydantic import BaseModel, Field


class ConfigurationUpdatedSchema(BaseModel):
    """WebSocket schema for ConfigurationUpdatedEvent."""

    entity_type: str = Field(default="", description="Type of the configuration entity")
    entity_id: Optional[str] = Field(None, description="ID of the configuration entity")
    action: str = Field(default="", description="Action performed (created/updated/removed)")
