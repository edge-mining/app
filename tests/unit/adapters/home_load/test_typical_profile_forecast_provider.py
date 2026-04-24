"""Unit tests for TypicalProfile forecast provider."""

from datetime import datetime, timedelta, timezone

import pytest

from edge_mining.adapters.domain.home_load.forecast_providers.typical_profile import (
    TypicalProfileForecastProvider,
    TypicalProfileForecastProviderFactory,
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
    EnergyLoadForecastProviderDummyConfig,
    EnergyLoadForecastProviderTypicalProfileConfig,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_history(weeks: int = 4, base_power: float = 300.0) -> LoadEnergyConsumption:
    """Build a synthetic hourly history going back ``weeks`` weeks.

    Power follows a deterministic pattern:
      ``base_power + (month * 5) + (dow * 3) + (hour * 10)``
    so each (month, dow, hour) has a unique, predictable value.
    """
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    total_hours = weeks * 168
    intervals = []
    for i in range(total_hours, 0, -1):
        start = Timestamp(now - timedelta(hours=i))
        end = Timestamp(start + timedelta(hours=1))
        power = Watts(base_power + start.month * 5 + start.weekday() * 3 + start.hour * 10)
        intervals.append(
            HomeLoadEnergyInterval(
                start=start,
                end=end,
                power_points=[HomeLoadPowerPoint(timestamp=start, power=power)],
                energy=WattHours(float(power)),
            )
        )
    return LoadEnergyConsumption(timestamp=Timestamp(now), intervals=intervals)


def _make_sparse_history(hours: int = 48, base_power: float = 400.0) -> LoadEnergyConsumption:
    """History with only a few hours, some (month, dow, hour) combos missing."""
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

class TestTypicalProfileForecastProviderFactory:
    """Tests for the factory."""

    def test_create_with_default_config(self):
        factory = TypicalProfileForecastProviderFactory()
        provider = factory.create(config=None, logger=None, external_service=None)
        assert isinstance(provider, TypicalProfileForecastProvider)

    def test_create_with_valid_config(self):
        config = EnergyLoadForecastProviderTypicalProfileConfig(hours_ahead=12, weeks_lookback=4)
        factory = TypicalProfileForecastProviderFactory()
        provider = factory.create(config=config, logger=None, external_service=None)
        assert isinstance(provider, TypicalProfileForecastProvider)
        assert provider._hours_ahead == 12
        assert provider._weeks_lookback == 4

    def test_create_with_wrong_config_type_raises(self):
        config = EnergyLoadForecastProviderDummyConfig()
        factory = TypicalProfileForecastProviderFactory()
        with pytest.raises(EnergyLoadForecastProviderError):
            factory.create(config=config, logger=None, external_service=None)


# ---------------------------------------------------------------------------
# Provider tests
# ---------------------------------------------------------------------------

class TestTypicalProfileForecastProvider:
    """Tests for the provider."""

    def test_adapter_type(self):
        provider = TypicalProfileForecastProvider()
        assert provider.forecast_provider_type == EnergyLoadForecastProviderAdapter.TYPICAL_PROFILE

    def test_min_required_history_hours_default(self):
        provider = TypicalProfileForecastProvider(weeks_lookback=8)
        assert provider.min_required_history_hours == 8 * 168

    def test_min_required_history_hours_custom(self):
        provider = TypicalProfileForecastProvider(weeks_lookback=2)
        assert provider.min_required_history_hours == 2 * 168

    def test_returns_none_for_empty_history(self):
        provider = TypicalProfileForecastProvider(hours_ahead=6)
        empty = LoadEnergyConsumption(timestamp=Timestamp(datetime.now(timezone.utc)), intervals=[])
        assert provider.get_consumption_forecast(empty) is None

    def test_returns_none_for_zero_hours(self):
        provider = TypicalProfileForecastProvider(hours_ahead=0)
        history = _make_history(4)
        assert provider.get_consumption_forecast(history) is None

    def test_forecast_length_matches_hours_ahead(self):
        provider = TypicalProfileForecastProvider(hours_ahead=6)
        history = _make_history(4)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 6

    def test_forecast_default_24h(self):
        provider = TypicalProfileForecastProvider(hours_ahead=24)
        history = _make_history(4)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 24

    def test_forecast_uses_month_dow_hour_profile(self):
        """Power should match the (month, dow, hour) average from history."""
        provider = TypicalProfileForecastProvider(hours_ahead=6)
        history = _make_history(4, base_power=300.0)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None

        for interval in forecast.intervals:
            expected = 300.0 + interval.start.month * 5 + interval.start.weekday() * 3 + interval.start.hour * 10
            assert float(interval.avg_power) == pytest.approx(expected, abs=1.0)

    def test_forecast_intervals_are_contiguous(self):
        provider = TypicalProfileForecastProvider(hours_ahead=8)
        history = _make_history(4)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        for i in range(len(forecast.intervals) - 1):
            assert forecast.intervals[i].end == forecast.intervals[i + 1].start

    def test_forecast_power_non_negative(self):
        provider = TypicalProfileForecastProvider(hours_ahead=6)
        history = _make_history(4, base_power=0.0)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        for interval in forecast.intervals:
            assert float(interval.avg_power) >= 0.0

    def test_fallback_to_dow_hour_when_month_missing(self):
        """When exact (month, dow, hour) isn't available, fall back to (dow, hour)."""
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        # Create history from a different month to force fallback
        intervals = []
        different_month_start = now.replace(month=(now.month % 12) + 1, day=1)
        # But that might be in the future — use past month instead
        if now.month == 1:
            different_month_start = now.replace(year=now.year - 1, month=12, day=1)
        else:
            different_month_start = now.replace(month=now.month - 1, day=1)

        for i in range(168):  # 1 week in the different month
            start = Timestamp(different_month_start + timedelta(hours=i))
            end = Timestamp(start + timedelta(hours=1))
            power = Watts(500.0)
            intervals.append(
                HomeLoadEnergyInterval(
                    start=start, end=end,
                    power_points=[HomeLoadPowerPoint(timestamp=start, power=power)],
                    energy=WattHours(500.0),
                )
            )
        history = LoadEnergyConsumption(timestamp=Timestamp(now), intervals=intervals)

        provider = TypicalProfileForecastProvider(hours_ahead=3)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 3
        # All should be 500.0 from (dow, hour) fallback
        for interval in forecast.intervals:
            assert float(interval.avg_power) == pytest.approx(500.0, abs=1.0)

    def test_fallback_to_global_avg_when_all_missing(self):
        """When no matching (dow, hour) slots exist, uses global average."""
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        # Create only 2 intervals at very specific times
        intervals = []
        for i in [2, 1]:
            start = Timestamp(now - timedelta(hours=i))
            end = Timestamp(start + timedelta(hours=1))
            power = Watts(750.0)
            intervals.append(
                HomeLoadEnergyInterval(
                    start=start, end=end,
                    power_points=[HomeLoadPowerPoint(timestamp=start, power=power)],
                    energy=WattHours(750.0),
                )
            )
        sparse = LoadEnergyConsumption(timestamp=Timestamp(now), intervals=intervals)

        provider = TypicalProfileForecastProvider(hours_ahead=24)
        forecast = provider.get_consumption_forecast(sparse)
        assert forecast is not None
        assert len(forecast.intervals) == 24

    def test_sparse_history_still_produces_forecast(self):
        """With limited history, provider should still produce valid intervals."""
        provider = TypicalProfileForecastProvider(hours_ahead=6)
        history = _make_sparse_history(48)
        forecast = provider.get_consumption_forecast(history)
        assert forecast is not None
        assert len(forecast.intervals) == 6


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

class TestTypicalProfileConfig:
    """Tests for the config dataclass."""

    def test_defaults(self):
        config = EnergyLoadForecastProviderTypicalProfileConfig()
        assert config.hours_ahead == 24
        assert config.weeks_lookback == 8

    def test_custom_values(self):
        config = EnergyLoadForecastProviderTypicalProfileConfig(hours_ahead=12, weeks_lookback=4)
        assert config.hours_ahead == 12
        assert config.weeks_lookback == 4

    def test_is_valid(self):
        config = EnergyLoadForecastProviderTypicalProfileConfig()
        assert config.is_valid(EnergyLoadForecastProviderAdapter.TYPICAL_PROFILE) is True
        assert config.is_valid(EnergyLoadForecastProviderAdapter.DUMMY) is False

    def test_to_dict_from_dict_roundtrip(self):
        config = EnergyLoadForecastProviderTypicalProfileConfig(hours_ahead=6, weeks_lookback=2)
        d = config.to_dict()
        restored = EnergyLoadForecastProviderTypicalProfileConfig.from_dict(d)
        assert restored == config

    def test_frozen(self):
        config = EnergyLoadForecastProviderTypicalProfileConfig()
        with pytest.raises(AttributeError):
            config.hours_ahead = 10  # type: ignore[misc]
