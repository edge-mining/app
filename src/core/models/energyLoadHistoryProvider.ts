export const EnergyLoadHistoryProviderAdapter = {
  DUMMY: "dummy",
  HOME_ASSISTANT_API: "home_assistant_api",
} as const;

export type EnergyLoadHistoryProviderAdapter = typeof EnergyLoadHistoryProviderAdapter[keyof typeof EnergyLoadHistoryProviderAdapter];

export interface EnergyLoadHistoryProviderConfig {
  [key: string]: any;
}

export interface EnergyLoadHistoryProvider {
  id?: string;
  name: string;
  adapter_type: EnergyLoadHistoryProviderAdapter;
  config?: EnergyLoadHistoryProviderConfig;
  external_service_id?: string;
}
