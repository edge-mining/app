"""API Router for rule engine operations."""

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException

# Import dependency injection setup functions
from edge_mining.adapters.infrastructure.api.setup import (
    get_adapter_service,
    get_config_service,
    get_optimization_service,
)
from edge_mining.adapters.infrastructure.rule_engine.schemas import (
    OPERATOR_DESCRIPTIONS,
    OPERATOR_EXAMPLES,
    OPERATOR_TYPES,
    OperatorInfoSchema,
    RuleEngineConfigSchema,
    RuleEngineInfoSchema,
    RuleEvaluationRequestSchema,
    RuleValidationRequestSchema,
    RuleValidationResultSchema,
)
from edge_mining.application.interfaces import (
    AdapterServiceInterface,
    ConfigurationServiceInterface,
    OptimizationServiceInterface,
)
from edge_mining.domain.common import EntityId
from edge_mining.domain.policy.common import OPERATOR_SYMBOLS, OperatorType, RuleEngineType
from edge_mining.domain.policy.entities import AutomationRule
from edge_mining.domain.policy.value_objects import DecisionalContext

router = APIRouter()


@router.get("/rule-engine/config", response_model=RuleEngineConfigSchema)
async def get_rule_engine_config(
    adapter_service: Annotated[AdapterServiceInterface, Depends(get_adapter_service)],
) -> RuleEngineConfigSchema:
    """Get current rule engine configuration."""
    rule_engine = adapter_service.get_rule_engine()

    if rule_engine:
        return RuleEngineConfigSchema.from_model(rule_engine)
    else:
        raise HTTPException(status_code=404, detail="Rule engine not configured")


@router.get("/rule-engine/info", response_model=RuleEngineInfoSchema)
async def get_rule_engine_info() -> RuleEngineInfoSchema:
    """Get information about rule engine capabilities and supported features."""

    # Create operator info for all supported operators
    operator_infos = []

    for operator in OperatorType:
        operator_infos.append(
            OperatorInfoSchema(
                operator=operator,
                symbol=OPERATOR_SYMBOLS.get(operator, "?"),
                description=OPERATOR_DESCRIPTIONS.get(operator, "No description available"),
                example_usage=OPERATOR_EXAMPLES.get(operator, "No example available"),
                supported_types=OPERATOR_TYPES.get(operator, ["any"]),
            )
        )

    return RuleEngineInfoSchema(
        supported_engines=list(RuleEngineType),
        supported_operators=operator_infos,
        max_nesting_level=10,
        supported_field_types=["string", "number", "boolean", "array", "object"],
    )


@router.post("/rule-engine/evaluate", response_model=bool)
async def evaluate_rules(
    evaluation_request: RuleEvaluationRequestSchema,
    optimization_service: Annotated[OptimizationServiceInterface, Depends(get_optimization_service)],
) -> bool:
    """Evaluate a set of rules against the provided context."""

    try:
        # Convert schema rules to domain entities
        automation_rules: List[AutomationRule] = []
        for rule_schema in evaluation_request.rules:
            automation_rules.append(rule_schema.to_model())

        context: Optional[DecisionalContext] = optimization_service.get_decisional_context(
            EntityId(uuid.UUID(evaluation_request.optimization_unit))
        )

        if not context:
            raise ValueError("Decisional context could not be created")

        return optimization_service.test_rules(automation_rules, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error during evaluation: {str(e)}") from e


@router.post("/rule-engine/validate", response_model=RuleValidationResultSchema)
async def validate_rule_conditions(
    request: RuleValidationRequestSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> RuleValidationResultSchema:
    """Validate rule conditions for syntax and field path correctness."""

    validation_errors = []
    syntax_errors: List[str] = []
    field_errors: List[str] = []
    is_valid = True

    try:
        # Basic validation of conditions structure
        conditions_dict = request.conditions.to_model()

        # Validate using ConfigurationService
        is_valid, syntax_errors, field_errors = config_service.validate_rule_conditions(conditions_dict)

        # Collect all validation errors
        validation_errors = syntax_errors + field_errors

    except Exception as e:
        is_valid = False
        validation_errors.append(f"Validation failed: {str(e)}")

    return RuleValidationResultSchema(
        is_valid=is_valid,
        validation_errors=validation_errors,
        syntax_errors=syntax_errors,
        field_errors=field_errors,
    )
