"""NaiveLastHour forecast provider for energy load consumption."""

from datetime import datetime, timedelta
from typing import List, Optional

from edge_mining.domain.common import Timestamp, Watts, WattHours
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.exceptions import EnergyLoadForecastProviderError
from edge_mining.domain.home_load.ports import EnergyLoadForecastProviderPort
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    LoadEnergyConsumption,
)
from edge_mining.shared.adapter_configs.home_load import EnergyLoadForecastProviderNaiveLastHourConfig
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import EnergyLoadForecastAdapterFactory
from edge_mining.shared.logging.port import LoggerPort


class NaiveLastHourForecastProviderFactory(EnergyLoadForecastAdapterFactory):
    """Factory for creating a NaiveLastHourForecastProvider instance."""

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> "NaiveLastHourForecastProvider":
        if config is not None and not isinstance(config, EnergyLoadForecastProviderNaiveLastHourConfig):
            raise EnergyLoadForecastProviderError(
                "Invalid configuration type for NaiveLastHour energy load forecast provider. "
                "Expected EnergyLoadForecastProviderNaiveLastHourConfig."
            )

        hours_ahead = 3
        if isinstance(config, EnergyLoadForecastProviderNaiveLastHourConfig):
            hours_ahead = config.hours_ahead

        return NaiveLastHourForecastProvider(
            hours_ahead=hours_ahead,
            logger=logger,
        )


class NaiveLastHourForecastProvider(EnergyLoadForecastProviderPort):
    """Forecast by repeating the average power of the last hour for N hours ahead.

    This is the simplest non-trivial baseline: it assumes the near future will
    look like the recent past.  Always available as a fallback even with very
    little historical data (only 1 hour needed).
    """

    def __init__(self, hours_ahead: int = 3, logger: Optional[LoggerPort] = None):
        super().__init__(forecast_provider_type=EnergyLoadForecastProviderAdapter.NAIVE_LAST_HOUR)
        self._hours_ahead = hours_ahead
        self._logger = logger

    def get_consumption_forecast(
        self, consumption_history: LoadEnergyConsumption, hours_ahead: int = 3
    ) -> Optional[LoadEnergyConsumption]:
        effective_hours = self._hours_ahead or hours_ahead
        if effective_hours <= 0:
            return None

        now = Timestamp(datetime.now())

        # Compute baseline from the last hour of history
        last_hour = consumption_history.in_last_hours(1, now=now)
        if last_hour.intervals:
            baseline_power = last_hour.avg_power
        elif consumption_history.intervals:
            # Fallback: use overall average if last hour is empty
            baseline_power = consumption_history.avg_power
        else:
            # No history at all — cannot forecast
            return None

        if float(baseline_power) <= 0:
            baseline_power = Watts(0.0)

        intervals: List[HomeLoadEnergyInterval] = []
        for i in range(effective_hours):
            start = Timestamp(now + timedelta(hours=i))
            end = Timestamp(start + timedelta(hours=1))
            point = HomeLoadPowerPoint(timestamp=start, power=baseline_power)
            intervals.append(
                HomeLoadEnergyInterval(
                    start=start,
                    end=end,
                    power_points=[point],
                    energy=WattHours(float(baseline_power)),
                )
            )

        forecast = LoadEnergyConsumption(timestamp=now, intervals=intervals)

        if self._logger:
            self._logger.debug(
                f"NaiveLastHourForecastProvider: baseline {baseline_power:.0f}W, "
                f"{effective_hours}h ahead, total_energy={forecast.total_energy:.0f}Wh"
            )
        return forecast
