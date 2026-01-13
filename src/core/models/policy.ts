export type RuleType = "start" | "stop";

export interface AutomationRule {
  id: string;
  name: string;
  description: string;
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
