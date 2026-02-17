export type ExternalServiceAdapter = string;

export interface ExternalServiceConfig {
  [key: string]: any;
}

export interface ExternalService {
  id?: number;
  name: string;
  adapter_type: ExternalServiceAdapter;
  config?: ExternalServiceConfig;
}

export type ExternalServiceStatusEnum = 'connected' | 'disconnected' | 'error' | 'unknown';

export interface ExternalServiceStatus {
  name: string;
  status: ExternalServiceStatusEnum;
  last_check: string; // ISO 8601 datetime string
  error_message?: string;
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

