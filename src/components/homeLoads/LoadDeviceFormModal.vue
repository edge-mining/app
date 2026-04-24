<script setup lang="ts">
import { computed, ref, watch, toRaw } from "vue";
import { LoadDeviceCategory, type LoadDevice } from "../../core/models/homeLoadsProfile";
import type { EnergyLoadForecastProvider } from "../../core/models/energyLoadForecastProvider";
import type { EnergyLoadHistoryProvider } from "../../core/models/energyLoadHistoryProvider";
import { formatType } from "../../core/utils/index";
import {
  PhX,
  PhFloppyDisk,
  PhPlug,
  PhGear,
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
  save: [device: LoadDevice];
}>();

const categories = Object.values(LoadDeviceCategory);

const formData = ref<LoadDevice>({
  name: "",
  category: LoadDeviceCategory.OCCASIONAL,
  enabled: true,
  energy_load_forecast_provider_id: "",
  energy_load_history_provider_id: "",
});

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
      } else {
        formData.value = {
          name: "",
          category: LoadDeviceCategory.OCCASIONAL,
          enabled: true,
          energy_load_forecast_provider_id: "",
          energy_load_history_provider_id: "",
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

function handleSave() {
  if (isFormValid.value) {
    const rawData = JSON.parse(JSON.stringify(toRaw(formData.value)));
    // Clean empty provider IDs
    if (!rawData.energy_load_forecast_provider_id) {
      delete rawData.energy_load_forecast_provider_id;
    }
    if (!rawData.energy_load_history_provider_id) {
      delete rawData.energy_load_history_provider_id;
    }
    emit("save", rawData);
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

        <!-- Provider Assignment -->
        <div class="space-y-4">
          <div class="flex items-center gap-2 text-sm font-semibold text-base-content/70 uppercase tracking-wider">
            <PhGear :size="16" />
            Provider Assignment
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label mb-1">
                <span class="label-text font-medium">Forecast Provider</span>
              </label>
              <select
                v-model="formData.energy_load_forecast_provider_id"
                class="select select-bordered w-full"
              >
                <option value="">-- None --</option>
                <option
                  v-for="provider in forecastProviders"
                  :key="provider.id"
                  :value="provider.id"
                >
                  {{ provider.name }} ({{ formatType(provider.adapter_type) }})
                </option>
              </select>
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
