"""Settings module for Edge Mining application."""

from pydantic_settings import BaseSettings, SettingsConfigDict

# Using pydantic-settings for easy environment variable loading


class AppSettings(BaseSettings):
    """Settings for the Edge Mining application."""

    # Application settings
    log_level: str = "INFO"
    timezone: str = "Europe/Rome"  # Default timezone
    latitude: float = 41.9028  # Default latitude for Rome
    longitude: float = 12.4964  # Default longitude for Rome

    # Adapters Configuration (select which ones to use)
    persistence_adapter: str = "sqlalchemy"  # Options: "in_memory", "sqlite", "yaml", "sqlalchemy"
    policies_persistence_adapter: str = "yaml"  # Options: "in_memory", "sqlite", "yaml", "sqlalchemy"

    db_path: str = "sqlite:///data/db/edgemining.db"  # Database URL

    # Database migration settings
    run_migrations_on_startup: bool = True  # Automatically run Alembic migrations on startup
    backup_before_migration: bool = True  # Create database backup before running migrations

    yaml_policies_dir: str = "data/policies"  # Directory for YAML policies

    # API Settings
    api_port: int = 8001

    # Scheduler settings
    scheduler_interval_seconds: int = 5  # Evaluate every 5 seconds
    history_ingestion_interval_seconds: int = 120  # Collect power points every 2 minutes
    history_retention_days: int = 90  # Purge power points older than 90 days

    # Forecast mix settings (α/β blending of forecast with last real measurement)
    forecast_mix_alpha: float = 0.5  # Weight for the forecasted value
    forecast_mix_beta: float = 0.5  # Weight for the last real measured value

    model_config = SettingsConfigDict(
        env_file=".env",  # Load .env file if exists
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields from env
    )
