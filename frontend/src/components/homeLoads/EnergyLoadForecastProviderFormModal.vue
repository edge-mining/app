<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import {
  EnergyLoadForecastProviderAdapter,
  type EnergyLoadForecastProvider,
} from "../../core/models/energyLoadForecastProvider";
import { useEnergyLoadForecastProviderStore } from "../../core/stores/energyLoadForecastProviderStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import ConfigSchemaForm from "../ConfigSchemaForm.vue";
import { formatType } from "../../core/utils/index";
import {
  PhX,
  PhFloppyDisk,
  PhBrain,
  PhGear,
  PhPlugs,
} from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
  provider?: EnergyLoadForecastProvider;
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [provider: EnergyLoadForecastProvider];
}>();

const forecastProviderStore = useEnergyLoadForecastProviderStore();
const externalServiceStore = useExternalServiceStore();

const requiresExternalService = ref(false);
const compatibleExternalServices = ref<any[]>([]);

const formData = ref<EnergyLoadForecastProvider>({
  name: "",
  adapter_type: EnergyLoadForecastProviderAdapter.DUMMY,
  config: {},
  external_service_id: "",
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
      if (props.provider) {
        formData.value = {
          ...props.provider,
          config: props.provider.config ? { ...props.provider.config } : {},
          external_service_id: props.provider.external_service_id || "",
        };
        if (props.provider.adapter_type) {
          updateCompatibleExternalServices(props.provider.adapter_type);
        }
      } else {
        formData.value = {
          name: "",
          adapter_type: forecastProviderStore.adapterTypes[0] || EnergyLoadForecastProviderAdapter.DUMMY,
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

watch(
  () => formData.value.adapter_type,
  (newType) => {
    if (newType) updateCompatibleExternalServices(newType);
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

function handleSave() {
  if (isFormValid.value) {
    const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));
    if (rawData.config && Object.keys(rawData.config).length === 0) {
      delete rawData.config;
    }
    if (rawData.external_service_id === "") {
      delete rawData.external_service_id;
    }
    emit("save", rawData);
  }
}
</script>

<template>
  <dialog class="modal" :class="{ 'modal-open': open }">
    <div class="modal-box max-w-3xl bg-base-100 border border-base-300/60">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-base-200/60 flex items-center justify-center">
            <PhBrain :size="22" class="text-purple-400" />
          </div>
          <h3 class="text-xl font-bold">
            {{ isEdit ? "Edit Forecast Provider" : "Add Forecast Provider" }}
          </h3>
        </div>
        <button class="btn btn-ghost btn-sm btn-square" @click="handleClose">
          <PhX :size="20" />
        </button>
      </div>

      <p class="text-xs text-base-content/50 mb-4">* Required fields</p>

      <form class="space-y-6" @submit.prevent="handleSave">
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
                placeholder="Enter provider name"
                class="input input-bordered w-full"
                required
              />
            </div>
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
              <option v-if="compatibleExternalServices.length === 0" disabled>
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
          </div>
        </div>

        <div class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhGear :size="16" />
            Configuration
          </div>
          <div class="bg-base-200/50 rounded-xl p-4 border border-base-300/40">
            <ConfigSchemaForm
              v-if="formData.config"
              v-model="formData.config"
              :adapter-type="formData.adapter_type"
              config-endpoint="energy-load-forecast-providers"
            />
            <div v-else class="text-sm text-base-content/50 italic py-4 text-center">
              Select an adapter type to see configuration options
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-3 pt-4 border-t border-base-300/40">
          <button type="button" class="btn btn-ghost" @click="handleClose">Cancel</button>
          <button type="submit" class="btn btn-primary gap-2" :disabled="!isFormValid">
            <PhFloppyDisk :size="18" />
            {{ isEdit ? "Save Changes" : "Create Provider" }}
          </button>
        </div>
      </form>
    </div>

    <form method="dialog" class="modal-backdrop bg-black/50">
      <button @click="handleClose">close</button>
    </form>
  </dialog>
</template>
