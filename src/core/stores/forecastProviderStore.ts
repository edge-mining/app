import { defineStore } from "pinia";
import { ref } from "vue";
import type { ForecastProvider } from "../models/forecastProvider";
import { ForecastProviderService } from "../services/forecastProviderService";

export const useForecastProviderStore = defineStore("forecastProvider", () => {
  const service = new ForecastProviderService();

  // State
  const forecastProviders = ref<ForecastProvider[]>([]);
  const adapterTypes = ref<string[]>([]);

  // Actions
  function loadForecastProviders() {
    return service.getForecastProviders().then((response) => {
      forecastProviders.value = response;
    });
  }

  function loadAdapterTypes() {
    return service.getAdapterTypes().then((response) => {
      adapterTypes.value = response;
    });
  }

  function addForecastProvider(forecastProvider: ForecastProvider) {
    return service.addForecastProvider(forecastProvider);
  }

  function updateForecastProvider(providerId: string, forecastProvider: Partial<ForecastProvider>) {
    return service.updateForecastProvider(providerId, forecastProvider);
  }

  function deleteForecastProvider(providerId: string) {
    return service.deleteForecastProvider(providerId);
  }

  return {
    //STATE
    forecastProviders,
    adapterTypes,
    // ACTIONS
    loadForecastProviders,
    loadAdapterTypes,
    addForecastProvider,
    updateForecastProvider,
    deleteForecastProvider,
  };
});
