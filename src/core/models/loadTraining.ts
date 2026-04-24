export interface HomeLoadPowerPoint {
  timestamp: string;
  power: number;
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
}
