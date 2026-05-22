export const ClimateMonitorAdapter = {
  HOME_ASSISTANT_API: "home_assistant_api",
} as const;

export type ClimateMonitorAdapter = typeof ClimateMonitorAdapter[keyof typeof ClimateMonitorAdapter];

export interface ClimateMonitorConfig {
  [key: string]: any;
}

export interface ClimateMonitor {
  id?: string;
  name: string;
  adapter_type: ClimateMonitorAdapter;
  config?: ClimateMonitorConfig;
  external_service_id?: string;
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
  $defs?: {
    [key: string]: ConfigSchemaProperty;
  };
}
