"""
Dummy adapter (Implementation of Port) that simulates
the home loads forecast for Edge Mining Application
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional

from edge_mining.domain.common import Timestamp, Watts
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.ports import EnergyLoadForecastProviderPort, EnergyLoadHistoryProviderPort
from edge_mining.domain.home_load.value_objects import ConsumptionForecast, HomeLoadEnergyInterval, HomeLoadPowerPoint
from edge_mining.shared.logging.port import LoggerPort


class DummyHomeForecastProvider(EnergyLoadForecastProviderPort):
    """Generates a very basic fake home load forecast."""

    def __init__(
        self,
        load_power_max: float = 500.0,
        history_provider: Optional[EnergyLoadHistoryProviderPort] = None,
        logger: Optional[LoggerPort] = None,
    ):
        """Initializes the DummyHomeForecastProvider."""
        super().__init__(provider_type=EnergyLoadForecastProviderAdapter.DUMMY, history_provider=history_provider)
        self._logger = logger

        self.load_power_max = load_power_max

    def get_home_consumption_forecast(self, hours_ahead: int = 1, hours_back: int = 3) -> Optional[ConsumptionForecast]:
        """Get the home consumption forecast."""
        # Super simple: return a random average load expected soon for next hours_ahead hours.
        if self._logger:
            self._logger.debug(
                f"DummyHomeForecastProvider: "
                f"Generating home load forecast for {hours_ahead} hours ahead "
                f"with max load {self.load_power_max} Wp"
                f"using history data provider: ${type(self.history_provider).__name__ if self.history_provider else None}"
            )

        # Historical period needed for the prediction
        now = Timestamp(datetime.now())
        history_end = now
        history_start = now - timedelta(hours=hours_back)

        # Get history data from history provider, if any
        if self.history_provider:
            historical_intervals = self.history_provider.get_history(start=history_start, end=history_end)

            # Pass historical_intervals to the ML/DL model.
            # For now, we simulate the prediction.
            # prediction_model.predict(historical_intervals, hours_ahead)
            future_intervals = self._simulate_prediction(historical_intervals, hours_ahead, now)

            consumption_forecast = ConsumptionForecast(timestamp=now, intervals=future_intervals)
        else:
            # Generate fake predictions if no history provider is provided

            # Average Watts expected for the next hours
            # For simplicity, we just generate a random load value
            # In a real scenario, this would be based on historical data, time of day, etc.
            # Here we assume a random load between 200W and max load
            avg_load = Watts(random.uniform(200, self.load_power_max))

            home_forecast_points: List[HomeLoadPowerPoint] = []
            for i in range(hours_ahead):  # Forecast for next hours_ahead hours
                future_time = now + timedelta(hours=i)
                home_forecast_point: HomeLoadPowerPoint = HomeLoadPowerPoint(
                    timestamp=Timestamp(future_time), power=avg_load
                )
                home_forecast_points.append(home_forecast_point)

            # Calculate the interval's energy using the factory function
            home_forecast_interval = HomeLoadEnergyInterval.create_from_power_points(
                start=Timestamp(now),
                end=Timestamp(now + timedelta(hours=hours_ahead)),
                power_points=home_forecast_points,
            )

            consumption_forecast = ConsumptionForecast(timestamp=Timestamp(now), intervals=[home_forecast_interval])

        if self._logger:
            self._logger.debug(
                f"DummyHomeForecastProvider: Estimated avg home load power {consumption_forecast.avg_power:.0f}W, "
                f"estimated avg home load energy {consumption_forecast.avg_energy:.0f}Wh "
                f"for next {hours_ahead} hours"
            )
        return consumption_forecast

    def _simulate_prediction(
        self,
        history: List[HomeLoadEnergyInterval],
        hours_ahead: int,
        start_time: Timestamp,
    ) -> List[HomeLoadEnergyInterval]:
        """Dummy prediction logic. Returns the average of the last hour."""
        # This is a placeholder for the future smart model's output.
        # Use the last hour average power.
        avg_power_last_hour = history[-1].avg_power if history else Watts(0)

        # Create future intervals with this simulated power
        intervals = []
        current_start = start_time
        for _ in range(hours_ahead):
            current_end = current_start + timedelta(hours=1)
            # The structure HomeLoadEnergyInterval can be used for both
            # historical data and future (predicted) data.

            #  The model predicts power points. Here we simulate one point.
            power_point = HomeLoadPowerPoint(timestamp=current_start, power=avg_power_last_hour)

            # Calculate the interval's energy using the factory function
            interval = HomeLoadEnergyInterval.create_from_power_points(
                start=current_start,
                end=current_end,
                power_points=[power_point],
            )

            intervals.append(interval)
            current_start = current_end

        return intervals
