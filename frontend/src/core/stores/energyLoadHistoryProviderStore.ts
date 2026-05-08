import { defineStore } from "pinia";
import { ref } from "vue";
import type {
  EnergyLoadHistoryProvider,
  EnergyLoadHistoryProviderAdapter,
} from "../models/energyLoadHistoryProvider";
import { EnergyLoadHistoryProviderService } from "../services/energyLoadHistoryProviderService";

export const useEnergyLoadHistoryProviderStore = defineStore(
  "energyLoadHistoryProvider",
  () => {
    const service = new EnergyLoadHistoryProviderService();

    // State
    const providers = ref<EnergyLoadHistoryProvider[]>([]);
    const adapterTypes = ref<EnergyLoadHistoryProviderAdapter[]>([]);

    // Actions
    function loadProviders() {
      return service.getProviders().then((response) => {
        providers.value = response;
      });
    }

    function loadAdapterTypes() {
      return service.getAdapterTypes().then((response) => {
        adapterTypes.value = response;
      });
    }

    function addProvider(provider: EnergyLoadHistoryProvider) {
      return service.addProvider(provider);
    }

    function updateProvider(
      providerId: string,
      provider: Partial<EnergyLoadHistoryProvider>
    ) {
      return service.updateProvider(providerId, provider);
    }

    function deleteProvider(providerId: string) {
      return service.deleteProvider(providerId);
    }

    function externalServices(adapterType: string) {
      return service.getExternalServices(adapterType);
    }

    return {
      // STATE
      providers,
      adapterTypes,
      // ACTIONS
      loadProviders,
      loadAdapterTypes,
      addProvider,
      updateProvider,
      deleteProvider,
      externalServices,
    };
  }
);
