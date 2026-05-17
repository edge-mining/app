# Forecast Power Point

## Description

The `ForecastPowerPoint` entity represents a single, precise prediction of power output at a specific moment in time. It serves as the most granular unit of forecasting data in the Edge Mining system, providing timestamped power predictions that enable detailed analysis of expected energy production patterns. These entities are the building blocks for creating comprehensive energy forecasts and supporting sophisticated interpolation algorithms.

## Properties

| Property    | Description                                                               |
| :---------- | :------------------------------------------------------------------------ |
| `timestamp` | The exact time for which this power prediction is made.                   |
| `power`     | The predicted power output at the specified timestamp, measured in Watts. |

## Relationships

- **Belongs to `ForecastInterval`**: Each `ForecastPowerPoint` is contained within a `ForecastInterval` that defines the broader time period.
- **Part of `Forecast` time series**: Multiple power points across intervals form a complete time-series forecast.
- **Used for Interpolation**: Serves as anchor points for calculating power predictions at intermediate times.

## Key Operations

The `ForecastPowerPoint` is primarily a data container, but it participates in several important operations:

- **Linear Interpolation**: Used as reference points for calculating power predictions between available timestamps.
- **Time Series Analysis**: Provides discrete data points for trend analysis and pattern recognition.
- **Chronological Sorting**: Automatically organized in time order within forecast intervals.

## Usage Patterns

- **Precision Forecasting**: Provides exact power predictions for specific moments, enabling precise energy planning.
- **Interpolation Base**: Serves as anchor points for calculating power values at any intermediate time.
- **Trend Analysis**: Multiple power points reveal patterns in expected energy production over time.
- **Real-time Comparison**: Used to compare actual power production against predictions for accuracy assessment.

## Data Processing Integration

- **Interpolation Support**: The `Forecast` entity uses power points to calculate predicted power at any time through linear interpolation between adjacent points.
- **Average Calculations**: Power points within an interval are used to compute average power output for that period.
- **Time-based Queries**: Enables precise power predictions for any requested timestamp within the forecast timeframe.

## Example Applications

- **Mining Schedule Optimization**: Determining exact power availability at planned mining start times.
- **Energy Balance Calculations**: Predicting precise power output for load balancing decisions.
- **Performance Monitoring**: Comparing actual vs. predicted power output for forecast accuracy evaluation.
- **Grid Integration**: Providing precise power predictions for grid export/import planning.

This entity represents the fundamental unit of forecast precision, enabling the Edge Mining system to make highly accurate predictions about energy availability at any specific moment in time.
