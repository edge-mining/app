export interface Miner {
  id?: string;
  name: string;
  status: string;
  hash_rate?: HashRateSchema;
  hash_rate_max?: HashRateSchema;
  power_consumption?: number;
  power_consumption_max?: number;
  active: boolean;
  controller_id?: string;
}

export interface HashRateSchema {
  value: number;
  unit: string;
}
