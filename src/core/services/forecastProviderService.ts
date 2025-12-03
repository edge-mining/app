import { BaseService } from "./baseService";
import type { ForecastProvider, ConfigSchema } from "../models/forecastProvider";

export class ForecastProviderService extends BaseService {
  getForecastProviders(): Promise<ForecastProvider[]> {
    return this.get<ForecastProvider[]>("/forecast-providers").getData();
  }

  getForecastProvider(providerId: string): Promise<ForecastProvider> {
    return this.get<ForecastProvider>(`/forecast-providers/${providerId}`).getData();
  }

  addForecastProvider(forecastProvider: ForecastProvider): Promise<ForecastProvider> {
    return this.post<ForecastProvider>("/forecast-providers", forecastProvider).getData();
  }

  updateForecastProvider(providerId: string, forecastProvider: Partial<ForecastProvider>): Promise<ForecastProvider> {
    return this.put<ForecastProvider>(`/forecast-providers/${providerId}`, forecastProvider).getData();
  }

  deleteForecastProvider(providerId: string): Promise<ForecastProvider> {
    return this.delete<ForecastProvider>(`/forecast-providers/${providerId}`).getData();
  }

  getAdapterTypes(): Promise<string[]> {
    return this.get<string[]>("/forecast-providers/types").getData();
  }

  getConfigSchema(adapterType: string): Promise<ConfigSchema> {
    return this.get<ConfigSchema>(`/forecast-providers/types/${adapterType}/config-schema`).getData();
  }
}
