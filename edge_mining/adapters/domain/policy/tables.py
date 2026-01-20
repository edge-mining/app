"""SQLAlchemy ORM mappings for Policy domain entities.

This module implements imperative (classical) mapping of the domain entities
to database tables. The domain entities are mapped directly without
creating separate ORM model classes, maintaining domain purity.

All tables and mappings use the shared metadata and mapper registry from
the sqlalchemy.registry module, which are available as module-level singletons.
"""

import json
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, String, Table, TypeDecorator, event

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import mapper_registry, metadata
from edge_mining.domain.policy.aggregate_roots import AutomationRule, OptimizationPolicy


class AutomationRulesListType(TypeDecorator):
    """Custom SQLAlchemy type that converts List[AutomationRule] to/from JSON string.

    This type handles serialization when writing to the database.
    Deserialization is handled by the @event.listens_for decorator on the entity.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[List[AutomationRule]], dialect) -> Optional[str]:
        """Convert List[AutomationRule] to JSON string before storing in DB.

        Args:
            value: List of AutomationRule instances or None
            dialect: SQLAlchemy dialect

        Returns:
            JSON string representation or None
        """
        if value is None:
            return None

        # Serialize rules to JSON
        rules_data = []
        for rule in value:
            rule_dict = {
                "id": str(rule.id),
                "name": rule.name,
                "description": rule.description,
                "priority": rule.priority,
                "enabled": rule.enabled,
                "conditions": rule.conditions,
            }
            rules_data.append(rule_dict)

        return json.dumps(rules_data)

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Return the JSON string as-is. Actual deserialization happens in the event listener.

        Args:
            value: JSON string from database or None
            dialect: SQLAlchemy dialect

        Returns:
            JSON string or None (will be converted to List[AutomationRule] by event listener)
        """
        return value  # Return as string, event listener will convert


def _deserialize_automation_rules(rules_json: Optional[str]) -> List[AutomationRule]:
    """Deserialize JSON string to List[AutomationRule].

    Args:
        rules_json: JSON string representation of rules

    Returns:
        List of AutomationRule instances
    """
    if not rules_json:
        return []

    rules_data: List[Dict[str, Any]] = json.loads(rules_json)
    rules = []

    for rule_data in rules_data:
        rule = AutomationRule(
            id=rule_data["id"],  # EntityId will handle UUID conversion
            priority=rule_data["priority"],
            name=rule_data["name"],
            description=rule_data["description"],
            enabled=rule_data["enabled"],
            conditions=rule_data["conditions"],
        )
        rules.append(rule)

    return rules


@event.listens_for(OptimizationPolicy, "load")
def _receive_optimization_policy_load(target: OptimizationPolicy, context) -> None:
    """Event listener that deserializes rules after loading from database.

    Args:
        target: The OptimizationPolicy instance being loaded
        context: SQLAlchemy context
    """
    # During load, SQLAlchemy may pass the JSON string before type conversion
    # We need to check at runtime and convert if necessary
    if target.start_rules and isinstance(target.start_rules, str):  # type: ignore
        target.start_rules = _deserialize_automation_rules(target.start_rules)  # type: ignore

    if target.stop_rules and isinstance(target.stop_rules, str):  # type: ignore
        target.stop_rules = _deserialize_automation_rules(target.stop_rules)  # type: ignore


# Define the policies table using imperative style
policies_table = Table(
    "policies",
    metadata,
    # Primary Key
    Column("id", String, primary_key=True, index=True),
    # Basic attributes
    Column("name", String, nullable=False, unique=True),
    Column("description", String, nullable=True),
    # Rules stored as JSON strings with automatic conversion
    Column("start_rules", AutomationRulesListType, nullable=True),
    Column("stop_rules", AutomationRulesListType, nullable=True),
)

# Map OptimizationPolicy to the policies table
mapper_registry.map_imperatively(
    OptimizationPolicy,
    policies_table,
)
