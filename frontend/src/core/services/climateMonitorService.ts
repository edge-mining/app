import { BaseService } from "./baseService";
import type { ClimateMonitor, ClimateMonitorAdapter, ConfigSchema } from "../models/climateMonitor";
import type { ExternalServiceAdapter } from "../models/externalService";

export class ClimateMonitorService extends BaseService {
  getClimateMonitors(): Promise<ClimateMonitor[]> {
    return this.get<ClimateMonitor[]>("/climate-monitors").getData();
  }

  getClimateMonitor(monitorId: string): Promise<ClimateMonitor> {
    return this.get<ClimateMonitor>(`/climate-monitors/${monitorId}`).getData();
  }

  addClimateMonitor(monitor: ClimateMonitor): Promise<ClimateMonitor> {
    return this.post<ClimateMonitor>("/climate-monitors", monitor).getData();
  }

  updateClimateMonitor(monitorId: string, monitor: Partial<ClimateMonitor>): Promise<ClimateMonitor> {
    return this.put<ClimateMonitor>(`/climate-monitors/${monitorId}`, monitor).getData();
  }

  deleteClimateMonitor(monitorId: string): Promise<ClimateMonitor> {
    return this.delete<ClimateMonitor>(`/climate-monitors/${monitorId}`).getData();
  }

  getAdapterTypes(): Promise<ClimateMonitorAdapter[]> {
    return this.get<ClimateMonitorAdapter[]>("/climate-monitors/types").getData();
  }

  getConfigSchema(adapterType: string): Promise<ConfigSchema> {
    return this.get<ConfigSchema>(`/climate-monitors/types/${adapterType}/config-schema`).getData();
  }

  getExternalServices(adapterType: string): Promise<ExternalServiceAdapter | null> {
    return this.get<ExternalServiceAdapter | null>(`/climate-monitors/types/${adapterType}/external-services`).getData();
  }

  checkMonitor(monitorId: string): Promise<{ status: string }> {
    return this.post<{ status: string }>(`/climate-monitors/${monitorId}/check`, {}).getData();
  }
}
