# Hash Rate

## Description

The `HashRate` entity represents the computational performance metric of a bitcoin mining device. It quantifies the mining power in terms of hash calculations per second, which is a critical indicator of mining efficiency and performance in the Edge Mining system.

## Properties

| Property | Description                                                                                                                         |
| :------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| `value`  | The numerical value of the hash rate, representing the computational performance.                                                   |
| `unit`   | The unit of measurement for the hash rate, with a default of "TH/s" (terahashes per second). Other common units include GH/s, EH/s. |

## Relationships

- **Performance metric for `Miner`**: The `HashRate` serves as a performance indicator for [`Miner`](miner.md) entities, tracking their computational output.
- **Used in `DecisionalContext`**: The `tracker_current_hashrate` in the decision-making context providing the current miner pool performance data for optimization decisions.
