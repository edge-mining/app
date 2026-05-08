import { defineStore } from "pinia";
import { ref } from "vue";
import type { ForecastProvider, ForecastProviderAdapter } from "../models/forecastProvider";
import { ForecastProviderService } from "../services/forecastProviderService";

export const useForecastProviderStore = defineStore("forecastProvider", () => {
  const service = new ForecastProviderService();

  // State
  const forecastProviders = ref<ForecastProvider[]>([]);
  const adapterTypes = ref<ForecastProviderAdapter[]>([]);

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

  function externalServices(adapterType: string) {
    return service.getExternalServices(adapterType);
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
    externalServices
  };
});
