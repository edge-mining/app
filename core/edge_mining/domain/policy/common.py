"""Collection of Common Objects for the Energy Optimization domain of the Edge Mining application."""

from enum import Enum
from typing import Dict


# Decision object
class MiningDecision(Enum):
    """Types of different mining decisions."""

    START_MINING = "start_mining"
    STOP_MINING = "stop_mining"
    MAINTAIN_STATE = "maintain_state"
    # Could add more granular decisions later, e.g., ADJUST_POWER


# Rule type
class RuleType(Enum):
    """Types of different rules."""

    START = "start"
    STOP = "stop"
    # Could add more types of rules in the future


class RuleEngineType(Enum):
    """Types of rule engines."""

    CUSTOM = "custom"  # Custom rule engine


# Operator types for rule conditions
class OperatorType(Enum):
    """Supported operators for rule conditions."""

    EQ = "eq"  # equal
    NE = "ne"  # not equal
    GT = "gt"  # greater than
    GTE = "gte"  # greater than or equal
    LT = "lt"  # less than
    LTE = "lte"  # less than or equal
    IN = "in"  # in list/array
    NOT_IN = "not_in"  # not in list/array
    CONTAINS = "contains"  # string contains
    STARTS_WITH = "starts_with"  # string starts with
    ENDS_WITH = "ends_with"  # string ends with
    REGEX = "regex"  # regex match


# Mapping of operators to their symbolic representation
OPERATOR_SYMBOLS: Dict[OperatorType, str] = {
    OperatorType.EQ: "==",
    OperatorType.NE: "!=",
    OperatorType.GT: ">",
    OperatorType.GTE: ">=",
    OperatorType.LT: "<",
    OperatorType.LTE: "<=",
    OperatorType.IN: "∈",
    OperatorType.NOT_IN: "∉",
    OperatorType.CONTAINS: "⊃",
    OperatorType.STARTS_WITH: "^",
    OperatorType.ENDS_WITH: "$",
    OperatorType.REGEX: "~",
}
