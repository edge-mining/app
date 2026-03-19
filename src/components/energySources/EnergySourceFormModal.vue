<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { EnergySource } from "../../core/models/energySource";
import { EnergySourceType } from "../../core/models/energySource";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import {
  PhSun,
  PhWind,
  PhPlug,
  PhDrop,
  PhLightning,
  PhX,
  PhFloppyDisk,
  PhBatteryFull,
  PhActivity,
  PhChartLine,
} from "@phosphor-icons/vue";

const props = defineProps<{
  open: boolean;
  energySource?: EnergySource;
  allEnergySources?: EnergySource[];
  isEdit?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [energySource: EnergySource];
}>();

const energyMonitorStore = useEnergyMonitorStore();
const forecastProviderStore = useForecastProviderStore();

// Local form state
const formData = ref<EnergySource>({
  name: "",
  type: EnergySourceType.SOLAR,
});

// Watch for changes in the prop to reset form
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.energySource) {
        formData.value = { ...props.energySource };
      } else {
        formData.value = {
          name: "",
          type: EnergySourceType.SOLAR,
        };
      }
    }
  },
  { immediate: true }
);

// Type options with icons
const typeOptions = [
  { value: EnergySourceType.SOLAR, label: "Solar", icon: PhSun, color: "text-amber-400" },
  { value: EnergySourceType.WIND, label: "Wind", icon: PhWind, color: "text-sky-400" },
  { value: EnergySourceType.GRID, label: "Grid", icon: PhPlug, color: "text-slate-300" },
  { value: EnergySourceType.HYDROELECTRIC, label: "Hydro", icon: PhDrop, color: "text-blue-400" },
  { value: EnergySourceType.OTHER, label: "Other", icon: PhLightning, color: "text-purple-400" },
];

// Compute the monitor IDs already assigned to other energy sources
const assignedEnergyMonitorIds = computed(() => {
  if (!props.allEnergySources) return new Set<string>();
  return new Set(
    props.allEnergySources
      .filter((es) => es.id !== formData.value.id && es.energy_monitor_id)
      .map((es) => String(es.energy_monitor_id))
  );
});

// Compute the forecast provider IDs already assigned to other energy sources
const assignedForecastProviderIds = computed(() => {
  if (!props.allEnergySources) return new Set<string>();
  return new Set(
    props.allEnergySources
      .filter((es) => es.id !== formData.value.id && es.forecast_provider_id)
      .map((es) => String(es.forecast_provider_id))
  );
});

// Filter available energy monitors
const availableEnergyMonitors = computed(() => {
  return energyMonitorStore.energyMonitors.filter(
    (monitor) =>
      !assignedEnergyMonitorIds.value.has(String(monitor.id)) ||
      String(monitor.id) === String(formData.value.energy_monitor_id)
  );
});

// Filter available forecast providers
const availableForecastProviders = computed(() => {
  return forecastProviderStore.forecastProviders.filter(
    (provider) =>
      !assignedForecastProviderIds.value.has(String(provider.id)) ||
      String(provider.id) === String(formData.value.forecast_provider_id)
  );
});

const selectedTypeIndex = computed(() => {
  return typeOptions.findIndex((o) => o.value === formData.value.type);
});

const isFormValid = computed(() => {
  return formData.value.name.trim().length > 0;
});

function handleClose() {
  emit("close");
}

function handleSave() {
  if (isFormValid.value) {
    emit("save", { ...formData.value });
  }
}

function selectType(type: EnergySourceType) {
  formData.value.type = type;
}

function handleStorageCapacityInput(e: Event) {
  const value = (e.target as HTMLInputElement).value;
  if (value === "" || value === null) {
    if (formData.value.storage) {
      delete formData.value.storage;
    }
  } else {
    if (!formData.value.storage) {
      formData.value.storage = { nominal_capacity: 0 };
    }
    formData.value.storage.nominal_capacity = Number(value);
  }
}

