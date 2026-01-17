"""Domain services for the Energy Optimization domain."""

import re
from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Union

from edge_mining.domain.policy.common import OperatorType, RuleEngineType
from edge_mining.domain.policy.entities import AutomationRule
from edge_mining.domain.policy.value_objects import DecisionalContext


class RuleValidationService:
    """Domain service for validating automation rule conditions."""

    def validate_conditions(self, conditions: dict) -> Tuple[bool, List[str], List[str]]:
        """
        Validate rule conditions structure and semantics.

        Args:
            conditions: Dictionary representing the rule conditions

        Returns:
            Tuple[bool, List[str], List[str]]: (is_valid, syntax_errors, field_errors)
        """
        return self._validate_recursively(conditions, "")

    def _validate_recursively(self, cond_dict: Any, path: str = "") -> Tuple[bool, List[str], List[str]]:
        """
        Recursively validate condition structure and return validation results.

        Returns:
            tuple: (is_valid, syntax_errors, field_errors)
        """
        syntax_errors: List[str] = []
        field_errors: List[str] = []
        is_valid = True

        if not isinstance(cond_dict, dict):
            syntax_errors.append(f"Invalid condition at {path}: expected dict, got {type(cond_dict).__name__}")
            return False, syntax_errors, field_errors

        # Check if it's a rule condition (has field, operator, value)
        if self._is_rule_condition(cond_dict):
            # Validate field path
            field_path = cond_dict.get("field", "")
            valid_field, field_error = self._validate_field_path(path, field_path)
            if not valid_field:
                field_errors.append(field_error)
                is_valid = False

            # Validate operator
            operator = cond_dict.get("operator")
            if operator is None:
                syntax_errors.append(f"Missing operator at {path}")
                is_valid = False
            else:
                valid_operator, operator_error = self._validate_operator(path, operator)
                if not valid_operator:
                    syntax_errors.append(operator_error)
                    is_valid = False

            # Validate value
            value = cond_dict.get("value")
            if operator is not None:
                valid_value, value_error = self._validate_value(path, value, field_path, operator)
                if not valid_value:
                    syntax_errors.append(value_error)
                    is_valid = False

        # Check logical groups (all_of, any_of, not_)
        elif self._is_logical_group(cond_dict):
            for key, sub_conditions in cond_dict.items():
                if key in ["all_of", "any_of"] and isinstance(sub_conditions, list):
                    for i, sub_cond in enumerate(sub_conditions):
                        sub_valid, sub_syntax_errors, sub_field_errors = self._validate_recursively(
                            sub_cond, f"{path}.{key}[{i}]"
                        )
                        if not sub_valid:
                            is_valid = False
                        syntax_errors.extend(sub_syntax_errors)
                        field_errors.extend(sub_field_errors)
                elif key == "not_" and sub_conditions:
                    sub_valid, sub_syntax_errors, sub_field_errors = self._validate_recursively(
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

    def _is_rule_condition(self, cond_dict: dict) -> bool:
        """Check if dictionary represents a rule condition."""
        return "field" in cond_dict and "operator" in cond_dict and "value" in cond_dict

    def _is_logical_group(self, cond_dict: dict) -> bool:
        """Check if dictionary represents a logical group."""
        return any(k in cond_dict for k in ["all_of", "any_of", "not_"])

    def _validate_field_path(self, path: str, field_path: str) -> Tuple[bool, str]:
        """
        Validate if the given field path is valid within the decisional context.

        Args:
            path: The current path in the condition structure
            field_path: The field path to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not field_path or not isinstance(field_path, str):
            return False, f"Invalid field path at {path}: '{field_path}'"

        # Validate field path exists in DecisionalContext structure
        parts = field_path.split(".")
        current_type = DecisionalContext

        for i, part in enumerate(parts):
            # Check if part is a numeric index (for array access)
            if part.isdigit():
                # Numeric index - extract the item type from the list/array
                if hasattr(current_type, "__origin__"):
                    # Handle List, Sequence, etc.
                    if hasattr(current_type, "__args__") and current_type.__args__:
                        # Get the item type from List[ItemType]
                        current_type = current_type.__args__[0]
                        continue
                    else:
                        return (
                            False,
                            f"Invalid field path at {path}: '{field_path}' - "
                            f"cannot determine item type for array index '{part}'",
                        )
                else:
                    return (
                        False,
                        f"Invalid field path at {path}: '{field_path}' - index '{part}' used on non-array type",
                    )

            if not hasattr(current_type, "__annotations__"):
                if hasattr(current_type, part):
                    attr = getattr(current_type, part)
                    if isinstance(attr, property):
                        if hasattr(attr.fget, "__annotations__") and "return" in attr.fget.__annotations__:
                            field_type = attr.fget.__annotations__["return"]
                            current_type = field_type
                            continue
                        else:
                            if i < len(parts) - 1:
                                return (
                                    False,
                                    f"Invalid field path at {path}: '{field_path}' - "
                                    f"cannot traverse beyond property '{part}' without type annotation",
                                )
                            else:
                                return True, ""
                return (
                    False,
                    f"Invalid field path at {path}: '{field_path}' - cannot traverse beyond '{'.'.join(parts[:i])}'.",
                )

            annotations = current_type.__annotations__

            if part in annotations:
                field_type = annotations[part]

                # Handle Optional types (Union[X, None])
                if hasattr(field_type, "__origin__"):
                    if field_type.__origin__ is Union:
                        args = [arg for arg in field_type.__args__ if arg is not type(None)]
                        if args:
                            field_type = args[0]

                current_type = field_type
            elif hasattr(current_type, part):
                attr = getattr(current_type, part)
                if isinstance(attr, property):
                    if hasattr(attr.fget, "__annotations__") and "return" in attr.fget.__annotations__:
                        field_type = attr.fget.__annotations__["return"]
                        current_type = field_type
                    else:
                        if i < len(parts) - 1:
                            return (
                                False,
                                f"Invalid field path at {path}: '{field_path}' - "
                                f"cannot traverse beyond property '{part}' without type annotation",
                            )
                        else:
                            return True, ""
                else:
                    return (
                        False,
                        f"Invalid field path at {path}: '{field_path}' - '{part}' is not a valid field or property",
                    )
            else:
                available_fields = list(annotations.keys())
                properties = [
                    name for name in dir(current_type) if isinstance(getattr(current_type, name, None), property)
                ]
                available_fields.extend(properties)
                return (
                    False,
                    f"Invalid field path at {path}: '{field_path}' - "
                    f"field '{part}' not found in {current_type.__name__}. "
                    f"Available fields: {', '.join(available_fields)}",
                )

        return True, ""

    def _validate_operator(self, path: str, operator: Union[str, OperatorType]) -> Tuple[bool, str]:
        """
        Validate if the given operator is valid.

        Args:
            path: The current path in the condition structure
            operator: The operator to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
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

    def _validate_value(
        self, path: str, value: Any, field_path: str, operator: Union[str, OperatorType]
    ) -> Tuple[bool, str]:
        """
        Validate if the given value is valid for the specified field and operator.

        Args:
            path: The current path in the condition structure
            value: The value to validate
            field_path: The field path this value is for
            operator: The operator being used

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
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
            if not isinstance(value, (list, tuple)):
                return False, f"Value at {path} must be a list/array for '{operator_type.value}' operator"
            if len(value) == 0:
                return False, f"Value list at {path} cannot be empty for '{operator_type.value}' operator"

        elif operator_type in [OperatorType.CONTAINS, OperatorType.STARTS_WITH, OperatorType.ENDS_WITH]:
            if not isinstance(value, str):
                return False, f"Value at {path} must be a string for '{operator_type.value}' operator"
            if len(value) == 0:
                return False, f"Value string at {path} cannot be empty for '{operator_type.value}' operator"

        elif operator_type == OperatorType.REGEX:
            if not isinstance(value, str):
                return False, f"Value at {path} must be a string (regex pattern) for '{operator_type.value}' operator"
            try:
                re.compile(value)
            except re.error as e:
                return False, f"Invalid regex pattern at {path}: {str(e)}"

        elif operator_type in [OperatorType.GT, OperatorType.GTE, OperatorType.LT, OperatorType.LTE]:
            if not isinstance(value, (int, float, str)):
                return (
                    False,
                    f"Value at {path} must be numeric or comparable for '{operator_type.value}' operator",
                )

        return True, ""


class RuleEngine(ABC):
    """Domain service for rule evaluation."""

    @abstractmethod
    def load_rules(self, rules: List[AutomationRule]) -> None:
        """
        Loads rules. This method should be called before evaluating any rules.
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, context: DecisionalContext) -> bool:
        """
        Evaluates rules based on the given context and returns True if any rule matches.
        If no rules match, returns False.
        This is the core decision-making logic of the rule engine.
        """
        raise NotImplementedError

    @abstractmethod
    def get_type(self) -> RuleEngineType:
        """
        Returns the type of the rule engine.
        """
        raise NotImplementedError
