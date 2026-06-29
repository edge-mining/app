<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import { type MinerController, MinerControllerAdapter } from "../../core/models/minerController";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { MinerControllerService } from "../../core/services/minerControllerService";
import MinerControllerConfigForm from "./MinerControllerConfigForm.vue";
import {
  PhX,
  PhFloppyDisk,
  PhGear,
  PhPlugs,
  PhCircuitry,
  PhPlugsConnected,
  PhCheckCircle,
  PhWarningCircle,
} from "@phosphor-icons/vue";
import { formatType } from "../../core/utils/index";

const props = defineProps<{
  open: boolean;
  minerController?: MinerController;
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [minerController: MinerController];
}>();

const minerControllerStore = useMinerControllerStore();
const externalServiceStore = useExternalServiceStore();
const minerControllerService = new MinerControllerService();

// External service type for current adapter (null means not required)
const requiredExternalServiceType = ref<string | null>(null);
const isLoadingExternalServiceType = ref(false);

// Connection test state
const isTestingConnection = ref(false);
const testResult = ref<{ success: boolean; message: string } | null>(null);

// The connection test is only available for the PyASIC controller
const canTestConnection = computed(
  () => formData.value.adapter_type === MinerControllerAdapter.PYASIC
);

// Local form state
const formData = ref<MinerController>({
  name: "",
  adapter_type: MinerControllerAdapter.DUMMY,
  config: {},
  external_service_id: "",
});

// Watch for changes in the prop to reset form
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      testResult.value = null;
      if (props.minerController) {
        formData.value = {
          ...props.minerController,
          config: props.minerController.config
            ? { ...props.minerController.config }
            : {},
          external_service_id: props.minerController.external_service_id || "",
        };
      } else {
        formData.value = {
          name: "",
          adapter_type: minerControllerStore.adapterTypes[0] || MinerControllerAdapter.DUMMY,
          config: {},
          external_service_id: "",
        };
      }
    }
  },
  { immediate: true }
);

const isFormValid = computed(() => {
  return (
    formData.value.name.trim().length > 0 &&
    formData.value.adapter_type.trim().length > 0
  );
});

const isExternalServiceDisabled = computed(() => {
  return requiredExternalServiceType.value === null;
});

// Filter external services by required type
const filteredExternalServices = computed(() => {
  if (!requiredExternalServiceType.value) return [];
  return externalServiceStore.externalServices.filter(
    (svc) => svc.adapter_type?.toLowerCase() === requiredExternalServiceType.value?.toLowerCase()
  );
});

// Fetch external service type when adapter type changes
watch(
  () => formData.value.adapter_type,
  async (newType) => {
    // Reset any previous connection test result when the adapter changes
    testResult.value = null;

    if (!newType) {
      requiredExternalServiceType.value = null;
      return;
    }

    isLoadingExternalServiceType.value = true;
    try {
      requiredExternalServiceType.value = await minerControllerService.getExternalServiceType(newType);
      // Clear external_service_id if the type doesn't need it
      if (requiredExternalServiceType.value === null) {
        formData.value.external_service_id = "";
      }
    } catch {
      // On error, assume no external service required
      requiredExternalServiceType.value = null;
      formData.value.external_service_id = "";
    } finally {
      isLoadingExternalServiceType.value = false;
    }
  },
  { immediate: true }
);

function handleClose() {
  emit("close");
}

function cleanMinerController(minerController: MinerController): MinerController {
  const cleaned = { ...minerController };
  // Remove empty config object if no properties
  if (cleaned.config && Object.keys(cleaned.config).length === 0) {
    delete cleaned.config;
  }
  // Remove empty string values for external_service_id
  if (cleaned.external_service_id === "") {
    delete cleaned.external_service_id;
  }
  return cleaned;
}

async function handleTestConnection() {
  if (!isFormValid.value || isTestingConnection.value) return;

  isTestingConnection.value = true;
  testResult.value = null;
  try {
    // Deep clone to remove Vue reactive proxies
    const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));
    const cleanedData = cleanMinerController(rawData);
    const result = await minerControllerService.testConnection(cleanedData);
    testResult.value = { success: result.success, message: result.message };
  } catch (error) {
    testResult.value = {
      success: false,
      message: error instanceof Error ? error.message : "Connection test failed",
    };
  } finally {
    isTestingConnection.value = false;
  }
}

