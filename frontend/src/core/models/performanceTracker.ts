import type { ConfigSchema } from "./minerController";

export const MiningPerformanceTrackerAdapter = {
  DUMMY: "dummy",
  OCEAN: "ocean",
  BRAIINS_POOL: "braiins_pool",
} as const;

export type MiningPerformanceTrackerAdapter =
  typeof MiningPerformanceTrackerAdapter[keyof typeof MiningPerformanceTrackerAdapter];

export interface PerformanceTrackerConfig {
  [key: string]: any;
}

export interface PerformanceTracker {
  id?: string;
  name: string;
  adapter_type: MiningPerformanceTrackerAdapter;
  config?: PerformanceTrackerConfig;
  external_service_id?: string;
}

export interface HashRate {
  value: number;
  unit: string;
}

export interface PoolWorkerStats {
  worker_name: string;
  hashrate?: HashRate | null;
  last_share_at?: string | null;
  valid_shares?: number | null;
  stale_shares?: number | null;
  rejected_shares?: number | null;
}

export interface PoolStats {
  current_hashrate?: HashRate | null;
  average_hashrate_24h?: HashRate | null;
  average_hashrate_7d?: HashRate | null;
  unpaid_balance?: number | null;
  estimated_next_payout?: number | null;
  workers: PoolWorkerStats[];
  timestamp: string;
}

export interface MiningReward {
  amount: number;
  timestamp: string;
}

export const PayoutFrequency = {
  DAILY: "daily",
  WEEKLY: "weekly",
  MONTHLY: "monthly",
  THRESHOLD: "threshold",
  UNKNOWN: "unknown",
} as const;

export type PayoutFrequency = typeof PayoutFrequency[keyof typeof PayoutFrequency];

export interface PayoutSchedule {
  frequency: PayoutFrequency;
  threshold?: number | null;
  next_payout_at?: string | null;
}

export interface TrackerTestResult {
  status: string;
  message: string;
}

export type { ConfigSchema };
