import { BaseService } from "./baseService";
import type {
  PerformanceTracker,
  MiningPerformanceTrackerAdapter,
  ConfigSchema,
  PoolStats,
  PoolWorkerStats,
  MiningReward,
  PayoutSchedule,
  TrackerTestResult,
} from "../models/performanceTracker";

export class PerformanceTrackerService extends BaseService {
  getPerformanceTrackers(): Promise<PerformanceTracker[]> {
    return this.get<PerformanceTracker[]>("/mining-performance-trackers").getData();
  }

  getPerformanceTracker(trackerId: string): Promise<PerformanceTracker> {
    return this.get<PerformanceTracker>(`/mining-performance-trackers/${trackerId}`).getData();
  }

  addPerformanceTracker(tracker: PerformanceTracker): Promise<PerformanceTracker> {
    return this.post<PerformanceTracker>("/mining-performance-trackers", tracker).getData();
  }

  updatePerformanceTracker(
    trackerId: string,
    tracker: Partial<PerformanceTracker>
  ): Promise<PerformanceTracker> {
    return this.put<PerformanceTracker>(
      `/mining-performance-trackers/${trackerId}`,
      tracker
    ).getData();
  }

  deletePerformanceTracker(trackerId: string): Promise<PerformanceTracker> {
    return this.delete<PerformanceTracker>(
      `/mining-performance-trackers/${trackerId}`
    ).getData();
  }

  getAdapterTypes(): Promise<MiningPerformanceTrackerAdapter[]> {
    return this.get<MiningPerformanceTrackerAdapter[]>(
      "/mining-performance-trackers/types"
    ).getData();
  }

  getConfigSchema(adapterType: string): Promise<ConfigSchema> {
    return this.get<ConfigSchema>(
      `/mining-performance-trackers/types/${adapterType}/config-schema`
    ).getData();
  }

  getExternalServiceType(adapterType: string): Promise<string | null> {
    return this.get<string>(
      `/mining-performance-trackers/types/${adapterType}/external-services`
    )
      .getData()
      .then((result) => (result === "null" || result === null ? null : result));
  }

  testPerformanceTracker(trackerId: string): Promise<TrackerTestResult> {
    return this.post<TrackerTestResult>(
      `/mining-performance-trackers/${trackerId}/test`,
      {}
    ).getData();
  }

  getPoolStats(trackerId: string): Promise<PoolStats> {
    return this.get<PoolStats>(
      `/mining-performance-trackers/${trackerId}/stats`
    ).getData();
  }

  getWorkers(trackerId: string): Promise<PoolWorkerStats[]> {
    return this.get<PoolWorkerStats[]>(
      `/mining-performance-trackers/${trackerId}/workers`
    ).getData();
  }

  getRewards(trackerId: string, limit = 10): Promise<MiningReward[]> {
    return this.get<MiningReward[]>(
      `/mining-performance-trackers/${trackerId}/rewards?limit=${limit}`
    ).getData();
  }

  getPayoutSchedule(trackerId: string): Promise<PayoutSchedule> {
    return this.get<PayoutSchedule>(
      `/mining-performance-trackers/${trackerId}/payout-schedule`
    ).getData();
  }
}
