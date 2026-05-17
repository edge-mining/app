# Energy Monitor

## Description

The `EnergyMonitor` entity acts as an intermediary between the Edge Mining system and physical or software-based energy monitoring devices. Its purpose is to abstract the specific details of how to communicate with different types of energy monitoring hardware or services. It translates generic energy monitoring requests from the system into specific API calls or protocols that the actual monitoring device understands, providing real-time data about energy production, consumption, and storage.

## Properties

| Property              | Description                                                                                                                                                                                                   |
| :-------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `name`                | A user-friendly name for the energy monitor (e.g., "Home Assistant Solar Monitor", "SolarEdge Inverter Monitor").                                                                                             |
| `adapter_type`        | Specifies the type of adapter to use for communication. This determines which communication protocol or API will be used. Examples: `DUMMY_SOLAR` (for testing), `HOME_ASSISTANT_API`, `HOME_ASSISTANT_MQTT`. |
| `config`              | A set of configuration parameters required by the specific adapter. This could include things like an IP address, API key, entity IDs, MQTT topics, username, or password.                                    |
| `external_service_id` | The unique identifier of the external service this monitor connects to, if applicable (e.g., Home Assistant Service ID).                                                                                      |

## Relationships

- **Monitors `EnergySource`**: An `EnergyMonitor` is responsible for monitoring one `EnergySource` entity. It receives requests from the Optimization Service and uses its adapter to fetch real-time data from the actual monitoring hardware or service. The link between an `EnergySource` and its `EnergyMonitor` is established via the `energy_monitor_id` property in the `EnergySource` entity.
- **Produces `EnergyStateSnapshot`**: The monitor collects comprehensive energy data and packages it into an `EnergyStateSnapshot` that contains all current system metrics.
- **Tracks `BatteryState`**: When monitoring energy storage systems, the monitor provides detailed battery information including state of charge, remaining capacity, and charging/discharging power.
- **Monitors `GridState`**: For grid-connected systems, the monitor tracks power import/export status and current grid interaction metrics.
- **Measures `LoadState`**: The monitor tracks current energy consumption (excluding mining loads).

## Key Operations

The `EnergyMonitor` itself doesn't have operations like `get_production` directly within its entity definition. Instead, its primary role is defined by its behavior within the system's infrastructure layer. The application uses the `adapter_type` and `config` of the monitor to instantiate a specific **Adapter** (e.g., `HomeAssistantAPIEnergyMonitor`). This adapter then provides the concrete implementation for actions like:

- **`get_current_energy_state()`**: Returns a complete `EnergyStateSnapshot` containing all current energy system metrics including production, consumption, battery status, and grid interaction.
- **Fetching real-time energy production data**: Current power output from renewable sources (solar panels, wind turbines, etc.), measured in Watts.
- **Retrieving energy consumption metrics**: Current load state with timestamped power measurements, excluding mining operations.
- **Monitoring battery status**: Comprehensive battery metrics including:
  - State of charge (as percentage)
  - Remaining capacity (in WattHours)
  - Current charging/discharging power (Watts, positive when charging, negative when discharging)
  - Calculated charging and discharging power properties
- **Tracking grid interaction**: Grid state monitoring including:
  - Current power flow (Watts, positive when importing, negative when exporting)
  - Calculated importing and exporting power properties
  - Grid connection status
- **Collecting external source data**: Monitoring of external power sources like generators for supplementary energy.

## Data Structures

The `EnergyMonitor` works with several sub-entities to provide structured energy data:

- **`EnergyStateSnapshot`**: A comprehensive snapshot containing:

  - `production` (Watts): Current energy production
  - `consumption` (LoadState): Current load excluding miners
  - `battery` (BatteryState, optional): Battery status if present
  - `grid` (GridState, optional): Grid interaction if connected
  - `external_source` (Watts, optional): External generator power
  - `timestamp`: When the snapshot was taken

- **`BatteryState`**: Detailed battery information including state of charge, capacity, and power flow with computed charging/discharging properties.

- **`GridState`**: Grid interaction data with computed import/export power calculations.

- **`LoadState`**: Timestamped power consumption measurements for system loads.

This design allows the core domain logic to remain independent of the specific technologies used to monitor energy systems, whether they are hardware-based monitoring devices, cloud services, or home automation platforms.
