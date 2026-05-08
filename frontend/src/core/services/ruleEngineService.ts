import { BaseService } from "./baseService";
import type {
  RuleEngineConfig,
  RuleEngineInfo,
  RuleEvaluationRequest,
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

  evaluate(request: RuleEvaluationRequest): Promise<boolean> {
    return this.post<boolean>("/rule-engine/evaluate", request).getData();
  }

  validate(request: RuleValidationRequest): Promise<RuleValidationResult> {
    return this.post<RuleValidationResult>("/rule-engine/validate", request).getData();
  }
}