function handleSave() {
  if (isFormValid.value) {
    // Deep clone to remove Vue reactive proxies
    const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));
    const cleanedData = cleanMinerController(rawData);
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
            <PhCircuitry :size="22" class="text-info" />
          </div>
          <h3 class="text-xl font-bold">
            {{ isEdit ? "Edit Controller" : "Add Controller" }}
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
                placeholder="Enter controller name"
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
                  v-for="adapterType in minerControllerStore.adapterTypes"
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

        <!-- External Service Section -->
        <div class="space-y-4" :class="{ 'opacity-50': isExternalServiceDisabled }">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhPlugs :size="16" />
            External Service
          </div>

          <div class="form-control">
            <label class="label mb-1 flex justify-between items-center">
              <span class="label-text font-medium">Linked Service</span>
              <span v-if="requiredExternalServiceType" class="label-text-alt badge badge-sm badge-info">
                {{ requiredExternalServiceType }}
              </span>
            </label>
            <select
              v-model="formData.external_service_id"
              class="select select-bordered w-full"
              :disabled="isExternalServiceDisabled || isLoadingExternalServiceType"
            >
              <option value="">-- None --</option>
              <option
                v-for="svc in filteredExternalServices"
                :key="svc.id"
                :value="svc.id"
              >
                {{ svc.name }}
              </option>
            </select>
            <label class="label">
              <span v-if="isLoadingExternalServiceType" class="label-text-alt text-base-content/50 italic">
                Loading...
              </span>
              <span v-else-if="isExternalServiceDisabled" class="label-text-alt text-base-content/50 italic">
                External service not required for this adapter type
              </span>
              <span v-else-if="filteredExternalServices.length === 0" class="label-text-alt text-warning italic">
                No {{ requiredExternalServiceType ? formatType(requiredExternalServiceType) : '' }} services configured
              </span>
              <span v-else class="label-text-alt text-base-content/50">
                Link to a {{ requiredExternalServiceType ? formatType(requiredExternalServiceType) : '' }} service for API connectivity
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
            <MinerControllerConfigForm
              v-if="formData.config"
              v-model="formData.config"
              :adapter-type="formData.adapter_type"
            />
            <div v-else class="text-sm text-base-content/50 italic py-4 text-center">
              Select an adapter type to see configuration options
            </div>
          </div>
        </div>

        <!-- Connection test result -->
        <div
          v-if="canTestConnection && testResult"
          class="alert"
          :class="testResult.success ? 'alert-success' : 'alert-error'"
        >
          <PhCheckCircle v-if="testResult.success" :size="20" />
          <PhWarningCircle v-else :size="20" />
          <span class="text-sm">{{ testResult.message }}</span>
        </div>

        <!-- Actions -->
        <div class="flex justify-between items-center gap-3 pt-4 border-t border-base-300/40">
          <!-- Test connection (PyASIC only) -->
          <button
            v-if="canTestConnection"
            type="button"
            class="btn btn-outline gap-2"
            :disabled="!isFormValid || isTestingConnection"
            @click="handleTestConnection"
          >
            <span v-if="isTestingConnection" class="loading loading-spinner loading-sm"></span>
            <PhPlugsConnected v-else :size="18" />
            {{ isTestingConnection ? "Testing..." : "Test Connection" }}
          </button>
          <div v-else></div>

          <div class="flex gap-3">
            <button type="button" class="btn btn-ghost" @click="handleClose">
              Cancel
            </button>
            <button
              type="submit"
              class="btn btn-primary gap-2"
              :disabled="!isFormValid"
            >
              <PhFloppyDisk :size="18" />
              {{ isEdit ? "Save Changes" : "Create Controller" }}
            </button>
          </div>
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
/* Subtle hover effect for form sections */
.space-y-4:hover .uppercase {
  color: oklch(var(--bc) / 0.8);
}
</style>
