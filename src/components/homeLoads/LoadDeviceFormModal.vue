<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import { LoadDeviceCategory, type LoadDevice } from "../../core/models/homeLoadsProfile";
import {
  EnergyLoadForecastProviderAdapter,
  type EnergyLoadForecastProvider,
} from "../../core/models/energyLoadForecastProvider";
import type { EnergyLoadHistoryProvider } from "../../core/models/energyLoadHistoryProvider";
import { useEnergyLoadForecastProviderStore } from "../../core/stores/energyLoadForecastProviderStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import ConfigSchemaForm from "../ConfigSchemaForm.vue";
import { formatType } from "../../core/utils/index";
import {
  PhX,
  PhFloppyDisk,
  PhPlug,
  PhGear,
  PhBrain,
  PhPlugs,
  PhTrash,
} from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
  device?: LoadDevice;
  isEdit?: boolean;
  forecastProviders: EnergyLoadForecastProvider[];
  historyProviders: EnergyLoadHistoryProvider[];
}>();

const emit = defineEmits<{
  close: [];
  save: [device: LoadDevice, forecastProvider?: EnergyLoadForecastProvider | null];
}>();

const forecastProviderStore = useEnergyLoadForecastProviderStore();
const externalServiceStore = useExternalServiceStore();

const categories = Object.values(LoadDeviceCategory);

const formData = ref<LoadDevice>({
  name: "",
  category: LoadDeviceCategory.OCCASIONAL,
  enabled: true,
  energy_load_forecast_provider_id: "",
  energy_load_history_provider_id: "",
});

// Forecast provider inline config
const forecastEnabled = ref(false);
const forecastAdapterType = ref<string>(EnergyLoadForecastProviderAdapter.DUMMY);
const forecastConfig = ref<Record<string, any>>({});
const forecastExternalServiceId = ref("");
const requiresExternalService = ref(false);
const compatibleExternalServices = ref<any[]>([]);

// Resolve the existing forecast provider linked to this device
const existingForecastProvider = computed(() => {
  if (!formData.value.energy_load_forecast_provider_id) return null;
  return props.forecastProviders.find(
    (p) => p.id === formData.value.energy_load_forecast_provider_id
  ) ?? null;
});

async function updateCompatibleExternalServices(adapterType: string) {
  if (!adapterType) {
    requiresExternalService.value = false;
    compatibleExternalServices.value = [];
    return;
  }
  try {
    const resp = await forecastProviderStore.externalServices(adapterType);
    let required = false;
    let compatibleAdapterTypes: string[] = [];
    if (resp === null || resp === undefined) {
      required = false;
    } else if (typeof resp === "string") {
      required = true;
      compatibleAdapterTypes = [resp];
    }
    requiresExternalService.value = required;
    if (compatibleAdapterTypes.length > 0) {
      compatibleExternalServices.value =
        externalServiceStore.externalServices.filter((s: any) =>
          compatibleAdapterTypes.includes(s.adapter_type)
        );
    } else if (required) {
      compatibleExternalServices.value = externalServiceStore.externalServices;
    } else {
      compatibleExternalServices.value = [];
    }
  } catch {
    requiresExternalService.value = false;
    compatibleExternalServices.value = [];
  }
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.device) {
        formData.value = {
          ...props.device,
          energy_load_forecast_provider_id:
            props.device.energy_load_forecast_provider_id || "",
          energy_load_history_provider_id:
            props.device.energy_load_history_provider_id || "",
        };
        // Initialize forecast section from existing provider
        const fp = props.forecastProviders.find(
          (p) => p.id === props.device!.energy_load_forecast_provider_id
        );
        if (fp) {
          forecastEnabled.value = true;
          forecastAdapterType.value = fp.adapter_type;
          forecastConfig.value = fp.config ? { ...fp.config } : {};
          forecastExternalServiceId.value = fp.external_service_id || "";
          updateCompatibleExternalServices(fp.adapter_type);
        } else {
          resetForecastSection();
        }
      } else {
        formData.value = {
          name: "",
          category: LoadDeviceCategory.OCCASIONAL,
          enabled: true,
          energy_load_forecast_provider_id: "",
          energy_load_history_provider_id: "",
        };
        resetForecastSection();
      }
    }
  },
  { immediate: true }
);

