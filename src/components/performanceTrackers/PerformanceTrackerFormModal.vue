<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import {
  type PerformanceTracker,
  MiningPerformanceTrackerAdapter,
} from "../../core/models/performanceTracker";
import { usePerformanceTrackerStore } from "../../core/stores/performanceTrackerStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { PerformanceTrackerService } from "../../core/services/performanceTrackerService";
import PerformanceTrackerConfigForm from "./PerformanceTrackerConfigForm.vue";
import {
  PhX,
  PhFloppyDisk,
  PhGear,
  PhPlugs,
  PhChartLineUp,
} from "@phosphor-icons/vue";
import { formatType } from "../../core/utils/index";

const props = defineProps<{
  open: boolean;
  performanceTracker?: PerformanceTracker;
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [tracker: PerformanceTracker];
}>();

const performanceTrackerStore = usePerformanceTrackerStore();
const externalServiceStore = useExternalServiceStore();
const performanceTrackerService = new PerformanceTrackerService();

const requiredExternalServiceType = ref<string | null>(null);
const isLoadingExternalServiceType = ref(false);

const formData = ref<PerformanceTracker>({
  name: "",
  adapter_type: MiningPerformanceTrackerAdapter.DUMMY,
  config: {},
  external_service_id: "",
});

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.performanceTracker) {
        formData.value = {
          ...props.performanceTracker,
          config: props.performanceTracker.config
            ? { ...props.performanceTracker.config }
            : {},
          external_service_id:
            props.performanceTracker.external_service_id || "",
        };
      } else {
        formData.value = {
          name: "",
          adapter_type:
            performanceTrackerStore.adapterTypes[0] ||
            MiningPerformanceTrackerAdapter.DUMMY,
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

const filteredExternalServices = computed(() => {
  if (!requiredExternalServiceType.value) return [];
  return externalServiceStore.externalServices.filter(
    (svc) =>
      svc.adapter_type?.toLowerCase() ===
      requiredExternalServiceType.value?.toLowerCase()
  );
});

watch(
  () => formData.value.adapter_type,
  async (newType) => {
    if (!newType) {
      requiredExternalServiceType.value = null;
      return;
    }

    isLoadingExternalServiceType.value = true;
    try {
      requiredExternalServiceType.value =
        await performanceTrackerService.getExternalServiceType(newType);
      if (requiredExternalServiceType.value === null) {
        formData.value.external_service_id = "";
      }
    } catch {
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

function cleanTracker(tracker: PerformanceTracker): PerformanceTracker {
  const cleaned = { ...tracker };
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
    emit("save", cleanTracker(rawData));
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
            <PhChartLineUp :size="22" class="text-warning" />
          </div>
          <h3 class="text-xl font-bold">
            {{ isEdit ? "Edit Performance Tracker" : "Add Performance Tracker" }}
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
                placeholder="Enter tracker name"
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
                  v-for="adapterType in performanceTrackerStore.adapterTypes"
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

        <!-- External Service -->
        <div class="space-y-4" :class="{ 'opacity-50': isExternalServiceDisabled }">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhPlugs :size="16" />
            External Service
          </div>

          <div class="form-control">
            <label class="label mb-1 flex justify-between items-center">
              <span class="label-text font-medium">Linked Service</span>
              <span
                v-if="requiredExternalServiceType"
                class="label-text-alt badge badge-sm badge-info"
              >
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
              <span
                v-if="isLoadingExternalServiceType"
                class="label-text-alt text-base-content/50 italic"
                >Loading...</span
              >
              <span
                v-else-if="isExternalServiceDisabled"
                class="label-text-alt text-base-content/50 italic"
                >External service not required for this adapter type</span
              >
              <span
                v-else-if="filteredExternalServices.length === 0"
                class="label-text-alt text-warning italic"
              >
                No
                {{
                  requiredExternalServiceType
                    ? formatType(requiredExternalServiceType)
                    : ""
                }}
                services configured
              </span>
              <span v-else class="label-text-alt text-base-content/50">
                Link to a
                {{
                  requiredExternalServiceType
                    ? formatType(requiredExternalServiceType)
                    : ""
                }}
                service for API connectivity
              </span>
            </label>
          </div>
        </div>

        <!-- Configuration -->
        <div class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhGear :size="16" />
            Configuration
          </div>

          <div class="bg-base-200/50 rounded-xl p-4 border border-base-300/40">
            <PerformanceTrackerConfigForm
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
            {{ isEdit ? "Save Changes" : "Create Tracker" }}
          </button>
        </div>
      </form>
    </div>

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
