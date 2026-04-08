import { defineStore } from "pinia";
import { ref } from "vue";
import type { EnergyMonitor, EnergyMonitorAdapter } from "../models/energyMonitor";
import { EnergyMonitorService } from "../services/energyMonitorService";

export const useEnergyMonitorStore = defineStore("energyMonitor", () => {
  const service = new EnergyMonitorService();

  // State
  const energyMonitors = ref<EnergyMonitor[]>([]);
  const adapterTypes = ref<EnergyMonitorAdapter[]>([]);

  // Actions
  function loadEnergyMonitors() {
    return service.getEnergyMonitors().then((response) => {
      energyMonitors.value = response;
    });
  }

  function loadAdapterTypes() {
    return service.getAdapterTypes().then((response) => {
      adapterTypes.value = response;
    });
  }

  function addEnergyMonitor(energyMonitor: EnergyMonitor) {
    return service.addEnergyMonitor(energyMonitor);
  }

  function updateEnergyMonitor(monitorId: string, energyMonitor: Partial<EnergyMonitor>) {
    return service.updateEnergyMonitor(monitorId, energyMonitor);
  }

  function deleteEnergyMonitor(monitorId: string) {
    return service.deleteEnergyMonitor(monitorId);
  }

  function externalServices(adapterType: string) {
    return service.getExternalServices(adapterType);
  }

  return {
    //STATE
    energyMonitors,
    adapterTypes,
    // ACTIONS
    loadEnergyMonitors,
    loadAdapterTypes,
    addEnergyMonitor,
    updateEnergyMonitor,
    deleteEnergyMonitor,
    externalServices,
  };
});
