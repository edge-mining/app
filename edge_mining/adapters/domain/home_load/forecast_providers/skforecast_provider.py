"""Skforecast ForecasterRecursive provider for energy load consumption.

Uses ``skforecast.recursive.ForecasterRecursive`` with a configurable
scikit-learn regressor backend.  The forecaster handles auto-regressive
multi-step prediction natively: it feeds its own predictions back as input
for subsequent steps.

Supported sklearn models (selected via ``sklearn_model`` config string):
    RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor,
    KNeighborsRegressor, Ridge, Lasso, ElasticNet, AdaBoostRegressor,
    MLPRegressor, SVR.

If a pre-trained model exists in ``model_repo`` it is loaded.  Otherwise
the provider fits on-the-fly from the supplied consumption history.
"""

import pickle
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Type

from edge_mining.domain.common import EntityId, Timestamp, WattHours, Watts
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.exceptions import EnergyLoadForecastProviderError
from edge_mining.domain.home_load.ports import EnergyLoadForecastProviderPort, LoadConsumptionModelRepository
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    LoadEnergyConsumption,
)
from edge_mining.shared.adapter_configs.home_load import EnergyLoadForecastProviderSkforecastConfig
from edge_mining.shared.external_services.ports import ExternalServicePort
from edge_mining.shared.interfaces.config import Configuration
from edge_mining.shared.interfaces.factories import EnergyLoadForecastAdapterFactory
from edge_mining.shared.logging.port import LoggerPort

from .features import fill_missing_hours, intervals_to_hourly_series

# ---------------------------------------------------------------------------
# Lazy imports — heavy dependencies
# ---------------------------------------------------------------------------
_SKFORECAST_AVAILABLE = False
try:
    import pandas as pd
    from skforecast.recursive import ForecasterRecursive

    _SKFORECAST_AVAILABLE = True
except ImportError:
    pd = None  # type: ignore[assignment]
    ForecasterRecursive = None  # type: ignore[assignment,misc]

# ---------------------------------------------------------------------------
# Mapping from config string → sklearn class (lazy-resolved)
# ---------------------------------------------------------------------------
_SKLEARN_MODEL_REGISTRY: Dict[str, str] = {
    "RandomForestRegressor": "sklearn.ensemble.RandomForestRegressor",
    "GradientBoostingRegressor": "sklearn.ensemble.GradientBoostingRegressor",
    "ExtraTreesRegressor": "sklearn.ensemble.ExtraTreesRegressor",
    "AdaBoostRegressor": "sklearn.ensemble.AdaBoostRegressor",
    "KNeighborsRegressor": "sklearn.neighbors.KNeighborsRegressor",
    "Ridge": "sklearn.linear_model.Ridge",
    "Lasso": "sklearn.linear_model.Lasso",
    "ElasticNet": "sklearn.linear_model.ElasticNet",
    "MLPRegressor": "sklearn.neural_network.MLPRegressor",
    "SVR": "sklearn.svm.SVR",
}


def _resolve_sklearn_model(name: str) -> object:
    """Instantiate an sklearn regressor by its class name."""
    import importlib

    fqn = _SKLEARN_MODEL_REGISTRY.get(name)
    if fqn is None:
        raise EnergyLoadForecastProviderError(
            f"Unsupported sklearn model '{name}'. Available: {list(_SKLEARN_MODEL_REGISTRY.keys())}"
        )
    module_path, class_name = fqn.rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls: Type = getattr(module, class_name)
    return cls()


class SkforecastForecastProviderFactory(EnergyLoadForecastAdapterFactory):
    """Factory for creating a SkforecastForecastProvider instance."""

    def __init__(self, model_repo: Optional[LoadConsumptionModelRepository] = None) -> None:
        self._model_repo = model_repo

    def create(
        self,
        config: Optional[Configuration],
        logger: Optional[LoggerPort],
        external_service: Optional[ExternalServicePort],
    ) -> "SkforecastForecastProvider":
        if config is not None and not isinstance(config, EnergyLoadForecastProviderSkforecastConfig):
            raise EnergyLoadForecastProviderError(
                "Invalid configuration type for Skforecast energy load forecast provider. "
                "Expected EnergyLoadForecastProviderSkforecastConfig."
            )

        hours_ahead = 24
        weeks_lookback = 8
        sklearn_model = "RandomForestRegressor"
        num_lags = 72
        if isinstance(config, EnergyLoadForecastProviderSkforecastConfig):
            hours_ahead = config.hours_ahead
            weeks_lookback = config.weeks_lookback
            sklearn_model = config.sklearn_model
            num_lags = config.num_lags

        return SkforecastForecastProvider(
            hours_ahead=hours_ahead,
            weeks_lookback=weeks_lookback,
            sklearn_model=sklearn_model,
            num_lags=num_lags,
            model_repo=self._model_repo,
            logger=logger,
        )


