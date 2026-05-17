<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import { type ForecastProvider, ForecastProviderAdapter } from "../../core/models/forecastProvider";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import ForecastProviderConfigForm from "./ForecastProviderConfigForm.vue";
import { formatType } from "../../core/utils/index";
import {
  PhX,
  PhFloppyDisk,
  PhChartLine,
  PhGear,
  PhPlugs,
} from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
  forecastProvider?: ForecastProvider;
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [forecastProvider: ForecastProvider];
}>();

const forecastProviderStore = useForecastProviderStore();
const externalServiceStore = useExternalServiceStore();

// External service UI state
const requiresExternalService = ref(false);
const compatibleExternalServices = ref<any[]>([]);

// Local form state
const formData = ref<ForecastProvider>({
  name: "",
  adapter_type: ForecastProviderAdapter.DUMMY_SOLAR,
  config: {},
  external_service_id: "",
});

// Update compatible external services based on adapter type
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
      compatibleAdapterTypes = [];
    } else if (typeof resp === "string") {
      required = true;
      compatibleAdapterTypes = [resp];
    } else {
      required = false;
      compatibleAdapterTypes = [];
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
  } catch (err) {
    console.error("Failed to get external services info for adapter:", err);
    requiresExternalService.value = false;
    compatibleExternalServices.value = [];
  }
}

// Watch for changes in the prop to reset form
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.forecastProvider) {
        formData.value = {
          ...props.forecastProvider,
          config: props.forecastProvider.config
            ? { ...props.forecastProvider.config }
            : {},
          external_service_id: props.forecastProvider.external_service_id || "",
        };
        if (props.forecastProvider.adapter_type) {
          updateCompatibleExternalServices(props.forecastProvider.adapter_type);
        }
      } else {
        formData.value = {
          name: "",
          adapter_type: forecastProviderStore.adapterTypes[0] || ForecastProviderAdapter.DUMMY_SOLAR,
          config: {},
          external_service_id: "",
        };
        if (formData.value.adapter_type) {
          updateCompatibleExternalServices(formData.value.adapter_type);
        }
      }
    }
  },
  { immediate: true }
);

// Watch for adapter type changes to update external service options
watch(
  () => formData.value.adapter_type,
  (newAdapterType) => {
    if (newAdapterType) {
      updateCompatibleExternalServices(newAdapterType);
    }
  }
);

const isFormValid = computed(() => {
  return (
    formData.value.name.trim().length > 0 &&
    formData.value.adapter_type.trim().length > 0
  );
});

function handleClose() {
  emit("close");
}

function cleanForecastProvider(fp: ForecastProvider): ForecastProvider {
  const cleaned = { ...fp };
  if (cleaned.config && Object.keys(cleaned.config).length === 0) {
    delete cleaned.config;
  }
  if (cleaned.external_service_id === "") {
    delete cleaned.external_service_id;
  }
  return cleaned;
}

function handleSave() {
  if (isFormValid.value) {
    const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));
    const cleanedData = cleanForecastProvider(rawData);
    emit("save", cleanedData);
  }
}
</script>

<template>
  <dialog class="modal" :class="{ 'modal-open': open }">
    <div class="modal-box max-w-2xl bg-base-100 border border-base-300/60">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-base-200/60 flex items-center justify-center">
            <PhChartLine :size="22" class="text-indigo-400" />
          </div>
          <h3 class="text-xl font-bold">
            {{ isEdit ? "Edit Forecast Provider" : "Add Forecast Provider" }}
          </h3>
        </div>
        <button class="btn btn-ghost btn-sm btn-square" @click="handleClose">
          <PhX :size="20" />
        </button>
      </div>

      <!-- Required fields note -->
      <p class="text-xs text-base-content/50 mb-4">* Required fields</p>

      <!-- Form -->
      <form class="space-y-6" @submit.prevent="handleSave">
        <!-- Basic Info Section -->
        <div class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhGear :size="16" />
            Basic Information
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Name Input -->
            <div class="form-control">
              <label class="label mb-1">
                <span class="label-text font-medium">Name *</span>
              </label>
              <input
                v-model="formData.name"
                type="text"
                placeholder="Enter provider name"
                class="input input-bordered w-full"
                required
              />
            </div>

            <!-- Adapter Type Select -->
            <div class="form-control">
              <label class="label mb-1">
                <span class="label-text font-medium">Adapter Type *</span>
              </label>
              <select
                v-model="formData.adapter_type"
                class="select select-bordered w-full"
                :disabled="isEdit"
                required
              >
                <option value="" disabled>Select adapter type</option>
                <option
                  v-for="adapterType in forecastProviderStore.adapterTypes"
                  :key="adapterType"
                  :value="adapterType"
                >
                  {{ formatType(adapterType) }}
                </option>
              </select>
              <label v-if="isEdit" class="label">
                <span class="label-text-alt text-base-content/50 italic">
                  Adapter type cannot be changed after creation
                </span>
              </label>
            </div>
          </div>
        </div>

        <!-- External Service Section (conditional) -->
        <div v-if="requiresExternalService" class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhPlugs :size="16" />
            External Service
            <span class="badge badge-sm badge-warning">Required</span>
          </div>

          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Linked Service *</span>
            </label>
            <select
              v-model="formData.external_service_id"
              class="select select-bordered w-full"
            >
              <option value="">-- Select service --</option>
              <option
                v-if="compatibleExternalServices.length === 0"
                disabled
              >
                No compatible external services available
              </option>
              <option
                v-for="svc in compatibleExternalServices"
                :key="svc.id"
                :value="svc.id"
              >
                {{ svc.name }}
              </option>
            </select>
            <label class="label">
              <span class="label-text-alt text-base-content/50">
                This adapter requires an external service for API connectivity
              </span>
            </label>
          </div>
        </div>

        <!-- Configuration Section -->
        <div class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhGear :size="16" />
            Configuration
          </div>

          <div class="bg-base-200/50 rounded-xl p-4 border border-base-300/40">
            <ForecastProviderConfigForm
              v-if="formData.config"
              v-model="formData.config"
              :adapter-type="formData.adapter_type"
            />
            <div v-else class="text-sm text-base-content/50 italic py-4 text-center">
              Select an adapter type to see configuration options
            </div>
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
            {{ isEdit ? "Save Changes" : "Create Provider" }}
          </button>
        </div>
      </form>
    </div>

    <!-- Backdrop -->
    <form method="dialog" class="modal-backdrop bg-black/50">
      <button @click="handleClose">close</button>
    </form>
  </dialog>
</template>

<style scoped>
.space-y-4:hover .uppercase {
  color: oklch(var(--bc) / 0.8);
}
</style>
