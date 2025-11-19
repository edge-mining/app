import { BaseService } from "./baseService";
import type { EnergySource } from "../models/energySource";

export class EnergySourceService extends BaseService {
  getEnergySources(): Promise<EnergySource[]> {
    return this.get<EnergySource[]>("/energy-sources").getData();
  }

  getEnergySource(sourceId: string): Promise<EnergySource> {
    return this.get<EnergySource>(`/energy-sources/${sourceId}`).getData();
  }

  addEnergySource(energySource: EnergySource): Promise<EnergySource> {
    return this.post<EnergySource>("/energy-sources", energySource).getData();
  }

  updateEnergySource(sourceId: string, energySource: Partial<EnergySource>): Promise<EnergySource> {
    return this.put<EnergySource>(`/energy-sources/${sourceId}`, energySource).getData();
  }

  deleteEnergySource(sourceId: string): Promise<EnergySource> {
    return this.delete<EnergySource>(`/energy-sources/${sourceId}`).getData();
  }

  getEnergySourceTypes(): Promise<string[]> {
    return this.get<string[]>("/energy-sources/types").getData();
  }
}
