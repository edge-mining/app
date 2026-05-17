# Load State

## Description

The `LoadState` entity represents the energy consumption state of non-mining loads at a specific point in time. This includes all energy-consuming devices and systems in the facility except for the mining equipment itself, providing crucial information for energy balance calculations and optimization decisions.

## Properties

| Property        | Description                                                                                                                                                                   |
| :-------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `current_power` | The amount of power being consumed by the load at the time of measurement, measured in Watts. This represents the instantaneous energy consumption of all non-mining systems. |
| `timestamp`     | The date and time when the load state was recorded, ensuring temporal accuracy for energy consumption measurements.                                                           |

## Relationships

- **Part of `EnergyStateSnapshot`**: `LoadState` is a sub-entity of the [`EnergyStateSnapshot`](energy_state_snapshot.md), representing the consumption component of the overall energy system state.
