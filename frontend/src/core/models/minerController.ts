export const MinerControllerAdapter = {
  DUMMY: "dummy",
  GENERIC_SOCKET_HOME_ASSISTANT_API: "generic_socket_home_assistant_api",
  PYASIC: "pyasic"
} as const;

export type MinerControllerAdapter = typeof MinerControllerAdapter[keyof typeof MinerControllerAdapter];

export interface MinerControllerConfig {
  [key: string]: any;
}

export interface MinerController {
  id?: string;
  name: string;
  adapter_type: MinerControllerAdapter;
  config?: MinerControllerConfig;
  external_service_id?: string;
}

export interface MinerControllerTestConnectionResult {
  success: boolean;
  message: string;
  details?: unknown;
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
