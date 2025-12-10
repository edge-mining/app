import { BaseService } from "./baseService";
import type { ExternalService, ConfigSchema } from "../models/externalService";

export class ExternalServiceService extends BaseService {
  getExternalServices(): Promise<ExternalService[]> {
    return this.get<ExternalService[]>("/external-services").getData();
  }

  getExternalService(serviceId: string): Promise<ExternalService> {
    return this.get<ExternalService>(`/external-services/${serviceId}`).getData();
  }

  addExternalService(externalService: ExternalService): Promise<ExternalService> {
    return this.post<ExternalService>("/external-services", externalService).getData();
  }

  updateExternalService(serviceId: string, externalService: Partial<ExternalService>): Promise<ExternalService> {
    return this.put<ExternalService>(`/external-services/${serviceId}`, externalService).getData();
  }

  deleteExternalService(serviceId: string): Promise<ExternalService> {
    return this.delete<ExternalService>(`/external-services/${serviceId}`).getData();
  }

  getAdapterTypes(): Promise<string[]> {
    return this.get<string[]>("/external-services/types").getData();
  }

  getConfigSchema(adapterType: string): Promise<ConfigSchema> {
    return this.get<ConfigSchema>(`/external-services/types/${adapterType}/config-schema`).getData();
  }
}
