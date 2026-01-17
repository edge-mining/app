import { defineStore } from "pinia";
import { ref } from "vue";
import type { Miner } from "../models/miner";
import { MinerService } from "../services/minerService";

export const useMinerStore = defineStore("miner", () => {
  const service = new MinerService();

  // State
  const miners = ref<Miner[]>([]);

  // Actions
  function loadMiners() {
    return service.getMiners().then((response) => {
      miners.value = response;
    });
  }

  function addMiner(miner: Miner) {
    return service.addMiner(miner);
  }

  function updateMiner(minerId: string, miner: Partial<Miner>) {
    return service.updateMiner(minerId, miner);
  }

  function deleteMiner(minerId: string) {
    return service.deleteMiner(minerId);
  }

  function startMiner(minerId: string) {
    return service.startMiner(minerId);
  }

  function stopMiner(minerId: string) {
    return service.stopMiner(minerId);
  }

  function activateMiner(minerId: string) {
    return service.activateMiner(minerId);
  }

  function deactivateMiner(minerId: string) {
    return service.deactivateMiner(minerId);
  }

  function getMinerStatus(minerId: string) {
    return service.getMinerStatus(minerId).then((updatedMiner) => {
      // Update the miner in the array with the new status
      const index = miners.value.findIndex(m => m.id?.toString() === minerId);
      if (index !== -1) {
        // Update properties individually to ensure reactivity
        Object.assign(miners.value[index], updatedMiner);
      }
      return updatedMiner;
    });
  }

  return {
    //STATE
    miners,
    // ACTIONS
    loadMiners,
    addMiner,
    updateMiner,
    deleteMiner,
    startMiner,
    stopMiner,
    activateMiner,
    deactivateMiner,
    getMinerStatus,
  };
});
