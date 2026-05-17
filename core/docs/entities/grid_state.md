# Grid State

## Description

The `GridState` entity represents the operational state of the electrical grid connection at a specific point in time. It tracks the bidirectional power flow between the local energy system and the main electrical grid, providing essential information for energy management and optimization decisions.

## Properties

| Property          | Description                                                                                                                                                                                               |
| :---------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `current_power`   | The power currently being exchanged with the grid, measured in Watts. A positive value indicates power is being imported from the grid, while a negative value means power is being exported to the grid. |
| `timestamp`       | The date and time when the grid state was recorded, ensuring temporal accuracy for power flow measurements.                                                                                               |
| `importing_power` | A computed property that returns the power being imported from the grid (always a positive value or zero).                                                                                                |
| `exporting_power` | A computed property that returns the power being exported to the grid (always a positive value or zero).                                                                                                  |

## Relationships

- **State of `Grid`**: `GridState` represents the current operational state of a [`Grid`](grid.md) entity at a specific moment.
- **Part of `EnergyStateSnapshot`**: `GridState` is an optional sub-entity within the [`EnergyStateSnapshot`](energy_state_snapshot.md), representing the grid's contribution to the overall energy system state.
