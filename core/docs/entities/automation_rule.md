# Automation Rule

## Description

The `AutomationRule` entity represents an individual decision-making rule within the Edge Mining optimization system. Each rule defines specific conditions that must be met for the system to take a particular action (start or stop mining). These rules form the building blocks of the optimization logic, allowing for flexible and customizable automation strategies that can adapt to various energy scenarios and operational requirements.

## Properties

| Property      | Description                                                                                                                 |
| :------------ | :-------------------------------------------------------------------------------------------------------------------------- |
| `name`        | A user-friendly name to identify the rule (e.g., "High Solar Production", "Low Battery Threshold", "Peak Grid Hours").      |
| `description` | Detailed description explaining what the rule does and when it should trigger.                                              |
| `priority`    | Numeric priority for rule evaluation, where higher numbers indicate higher priority. Rules are evaluated in priority order. |
| `enabled`     | Boolean flag that determines whether the rule is active. Disabled rules are ignored during evaluation.                      |
| `conditions`  | Dictionary containing the specific conditions and parameters that define when the rule should trigger.                      |

## Relationships

- **Belongs to `OptimizationPolicy`**: Each `AutomationRule` is part of either the _start rules_ or _stop rules_ collection within an `OptimizationPolicy`.
- **Evaluated by `RuleEngine`**: Rules are processed by the rule engine service that interprets the conditions and determines if they match the current context.
- **Uses `DecisionalContext`**: Rule evaluation is performed against comprehensive system state data provided by the decisional context.
- **Influences `MiningDecision`**: When a rule's conditions are met, it contributes to the final mining decision output.

## Key Operations

The `AutomationRule` is primarily a data container, but it participates in several important operations:

- **Condition Evaluation**: The rule's conditions are analyzed by the rule engine against the current system context.
- **Priority Ordering**: Rules are automatically sorted by priority within their parent optimization policy.
- **Enable/Disable Control**: Rules can be dynamically activated or deactivated without removing them from the policy.

## Rule Types and Usage Patterns

- **Energy Production Rules**: Trigger based on current or forecasted energy production levels

  - "Start mining when solar production exceeds 2000W"
  - "Stop mining when production drops below 1000W"

- **Energy Storage Rules**: Based on battery state and capacity

  - "Start mining when battery is above 80% charge"
  - "Stop mining when battery drops below 20%"

- **Grid Interaction Rules**: Consider grid import/export status

  - "Start mining during peak grid hours"
  - "Stop mining when importing energy from grid"

- **Time-Based Rules**: Incorporate scheduling and time constraints

  - "Stop mining at 6 PM for evening peak load"
  - "Start mining only during daylight hours"

- **Forecast-Driven Rules**: Use predicted energy availability

  - "Start mining if next 4 hours show high solar forecast"
  - "Stop mining if weather forecast shows cloudy conditions"

- **Load Management Rules**: Consider household energy consumption
  - "Stop mining when home load exceeds available production"
  - "Start mining only when home needs are satisfied"

## Condition Structure

The `conditions` dictionary contains rule-specific parameters that define the evaluation logic. Common condition types include:

- **Threshold Conditions**: Numeric comparisons (greater than, less than, equals)
- **Time Conditions**: Schedule-based triggers and time ranges
- **State Conditions**: Specific system states or status values
- **Composite Conditions**: Complex logic combining multiple factors
- **Forecast Conditions**: Future-looking predictions and trends

## Priority System

- **High Priority (90-100)**: Critical safety and protection rules
- **Medium Priority (50-89)**: Standard optimization rules
- **Low Priority (1-49)**: Fine-tuning and preference rules
- **Priority 0**: Lowest priority, evaluated last

## Enable/Disable Functionality

- **Dynamic Control**: Rules can be enabled or disabled without system restart
- **Testing and Debugging**: Allows temporary rule deactivation for troubleshooting
- **Seasonal Adjustments**: Rules can be enabled/disabled based on changing conditions
- **Maintenance Mode**: Critical rules can be disabled during system maintenance

This entity provides the granular control needed to implement smart energy optimization strategies, allowing users to define precise conditions for automated mining operations while maintaining flexibility and control over system behavior.
