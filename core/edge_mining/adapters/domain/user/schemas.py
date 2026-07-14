"""Validation schemas for the user/system settings domain."""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator

from edge_mining.domain.user.value_objects import SystemConfiguration


class SystemConfigurationSchema(BaseModel):
    """Schema for the user-editable system configuration."""

    timezone: str = Field(default="Europe/Rome", description="IANA timezone name (e.g. Europe/Rome)")
    latitude: float = Field(default=41.9028, ge=-90.0, le=90.0, description="Location latitude in degrees")
    longitude: float = Field(default=12.4964, ge=-180.0, le=180.0, description="Location longitude in degrees")
    scheduler_interval_seconds: int = Field(
        default=5, ge=1, description="Interval in seconds between optimization evaluations"
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate that the timezone is a known IANA timezone."""
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"'{v}' is not a valid IANA timezone") from exc
        return v

    @classmethod
    def from_model(cls, configuration: SystemConfiguration) -> "SystemConfigurationSchema":
        """Build the schema from a domain configuration."""
        return cls(
            timezone=configuration.timezone,
            latitude=configuration.latitude,
            longitude=configuration.longitude,
            scheduler_interval_seconds=configuration.scheduler_interval_seconds,
        )

    def to_model(self) -> SystemConfiguration:
        """Convert the schema into a domain configuration."""
        return SystemConfiguration(
            timezone=self.timezone,
            latitude=self.latitude,
            longitude=self.longitude,
            scheduler_interval_seconds=self.scheduler_interval_seconds,
        )
