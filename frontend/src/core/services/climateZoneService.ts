import { BaseService } from "./baseService";
import type { ClimateZone, ClimateZoneReading } from "../models/climateZone";

export class ClimateZoneService extends BaseService {
  getClimateZones(): Promise<ClimateZone[]> {
    return this.get<ClimateZone[]>("/climate-zones").getData();
  }

  getClimateZone(zoneId: string): Promise<ClimateZone> {
    return this.get<ClimateZone>(`/climate-zones/${zoneId}`).getData();
  }

  addClimateZone(zone: ClimateZone): Promise<ClimateZone> {
    return this.post<ClimateZone>("/climate-zones", zone).getData();
  }

  updateClimateZone(zoneId: string, zone: Partial<ClimateZone>): Promise<ClimateZone> {
    return this.put<ClimateZone>(`/climate-zones/${zoneId}`, zone).getData();
  }

  deleteClimateZone(zoneId: string): Promise<ClimateZone> {
    return this.delete<ClimateZone>(`/climate-zones/${zoneId}`).getData();
  }

  getReading(zoneId: string): Promise<ClimateZoneReading | null> {
    return this.get<ClimateZoneReading | null>(`/climate-zones/${zoneId}/reading`).getData();
  }

  linkMonitor(zoneId: string, monitorId: string): Promise<ClimateZone> {
    return this.post<ClimateZone>(`/climate-zones/${zoneId}/monitor/${monitorId}`, {}).getData();
  }

  unlinkMonitor(zoneId: string): Promise<ClimateZone> {
    return this.delete<ClimateZone>(`/climate-zones/${zoneId}/monitor`).getData();
  }
}
