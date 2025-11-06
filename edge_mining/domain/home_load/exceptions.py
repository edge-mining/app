"""Collection of Exceptions."""

from edge_mining.domain.exceptions import DomainError


class HomeLoadError(DomainError):
    """Base class for home load-related errors."""

    pass


class HomeLoadsProfileAlreadyExistsError(HomeLoadError):
    """Home Loads Profile already exists."""

    pass


class HomeLoadsProfileNotFoundError(HomeLoadError):
    """Home Loads Profile not found."""

    pass


class HomeLoadsProfileAddDeviceError(HomeLoadError):
    """Error adding device to Home Loads Profile."""

    pass


class HomeLoadsProfileDeviceNotFoundError(HomeLoadError):
    """Load Device not found in Home Loads Profile."""

    pass


class HomeLoadsProfileRemoveDeviceError(HomeLoadError):
    """Error removing device from Home Loads Profile."""

    pass


class HomeForecastError(HomeLoadError):
    """Base class for home forecast-specific errors."""

    pass


class HomeForecastProviderError(HomeForecastError):
    """Errors related to home forecast provider."""

    pass


class HomeForecastProviderNotFoundError(HomeForecastProviderError):
    """Home Forecast Provider not found."""

    pass


class HomeForecastProviderAlreadyExistsError(HomeForecastProviderError):
    """Home Forecast Provider already exists."""

    pass


class HomeForecastProviderConfigurationError(HomeForecastProviderError):
    """Error with the configuration."""

    pass


class EnergyLoadHistoryProviderError(HomeForecastError):
    """Errors related to energy load history provider."""

    pass


class EnergyLoadHistoryProviderConfigurationError(EnergyLoadHistoryProviderError):
    """Error with the configuration."""

    pass
