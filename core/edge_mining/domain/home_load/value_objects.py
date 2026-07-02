"""Collection of Value Objects for the Home Consumption Analytics domain of the Edge Mining application."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from edge_mining.domain.common import EntityId, Timestamp, ValueObject, WattHours, Watts
from edge_mining.domain.home_load.common import EnergyLoadForecastProviderAdapter, LoadDeviceCategory


@dataclass(frozen=True)
class HomeLoadPowerPoint(ValueObject):
    """Value Object for a single home loads power consumption point."""

    timestamp: Timestamp
    power: Watts


@dataclass(frozen=True)
class LoadTrainingResult(ValueObject):
    """Outcome of a forecast-model (re)training run for a single LoadDevice.

    ``status`` is one of "trained", "skipped" or "failed". On "trained" the best
    model metadata is filled; on "skipped"/"failed" ``reason`` explains why, so
    callers can surface it to the user.
    """

    device_name: str
    status: str
    reason: Optional[str] = None
    best_adapter: Optional[EnergyLoadForecastProviderAdapter] = None
    best_mae: Optional[float] = None
    samples_used: Optional[int] = None


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
    Value Object for a time series of load energy consumption.
    Intended to be agnostic: can represent history, forecast, per-device or aggregate.
    Intervals are typically 1 hour time ranges.
    """

    timestamp: Timestamp = field(default_factory=Timestamp(datetime.now(timezone.utc)))
    intervals: List[HomeLoadEnergyInterval] = field(default_factory=list)

    @property
    def total_energy(self) -> WattHours:
        """Sum of energy across all intervals."""
        return WattHours(sum(float(i.energy) for i in self.intervals if i.energy is not None))

    @property
    def avg_energy(self) -> WattHours:
        """Average of per-interval energy."""
        if not self.intervals:
            return WattHours(0.0)

        total_energy = sum(float(interval.energy) for interval in self.intervals if interval.energy)
        return WattHours(total_energy / len(self.intervals)) if total_energy else WattHours(0.0)

    @property
    def avg_power(self) -> Watts:
        """Average of per-interval average power."""
        if not self.intervals:
            return Watts(0.0)

        total_power = sum(interval.avg_power for interval in self.intervals)
        return Watts(total_power / len(self.intervals)) if total_power else Watts(0.0)

    @property
    def peak_power(self) -> Watts:
        """Maximum avg_power observed across intervals."""
        if not self.intervals:
            return Watts(0.0)
        return Watts(max(float(i.avg_power) for i in self.intervals))

    def in_window(self, start: Timestamp, end: Timestamp) -> "LoadEnergyConsumption":
        """Return a subset whose intervals overlap the given window [start, end)."""
        if start >= end:
            return LoadEnergyConsumption(timestamp=self.timestamp, intervals=[])
        filtered = [i for i in self.intervals if i.start < end and i.end > start]
        return LoadEnergyConsumption(timestamp=self.timestamp, intervals=filtered)

    def in_next_hours(self, hours: int, now: Optional[Timestamp] = None) -> "LoadEnergyConsumption":
        """Return a subset covering the next `hours` starting from `now` (defaults to datetime.now)."""
        anchor = now if now is not None else Timestamp(datetime.now(timezone.utc))
        return self.in_window(anchor, Timestamp(anchor + timedelta(hours=hours)))

    def in_last_hours(self, hours: int, now: Optional[Timestamp] = None) -> "LoadEnergyConsumption":
        """Return a subset covering the last `hours` up to `now`."""
        anchor = now if now is not None else Timestamp(datetime.now(timezone.utc))
        return self.in_window(Timestamp(anchor - timedelta(hours=hours)), anchor)

    # Pre-computed window properties for rule engine paths
    # e.g. home_load.total_forecast.next_1h.total_energy

    @property
    def next_1h(self) -> "LoadEnergyConsumption":
        """Subset covering the next 1 hour from now."""
        return self.in_next_hours(1)

    @property
    def next_2h(self) -> "LoadEnergyConsumption":
        """Subset covering the next 2 hours from now."""
        return self.in_next_hours(2)

    @property
    def next_4h(self) -> "LoadEnergyConsumption":
        """Subset covering the next 4 hours from now."""
        return self.in_next_hours(4)

    @property
    def next_6h(self) -> "LoadEnergyConsumption":
        """Subset covering the next 6 hours from now."""
        return self.in_next_hours(6)

    @property
    def next_8h(self) -> "LoadEnergyConsumption":
        """Subset covering the next 8 hours from now."""
        return self.in_next_hours(8)

    @property
    def next_12h(self) -> "LoadEnergyConsumption":
        """Subset covering the next 12 hours from now."""
        return self.in_next_hours(12)

    @property
    def next_24h(self) -> "LoadEnergyConsumption":
        """Subset covering the next 24 hours from now."""
        return self.in_next_hours(24)

    @property
    def last_1h(self) -> "LoadEnergyConsumption":
        """Subset covering the last 1 hour up to now."""
        return self.in_last_hours(1)

    @property
    def last_4h(self) -> "LoadEnergyConsumption":
        """Subset covering the last 4 hours up to now."""
        return self.in_last_hours(4)

    @property
    def last_12h(self) -> "LoadEnergyConsumption":
        """Subset covering the last 12 hours up to now."""
        return self.in_last_hours(12)

    @property
    def last_24h(self) -> "LoadEnergyConsumption":
        """Subset covering the last 24 hours up to now."""
        return self.in_last_hours(24)

    @staticmethod
    def mix(
        forecast: "LoadEnergyConsumption",
        last_real_power: Watts,
        alpha: float = 0.5,
        beta: float = 0.5,
    ) -> "LoadEnergyConsumption":
        """Blend the first forecast interval with the last measured power.

        Implements the mix formula:

            P_mix(k) = α · P̂(k) + β · P_real(k-1)

        Only the **first** interval is blended; the remaining forecast is
        returned unchanged.  This improves short-term accuracy when the
        optimisation loop runs frequently (e.g. every 5 s).

        :param forecast: The original forecast consumption.
        :param last_real_power: The most recent measured power value (W).
        :param alpha: Weight for the forecast side (default 0.5).
        :param beta: Weight for the real-measurement side (default 0.5).
        :returns: A new ``LoadEnergyConsumption`` with the blended first interval.
        """
        if not forecast.intervals:
            return forecast

        first = forecast.intervals[0]
        blended_power = Watts(alpha * first.avg_power + beta * float(last_real_power))

        duration_hours = first.duration.total_seconds() / 3600.0
        blended_energy = WattHours(blended_power * duration_hours) if duration_hours > 0 else first.energy

        blended_interval = HomeLoadEnergyInterval(
            start=first.start,
            end=first.end,
            energy=blended_energy,
            power_points=first.power_points,
        )

        new_intervals = [blended_interval] + list(forecast.intervals[1:])
        return LoadEnergyConsumption(timestamp=forecast.timestamp, intervals=new_intervals)


