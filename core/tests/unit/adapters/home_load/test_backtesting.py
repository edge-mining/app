"""Unit tests for F7 — Rolling-window backtesting integration.

Tests the ``backtest()`` static method on ``SkforecastForecastProvider``,
the new ``backtest_mae / backtest_rmse / backtest_folds`` fields on
``LoadConsumptionModel``, and the corresponding schema fields.
"""

import pytest

from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
    _SKFORECAST_AVAILABLE,
)
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.entities import LoadConsumptionModel

pytestmark = pytest.mark.skipif(not _SKFORECAST_AVAILABLE, reason="skforecast not installed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_series(hours: int = 300):
    """Create a pandas Series of synthetic hourly power values."""
    import pandas as pd

    values = [300.0 + (i % 24) * 10 + (i % 7) * 5 for i in range(hours)]
    return pd.Series(values, name="power")


def _fit_forecaster(y, lags: int = 24):
    """Return a fitted ForecasterRecursive on *y*."""
    from skforecast.recursive import ForecasterRecursive
    from sklearn.linear_model import Ridge

    forecaster = ForecasterRecursive(estimator=Ridge(), lags=lags)
    forecaster.fit(y=y)
    return forecaster


# ---------------------------------------------------------------------------
# backtest() static method tests
# ---------------------------------------------------------------------------


class TestSkforecastBacktest:
    """Tests for SkforecastForecastProvider.backtest()."""

    def test_backtest_returns_dict_with_expected_keys(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            SkforecastForecastProvider,
        )

        y = _make_series(300)
        forecaster = _fit_forecaster(y)
        result = SkforecastForecastProvider.backtest(
            forecaster=forecaster,
            y_series=y,
            steps=24,
            folds=3,
        )
        assert isinstance(result, dict)
        assert "backtest_mae" in result
        assert "backtest_rmse" in result
        assert "backtest_folds" in result

    def test_backtest_mae_is_positive(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            SkforecastForecastProvider,
        )

        y = _make_series(300)
        forecaster = _fit_forecaster(y)
        result = SkforecastForecastProvider.backtest(
            forecaster=forecaster,
            y_series=y,
            steps=24,
            folds=3,
        )
        assert result["backtest_mae"] is not None
        assert result["backtest_mae"] >= 0

    def test_backtest_rmse_is_positive(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            SkforecastForecastProvider,
        )

        y = _make_series(300)
        forecaster = _fit_forecaster(y)
        result = SkforecastForecastProvider.backtest(
            forecaster=forecaster,
            y_series=y,
            steps=24,
            folds=3,
        )
        assert result["backtest_rmse"] is not None
        assert result["backtest_rmse"] >= 0

    def test_backtest_folds_positive(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            SkforecastForecastProvider,
        )

        y = _make_series(300)
        forecaster = _fit_forecaster(y)
        result = SkforecastForecastProvider.backtest(
            forecaster=forecaster,
            y_series=y,
            steps=24,
            folds=3,
        )
        assert result["backtest_folds"] > 0

    def test_backtest_too_short_series_returns_zeros(self):
        from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
            SkforecastForecastProvider,
        )

        # Very short series — not enough for even 2*steps training
        y = _make_series(30)
        forecaster = _fit_forecaster(y, lags=6)
        result = SkforecastForecastProvider.backtest(
            forecaster=forecaster,
            y_series=y,
            steps=24,
            folds=3,
        )
        assert result["backtest_mae"] is None
        assert result["backtest_folds"] == 0


# ---------------------------------------------------------------------------
# LoadConsumptionModel backtest fields tests
# ---------------------------------------------------------------------------


class TestLoadConsumptionModelBacktestFields:
    """Tests for backtest_mae/rmse/folds fields on the entity."""

    def test_defaults(self):
        model = LoadConsumptionModel()
        assert model.backtest_mae is None
        assert model.backtest_rmse is None
        assert model.backtest_folds == 0

    def test_set_values(self):
        model = LoadConsumptionModel(backtest_mae=12.5, backtest_rmse=15.3, backtest_folds=5)
        assert model.backtest_mae == 12.5
        assert model.backtest_rmse == 15.3
        assert model.backtest_folds == 5

    def test_schema_includes_backtest_fields(self):
        from edge_mining.adapters.domain.home_load.schemas import LoadConsumptionModelSchema

        model = LoadConsumptionModel(
            adapter_type=EnergyLoadForecastProviderAdapter.SKFORECAST,
            backtest_mae=8.2,
            backtest_rmse=10.1,
            backtest_folds=4,
        )
        schema = LoadConsumptionModelSchema.from_model(model)
        assert schema.backtest_mae == 8.2
        assert schema.backtest_rmse == 10.1
        assert schema.backtest_folds == 4

    def test_schema_backtest_defaults(self):
        from edge_mining.adapters.domain.home_load.schemas import LoadConsumptionModelSchema

        model = LoadConsumptionModel()
        schema = LoadConsumptionModelSchema.from_model(model)
        assert schema.backtest_mae is None
        assert schema.backtest_rmse is None
        assert schema.backtest_folds == 0
