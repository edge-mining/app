"""Validation schemas for rule engine operations."""

from typing import Dict, List, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from edge_mining.adapters.domain.policy.schemas import AutomationRuleSchema, LogicalGroupSchema, RuleConditionSchema
from edge_mining.domain.policy.common import OperatorType, RuleEngineType
from edge_mining.domain.policy.services import RuleEngine


class RuleEngineConfigSchema(BaseModel):
    """Schema for rule engine configuration."""

    engine_type: RuleEngineType = Field(default=RuleEngineType.CUSTOM, description="Type of rule engine to use")

    @field_validator("engine_type", mode="before")
    @classmethod
    def validate_engine_type(cls, v: Union[str, RuleEngineType]) -> RuleEngineType:
        """Validate engine type."""
        if isinstance(v, str):
            try:
                return RuleEngineType(v.lower())
            except ValueError as e:
                raise ValueError(f"Invalid engine type: {v}. Must be one of {list(RuleEngineType)}") from e
        elif isinstance(v, RuleEngineType):
            return v
        else:
            raise ValueError("Engine type must be a string or RuleEngineType enum value")

    @classmethod
    def from_model(cls, rule_engine: RuleEngine) -> "RuleEngineConfigSchema":
        """Create schema from rule engine model."""
        return cls(engine_type=rule_engine.get_type())

    model_config = ConfigDict(from_attributes=True)


class RuleEvaluationRequestSchema(BaseModel):
    """Schema for rule evaluation request."""

    rules: List[AutomationRuleSchema] = Field(..., description="List of rules to evaluate")
    context: dict = Field(..., description="Decisional context data for rule evaluation")
    optimization_unit: str = Field(..., description="Optimization unit for the evaluation")

    @field_validator("rules")
    @classmethod
    def validate_rules_not_empty(cls, v: List[AutomationRuleSchema]) -> List[AutomationRuleSchema]:
        """Ensure at least one rule is provided."""
        if not v:
            raise ValueError("At least one rule must be provided for evaluation")
        return v

    @field_validator("context")
    @classmethod
    def validate_context_not_empty(cls, v: dict) -> dict:
        """Ensure context is not empty."""
        if not v:
            raise ValueError("Context must not be empty")
        return v

    model_config = ConfigDict(from_attributes=True)


class RuleValidationRequestSchema(BaseModel):
    """Schema for rule validation request."""

    conditions: Union[LogicalGroupSchema, RuleConditionSchema] = Field(..., description="Rule conditions to validate")

    model_config = ConfigDict(from_attributes=True)


class RuleValidationResultSchema(BaseModel):
    """Schema for rule validation result."""

    is_valid: bool = Field(..., description="Whether the rule conditions are valid")
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors, if any")
    syntax_errors: List[str] = Field(default_factory=list, description="List of syntax errors, if any")
    field_errors: List[str] = Field(default_factory=list, description="List of field path errors, if any")

    model_config = ConfigDict(from_attributes=True)


class OperatorInfoSchema(BaseModel):
    """Schema for operator information."""

    operator: OperatorType = Field(..., description="Operator type")
    symbol: str = Field(..., description="Symbolic representation")
    description: str = Field(..., description="Human-readable description")
    example_usage: str = Field(..., description="Example of how to use this operator")
    supported_types: List[str] = Field(..., description="List of supported data types")

    model_config = ConfigDict(from_attributes=True)


class RuleEngineInfoSchema(BaseModel):
    """Schema for rule engine information and capabilities."""

    supported_engines: List[RuleEngineType] = Field(..., description="List of supported engine types")
    supported_operators: List[OperatorInfoSchema] = Field(..., description="List of supported operators")
    max_nesting_level: int = Field(default=10, description="Maximum nesting level for logical groups")
    supported_field_types: List[str] = Field(
        default=["string", "number", "boolean", "array"], description="Supported field types in context"
    )

    model_config = ConfigDict(from_attributes=True)


OPERATOR_DESCRIPTIONS: Dict[OperatorType, str] = {
    OperatorType.EQ: "Equal to - checks if field value equals the specified value",
    OperatorType.NE: "Not equal to - checks if field value does not equal the specified value",
    OperatorType.GT: "Greater than - checks if field value is greater than the specified value",
    OperatorType.GTE: "Greater than or equal - checks if field value is greater than or equal to specified value",
    OperatorType.LT: "Less than - checks if field value is less than the specified value",
    OperatorType.LTE: "Less than or equal - checks if field value is less than or equal to specified value",
    OperatorType.IN: "In list - checks if field value is contained in the specified list",
    OperatorType.NOT_IN: "Not in list - checks if field value is not contained in the specified list",
    OperatorType.CONTAINS: "Contains - checks if field value contains the specified substring",
    OperatorType.STARTS_WITH: "Starts with - checks if field value starts with the specified string",
    OperatorType.ENDS_WITH: "Ends with - checks if field value ends with the specified string",
    OperatorType.REGEX: "Regular expression - checks if field value matches the specified regex pattern",
}

OPERATOR_EXAMPLES: Dict[OperatorType, str] = {
    OperatorType.EQ: '{"field": "energy_state.battery.percentage", "operator": "eq", "value": 50}',
    OperatorType.NE: '{"field": "miner_state.status", "operator": "ne", "value": "running"}',
    OperatorType.GT: '{"field": "energy_state.grid.power", "operator": "gt", "value": 1000}',
    OperatorType.GTE: '{"field": "forecast.total_energy", "operator": "gte", "value": 5000}',
    OperatorType.LT: '{"field": "energy_state.battery.percentage", "operator": "lt", "value": 20}',
    OperatorType.LTE: '{"field": "tracker_current_hashrate", "operator": "lte", "value": 50}',
    OperatorType.IN: '{"field": "miner_state.status", "operator": "in", "value": ["running", "mining"]}',
    OperatorType.NOT_IN: '{"field": "energy_source.type", "operator": "not_in", "value": ["GRID"]}',
    OperatorType.CONTAINS: '{"field": "miner.name", "operator": "contains", "value": "antminer"}',
    OperatorType.STARTS_WITH: '{"field": "energy_source.name", "operator": "starts_with", "value": "solar"}',
    OperatorType.ENDS_WITH: '{"field": "energy_source.name", "operator": "ends_with", "value": "_panel"}',
    OperatorType.REGEX: '{"field": "miner.model", "operator": "regex", "value": "^S[0-9]+$"}',
}

OPERATOR_TYPES: Dict[OperatorType, List[str]] = {
    OperatorType.EQ: ["string", "number", "boolean"],
    OperatorType.NE: ["string", "number", "boolean"],
    OperatorType.GT: ["number"],
    OperatorType.GTE: ["number"],
    OperatorType.LT: ["number"],
    OperatorType.LTE: ["number"],
    OperatorType.IN: ["string", "number"],
    OperatorType.NOT_IN: ["string", "number"],
    OperatorType.CONTAINS: ["string"],
    OperatorType.STARTS_WITH: ["string"],
    OperatorType.ENDS_WITH: ["string"],
    OperatorType.REGEX: ["string"],
}