@dataclass(frozen=True)
class LoadDeviceConsumption(ValueObject):
    """Consumption (history + forecast) for a single LoadDevice.

    Binds the generic ``LoadEnergyConsumption`` time series to the identity
    of a LoadDevice so downstream consumers (policy engine, UI) can reason
    per-device without losing track of "who is consuming what".
    """

    device_id: EntityId
    device_name: str
    device_category: LoadDeviceCategory
    history: LoadEnergyConsumption = field(default_factory=LoadEnergyConsumption)
    forecast: LoadEnergyConsumption = field(default_factory=LoadEnergyConsumption)


@dataclass(frozen=True)
class HomeLoadsConsumption(ValueObject):
    """Unified household consumption view for the DecisionalContext.

    Carries:
      - ``per_device``: individual device history+forecast, keyed by unique name.
      - ``total_history`` / ``total_forecast``: aggregated household time series.

    Exposes ``devices`` as a name-indexed mapping for readable rule paths
    (e.g., ``home_load.devices.boiler.forecast.total_energy``).
    """

    per_device: List[LoadDeviceConsumption] = field(default_factory=list)
    total_history: LoadEnergyConsumption = field(default_factory=LoadEnergyConsumption)
    total_forecast: LoadEnergyConsumption = field(default_factory=LoadEnergyConsumption)

    @property
    def devices(self) -> "dict[str, LoadDeviceConsumption]":
        """Device-name-indexed map for rule engine path navigation.

        Relies on the uniqueness invariant enforced by ``HomeLoadsProfile``.
        """
        return {d.device_name: d for d in self.per_device}

    def device_by_name(self, name: str) -> Optional[LoadDeviceConsumption]:
        """Lookup by (unique) device name."""
        return self.devices.get(name)

    def device_by_id(self, device_id: EntityId) -> Optional[LoadDeviceConsumption]:
        """Lookup by device id."""
        return next((d for d in self.per_device if d.device_id == device_id), None)
