"""Feature engineering utilities for ML-based home load forecast providers.

Converts LoadEnergyConsumption interval data into structured feature arrays
suitable for scikit-learn / statsmodels / XGBoost models.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from edge_mining.domain.home_load.value_objects import LoadEnergyConsumption


def intervals_to_hourly_series(
    consumption: LoadEnergyConsumption,
) -> List[Tuple[datetime, float]]:
    """Convert intervals to a sorted list of (timestamp, avg_power) pairs.

    Missing hours are NOT filled — that is the caller's responsibility
    (e.g. via ``fill_missing_hours``).
    """
    pairs: List[Tuple[datetime, float]] = []
    for interval in consumption.intervals:
        pairs.append((interval.start, float(interval.avg_power)))
    pairs.sort(key=lambda x: x[0])
    return pairs


def fill_missing_hours(
    series: List[Tuple[datetime, float]],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    fill_value: float = 0.0,
) -> List[Tuple[datetime, float]]:
    """Ensure contiguous hourly coverage by inserting fill_value for missing slots.

    If *start*/*end* are not provided they default to the min/max of the
    existing series.
    """
    if not series:
        return []

    existing = {ts.replace(minute=0, second=0, microsecond=0): power for ts, power in series}
    first = start or min(existing)
    last = end or max(existing)

    result: List[Tuple[datetime, float]] = []
    current = first.replace(minute=0, second=0, microsecond=0)
    last_rounded = last.replace(minute=0, second=0, microsecond=0)
    while current <= last_rounded:
        result.append((current, existing.get(current, fill_value)))
        current += timedelta(hours=1)
    return result


def build_calendar_features(timestamps: List[datetime]) -> List[List[float]]:
    """Build calendar feature vectors for a list of timestamps.

    Each row contains:
        [hour_of_day, day_of_week, is_weekend, month]

    All values are numeric (float) for direct use in sklearn / XGBoost.
    """
    features: List[List[float]] = []
    for ts in timestamps:
        hour = float(ts.hour)
        dow = float(ts.weekday())  # 0=Mon … 6=Sun
        is_weekend = 1.0 if dow >= 5 else 0.0
        month = float(ts.month)
        features.append([hour, dow, is_weekend, month])
    return features


def build_lag_features(
    power_values: List[float],
    lags: Optional[List[int]] = None,
) -> List[List[Optional[float]]]:
    """Build lag feature vectors from a power time series.

    Default lags: 1h, 2h, 3h, 24h (same hour yesterday), 168h (same hour last week).

    Returns a list of rows; each row has one value per lag.
    Positions where the lag is not available are filled with ``None``.
    """
    if lags is None:
        lags = [1, 2, 3, 24, 168]

    rows: List[List[Optional[float]]] = []
    for i in range(len(power_values)):
        row: List[Optional[float]] = []
        for lag in lags:
            idx = i - lag
            row.append(power_values[idx] if idx >= 0 else None)
        rows.append(row)
    return rows


def prepare_supervised_dataset(
    consumption: LoadEnergyConsumption,
    hours_ahead: int = 3,
    lags: Optional[List[int]] = None,
) -> Tuple[List[List[float]], List[float]]:
    """Build X (features) and y (targets) from historical consumption.

    Each sample is one historical hour; features are calendar + lag;
    target is the avg_power ``hours_ahead`` hours later.

    Rows where lags or target are unavailable are dropped.

    Returns (X, y) where X is a list of feature rows and y is a list of targets.
    """
    if lags is None:
        lags = [1, 2, 3, 24, 168]

    series = intervals_to_hourly_series(consumption)
    series = fill_missing_hours(series)

    if not series:
        return [], []

    timestamps = [ts for ts, _ in series]
    powers = [p for _, p in series]
    calendar = build_calendar_features(timestamps)
    lag_rows = build_lag_features(powers, lags=lags)

    max_lag = max(lags) if lags else 0

    X: List[List[float]] = []
    y: List[float] = []

    for i in range(max_lag, len(series) - hours_ahead):
        lag_row = lag_rows[i]
        # skip if any lag is None (should not happen past max_lag, but be safe)
        if any(v is None for v in lag_row):
            continue
        features = calendar[i] + [float(v) for v in lag_row]  # type: ignore[arg-type]
        target = powers[i + hours_ahead]
        X.append(features)
        y.append(target)

    return X, y
