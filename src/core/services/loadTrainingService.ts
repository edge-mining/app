import { BaseService } from "./baseService";
import type { LoadConsumptionModel } from "../models/loadTraining";

export class LoadTrainingService extends BaseService {
  triggerTrainingAll(
    weeksLookback: number = 8
  ): Promise<{ status: string; detail: string }> {
    return this.post<{ status: string; detail: string }>(
      `/training/trigger?weeks_lookback=${weeksLookback}`,
      {}
    ).getData();
  }

  triggerTrainingDevice(
    profileId: string,
    deviceId: string,
    weeksLookback: number = 8
  ): Promise<{ status: string; detail: string }> {
    return this.post<{ status: string; detail: string }>(
      `/home-loads-profiles/${profileId}/devices/${deviceId}/training/trigger?weeks_lookback=${weeksLookback}`,
      {}
    ).getData();
  }

  getModels(deviceId?: string): Promise<LoadConsumptionModel[]> {
    const params = deviceId ? `?device_id=${deviceId}` : "";
    return this.get<LoadConsumptionModel[]>(`/training/models${params}`).getData();
  }
}
