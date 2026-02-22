export type NotifierAdapter = string;

export interface NotifierConfig {
  [key: string]: any;
}

export interface Notifier {
  id?: string;
  name: string;
  adapter_type: NotifierAdapter;
  config?: NotifierConfig;
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
}

export interface TestNotifierResult {
  status: string;
  message?: string;
}
