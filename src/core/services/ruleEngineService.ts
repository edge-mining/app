import { BaseService } from "./baseService";
import type {
  RuleEngineConfig,
  RuleEngineInfo,
  EvaluationContext,
  EvaluationResult,
  RuleValidationRequest,
  RuleValidationResult,
} from "../models/ruleEngine";

export class RuleEngineService extends BaseService {
  getConfig(): Promise<RuleEngineConfig> {
    return this.get<RuleEngineConfig>("/rule-engine/config").getData();
  }

  getInfo(): Promise<RuleEngineInfo> {
    return this.get<RuleEngineInfo>("/rule-engine/info").getData();
  }

  evaluate(context: EvaluationContext): Promise<EvaluationResult> {
    return this.post<EvaluationResult>("/rule-engine/evaluate", context).getData();
  }

  validate(request: RuleValidationRequest): Promise<RuleValidationResult> {
    return this.post<RuleValidationResult>("/rule-engine/validate", request).getData();
  }
}
