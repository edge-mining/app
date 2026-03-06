import { BaseService } from "./baseService";
import type { MinerController, ConfigSchema } from "../models/minerController";

export class MinerControllerService extends BaseService {
  getMinerControllers(): Promise<MinerController[]> {
    return this.get<MinerController[]>("/miner-controllers").getData();
  }

  getMinerController(controllerId: string): Promise<MinerController> {
    return this.get<MinerController>(`/miner-controllers/${controllerId}`).getData();
  }

  addMinerController(minerController: MinerController): Promise<MinerController> {
    return this.post<MinerController>("/miner-controllers", minerController).getData();
  }

  updateMinerController(controllerId: string, minerController: Partial<MinerController>): Promise<MinerController> {
    return this.put<MinerController>(`/miner-controllers/${controllerId}`, minerController).getData();
  }

  deleteMinerController(controllerId: string): Promise<MinerController> {
    return this.delete<MinerController>(`/miner-controllers/${controllerId}`).getData();
  }

  getAdapterTypes(): Promise<string[]> {
    return this.get<string[]>("/miner-controllers/types").getData();
  }

  getConfigSchema(adapterType: string): Promise<ConfigSchema> {
    return this.get<ConfigSchema>(`/miner-controllers/types/${adapterType}/config-schema`).getData();
  }

  getExternalServiceType(adapterType: string): Promise<string | null> {
    return this.get<string>(`/miner-controllers/types/${adapterType}/external-services`).getData()
      .then((result) => (result === "null" ? null : result));
  }
}
