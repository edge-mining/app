<script setup lang="ts">
import { ref, watch, computed, toRaw } from "vue";
import { LoadDeviceCategory, type LoadDevice } from "../../core/models/homeLoadsProfile";
import {
  EnergyLoadForecastProviderAdapter,
  type EnergyLoadForecastProvider,
} from "../../core/models/energyLoadForecastProvider";
import {
  EnergyLoadHistoryProviderAdapter,
  type EnergyLoadHistoryProvider,
} from "../../core/models/energyLoadHistoryProvider";
import { useEnergyLoadForecastProviderStore } from "../../core/stores/energyLoadForecastProviderStore";
import { useEnergyLoadHistoryProviderStore } from "../../core/stores/energyLoadHistoryProviderStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import ConfigSchemaForm from "../ConfigSchemaForm.vue";
import ForecastProviderInfo from "./ForecastProviderInfo.vue";
import { formatType } from "../../core/utils/index";
import {
  PhX,
  PhPlug,
  PhBrain,
  PhPlugs,
  PhChartLine,
  PhArrowRight,
  PhArrowLeft,
  PhCheck,
} from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [device: LoadDevice, forecastProvider?: EnergyLoadForecastProvider | null, historyProvider?: EnergyLoadHistoryProvider | null];
}>();

const forecastProviderStore = useEnergyLoadForecastProviderStore();
const historyProviderStore = useEnergyLoadHistoryProviderStore();
const externalServiceStore = useExternalServiceStore();

const categories = Object.values(LoadDeviceCategory);
const currentStep = ref(1);
const totalSteps = 3;

// Step 1: Basic Info
const formData = ref<LoadDevice>({
  name: "",
  category: LoadDeviceCategory.OCCASIONAL,
  enabled: true,
  energy_load_forecast_provider_id: "",
  energy_load_history_provider_id: "",
});

// Step 2: Forecast Provider
const forecastEnabled = ref(false);
const forecastAdapterType = ref<string>(EnergyLoadForecastProviderAdapter.DUMMY);
const forecastConfig = ref<Record<string, any>>({});
const forecastExternalServiceId = ref("");
const requiresExternalService = ref(false);
const compatibleExternalServices = ref<any[]>([]);
const showForecastConfig = ref(false);

// Step 3: History Provider
const historyEnabled = ref(false);
const historyAdapterType = ref<string>(EnergyLoadHistoryProviderAdapter.DUMMY);
const historyConfig = ref<Record<string, any>>({});
const historyExternalServiceId = ref("");
const historyRequiresExternalService = ref(false);
const historyCompatibleExternalServices = ref<any[]>([]);
const showHistoryConfig = ref(false);

// Validation
const isStep1Valid = computed(() => formData.value.name.trim().length > 0);

const stepLabels = ["Device Info", "Forecast", "History"];

// External services logic
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

async function updateHistoryCompatibleExternalServices(adapterType: string) {
  if (!adapterType) {
    historyRequiresExternalService.value = false;
    historyCompatibleExternalServices.value = [];
    return;
  }
  try {
    const resp = await historyProviderStore.externalServices(adapterType);
    let required = false;
    let compatibleAdapterTypes: string[] = [];
    if (resp === null || resp === undefined) {
      required = false;
    } else if (typeof resp === "string") {
      required = true;
      compatibleAdapterTypes = [resp];
    }
    historyRequiresExternalService.value = required;
    if (compatibleAdapterTypes.length > 0) {
      historyCompatibleExternalServices.value =
        externalServiceStore.externalServices.filter((s: any) =>
          compatibleAdapterTypes.includes(s.adapter_type)
        );
    } else if (required) {
      historyCompatibleExternalServices.value = externalServiceStore.externalServices;
    } else {
      historyCompatibleExternalServices.value = [];
    }
  } catch {
    historyRequiresExternalService.value = false;
    historyCompatibleExternalServices.value = [];
  }
}

// Watchers
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

watch(historyAdapterType, (newType) => {
  if (newType && historyEnabled.value) {
    historyConfig.value = {};
    updateHistoryCompatibleExternalServices(newType);
  }
});

watch(historyEnabled, (enabled) => {
  if (enabled) {
    updateHistoryCompatibleExternalServices(historyAdapterType.value);
  }
});

