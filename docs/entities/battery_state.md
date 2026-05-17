# Battery State

## Description

The `BatteryState` entity captures the state of a battery at a particular moment in time. It provides detailed information about the battery's charge level, power flow direction, and remaining capacity. This entity is essential for tracking energy storage systems and making informed decisions about energy management.

## Properties

| Property             | Description                                                                                                                                 |
| :------------------- | :------------------------------------------------------------------------------------------------------------------------------------------ |
| `state_of_charge`    | The current charge level of the battery, expressed as a percentage of its nominal capacity.                                                 |
| `remaining_capacity` | The remaining energy stored in the battery, measured in Watt-hours. This can be `None` if not available.                                    |
| `current_power`      | The power currently flowing to or from the battery, measured in Watts. A positive value indicates charging, negative indicates discharging. |
| `timestamp`          | The date and time when the battery state was recorded.                                                                                      |
| `charging_power`     | A computed property that returns the power being used to charge the battery (always a positive value or zero).                              |
| `discharging_power`  | A computed property that returns the power being drawn from the battery (always a positive value or zero).                                  |

## Relationships

- **Snapshot of `Battery`**: `BatteryState` represents the current state of a `Battery` entity at a specific point in time.
- **Part of `EnergyStateSnapshot`**: `BatteryState` is an optional sub-entity within the [`EnergyStateSnapshot`](energy_state_snapshot.md), representing the battery's contribution to the overall energy system state.
