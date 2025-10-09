import { BaseService } from "./baseService";
import type { EnergySource } from "../models/energySource";

export class EnergySourceService extends BaseService {
  getEnergySources(): Promise<EnergySource[]> {
    return this.get<EnergySource[]>("/energy-sources").getData();
  }

  addEnergySource(energySource: EnergySource): Promise<EnergySource> {
    return this.post<EnergySource>("/energy-sources", energySource).getData();
  }
}
