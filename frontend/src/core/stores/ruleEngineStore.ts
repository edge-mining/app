import { defineStore } from "pinia";
import { ref } from "vue";
import type {
  RuleEngineConfig,
  RuleEngineInfo,
  RuleEvaluationRequest,
  RuleValidationRequest,
  RuleValidationResult,
} from "../models/ruleEngine";
import { RuleEngineService } from "../services/ruleEngineService";

export const useRuleEngineStore = defineStore("ruleEngine", () => {
  const service = new RuleEngineService();

  // State
  const config = ref<RuleEngineConfig | null>(null);
  const info = ref<RuleEngineInfo | null>(null);

  // Actions
  function loadConfig() {
    return service.getConfig().then((response) => {
      config.value = response;
      return response;
    });
  }

  function loadInfo() {
    return service.getInfo().then((response) => {
      info.value = response;
      return response;
    });
  }

  function evaluate(request: RuleEvaluationRequest): Promise<boolean> {
    return service.evaluate(request);
  }

  function validate(request: RuleValidationRequest): Promise<RuleValidationResult> {
    return service.validate(request);
  }

  return {
    // STATE
    config,
    info,
    // ACTIONS
    loadConfig,
    loadInfo,
    evaluate,
    validate,
  };
});
