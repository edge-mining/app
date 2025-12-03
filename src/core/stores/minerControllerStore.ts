import { defineStore } from "pinia";
import { ref } from "vue";
import type { MinerController } from "../models/minerController";
import { MinerControllerService } from "../services/minerControllerService";

export const useMinerControllerStore = defineStore("minerController", () => {
  const service = new MinerControllerService();

  // State
  const minerControllers = ref<MinerController[]>([]);
  const adapterTypes = ref<string[]>([]);

  // Actions
  function loadMinerControllers() {
    return service.getMinerControllers().then((response) => {
      minerControllers.value = response;
    });
  }

  function loadAdapterTypes() {
    return service.getAdapterTypes().then((response) => {
      adapterTypes.value = response;
    });
  }

  function addMinerController(minerController: MinerController) {
    return service.addMinerController(minerController);
  }

  function updateMinerController(controllerId: string, minerController: Partial<MinerController>) {
    return service.updateMinerController(controllerId, minerController);
  }

  function deleteMinerController(controllerId: string) {
    return service.deleteMinerController(controllerId);
  }

  return {
    //STATE
    minerControllers,
    adapterTypes,
    // ACTIONS
    loadMinerControllers,
    loadAdapterTypes,
    addMinerController,
    updateMinerController,
    deleteMinerController,
  };
});
