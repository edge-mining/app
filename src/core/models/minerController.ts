export type MinerControllerAdapter = string;

export interface MinerControllerConfig {
  [key: string]: any;
}

export interface MinerController {
  id?: number;
  name: string;
  adapter_type: MinerControllerAdapter;
  config?: MinerControllerConfig;
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