// Reset on open
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      currentStep.value = 1;
      formData.value = {
        name: "",
        category: LoadDeviceCategory.OCCASIONAL,
        enabled: true,
        energy_load_forecast_provider_id: "",
        energy_load_history_provider_id: "",
      };
      forecastEnabled.value = false;
      forecastAdapterType.value =
        forecastProviderStore.adapterTypes[0] || EnergyLoadForecastProviderAdapter.DUMMY;
      forecastConfig.value = {};
      forecastExternalServiceId.value = "";
      requiresExternalService.value = false;
      compatibleExternalServices.value = [];
      showForecastConfig.value = false;

      historyEnabled.value = false;
      historyAdapterType.value =
        historyProviderStore.adapterTypes[0] || EnergyLoadHistoryProviderAdapter.DUMMY;
      historyConfig.value = {};
      historyExternalServiceId.value = "";
      historyRequiresExternalService.value = false;
      historyCompatibleExternalServices.value = [];
      showHistoryConfig.value = false;
    }
  }
);

function nextStep() {
  if (currentStep.value < totalSteps) {
    currentStep.value++;
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--;
  }
}

function canProceed(): boolean {
  if (currentStep.value === 1) return isStep1Valid.value;
  return true;
}

function handleClose() {
  emit("close");
}

function handleSave() {
  if (!isStep1Valid.value) return;

  const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));
  delete rawData.energy_load_forecast_provider_id;
  delete rawData.energy_load_history_provider_id;

  // Build forecast provider payload
  let forecastPayload: EnergyLoadForecastProvider | null | undefined;
  if (forecastEnabled.value) {
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
    forecastPayload = fpData;
  }

  // Build history provider payload
  let historyPayload: EnergyLoadHistoryProvider | null | undefined;
  if (historyEnabled.value) {
    const hpData: EnergyLoadHistoryProvider = {
      name: `${formData.value.name} - History`,
      adapter_type: historyAdapterType.value as EnergyLoadHistoryProviderAdapter,
      config: Object.keys(historyConfig.value).length > 0
        ? { ...historyConfig.value }
        : undefined,
    };
    if (historyExternalServiceId.value) {
      hpData.external_service_id = historyExternalServiceId.value;
    }
    historyPayload = hpData;
  }

  emit("save", rawData, forecastPayload, historyPayload);
}
</script>

