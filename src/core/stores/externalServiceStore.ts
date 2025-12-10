import { defineStore } from "pinia";
import { ref } from "vue";
import type { ExternalService, ConfigSchema } from "../models/externalService";
import { ExternalServiceService } from "../services/externalServiceService";

export const useExternalServiceStore = defineStore("externalService", () => {
  const service = new ExternalServiceService();

  // State
  const externalServices = ref<ExternalService[]>([]);
  const adapterTypes = ref<string[]>([]);
  const configSchemas = ref<Map<string, ConfigSchema>>(new Map());

  // Actions
  function loadExternalServices() {
    return service.getExternalServices().then((response) => {
      externalServices.value = response;
    });
  }

  function loadAdapterTypes() {
    return service.getAdapterTypes().then((response) => {
      adapterTypes.value = response;
    });
  }

  function loadConfigSchema(adapterType: string) {
    return service.getConfigSchema(adapterType).then((response) => {
      configSchemas.value.set(adapterType, response);
      return response;
    });
  }

  function addExternalService(externalService: ExternalService) {
    return service.addExternalService(externalService);
  }

  function updateExternalService(serviceId: string, externalService: Partial<ExternalService>) {
    return service.updateExternalService(serviceId, externalService);
  }

  function deleteExternalService(serviceId: string) {
    return service.deleteExternalService(serviceId);
  }

  return {
    // STATE
    externalServices,
    adapterTypes,
    configSchemas,
    // ACTIONS
    loadExternalServices,
    loadAdapterTypes,
    loadConfigSchema,
    addExternalService,
    updateExternalService,
    deleteExternalService,
  };
});
