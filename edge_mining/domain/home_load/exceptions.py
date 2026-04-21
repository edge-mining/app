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


class EnergyLoadForecastError(HomeLoadError):
    """Base class for energy load forecast-specific errors."""

    pass


class EnergyLoadForecastProviderError(EnergyLoadForecastError):
    """Errors related to energy load forecast provider."""

    pass


class EnergyLoadForecastProviderNotFoundError(EnergyLoadForecastProviderError):
    """Energy Load Forecast Provider not found."""

    pass


class EnergyLoadForecastProviderAlreadyExistsError(EnergyLoadForecastProviderError):
    """Energy Load Forecast Provider already exists."""

    pass


class EnergyLoadForecastProviderConfigurationError(EnergyLoadForecastProviderError):
    """Error with the configuration."""

    pass


class EnergyLoadHistoryProviderError(EnergyLoadForecastError):
    """Errors related to energy load history provider."""

    pass


class EnergyLoadHistoryProviderConfigurationError(EnergyLoadHistoryProviderError):
    """Error with the configuration."""

    pass
