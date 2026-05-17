"""Validation schemas for notification domain."""

import uuid
from typing import Dict, Optional, Union, cast

from pydantic import BaseModel, Field, field_serializer, field_validator

from edge_mining.domain.common import EntityId
from edge_mining.domain.notification.common import NotificationAdapter
from edge_mining.domain.notification.entities import Notifier
from edge_mining.shared.adapter_configs.notification import (
    DummyNotificationConfig,
    TelegramNotificationConfig,
)
from edge_mining.shared.adapter_maps.notification import NOTIFIER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import NotificationConfig


class NotifierSchema(BaseModel):
    """Schema for Notifier entity with complete validation."""

    id: str = Field(..., description="Unique identifier for the notifier")
    name: str = Field(default="", description="Notifier name")
    adapter_type: NotificationAdapter = Field(
        default=NotificationAdapter.DUMMY, description="Type of notification adapter"
    )
    config: dict = Field(default={}, description="Notifier configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that id is a valid UUID string."""
        try:
            uuid.UUID(v)
        except ValueError as exc:
            raise ValueError("id must be a valid UUID string") from exc
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate notifier name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> NotificationAdapter:
        """Validate that adapter_type is a recognized NotificationAdapter."""
        adapter_values = [adapter.value for adapter in NotificationAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return NotificationAdapter(v)

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that external_service_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("external_service_id must be a valid UUID string") from exc
        return v

    @classmethod
    def from_model(cls, notifier: Notifier) -> "NotifierSchema":
        """Create NotifierSchema from a Notifier domain model instance."""
        return cls(
            id=str(notifier.id),
            name=notifier.name,
            adapter_type=notifier.adapter_type,
            config=notifier.config.to_dict() if notifier.config else {},
            external_service_id=str(notifier.external_service_id) if notifier.external_service_id else None,
        )

    @field_serializer("id")
    def serialize_id(self, value: str) -> str:
        """Serialize id field."""
        return str(value)

    @field_serializer("external_service_id")
    def serialize_external_service_id(self, value: Optional[str]) -> Optional[str]:
        """Serialize external_service_id field."""
        return str(value) if value is not None else None

    def to_model(self) -> Notifier:
        """Convert NotifierSchema to Notifier domain model instance."""
        configuration: Optional[NotificationConfig] = None
        if self.config:
            config_class = NOTIFIER_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(NotificationConfig, config_class.from_dict(self.config))

        return Notifier(
            id=EntityId(uuid.UUID(self.id)),
            name=self.name,
            adapter_type=self.adapter_type,
            config=configuration,
            external_service_id=EntityId(uuid.UUID(self.external_service_id)) if self.external_service_id else None,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            uuid.UUID: str,
            NotificationAdapter: lambda v: v.value,
        }


class NotifierCreateSchema(BaseModel):
    """Schema for creating a new notifier."""

    name: str = Field(default="", description="Notifier name")
    adapter_type: NotificationAdapter = Field(
        default=NotificationAdapter.DUMMY, description="Type of notification adapter"
    )
    config: Optional[dict] = Field(default=None, description="Notifier configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate notifier name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("adapter_type")
    @classmethod
    def validate_adapter_type(cls, v: str) -> NotificationAdapter:
        """Validate that adapter_type is a recognized NotificationAdapter."""
        adapter_values = [adapter.value for adapter in NotificationAdapter]
        if v not in adapter_values:
            raise ValueError(f"adapter_type must be one of {adapter_values}")
        return NotificationAdapter(v)

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that external_service_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("external_service_id must be a valid UUID string") from exc
        return v

    def to_model(self) -> Notifier:
        """Convert NotifierCreateSchema to a Notifier domain model instance."""
        configuration: Optional[NotificationConfig] = None
        if self.config:
            config_class = NOTIFIER_CONFIG_TYPE_MAP.get(self.adapter_type, None)
            if config_class:
                configuration = cast(NotificationConfig, config_class.from_dict(self.config))

        return Notifier(
            id=EntityId(uuid.uuid4()),
            name=self.name,
            adapter_type=self.adapter_type,
            config=configuration,
            external_service_id=EntityId(uuid.UUID(self.external_service_id)) if self.external_service_id else None,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            uuid.UUID: str,
            NotificationAdapter: lambda v: v.value,
        }


class NotifierUpdateSchema(BaseModel):
    """Schema for updating an existing notifier."""

    name: str = Field(default="", description="Notifier name")
    config: Optional[dict] = Field(default=None, description="Notifier configuration")
    external_service_id: Optional[str] = Field(default=None, description="ID of external service")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate notifier name."""
        v = v.strip()
        if not v:
            v = ""
        return v

    @field_validator("external_service_id")
    @classmethod
    def validate_external_service_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate that external_service_id is a valid UUID string if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError as exc:
                raise ValueError("external_service_id must be a valid UUID string") from exc
        return v

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            uuid.UUID: str,
        }


class DummyNotificationConfigSchema(BaseModel):
    """Schema for Dummy NotificationConfig."""

    message: str = Field(default="This is a dummy notification", description="Default message for dummy notifications")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message."""
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        return v

    def to_model(self) -> DummyNotificationConfig:
        """
        Convert DummyNotificationConfigSchema to DummyNotificationConfig adapter configuration model instance.
        """
        return DummyNotificationConfig(
            message=self.message,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


class TelegramNotificationConfigSchema(BaseModel):
    """Schema for TelegramNotificationConfig."""

    bot_token: str = Field(..., description="Telegram bot token")
    chat_id: str = Field(..., description="Telegram chat ID")

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate bot token."""
        v = v.strip()
        if not v:
            raise ValueError("Bot token cannot be empty")
        # Basic format validation for Telegram bot tokens
        if not v.startswith("bot"):
            v = f"bot{v}"
        if ":" not in v:
            raise ValueError("Bot token must contain ':' separator")
        return v

    @field_validator("chat_id")
    @classmethod
    def validate_chat_id(cls, v: str) -> str:
        """Validate chat ID."""
        v = v.strip()
        if not v:
            raise ValueError("Chat ID cannot be empty")
        return v

    def to_model(self) -> TelegramNotificationConfig:
        """
        Convert schema to TelegramNotificationConfig adapter configuration model instance.
        """
        return TelegramNotificationConfig(
            bot_token=self.bot_token,
            chat_id=self.chat_id,
        )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        validate_assignment = True


NOTIFICATION_CONFIG_SCHEMA_MAP: Dict[
    type[NotificationConfig],
    Union[type[DummyNotificationConfigSchema], type[TelegramNotificationConfigSchema]],
] = {
    DummyNotificationConfig: DummyNotificationConfigSchema,
    TelegramNotificationConfig: TelegramNotificationConfigSchema,
}
