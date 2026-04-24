"""Statsmodels (Holt-Winters / SARIMA) forecast provider for energy load consumption."""

import pickle
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from edge_mining.domain.common import EntityId, Timestamp, WattHours, Watts
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.exceptions import EnergyLoadForecastProviderError
from edge_mining.domain.home_load.ports import EnergyLoadForecastProviderPort, LoadConsumptionModelRepository
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    LoadEnergyConsumption,
)
from edge_mining.shared.adapter_configs.home_load import EnergyLoadForecastProviderStatsmodelsConfig
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import EnergyLoadForecastAdapterFactory
from edge_mining.shared.logging.port import LoggerPort

from .features import fill_missing_hours, intervals_to_hourly_series

# Lazy imports to avoid hard dependency when [ml] extras are not installed.
_HW_AVAILABLE = False
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    _HW_AVAILABLE = True
except ImportError:
    ExponentialSmoothing = None  # type: ignore[misc,assignment]


class StatsmodelsForecastProviderFactory(EnergyLoadForecastAdapterFactory):
    """Factory for creating a StatsmodelsForecastProvider instance."""

    def __init__(self, model_repo: Optional[LoadConsumptionModelRepository] = None) -> None:
        self._model_repo = model_repo

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> "StatsmodelsForecastProvider":
        if config is not None and not isinstance(config, EnergyLoadForecastProviderStatsmodelsConfig):
            raise EnergyLoadForecastProviderError(
                "Invalid configuration type for Statsmodels energy load forecast provider. "
                "Expected EnergyLoadForecastProviderStatsmodelsConfig."
            )

        hours_ahead = 3
        weeks_lookback = 8
        seasonal_periods = 24
        if isinstance(config, EnergyLoadForecastProviderStatsmodelsConfig):
            hours_ahead = config.hours_ahead
            weeks_lookback = config.weeks_lookback
            seasonal_periods = config.seasonal_periods

        return StatsmodelsForecastProvider(
            hours_ahead=hours_ahead,
            weeks_lookback=weeks_lookback,
            seasonal_periods=seasonal_periods,
            model_repo=self._model_repo,
            logger=logger,
        )


class StatsmodelsForecastProvider(EnergyLoadForecastProviderPort):
    """Forecast provider using Holt-Winters exponential smoothing from statsmodels.

    If a pre-trained model exists in ``model_repo`` it will be used.
    Otherwise the provider fits a new model on-the-fly from the supplied history
    (slower, but always works as a fallback).
    """

    def __init__(
        self,
        hours_ahead: int = 3,
        weeks_lookback: int = 8,
        seasonal_periods: int = 24,
        model_repo: Optional[LoadConsumptionModelRepository] = None,
        device_id: Optional[EntityId] = None,
        logger: Optional[LoggerPort] = None,
    ):
        super().__init__(forecast_provider_type=EnergyLoadForecastProviderAdapter.STATSMODELS)
        self._hours_ahead = hours_ahead
        self._weeks_lookback = weeks_lookback
        self._seasonal_periods = seasonal_periods
        self._model_repo = model_repo
        self._device_id = device_id
        self._logger = logger

    def get_consumption_forecast(
        self, consumption_history: LoadEnergyConsumption, hours_ahead: int = 3
    ) -> Optional[LoadEnergyConsumption]:
        if not _HW_AVAILABLE:
            raise EnergyLoadForecastProviderError(
                "statsmodels is not installed. Install the [ml] extras to enable Holt-Winters forecasting."
            )

        effective_hours = self._hours_ahead or hours_ahead
        if effective_hours <= 0:
            return None

        # Try to load a pre-trained model
        predictions = self._predict_from_saved_model(effective_hours)

        # Fallback: fit on-the-fly
        if predictions is None:
            predictions = self._fit_and_predict(consumption_history, effective_hours)

        if predictions is None:
            return None

        return self._build_forecast(predictions)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _predict_from_saved_model(self, hours_ahead: int) -> Optional[List[float]]:
        """Try to load a saved model from the repository and forecast."""
        if self._model_repo is None:
            return None
        model_entity = self._model_repo.get_active_model(
            adapter_type=EnergyLoadForecastProviderAdapter.STATSMODELS,
            device_id=self._device_id,
        )
        if model_entity is None or model_entity.model_bytes is None:
            return None
        try:
            fitted = pickle.loads(model_entity.model_bytes)  # noqa: S301
            forecast = fitted.forecast(hours_ahead)
            return [max(0.0, float(v)) for v in forecast]
        except Exception as exc:
            if self._logger:
                self._logger.warning(f"Failed to use saved statsmodels model: {exc}")
            return None

    def _fit_and_predict(self, consumption_history: LoadEnergyConsumption, hours_ahead: int) -> Optional[List[float]]:
        """Fit a Holt-Winters model on the provided history and forecast."""
        series = intervals_to_hourly_series(consumption_history)
        series = fill_missing_hours(series)

        if len(series) < self._seasonal_periods * 2:
            raise EnergyLoadForecastProviderError(
                f"Insufficient data for Holt-Winters forecasting: {len(series)} hourly data points "
                f"available, but at least {self._seasonal_periods * 2} are required. "
                f"Collect more history before requesting a forecast."
            )

        # Limit lookback
        max_points = self._weeks_lookback * 7 * 24
        if len(series) > max_points:
            series = series[-max_points:]

        powers = [p for _, p in series]

        try:
            model = ExponentialSmoothing(
                powers,
                trend="add",
                seasonal="add",
                seasonal_periods=self._seasonal_periods,
            )
            fitted = model.fit(optimized=True)
            forecast = fitted.forecast(hours_ahead)
            return [max(0.0, float(v)) for v in forecast]
        except Exception as exc:
            raise EnergyLoadForecastProviderError(f"Holt-Winters model fitting failed: {exc}") from exc

    def _build_forecast(self, predictions: List[float]) -> LoadEnergyConsumption:
        """Convert a list of predicted avg_power values to LoadEnergyConsumption."""
        now = Timestamp(datetime.now(timezone.utc))
        intervals: List[HomeLoadEnergyInterval] = []
        for i, power_val in enumerate(predictions):
            start = Timestamp(now + timedelta(hours=i))
            end = Timestamp(start + timedelta(hours=1))
            power = Watts(power_val)
            point = HomeLoadPowerPoint(timestamp=start, power=power)
            intervals.append(
                HomeLoadEnergyInterval(
                    start=start,
                    end=end,
                    power_points=[point],
                    energy=WattHours(power_val),
                )
            )
        return LoadEnergyConsumption(timestamp=now, intervals=intervals)
