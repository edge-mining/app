"""SQLAlchemy ORM mappings for Performance domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

All tables and mappings use the shared metadata and mapper registry from
the sqlalchemy.registry module, which are available as module-level singletons.
"""

import json
from typing import Optional

from sqlalchemy import Column, String, Table, TypeDecorator, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.performance.common import MiningPerformanceTrackerAdapter
from edge_mining.domain.performance.entities import MiningPerformanceTracker
from edge_mining.domain.performance.exceptions import MiningPerformanceTrackerConfigurationError
from edge_mining.shared.adapter_maps.performance import MINING_PERFORMANCE_TRACKER_CONFIG_TYPE_MAP
from edge_mining.shared.interfaces.config import MiningPerformanceTrackerConfig


class MiningPerformanceTrackerConfigType(TypeDecorator):
    """Custom SQLAlchemy type that converts MiningPerformanceTrackerConfig to/from JSON string.

    This type handles serialization when writing to the database.
    Deserialization is handled by the @event.listens_for decorator on the entity.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[MiningPerformanceTrackerConfig], dialect) -> Optional[str]:
        """Convert MiningPerformanceTrackerConfig to JSON string before storing in DB."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value.to_dict())

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Return the JSON string as-is. Actual deserialization happens in the event listener."""
        return value


def _deserialize_mining_performance_tracker_config(
    adapter_type: MiningPerformanceTrackerAdapter, config_json: str
) -> Optional[MiningPerformanceTrackerConfig]:
    """Deserialize JSON string to MiningPerformanceTrackerConfig based on adapter type."""
    if not config_json:
        return None

    data: dict = json.loads(config_json)

    if adapter_type not in MINING_PERFORMANCE_TRACKER_CONFIG_TYPE_MAP:
        raise MiningPerformanceTrackerConfigurationError(
            f"Error reading MiningPerformanceTracker configuration. Invalid type '{adapter_type}'"
        )

    config_class: Optional[type[MiningPerformanceTrackerConfig]] = MINING_PERFORMANCE_TRACKER_CONFIG_TYPE_MAP.get(
        adapter_type
    )
    if not config_class:
        raise MiningPerformanceTrackerConfigurationError(
            f"Error creating MiningPerformanceTracker configuration. Type '{adapter_type}'"
        )

    config_instance = config_class.from_dict(data)
    if not isinstance(config_instance, MiningPerformanceTrackerConfig):
        raise MiningPerformanceTrackerConfigurationError(
            f"Deserialized config is not of type MiningPerformanceTrackerConfig for adapter type {adapter_type}."
        )
    return config_instance


@event.listens_for(MiningPerformanceTracker, "load")
def _receive_mining_performance_tracker_load(target: MiningPerformanceTracker, context) -> None:
    """Event listener that deserializes config after loading from database."""
    if target.config and isinstance(target.config, str):
        target.config = _deserialize_mining_performance_tracker_config(target.adapter_type, target.config)


# Define the mining_performance_trackers table using imperative style
mining_performance_trackers_table = Table(
    "mining_performance_trackers",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("adapter_type", String, nullable=False),
    Column("config", MiningPerformanceTrackerConfigType, nullable=True),
    Column("external_service_id", String, nullable=True),
)

# Map MiningPerformanceTracker
mapper_registry.map_imperatively(
    MiningPerformanceTracker,
    mining_performance_trackers_table,
)
