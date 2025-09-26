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

  return {
    //STATE
    miners,
    addMiner,
    // ACTIONS
    loadMiners,
  };
});
