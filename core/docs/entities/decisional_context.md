# Decisional Context

## Description

The `DecisionalContext` entity represents a comprehensive snapshot of all relevant system data at the moment a mining decision needs to be made. It serves as the complete information package that optimization policies and automation rules use to evaluate current conditions and make informed decisions about mining operations. This entity aggregates real-time data, forecasts, and system state information into a single, cohesive context for decision-making.

## Properties

| Property                   | Description                                                                                                                       |
| :------------------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| `energy_source`            | The `EnergySource` representing the current energy generation system being monitored.                                             |
| `energy_state`             | An [`EnergyStateSnapshot`](energy_state_snapshot.md) containing real-time energy production, consumption, battery, and grid data. |
| `forecast`                 | Optional [`Forecast`](forecast.md) containing predicted energy production data.                                                   |
| `home_load_forecast`       | Optional [`ConsumptionForecast`](consumption_forecast.md) with predicted household energy consumption patterns.                   |
| `tracker_current_hashrate` | Optional current hash rate performance data from mining operations.                                                               |
| `sun`                      | Optional [`Sun`](sun.md) containing astronomical data for the sun.                                                                |
| `miner`                    | Optional [`Miner`](miner.md) entity representing the mining device whose operation is being decided.                              |
| `timestamp`                | The exact time when this decisional context was created, enabling time-based rule evaluation.                                     |

## Relationships

- **Used by `OptimizationPolicy`**: Provides the complete data context needed for policy decision-making.
- **Evaluated by `AutomationRule`**: Individual rules analyze specific aspects of the context to determine if their conditions are met.
- **Processed by `RuleEngine`**: The rule engine uses context data to evaluate rule conditions and generate decisions.
- **Integrates Multiple Domains**: Combines data from energy, forecast, miner, and home load domains into a unified view.
- **Supports Time-based Decisions**: Timestamp enables time-sensitive rule evaluation and scheduling.

## Key Operations

The `DecisionalContext` is primarily a data container, but it supports several important operational patterns:

- **Context Assembly**: Aggregates data from multiple system components into a single decision-making package.
- **Rule Evaluation Support**: Provides all necessary data for automation rules to assess their conditions.
- **Time-based Analysis**: Enables rules to consider both current state and temporal factors.
- **Cross-domain Integration**: Allows rules to consider interactions between energy, mining, and consumption systems.

## Data Integration Patterns

- **Real-time Data**: Current energy production, consumption, and system states
- **Predictive Data**: Forecasts for energy production and household consumption
- **Performance Data**: Mining operation metrics and hash rate information
- **Environmental Data**: Sun position and astronomical calculations
- **Historical Context**: Time-stamped data for trend analysis

## Usage in Decision-Making

- **Energy Availability Assessment**: Rules can evaluate current production vs. consumption to determine excess energy availability.
- **Future Planning**: Forecast data enables rules to consider upcoming energy conditions before making decisions.
- **Load Balancing**: Home load forecasts help rules ensure household energy needs are prioritized.
- **Solar Optimization**: Sun data enables rules to optimize for peak solar production periods.
- **Performance Monitoring**: Hash rate data allows rules to consider mining efficiency in their decisions.

## Context Validation

- **Miner Requirement**: Critical that the miner property is set, as policies require knowledge of current miner status.
- **Energy State Requirement**: Energy state snapshot is essential for all energy-based decision rules.
- **Optional Forecasts**: Forecast data enhances decision quality but is not always required.
- **Timestamp Accuracy**: Ensures time-based rules can accurately evaluate temporal conditions.

## Decision Support Capabilities

- **Comprehensive Analysis**: Provides complete system view for sophisticated decision-making.
- **Multi-factor Evaluation**: Enables rules to consider multiple simultaneous conditions.
- **Predictive Planning**: Supports forward-looking decisions based on forecast data.
- **Real-time Responsiveness**: Includes current system state for immediate decision needs.
- **Historical Context**: Timestamp enables trend analysis and time-based patterns.

This entity serves as the foundation for intelligent, data-driven mining decisions by providing optimization policies and automation rules with complete, accurate, and timely information about all relevant system conditions.
