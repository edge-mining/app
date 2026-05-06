import { defineStore } from "pinia";
import { ref } from "vue";
import type {
  PerformanceTracker,
  MiningPerformanceTrackerAdapter,
} from "../models/performanceTracker";
import { PerformanceTrackerService } from "../services/performanceTrackerService";

export const usePerformanceTrackerStore = defineStore("performanceTracker", () => {
  const service = new PerformanceTrackerService();

  // State
  const performanceTrackers = ref<PerformanceTracker[]>([]);
  const adapterTypes = ref<MiningPerformanceTrackerAdapter[]>([]);

  // Actions
  function loadPerformanceTrackers() {
    return service.getPerformanceTrackers().then((response) => {
      performanceTrackers.value = response;
    });
  }

  function loadAdapterTypes() {
    return service.getAdapterTypes().then((response) => {
      adapterTypes.value = response;
    });
  }

  function addPerformanceTracker(tracker: PerformanceTracker) {
    return service.addPerformanceTracker(tracker);
  }

  function updatePerformanceTracker(
    trackerId: string,
    tracker: Partial<PerformanceTracker>
  ) {
    return service.updatePerformanceTracker(trackerId, tracker);
  }

  function deletePerformanceTracker(trackerId: string) {
    return service.deletePerformanceTracker(trackerId);
  }

  function testPerformanceTracker(trackerId: string) {
    return service.testPerformanceTracker(trackerId);
  }

  return {
    // STATE
    performanceTrackers,
    adapterTypes,
    // ACTIONS
    loadPerformanceTrackers,
    loadAdapterTypes,
    addPerformanceTracker,
    updatePerformanceTracker,
    deletePerformanceTracker,
    testPerformanceTracker,
  };
});
