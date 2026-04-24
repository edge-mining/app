"""TypicalProfile forecast provider for energy load consumption.

Forecasts by computing the "typical" consumption profile: historical data is
grouped by **(month, day_of_week, hour_of_day)** and averaged.  This captures
both weekly patterns (workday vs. weekend) *and* seasonal variation (summer vs.
winter) — more granular than ``SeasonalBaseline`` which only uses (dow, hour).
"""

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
from edge_mining.shared.adapter_configs.home_load import EnergyLoadForecastProviderTypicalProfileConfig
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import EnergyLoadForecastAdapterFactory
from edge_mining.shared.logging.port import LoggerPort


class TypicalProfileForecastProviderFactory(EnergyLoadForecastAdapterFactory):
    """Factory for creating a TypicalProfileForecastProvider instance."""

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> "TypicalProfileForecastProvider":
        if config is not None and not isinstance(config, EnergyLoadForecastProviderTypicalProfileConfig):
            raise EnergyLoadForecastProviderError(
                "Invalid configuration type for TypicalProfile energy load forecast provider. "
                "Expected EnergyLoadForecastProviderTypicalProfileConfig."
            )

        hours_ahead = 24
        weeks_lookback = 8
        if isinstance(config, EnergyLoadForecastProviderTypicalProfileConfig):
            hours_ahead = config.hours_ahead
            weeks_lookback = config.weeks_lookback

        return TypicalProfileForecastProvider(
            hours_ahead=hours_ahead,
            weeks_lookback=weeks_lookback,
            logger=logger,
        )


class TypicalProfileForecastProvider(EnergyLoadForecastProviderPort):
    """Forecast by averaging historical power for each (month, dow, hour) slot.

    Compared to ``SeasonalBaseline`` (which groups by ``(dow, hour)`` only),
    this provider also factors in the **month**, so the profile naturally adapts
    to seasonal consumption changes (heating in winter, AC in summer, etc.).

    If insufficient data exists for the exact (month, dow, hour) triplet, the
    provider falls back to (dow, hour) and then to the global average.
    """

    def __init__(
        self,
        hours_ahead: int = 24,
        weeks_lookback: int = 8,
        logger: Optional[LoggerPort] = None,
    ):
        super().__init__(forecast_provider_type=EnergyLoadForecastProviderAdapter.TYPICAL_PROFILE)
        self._hours_ahead = hours_ahead
        self._weeks_lookback = weeks_lookback
        self._logger = logger

    @property
    def min_required_history_hours(self) -> int:  # noqa: D102
        return self._weeks_lookback * 168  # weeks × 168 h/week

    def get_consumption_forecast(
        self, consumption_history: LoadEnergyConsumption, hours_ahead: int = 24
    ) -> Optional[LoadEnergyConsumption]:
        effective_hours = self._hours_ahead
        if effective_hours <= 0:
            return None

        if not consumption_history.intervals:
            return None

        # Build profiles at two granularity levels
        # Level 1 (precise): (month, dow, hour) → list[power]
        profile_mdh: Dict[Tuple[int, int, int], List[float]] = defaultdict(list)
        # Level 2 (fallback): (dow, hour) → list[power]
        profile_dh: Dict[Tuple[int, int], List[float]] = defaultdict(list)

        for interval in consumption_history.intervals:
            month = interval.start.month
            dow = interval.start.weekday()
            hod = interval.start.hour
            power = float(interval.avg_power)
            if power >= 0:
                profile_mdh[(month, dow, hod)].append(power)
                profile_dh[(dow, hod)].append(power)

        if not profile_dh:
            return None

        # Global fallback
        all_powers = [p for powers in profile_dh.values() for p in powers]
        global_avg = sum(all_powers) / len(all_powers) if all_powers else 0.0

        now = Timestamp(datetime.now(timezone.utc))
        intervals: List[HomeLoadEnergyInterval] = []
        for i in range(effective_hours):
            start = Timestamp(now + timedelta(hours=i))
            end = Timestamp(start + timedelta(hours=1))

            month = start.month
            dow = start.weekday()
            hod = start.hour

            # Try precise (month, dow, hour) first, then (dow, hour), then global
            mdh_values = profile_mdh.get((month, dow, hod))
            if mdh_values:
                slot_power = Watts(sum(mdh_values) / len(mdh_values))
            else:
                dh_values = profile_dh.get((dow, hod))
                if dh_values:
                    slot_power = Watts(sum(dh_values) / len(dh_values))
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
                f"TypicalProfileForecastProvider: {len(profile_mdh)} (m,d,h) slots, "
                f"{len(profile_dh)} (d,h) slots, "
                f"{effective_hours}h ahead, total_energy={forecast.total_energy:.0f}Wh"
            )
        return forecast
