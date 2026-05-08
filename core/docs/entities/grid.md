# Grid

## Description

The `Grid` entity represents the connection to the main electrical grid infrastructure. It defines the contractual and physical limitations of the grid connection, serving as a reference for grid-related operations and energy management decisions in the Edge Mining system.

## Properties

| Property           | Description                                                                                                                                                                                         |
| :----------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `contracted_power` | The maximum power that can be drawn from the grid according to the contract with the utility provider, measured in Watts. This represents the legal and technical limit for grid power consumption. |

## Relationships

- **Current state tracked by `GridState`**: The current operational state of the grid connection is represented by the [`GridState`](grid_state.md) entity, which tracks real-time power flow.
- **Monitored by `EnergyMonitor`**: The [`EnergyMonitor`](energy_monitor.md) uses `Grid` information to understand the constraints and capabilities of the grid connection during energy system monitoring.
- **Part of `EnergySource`**: A `Grid` can be associated with an [`EnergySource`](energy_source.md) to provide grid connectivity for energy import/export operations.
