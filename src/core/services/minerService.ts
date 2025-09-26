import { BaseService } from "./baseService";
import type { Miner } from "../models/miner";

export class MinerService extends BaseService {
  getMiners(): Promise<Miner[]> {
    return this.get<Miner[]>("/miners").getData();
  }

  addMiner(miner: Miner): Promise<Miner> {
    return this.post<Miner>("/miners", miner).getData();
  // {
  //   "id": "b271dea2-7fa6-49ef-9d87-955ba00a243d",
  //   "name": "123supa",
  //   "status": "unknown",
  //   "hash_rate": null,
  //   "hash_rate_max": {
  //     "value": 3,
  //     "unit": "TH/s"
  //   },
  //   "power_consumption": null,
  //   "power_consumption_max": 123,
  //   "active": true,
  //   "controller_id": null
  // }
  }
}
