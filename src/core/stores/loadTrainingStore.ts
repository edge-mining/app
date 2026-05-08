import { defineStore } from "pinia";
import { ref } from "vue";
import type { LoadConsumptionModel } from "../models/loadTraining";
import { LoadTrainingService } from "../services/loadTrainingService";

export const useLoadTrainingStore = defineStore("loadTraining", () => {
  const service = new LoadTrainingService();

  // State
  const models = ref<LoadConsumptionModel[]>([]);
  const trainingInProgress = ref(false);

  // Actions
  function loadModels(deviceId?: string) {
    return service.getModels(deviceId).then((response) => {
      models.value = response;
    });
  }

  function triggerTrainingAll(weeksLookback: number = 8) {
    trainingInProgress.value = true;
    return service
      .triggerTrainingAll(weeksLookback)
      .finally(() => {
        trainingInProgress.value = false;
      });
  }

  function triggerTrainingDevice(
    profileId: string,
    deviceId: string,
    weeksLookback: number = 8
  ) {
    trainingInProgress.value = true;
    return service
      .triggerTrainingDevice(profileId, deviceId, weeksLookback)
      .finally(() => {
        trainingInProgress.value = false;
      });
  }

  function deleteModel(modelId: string) {
    return service.deleteModel(modelId).then(() => {
      models.value = models.value.filter((m) => m.id !== modelId);
    });
  }

  return {
    // STATE
    models,
    trainingInProgress,
    // ACTIONS
    loadModels,
    triggerTrainingAll,
    triggerTrainingDevice,
    deleteModel,
  };
});
