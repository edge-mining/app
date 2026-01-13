import { defineStore } from "pinia";
import { ref } from "vue";
import type { OptimizationPolicy, AutomationRule, PolicyCheckResult } from "../models/optimizationPolicy";
import { PolicyService } from "../services/policyService";

export const usePolicyStore = defineStore("policy", () => {
  const service = new PolicyService();

  // State
  const policies = ref<OptimizationPolicy[]>([]);
  const selectedPolicy = ref<OptimizationPolicy | null>(null);
  const checkResult = ref<PolicyCheckResult | null>(null);

  // Policy Actions
  function loadPolicies() {
    return service.getPolicies().then((response) => {
      policies.value = response;
    });
  }

  function loadPolicy(policyId: string) {
    return service.getPolicy(policyId).then((response) => {
      selectedPolicy.value = response;
      return response;
    });
  }

  function addPolicy(policy: OptimizationPolicy) {
    return service.addPolicy(policy);
  }

  function updatePolicy(policyId: string, policy: Partial<OptimizationPolicy>) {
    return service.updatePolicy(policyId, policy);
  }

  function deletePolicy(policyId: string) {
    return service.deletePolicy(policyId);
  }

  function checkPolicy(policyId: string) {
    return service.checkPolicy(policyId).then((response) => {
      checkResult.value = response;
      return response;
    });
  }

  // Rule Actions
  function addRule(policyId: string, rule: AutomationRule) {
    return service.addRule(policyId, rule);
  }

  function getRulesByType(policyId: string, ruleType: string) {
    return service.getRulesByType(policyId, ruleType);
  }

  function getRule(policyId: string, ruleId: string) {
    return service.getRule(policyId, ruleId);
  }

  function updateRule(policyId: string, ruleId: string, rule: Partial<AutomationRule>) {
    return service.updateRule(policyId, ruleId, rule);
  }

  function deleteRule(policyId: string, ruleId: string) {
    return service.deleteRule(policyId, ruleId);
  }

  function enableRule(policyId: string, ruleId: string) {
    return service.enableRule(policyId, ruleId);
  }

  function disableRule(policyId: string, ruleId: string) {
    return service.disableRule(policyId, ruleId);
  }

  return {
    // STATE
    policies,
    selectedPolicy,
    checkResult,
    // POLICY ACTIONS
    loadPolicies,
    loadPolicy,
    addPolicy,
    updatePolicy,
    deletePolicy,
    checkPolicy,
    // RULE ACTIONS
    addRule,
    getRulesByType,
    getRule,
    updateRule,
    deleteRule,
    enableRule,
    disableRule,
  };
});
