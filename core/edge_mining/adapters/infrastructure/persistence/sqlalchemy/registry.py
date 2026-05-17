"""Shared SQLAlchemy metadata and mapper registry.

This module provides singleton instances of MetaData and mapper registry
that are shared across all domain table definitions and mappings.

By keeping these as module-level singletons, we avoid initialization order
issues and allow imports to happen in any order.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import registry

# Shared metadata instance for all table definitions
# All tables across all domains will use this single metadata instance
metadata = MetaData()

# Shared mapper registry for all imperative mappings
# All domain entities will be registered with this single registry
mapper_registry = registry(metadata=metadata)
