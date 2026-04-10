import { defineStore } from "pinia";
import { ref } from "vue";
import type { Miner, MinerFeature, MinerStateSnapshot } from "../models/miner";
import { MinerService } from "../services/minerService";

export const useMinerStore = defineStore("miner", () => {
  const service = new MinerService();

  // State
  const miners = ref<Miner[]>([]);
  const minerStates = ref<Map<string, MinerStateSnapshot>>(new Map());

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
    return service.getMinerStatus(minerId).then((snapshot) => {
      // Store the runtime state snapshot in the map
      const newMap = new Map(minerStates.value);
      newMap.set(minerId, snapshot);
      minerStates.value = newMap;
      return snapshot;
    });
  }

  function getMinerState(minerId: string): MinerStateSnapshot | undefined {
    return minerStates.value.get(minerId);
  }

  function setMinerController(minerId: string, controllerId: string) {
    return service.setMinerController(minerId, controllerId);
  }

  function unlinkMinerController(minerId: string, controllerId: string) {
    return service.unlinkMinerController(minerId, controllerId);
  }

  function enableFeature(minerId: string, controllerId: string, featureType: string) {
    return service.enableFeature(minerId, controllerId, featureType);
  }

  function disableFeature(minerId: string, controllerId: string, featureType: string) {
    return service.disableFeature(minerId, controllerId, featureType);
  }

  function setFeaturePriority(minerId: string, controllerId: string, featureType: string, priority: number) {
    return service.setFeaturePriority(minerId, controllerId, featureType, priority);
  }

  return {
    //STATE
    miners,
    minerStates,
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
    getMinerState,
    setMinerController,
    unlinkMinerController,
    enableFeature,
    disableFeature,
    setFeaturePriority,
  };
});
