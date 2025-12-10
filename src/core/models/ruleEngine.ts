export interface RuleEngineConfig {
  [key: string]: any;
}

export interface RuleEngineInfo {
  name: string;
  version?: string;
  capabilities?: string[];
  supported_operators?: string[];
  supported_functions?: string[];
}

export interface EvaluationContext {
  [key: string]: any;
}

export interface EvaluationResult {
  success: boolean;
  results?: any[];
  errors?: string[];
}

export interface ValidationResult {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}
