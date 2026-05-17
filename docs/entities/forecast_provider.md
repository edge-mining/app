# Forecast Provider

## Description

The `ForecastProvider` entity acts as an intermediary between the Edge Mining system and external forecasting services that predict future energy production. Its purpose is to abstract the specific details of how to communicate with different types of weather forecasting services or energy prediction platforms. It translates generic forecast requests from the system into specific API calls or protocols that the actual forecasting service understands, providing predictions about future energy generation based on weather conditions and other factors.

## Properties

| Property              | Description                                                                                                                                                                         |
| :-------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                | A user-friendly name for the forecast provider (e.g., "HomeAssistant Forecast", "SolarForecast API").                                                                               |
| `adapter_type`        | Specifies the type of adapter to use for communication. This determines which forecasting service or API will be used. Examples: `DUMMY_SOLAR` (for testing), `HOME_ASSISTANT_API`. |
| `config`              | A set of configuration parameters required by the specific adapter. This could include things like an API key, location coordinates, service endpoints, or authentication tokens.   |
| `external_service_id` | The unique identifier of the external service this provider needs to use, if applicable (e.g., HomeAssistant Service).                                                              |

## Relationships

- **Used by `EnergySource`**: A `ForecastProvider` can be associated with one `EnergySource` entities to provide energy production forecasts. The link is established via the `forecast_provider_id` property in the `EnergySource` entity.
- **Produces `Forecast`**: The provider generates forecast data packaged into `Forecast` entities containing detailed predictions about future energy production.

## Key Operations

The `ForecastProvider` itself doesn't have operations like `get_forecast` directly within its entity definition. Instead, its primary role is defined by its behavior within the system's infrastructure layer. The application uses the `adapter_type` and `config` of the provider to instantiate a specific **Adapter** (e.g., `HomeAssistantAPIForecastProvider`). This adapter then provides the concrete implementation for actions like:

- **`get_forecast()`**: Returns a complete `Forecast` entity containing predicted energy production data over multiple time intervals.
- **Fetching weather-based predictions**: Retrieving solar irradiance forecasts, wind speed predictions, or other weather-dependent factors affecting energy production.
- **Providing time-series forecasts**: Generating detailed predictions with specific power values at different time points.

This design allows the core domain logic to remain independent of the specific forecasting technologies or services used, whether they are commercial weather APIs, machine learning models, or integrated home automation forecasting systems.
