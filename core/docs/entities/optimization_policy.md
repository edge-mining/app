# Optimization Policy

## Description

The `OptimizationPolicy` entity represents a comprehensive decision-making framework for automated mining operations in the Edge Mining system. It serves as the central intelligence that determines when to start or stop mining operations based on current energy conditions, forecasts, and predefined automation rules. This entity encapsulates the core optimization logic that enables the system to automatically adapt mining behavior to maximize efficiency and profitability while respecting energy constraints.

## Properties

| Property      | Description                                                                                                          |
| :------------ | :------------------------------------------------------------------------------------------------------------------- |
| `name`        | A user-friendly name to identify the optimization policy (e.g., "Solar Priority Policy", "Grid Cost Optimization").  |
| `description` | Optional detailed description explaining the policy's purpose and optimization strategy.                             |
| `start_rules` | A list of [`AutomationRule`](automation_rule.md) sub-entities that define conditions for starting mining operations. |
| `stop_rules`  | A list of [`AutomationRule`](automation_rule.md) sub-entities that define conditions for stopping mining operations. |

## Relationships

- **Contains [`AutomationRule`](automation_rule.md) sub-entities**: Multiple rules organized into start and stop categories that define the decision-making logic.
- **Uses [`RuleEngine`](rule_engine.md) service**: Collaborates with the rule engine service to evaluate rules against the current context.
- **Processes [`DecisionalContext`](decisional_context.md)**: Analyzes comprehensive system state data to make informed mining decisions.
- **Produces `MiningDecision`**: Generates actionable decisions for the mining system (START_MINING, STOP_MINING, MAINTAIN_STATE).
- **Manages [`Miner`](miner.md) operations**: Indirectly controls miner behavior through decision outputs.

## Key Operations

- **`sort_rules()`**: Organizes automation rules by priority, ensuring higher-priority rules are evaluated first.
- **`decide_next_action()`**: Core decision-making method that analyzes the current system state and returns an appropriate mining decision.

## Decision-Making Logic

The `OptimizationPolicy` implements smart decision logic:

- **Context-Aware Analysis**: Evaluates current miner status to determine which rule set to apply (start rules for OFF miners, stop rules for ON miners).
- **Priority-Based Rule Evaluation**: Processes rules in priority order to ensure the most important conditions are checked first.
- **State-Specific Logic**:
  - For OFF/ERROR/UNKNOWN miners: Evaluates start rules
  - For ON miners: Evaluates stop rules
  - For STARTING/STOPPING miners: Maintains state until confirmation
- **Fail-Safe Behavior**: Defaults to MAINTAIN_STATE when no rules match, ensuring stable operation.

## Rule Processing Workflow

1. **Status Assessment**: Determines current miner operational status
2. **Rule Selection**: Chooses appropriate rule set based on miner status
3. **Priority Sorting**: Organizes rules by priority for optimal evaluation order
4. **Rule Engine Integration**: Loads rules into the rule engine for evaluation
5. **Context Evaluation**: Processes current system context against loaded rules
6. **Decision Generation**: Returns appropriate mining decision based on rule matches

## Usage Patterns

- **Energy Optimization**: Automatically starts mining when excess energy is available and stops when energy is needed elsewhere.
- **Cost Minimization**: Optimizes mining operations based on energy costs and grid pricing.
- **Solar Maximization**: Prioritizes solar energy utilization for sustainable mining operations.
- **Load Balancing**: Coordinates mining operations with household energy consumption patterns.

This entity serves as the brain of the automated mining system, enabling intelligent, context-aware decision-making that adapts to changing energy conditions and operational requirements.
