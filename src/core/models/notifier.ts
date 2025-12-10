export type NotifierAdapter = string;

export interface NotifierConfig {
  [key: string]: any;
}

export interface Notifier {
  id?: number;
  name: string;
  adapter_type: NotifierAdapter;
  config?: NotifierConfig;
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
  success: boolean;
  message?: string;
}
