import { defineStore } from "pinia";
import { ref } from "vue";
import type {
  RuleEngineConfig,
  RuleEngineInfo,
  EvaluationContext,
  EvaluationResult,
  ValidationResult,
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

  function evaluate(context: EvaluationContext): Promise<EvaluationResult> {
    return service.evaluate(context);
  }

  function validate(conditions: any): Promise<ValidationResult> {
    return service.validate(conditions);
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
