export const LoadDeviceCategory = {
  CONTROLLABLE: "controllable",
  CONTINUOUS: "continuous",
  SEASONAL: "seasonal",
  OCCASIONAL: "occasional",
} as const;

export type LoadDeviceCategory = typeof LoadDeviceCategory[keyof typeof LoadDeviceCategory];

export interface LoadDevice {
  id?: string;
  name: string;
  category: LoadDeviceCategory;
  enabled: boolean;
  energy_load_forecast_provider_id?: string;
  energy_load_history_provider_id?: string;
}

export interface LoadDeviceCreate {
  name: string;
  category: LoadDeviceCategory;
  enabled: boolean;
  energy_load_forecast_provider_id?: string;
  energy_load_history_provider_id?: string;
}

export interface LoadDeviceUpdate {
  name: string;
  category: LoadDeviceCategory;
  enabled: boolean;
  energy_load_forecast_provider_id?: string;
  energy_load_history_provider_id?: string;
}

export interface HomeLoadsProfile {
  id?: string;
  name: string;
  devices: LoadDevice[];
}
