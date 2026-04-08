// Hash Rate
export interface HashRate {
  value: number;
  unit: string; // e.g., 'TH/s', 'GH/s'
}

export type MinerStatus = 'unknown' | 'off' | 'on' | 'starting' | 'stopping' | 'error';

// Feature types matching backend MinerFeatureType enum
export const MinerFeatureType = {
  HASHRATE_MONITORING: 'hashrate_monitoring',
  POWER_MONITORING: 'power_monitoring',
  STATUS_MONITORING: 'status_monitoring',
  TEMPERATURE_BOARD_MONITORING: 'temperature_board_monitoring',
  TEMPERATURE_CHIP_MONITORING: 'temperature_chip_monitoring',
  TEMPERATURE_INTAKE_MONITORING: 'temperature_intake_monitoring',
  TEMPERATURE_EXHAUST_MONITORING: 'temperature_exhaust_monitoring',
  FAN_SPEED_INTERNAL_MONITORING: 'fan_speed_internal_monitoring',
  FAN_SPEED_PSU_MONITORING: 'fan_speed_psu_monitoring',
  VOLTAGE_MONITORING: 'voltage_monitoring',
  FREQUENCY_MONITORING: 'frequency_monitoring',
  MINING_CONTROL: 'mining_control',
  POWER_CONTROL: 'power_control',
  FREQUENCY_CONTROL: 'frequency_control',
  FAN_SPEED_CONTROL: 'fan_speed_control',
  MODEL_DETECTION: 'model_detection',
} as const;

export type MinerFeatureType = typeof MinerFeatureType[keyof typeof MinerFeatureType];

export interface MinerFeature {
  feature_type: MinerFeatureType;
  controller_id: string;
  priority: number;
  enabled: boolean;
}

export interface Miner {
  id?: string;
  name: string;
  model?: string;
  hash_rate_max?: HashRate;
  power_consumption_max?: number;
  active: boolean;
  features?: MinerFeature[];
  controller_ids?: string[];
}

// Runtime operational state
export interface MinerStateSnapshot {
  status: MinerStatus;
  hash_rate?: HashRate;
  power_consumption?: number;
  temperature_board?: number;
  temperature_chip?: number;
  temperature_intake?: number;
  temperature_exhaust?: number;
  fan_speed_internal?: number;
  fan_speed_psu?: number;
  voltage?: number;
  frequency?: number;
}