function handleGridPowerInput(e: Event) {
  const value = (e.target as HTMLInputElement).value;
  if (value === "" || value === null) {
    if (formData.value.grid) {
      delete formData.value.grid;
    }
  } else {
    if (!formData.value.grid) {
      formData.value.grid = { contracted_power: 0 };
    }
    formData.value.grid.contracted_power = Number(value);
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
            <PhLightning :size="22" class="text-warning" />
          </div>
          <h3 class="text-xl font-bold">
            {{ isEdit ? "Edit Energy Source" : "Add Energy Source" }}
          </h3>
        </div>
        <button class="btn btn-ghost btn-sm btn-square" @click="handleClose">
          <PhX :size="20" />
        </button>
      </div>

      <!-- Form -->
      <div class="space-y-6">
        <!-- Name Input -->
        <div class="form-control">
          <label class="label mb-1">
            <span class="label-text font-medium">Name</span>
          </label>
          <input
            v-model="formData.name"
            type="text"
            placeholder="Enter energy source name"
            class="input input-bordered w-full"
            required
          />
        </div>

        <!-- Type Selection -->
        <div class="form-control">
          <label class="label mb-1">
            <span class="label-text font-medium">Type</span>
          </label>
          <div class="type-selector relative grid grid-cols-5 gap-2">
            <!-- Sliding highlight -->
            <div
              class="type-slider absolute rounded-xl border-2 border-primary bg-primary/10 pointer-events-none"
              :style="{
                width: `calc((100% - 0.5rem * 4) / 5)`,
                height: '100%',
                left: `calc(${selectedTypeIndex} * (100% - 0.5rem * 4) / 5 + ${selectedTypeIndex} * 0.5rem)`,
              }"
            ></div>
            <button
              v-for="option in typeOptions"
              :key="option.value"
              type="button"
              class="relative z-10 flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-colors duration-300"
              :class="[
                formData.type === option.value
                  ? 'border-transparent'
                  : 'border-base-300/50 hover:border-base-300 bg-base-200/30',
              ]"
              @click="selectType(option.value)"
            >
              <component
                :is="option.icon"
                :size="28"
                weight="duotone"
                :class="formData.type === option.value ? option.color : 'text-base-content/50'"
                class="transition-colors duration-300"
              />
              <span
                class="text-xs font-medium transition-colors duration-300"
                :class="
                  formData.type === option.value
                    ? 'text-primary'
                    : 'text-base-content/70'
                "
              >
                {{ option.label }}
              </span>
            </button>
          </div>
        </div>

        <!-- Power Settings -->
        <div class="divider text-xs text-base-content/50 my-4">POWER CONFIGURATION</div>

        <div class="grid grid-cols-2 gap-4">
          <!-- Nominal Power Max -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhLightning :size="16" class="text-warning" />
                Max Power
              </span>
            </label>
            <label class="input input-bordered flex items-center gap-2">
              <input
                v-model.number="formData.nominal_power_max"
                type="number"
                class="grow"
                placeholder="0"
              />
              <span class="text-sm text-base-content/50">W</span>
            </label>
          </div>

          <!-- External Source -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhLightning :size="16" class="text-secondary" />
                External Source
              </span>
            </label>
            <label class="input input-bordered flex items-center gap-2">
              <input
                v-model.number="formData.external_source"
                type="number"
                class="grow"
                placeholder="0"
              />
              <span class="text-sm text-base-content/50">W</span>
            </label>
          </div>

          <!-- Storage Capacity -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhBatteryFull :size="16" class="text-success" />
                Storage Capacity
              </span>
            </label>
            <label class="input input-bordered flex items-center gap-2">
              <input
                :value="formData.storage?.nominal_capacity ?? ''"
                type="number"
                class="grow"
                placeholder="0"
                @input="handleStorageCapacityInput"
              />
              <span class="text-sm text-base-content/50">Wh</span>
            </label>
          </div>

          <!-- Grid Contracted Power -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhPlug :size="16" class="text-info" />
                Grid Contracted Power
              </span>
            </label>
            <label class="input input-bordered flex items-center gap-2">
              <input
                :value="formData.grid?.contracted_power ?? ''"
                type="number"
                class="grow"
                placeholder="0"
                @input="handleGridPowerInput"
              />
              <span class="text-sm text-base-content/50">W</span>
            </label>
          </div>
        </div>

        <!-- Connections -->
        <div class="divider text-xs text-base-content/50 my-4">INTEGRATIONS</div>

        <div class="grid grid-cols-2 gap-4">
          <!-- Energy Monitor -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhActivity :size="16" class="text-success" />
                Energy Monitor
              </span>
            </label>
            <select
              v-model="formData.energy_monitor_id"
              class="select select-bordered w-full"
            >
              <option :value="undefined">None</option>
              <option
                v-for="monitor in availableEnergyMonitors"
                :key="monitor.id"
                :value="monitor.id"
              >
                {{ monitor.name }}
              </option>
            </select>
          </div>

          <!-- Forecast Provider -->
          <div class="form-control">
            <label class="label mb-1">
              <span class="label-text flex items-center gap-2">
                <PhChartLine :size="16" class="text-info" />
                Forecast Provider
              </span>
            </label>
            <select
              v-model="formData.forecast_provider_id"
              class="select select-bordered w-full"
            >
              <option :value="undefined">None</option>
              <option
                v-for="provider in availableForecastProviders"
                :key="provider.id"
                :value="provider.id"
              >
                {{ provider.name }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="modal-action mt-8">
        <button class="btn btn-ghost" @click="handleClose">Cancel</button>
        <button
          class="btn btn-primary"
          :disabled="!isFormValid"
          @click="handleSave"
        >
          <PhFloppyDisk :size="18" />
          {{ isEdit ? "Save Changes" : "Create" }}
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop bg-black/60" @click="handleClose">
      <button>close</button>
    </form>
  </dialog>
</template>

<style scoped>
.type-slider {
  transition: left 0.30s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
