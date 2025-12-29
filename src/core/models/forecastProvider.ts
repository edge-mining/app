export type ForecastProviderAdapter = string;

export interface ForecastProviderConfig {
  [key: string]: any;
}

export interface ForecastProvider {
  id?: number;
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
