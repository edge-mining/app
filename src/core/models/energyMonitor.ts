export type EnergyMonitorAdapter = string;

export interface EnergyMonitorConfig {
  [key: string]: any;
}

export interface EnergyMonitor {
  id?: number;
  name: string;
  adapter_type: EnergyMonitorAdapter;
  config?: EnergyMonitorConfig;
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
