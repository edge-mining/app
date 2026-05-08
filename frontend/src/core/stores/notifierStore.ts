import { defineStore } from "pinia";
import { ref } from "vue";
import type { Notifier, ConfigSchema } from "../models/notifier";
import { NotifierService } from "../services/notifierService";

export const useNotifierStore = defineStore("notifier", () => {
  const service = new NotifierService();

  // State
  const notifiers = ref<Notifier[]>([]);
  const adapterTypes = ref<string[]>([]);
  const configSchemas = ref<Map<string, ConfigSchema>>(new Map());

  // Actions
  function loadNotifiers() {
    return service.getNotifiers().then((response) => {
      notifiers.value = response;
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

  function addNotifier(notifier: Notifier) {
    return service.addNotifier(notifier);
  }

  function updateNotifier(notifierId: string, notifier: Partial<Notifier>) {
    return service.updateNotifier(notifierId, notifier);
  }

  function deleteNotifier(notifierId: string) {
    return service.deleteNotifier(notifierId);
  }

  function testNotifier(notifierId: string) {
    return service.testNotifier(notifierId);
  }

  function externalServices(adapterType: string) {
    return service.getExternalServices(adapterType);
  }

  return {
    // STATE
    notifiers,
    adapterTypes,
    configSchemas,
    // ACTIONS
    loadNotifiers,
    loadAdapterTypes,
    loadConfigSchema,
    addNotifier,
    updateNotifier,
    deleteNotifier,
    testNotifier,
    externalServices,
  };
});
