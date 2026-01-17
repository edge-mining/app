"""Utility functions for rule engine Fast API operations."""

from typing import Any, List, Tuple, Union

from edge_mining.adapters.infrastructure.rule_engine.common import OperatorType
from edge_mining.adapters.infrastructure.rule_engine.schemas import LogicalGroupSchema, RuleConditionSchema
from edge_mining.domain.policy.value_objects import DecisionalContext


def validate_condition_recursively(cond_dict, path="") -> Tuple[bool, List[str], List[str]]:
    """
    Recursively validate condition structure and return validation results.

    Returns:
        tuple: (is_valid, syntax_errors, field_errors)
    """
    syntax_errors = []
    field_errors = []
    is_valid = True

    if isinstance(cond_dict, dict):
        # Check if it's a rule condition
        if all(k in cond_dict for k in RuleConditionSchema.model_fields.keys()):
            # Validate field path
            field_path = cond_dict.get("field", "")
            valid_field, field_error = validate_condition__field_path(path, field_path)
            if not valid_field:
                field_errors.append(field_error)
                is_valid = False

            # Validate operator
            operator = cond_dict.get("operator")
            if operator is None:
                syntax_errors.append(f"Missing operator at {path}")
                is_valid = False
            else:
                valid_operator, operator_error = validate_condition__operator(path, operator)
                if not valid_operator:
                    syntax_errors.append(operator_error)
                    is_valid = False

            # Validate value
            value = cond_dict.get("value")
            if operator is not None:
                valid_value, value_error = validate_condition__value(path, value, field_path, operator)
                if not valid_value:
                    syntax_errors.append(value_error)
                    is_valid = False

        # Check logical groups
        elif any(k in cond_dict for k in LogicalGroupSchema.model_fields.keys()):
            for key, sub_conditions in cond_dict.items():
                if key in ["all_of", "any_of"] and isinstance(sub_conditions, list):
                    for i, sub_cond in enumerate(sub_conditions):
                        sub_valid, sub_syntax_errors, sub_field_errors = validate_condition_recursively(
                            sub_cond, f"{path}.{key}[{i}]"
                        )
                        if not sub_valid:
                            is_valid = False
                        syntax_errors.extend(sub_syntax_errors)
                        field_errors.extend(sub_field_errors)
                elif key == "not_" and sub_conditions:
                    sub_valid, sub_syntax_errors, sub_field_errors = validate_condition_recursively(
                        sub_conditions, f"{path}.{key}"
                    )
                    if not sub_valid:
                        is_valid = False
                    syntax_errors.extend(sub_syntax_errors)
                    field_errors.extend(sub_field_errors)

        else:
            syntax_errors.append(f"Invalid condition structure at {path}: {cond_dict}")
            is_valid = False

    return is_valid, syntax_errors, field_errors


def validate_condition__field_path(path: str, field_path: str) -> Tuple[bool, str]:
    """
    Validate if the given field path is valid within the decisional context.

    Args:
        path (str): The current path in the condition structure, expressed as a string with dot notation.
        field_path (str): The field path to validate.
    Returns:
        Tuple[bool, str]: (is_valid, error_message). Returns (True, "") if valid.
    """
    if not field_path or not isinstance(field_path, str):
        return False, f"Invalid field path at {path}: '{field_path}'"

    # Validate field path exists in DecisionalContext structure
    parts = field_path.split(".")
    current_type = DecisionalContext

    for i, part in enumerate(parts):
        # Check if the current type has the attribute (either in annotations or as a property)
        if not hasattr(current_type, "__annotations__"):
            # Check if it's a property or method
            if hasattr(current_type, part):
                attr = getattr(current_type, part)
                # If it's a property, get its return type from the property object
                if isinstance(attr, property):
                    # Properties don't have direct type annotations, so we allow them but can't traverse further
                    # We'll need to check the property's return type annotation if available
                    if hasattr(attr.fget, "__annotations__") and "return" in attr.fget.__annotations__:
                        field_type = attr.fget.__annotations__["return"]
                        current_type = field_type
                        continue
                    else:
                        # Property exists but we can't determine its type for further traversal
                        if i < len(parts) - 1:
                            return (
                                False,
                                f"Invalid field path at {path}: '{field_path}' - cannot traverse beyond property '{part}' without type annotation",
                            )
                        else:
                            # It's the last part, property exists
                            return True, ""
            return (
                False,
                f"Invalid field path at {path}: '{field_path}' - cannot traverse beyond '{'.'.join(parts[:i])}'",
            )

        annotations = current_type.__annotations__

        # Check in annotations first
        if part in annotations:
            # Get the type of the field to continue traversal
            field_type = annotations[part]

            # Handle Optional types (e.g., Optional[Miner])
            if hasattr(field_type, "__origin__"):
                # For Union types (Optional is Union[X, None])
                if field_type.__origin__ is Union:
                    # Get the non-None type
                    args = [arg for arg in field_type.__args__ if arg is not type(None)]
                    if args:
                        field_type = args[0]

            # Update current_type for next iteration
            current_type = field_type
        # Check if it's a property
        elif hasattr(current_type, part):
            attr = getattr(current_type, part)
            if isinstance(attr, property):
                # If it's a property, try to get its return type
                if hasattr(attr.fget, "__annotations__") and "return" in attr.fget.__annotations__:
                    field_type = attr.fget.__annotations__["return"]
                    current_type = field_type
                else:
                    # Property exists but we can't determine its type for further traversal
                    if i < len(parts) - 1:
                        return (
                            False,
                            f"Invalid field path at {path}: '{field_path}' - cannot traverse beyond property '{part}' without type annotation",
                        )
                    else:
                        # It's the last part, property exists
                        return True, ""
            else:
                return (
                    False,
                    f"Invalid field path at {path}: '{field_path}' - '{part}' is not a valid field or property",
                )
        else:
            # Get available fields for better error message
            available_fields = list(annotations.keys())
            # Also add properties
            properties = [name for name in dir(current_type) if isinstance(getattr(current_type, name, None), property)]
            available_fields.extend(properties)
            return (
                False,
                f"Invalid field path at {path}: '{field_path}' - field '{part}' not found in {current_type.__name__}. Available fields: {', '.join(available_fields)}",
            )

    return True, ""


