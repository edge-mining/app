"""Unit tests for Skforecast forecast provider."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from edge_mining.adapters.domain.home_load.forecast_providers.skforecast_provider import (
    SkforecastForecastProvider,
    SkforecastForecastProviderFactory,
    _resolve_sklearn_model,
    _SKFORECAST_AVAILABLE,
)
from edge_mining.domain.common import EntityId, Timestamp, WattHours, Watts
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.exceptions import EnergyLoadForecastProviderError
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    LoadEnergyConsumption,
)
from edge_mining.shared.adapter_configs.home_load import (
    EnergyLoadForecastProviderDummyConfig,
    EnergyLoadForecastProviderSkforecastConfig,
)

pytestmark = pytest.mark.skipif(not _SKFORECAST_AVAILABLE, reason="skforecast not installed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_history(hours: int = 200, base_power: float = 300.0) -> LoadEnergyConsumption:
    """Build a synthetic hourly history.

    Power pattern: ``base_power + hour_of_day * 10 + sin-like wobble``.
    Needs to be long enough for num_lags + forecast horizon.
    """
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
# sklearn resolver tests
# ---------------------------------------------------------------------------


class TestSklearnModelResolver:
    """Tests for _resolve_sklearn_model."""

    def test_random_forest(self):
        model = _resolve_sklearn_model("RandomForestRegressor")
        assert model.__class__.__name__ == "RandomForestRegressor"

    def test_ridge(self):
        model = _resolve_sklearn_model("Ridge")
        assert model.__class__.__name__ == "Ridge"

    def test_kneighbors(self):
        model = _resolve_sklearn_model("KNeighborsRegressor")
        assert model.__class__.__name__ == "KNeighborsRegressor"

    def test_gradient_boosting(self):
        model = _resolve_sklearn_model("GradientBoostingRegressor")
        assert model.__class__.__name__ == "GradientBoostingRegressor"

    def test_unsupported_model_raises(self):
        with pytest.raises(EnergyLoadForecastProviderError, match="Unsupported sklearn model"):
            _resolve_sklearn_model("FakeModel")


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------


class TestSkforecastForecastProviderFactory:
    """Tests for the factory."""

    def test_create_with_default_config(self):
        factory = SkforecastForecastProviderFactory()
        provider = factory.create(config=None, logger=None, external_service=None)
        assert isinstance(provider, SkforecastForecastProvider)

    def test_create_with_valid_config(self):
        config = EnergyLoadForecastProviderSkforecastConfig(
            hours_ahead=12, weeks_lookback=4, sklearn_model="Ridge", num_lags=48
        )
        factory = SkforecastForecastProviderFactory()
        provider = factory.create(config=config, logger=None, external_service=None)
        assert isinstance(provider, SkforecastForecastProvider)
        assert provider._hours_ahead == 12
        assert provider._sklearn_model == "Ridge"
        assert provider._num_lags == 48

    def test_create_with_model_repo(self):
        mock_repo = MagicMock()
        factory = SkforecastForecastProviderFactory(model_repo=mock_repo)
        provider = factory.create(config=None, logger=None, external_service=None)
        assert provider._model_repo is mock_repo

    def test_create_with_wrong_config_type_raises(self):
        config = EnergyLoadForecastProviderDummyConfig()
        factory = SkforecastForecastProviderFactory()
        with pytest.raises(EnergyLoadForecastProviderError):
            factory.create(config=config, logger=None, external_service=None)


# ---------------------------------------------------------------------------
# Provider tests
# ---------------------------------------------------------------------------


class TestSkforecastForecastProvider:
    """Tests for the provider."""

    def test_adapter_type(self):
        provider = SkforecastForecastProvider()
        assert provider.forecast_provider_type == EnergyLoadForecastProviderAdapter.SKFORECAST

    def test_min_required_history_hours(self):
        provider = SkforecastForecastProvider(num_lags=72, hours_ahead=24)
        assert provider.min_required_history_hours == 72 + 48 + 24

    def test_returns_none_for_empty_history(self):
        provider = SkforecastForecastProvider(hours_ahead=6, num_lags=24)
        empty = LoadEnergyConsumption(timestamp=Timestamp(datetime.now(timezone.utc)), intervals=[])
        assert provider.get_consumption_forecast(empty) is None

    def test_returns_none_for_zero_hours(self):
        provider = SkforecastForecastProvider(hours_ahead=0)
        history = _make_history(200)
        assert provider.get_consumption_forecast(history) is None

    def test_returns_none_for_insufficient_history(self):
        provider = SkforecastForecastProvider(hours_ahead=24, num_lags=72)
        short_history = _make_history(50)  # < 72 + 24 = 96 needed
        assert provider.get_consumption_forecast(short_history) is None

    def test_forecast_length_matches_hours_ahead(self):
        provider = SkforecastForecastProvider(hours_ahead=6, num_lags=24)
        history = _make_history(200)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 6

    def test_forecast_with_random_forest(self):
        provider = SkforecastForecastProvider(hours_ahead=12, num_lags=24, sklearn_model="RandomForestRegressor")
        history = _make_history(200)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 12

    def test_forecast_with_ridge(self):
        provider = SkforecastForecastProvider(hours_ahead=6, num_lags=24, sklearn_model="Ridge")
        history = _make_history(200)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 6

    def test_forecast_intervals_are_contiguous(self):
        provider = SkforecastForecastProvider(hours_ahead=8, num_lags=24)
        history = _make_history(200)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        for i in range(len(forecast.intervals) - 1):
            assert forecast.intervals[i].end == forecast.intervals[i + 1].start

    def test_forecast_power_non_negative(self):
        provider = SkforecastForecastProvider(hours_ahead=6, num_lags=24)
        history = _make_history(200)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        for interval in forecast.intervals:
            assert float(interval.avg_power) >= 0.0

    def test_saved_model_used_when_available(self):
        """If model_repo returns a saved model, it should be used."""
        import pickle

        import pandas as pd
        from skforecast.recursive import ForecasterRecursive
        from sklearn.linear_model import Ridge

        # Train a small model
        history = _make_history(200)
        from edge_mining.adapters.domain.home_load.forecast_providers.features import (
            fill_missing_hours,
            intervals_to_hourly_series,
        )

        series = intervals_to_hourly_series(history)
        series = fill_missing_hours(series)
        powers = [p for _, p in series]
        y = pd.Series(powers, name="power")
        forecaster = ForecasterRecursive(estimator=Ridge(), lags=24)
        forecaster.fit(y=y)
        model_bytes = pickle.dumps(forecaster)

        # Mock model_repo
        mock_model = MagicMock()
        mock_model.model_bytes = model_bytes
        mock_repo = MagicMock()
        mock_repo.get_active_model.return_value = mock_model

        provider = SkforecastForecastProvider(hours_ahead=6, num_lags=24, model_repo=mock_repo)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 6
        mock_repo.get_active_model.assert_called_once()


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------


class TestSkforecastConfig:
    """Tests for the config dataclass."""

    def test_defaults(self):
        config = EnergyLoadForecastProviderSkforecastConfig()
        assert config.hours_ahead == 24
        assert config.weeks_lookback == 8
        assert config.sklearn_model == "RandomForestRegressor"
        assert config.num_lags == 72

    def test_custom_values(self):
        config = EnergyLoadForecastProviderSkforecastConfig(
            hours_ahead=12, weeks_lookback=4, sklearn_model="Ridge", num_lags=48
        )
        assert config.sklearn_model == "Ridge"
        assert config.num_lags == 48

    def test_is_valid(self):
        config = EnergyLoadForecastProviderSkforecastConfig()
        assert config.is_valid(EnergyLoadForecastProviderAdapter.SKFORECAST) is True
        assert config.is_valid(EnergyLoadForecastProviderAdapter.DUMMY) is False

    def test_to_dict_from_dict_roundtrip(self):
        config = EnergyLoadForecastProviderSkforecastConfig(hours_ahead=6, sklearn_model="Lasso", num_lags=36)
        d = config.to_dict()
        restored = EnergyLoadForecastProviderSkforecastConfig.from_dict(d)
        assert restored == config

    def test_frozen(self):
        config = EnergyLoadForecastProviderSkforecastConfig()
        with pytest.raises(AttributeError):
            config.hours_ahead = 10  # type: ignore[misc]
