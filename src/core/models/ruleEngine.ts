export interface RuleEngineConfig {
  engine_type: string;
}

export interface RuleEvaluationRequest {
  rules: any[];
  context: Record<string, any>;
  optimization_unit: string;
}

export interface ValidationResult {
  is_valid: boolean;
  validation_errors: string[];
  syntax_errors: string[];
  field_errors: string[];
}

// Operator Types
export type OperatorType =
  | 'eq'           // equal
  | 'ne'           // not equal
  | 'gt'           // greater than
  | 'gte'          // greater than or equal
  | 'lt'           // less than
  | 'lte'          // less than or equal
  | 'in'           // in list/array
  | 'not_in'       // not in list/array
  | 'contains'     // string contains
  | 'starts_with'  // string starts with
  | 'ends_with'    // string ends with
  | 'regex';       // regex match

// Mapping of operators to their symbolic representation
export const OPERATOR_SYMBOLS: Record<OperatorType, string> = {
  'eq': '==',
  'ne': '!=',
  'gt': '>',
  'gte': '>=',
  'lt': '<',
  'lte': '<=',
  'in': '∈',
  'not_in': '∉',
  'contains': '⊃',
  'starts_with': '^',
  'ends_with': '$',
  'regex': '~'
};

// Rule Condition
export interface RuleCondition {
  field: string;
  operator: OperatorType;
  value: number | string | boolean | Array<number | string>;
}

// Logical Group
export interface LogicalGroup {
  all_of?: Array<RuleCondition | LogicalGroup> | null;
  any_of?: Array<RuleCondition | LogicalGroup> | null;
  not_?: RuleCondition | LogicalGroup | null;
}

// Rule Conditions
export type RuleConditions = LogicalGroup | RuleCondition;

// Rule Validation Request
export interface RuleValidationRequest {
  conditions: RuleConditions;
}

// Rule Validation Result
export interface RuleValidationResult {
  is_valid: boolean;
  validation_errors: string[];
  syntax_errors: string[];
  field_errors: string[];
}

// Operator Info
export interface OperatorInfo {
  operator: OperatorType;
  symbol: string;
  description: string;
  example_usage: string;
  supported_types: string[];
}

// Rule Engine Info
export interface RuleEngineInfo {
  supported_engines: string[];
  supported_operators: OperatorInfo[];
  max_nesting_level: number;
  supported_field_types: string[];
}
