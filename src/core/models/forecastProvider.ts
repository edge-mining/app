export type ForecastProviderAdapter = string;

export interface ForecastProviderConfig {
  [key: string]: any;
}

export interface ForecastProvider {
  id?: number;
  name: string;
  adapter_type: ForecastProviderAdapter;
  config?: ForecastProviderConfig;
}

export interface ConfigSchemaProperty {
  type: string;
  title: string;
  description?: string;
  default?: any;
}

export interface ConfigSchema {
  title: string;
  description: string;
  type: string;
  properties: {
    [key: string]: ConfigSchemaProperty;
  };
  required?: string[];
}
