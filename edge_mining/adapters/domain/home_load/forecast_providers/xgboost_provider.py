"""XGBoost forecast provider for energy load consumption."""

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
from edge_mining.shared.adapter_configs.home_load import EnergyLoadForecastProviderXGBoostConfig
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import EnergyLoadForecastAdapterFactory
from edge_mining.shared.logging.port import LoggerPort

from .features import (
    build_calendar_features,
    fill_missing_hours,
    intervals_to_hourly_series,
    prepare_supervised_dataset,
)

# Lazy imports
_XGB_AVAILABLE = False
try:
    import xgboost as xgb

    _XGB_AVAILABLE = True
except ImportError:
    xgb = None  # type: ignore[assignment]


class XGBoostForecastProviderFactory(EnergyLoadForecastAdapterFactory):
    """Factory for creating an XGBoostForecastProvider instance."""

    def __init__(self, model_repo: Optional[LoadConsumptionModelRepository] = None) -> None:
        self._model_repo = model_repo

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> "XGBoostForecastProvider":
        if config is not None and not isinstance(config, EnergyLoadForecastProviderXGBoostConfig):
            raise EnergyLoadForecastProviderError(
                "Invalid configuration type for XGBoost energy load forecast provider. "
                "Expected EnergyLoadForecastProviderXGBoostConfig."
            )

        hours_ahead = 3
        weeks_lookback = 8
        n_estimators = 100
        max_depth = 6
        learning_rate = 0.1
        if isinstance(config, EnergyLoadForecastProviderXGBoostConfig):
            hours_ahead = config.hours_ahead
            weeks_lookback = config.weeks_lookback
            n_estimators = config.n_estimators
            max_depth = config.max_depth
            learning_rate = config.learning_rate

        return XGBoostForecastProvider(
            hours_ahead=hours_ahead,
            weeks_lookback=weeks_lookback,
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            model_repo=self._model_repo,
            logger=logger,
        )


class XGBoostForecastProvider(EnergyLoadForecastProviderPort):
    """Forecast provider using XGBoost gradient boosting.

    Uses calendar features (hour, day-of-week, is-weekend, month) and lag
    features (1h, 2h, 3h, 24h, 168h) to predict avg_power per future hour.

    If a pre-trained model exists in ``model_repo`` it is used.
    Otherwise, fits on-the-fly from the supplied history.
    """

    def __init__(
        self,
        hours_ahead: int = 3,
        weeks_lookback: int = 8,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        model_repo: Optional[LoadConsumptionModelRepository] = None,
        device_id: Optional[EntityId] = None,
        logger: Optional[LoggerPort] = None,
    ):
        super().__init__(forecast_provider_type=EnergyLoadForecastProviderAdapter.XGBOOST)
        self._hours_ahead = hours_ahead
        self._weeks_lookback = weeks_lookback
        self._n_estimators = n_estimators
        self._max_depth = max_depth
        self._learning_rate = learning_rate
        self._model_repo = model_repo
        self._device_id = device_id
        self._logger = logger

    def get_consumption_forecast(
        self, consumption_history: LoadEnergyConsumption, hours_ahead: int = 3
    ) -> Optional[LoadEnergyConsumption]:
        if not _XGB_AVAILABLE:
            if self._logger:
                self._logger.warning("xgboost is not installed — cannot produce forecast")
            return None

        effective_hours = self._hours_ahead or hours_ahead
        if effective_hours <= 0:
            return None

        # Try saved model first
        predictions = self._predict_from_saved_model(consumption_history, effective_hours)

        # Fallback: fit on-the-fly
        if predictions is None:
            predictions = self._fit_and_predict(consumption_history, effective_hours)

        if predictions is None:
            return None

        return self._build_forecast(predictions)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _predict_from_saved_model(
        self, consumption_history: LoadEnergyConsumption, hours_ahead: int
    ) -> Optional[List[float]]:
        if self._model_repo is None:
            return None
        model_entity = self._model_repo.get_active_model(
            adapter_type=EnergyLoadForecastProviderAdapter.XGBOOST,
            device_id=self._device_id,
        )
        if model_entity is None or model_entity.model_bytes is None:
            return None
        try:
            saved_model = pickle.loads(model_entity.model_bytes)  # noqa: S301
            return self._predict_future(saved_model, consumption_history, hours_ahead)
        except Exception as exc:
            if self._logger:
                self._logger.warning(f"Failed to use saved XGBoost model: {exc}")
            return None

    def _fit_and_predict(self, consumption_history: LoadEnergyConsumption, hours_ahead: int) -> Optional[List[float]]:
        X, y = prepare_supervised_dataset(consumption_history, hours_ahead=hours_ahead)
        if len(X) < 48:
            if self._logger:
                self._logger.debug(f"Insufficient training data for XGBoost ({len(X)} samples, need 48)")
            return None

        try:
            model = xgb.XGBRegressor(
                n_estimators=self._n_estimators,
                max_depth=self._max_depth,
                learning_rate=self._learning_rate,
                objective="reg:squarederror",
                verbosity=0,
            )
            model.fit(X, y)
            return self._predict_future(model, consumption_history, hours_ahead)
        except Exception as exc:
            if self._logger:
                self._logger.warning(f"XGBoost fit failed: {exc}")
            return None

    def _predict_future(
        self, model: "xgb.XGBRegressor", consumption_history: LoadEnergyConsumption, hours_ahead: int
    ) -> Optional[List[float]]:
        """Build feature rows for the next N hours and predict."""
        series = intervals_to_hourly_series(consumption_history)
        series = fill_missing_hours(series)
        if not series:
            return None

        powers = [p for _, p in series]
        now = datetime.now(timezone.utc)
        lags = [1, 2, 3, 24, 168]

        predictions: List[float] = []
        # Iteratively predict one step at a time, appending predictions to powers
        extended_powers = list(powers)
        for step in range(hours_ahead):
            future_ts = now + timedelta(hours=step)
            cal = build_calendar_features([future_ts])[0]
            lag_row = []
            n = len(extended_powers)
            for lag in lags:
                idx = n - lag
                lag_row.append(extended_powers[idx] if idx >= 0 else 0.0)
            feature_row = [cal + lag_row]
            pred = float(model.predict(feature_row)[0])
            pred = max(0.0, pred)
            predictions.append(pred)
            extended_powers.append(pred)

        return predictions

    def _build_forecast(self, predictions: List[float]) -> LoadEnergyConsumption:
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
