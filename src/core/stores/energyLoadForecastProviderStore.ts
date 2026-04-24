import { defineStore } from "pinia";
import { ref } from "vue";
import type {
  EnergyLoadForecastProvider,
  EnergyLoadForecastProviderAdapter,
} from "../models/energyLoadForecastProvider";
import { EnergyLoadForecastProviderService } from "../services/energyLoadForecastProviderService";

export const useEnergyLoadForecastProviderStore = defineStore(
  "energyLoadForecastProvider",
  () => {
    const service = new EnergyLoadForecastProviderService();

    // State
    const providers = ref<EnergyLoadForecastProvider[]>([]);
    const adapterTypes = ref<EnergyLoadForecastProviderAdapter[]>([]);

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

    function addProvider(provider: EnergyLoadForecastProvider) {
      return service.addProvider(provider);
    }

    function updateProvider(
      providerId: string,
      provider: Partial<EnergyLoadForecastProvider>
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
