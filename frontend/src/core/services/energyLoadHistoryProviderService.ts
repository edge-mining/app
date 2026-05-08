import { BaseService } from "./baseService";
import type {
  EnergyLoadHistoryProvider,
  EnergyLoadHistoryProviderAdapter,
} from "../models/energyLoadHistoryProvider";
import type { ConfigSchema } from "../models/energyLoadForecastProvider";
import type { ExternalServiceAdapter } from "../models/externalService";

export class EnergyLoadHistoryProviderService extends BaseService {
  getProviders(): Promise<EnergyLoadHistoryProvider[]> {
    return this.get<EnergyLoadHistoryProvider[]>("/energy-load-history-providers").getData();
  }

  getProvider(providerId: string): Promise<EnergyLoadHistoryProvider> {
    return this.get<EnergyLoadHistoryProvider>(
      `/energy-load-history-providers/${providerId}`
    ).getData();
  }

  addProvider(provider: EnergyLoadHistoryProvider): Promise<EnergyLoadHistoryProvider> {
    return this.post<EnergyLoadHistoryProvider>(
      "/energy-load-history-providers",
      provider
    ).getData();
  }

  updateProvider(
    providerId: string,
    provider: Partial<EnergyLoadHistoryProvider>
  ): Promise<EnergyLoadHistoryProvider> {
    return this.put<EnergyLoadHistoryProvider>(
      `/energy-load-history-providers/${providerId}`,
      provider
    ).getData();
  }

  deleteProvider(providerId: string): Promise<EnergyLoadHistoryProvider> {
    return this.delete<EnergyLoadHistoryProvider>(
      `/energy-load-history-providers/${providerId}`
    ).getData();
  }

  getAdapterTypes(): Promise<EnergyLoadHistoryProviderAdapter[]> {
    return this.get<EnergyLoadHistoryProviderAdapter[]>(
      "/energy-load-history-providers/types"
    ).getData();
  }

  getConfigSchema(adapterType: string): Promise<ConfigSchema> {
    return this.get<ConfigSchema>(
      `/energy-load-history-providers/types/${adapterType}/config-schema`
    ).getData();
  }

  getExternalServices(adapterType: string): Promise<ExternalServiceAdapter | null> {
    return this.get<ExternalServiceAdapter | null>(
      `/energy-load-history-providers/types/${adapterType}/external-services`
    ).getData();
  }
}
