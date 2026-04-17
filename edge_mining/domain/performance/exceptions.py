"""Collection of Exceptions."""

from edge_mining.domain.exceptions import DomainError


class MiningPerformanceTrackerError(DomainError):
    """Base class for performance tracker-specific errors."""

    pass


class MiningPerformanceTrackerNotFoundError(MiningPerformanceTrackerError):
    """Performance Tracker not found."""

    pass


class MiningPerformanceTrackerAlreadyExistsError(MiningPerformanceTrackerError):
    """Performance Tracker already exists."""

    pass


class MiningPerformanceTrackerConfigurationError(MiningPerformanceTrackerError):
    """Error with the configuration."""

    pass


class MiningPoolUnreachableError(MiningPerformanceTrackerError):
    """The mining pool API could not be reached (timeout, network error, 5xx)."""

    pass


class MiningPoolAuthError(MiningPerformanceTrackerError):
    """Authentication against the mining pool API failed (401/403)."""

    pass


class MiningPoolResponseError(MiningPerformanceTrackerError):
    """The mining pool API returned an unexpected or malformed response."""

    pass