<template>
  <dialog class="modal" :class="{ 'modal-open': open }">
    <div class="modal-box max-w-2xl bg-base-100 border border-base-300/60">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-base-200/60 flex items-center justify-center">
            <PhPlug :size="22" class="text-teal-400" />
          </div>
          <div>
            <h3 class="text-xl font-bold">Add Load Device</h3>
            <p class="text-xs text-base-content/50">Step {{ currentStep }} of {{ totalSteps }}</p>
          </div>
        </div>
        <button type="button" class="btn btn-ghost btn-sm btn-square" @click="handleClose">
          <PhX :size="20" />
        </button>
      </div>

      <!-- Stepper -->
      <ul class="steps steps-horizontal w-full mb-6">
        <li
          v-for="(label, idx) in stepLabels"
          :key="idx"
          class="step"
          :class="{ 'step-primary': idx + 1 <= currentStep }"
        >
          {{ label }}
        </li>
      </ul>

      <!-- Step 1: Basic Info -->
      <div v-if="currentStep === 1" class="space-y-4">
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
            />
          </div>

          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Category *</span>
            </label>
            <select
              v-model="formData.category"
              class="select select-bordered w-full"
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

      <!-- Step 2: Forecast Provider -->
      <div v-if="currentStep === 2" class="space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhBrain :size="16" />
            Forecast Provider
          </div>
          <label class="label cursor-pointer gap-2 p-0">
            <span class="label-text text-xs text-base-content/50">{{ forecastEnabled ? 'Enabled' : 'Skip' }}</span>
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
            <div class="flex items-center gap-2">
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
              <ForecastProviderInfo :adapter-type="forecastAdapterType" />
            </div>
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
            <button
              type="button"
              class="btn btn-ghost btn-xs gap-1 mb-1"
              @click="showForecastConfig = !showForecastConfig"
            >
              <span class="text-xs">{{ showForecastConfig ? '▼' : '▶' }}</span>
              <span class="label-text font-medium">Configuration</span>
            </button>
            <div v-if="showForecastConfig" class="bg-base-200/50 rounded-lg p-3 border border-base-300/30">
              <ConfigSchemaForm
                v-model="forecastConfig"
                :adapter-type="forecastAdapterType"
                config-endpoint="energy-load-forecast-providers"
              />
            </div>
          </div>
        </div>

        <div v-else class="text-sm text-base-content/40 italic">
          You can skip this step and configure it later.
        </div>
      </div>

      <!-- Step 3: History Provider -->
      <div v-if="currentStep === 3" class="space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhChartLine :size="16" />
            History Provider
          </div>
          <label class="label cursor-pointer gap-2 p-0">
            <span class="label-text text-xs text-base-content/50">{{ historyEnabled ? 'Enabled' : 'Skip' }}</span>
            <input
              v-model="historyEnabled"
              type="checkbox"
              class="toggle toggle-sm toggle-primary"
            />
          </label>
        </div>

        <div v-if="historyEnabled" class="bg-base-200/30 rounded-xl border border-base-300/30 p-4 space-y-4">
          <!-- Adapter Type -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Adapter Type *</span>
            </label>
            <select
              v-model="historyAdapterType"
              class="select select-bordered w-full"
            >
              <option value="" disabled>Select adapter type</option>
              <option
                v-for="at in historyProviderStore.adapterTypes"
                :key="at"
                :value="at"
              >
                {{ formatType(at) }}
              </option>
            </select>
          </div>

          <!-- External Service -->
          <div v-if="historyRequiresExternalService" class="form-control">
            <div class="flex items-center gap-2 mb-1">
              <PhPlugs :size="14" class="text-warning" />
              <span class="label-text font-medium">External Service</span>
              <span class="badge badge-xs badge-warning">Required</span>
            </div>
            <select
              v-model="historyExternalServiceId"
              class="select select-bordered w-full"
            >
              <option value="">-- Select service --</option>
              <option v-if="historyCompatibleExternalServices.length === 0" disabled>
                No compatible services available
              </option>
              <option
                v-for="svc in historyCompatibleExternalServices"
                :key="svc.id"
                :value="svc.id"
              >
                {{ svc.name }}
              </option>
            </select>
          </div>

          <!-- Config Schema -->
          <div>
            <button
              type="button"
              class="btn btn-ghost btn-xs gap-1 mb-1"
              @click="showHistoryConfig = !showHistoryConfig"
            >
              <span class="text-xs">{{ showHistoryConfig ? '▼' : '▶' }}</span>
              <span class="label-text font-medium">Configuration</span>
            </button>
            <div v-if="showHistoryConfig" class="bg-base-200/50 rounded-lg p-3 border border-base-300/30">
              <ConfigSchemaForm
                v-model="historyConfig"
                :adapter-type="historyAdapterType"
                config-endpoint="energy-load-history-providers"
                :sensor-prefix="historyAdapterType === 'home_assistant_api'"
              />
            </div>
          </div>
        </div>

        <div v-else class="text-sm text-base-content/40 italic">
          You can skip this step and configure it later.
        </div>
      </div>

      <!-- Navigation -->
      <div class="flex justify-between pt-6 border-t border-base-300/40 mt-6">
        <button
          v-if="currentStep > 1"
          type="button"
          class="btn btn-ghost gap-2"
          @click="prevStep"
        >
          <PhArrowLeft :size="16" />
          Back
        </button>
        <div v-else></div>

        <div class="flex gap-2">
          <button type="button" class="btn btn-ghost" @click="handleClose">
            Cancel
          </button>
          <button
            v-if="currentStep < totalSteps"
            type="button"
            class="btn btn-primary gap-2"
            :disabled="!canProceed()"
            @click="nextStep"
          >
            Next
            <PhArrowRight :size="16" />
          </button>
          <button
            v-else
            type="button"
            class="btn btn-primary gap-2"
            :disabled="!isStep1Valid"
            @click="handleSave"
          >
            <PhCheck :size="18" />
            Create Device
          </button>
        </div>
      </div>
    </div>

    <form method="dialog" class="modal-backdrop bg-black/50">
      <button @click="handleClose">close</button>
    </form>
  </dialog>
</template>
