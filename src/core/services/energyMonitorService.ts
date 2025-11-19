import { BaseService } from "./baseService";
import type { EnergyMonitor, ConfigSchema } from "../models/energyMonitor";

export class EnergyMonitorService extends BaseService {
  getEnergyMonitors(): Promise<EnergyMonitor[]> {
    return this.get<EnergyMonitor[]>("/energy-monitors").getData();
  }

  getEnergyMonitor(monitorId: string): Promise<EnergyMonitor> {
    return this.get<EnergyMonitor>(`/energy-monitors/${monitorId}`).getData();
  }

  addEnergyMonitor(energyMonitor: EnergyMonitor): Promise<EnergyMonitor> {
    return this.post<EnergyMonitor>("/energy-monitors", energyMonitor).getData();
  }

  updateEnergyMonitor(monitorId: string, energyMonitor: Partial<EnergyMonitor>): Promise<EnergyMonitor> {
    return this.put<EnergyMonitor>(`/energy-monitors/${monitorId}`, energyMonitor).getData();
  }

  deleteEnergyMonitor(monitorId: string): Promise<EnergyMonitor> {
    return this.delete<EnergyMonitor>(`/energy-monitors/${monitorId}`).getData();
  }

  getAdapterTypes(): Promise<string[]> {
    return this.get<string[]>("/energy-monitors/types").getData();
  }

  getConfigSchema(adapterType: string): Promise<ConfigSchema> {
    return this.get<ConfigSchema>(`/energy-monitors/types/${adapterType}/config-schema`).getData();
  }
}
