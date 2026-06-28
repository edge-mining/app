# Battery

## Description

The `Battery` entity represents a battery storage system within the energy source. It defines the fundamental characteristics of energy storage capacity and serves as a reference for battery-related operations in the Edge Mining system.

## Properties

| Property           | Description                                                                                                                       |
| :----------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| `nominal_capacity` | The total energy capacity that the battery can hold, measured in Watt-hours. This represents the nominal energy storage capacity. |

## Relationships

- **Part of `EnergySource`**: A `Battery` can be connected to an [`EnergySource`](energy_source.md) to provide energy storage capabilities and used in the [`DecisionalContext`](decisional_context.md).
