import type { EnergySource, EnergyStateSnapshot } from "./energySource";
import type { Forecast, Sun } from "./forecast";
import type { ConsumptionForecast } from "./homeLoad";
import type { Miner, HashRate } from "./miner";

export type RuleType = "start" | "stop";

export interface AutomationRule {
  id: string;
  name: string;
  description?: string;
  priority: number;
  enabled: boolean;
  conditions: Record<string, any>;
}

export interface Metadata {
  author?: string;
  version?: number;
  created?: string;
  last_modified?: string;
}

export interface OptimizationPolicy {
  id: string;
  name: string;
  description?: string;
  start_rules: AutomationRule[];
  stop_rules: AutomationRule[];
  metadata?: Metadata;
}

export interface PolicyCheckResult {
  valid: boolean;
  policy_id: string;
  policy_name?: string;
  errors: string[];
  warnings: string[];
  start_rules_count: number;
  stop_rules_count: number;
  enabled_start_rules_count: number;
  enabled_stop_rules_count: number;
}

export interface DecisionalContextField {
  path: string;
  type: string;
  description: string;
  is_optional: boolean;
  values: string[] | null;
  children: DecisionalContextField[] | null;
}

export interface DecisionalContextStructure {
  fields: DecisionalContextField[];
  total_fields: number;
}

// Decisional Context - aggregates all domain data for decision making
export interface DecisionalContext {
  energy_source?: EnergySource;
  energy_state?: EnergyStateSnapshot;
  forecast?: Forecast;
  home_load_forecast?: ConsumptionForecast;
  tracker_current_hashrate?: HashRate;
  sun?: Sun;
  miner?: Miner;
  timestamp: string; // ISO datetime
}
