# Energy Optimization Unit

## Description

The `EnergyOptimizationUnit` entity represents a complete optimization configuration that orchestrates automated mining operations within the Edge Mining system. It serves as the central coordination hub that brings together optimization policies, target miners, energy sources, and various monitoring services to create a comprehensive automated mining solution. This entity encapsulates all the components needed to intelligently manage mining operations based on energy availability and optimization strategies.

## Properties

| Property                    | Description                                                                                                                       |
| :-------------------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| `name`                      | A user-friendly name to identify the optimization unit (e.g., "Main Solar Mining Unit", "Grid Cost Optimizer").                   |
| `description`               | Optional detailed description explaining the unit's purpose and optimization strategy.                                            |
| `is_enabled`                | Boolean flag that determines whether the optimization unit is active and should process optimization decisions.                   |
| `policy_id`                 | The unique identifier of the [`OptimizationPolicy`](optimization_policy.md) that defines the decision-making rules for this unit. |
| `target_miner_ids`          | A list of unique identifiers for the [`Miner`](miner.md) entities that this unit will control and optimize.                       |
| `energy_source_id`          | The unique identifier of the [`EnergySource`](energy_source.md) that provides energy data for optimization decisions.             |
| `home_forecast_provider_id` | Optional identifier for a home load forecast provider that predicts household energy consumption patterns.                        |
| `performance_tracker_id`    | Optional identifier for a performance tracking service that monitors mining efficiency and profitability metrics.                 |
| `notifier_ids`              | A list of identifiers for notification services that alert users about optimization decisions and system status changes.          |

## Relationships

- **Uses [`OptimizationPolicy`](optimization_policy.md)**: Each unit is associated with a specific optimization policy that defines the automation rules and decision-making logic.
- **Controls [`Miner`](miner.md) entities**: The unit manages one or more mining devices, coordinating their operations based on optimization decisions.
- **Monitors [`EnergySource`](energy_source.md)**: Connected to an energy source that provides real-time production data and forecasting information.
- **Integrates Home Forecast Providers**: Uses home load forecast providers to understand household energy consumption patterns.
- **Tracks Performance**: Optional integration with mining performance tracking services for efficiency monitoring.
- **Sends Notifications**: Connects to notification services to alert users about system status and decisions.

## Key Operations

- **`add_target_miner(miner_id)`**: Adds a new miner to the list of devices controlled by this optimization unit.
- **`remove_target_miner(miner_id)`**: Removes a miner from the unit's control, stopping optimization for that device.
- **`assign_policy(policy_id)`**: Associates the unit with a specific optimization policy that defines decision-making rules.
- **`assign_energy_source(energy_source_id)`**: Connects the unit to an energy source for monitoring production and consumption data.
- **`assign_home_forecast_provider(home_forecast_provider_id)`**: Integrates household energy consumption forecasting for better optimization decisions.
- **`assign_performance_tracker(performance_tracker_id)`**: Connects performance monitoring services to track mining efficiency.
- **`add_notifier(notifier_id)`**: Adds a notification service to alert users about system status and optimization decisions.
- **`remove_notifier(notifier_id)`**: Removes a notification service from the unit's notification list.
- **`enable()`**: Activates the optimization unit, allowing it to process optimization decisions and control miners.
- **`disable()`**: Deactivates the optimization unit, stopping all automated optimization operations.

## Optimization Workflow

The `EnergyOptimizationUnit` coordinates the following optimization process:

1. **Data Collection**: Gathers real-time energy data from the connected energy source
2. **Context Building**: Assembles a comprehensive decisional context including energy state, forecasts, and miner status
3. **Policy Evaluation**: Uses the assigned optimization policy to evaluate automation rules against current conditions
4. **Decision Making**: Generates mining decisions (start, stop, or maintain state) based on rule evaluation
5. **Action Execution**: Sends control commands to target miners based on optimization decisions
6. **Performance Tracking**: Monitors mining efficiency and system performance through connected trackers
7. **Notification**: Alerts users about important decisions and system status changes

## Configuration Management

- **Modular Design**: Each component (policy, miners, energy source, etc.) can be independently configured and updated
- **Dynamic Reconfiguration**: Components can be added, removed, or changed without stopping the optimization process
- **Enable/Disable Control**: Units can be temporarily disabled for maintenance or testing without losing configuration
- **Multiple Units**: Multiple optimization units can operate simultaneously with different configurations

This entity serves as the orchestration layer that transforms energy data and optimization policies into intelligent, automated mining operations, providing users with a comprehensive solution for energy-efficient bitcoin mining.
