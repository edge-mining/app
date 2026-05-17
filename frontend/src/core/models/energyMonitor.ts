export const EnergyMonitorAdapter = {
  DUMMY_SOLAR: "dummy_solar",
  HOME_ASSISTANT_API: "home_assistant_api",
  HOME_ASSISTANT_MQTT: "home_assistant_mqtt"
} as const;

export type EnergyMonitorAdapter = typeof EnergyMonitorAdapter[keyof typeof EnergyMonitorAdapter];

export interface EnergyMonitorConfig {
  [key: string]: any;
}

export interface EnergyMonitor {
  id?: string;
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
