"""API Router for policy domain"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException

from edge_mining.adapters.domain.policy.schemas import (
    AutomationRuleCreateSchema,
    AutomationRuleSchema,
    AutomationRuleUpdateSchema,
    OptimizationPolicyCreateSchema,
    OptimizationPolicySchema,
    OptimizationPolicyUpdateSchema,
    PolicyCheckSchema,
)

# Import dependency injection setup functions
from edge_mining.adapters.infrastructure.api.setup import get_config_service
from edge_mining.application.interfaces import ConfigurationServiceInterface
from edge_mining.domain.common import EntityId
from edge_mining.domain.policy.aggregate_roots import OptimizationPolicy
from edge_mining.domain.policy.common import RuleType
from edge_mining.domain.policy.entities import AutomationRule
from edge_mining.domain.policy.exceptions import (
    PolicyConfigurationError,
    PolicyError,
    PolicyNotFoundError,
    RuleNotFoundError,
)

router = APIRouter()


@router.get("/policies", response_model=List[OptimizationPolicySchema])
async def get_policies_list(
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[OptimizationPolicySchema]:
    """Get a list of all optimization policies"""
    try:
        policies = config_service.list_policies()

        # Convert policies to schema
        policy_schemas: List[OptimizationPolicySchema] = []

        # TODO: Here we are losing metadata information. Consider adding it to the schema if needed.
        for policy in policies:
            policy_schemas.append(OptimizationPolicySchema.from_model(policy))

        return policy_schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.post("/policies", response_model=OptimizationPolicySchema)
async def add_policy(
    policy_schema: OptimizationPolicyCreateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> OptimizationPolicySchema:
    """Add a new optimization policy"""
    try:
        policy_to_add: OptimizationPolicy = policy_schema.to_model()

        # Create policy using configuration service
        new_policy = config_service.create_policy(
            name=policy_to_add.name,
            description=policy_to_add.description or "",
        )

        if policy_to_add.start_rules:
            for rule in policy_to_add.start_rules:
                config_service.add_rule_to_policy(
                    policy_id=new_policy.id,
                    rule_type=RuleType.START,
                    name=rule.name,
                    priority=rule.priority,
                    conditions=rule.conditions,
                    description=rule.description or "",
                )
        if policy_to_add.stop_rules:
            for rule in policy_to_add.stop_rules:
                config_service.add_rule_to_policy(
                    policy_id=new_policy.id,
                    rule_type=RuleType.STOP,
                    name=rule.name,
                    priority=rule.priority,
                    conditions=rule.conditions,
                    description=rule.description or "",
                )

        return OptimizationPolicySchema.from_model(new_policy)

    except PolicyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except PolicyConfigurationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/policies/{policy_id}", response_model=OptimizationPolicySchema)
async def get_policy(
    policy_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> OptimizationPolicySchema:
    """Get a specific optimization policy"""
    try:
        policy = config_service.get_policy(policy_id)
        if not policy:
            raise PolicyNotFoundError()
        return OptimizationPolicySchema.from_model(policy)
    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail="Policy not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.put("/policies/{policy_id}", response_model=OptimizationPolicySchema)
async def update_policy(
    policy_id: EntityId,
    policy_update: OptimizationPolicyUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> OptimizationPolicySchema:
    """Update an existing optimization policy"""
    try:
        # Get existing policy
        existing_policy = config_service.get_policy(policy_id)
        if not existing_policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        # Update policy fields
        updated_policy = config_service.update_policy(
            policy_id=policy_id,
            name=policy_update.name or existing_policy.name,
            description=policy_update.description or existing_policy.description or "",
        )

        return OptimizationPolicySchema.from_model(updated_policy)

    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail="Policy not found") from e
    except PolicyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.delete("/policies/{policy_id}", response_model=OptimizationPolicySchema)
async def delete_policy(
    policy_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> OptimizationPolicySchema:
    """Delete an optimization policy"""
    try:
        # Get policy before deletion
        policy = config_service.get_policy(policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        # Delete policy
        config_service.delete_policy(policy_id)

        return OptimizationPolicySchema.from_model(policy)

    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail="Policy not found") from e
    except PolicyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/policies/{policy_id}/check", response_model=PolicyCheckSchema)
async def check_policy(
    policy_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> PolicyCheckSchema:
    """Check if a policy is valid and can be used."""
    errors = []
    warnings = []
    valid = False
    policy_name = None
    start_rules_count = 0
    stop_rules_count = 0
    enabled_start_rules_count = 0
    enabled_stop_rules_count = 0

    try:
        # Get policy to extract metadata
        policy = config_service.get_policy(policy_id)
        if not policy:
            raise PolicyNotFoundError()

        policy_name = policy.name
        start_rules_count = len(policy.start_rules)
        stop_rules_count = len(policy.stop_rules)
        enabled_start_rules_count = sum(1 for rule in policy.start_rules if rule.enabled)
        enabled_stop_rules_count = sum(1 for rule in policy.stop_rules if rule.enabled)

        # Add warnings for disabled rules
        disabled_start_rules = start_rules_count - enabled_start_rules_count
        disabled_stop_rules = stop_rules_count - enabled_stop_rules_count

        if disabled_start_rules > 0:
            warnings.append(f"{disabled_start_rules} start rule(s) are disabled")
        if disabled_stop_rules > 0:
            warnings.append(f"{disabled_stop_rules} stop rule(s) are disabled")

        # Perform the actual validation
        valid = config_service.check_policy(policy_id)

    except PolicyNotFoundError:
        errors.append("Policy not found")
    except PolicyError as e:
        errors.append(str(e))
        valid = False
    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")

    return PolicyCheckSchema(
        valid=valid,
        policy_id=str(policy_id),
        policy_name=policy_name,
        errors=errors,
        warnings=warnings,
        start_rules_count=start_rules_count,
        stop_rules_count=stop_rules_count,
        enabled_start_rules_count=enabled_start_rules_count,
        enabled_stop_rules_count=enabled_stop_rules_count,
    )


# Policy rule management endpoints
@router.post("/policies/{policy_id}/rules", response_model=AutomationRuleSchema)
async def add_rule_to_policy(
    policy_id: EntityId,
    rule_schema: AutomationRuleCreateSchema,
    rule_type: RuleType,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> AutomationRuleSchema:
    """Add a new rule to an existing optimization policy"""
    try:
        rule_to_add: AutomationRule = rule_schema.to_model()

        new_rule = config_service.add_rule_to_policy(
            policy_id=policy_id,
            rule_type=rule_type,
            name=rule_to_add.name,
            priority=rule_to_add.priority,
            conditions=rule_to_add.conditions,
            description=rule_to_add.description or "",
        )

        return AutomationRuleSchema.from_model(new_rule)

    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail="Policy not found") from e
    except PolicyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/policies/{policy_id}/types/{rule_type}", response_model=List[AutomationRuleSchema])
async def get_policy_rules(
    policy_id: EntityId,
    rule_type: RuleType,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> List[AutomationRuleSchema]:
    """Get all rules of a specific type for a policy"""
    try:
        rules = config_service.get_policy_rules(policy_id, rule_type)
        automation_rule_schemas: List[AutomationRuleSchema] = []
        for rule in rules:
            automation_rule_schemas.append(AutomationRuleSchema.from_model(rule))
        return automation_rule_schemas
    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail="Policy not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/policies/{policy_id}/rules/{rule_id}", response_model=AutomationRuleSchema)
async def get_policy_rule(
    policy_id: EntityId,
    rule_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> AutomationRuleSchema:
    """Get a specific rule for a policy"""
    try:
        rule = config_service.get_policy_rule(policy_id, rule_id)
        if not rule:
            raise RuleNotFoundError()
        return AutomationRuleSchema.from_model(rule)
    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail="Policy not found") from e
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail="Rule not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/policies/{policy_id}/rules/{rule_id}/enable", response_model=AutomationRuleSchema)
async def enable_policy_rule(
    policy_id: EntityId,
    rule_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> AutomationRuleSchema:
    """Enable a specific rule for a policy"""
    try:
        rule: AutomationRule = config_service.enable_policy_rule(policy_id, rule_id)

        return AutomationRuleSchema.from_model(rule)
    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail="Policy not found") from e
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail="Rule not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.get("/policies/{policy_id}/rules/{rule_id}/disable", response_model=AutomationRuleSchema)
async def disable_policy_rule(
    policy_id: EntityId,
    rule_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> AutomationRuleSchema:
    """Disable a specific rule for a policy"""
    try:
        rule: AutomationRule = config_service.disable_policy_rule(policy_id, rule_id)

        return AutomationRuleSchema.from_model(rule)
    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail="Policy not found") from e
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail="Rule not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.put("/policies/{policy_id}/rules/{rule_id}", response_model=AutomationRuleSchema)
async def update_policy_rule(
    policy_id: EntityId,
    rule_id: EntityId,
    rule_schema: AutomationRuleUpdateSchema,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> AutomationRuleSchema:
    """Update a specific rule for a policy"""
    try:
        # Get existing rule
        existing_rule = config_service.get_policy_rule(policy_id, rule_id)
        if not existing_rule:
            raise RuleNotFoundError()

        conditions: dict = existing_rule.conditions
        if rule_schema.conditions is not None:
            conditions = rule_schema.conditions.to_model()

        updated_rule = config_service.update_policy_rule(
            policy_id=policy_id,
            rule_id=rule_id,
            name=rule_schema.name or existing_rule.name,
            priority=rule_schema.priority if rule_schema.priority is not None else existing_rule.priority,
            enabled=rule_schema.enabled if rule_schema.enabled is not None else existing_rule.enabled,
            conditions=conditions,
            description=rule_schema.description or existing_rule.description,
        )

        return AutomationRuleSchema.from_model(updated_rule)

    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail="Policy not found") from e
    except RuleNotFoundError as e:
        raise HTTPException(status_code=404, detail="Rule not found") from e
    except PolicyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.delete("/policies/{policy_id}/rules/{rule_id}", response_model=AutomationRuleSchema)
async def delete_policy_rule(
    policy_id: EntityId,
    rule_id: EntityId,
    config_service: Annotated[ConfigurationServiceInterface, Depends(get_config_service)],
) -> AutomationRuleSchema:
    """Delete a specific rule from a policy"""
    try:
        # Get rule before deletion
        rule = config_service.get_policy_rule(policy_id, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        deleted_rule = config_service.delete_policy_rule(policy_id, rule_id)
        return AutomationRuleSchema.from_model(deleted_rule)

    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail="Policy not found") from e
    except PolicyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e