function resetForecastSection() {
  forecastEnabled.value = false;
  forecastAdapterType.value =
    forecastProviderStore.adapterTypes[0] || EnergyLoadForecastProviderAdapter.DUMMY;
  forecastConfig.value = {};
  forecastExternalServiceId.value = "";
  requiresExternalService.value = false;
  compatibleExternalServices.value = [];
}

watch(forecastAdapterType, (newType) => {
  if (newType && forecastEnabled.value) {
    forecastConfig.value = {};
    updateCompatibleExternalServices(newType);
  }
});

watch(forecastEnabled, (enabled) => {
  if (enabled) {
    updateCompatibleExternalServices(forecastAdapterType.value);
  }
});

const isFormValid = computed(() => {
  return formData.value.name.trim().length > 0;
});

function handleClose() {
  emit("close");
}

function handleSave() {
  if (!isFormValid.value) return;

  const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));

  // Clean empty provider IDs
  if (!rawData.energy_load_forecast_provider_id) {
    delete rawData.energy_load_forecast_provider_id;
  }
  if (!rawData.energy_load_history_provider_id) {
    delete rawData.energy_load_history_provider_id;
  }

  // Build forecast provider payload
  let forecastPayload: EnergyLoadForecastProvider | null | undefined;

  if (forecastEnabled.value) {
    const adapterChanged = existingForecastProvider.value &&
      existingForecastProvider.value.adapter_type !== forecastAdapterType.value;

    const fpData: EnergyLoadForecastProvider = {
      name: `${formData.value.name} - Forecast`,
      adapter_type: forecastAdapterType.value as EnergyLoadForecastProviderAdapter,
      config: Object.keys(forecastConfig.value).length > 0
        ? { ...forecastConfig.value }
        : undefined,
    };
    if (forecastExternalServiceId.value) {
      fpData.external_service_id = forecastExternalServiceId.value;
    }
    // Keep existing ID only if adapter type hasn't changed (update)
    // If adapter changed, don't set ID so it triggers delete old + create new
    if (existingForecastProvider.value?.id && !adapterChanged) {
      fpData.id = existingForecastProvider.value.id;
    }
    // When creating a new provider, clear stale forecast link from device data
    if (!fpData.id) {
      delete rawData.energy_load_forecast_provider_id;
    }
    forecastPayload = fpData;
  } else if (existingForecastProvider.value) {
    // Forecast was enabled, now disabled → signal deletion
    forecastPayload = null;
  }

  emit("save", rawData, forecastPayload);
}
</script>

