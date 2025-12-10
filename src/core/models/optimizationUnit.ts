export interface OptimizationUnit {
  id?: string;
  name: string;
  description?: string;
  is_enabled: boolean;
  policy_id?: string;
  target_miner_ids: string[];
  energy_source_id?: string;
  home_forecast_provider_id?: string;
  performance_tracker_id?: string;
  notifier_ids: string[];
}

export interface OptimizationUnitCreate {
  name: string;
  description?: string;
  policy_id?: string;
  target_miner_ids?: string[];
  energy_source_id?: string;
  home_forecast_provider_id?: string;
  performance_tracker_id?: string;
  notifier_ids?: string[];
}

export interface OptimizationUnitUpdate {
  name?: string;
  description?: string;
  policy_id?: string;
  target_miner_ids?: string[];
  energy_source_id?: string;
  home_forecast_provider_id?: string;
  performance_tracker_id?: string;
  notifier_ids?: string[];
}
