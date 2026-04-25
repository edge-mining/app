export interface HomeLoadPowerPoint {
  timestamp: string;
  power: number;
}

export interface HomeLoadEnergyInterval {
  start: string;
  end: string;
  energy: number | null;
  avg_power: number | null;
}

export interface LoadEnergyConsumption {
  timestamp: string;
  intervals: HomeLoadEnergyInterval[];
}

export interface LoadConsumptionModel {
  id: string;
  device_id?: string;
  adapter_type: string;
  trained_at?: string;
  mae?: number;
  rmse?: number;
  samples_used: number;
  is_active: boolean;
  tuning_params?: Record<string, any>;
}
