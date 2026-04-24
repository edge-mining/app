import { BaseService } from "./baseService";
import type { HomeLoadsProfile, LoadDevice, LoadDeviceCreate, LoadDeviceUpdate } from "../models/homeLoadsProfile";
import type { HomeLoadPowerPoint } from "../models/loadTraining";

export class HomeLoadsProfileService extends BaseService {
  getProfiles(): Promise<HomeLoadsProfile[]> {
    return this.get<HomeLoadsProfile[]>("/home-loads-profiles").getData();
  }

  getProfile(profileId: string): Promise<HomeLoadsProfile> {
    return this.get<HomeLoadsProfile>(`/home-loads-profiles/${profileId}`).getData();
  }

  addProfile(name: string): Promise<HomeLoadsProfile> {
    return this.post<HomeLoadsProfile>(
      `/home-loads-profiles?profile_name=${encodeURIComponent(name)}`,
      {}
    ).getData();
  }

  updateProfile(profileId: string, name: string): Promise<HomeLoadsProfile> {
    return this.put<HomeLoadsProfile>(
      `/home-loads-profiles/${profileId}?profile_new_name=${encodeURIComponent(name)}`,
      {}
    ).getData();
  }

  deleteProfile(profileId: string): Promise<HomeLoadsProfile> {
    return this.delete<HomeLoadsProfile>(`/home-loads-profiles/${profileId}`).getData();
  }

  getDevices(profileId: string): Promise<LoadDevice[]> {
    return this.get<LoadDevice[]>(`/home-loads-profiles/${profileId}/devices`).getData();
  }

  getDevice(profileId: string, deviceId: string): Promise<LoadDevice> {
    return this.get<LoadDevice>(`/home-loads-profiles/${profileId}/devices/${deviceId}`).getData();
  }

  addDevice(profileId: string, device: LoadDeviceCreate): Promise<LoadDevice> {
    return this.post<LoadDevice>(`/home-loads-profiles/${profileId}/devices`, device).getData();
  }

  updateDevice(profileId: string, deviceId: string, device: LoadDeviceUpdate): Promise<LoadDevice> {
    return this.put<LoadDevice>(
      `/home-loads-profiles/${profileId}/devices/${deviceId}`,
      device
    ).getData();
  }

  deleteDevice(profileId: string, deviceId: string): Promise<LoadDevice> {
    return this.delete<LoadDevice>(
      `/home-loads-profiles/${profileId}/devices/${deviceId}`
    ).getData();
  }

  getDeviceHistory(
    profileId: string,
    deviceId: string,
    start: string,
    end: string
  ): Promise<HomeLoadPowerPoint[]> {
    return this.get<HomeLoadPowerPoint[]>(
      `/home-loads-profiles/${profileId}/devices/${deviceId}/history?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`
    ).getData();
  }

  collectDeviceHistory(
    profileId: string,
    deviceId: string,
    lookbackHours: number = 24
  ): Promise<Record<string, string>> {
    return this.post<Record<string, string>>(
      `/home-loads-profiles/${profileId}/devices/${deviceId}/history/collect?lookback_hours=${lookbackHours}`,
      {}
    ).getData();
  }

  clearDeviceHistory(
    profileId: string,
    deviceId: string
  ): Promise<Record<string, string>> {
    return this.delete<Record<string, string>>(
      `/home-loads-profiles/${profileId}/devices/${deviceId}/history`
    ).getData();
  }
}
