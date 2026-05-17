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
            forecaster = ForecasterRecursive(estimator=regressor, lags=self._num_lags)

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

    @staticmethod
    def tune(
        y_series: "pd.Series",
        sklearn_model_name: str = "RandomForestRegressor",
        num_lags: int = 72,
        steps: int = 24,
        n_trials: int = 20,
        metric: str = "mean_absolute_error",
    ) -> tuple:
        """Run Bayesian hyperparameter optimisation via Optuna.

        Returns ``(best_params, tuned_forecaster)`` where *best_params* is a
        dict of the winning hyperparameter combination and *tuned_forecaster*
        is the ``ForecasterRecursive`` already refit with those params.

        This is a **static helper** so it can be called from the training
        service without instantiating a full provider.
        """
        import optuna
        from skforecast.model_selection import TimeSeriesFold, bayesian_search_forecaster

        optuna.logging.set_verbosity(optuna.logging.WARNING)

        regressor = _resolve_sklearn_model(sklearn_model_name)
        forecaster = ForecasterRecursive(estimator=regressor, lags=num_lags)

        cv = TimeSeriesFold(
            steps=steps,
            initial_train_size=len(y_series) - steps * 2,
            refit=False,
            fixed_train_size=False,
        )

        search_space = _build_search_space(sklearn_model_name)

        results_df, _study = bayesian_search_forecaster(
            forecaster=forecaster,
            y=y_series,
            cv=cv,
            search_space=search_space,
            metric=metric,
            n_trials=n_trials,
            return_best=True,
            verbose=False,
            show_progress=False,
        )

        best_params = results_df.iloc[0].to_dict() if not results_df.empty else {}
        # Keep only hyperparameter keys (filter out metric columns)
        param_keys = {k for k in best_params if k not in ("mean_absolute_error", "mean_squared_error", metric)}
        best_params = {k: v for k, v in best_params.items() if k in param_keys}

        # return_best=True refits the forecaster in-place with the best params
        return best_params, forecaster

    @staticmethod
    def backtest(
        forecaster: "ForecasterRecursive",
        y_series: "pd.Series",
        steps: int = 24,
        folds: int = 3,
        metric: str = "mean_absolute_error",
    ) -> dict:
        """Run rolling-window backtesting on an already-fit forecaster.

        Returns a dict with ``backtest_mae``, ``backtest_rmse`` and
        ``backtest_folds``.
        """
        import numpy as np
        from skforecast.model_selection import TimeSeriesFold, backtesting_forecaster

        # Need at least window_size + steps*(folds+1) data points
        window = getattr(forecaster, "window_size", steps)
        min_required = window + steps * (folds + 1)
        if len(y_series) < min_required:
            return {"backtest_mae": None, "backtest_rmse": None, "backtest_folds": 0}

        initial_train_size = len(y_series) - steps * folds
        if initial_train_size <= window:
            return {"backtest_mae": None, "backtest_rmse": None, "backtest_folds": 0}

        cv = TimeSeriesFold(
            steps=steps,
            initial_train_size=initial_train_size,
            refit=False,
            fixed_train_size=False,
        )

        metric_values, predictions = backtesting_forecaster(
            forecaster=forecaster,
            y=y_series,
            cv=cv,
            metric=[metric, "mean_squared_error"],
            verbose=False,
            show_progress=False,
        )

        # metric_values is a DataFrame with one row, columns = metric names
        bt_mae = float(metric_values[metric].iloc[0]) if metric in metric_values.columns else None
        bt_mse = (
            float(metric_values["mean_squared_error"].iloc[0])
            if "mean_squared_error" in metric_values.columns
            else None
        )
        bt_rmse = float(np.sqrt(bt_mse)) if bt_mse is not None else None

        # Number of folds = number of complete prediction windows
        actual_folds = len(predictions) // steps if len(predictions) >= steps else 0

        return {
            "backtest_mae": bt_mae,
            "backtest_rmse": bt_rmse,
            "backtest_folds": actual_folds,
        }


def _build_search_space(sklearn_model_name: str):
    """Return an Optuna search_space callable for the given model."""
    import optuna

    def _rf_space(trial: optuna.Trial) -> dict:
        return {
            "n_estimators": trial.suggest_int("n_estimators", 50, 400),
            "max_depth": trial.suggest_int("max_depth", 3, 20),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "lags": trial.suggest_categorical("lags", [24, 48, 72]),
        }

    def _gb_space(trial: optuna.Trial) -> dict:
        return {
            "n_estimators": trial.suggest_int("n_estimators", 50, 400),
            "max_depth": trial.suggest_int("max_depth", 3, 15),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "lags": trial.suggest_categorical("lags", [24, 48, 72]),
        }

    def _ridge_space(trial: optuna.Trial) -> dict:
        return {
            "alpha": trial.suggest_float("alpha", 0.01, 100.0, log=True),
            "lags": trial.suggest_categorical("lags", [24, 48, 72]),
        }

    def _knn_space(trial: optuna.Trial) -> dict:
        return {
            "n_neighbors": trial.suggest_int("n_neighbors", 3, 30),
            "weights": trial.suggest_categorical("weights", ["uniform", "distance"]),
            "lags": trial.suggest_categorical("lags", [24, 48, 72]),
        }

    def _default_space(trial: optuna.Trial) -> dict:
        return {
            "lags": trial.suggest_categorical("lags", [24, 48, 72]),
        }

    space_map = {
        "RandomForestRegressor": _rf_space,
        "ExtraTreesRegressor": _rf_space,
        "GradientBoostingRegressor": _gb_space,
        "AdaBoostRegressor": _gb_space,
        "Ridge": _ridge_space,
        "Lasso": _ridge_space,
        "ElasticNet": _ridge_space,
        "KNeighborsRegressor": _knn_space,
    }
    return space_map.get(sklearn_model_name, _default_space)
