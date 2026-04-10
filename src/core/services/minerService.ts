import { BaseService } from "./baseService";
import type { Miner, MinerFeature, MinerStateSnapshot } from "../models/miner";

export class MinerService extends BaseService {
  getMiners(): Promise<Miner[]> {
    return this.get<Miner[]>("/miners").getData();
  }

  getMiner(minerId: string): Promise<Miner> {
    return this.get<Miner>(`/miners/${minerId}`).getData();
  }

  addMiner(miner: Miner): Promise<Miner> {
    return this.post<Miner>("/miners", miner).getData();
  }

  updateMiner(minerId: string, miner: Partial<Miner>): Promise<Miner> {
    return this.put<Miner>(`/miners/${minerId}`, miner).getData();
  }

  deleteMiner(minerId: string): Promise<Miner> {
    return this.delete<Miner>(`/miners/${minerId}`).getData();
  }

  startMiner(minerId: string): Promise<Miner> {
    return this.post<Miner>(`/miners/${minerId}/start`, {}).getData();
  }

  stopMiner(minerId: string): Promise<Miner> {
    return this.post<Miner>(`/miners/${minerId}/stop`, {}).getData();
  }

  getMinerStatus(minerId: string): Promise<MinerStateSnapshot> {
    return this.get<MinerStateSnapshot>(`/miners/${minerId}/status`).getData();
  }

  activateMiner(minerId: string): Promise<Miner> {
    return this.post<Miner>(`/miners/${minerId}/activate`, {}).getData();
  }

  deactivateMiner(minerId: string): Promise<Miner> {
    return this.post<Miner>(`/miners/${minerId}/deactivate`, {}).getData();
  }

  setMinerController(minerId: string, controllerId: string): Promise<Miner> {
    return this.post<Miner>(`/miners/${minerId}/set-controller`, {}, { params: { controller_id: controllerId } }).getData();
  }

  unlinkMinerController(minerId: string, controllerId: string): Promise<Miner> {
    return this.post<Miner>(`/miners/${minerId}/unlink-controller`, {}, { params: { controller_id: controllerId } }).getData();
  }

  enableFeature(minerId: string, controllerId: string, featureType: string): Promise<Miner> {
    return this.post<Miner>(`/miners/${minerId}/features/${controllerId}/${featureType}/enable`).getData();
  }

  disableFeature(minerId: string, controllerId: string, featureType: string): Promise<Miner> {
    return this.post<Miner>(`/miners/${minerId}/features/${controllerId}/${featureType}/disable`).getData();
  }

  setFeaturePriority(minerId: string, controllerId: string, featureType: string, priority: number): Promise<Miner> {
    return this.put<Miner>(`/miners/${minerId}/features/${controllerId}/${featureType}/priority`, { priority }).getData();
  }
}
