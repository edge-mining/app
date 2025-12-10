import { BaseService } from "./baseService";
import type { Policy, PolicyRule, PolicyCheckResult } from "../models/policy";

export class PolicyService extends BaseService {
  // Policy CRUD operations
  getPolicies(): Promise<Policy[]> {
    return this.get<Policy[]>("/policies").getData();
  }

  getPolicy(policyId: string): Promise<Policy> {
    return this.get<Policy>(`/policies/${policyId}`).getData();
  }

  addPolicy(policy: Policy): Promise<Policy> {
    return this.post<Policy>("/policies", policy).getData();
  }

  updatePolicy(policyId: string, policy: Partial<Policy>): Promise<Policy> {
    return this.put<Policy>(`/policies/${policyId}`, policy).getData();
  }

  deletePolicy(policyId: string): Promise<Policy> {
    return this.delete<Policy>(`/policies/${policyId}`).getData();
  }

  checkPolicy(policyId: string): Promise<PolicyCheckResult> {
    return this.get<PolicyCheckResult>(`/policies/${policyId}/check`).getData();
  }

  // Policy Rules CRUD operations
  addRule(policyId: string, rule: PolicyRule): Promise<PolicyRule> {
    return this.post<PolicyRule>(`/policies/${policyId}/rules`, rule).getData();
  }

  getRulesByType(policyId: string, ruleType: string): Promise<PolicyRule[]> {
    return this.get<PolicyRule[]>(`/policies/${policyId}/types/${ruleType}`).getData();
  }

  getRule(policyId: string, ruleId: string): Promise<PolicyRule> {
    return this.get<PolicyRule>(`/policies/${policyId}/rules/${ruleId}`).getData();
  }

  updateRule(policyId: string, ruleId: string, rule: Partial<PolicyRule>): Promise<PolicyRule> {
    return this.put<PolicyRule>(`/policies/${policyId}/rules/${ruleId}`, rule).getData();
  }

  deleteRule(policyId: string, ruleId: string): Promise<PolicyRule> {
    return this.delete<PolicyRule>(`/policies/${policyId}/rules/${ruleId}`).getData();
  }

  enableRule(policyId: string, ruleId: string): Promise<PolicyRule> {
    return this.get<PolicyRule>(`/policies/${policyId}/rules/${ruleId}/enable`).getData();
  }

  disableRule(policyId: string, ruleId: string): Promise<PolicyRule> {
    return this.get<PolicyRule>(`/policies/${policyId}/rules/${ruleId}/disable`).getData();
  }
}
