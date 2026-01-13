export interface AutomationRule {
  id: string;
  name: string;
  description: string;
  priority: number;
  enabled: boolean;
  conditions: Record<string, any>;
}

export interface OptimizationPolicy {
  id: string;
  name: string;
  description?: string;
  start_rules: AutomationRule[];
  stop_rules: AutomationRule[];
}

export interface PolicyCheckResult {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}
