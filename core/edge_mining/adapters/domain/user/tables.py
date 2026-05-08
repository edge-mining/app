"""SQLAlchemy table definitions for User/Settings domain.

This module defines the database schema and ORM mappings for the User and Settings entities
using SQLAlchemy's imperative (classical) mapping style.

⚠️  DEVELOPER WARNING ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANY SCHEMA CHANGE (adding/removing/modifying tables or columns) REQUIRES an
Alembic migration. Do NOT modify this file without creating a migration:

  python scripts/migrate.py create "Description of your change"

For detailed instructions, see: docs/ALEMBIC_MIGRATIONS.md
For a step-by-step example, see: docs/MIGRATION_EXAMPLE.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from sqlalchemy import JSON, Column, String, Table

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.user.entities import SystemSettings


# Settings table
settings_table = Table(
    "settings",
    metadata,
    Column("id", String, primary_key=True),
    Column("settings_json", JSON, nullable=False),
)

# Map SystemSettings entity to settings table
mapper_registry.map_imperatively(
    SystemSettings,
    settings_table,
    properties={
        "id": settings_table.c.id,
        "settings": settings_table.c.settings_json,
    },
)
