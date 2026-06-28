# Miner

## Description

The `Miner` entity represents a physical or virtual bitcoin mining device in the Edge Mining system. Its primary role is to perform the computational work (hashing) required for mining. This entity holds all the relevant information about a specific miner, such as its operational status, performance metrics, and configuration.

## Properties

| Property                | Description                                                                                                                                              |
| :---------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                  | A user-friendly name to identify the miner (e.g., "Antminer S19 Pro").                                                                                   |
| `status`                | The current operational state of the miner. Possible values are: `ON`, `OFF`, `STARTING`, `STOPPING`, `ERROR`, `UNKNOWN`.                                |
| `hash_rate`             | The current processing power of the miner, measured in Gigahashes or Terahashes per second (GH/s or TH/s). This indicates how fast the miner is working. |
| `hash_rate_max`         | The maximum theoretical hash rate that the miner can achieve.                                                                                            |
| `power_consumption`     | The amount of electricity the miner is currently consuming, measured in Watts.                                                                           |
| `power_consumption_max` | The maximum power the miner can draw.                                                                                                                    |
| `active`                | A boolean flag that indicates if the miner is actively managed by the system. An inactive miner is ignored by the system's control logic.                |
| `controller_id`         | The unique identifier of the `MinerController` that is responsible for managing this miner.                                                              |

## Relationships

- **Managed by `MinerController`**: Each `Miner` instance is associated with a [`MinerController`](miner_controller.md). The controller is responsible for sending commands to the miner, such as `turn_on` and `turn_off`, and for receiving status updates from it. This relationship is established through the `controller_id`.

## Key Operations

- **`turn_on()` / `turn_off()`**: These actions change the intended state of the miner to `STARTING` or `STOPPING`. The actual transition to `ON` or `OFF` depends on the feedback from the physical device, managed via the `MinerController`.
- **`update_status()`**: This operation is used to update the miner's status based on real-world data, such as a change in hash rate or power consumption.
- **`activate()` / `deactivate()`**: These operations control whether the miner is considered part of the active fleet managed by the system.
