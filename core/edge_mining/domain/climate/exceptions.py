"""Collection of Exceptions for the Climate domain."""

from edge_mining.domain.exceptions import DomainError


class ClimateError(DomainError):
    """Base class for climate-related errors."""

    pass


class ClimateZoneError(ClimateError):
    """Errors related to climate zones."""

    pass


class ClimateZoneNotFoundError(ClimateZoneError):
    """Climate zone not found."""

    pass


class ClimateZoneAlreadyExistsError(ClimateZoneError):
    """Climate zone already exists."""

    pass


class ClimateZoneConfigurationError(ClimateZoneError):
    """Climate zone configuration error."""

    pass


class ClimateMonitorError(ClimateError):
    """Errors related to climate monitors."""

    pass


class ClimateMonitorNotFoundError(ClimateMonitorError):
    """Climate monitor not found."""

    pass


class ClimateMonitorAlreadyExistsError(ClimateMonitorError):
    """Climate monitor already exists."""

    pass


class ClimateMonitorConfigurationError(ClimateMonitorError):
    """Climate monitor configuration error."""

    pass
