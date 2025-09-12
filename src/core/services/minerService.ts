import { BaseService } from "./baseService";
import type { Miner } from "../models/miner";

/**
 * Base service class, wraps common http methods for all services.
 * The inheriting services should not use axios call directly.
 */
export class MinerService extends BaseService {
  getMiners(): Promise<Miner[]> {
    return this.get<Miner[]>("/miners").getData();
  }
}
