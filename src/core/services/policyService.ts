import { BaseService } from "./baseService";
import type { OptimizationPolicy, AutomationRule, PolicyCheckResult } from "../models/optimizationPolicy";

export class PolicyService extends BaseService {
  // Policy CRUD operations
  getPolicies(): Promise<OptimizationPolicy[]> {
    return this.get<OptimizationPolicy[]>("/policies").getData();
  }

  getPolicy(policyId: string): Promise<OptimizationPolicy> {
    return this.get<OptimizationPolicy>(`/policies/${policyId}`).getData();
  }

  addPolicy(policy: OptimizationPolicy): Promise<OptimizationPolicy> {
    return this.post<OptimizationPolicy>("/policies", policy).getData();
  }

  updatePolicy(policyId: string, policy: Partial<OptimizationPolicy>): Promise<OptimizationPolicy> {
    return this.put<OptimizationPolicy>(`/policies/${policyId}`, policy).getData();
  }

  deletePolicy(policyId: string): Promise<OptimizationPolicy> {
    return this.delete<OptimizationPolicy>(`/policies/${policyId}`).getData();
  }

  checkPolicy(policyId: string): Promise<PolicyCheckResult> {
    return this.get<PolicyCheckResult>(`/policies/${policyId}/check`).getData();
  }

  // Policy Rules CRUD operations
  addRule(policyId: string, rule: AutomationRule): Promise<AutomationRule> {
    return this.post<AutomationRule>(`/policies/${policyId}/rules`, rule).getData();
  }

  getRulesByType(policyId: string, ruleType: string): Promise<AutomationRule[]> {
    return this.get<AutomationRule[]>(`/policies/${policyId}/types/${ruleType}`).getData();
  }

  getRule(policyId: string, ruleId: string): Promise<AutomationRule> {
    return this.get<AutomationRule>(`/policies/${policyId}/rules/${ruleId}`).getData();
  }

  updateRule(policyId: string, ruleId: string, rule: Partial<AutomationRule>): Promise<AutomationRule> {
    return this.put<AutomationRule>(`/policies/${policyId}/rules/${ruleId}`, rule).getData();
  }

  deleteRule(policyId: string, ruleId: string): Promise<AutomationRule> {
    return this.delete<AutomationRule>(`/policies/${policyId}/rules/${ruleId}`).getData();
  }

  enableRule(policyId: string, ruleId: string): Promise<AutomationRule> {
    return this.get<AutomationRule>(`/policies/${policyId}/rules/${ruleId}/enable`).getData();
  }

  disableRule(policyId: string, ruleId: string): Promise<AutomationRule> {
    return this.get<AutomationRule>(`/policies/${policyId}/rules/${ruleId}/disable`).getData();
  }
}