def validate_condition__operator(path: str, operator: Union[str, OperatorType]) -> Tuple[bool, str]:
    """
    Validate if the given operator is valid.

    Args:
        path (str): The current path in the condition structure.
        operator (Union[str, OperatorType]): The operator to validate.
    Returns:
        Tuple[bool, str]: (is_valid, error_message). Returns (True, "") if valid.
    """
    try:
        if isinstance(operator, str):
            if operator.lower() not in [op.value for op in OperatorType]:
                raise ValueError(f"Invalid operator: {operator}")
        elif not isinstance(operator, OperatorType):
            raise ValueError(f"Invalid operator type: {type(operator)}")
    except ValueError:
        return False, f"Invalid operator at {path}: '{operator}'"

    return True, ""


def validate_condition__value(
    path: str, value: Any, field_path: str, operator: Union[str, OperatorType]
) -> Tuple[bool, str]:
    """
    Validate if the given value is valid for the specified field and operator.

    Args:
        path (str): The current path in the condition structure.
        value (any): The value to validate.
        field_path (str): The field path this value is for.
        operator (Union[str, OperatorType]): The operator being used.
    Returns:
        Tuple[bool, str]: (is_valid, error_message). Returns (True, "") if valid.
    """
    # Check if value is None
    if value is None:
        return False, f"Missing or null value at {path}"

    # Normalize operator
    if isinstance(operator, str):
        try:
            operator_type = OperatorType(operator.lower())
        except ValueError:
            return False, f"Cannot validate value: invalid operator '{operator}' at {path}"
    else:
        operator_type = operator

    # Validate value type based on operator
    if operator_type in [OperatorType.IN, OperatorType.NOT_IN]:
        # Value should be a list or array
        if not isinstance(value, (list, tuple)):
            return False, f"Value at {path} must be a list/array for '{operator_type.value}' operator"
        if len(value) == 0:
            return False, f"Value list at {path} cannot be empty for '{operator_type.value}' operator"

    elif operator_type in [OperatorType.CONTAINS, OperatorType.STARTS_WITH, OperatorType.ENDS_WITH]:
        # Value should be a string
        if not isinstance(value, str):
            return False, f"Value at {path} must be a string for '{operator_type.value}' operator"
        if len(value) == 0:
            return False, f"Value string at {path} cannot be empty for '{operator_type.value}' operator"

    elif operator_type == OperatorType.REGEX:
        # Value should be a valid regex pattern string
        if not isinstance(value, str):
            return False, f"Value at {path} must be a string (regex pattern) for '{operator_type.value}' operator"
        # TODO: Optionally validate regex pattern syntax
        import re

        try:
            re.compile(value)
        except re.error as e:
            return False, f"Invalid regex pattern at {path}: {str(e)}"

    elif operator_type in [OperatorType.GT, OperatorType.GTE, OperatorType.LT, OperatorType.LTE]:
        # Value should be numeric (int, float) or comparable
        if not isinstance(value, (int, float, str)):
            return False, f"Value at {path} must be numeric or comparable for '{operator_type.value}' operator"

    # TODO: Add field-specific validation based on field_path
    # This should check if the value type matches the expected type for the field in decisional context

    return True, ""
