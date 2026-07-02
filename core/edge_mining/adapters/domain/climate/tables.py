"""SQLAlchemy table definitions for the Climate domain."""

import json
import uuid
from typing import Any

from sqlalchemy import Column, Float, String, Table, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.climate.common import ClimateMonitorAdapter
from edge_mining.domain.climate.entities import ClimateMonitor, ClimateZone
from edge_mining.domain.common import EntityId


# --- ClimateMonitor event listeners ---


@event.listens_for(ClimateMonitor, "load")
def _receive_climate_monitor_load(target: ClimateMonitor, context) -> None:
    """Deserialize after loading from database."""
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore

    if hasattr(target, "external_service_id") and target.external_service_id is not None:
        if isinstance(target.external_service_id, str):  # type: ignore
            target.external_service_id = EntityId(uuid.UUID(target.external_service_id))  # type: ignore

    if isinstance(target.adapter_type, str):
        try:
            target.adapter_type = ClimateMonitorAdapter(target.adapter_type)
        except ValueError:
            pass

    if target.config and isinstance(target.config, str):
        from edge_mining.shared.adapter_maps.climate import CLIMATE_MONITOR_CONFIG_TYPE_MAP

        try:
            data = json.loads(target.config)
            config_class = CLIMATE_MONITOR_CONFIG_TYPE_MAP.get(target.adapter_type, None)
            if config_class:
                target.config = config_class.from_dict(data)
            else:
                target.config = None
        except (json.JSONDecodeError, ValueError):
            target.config = None


@event.listens_for(ClimateMonitor, "before_insert")
@event.listens_for(ClimateMonitor, "before_update")
def _flatten_climate_monitor_composites(mapper, connection, target: Any) -> None:
    """Flatten value objects before persisting."""
    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, ClimateMonitorAdapter):
            target.adapter_type = target.adapter_type.value

    if hasattr(target, "config") and target.config is not None:
        if not isinstance(target.config, str):
            target.config = json.dumps(target.config.to_dict())

    if hasattr(target, "id") and target.id is not None:
        if not isinstance(target.id, str):
            target.id = str(target.id)

    if hasattr(target, "external_service_id") and target.external_service_id is not None:
        if not isinstance(target.external_service_id, str):
            target.external_service_id = str(target.external_service_id)


@event.listens_for(ClimateMonitor, "after_insert")
@event.listens_for(ClimateMonitor, "after_update")
def _restore_climate_monitor_composites(mapper, connection, target: Any) -> None:
    """Restore value objects after persisting."""
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore

    if hasattr(target, "external_service_id") and target.external_service_id is not None:
        if isinstance(target.external_service_id, str):  # type: ignore
            target.external_service_id = EntityId(uuid.UUID(target.external_service_id))  # type: ignore

    if hasattr(target, "adapter_type") and target.adapter_type is not None:
        if isinstance(target.adapter_type, str):
            try:
                target.adapter_type = ClimateMonitorAdapter(target.adapter_type)
            except ValueError:
                pass

    if hasattr(target, "config") and target.config is not None:
        if isinstance(target.config, str):
            from edge_mining.shared.adapter_maps.climate import CLIMATE_MONITOR_CONFIG_TYPE_MAP

            try:
                data = json.loads(target.config)
                config_class = CLIMATE_MONITOR_CONFIG_TYPE_MAP.get(target.adapter_type, None)
                if config_class:
                    target.config = config_class.from_dict(data)
                else:
                    target.config = None
            except (json.JSONDecodeError, ValueError):
                target.config = None


# --- ClimateZone event listeners ---


