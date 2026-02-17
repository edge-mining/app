import type { EnergyMonitor } from "./energyMonitor";
import type { ForecastProvider } from "./forecastProvider";
import type { MinerController } from "./minerController";
import type { Notifier } from "./notifier";

export type ExternalServiceAdapter = string;

export interface ExternalServiceConfig {
  [key: string]: any;
}

export interface ExternalService {
  id?: string;
  name: string;
  adapter_type: ExternalServiceAdapter;
  config?: ExternalServiceConfig;
}

export type ExternalServiceStatusType = 'connected' | 'disconnected' | 'unauthorized';

export interface ExternalServiceStatus {
  name: string;
  status: ExternalServiceStatusType;
  last_check: string;
  error_message?: string;
}

export interface ExternalServiceLinkedEntities {
  miner_controllers: MinerController[];
  energy_monitors: EnergyMonitor[];
  forecast_providers: ForecastProvider[];
  home_forecast_providers: ForecastProvider[];
  notifiers: Notifier[];
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

