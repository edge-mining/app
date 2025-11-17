import { defineStore } from "pinia";
import { ref } from "vue";
import type { EnergyMonitor } from "../models/energyMonitor";
import { EnergyMonitorService } from "../services/energyMonitorService";

export const useEnergyMonitorStore = defineStore("energyMonitor", () => {
  const service = new EnergyMonitorService();

  // State
  const energyMonitors = ref<EnergyMonitor[]>([]);
  const adapterTypes = ref<string[]>([]);

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

  return {
    //STATE
    energyMonitors,
    adapterTypes,
    addEnergyMonitor,
    // ACTIONS
    loadEnergyMonitors,
    loadAdapterTypes,
  };
});
