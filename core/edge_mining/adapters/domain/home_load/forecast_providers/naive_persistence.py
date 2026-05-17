"""NaivePersistence forecast provider for energy load consumption.

Forecasts by repeating the consumption profile from the *same hours of the
previous day*.  Unlike ``NaiveLastHour`` (which repeats a single recent average),
this provider preserves the intra-day shape of the load profile — capturing
morning peaks, afternoon dips, etc.

Inspired by the "naive/persistence" method used in EMHASS.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from edge_mining.domain.common import Timestamp, WattHours, Watts
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.exceptions import EnergyLoadForecastProviderError
from edge_mining.domain.home_load.ports import EnergyLoadForecastProviderPort
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    LoadEnergyConsumption,
)
from edge_mining.shared.adapter_configs.home_load import EnergyLoadForecastProviderNaivePersistenceConfig
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import EnergyLoadForecastAdapterFactory
from edge_mining.shared.logging.port import LoggerPort


class NaivePersistenceForecastProviderFactory(EnergyLoadForecastAdapterFactory):
    """Factory for creating a NaivePersistenceForecastProvider instance."""

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> "NaivePersistenceForecastProvider":
        if config is not None and not isinstance(config, EnergyLoadForecastProviderNaivePersistenceConfig):
            raise EnergyLoadForecastProviderError(
                "Invalid configuration type for NaivePersistence energy load forecast provider. "
                "Expected EnergyLoadForecastProviderNaivePersistenceConfig."
            )

        hours_ahead = 24
        delta_days = 1
        if isinstance(config, EnergyLoadForecastProviderNaivePersistenceConfig):
            hours_ahead = config.hours_ahead
            delta_days = config.delta_days

        return NaivePersistenceForecastProvider(
            hours_ahead=hours_ahead,
            delta_days=delta_days,
            logger=logger,
        )


class NaivePersistenceForecastProvider(EnergyLoadForecastProviderPort):
    """Forecast by repeating the load profile from ``delta_days`` ago.

    For each future hour, this provider looks up the corresponding hour from
    ``delta_days`` days in the past and uses that power value.  If a specific
    hour slot is missing from history, the overall history average is used as
    fallback.
    """

    def __init__(
        self,
        hours_ahead: int = 24,
        delta_days: int = 1,
        logger: Optional[LoggerPort] = None,
    ):
        super().__init__(forecast_provider_type=EnergyLoadForecastProviderAdapter.NAIVE_PERSISTENCE)
        self._hours_ahead = hours_ahead
        self._delta_days = delta_days
        self._logger = logger

    @property
    def min_required_history_hours(self) -> int:  # noqa: D102
        return self._delta_days * 24

    def get_consumption_forecast(
        self, consumption_history: LoadEnergyConsumption, hours_ahead: int = 24
    ) -> Optional[LoadEnergyConsumption]:
        effective_hours = self._hours_ahead
        if effective_hours <= 0:
            return None

        if not consumption_history.intervals:
            return None

        now = Timestamp(datetime.now(timezone.utc))
        fallback_power = consumption_history.avg_power

        # Build an hour-of-day → power lookup from the reference day
        reference_date = (now - timedelta(days=self._delta_days)).date()
        hour_power: dict[int, float] = {}
        for interval in consumption_history.intervals:
            if interval.start.date() == reference_date:
                hour_power[interval.start.hour] = float(interval.avg_power)

        intervals: List[HomeLoadEnergyInterval] = []
        for i in range(effective_hours):
            start = Timestamp(now + timedelta(hours=i))
            end = Timestamp(start + timedelta(hours=1))
            target_hour = start.hour

            power = Watts(hour_power.get(target_hour, float(fallback_power)))
            if float(power) < 0:
                power = Watts(0.0)

            point = HomeLoadPowerPoint(timestamp=start, power=power)
            intervals.append(
                HomeLoadEnergyInterval(
                    start=start,
                    end=end,
                    power_points=[point],
                    energy=WattHours(float(power)),
                )
            )

        forecast = LoadEnergyConsumption(timestamp=now, intervals=intervals)

        if self._logger:
            self._logger.debug(
                f"NaivePersistenceForecastProvider: delta_days={self._delta_days}, "
                f"{effective_hours}h ahead, total_energy={forecast.total_energy:.0f}Wh"
            )
        return forecast