<template>
  <dialog class="modal" :class="{ 'modal-open': open }">
    <div class="modal-box max-w-2xl bg-base-100 border border-base-300/60">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-base-200/60 flex items-center justify-center">
            <PhPlug :size="22" class="text-teal-400" />
          </div>
          <h3 class="text-xl font-bold">
            {{ isEdit ? "Edit Load Device" : "Add Load Device" }}
          </h3>
        </div>
        <button class="btn btn-ghost btn-sm btn-square" @click="handleClose">
          <PhX :size="20" />
        </button>
      </div>

      <p class="text-xs text-base-content/50 mb-4">* Required fields</p>

      <form class="space-y-6" @submit.prevent="handleSave">
        <!-- Basic Info -->
        <div class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhGear :size="16" />
            Basic Information
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label mb-1">
                <span class="label-text font-medium">Name *</span>
              </label>
              <input
                v-model="formData.name"
                type="text"
                placeholder="e.g. Dishwasher, Heat Pump"
                class="input input-bordered w-full"
                required
              />
            </div>

            <div class="form-control">
              <label class="label mb-1">
                <span class="label-text font-medium">Category *</span>
              </label>
              <select
                v-model="formData.category"
                class="select select-bordered w-full"
                required
              >
                <option v-for="cat in categories" :key="cat" :value="cat">
                  {{ formatType(cat) }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-control">
            <label class="label cursor-pointer justify-start gap-3">
              <input
                v-model="formData.enabled"
                type="checkbox"
                class="toggle toggle-success"
              />
              <span class="label-text font-medium">Enabled</span>
            </label>
          </div>
        </div>

        <!-- History Provider -->
        <div class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhGear :size="16" />
            History Provider
          </div>
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">History Provider</span>
            </label>
            <select
              v-model="formData.energy_load_history_provider_id"
              class="select select-bordered w-full"
            >
              <option value="">-- None --</option>
              <option
                v-for="provider in historyProviders"
                :key="provider.id"
                :value="provider.id"
              >
                {{ provider.name }} ({{ formatType(provider.adapter_type) }})
              </option>
            </select>
          </div>
        </div>

        <!-- Forecast Provider (inline) -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
              <PhBrain :size="16" />
              Forecast Provider
            </div>
            <label class="label cursor-pointer gap-2 p-0">
              <span class="label-text text-xs text-base-content/50">{{ forecastEnabled ? 'Enabled' : 'Disabled' }}</span>
              <input
                v-model="forecastEnabled"
                type="checkbox"
                class="toggle toggle-sm toggle-primary"
              />
            </label>
          </div>

          <div v-if="forecastEnabled" class="bg-base-200/30 rounded-xl border border-base-300/30 p-4 space-y-4">
            <!-- Adapter Type -->
            <div class="form-control">
              <label class="label mb-1">
                <span class="label-text font-medium">Adapter Type *</span>
              </label>
              <select
                v-model="forecastAdapterType"
                class="select select-bordered w-full"
              >
                <option value="" disabled>Select adapter type</option>
                <option
                  v-for="at in forecastProviderStore.adapterTypes"
                  :key="at"
                  :value="at"
                >
                  {{ formatType(at) }}
                </option>
              </select>
            </div>

            <!-- External Service -->
            <div v-if="requiresExternalService" class="form-control">
              <div class="flex items-center gap-2 mb-1">
                <PhPlugs :size="14" class="text-warning" />
                <span class="label-text font-medium">External Service</span>
                <span class="badge badge-xs badge-warning">Required</span>
              </div>
              <select
                v-model="forecastExternalServiceId"
                class="select select-bordered w-full"
              >
                <option value="">-- Select service --</option>
                <option v-if="compatibleExternalServices.length === 0" disabled>
                  No compatible services available
                </option>
                <option
                  v-for="svc in compatibleExternalServices"
                  :key="svc.id"
                  :value="svc.id"
                >
                  {{ svc.name }}
                </option>
              </select>
            </div>

            <!-- Config Schema -->
            <div>
              <label class="label mb-1">
                <span class="label-text font-medium">Configuration</span>
              </label>
              <div class="bg-base-200/50 rounded-lg p-3 border border-base-300/30">
                <ConfigSchemaForm
                  v-model="forecastConfig"
                  :adapter-type="forecastAdapterType"
                  config-endpoint="energy-load-forecast-providers"
                />
              </div>
            </div>

            <!-- Remove button for existing providers -->
            <div v-if="existingForecastProvider" class="pt-2 border-t border-base-300/30">
              <button
                type="button"
                class="btn btn-ghost btn-sm text-error gap-1.5"
                @click="forecastEnabled = false"
              >
                <PhTrash :size="14" />
                Remove Forecast Provider
              </button>
              <p class="text-xs text-base-content/40 mt-1">
                The forecast provider will be deleted when you save.
              </p>
            </div>
          </div>

          <div v-else class="text-sm text-base-content/40 italic pl-1">
            No forecast provider configured for this device.
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-base-300/40">
          <button type="button" class="btn btn-ghost" @click="handleClose">
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-primary gap-2"
            :disabled="!isFormValid"
          >
            <PhFloppyDisk :size="18" />
            {{ isEdit ? "Save Changes" : "Create Device" }}
          </button>
        </div>
      </form>
    </div>

    <form method="dialog" class="modal-backdrop bg-black/50">
      <button @click="handleClose">close</button>
    </form>
  </dialog>
</template>
