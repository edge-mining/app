"""Collection of Exceptions."""

from edge_mining.domain.exceptions import DomainError


class PolicyError(DomainError):
    """Errors related to optimization policies."""

    pass


class PolicyNotFoundError(PolicyError):
    """Optimization policy not found."""

    pass


class PolicyAlreadyExistsError(PolicyError):
    """Optimization policy already exists."""

    pass


class InvalidRuleError(PolicyError):
    """Invalid automation rule."""

    pass


class RuleNotFoundError(PolicyError):
    """Automation rule not found."""

    pass


class PolicyConfigurationError(PolicyError):
    """Error in policy configuration."""

    pass


class RuleEngineError(Exception):
    """Base exception for rule engine errors."""

    pass


class RuleLoadError(RuleEngineError):
    """Exception raised when rules fail to load."""

    pass


class RuleEvaluationError(RuleEngineError):
    """Exception raised during rule evaluation."""

    pass


class RuleValidationError(RuleEngineError):
    """Exception raised during rule validation."""

    pass


class UnsupportedConditionError(RuleEngineError):
    """Exception raised when an unsupported condition is used."""

    pass


class UnsupportedOperatorError(RuleEngineError):
    """Exception raised when an unsupported operator is used."""

    pass


class InvalidContextError(RuleEngineError):
    """Exception raised when the decisional context is invalid."""

    pass
