# Notifier

## Description

The `Notifier` entity represents a notification channel configuration within the Edge Mining system. It manages the setup and configuration for specific notification adapters that are responsible for sending alerts, status updates, and system notifications through various communication services such as Telegram, email, or other messaging platforms.

## Properties

| Property              | Description                                                                                                                                                                                    |
| :-------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                | A user-friendly name to identify the notifier (e.g., "Telegram Bot", "Email Alerts").                                                                                                          |
| `adapter_type`        | The type of notification adapter to use, determining which communication protocol or service will be used for sending notifications.                                                           |
| `config`              | Configuration parameters required by the specific notification adapter, such as API keys, chat IDs, email addresses, or connection settings. This can be `None` if no configuration is needed. |
| `external_service_id` | The unique identifier of an external service associated with the notifier, if applicable. This can be `None` for standalone notifiers.                                                         |

## Relationships

- **Used by `EnergyOptimizationUnit`**: An [`EnergyOptimizationUnit`](energy_optimization_unit.md) can have multiple `Notifier` entities to send alerts, status updates, and notifications about energy optimization activities and mining operations.
