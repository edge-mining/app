import { defineStore } from "pinia";
import { ref } from "vue";
import type { ClimateMonitor, ClimateMonitorAdapter } from "../models/climateMonitor";
import { ClimateMonitorService } from "../services/climateMonitorService";

export const useClimateMonitorStore = defineStore("climateMonitor", () => {
  const service = new ClimateMonitorService();

  // State
  const climateMonitors = ref<ClimateMonitor[]>([]);
  const adapterTypes = ref<ClimateMonitorAdapter[]>([]);

  // Actions
  function loadClimateMonitors() {
    return service.getClimateMonitors().then((response) => {
      climateMonitors.value = response;
    });
  }

  function loadAdapterTypes() {
    return service.getAdapterTypes().then((response) => {
      adapterTypes.value = response;
    });
  }

  function addClimateMonitor(monitor: ClimateMonitor) {
    return service.addClimateMonitor(monitor);
  }

  function updateClimateMonitor(monitorId: string, monitor: Partial<ClimateMonitor>) {
    return service.updateClimateMonitor(monitorId, monitor);
  }

  function deleteClimateMonitor(monitorId: string) {
    return service.deleteClimateMonitor(monitorId);
  }

  function externalServices(adapterType: string) {
    return service.getExternalServices(adapterType);
  }

  function checkMonitor(monitorId: string) {
    return service.checkMonitor(monitorId);
  }

  return {
    // STATE
    climateMonitors,
    adapterTypes,
    // ACTIONS
    loadClimateMonitors,
    loadAdapterTypes,
    addClimateMonitor,
    updateClimateMonitor,
    deleteClimateMonitor,
    externalServices,
    checkMonitor,
  };
});
