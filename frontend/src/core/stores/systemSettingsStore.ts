import { defineStore } from "pinia";
import { ref } from "vue";
import type { SystemConfiguration } from "../models/systemConfiguration";
import { SystemSettingsService } from "../services/systemSettingsService";

export const useSystemSettingsStore = defineStore("systemSettings", () => {
  const service = new SystemSettingsService();

  // State
  const configuration = ref<SystemConfiguration | null>(null);

  // Actions
  function loadConfiguration() {
    return service.getSystemConfiguration().then((response) => {
      configuration.value = response;
    });
  }

  function updateConfiguration(config: SystemConfiguration) {
    return service.updateSystemConfiguration(config).then((response) => {
      configuration.value = response;
    });
  }

  return {
    // STATE
    configuration,
    // ACTIONS
    loadConfiguration,
    updateConfiguration,
  };
});
