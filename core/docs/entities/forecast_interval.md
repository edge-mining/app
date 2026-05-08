# Forecast Interval

## Description

The `ForecastInterval` entity represents a specific time period within a forecast with detailed energy production predictions. It serves as a fundamental building block of the forecasting system, containing both aggregate energy estimates for the entire interval and granular power predictions at specific time points. This entity enables the system to understand energy availability patterns across different time periods.

## Properties

| Property           | Description                                                                                                  |
| :----------------- | :----------------------------------------------------------------------------------------------------------- |
| `start`            | The beginning timestamp of the forecast interval.                                                            |
| `end`              | The ending timestamp of the forecast interval.                                                               |
| `energy`           | Optional total energy expected to be produced during this interval, measured in WattHours.                   |
| `energy_remaining` | Optional remaining energy available in this interval (useful for real-time tracking), measured in WattHours. |
| `power_points`     | A list of `ForecastPowerPoint` sub-entities containing timestamped power predictions within this interval.   |

## Sub-Entities

- **`ForecastPowerPoint`**: Individual prediction points within the interval, each containing:
  - `timestamp`: Specific time for the power prediction
  - `power`: Predicted power output at that moment (in Watts)

## Relationships

- **Belongs to `Forecast`**: Each `ForecastInterval` is part of a larger `Forecast` entity that aggregates multiple intervals.
- **Contains `ForecastPowerPoint` sub-entities**: Multiple timestamped power predictions that provide granular detail within the interval.
- **Used by Optimization Algorithms**: The interval data is analyzed by the system to determine optimal mining operation windows.

## Key Operations

- **`duration`**: Calculated property that returns the time span of the interval as a `timedelta`.
- **`avg_power`**: Calculated property that computes the average power across all power points in the interval, returning the mean predicted power output.

## Data Processing Features

The `ForecastInterval` provides several computational capabilities:

- **Average Power Calculation**: Automatically computes the mean power output across all power points within the interval.
- **Duration Calculation**: Provides the exact time span covered by the interval for energy calculations.
- **Power Point Management**: Organizes multiple granular power predictions within the interval timeframe.
- **Energy Distribution**: Supports both total energy estimates and remaining energy tracking for real-time applications.

## Usage Patterns

- **Energy Planning**: Used to understand total energy availability during specific time windows.
- **Power Profiling**: Provides detailed power variation patterns within the interval through power points.
- **Real-time Monitoring**: Tracks remaining energy as actual production occurs.
- **Optimization Input**: Serves as input data for algorithms that determine optimal mining schedules (_work in progress_).

This entity is essential for translating weather-based predictions into actionable energy production forecasts that the Edge Mining system can use for intelligent operation planning.
