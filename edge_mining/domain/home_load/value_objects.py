"""Collection of Value Objects for the Home Consumption Analytics domain of the Edge Mining application."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from edge_mining.domain.common import Timestamp, ValueObject, WattHours, Watts


@dataclass(frozen=True)
class HomeLoadPowerPoint(ValueObject):
    """Value Object for a single home loads power consumption point."""

    timestamp: Timestamp
    power: Watts


@dataclass(frozen=True)
class HomeLoadEnergyInterval(ValueObject):
    """
    Value Object for a home load energy consumption interval.
    In most cases this can be understood as a 1 hour time range
    """

    start: Timestamp
    end: Timestamp
    energy: Optional[WattHours] = None
    power_points: List[HomeLoadPowerPoint] = field(default_factory=list)

    def __post_init__(self):
        """Post-initialization validation."""
        if self.start >= self.end:
            raise ValueError("Interval start time must be before end time.")

        for point in self.power_points:
            if not (self.start <= point.timestamp <= self.end):
                raise ValueError(
                    f"Power point timestamp {point.timestamp} is outside the interval [{self.start}, {self.end}]."
                )

    @classmethod
    def create_from_power_points(
        cls,
        start: Timestamp,
        end: Timestamp,
        power_points: List[HomeLoadPowerPoint],
    ) -> "HomeLoadEnergyInterval":
        """Factory method to create an interval and calculate its energy from power points."""
        total_power = sum(point.power for point in power_points)
        avg_power = Watts(total_power / len(power_points)) if power_points else Watts(0.0)

        duration_hours = (end - start).total_seconds() / 3600.0
        calculated_energy = WattHours(avg_power * duration_hours)

        return cls(
            start=start,
            end=end,
            power_points=power_points,
            energy=calculated_energy,
        )

    @property
    def duration(self) -> timedelta:
        """Calculate the duration of the interval"""
        return self.end - self.start

    @property
    def avg_power(self) -> Watts:
        """Calculate the average power over the interval."""
        if not self.power_points:
            return Watts(0.0)

        total_power = sum(point.power for point in self.power_points)
        return Watts(total_power / len(self.power_points)) if total_power else Watts(0.0)


@dataclass(frozen=True)
class LoadEnergyConsumption(ValueObject):
    """
    Value Object for a consumption forecast.
    In most cases intervals can be understood as a list of 1 hour time ranges.
    """

    timestamp: Timestamp = field(default_factory=Timestamp(datetime.now()))
    intervals: List[HomeLoadEnergyInterval] = field(default_factory=list)

    @property
    def avg_energy(self) -> WattHours:
        """Calculate the average energy over all intervals."""
        if not self.intervals:
            return WattHours(0.0)

        total_energy = sum(interval.energy for interval in self.intervals if interval.energy)
        return WattHours(total_energy / len(self.intervals)) if total_energy else WattHours(0.0)

    @property
    def avg_power(self) -> Watts:
        """Calculate the average power over all intervals."""
        if not self.intervals:
            return Watts(0.0)

        total_power = sum(interval.avg_power for interval in self.intervals)
        return Watts(total_power / len(self.intervals)) if total_power else Watts(0.0)
