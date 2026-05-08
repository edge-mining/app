"""Unit tests for LoadEnergyConsumption extended window properties (F2 — 24h horizon)."""

from datetime import datetime, timedelta, timezone

import pytest

from edge_mining.domain.common import Timestamp, WattHours, Watts
from edge_mining.domain.home_load.value_objects import (
    HomeLoadEnergyInterval,
    HomeLoadPowerPoint,
    LoadEnergyConsumption,
)

# Fixed "now" used as anchor for all tests
_NOW = datetime(2026, 4, 25, 12, 0, 0, tzinfo=timezone.utc)


def _ts(offset_hours: float = 0) -> Timestamp:
    return Timestamp(_NOW + timedelta(hours=offset_hours))


def _interval(start_h: float, end_h: float, power: float = 100.0) -> HomeLoadEnergyInterval:
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


def _make_24h_forecast() -> LoadEnergyConsumption:
    """Build a 24-hour forecast with one interval per hour starting at _NOW."""
    intervals = [_interval(h, h + 1, power=float(100 + h * 10)) for h in range(24)]
    return LoadEnergyConsumption(timestamp=_ts(0), intervals=intervals)


def _make_24h_history() -> LoadEnergyConsumption:
    """Build a 24-hour history ending at _NOW."""
    intervals = [_interval(-24 + h, -23 + h, power=float(50 + h * 5)) for h in range(24)]
    return LoadEnergyConsumption(timestamp=_ts(0), intervals=intervals)


class TestExtendedNextWindowProperties:
    """Verify next_Xh properties return correct number of intervals."""

    def test_next_1h(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(1, now=_ts(0))
        assert len(subset.intervals) == 1

    def test_next_2h(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(2, now=_ts(0))
        assert len(subset.intervals) == 2

    def test_next_4h(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(4, now=_ts(0))
        assert len(subset.intervals) == 4

    def test_next_6h(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(6, now=_ts(0))
        assert len(subset.intervals) == 6

    def test_next_8h(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(8, now=_ts(0))
        assert len(subset.intervals) == 8

    def test_next_12h(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(12, now=_ts(0))
        assert len(subset.intervals) == 12

    def test_next_24h(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(24, now=_ts(0))
        assert len(subset.intervals) == 24

    def test_next_24h_total_energy(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(24, now=_ts(0))
        assert float(subset.total_energy) == float(forecast.total_energy)


class TestExtendedLastWindowProperties:
    """Verify last_Xh properties return correct number of intervals."""

    def test_last_1h(self):
        history = _make_24h_history()
        subset = history.in_last_hours(1, now=_ts(0))
        assert len(subset.intervals) == 1

    def test_last_4h(self):
        history = _make_24h_history()
        subset = history.in_last_hours(4, now=_ts(0))
        assert len(subset.intervals) == 4

    def test_last_12h(self):
        history = _make_24h_history()
        subset = history.in_last_hours(12, now=_ts(0))
        assert len(subset.intervals) == 12

    def test_last_24h(self):
        history = _make_24h_history()
        subset = history.in_last_hours(24, now=_ts(0))
        assert len(subset.intervals) == 24

    def test_last_24h_total_energy(self):
        history = _make_24h_history()
        subset = history.in_last_hours(24, now=_ts(0))
        assert float(subset.total_energy) == float(history.total_energy)


class TestWindowAggregates:
    """Verify energy/power aggregates on windowed subsets."""

    def test_next_6h_avg_power(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(6, now=_ts(0))
        # Intervals 0..5 have power 100,110,120,130,140,150 → avg = 125
        assert float(subset.avg_power) == pytest.approx(125.0)

    def test_next_6h_peak_power(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(6, now=_ts(0))
        assert float(subset.peak_power) == pytest.approx(150.0)

    def test_next_12h_total_energy(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(12, now=_ts(0))
        # Powers: 100,110,...,210 → sum = 12 * 100 + 10*(0+1+..+11) = 1200+660 = 1860
        # Each 1h interval → energy = power, so total = 1860
        assert float(subset.total_energy) == pytest.approx(1860.0)

    def test_partial_window_returns_overlapping_intervals(self):
        """Window that starts mid-interval still returns that interval."""
        forecast = _make_24h_forecast()
        subset = forecast.in_window(_ts(0.5), _ts(2.5))
        # Intervals [0,1), [1,2), [2,3) all overlap [0.5, 2.5)
        assert len(subset.intervals) == 3

    def test_empty_window(self):
        forecast = _make_24h_forecast()
        subset = forecast.in_next_hours(1, now=_ts(100))
        assert len(subset.intervals) == 0
        assert float(subset.total_energy) == 0.0
