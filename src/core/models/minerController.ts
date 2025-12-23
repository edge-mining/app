export type MinerControllerAdapter = string;

export interface MinerControllerConfig {
  [key: string]: any;
}

export interface MinerController {
  id?: number;
  name: string;
  adapter_type: MinerControllerAdapter;
  config?: MinerControllerConfig;
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
