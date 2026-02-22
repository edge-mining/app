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
  id?: string;
  name: string;
  type: EnergySourceType;
  nominal_power_max?: number;
  storage?: StorageSchema;
  grid?: GridSchema;
  external_source?: number;
  energy_monitor_id?: string;
  forecast_provider_id?: string;
}

// Battery State with computed fields
export interface BatteryState {
  state_of_charge: number; // 0-100
  remaining_capacity?: number; // WattHours
  current_power: number; // Watts (positive=charging, negative=discharging)
  timestamp: string; // ISO datetime
  readonly charging_power?: number; // Computed: max(current_power, 0)
  readonly discharging_power?: number; // Computed: max(-current_power, 0)
}

// Grid State with computed fields
export interface GridState {
  current_power: number; // Watts (positive=importing, negative=exporting)
  timestamp: string; // ISO datetime
  readonly importing_power?: number; // Computed: max(current_power, 0)
  readonly exporting_power?: number; // Computed: max(-current_power, 0)
}

// Load State
export interface LoadState {
  current_power: number; // Watts
  timestamp: string; // ISO datetime
}

// Energy State Snapshot
export interface EnergyStateSnapshot {
  production: number; // Watts
  consumption: LoadState;
  battery?: BatteryState;
  grid?: GridState;
  external_source?: number; // Watts
  timestamp: string; // ISO datetime
}

// Factory functions for computed fields
export function createBatteryState(data: Omit<BatteryState, 'charging_power' | 'discharging_power'>): BatteryState {
  return {
    ...data,
    get charging_power() {
      return Math.max(data.current_power, 0);
    },
    get discharging_power() {
      return Math.abs(Math.min(data.current_power, 0));
    },
  };
}

export function createGridState(data: Omit<GridState, 'importing_power' | 'exporting_power'>): GridState {
  return {
    ...data,
    get importing_power() {
      return Math.max(data.current_power, 0);
    },
    get exporting_power() {
      return Math.abs(Math.min(data.current_power, 0));
    },
  };
}
