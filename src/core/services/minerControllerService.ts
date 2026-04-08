import { BaseService } from "./baseService";
import type { MinerController, MinerControllerAdapter, ConfigSchema } from "../models/minerController";
import type { Miner } from "../models/miner";

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

  getAdapterTypes(): Promise<MinerControllerAdapter[]> {
    return this.get<MinerControllerAdapter[]>("/miner-controllers/types").getData();
  }

  getConfigSchema(adapterType: string): Promise<ConfigSchema> {
    return this.get<ConfigSchema>(`/miner-controllers/types/${adapterType}/config-schema`).getData();
  }

  getExternalServiceType(adapterType: string): Promise<string | null> {
    return this.get<string>(`/miner-controllers/types/${adapterType}/external-services`).getData()
      .then((result) => (result === "null" ? null : result));
  }

  getMinerDetails(controllerId: string): Promise<Miner> {
    return this.get<Miner>(`/miner-controllers/${controllerId}/miner-details`).getData();
  }
}
