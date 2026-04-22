"""
Dummy adapter (Implementation of Port) that simulates
the home loads forecast for Edge Mining Application.
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional

from edge_mining.domain.common import Timestamp, WattHours, Watts
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.ports import EnergyLoadForecastProviderPort
from edge_mining.domain.home_load.value_objects import HomeLoadEnergyInterval, HomeLoadPowerPoint, LoadEnergyConsumption
from edge_mining.shared.logging.port import LoggerPort


class DummyEnergyLoadForecastProvider(EnergyLoadForecastProviderPort):
    """Generates a very basic fake energy load forecast.

    Ignores historical data and emits a random average load per hour bounded
    by ``load_power_max``. Useful as a placeholder until an ML/DL forecaster
    is wired in.
    """

    def __init__(
        self,
        load_power_max: float = 500.0,
        logger: Optional[LoggerPort] = None,
    ):
        super().__init__(forecast_provider_type=EnergyLoadForecastProviderAdapter.DUMMY)
        self._logger = logger
        self.load_power_max = load_power_max

    def get_consumption_forecast(
        self, consumption_history: LoadEnergyConsumption, hours_ahead: int = 3
    ) -> Optional[LoadEnergyConsumption]:
        """Produce a naive forecast of hourly consumption over ``hours_ahead``."""
        if hours_ahead <= 0:
            return None

        now = Timestamp(datetime.now())

        if consumption_history.intervals:
            # Simple baseline: replay the average of the last observed hour.
            baseline_power = consumption_history.intervals[-1].avg_power
        else:
            baseline_power = Watts(random.uniform(200.0, self.load_power_max))

        intervals: List[HomeLoadEnergyInterval] = []
        for i in range(hours_ahead):
            start = now + timedelta(hours=i)
            end = start + timedelta(hours=1)
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
                f"DummyEnergyLoadForecastProvider: baseline {baseline_power:.0f}W, "
                f"{hours_ahead}h ahead, avg_power={forecast.avg_power:.0f}W"
            )

        return forecast
