import { defineStore } from "pinia";
import { ref } from "vue";
import type { EnergySource } from "../models/energySource";
import { EnergySourceService } from "../services/energySourceService";

export const useEnergySourceStore = defineStore("energySource", () => {
  const service = new EnergySourceService();

  // State
  const energySources = ref<EnergySource[]>([]);

  // Actions
  function loadEnergySources() {
    return service.getEnergySources().then((response) => {
      energySources.value = response;
    });
  }

  function addEnergySource(energySource: EnergySource) {
    return service.addEnergySource(energySource);
  }

  return {
    //STATE
    energySources,
    addEnergySource,
    // ACTIONS
    loadEnergySources,
  };
});
