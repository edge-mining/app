import { defineStore } from "pinia";
import { ref } from "vue";
import type { ClimateZone, ClimateZoneReading } from "../models/climateZone";
import { ClimateZoneService } from "../services/climateZoneService";

export const useClimateZoneStore = defineStore("climateZone", () => {
  const service = new ClimateZoneService();

  // State
  const climateZones = ref<ClimateZone[]>([]);

  // Actions
  function loadClimateZones() {
    return service.getClimateZones().then((response) => {
      climateZones.value = response;
    });
  }

  function addClimateZone(zone: ClimateZone) {
    return service.addClimateZone(zone);
  }

  function updateClimateZone(zoneId: string, zone: Partial<ClimateZone>) {
    return service.updateClimateZone(zoneId, zone);
  }

  function deleteClimateZone(zoneId: string) {
    return service.deleteClimateZone(zoneId);
  }

  function getReading(zoneId: string): Promise<ClimateZoneReading | null> {
    return service.getReading(zoneId);
  }

  function linkMonitor(zoneId: string, monitorId: string) {
    return service.linkMonitor(zoneId, monitorId);
  }

  function unlinkMonitor(zoneId: string) {
    return service.unlinkMonitor(zoneId);
  }

  return {
    // STATE
    climateZones,
    // ACTIONS
    loadClimateZones,
    addClimateZone,
    updateClimateZone,
    deleteClimateZone,
    getReading,
    linkMonitor,
    unlinkMonitor,
  };
});
