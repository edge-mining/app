import { defineStore } from "pinia";
import { ref } from "vue";
import type { HomeLoadsProfile, LoadDevice, LoadDeviceCreate, LoadDeviceUpdate } from "../models/homeLoadsProfile";
import { HomeLoadsProfileService } from "../services/homeLoadsProfileService";
import type { HomeLoadPowerPoint } from "../models/loadTraining";

export const useHomeLoadsProfileStore = defineStore("homeLoadsProfile", () => {
  const service = new HomeLoadsProfileService();

  // State
  const profiles = ref<HomeLoadsProfile[]>([]);
  const selectedProfileId = ref<string | null>(null);

  // Actions
  function loadProfiles() {
    return service.getProfiles().then((response) => {
      profiles.value = response;
      // Auto-select first profile if none selected
      if (!selectedProfileId.value && response.length > 0) {
        selectedProfileId.value = response[0].id ?? null;
      }
    });
  }

  function addProfile(name: string) {
    return service.addProfile(name);
  }

  function updateProfile(profileId: string, name: string) {
    return service.updateProfile(profileId, name);
  }

  function deleteProfile(profileId: string) {
    return service.deleteProfile(profileId);
  }

  function addDevice(profileId: string, device: LoadDeviceCreate) {
    return service.addDevice(profileId, device);
  }

  function updateDevice(profileId: string, deviceId: string, device: LoadDeviceUpdate) {
    return service.updateDevice(profileId, deviceId, device);
  }

  function deleteDevice(profileId: string, deviceId: string) {
    return service.deleteDevice(profileId, deviceId);
  }

  function getDeviceHistory(
    profileId: string,
    deviceId: string,
    start: string,
    end: string
  ): Promise<HomeLoadPowerPoint[]> {
    return service.getDeviceHistory(profileId, deviceId, start, end);
  }

  function collectDeviceHistory(
    profileId: string,
    deviceId: string,
    lookbackHours: number = 24
  ): Promise<Record<string, string>> {
    return service.collectDeviceHistory(profileId, deviceId, lookbackHours);
  }

  function clearDeviceHistory(
    profileId: string,
    deviceId: string
  ): Promise<Record<string, string>> {
    return service.clearDeviceHistory(profileId, deviceId);
  }

  return {
    // STATE
    profiles,
    selectedProfileId,
    // ACTIONS
    loadProfiles,
    addProfile,
    updateProfile,
    deleteProfile,
    addDevice,
    updateDevice,
    deleteDevice,
    getDeviceHistory,
    collectDeviceHistory,
    clearDeviceHistory,
  };
});
