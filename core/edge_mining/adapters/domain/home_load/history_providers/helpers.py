"""Shared helpers for home load history provider adapters."""

from datetime import timedelta
from typing import List, Optional

from edge_mining.domain.common import Timestamp, WattHours
from edge_mining.domain.home_load.value_objects import HomeLoadEnergyInterval, HomeLoadPowerPoint


def group_power_points_into_intervals(
    power_points: List[HomeLoadPowerPoint],
    start: Optional[Timestamp] = None,
    end: Optional[Timestamp] = None,
) -> List[HomeLoadEnergyInterval]:
    """Group power points into contiguous 1-hour intervals.

    Intervals walk forward from ``start`` (or first point) by 1-hour steps
    up to ``end`` (or last point). Empty intervals contribute zero energy
    so downstream consumers see a contiguous timeline.
    """
    if not power_points and (start is None or end is None):
        return []

    sorted_points = sorted(power_points, key=lambda p: p.timestamp)

    if start is None:
        start = sorted_points[0].timestamp
    if end is None:
        end = sorted_points[-1].timestamp
    if start >= end:
        raise ValueError("Start timestamp must be before end timestamp.")

    intervals: List[HomeLoadEnergyInterval] = []
    current_start = start
    while current_start < end:
        current_end = min(current_start + timedelta(hours=1), end)

        interval_points = [p for p in sorted_points if current_start <= p.timestamp < current_end]

        if interval_points:
            intervals.append(
                HomeLoadEnergyInterval.create_from_power_points(
                    start=current_start,
                    end=current_end,
                    power_points=interval_points,
                )
            )
        else:
            intervals.append(
                HomeLoadEnergyInterval(
                    start=current_start,
                    end=current_end,
                    energy=WattHours(0.0),
                    power_points=[],
                )
            )

        current_start = current_end

    return intervals
