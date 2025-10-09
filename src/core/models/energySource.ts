export const EnergySourceType = {
  SOLAR: "solar",
  WIND: "wind",
  GRID: "grid",
  HYDROELECTRIC: "hydroelectric",
  OTHER: "other",
} as const;

export type EnergySourceType = typeof EnergySourceType[keyof typeof EnergySourceType];

export interface StorageSchema {
  nominal_capacity: number;
}

export interface GridSchema {
  contracted_power: number;
}

export interface EnergySource {
  id?: number;
  name: string;
  type: EnergySourceType;
  nominal_power_max?: number;
  storage?: StorageSchema;
  grid?: GridSchema;
  external_source?: number;
  energy_monitor_id?: string;
  forecast_provider_id?: string;
}
