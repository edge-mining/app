import { defineStore } from "pinia";
import { ref } from "vue";
import type { OptimizationUnit, OptimizationUnitCreate, OptimizationUnitUpdate } from "../models/optimizationUnit";
import { OptimizationUnitService } from "../services/optimizationUnitService";

export const useOptimizationUnitStore = defineStore("optimizationUnit", () => {
  const service = new OptimizationUnitService();

  // State
  const optimizationUnits = ref<OptimizationUnit[]>([]);

  // Basic CRUD Actions
  function loadOptimizationUnits() {
    return service.getOptimizationUnits().then((response) => {
      optimizationUnits.value = response;
    });
  }

  function getOptimizationUnit(unitId: string) {
    return service.getOptimizationUnit(unitId);
  }

  function addOptimizationUnit(unit: OptimizationUnitCreate) {
    return service.addOptimizationUnit(unit);
  }

  function updateOptimizationUnit(unitId: string, unit: OptimizationUnitUpdate) {
    return service.updateOptimizationUnit(unitId, unit);
  }

  function deleteOptimizationUnit(unitId: string) {
    return service.deleteOptimizationUnit(unitId);
  }

  // Enable/Disable Actions
  function enableOptimizationUnit(unitId: string) {
    return service.enableOptimizationUnit(unitId);
  }

  function disableOptimizationUnit(unitId: string) {
    return service.disableOptimizationUnit(unitId);
  }

  // Assignment Actions
  function assignEnergySource(unitId: string, energySourceId: string) {
    return service.assignEnergySource(unitId, energySourceId);
  }

  function assignPolicy(unitId: string, policyId: string) {
    return service.assignPolicy(unitId, policyId);
  }

  // Miner Actions
  function assignMiners(unitId: string, minerIds: string[]) {
    return service.assignMiners(unitId, minerIds);
  }

  function addMiner(unitId: string, minerId: string) {
    return service.addMiner(unitId, minerId);
  }

  function removeMiner(unitId: string, minerId: string) {
    return service.removeMiner(unitId, minerId);
  }

  // Notifier Actions
  function assignNotifiers(unitId: string, notifierIds: string[]) {
    return service.assignNotifiers(unitId, notifierIds);
  }

  function addNotifier(unitId: string, notifierId: string) {
    return service.addNotifier(unitId, notifierId);
  }

  function removeNotifier(unitId: string, notifierId: string) {
    return service.removeNotifier(unitId, notifierId);
  }

  return {
    // STATE
    optimizationUnits,
    // CRUD ACTIONS
    loadOptimizationUnits,
    getOptimizationUnit,
    addOptimizationUnit,
    updateOptimizationUnit,
    deleteOptimizationUnit,
    // ENABLE/DISABLE ACTIONS
    enableOptimizationUnit,
    disableOptimizationUnit,
    // ASSIGNMENT ACTIONS
    assignEnergySource,
    assignPolicy,
    // MINER ACTIONS
    assignMiners,
    addMiner,
    removeMiner,
    // NOTIFIER ACTIONS
    assignNotifiers,
    addNotifier,
    removeNotifier,
  };
});
