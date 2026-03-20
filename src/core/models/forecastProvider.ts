export const ForecastProviderAdapter = {
  DUMMY_SOLAR: "dummy_solar",
  HOME_ASSISTANT_API: "home_assistant_api"
} as const;

export type ForecastProviderAdapter = typeof ForecastProviderAdapter[keyof typeof ForecastProviderAdapter];

export interface ForecastProviderConfig {
  [key: string]: any;
}

export interface ForecastProvider {
  id?: string;
  name: string;
  adapter_type: ForecastProviderAdapter;
  config?: ForecastProviderConfig;
  external_service_id?: string;
}

export interface ConfigSchemaProperty {
  type?: string;
  title?: string;
  description?: string;
  default?: any;
  $ref?: string;
  enum?: any[];
  properties?: {
    [key: string]: ConfigSchemaProperty;
  };
  minimum?: number;
  maximum?: number;
  required?: string[];
}

export interface ConfigSchema {
  title: string;
  description: string;
  type: string;
  properties: {
    [key: string]: ConfigSchemaProperty;
  };
  required?: string[];
  $defs?: {
    [key: string]: ConfigSchemaProperty;
  };
}
