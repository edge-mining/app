"""Unit tests for Optuna Bayesian tuning integration (F6).

Tests the ``tune()`` static method on ``SkforecastForecastProvider``,
the ``_build_search_space`` helper, and the ``tuning_params`` field on
``LoadConsumptionModel``.
"""

from datetime import datetime, timedelta, timezone

import pytest

from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
    _SKFORECAST_AVAILABLE,
)
from edge_mining.domain.common import Timestamp, WattHours, Watts
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.entities import LoadConsumptionModel
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    LoadEnergyConsumption,
)

pytestmark = pytest.mark.skipif(not _SKFORECAST_AVAILABLE, reason="skforecast not installed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_series(hours: int = 300):
    """Create a pandas Series of synthetic hourly power values."""
    import pandas as pd

    values = [300.0 + (i % 24) * 10 + (i % 7) * 5 for i in range(hours)]
    return pd.Series(values, name="power")


def _make_history(hours: int = 300, base_power: float = 300.0) -> LoadEnergyConsumption:
    """Build hourly LoadEnergyConsumption for training service tests."""
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    intervals = []
    for i in range(hours, 0, -1):
        start = Timestamp(now - timedelta(hours=i))
        end = Timestamp(start + timedelta(hours=1))
        power = Watts(base_power + start.hour * 10 + (i % 7) * 5)
        intervals.append(
            HomeLoadEnergyInterval(
                start=start,
                end=end,
                power_points=[HomeLoadPowerPoint(timestamp=start, power=power)],
                energy=WattHours(float(power)),
            )
        )
    return LoadEnergyConsumption(timestamp=Timestamp(now), intervals=intervals)


# ---------------------------------------------------------------------------
# tune() static method tests
# ---------------------------------------------------------------------------


class TestSkforecastTune:
    """Tests for SkforecastForecastProvider.tune()."""

    def test_tune_returns_params_and_forecaster(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            SkforecastForecastProvider,
        )

        y = _make_series(300)
        best_params, tuned_forecaster = SkforecastForecastProvider.tune(
            y_series=y,
            sklearn_model_name="Ridge",
            num_lags=24,
            steps=24,
            n_trials=3,  # small for speed
        )
        assert isinstance(best_params, dict)
        assert tuned_forecaster is not None

    def test_tune_with_random_forest(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            SkforecastForecastProvider,
        )

        y = _make_series(300)
        best_params, tuned_forecaster = SkforecastForecastProvider.tune(
            y_series=y,
            sklearn_model_name="RandomForestRegressor",
            num_lags=24,
            steps=24,
            n_trials=3,
        )
        assert isinstance(best_params, dict)
        # Tuned forecaster should be able to predict
        preds = tuned_forecaster.predict(steps=6)
        assert len(preds) == 6

    def test_tune_with_kneighbors(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            SkforecastForecastProvider,
        )

        y = _make_series(300)
        best_params, tuned = SkforecastForecastProvider.tune(
            y_series=y,
            sklearn_model_name="KNeighborsRegressor",
            num_lags=24,
            steps=24,
            n_trials=3,
        )
        assert isinstance(best_params, dict)


# ---------------------------------------------------------------------------
# _build_search_space tests
# ---------------------------------------------------------------------------


class TestBuildSearchSpace:
    """Tests for the search space builder."""

    def test_rf_space_callable(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            _build_search_space,
        )

        space = _build_search_space("RandomForestRegressor")
        assert callable(space)

    def test_ridge_space_callable(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            _build_search_space,
        )

        space = _build_search_space("Ridge")
        assert callable(space)

    def test_unknown_model_returns_default_space(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            _build_search_space,
        )

        space = _build_search_space("SomeUnknownModel")
        assert callable(space)


# ---------------------------------------------------------------------------
# LoadConsumptionModel.tuning_params tests
# ---------------------------------------------------------------------------


class TestLoadConsumptionModelTuningParams:
    """Tests for the tuning_params field on the entity."""

    def test_default_is_none(self):
        model = LoadConsumptionModel()
        assert model.tuning_params is None

    def test_can_set_dict(self):
        params = {"n_estimators": 200, "max_depth": 10, "lags": 48}
        model = LoadConsumptionModel(tuning_params=params)
        assert model.tuning_params == params
        assert model.tuning_params["n_estimators"] == 200

    def test_schema_includes_tuning_params(self):
        from edge_mining.adapters.domain.home_load.schemas import LoadConsumptionModelSchema

        params = {"alpha": 0.5, "lags": 24}
        model = LoadConsumptionModel(
            adapter_type=EnergyLoadForecastProviderAdapter.SKFORECAST,
            tuning_params=params,
        )
        schema = LoadConsumptionModelSchema.from_model(model)
        assert schema.tuning_params == params

    def test_schema_tuning_params_none(self):
        from edge_mining.adapters.domain.home_load.schemas import LoadConsumptionModelSchema

        model = LoadConsumptionModel()
        schema = LoadConsumptionModelSchema.from_model(model)
        assert schema.tuning_params is None
