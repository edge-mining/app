export interface PolicyRule {
  id?: number;
  policy_id?: number;
  rule_type: string;
  name: string;
  description?: string;
  conditions: Record<string, any>;
  actions: Record<string, any>;
  priority?: number;
  enabled: boolean;
}

export interface Policy {
  id?: number;
  name: string;
  description?: string;
  enabled: boolean;
  rules?: PolicyRule[];
}

export interface PolicyCheckResult {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}
