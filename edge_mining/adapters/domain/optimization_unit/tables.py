"""SQLAlchemy ORM mappings for OptimizationUnit domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

All tables and mappings use the shared metadata and mapper registry from
the sqlalchemy.registry module, which are available as module-level singletons.

⚠️  DEVELOPER WARNING ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANY SCHEMA CHANGE (adding/removing/modifying tables or columns) REQUIRES an
Alembic migration. Do NOT modify this file without creating a migration:

  python scripts/migrate.py create "Description of your change"

For detailed instructions, see: docs/ALEMBIC_MIGRATIONS.md
For a step-by-step example, see: docs/MIGRATION_EXAMPLE.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import uuid
from typing import List

from sqlalchemy import Boolean, Column, ForeignKey, String, Table, TypeDecorator

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.common import EntityId
from edge_mining.domain.optimization_unit.aggregate_roots import EnergyOptimizationUnit


class EntityIdListType(TypeDecorator):
    """Custom SQLAlchemy type that converts List[EntityId] to/from JSON string."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect) -> str:
        """Convert List[EntityId] to JSON string before storing in DB."""
        if value is None:
            return json.dumps([])
        if not value:
            return json.dumps([])
        return json.dumps([str(eid) for eid in value])

    def process_result_value(self, value, dialect) -> List[EntityId]:
        """Convert JSON string to List[EntityId] when reading from DB."""
        if not value:
            return []

        return [EntityId(uuid.UUID(eid)) for eid in json.loads(value)]


# Define the optimization_units table using imperative style
optimization_units_table = Table(
    "optimization_units",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("description", String, nullable=True),
    Column("is_enabled", Boolean, nullable=False, default=False),
    Column("policy_id", String, nullable=True),  # TODO: Add ForeignKey when policies table exists
    Column("target_miner_ids", EntityIdListType, nullable=False),  # JSON list - could be association table
    Column("energy_source_id", String, ForeignKey("energy_sources.id"), nullable=True),
    Column("performance_tracker_id", String, ForeignKey("mining_performance_trackers.id"), nullable=True),
    Column("notifier_ids", EntityIdListType, nullable=False),  # JSON list - could be association table
)

# Map EnergyOptimizationUnit
mapper_registry.map_imperatively(
    EnergyOptimizationUnit,
    optimization_units_table,
)
