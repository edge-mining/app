# Sun

## Description

The `Sun` entity contains comprehensive astronomical data and solar position information crucial for automation rules in the Edge Mining system. It provides detailed information about daily solar patterns, including sunrise and sunset times, solar angles, and daylight duration calculations. This entity enables the system to understand solar energy potential based on astronomical factors.

## Properties

| Property    | Description                                                                                                 |
| :---------- | :---------------------------------------------------------------------------------------------------------- |
| `dawn`      | The time in the morning when the sun is a specific number of degrees below the horizon (astronomical dawn). |
| `sunrise`   | The time in the morning when the top of the sun breaks the horizon and becomes visible.                     |
| `noon`      | The time when the sun reaches its highest point directly above the observer (solar noon).                   |
| `midnight`  | The time when the sun is at its lowest point below the horizon (solar midnight).                            |
| `sunset`    | The time in the evening when the sun disappears below the horizon.                                          |
| `dusk`      | The time in the evening when the sun is a specific number of degrees below the horizon (astronomical dusk). |
| `daylight`  | The total duration when the sun is above the horizon (between sunrise and sunset).                          |
| `night`     | The duration between astronomical dusk of one day and astronomical dawn of the next day.                    |
| `twilight`  | The duration of twilight periods (between dawn and sunrise, or between sunset and dusk).                    |
| `azimuth`   | Optional: The number of degrees clockwise from North at which the sun can be observed.                      |
| `zenith`    | Optional: The angle of the sun measured down from directly above the observer.                              |
| `elevation` | Optional: The number of degrees up from the horizon at which the sun can be observed.                       |

## Relationships

- **Used by `DecisionalContext`**: A `Sun` is part of the [`DecisionalContext`](decisional_context.md), providing crucial information about the sun's position and daylight patterns for decision-making.

## Key Operations

- **`time_before_sunrise`**: Returns the time remaining until sunrise, or None if sunrise has already occurred.
- **`time_after_sunrise`**: Returns the duration that has elapsed since sunrise.
- **`time_before_sunset`**: Returns the time remaining until sunset, or None if sunset has already occurred.
- **`time_after_sunset`**: Returns the duration that has elapsed since sunset.

## Solar Position Data

The `Sun` entity provides comprehensive solar geometry information:

- **Azimuth Angle**: Directional orientation of the sun for optimal solar panel positioning calculations.
- **Zenith Angle**: Solar elevation data for irradiance calculations and shading analysis.
- **Elevation Angle**: Height of the sun above the horizon for direct solar exposure assessment.

## Usage Patterns

- **Solar Energy Optimization**: Determining optimal times for solar energy production based on sun position.
- **Daylight Planning**: Understanding available daylight hours for energy generation planning.
- **Seasonal Adjustments**: Adapting mining schedules based on changing daylight patterns throughout the year.

## Time-based Calculations

The entity provides several computed properties for real-time solar planning:

- **Sunrise/Sunset Timing**: Dynamic calculation of time remaining until key solar events.
- **Daylight Duration**: Total available sunlight hours for energy production planning.
- **Twilight Periods**: Extended periods of reduced sunlight that may still contribute to solar generation.
- **Night Duration**: Complete darkness periods when solar generation is not possible.

## Integration with Forecasting

- **Weather Correlation**: Combines astronomical data with weather forecasts for enhanced solar predictions.
- **Irradiance Modeling**: Provides the geometric foundation for calculating expected solar irradiance.
- **Seasonal Adaptation**: Enables forecasting systems to account for changing solar patterns throughout the year.
- **Geographic Accuracy**: Supports location-specific solar calculations based on local astronomical conditions.

This entity is essential for any solar-based energy forecasting, providing the astronomical foundation that enables accurate prediction of solar energy availability throughout different times of day and seasons.
