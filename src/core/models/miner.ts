// Hash Rate
export interface HashRate {
  value: number;
  unit: string; // e.g., 'TH/s', 'GH/s'
}

export type MinerStatus = 'unknown' | 'off' | 'on' | 'starting' | 'stopping' | 'error';

export interface Miner {
  id?: string;
  name: string;
  model?: string;
  hash_rate_max?: HashRate;
  power_consumption_max?: number;
  active: boolean;
  controller_id?: string;
}

// Runtime operational state
export interface MinerStateSnapshot {
  status: MinerStatus;
  hash_rate?: HashRate;
  power_consumption?: number;
}