@event.listens_for(ClimateZone, "load")
def _receive_climate_zone_load(target: ClimateZone, context) -> None:
    """Deserialize after loading from database."""
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore

    if hasattr(target, "climate_monitor_id") and target.climate_monitor_id is not None:
        if isinstance(target.climate_monitor_id, str):  # type: ignore
            target.climate_monitor_id = EntityId(uuid.UUID(target.climate_monitor_id))  # type: ignore

    # Deserialize temperature_schedule from JSON
    if hasattr(target, "temperature_schedule") and target.temperature_schedule is not None:
        if isinstance(target.temperature_schedule, str):
            from datetime import time as time_type

            from edge_mining.domain.climate.value_objects import TemperatureSlot

            try:
                data = json.loads(target.temperature_schedule)
                target.temperature_schedule = [
                    TemperatureSlot(
                        start_time=time_type.fromisoformat(s["start_time"]),
                        end_time=time_type.fromisoformat(s["end_time"]),
                        target_temperature=s["target_temperature"],
                    )
                    for s in data
                ]
            except (json.JSONDecodeError, KeyError, ValueError):
                target.temperature_schedule = []
    elif hasattr(target, "temperature_schedule"):
        target.temperature_schedule = []


@event.listens_for(ClimateZone, "before_insert")
@event.listens_for(ClimateZone, "before_update")
def _flatten_climate_zone_composites(mapper, connection, target: Any) -> None:
    """Flatten value objects before persisting."""
    if hasattr(target, "id") and target.id is not None:
        if not isinstance(target.id, str):
            target.id = str(target.id)

    if hasattr(target, "climate_monitor_id") and target.climate_monitor_id is not None:
        if not isinstance(target.climate_monitor_id, str):
            target.climate_monitor_id = str(target.climate_monitor_id)

    # Serialize temperature_schedule to JSON
    if hasattr(target, "temperature_schedule") and target.temperature_schedule is not None:
        if isinstance(target.temperature_schedule, list) and len(target.temperature_schedule) > 0:
            from edge_mining.domain.climate.value_objects import TemperatureSlot

            if isinstance(target.temperature_schedule[0], TemperatureSlot):
                target.temperature_schedule = json.dumps(
                    [
                        {
                            "start_time": s.start_time.isoformat(),
                            "end_time": s.end_time.isoformat(),
                            "target_temperature": s.target_temperature,
                        }
                        for s in target.temperature_schedule
                    ]
                )
        elif isinstance(target.temperature_schedule, list) and len(target.temperature_schedule) == 0:
            target.temperature_schedule = None


@event.listens_for(ClimateZone, "after_insert")
@event.listens_for(ClimateZone, "after_update")
def _restore_climate_zone_composites(mapper, connection, target: Any) -> None:
    """Restore value objects after persisting."""
    if hasattr(target, "id") and target.id is not None:
        if isinstance(target.id, str):  # type: ignore
            target.id = EntityId(uuid.UUID(target.id))  # type: ignore

    if hasattr(target, "climate_monitor_id") and target.climate_monitor_id is not None:
        if isinstance(target.climate_monitor_id, str):  # type: ignore
            target.climate_monitor_id = EntityId(uuid.UUID(target.climate_monitor_id))  # type: ignore

    # Restore temperature_schedule from JSON
    if hasattr(target, "temperature_schedule") and target.temperature_schedule is not None:
        if isinstance(target.temperature_schedule, str):
            from datetime import time as time_type

            from edge_mining.domain.climate.value_objects import TemperatureSlot

            try:
                data = json.loads(target.temperature_schedule)
                target.temperature_schedule = [
                    TemperatureSlot(
                        start_time=time_type.fromisoformat(s["start_time"]),
                        end_time=time_type.fromisoformat(s["end_time"]),
                        target_temperature=s["target_temperature"],
                    )
                    for s in data
                ]
            except (json.JSONDecodeError, KeyError, ValueError):
                target.temperature_schedule = []
    elif hasattr(target, "temperature_schedule"):
        target.temperature_schedule = []


# --- Table definitions ---

climate_monitors_table = Table(
    "climate_monitors",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False, default="home_assistant_api"),
    Column("config", String, nullable=True),
    Column("external_service_id", String, nullable=True),
)

climate_zones_table = Table(
    "climate_zones",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("area_sqm", Float, nullable=False),
    Column("climate_monitor_id", String, nullable=True),
    Column("temperature_schedule", String, nullable=True),
    Column("hysteresis_celsius", Float, nullable=False, default=0.5),
    Column("default_target_temperature", Float, nullable=True),
)

# Map entities to tables
mapper_registry.map_imperatively(ClimateMonitor, climate_monitors_table)
mapper_registry.map_imperatively(ClimateZone, climate_zones_table)
