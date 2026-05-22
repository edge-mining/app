<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import type { ClimateZone } from "../../core/models/climateZone";
import type { ClimateMonitor } from "../../core/models/climateMonitor";
import { useClimateMonitorStore } from "../../core/stores/climateMonitorStore";
import {
  PhX,
  PhFloppyDisk,
  PhThermometerSimple,
  PhGear,
  PhLink,
} from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
  climateZone?: ClimateZone;
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [zone: ClimateZone];
}>();

const climateMonitorStore = useClimateMonitorStore();

// Local form state
const formData = ref<ClimateZone>({
  name: "",
  area_sqm: undefined,
  climate_monitor_id: "",
});

// Watch for changes in the prop to reset form
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.climateZone) {
        formData.value = {
          ...props.climateZone,
          climate_monitor_id: props.climateZone.climate_monitor_id || "",
        };
      } else {
        formData.value = {
          name: "",
          area_sqm: undefined,
          climate_monitor_id: "",
        };
      }
    }
  },
  { immediate: true }
);

const isFormValid = computed(() => {
  return formData.value.name.trim().length > 0;
});

function handleClose() {
  emit("close");
}

function cleanZone(zone: ClimateZone): ClimateZone {
  const cleaned = { ...zone };
  if (!cleaned.area_sqm) {
    delete cleaned.area_sqm;
  }
  if (cleaned.climate_monitor_id === "") {
    delete cleaned.climate_monitor_id;
  }
  return cleaned;
}

function handleSave() {
  if (isFormValid.value) {
    const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));
    const cleanedData = cleanZone(rawData);
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
            <PhThermometerSimple :size="22" class="text-orange-400" />
          </div>
          <h3 class="text-xl font-bold">
            {{ isEdit ? "Edit Climate Zone" : "Add Climate Zone" }}
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
                placeholder="e.g. Living Room"
                class="input input-bordered w-full"
                required
              />
            </div>

            <!-- Area -->
            <div class="form-control">
              <label class="label mb-1">
                <span class="label-text font-medium">Area (m²)</span>
              </label>
              <input
                v-model.number="formData.area_sqm"
                type="number"
                step="0.1"
                min="0"
                placeholder="e.g. 25"
                class="input input-bordered w-full"
              />
            </div>
          </div>
        </div>

        <!-- Monitor Link Section -->
        <div class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhLink :size="16" />
            Climate Monitor
          </div>

          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text font-medium">Linked Monitor</span>
            </label>
            <select
              v-model="formData.climate_monitor_id"
              class="select select-bordered w-full"
            >
              <option value="">-- None --</option>
              <option
                v-for="monitor in climateMonitorStore.climateMonitors"
                :key="monitor.id"
                :value="monitor.id"
              >
                {{ monitor.name }}
              </option>
            </select>
            <label class="label">
              <span class="label-text-alt text-base-content/50">
                Link a climate monitor to get temperature readings for this zone
              </span>
            </label>
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
            {{ isEdit ? "Save Changes" : "Create Zone" }}
          </button>
        </div>
      </form>
    </div>

    <!-- Backdrop -->
    <form method="dialog" class="modal-backdrop" @click="handleClose">
      <button>close</button>
    </form>
  </dialog>
</template>
