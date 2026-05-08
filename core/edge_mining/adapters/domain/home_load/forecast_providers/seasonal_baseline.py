"""SeasonalBaseline forecast provider for energy load consumption."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from edge_mining.domain.common import Timestamp, WattHours, Watts
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.exceptions import EnergyLoadForecastProviderError
from edge_mining.domain.home_load.ports import EnergyLoadForecastProviderPort
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    LoadEnergyConsumption,
)
from edge_mining.shared.adapter_configs.home_load import EnergyLoadForecastProviderSeasonalBaselineConfig
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import EnergyLoadForecastAdapterFactory
from edge_mining.shared.logging.port import LoggerPort


class SeasonalBaselineForecastProviderFactory(EnergyLoadForecastAdapterFactory):
    """Factory for creating a SeasonalBaselineForecastProvider instance."""

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> "SeasonalBaselineForecastProvider":
        if config is not None and not isinstance(config, EnergyLoadForecastProviderSeasonalBaselineConfig):
            raise EnergyLoadForecastProviderError(
                "Invalid configuration type for SeasonalBaseline energy load forecast provider. "
                "Expected EnergyLoadForecastProviderSeasonalBaselineConfig."
            )

        hours_ahead = 3
        weeks_lookback = 4
        if isinstance(config, EnergyLoadForecastProviderSeasonalBaselineConfig):
            hours_ahead = config.hours_ahead
            weeks_lookback = config.weeks_lookback

        return SeasonalBaselineForecastProvider(
            hours_ahead=hours_ahead,
            weeks_lookback=weeks_lookback,
            logger=logger,
        )


class SeasonalBaselineForecastProvider(EnergyLoadForecastProviderPort):
    """Forecast by averaging historical power for each (hour_of_day, day_of_week) slot.

    Uses a configurable look-back window (default 4 weeks) to build a profile
    of typical consumption per time slot.  For CONTINUOUS and SEASONAL devices
    this is a strong baseline.

    If insufficient data exists for a particular slot, falls back to the global
    average across all available data.
    """

    def __init__(
        self,
        hours_ahead: int = 3,
        weeks_lookback: int = 4,
        logger: Optional[LoggerPort] = None,
    ):
        super().__init__(forecast_provider_type=EnergyLoadForecastProviderAdapter.SEASONAL_BASELINE)
        self._hours_ahead = hours_ahead
        self._weeks_lookback = weeks_lookback
        self._logger = logger

    def get_consumption_forecast(
        self, consumption_history: LoadEnergyConsumption, hours_ahead: int = 3
    ) -> Optional[LoadEnergyConsumption]:
        effective_hours = self._hours_ahead or hours_ahead
        if effective_hours <= 0:
            return None

        if not consumption_history.intervals:
            return None

        # Build seasonal profile: (day_of_week, hour_of_day) → list of avg_power
        profile: Dict[Tuple[int, int], List[float]] = defaultdict(list)
        for interval in consumption_history.intervals:
            dow = interval.start.weekday()  # 0=Monday
            hod = interval.start.hour
            power = float(interval.avg_power)
            if power > 0:
                profile[(dow, hod)].append(power)

        if not profile:
            return None

        # Global fallback: average of all observed power values
        all_powers = [p for powers in profile.values() for p in powers]
        global_avg = sum(all_powers) / len(all_powers) if all_powers else 0.0

        now = Timestamp(datetime.now(timezone.utc))
        intervals: List[HomeLoadEnergyInterval] = []
        for i in range(effective_hours):
            start = Timestamp(now + timedelta(hours=i))
            end = Timestamp(start + timedelta(hours=1))

            dow = start.weekday()
            hod = start.hour
            slot_values = profile.get((dow, hod))
            if slot_values:
                slot_power = Watts(sum(slot_values) / len(slot_values))
            else:
                slot_power = Watts(global_avg)

            point = HomeLoadPowerPoint(timestamp=start, power=slot_power)
            intervals.append(
                HomeLoadEnergyInterval(
                    start=start,
                    end=end,
                    power_points=[point],
                    energy=WattHours(float(slot_power)),
                )
            )

        forecast = LoadEnergyConsumption(timestamp=now, intervals=intervals)

        if self._logger:
            self._logger.debug(
                f"SeasonalBaselineForecastProvider: {len(profile)} slots, "
                f"{effective_hours}h ahead, total_energy={forecast.total_energy:.0f}Wh"
            )
        return forecast