class SkforecastForecastProvider(EnergyLoadForecastProviderPort):
    """Forecast provider using skforecast ForecasterRecursive.

    Uses a configurable sklearn regressor wrapped in ``ForecasterRecursive``
    which automatically manages lag features and recursive multi-step
    prediction.

    If a pre-trained model is available in ``model_repo``, it is loaded and
    used directly.  Otherwise, fits on-the-fly from the provided history.
    """

    def __init__(
        self,
        hours_ahead: int = 24,
        weeks_lookback: int = 8,
        sklearn_model: str = "RandomForestRegressor",
        num_lags: int = 72,
        model_repo: Optional[LoadConsumptionModelRepository] = None,
        device_id: Optional[EntityId] = None,
        logger: Optional[LoggerPort] = None,
    ):
        super().__init__(forecast_provider_type=EnergyLoadForecastProviderAdapter.SKFORECAST)
        self._hours_ahead = hours_ahead
        self._weeks_lookback = weeks_lookback
        self._sklearn_model = sklearn_model
        self._num_lags = num_lags
        self._model_repo = model_repo
        self._device_id = device_id
        self._logger = logger

    @property
    def min_required_history_hours(self) -> int:  # noqa: D102
        return self._num_lags + 48 + self._hours_ahead

    def get_consumption_forecast(
        self, consumption_history: LoadEnergyConsumption, hours_ahead: int = 24
    ) -> Optional[LoadEnergyConsumption]:
        if not _SKFORECAST_AVAILABLE:
            if self._logger:
                self._logger.warning("skforecast is not installed. Skipping Skforecast forecast.")
            return None

        effective_hours = self._hours_ahead
        if effective_hours <= 0:
            return None

        if not consumption_history.intervals:
            return None

        # Try saved model first
        forecast = self._predict_from_saved_model(effective_hours)
        if forecast is not None:
            return forecast

        # Fallback: fit on-the-fly
        return self._fit_and_predict(consumption_history, effective_hours)

    def _predict_from_saved_model(self, steps: int) -> Optional[LoadEnergyConsumption]:
        """Load a pre-trained ForecasterRecursive from model_repo and predict."""
        if self._model_repo is None:
            return None

        model_entity = self._model_repo.get_active_model(EnergyLoadForecastProviderAdapter.SKFORECAST, self._device_id)
        if model_entity is None or model_entity.model_bytes is None:
            return None

        try:
            forecaster = pickle.loads(model_entity.model_bytes)  # noqa: S301
            predictions = forecaster.predict(steps=steps)
            return self._build_forecast(predictions.tolist())
        except Exception as exc:
            if self._logger:
                self._logger.warning(f"Failed to predict from saved skforecast model: {exc}")
            return None

    def _fit_and_predict(
        self, consumption_history: LoadEnergyConsumption, steps: int
    ) -> Optional[LoadEnergyConsumption]:
        """Fit ForecasterRecursive on the fly and predict."""
        series = intervals_to_hourly_series(consumption_history)
        series = fill_missing_hours(series)
        powers = [p for _, p in series]

        if len(powers) < self._num_lags + steps:
            if self._logger:
                self._logger.debug(
                    f"Insufficient data for skforecast: {len(powers)} points, "
                    f"need {self._num_lags + steps} (lags + steps)."
                )
            return None

        try:
            regressor = _resolve_sklearn_model(self._sklearn_model)
            forecaster = ForecasterRecursive(regressor=regressor, lags=self._num_lags)

            y = pd.Series(powers, name="power")
            forecaster.fit(y=y)

            predictions = forecaster.predict(steps=steps)
            return self._build_forecast(predictions.tolist())
        except Exception as exc:
            if self._logger:
                self._logger.warning(f"Skforecast on-the-fly fit failed: {exc}")
            return None

    @staticmethod
    def _build_forecast(predictions: List[float]) -> LoadEnergyConsumption:
        """Convert a list of predicted power values to LoadEnergyConsumption."""
        now = Timestamp(datetime.now(timezone.utc))
        intervals: List[HomeLoadEnergyInterval] = []
        for i, power_val in enumerate(predictions):
            start = Timestamp(now + timedelta(hours=i))
            end = Timestamp(start + timedelta(hours=1))
            power = Watts(max(0.0, float(power_val)))
            point = HomeLoadPowerPoint(timestamp=start, power=power)
            intervals.append(
                HomeLoadEnergyInterval(
                    start=start,
                    end=end,
                    power_points=[point],
                    energy=WattHours(float(power)),
                )
            )
        return LoadEnergyConsumption(timestamp=now, intervals=intervals)
