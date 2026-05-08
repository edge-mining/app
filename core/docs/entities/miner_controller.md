# Miner Controller

## Description

The `MinerController` entity acts as an intermediary between the Edge Mining system and a physical or software-based miner controller. Its purpose is to abstract the specific details of how to communicate with different types of mining hardware or management software. It translates generic commands from the system (like "turn on miner X") into specific API calls or protocols that the actual controller understands.

## Properties

| Property              | Description                                                                                                                                                                        |
| :-------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                | A user-friendly name for the controller (e.g., "HomeAssistant API Controller").                                                                                                    |
| `adapter_type`        | Specifies the type of adapter to use for communication. This determines which communication protocol or API will be used. Examples: `DUMMY` (for testing), `AWESOME_MINER`, `SSH`. |
| `config`              | A set of configuration parameters required by the specific adapter. This could include things like an IP address, API key, entity IDs, username, or password.                      |
| `external_service_id` | The unique identifier of the service this controller needs, if applicable.                                                                                                         |

## Relationships

- **Manages `Miner`**: A `MinerController` is responsible for managing only one [`Miner`](miner.md) entity. It receives requests from the application's service (e.g., "turn on this miner") and uses its adapter to execute these commands on the actual mining hardware. The link between a `Miner` and its `MinerController` is established via the `controller_id` property in the `Miner` entity.

## Key Operations

The `MinerController` itself doesn't have operations like `turn_on` directly within its entity definition. Instead, its primary role is defined by its behavior within the system's infrastructure layer. The application uses the `adapter_type` and `config` of the controller to instantiate a specific **Adapter** (e.g., `GenericSocketHomeAssistantAPIMinerController`). This adapter then provides the concrete implementation for actions like:

- **Starting a miner**
- **Stopping a miner**
- **Fetching real-time data** (hash rate, power consumption)

This design allows the core domain logic to remain independent of the specific technologies used to control the miners.
