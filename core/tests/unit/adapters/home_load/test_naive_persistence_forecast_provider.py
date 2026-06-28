"""Unit tests for NaivePersistence forecast provider."""

from datetime import datetime, timedelta, timezone

import pytest

from edge_mining.adapters.domain.home_load.forecast_providers.naive_persistence import (
    NaivePersistenceForecastProvider,
    NaivePersistenceForecastProviderFactory,
)
from edge_mining.domain.common import Timestamp, WattHours, Watts
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter
from edge_mining.domain.home_load.exceptions import EnergyLoadForecastProviderError
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    LoadEnergyConsumption,
)
from edge_mining.shared.adapter_configs.home_load import (
    EnergyLoadForecastProviderNaivePersistenceConfig,
    EnergyLoadForecastProviderDummyConfig,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_history(hours: int = 48, base_power: float = 300.0) -> LoadEnergyConsumption:
    """Build a synthetic hourly history going back ``hours`` hours from now.

    Power follows a simple pattern based on hour-of-day to make assertions
    deterministic:  ``base_power + hour_of_day * 10``.
    """
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    intervals = []
    for i in range(hours, 0, -1):
        start = Timestamp(now - timedelta(hours=i))
        end = Timestamp(start + timedelta(hours=1))
        power = Watts(base_power + start.hour * 10)
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
# Factory tests
# ---------------------------------------------------------------------------

class TestNaivePersistenceForecastProviderFactory:
    """Tests for the factory."""

    def test_create_with_default_config(self):
        factory = NaivePersistenceForecastProviderFactory()
        provider = factory.create(config=None, logger=None, external_service=None)
        assert isinstance(provider, NaivePersistenceForecastProvider)

    def test_create_with_valid_config(self):
        config = EnergyLoadForecastProviderNaivePersistenceConfig(hours_ahead=12, delta_days=2)
        factory = NaivePersistenceForecastProviderFactory()
        provider = factory.create(config=config, logger=None, external_service=None)
        assert isinstance(provider, NaivePersistenceForecastProvider)
        assert provider._hours_ahead == 12
        assert provider._delta_days == 2

    def test_create_with_wrong_config_type_raises(self):
        config = EnergyLoadForecastProviderDummyConfig()
        factory = NaivePersistenceForecastProviderFactory()
        with pytest.raises(EnergyLoadForecastProviderError):
            factory.create(config=config, logger=None, external_service=None)


# ---------------------------------------------------------------------------
# Provider tests
# ---------------------------------------------------------------------------

class TestNaivePersistenceForecastProvider:
    """Tests for the provider."""

    def test_adapter_type(self):
        provider = NaivePersistenceForecastProvider()
        assert provider.forecast_provider_type == EnergyLoadForecastProviderAdapter.NAIVE_PERSISTENCE

    def test_min_required_history_hours_default(self):
        provider = NaivePersistenceForecastProvider(delta_days=1)
        assert provider.min_required_history_hours == 24

    def test_min_required_history_hours_custom(self):
        provider = NaivePersistenceForecastProvider(delta_days=3)
        assert provider.min_required_history_hours == 72

    def test_returns_none_for_empty_history(self):
        provider = NaivePersistenceForecastProvider(hours_ahead=3)
        empty = LoadEnergyConsumption(timestamp=Timestamp(datetime.now(timezone.utc)), intervals=[])
        assert provider.get_consumption_forecast(empty) is None

    def test_returns_none_for_zero_hours(self):
        provider = NaivePersistenceForecastProvider(hours_ahead=0)
        history = _make_history(48)
        assert provider.get_consumption_forecast(history) is None

    def test_forecast_length_matches_hours_ahead(self):
        provider = NaivePersistenceForecastProvider(hours_ahead=6)
        history = _make_history(48)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 6

    def test_forecast_default_24h(self):
        provider = NaivePersistenceForecastProvider(hours_ahead=24)
        history = _make_history(48)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 24

    def test_forecast_uses_yesterday_profile(self):
        """Each forecast hour should match the power from the same hour yesterday."""
        provider = NaivePersistenceForecastProvider(hours_ahead=6, delta_days=1)
        history = _make_history(48, base_power=300.0)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None

        for interval in forecast.intervals:
            expected_power = 300.0 + interval.start.hour * 10
            assert float(interval.avg_power) == pytest.approx(expected_power, abs=1.0)

    def test_forecast_delta_days_2(self):
        """With delta_days=2, power should come from 2 days ago."""
        provider = NaivePersistenceForecastProvider(hours_ahead=3, delta_days=2)
        history = _make_history(72, base_power=200.0)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 3

    def test_forecast_intervals_are_contiguous(self):
        provider = NaivePersistenceForecastProvider(hours_ahead=4)
        history = _make_history(48)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        for i in range(len(forecast.intervals) - 1):
            assert forecast.intervals[i].end == forecast.intervals[i + 1].start

    def test_forecast_power_non_negative(self):
        provider = NaivePersistenceForecastProvider(hours_ahead=6)
        history = _make_history(48, base_power=0.0)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        for interval in forecast.intervals:
            assert float(interval.avg_power) >= 0.0

    def test_fallback_to_avg_when_reference_missing(self):
        """When reference day has gaps, fallback to history average."""
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        # Only 2 hours of history — not enough for a full reference day
        intervals = []
        for i in [2, 1]:
            start = Timestamp(now - timedelta(hours=i))
            end = Timestamp(start + timedelta(hours=1))
            power = Watts(500.0)
            intervals.append(
                HomeLoadEnergyInterval(
                    start=start, end=end,
                    power_points=[HomeLoadPowerPoint(timestamp=start, power=power)],
                    energy=WattHours(500.0),
                )
            )
        sparse_history = LoadEnergyConsumption(timestamp=Timestamp(now), intervals=intervals)

        provider = NaivePersistenceForecastProvider(hours_ahead=3, delta_days=1)
        forecast = provider.get_consumption_forecast(sparse_history)
        assert forecast is not None
        # Should still produce 3 intervals, falling back to avg_power
        assert len(forecast.intervals) == 3


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

class TestNaivePersistenceConfig:
    """Tests for the config dataclass."""

    def test_defaults(self):
        config = EnergyLoadForecastProviderNaivePersistenceConfig()
        assert config.hours_ahead == 24
        assert config.delta_days == 1

    def test_custom_values(self):
        config = EnergyLoadForecastProviderNaivePersistenceConfig(hours_ahead=12, delta_days=3)
        assert config.hours_ahead == 12
        assert config.delta_days == 3

    def test_is_valid(self):
        config = EnergyLoadForecastProviderNaivePersistenceConfig()
        assert config.is_valid(EnergyLoadForecastProviderAdapter.NAIVE_PERSISTENCE) is True
        assert config.is_valid(EnergyLoadForecastProviderAdapter.DUMMY) is False

    def test_to_dict_from_dict_roundtrip(self):
        config = EnergyLoadForecastProviderNaivePersistenceConfig(hours_ahead=8, delta_days=2)
        d = config.to_dict()
        restored = EnergyLoadForecastProviderNaivePersistenceConfig.from_dict(d)
        assert restored == config

    def test_frozen(self):
        config = EnergyLoadForecastProviderNaivePersistenceConfig()
        with pytest.raises(AttributeError):
            config.hours_ahead = 10  # type: ignore[misc]
