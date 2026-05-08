"""Unit tests for LoadEnergyConsumption.mix() — α/β forecast blending."""

from datetime import datetime, timedelta, timezone

import pytest

from edge_mining.domain.common import Timestamp, WattHours, Watts
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    LoadEnergyConsumption,
)


def _ts(offset_hours: int = 0) -> Timestamp:
    """Utility: create a UTC timestamp offset from a fixed base."""
    base = datetime(2026, 4, 25, 10, 0, 0, tzinfo=timezone.utc)
    return Timestamp(base + timedelta(hours=offset_hours))


def _interval(start_h: int, end_h: int, power: float) -> HomeLoadEnergyInterval:
    """Build a 1-hour interval with a single power point and pre-computed energy."""
    start = _ts(start_h)
    end = _ts(end_h)
    pp = HomeLoadPowerPoint(timestamp=start, power=Watts(power))
    duration_hours = (end - start).total_seconds() / 3600.0
    return HomeLoadEnergyInterval(
        start=start,
        end=end,
        energy=WattHours(power * duration_hours),
        power_points=[pp],
    )


def _consumption(*powers: float) -> LoadEnergyConsumption:
    """Build a LoadEnergyConsumption with N hourly intervals starting at hour 0."""
    intervals = [_interval(i, i + 1, p) for i, p in enumerate(powers)]
    return LoadEnergyConsumption(timestamp=_ts(0), intervals=intervals)


class TestMixForecast:
    def test_empty_forecast_returns_unchanged(self):
        empty = LoadEnergyConsumption(timestamp=_ts(0), intervals=[])
        result = LoadEnergyConsumption.mix(empty, Watts(500.0))
        assert result.intervals == []

    def test_default_alpha_beta_equal_weights(self):
        forecast = _consumption(200.0, 300.0, 400.0)
        last_real = Watts(100.0)

        result = LoadEnergyConsumption.mix(forecast, last_real)

        # First interval: 0.5 * 200 + 0.5 * 100 = 150
        assert result.intervals[0].avg_power == pytest.approx(200.0)  # power_points unchanged
        assert float(result.intervals[0].energy) == pytest.approx(150.0)  # blended energy
        # Remaining intervals unchanged
        assert float(result.intervals[1].energy) == float(forecast.intervals[1].energy)
        assert float(result.intervals[2].energy) == float(forecast.intervals[2].energy)

    def test_alpha_1_beta_0_keeps_forecast(self):
        forecast = _consumption(200.0, 300.0)
        last_real = Watts(999.0)

        result = LoadEnergyConsumption.mix(forecast, last_real, alpha=1.0, beta=0.0)

        # 1.0 * 200 + 0.0 * 999 = 200
        assert float(result.intervals[0].energy) == pytest.approx(200.0)

    def test_alpha_0_beta_1_uses_real_only(self):
        forecast = _consumption(200.0, 300.0)
        last_real = Watts(500.0)

        result = LoadEnergyConsumption.mix(forecast, last_real, alpha=0.0, beta=1.0)

        # 0.0 * 200 + 1.0 * 500 = 500
        assert float(result.intervals[0].energy) == pytest.approx(500.0)

    def test_custom_weights(self):
        forecast = _consumption(200.0, 300.0)
        last_real = Watts(100.0)

        result = LoadEnergyConsumption.mix(forecast, last_real, alpha=0.25, beta=0.75)

        # 0.25 * 200 + 0.75 * 100 = 50 + 75 = 125
        assert float(result.intervals[0].energy) == pytest.approx(125.0)

    def test_single_interval_forecast(self):
        forecast = _consumption(400.0)
        last_real = Watts(200.0)

        result = LoadEnergyConsumption.mix(forecast, last_real)

        # 0.5 * 400 + 0.5 * 200 = 300
        assert float(result.intervals[0].energy) == pytest.approx(300.0)
        assert len(result.intervals) == 1

    def test_preserves_timestamp(self):
        forecast = _consumption(100.0, 200.0)
        result = LoadEnergyConsumption.mix(forecast, Watts(50.0))
        assert result.timestamp == forecast.timestamp

    def test_preserves_power_points(self):
        forecast = _consumption(100.0, 200.0)
        result = LoadEnergyConsumption.mix(forecast, Watts(50.0))
        assert result.intervals[0].power_points == forecast.intervals[0].power_points

    def test_preserves_interval_times(self):
        forecast = _consumption(100.0, 200.0, 300.0)
        result = LoadEnergyConsumption.mix(forecast, Watts(50.0))
        for i in range(3):
            assert result.intervals[i].start == forecast.intervals[i].start
            assert result.intervals[i].end == forecast.intervals[i].end

    def test_does_not_mutate_original(self):
        forecast = _consumption(200.0, 300.0)
        original_energy = float(forecast.intervals[0].energy)

        LoadEnergyConsumption.mix(forecast, Watts(100.0))

        assert float(forecast.intervals[0].energy) == original_energy
