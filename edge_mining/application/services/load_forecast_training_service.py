"""Service for training ML forecast models on collected home load history."""

import pickle
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from edge_mining.adapters.domain.home_load.forecast_providers.features import (
    fill_missing_hours,
    intervals_to_hourly_series,
    prepare_supervised_dataset,
)
from edge_mining.adapters.domain.home_load.history_providers.helpers import group_power_points_into_intervals
from edge_mining.application.interfaces import LoadForecastTrainingServiceInterface
from edge_mining.domain.common import EntityId, Timestamp
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.entities import LoadConsumptionModel
from edge_mining.domain.home_load.ports import (
    EnergyLoadHistoryRepository,
    HomeLoadsProfileRepository,
    LoadConsumptionModelRepository,
)
from edge_mining.domain.home_load.value_objects import LoadEnergyConsumption
from edge_mining.shared.logging.port import LoggerPort


class LoadForecastModelTrainingService(LoadForecastTrainingServiceInterface):
    """Trains ML models (Statsmodels, XGBoost) on historical home load data.

    Designed to be run nightly via the scheduler.  For each enabled device
    that has enough history, trains both a Holt-Winters and an XGBoost model,
    evaluates them against a holdout set, and promotes the best one to active.
    """

    def __init__(
        self,
        home_loads_repo: HomeLoadsProfileRepository,
        history_repo: EnergyLoadHistoryRepository,
        model_repo: LoadConsumptionModelRepository,
        logger: Optional[LoggerPort] = None,
    ):
        self._home_loads_repo = home_loads_repo
        self._history_repo = history_repo
        self._model_repo = model_repo
        self._logger = logger

    async def train_all(self, weeks_lookback: int = 8) -> None:
        """Train models for every device that has sufficient history."""
        profiles = self._home_loads_repo.get_all()
        if not profiles:
            if self._logger:
                self._logger.debug("No home load profiles found. Skipping training.")
            return

        for profile in profiles:
            for device in profile.devices:
                if not device.enabled:
                    continue
                try:
                    await self._train_for_device(device.id, device.name, weeks_lookback)
                except Exception as exc:
                    if self._logger:
                        self._logger.error(f"Training failed for device '{device.name}': {exc}")

    async def train_device(self, device_id: EntityId, weeks_lookback: int = 8) -> None:
        """Train models for a single device identified by device_id."""
        profiles = self._home_loads_repo.get_all()
        device_name: Optional[str] = None
        for profile in profiles:
            for device in profile.devices:
                if device.id == device_id:
                    device_name = device.name
                    break
            if device_name is not None:
                break

        if device_name is None:
            if self._logger:
                self._logger.warning(f"Device {device_id} not found in any profile. Skipping training.")
            return

        await self._train_for_device(device_id, device_name, weeks_lookback)

    def get_models(self, device_id: Optional[EntityId] = None) -> List[LoadConsumptionModel]:
        """Retrieve trained models, optionally filtered by device."""
        return self._model_repo.get_all(device_id)

    async def _train_for_device(
        self,
        device_id: EntityId,
        device_name: str,
        weeks_lookback: int,
    ) -> None:
        """Train HW + XGBoost models for one device, promote the better one."""
        now = Timestamp(datetime.now(timezone.utc))
        lookback_start = Timestamp(now - timedelta(weeks=weeks_lookback))

        power_points = self._history_repo.get_power_points(device_id, lookback_start, now)
        if len(power_points) < 48 * 2:  # at least 48 hours of data for train+holdout
            if self._logger:
                self._logger.debug(
                    f"Insufficient history for device '{device_name}' ({len(power_points)} points). Skipping training."
                )
            return

        # Build LoadEnergyConsumption from power points
        intervals = group_power_points_into_intervals(power_points)
        consumption = LoadEnergyConsumption(timestamp=now, intervals=intervals)

        # Split: last 24h as holdout
        holdout_start = Timestamp(now - timedelta(hours=24))
        train_consumption = consumption.in_window(lookback_start, holdout_start)
        holdout_consumption = consumption.in_window(holdout_start, now)

        if len(train_consumption.intervals) < 48 or len(holdout_consumption.intervals) < 12:
            if self._logger:
                self._logger.debug(f"Not enough data after split for device '{device_name}'. Skipping.")
            return

        hw_model = self._train_hw(train_consumption, holdout_consumption, device_id, device_name)
        xgb_model = self._train_xgb(train_consumption, holdout_consumption, device_id, device_name)

        # Promote the best model
        candidates = [m for m in [hw_model, xgb_model] if m is not None and m.mae is not None]
        if not candidates:
            if self._logger:
                self._logger.warning(f"No model trained successfully for device '{device_name}'.")
            return

        best = min(candidates, key=lambda m: m.mae)  # type: ignore[arg-type]
        best.is_active = True

        # Deactivate previous active models for this device
        for adapter_type in [EnergyLoadForecastProviderAdapter.STATSMODELS, EnergyLoadForecastProviderAdapter.XGBOOST]:
            old = self._model_repo.get_active_model(adapter_type, device_id)
            if old is not None:
                old.is_active = False
                self._model_repo.update(old)

        # Persist all trained models
        for model in candidates:
            self._model_repo.add(model)

        if self._logger:
            self._logger.info(
                f"Trained models for device '{device_name}': best={best.adapter_type.value} MAE={best.mae:.2f}"
            )

    def _train_hw(
        self,
        train: LoadEnergyConsumption,
        holdout: LoadEnergyConsumption,
        device_id: EntityId,
        device_name: str,
    ) -> Optional[LoadConsumptionModel]:
        """Train Holt-Winters and evaluate on holdout."""
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
        except ImportError:
            return None

        series = intervals_to_hourly_series(train)
        series = fill_missing_hours(series)
        powers = [p for _, p in series]

        seasonal_periods = 24
        if len(powers) < seasonal_periods * 2:
            return None

        try:
            model = ExponentialSmoothing(powers, trend="add", seasonal="add", seasonal_periods=seasonal_periods)
            fitted = model.fit(optimized=True)
            model_bytes = pickle.dumps(fitted)

            # Evaluate on holdout
            holdout_series = intervals_to_hourly_series(holdout)
            holdout_series = fill_missing_hours(holdout_series)
            holdout_powers = [p for _, p in holdout_series]

            n_eval = min(len(holdout_powers), 24)
            if n_eval == 0:
                return None

            forecast = fitted.forecast(n_eval)
            mae = sum(abs(float(forecast[i]) - holdout_powers[i]) for i in range(n_eval)) / n_eval
            rmse = (sum((float(forecast[i]) - holdout_powers[i]) ** 2 for i in range(n_eval)) / n_eval) ** 0.5

            return LoadConsumptionModel(
                device_id=device_id,
                adapter_type=EnergyLoadForecastProviderAdapter.STATSMODELS,
                trained_at=datetime.now(),
                mae=mae,
                rmse=rmse,
                samples_used=len(powers),
                is_active=False,
                model_bytes=model_bytes,
            )
        except Exception as exc:
            if self._logger:
                self._logger.warning(f"Holt-Winters training failed for '{device_name}': {exc}")
            return None

    def _train_xgb(
        self,
        train: LoadEnergyConsumption,
        holdout: LoadEnergyConsumption,
        device_id: EntityId,
        device_name: str,
    ) -> Optional[LoadConsumptionModel]:
        """Train XGBoost and evaluate on holdout."""
        try:
            import xgboost as xgb
        except ImportError:
            return None

        hours_ahead = 3
        X_train, y_train = prepare_supervised_dataset(train, hours_ahead=hours_ahead)
        if len(X_train) < 48:
            return None

        try:
            model = xgb.XGBRegressor(
                n_estimators=100, max_depth=6, learning_rate=0.1, objective="reg:squarederror", verbosity=0
            )
            model.fit(X_train, y_train)
            model_bytes = pickle.dumps(model)

            # Evaluate on holdout
            X_holdout, y_holdout = prepare_supervised_dataset(holdout, hours_ahead=hours_ahead)
            if len(X_holdout) < 3:
                # If holdout has insufficient supervised pairs, use raw MAE
                holdout_series = intervals_to_hourly_series(holdout)
                holdout_series = fill_missing_hours(holdout_series)
                holdout_powers = [p for _, p in holdout_series]
                if not holdout_powers:
                    return None
                # Predict on holdout features (from training data end)
                X_eval, y_eval = prepare_supervised_dataset(
                    LoadEnergyConsumption(
                        timestamp=holdout.timestamp,
                        intervals=list(train.intervals) + list(holdout.intervals),
                    ),
                    hours_ahead=hours_ahead,
                )
                # Use last portion as holdout
                n_eval = min(len(holdout_powers), len(X_eval))
                if n_eval == 0:
                    return None
                X_eval = X_eval[-n_eval:]
                y_eval = y_eval[-n_eval:]
            else:
                X_eval, y_eval = X_holdout, y_holdout
                n_eval = len(y_eval)

            predictions = model.predict(X_eval)
            mae = sum(abs(float(predictions[i]) - y_eval[i]) for i in range(n_eval)) / n_eval
            rmse = (sum((float(predictions[i]) - y_eval[i]) ** 2 for i in range(n_eval)) / n_eval) ** 0.5

            return LoadConsumptionModel(
                device_id=device_id,
                adapter_type=EnergyLoadForecastProviderAdapter.XGBOOST,
                trained_at=datetime.now(),
                mae=mae,
                rmse=rmse,
                samples_used=len(X_train),
                is_active=False,
                model_bytes=model_bytes,
            )
        except Exception as exc:
            if self._logger:
                self._logger.warning(f"XGBoost training failed for '{device_name}': {exc}")
            return None
