// Hash Rate
export interface HashRate {
  value: number;
  unit: string; // e.g., 'TH/s', 'GH/s'
}

export type MinerStatus = 'unknown' | 'off' | 'on' | 'starting' | 'stopping' | 'error';

// Feature types matching backend MinerFeatureType enum
export const MinerFeatureType = {
  // Monitoring (read-only)
  HASHRATE_MONITORING: 'hashrate_monitoring',
  POWER_MONITORING: 'power_monitoring',
  STATUS_MONITORING: 'status_monitoring',
  HASHBOARD_MONITORING: 'hashboard_monitoring',
  INLET_TEMPERATURE_MONITORING: 'inlet_temperature_monitoring',
  OUTLET_TEMPERATURE_MONITORING: 'outlet_temperature_monitoring',
  FAN_SPEED_INTERNAL_MONITORING: 'fan_speed_internal_monitoring',
  FAN_SPEED_EXTERNAL_MONITORING: 'fan_speed_external_monitoring',
  OPERATIONAL_MONITORING: 'operational_monitoring',
  // Control (write)
  MINING_CONTROL: 'mining_control',
  POWER_CONTROL: 'power_control',
  INTERNAL_FAN_CONTROL: 'internal_fan_control',
  EXTERNAL_FAN_CONTROL: 'external_fan_control',
  // Info
  MAX_POWER_DETECTION: 'max_power_detection',
  MAX_HASHRATE_DETECTION: 'max_hashrate_detection',
  DEVICE_INFO_DETECTION: 'device_info_detection',
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

// Temperature value object
export interface Temperature {
  value: number;
  unit: string; // e.g., '°C'
}

// Fan speed value object
export interface FanSpeed {
  value: number;
  unit: string; // e.g., 'RPM'
}

// Voltage value object
export interface Voltage {
  value: number;
  unit: string; // e.g., 'V'
}

// Frequency value object
export interface Frequency {
  value: number;
  unit: string; // e.g., 'MHz'
}

// Hashboard snapshot
export interface HashboardSnapshot {
  index: number;
  chip_temperature?: Temperature;
  board_temperature?: Temperature;
  voltage?: Voltage;
  frequency?: Frequency;
  hash_rate?: HashRate;
  nominal_hash_rate?: HashRate;
  hash_rate_error?: HashRate;
}

// Miner device information (from DeviceInfoPort)
export interface MinerInfo {
  model?: string;
  serial_number?: string;
  firmware_type?: string;
  firmware_version?: string;
  mac_address?: string;
  hostname?: string;
  hashboard_count?: number;
  chip_count?: number;
  fan_count?: number;
}

// Miner limits (max power and hash rate from detection ports)
export interface MinerLimit {
  max_power?: number;
  max_hash_rate?: HashRate;
}

// Runtime operational state
export interface MinerStateSnapshot {
  status: MinerStatus;
  hash_rate?: HashRate;
  power_consumption?: number;
  inlet_temperature?: Temperature;
  outlet_temperature?: Temperature;
  internal_fan_speed: FanSpeed[];
  external_fan_speed?: FanSpeed;
  hashboards: HashboardSnapshot[];
  blocks_found?: number;
  system_uptime?: number;
  max_chip_temperature?: Temperature;
  max_board_temperature?: Temperature;
  avg_chip_temperature?: Temperature;
  avg_board_temperature?: Temperature;
}
