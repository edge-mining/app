import { BaseService } from "./baseService";
import type {
  EnergyLoadForecastProvider,
  EnergyLoadForecastProviderAdapter,
  ConfigSchema,
} from "../models/energyLoadForecastProvider";
import type { ExternalServiceAdapter } from "../models/externalService";

export class EnergyLoadForecastProviderService extends BaseService {
  getProviders(): Promise<EnergyLoadForecastProvider[]> {
    return this.get<EnergyLoadForecastProvider[]>("/energy-load-forecast-providers").getData();
  }

  getProvider(providerId: string): Promise<EnergyLoadForecastProvider> {
    return this.get<EnergyLoadForecastProvider>(
      `/energy-load-forecast-providers/${providerId}`
    ).getData();
  }

  addProvider(provider: EnergyLoadForecastProvider): Promise<EnergyLoadForecastProvider> {
    return this.post<EnergyLoadForecastProvider>(
      "/energy-load-forecast-providers",
      provider
    ).getData();
  }

  updateProvider(
    providerId: string,
    provider: Partial<EnergyLoadForecastProvider>
  ): Promise<EnergyLoadForecastProvider> {
    return this.put<EnergyLoadForecastProvider>(
      `/energy-load-forecast-providers/${providerId}`,
      provider
    ).getData();
  }

  deleteProvider(providerId: string): Promise<EnergyLoadForecastProvider> {
    return this.delete<EnergyLoadForecastProvider>(
      `/energy-load-forecast-providers/${providerId}`
    ).getData();
  }

  getAdapterTypes(): Promise<EnergyLoadForecastProviderAdapter[]> {
    return this.get<EnergyLoadForecastProviderAdapter[]>(
      "/energy-load-forecast-providers/types"
    ).getData();
  }

  getConfigSchema(adapterType: string): Promise<ConfigSchema> {
    return this.get<ConfigSchema>(
      `/energy-load-forecast-providers/types/${adapterType}/config-schema`
    ).getData();
  }

  getExternalServices(adapterType: string): Promise<ExternalServiceAdapter | null> {
    return this.get<ExternalServiceAdapter | null>(
      `/energy-load-forecast-providers/types/${adapterType}/external-services`
    ).getData();
  }
}
