# Energy Source

## Description

The `EnergySource` entity represents a source of electrical energy in the Edge Mining system. It can be a renewable energy source (like solar panels or wind turbines), a grid connection, or other types of power generation. This entity manages all the relevant information about a specific energy source, such as its type, capacity, connected storage systems, and monitoring configuration.

## Properties

| Property               | Description                                                                                                                          |
| :--------------------- | :----------------------------------------------------------------------------------------------------------------------------------- |
| `name`                 | A user-friendly name to identify the energy source (e.g., "Rooftop Solar Array", "Grid Connection").                                 |
| `type`                 | The type of energy source. Possible values are: `SOLAR`, `WIND`, `GRID`, `HYDROELECTRIC`, `OTHER`.                                   |
| `nominal_power_max`    | The maximum theoretical power output that the energy source can provide, measured in Watts.                                          |
| `storage`              | An optional `Battery` value object representing connected energy storage system with its nominal capacity.                           |
| `grid`                 | An optional `Grid` value object representing grid connection with its contracted power limit.                                        |
| `external_source`      | An optional external power source (e.g., external generator), measured in Watts, for future use.                                     |
| `energy_monitor_id`    | The unique identifier of the `EnergyMonitor` that tracks the real-time performance of this energy source.                            |
| `forecast_provider_id` | The unique identifier of a forecast provider service used to predict future energy production (e.g., weather-based solar forecasts). |

## Relationships

- **Monitored by `EnergyMonitor`**: Each `EnergySource` can be associated with an [`EnergyMonitor`](energy_monitor.md) that tracks its real-time performance metrics. This relationship is established through the `energy_monitor_id`.
- **Has Storage**: An `EnergySource` can be connected to a `Battery` storage system to store energy.
- **Connected to Grid**: An `EnergySource` can be connected to the electrical `Grid` to import/export energy.
- **Uses Forecast Provider**: An `EnergySource` can use external forecast services to predict future energy production based on weather conditions or other factors.

## Key Operations

- **`connect_to_grid(grid)`**: Connects the energy source to the electrical grid with specified contracted power limits.
- **`disconnect_from_grid()`**: Disconnects the energy source from the electrical grid.
- **`connect_to_external_source(external_source)`**: Connects an external power source (like a generator) to supplement energy production.
- **`disconnect_from_external_source()`**: Disconnects the external power source.
- **`connect_to_storage(storage)`**: Connects a battery storage system to store excess energy production.
- **`disconnect_from_storage()`**: Disconnects the battery storage system.
- **`use_energy_monitor(energy_monitor_id)`**: Associates an energy monitor with this source to track real-time performance metrics.
- **`use_forecast_provider(forecast_provider_id)`**: Associates a forecast provider service to predict future energy production.
