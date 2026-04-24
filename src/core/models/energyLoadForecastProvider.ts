export const EnergyLoadForecastProviderAdapter = {
  DUMMY: "dummy",
  NAIVE_LAST_HOUR: "naive_last_hour",
  SEASONAL_BASELINE: "seasonal_baseline",
  STATSMODELS: "statsmodels",
  XGBOOST: "xgboost",
} as const;

export type EnergyLoadForecastProviderAdapter = typeof EnergyLoadForecastProviderAdapter[keyof typeof EnergyLoadForecastProviderAdapter];

export interface EnergyLoadForecastProviderConfig {
  [key: string]: any;
}

export interface EnergyLoadForecastProvider {
  id?: string;
  name: string;
  adapter_type: EnergyLoadForecastProviderAdapter;
  config?: EnergyLoadForecastProviderConfig;
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
