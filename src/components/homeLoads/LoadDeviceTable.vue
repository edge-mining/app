<script setup lang="ts">
import { computed, ref } from "vue";
import type { LoadDevice } from "../../core/models/homeLoadsProfile";
import type { EnergyLoadForecastProvider } from "../../core/models/energyLoadForecastProvider";
import type { EnergyLoadHistoryProvider } from "../../core/models/energyLoadHistoryProvider";
import { formatType } from "../../core/utils/index";
import {
  PhPencil,
  PhTrash,
  PhChartLine,
  PhBrain,
  PhCheckCircle,
  PhXCircle,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";

const props = defineProps<{
  devices: LoadDevice[];
  forecastProviders: EnergyLoadForecastProvider[];
  historyProviders: EnergyLoadHistoryProvider[];
}>();

const emit = defineEmits<{
  edit: [device: LoadDevice];
  delete: [device: LoadDevice];
  train: [device: LoadDevice];
  viewHistory: [device: LoadDevice];
}>();

const deviceToDelete = ref<LoadDevice | null>(null);
const showDeleteConfirm = ref(false);

function getForecastProvider(device: LoadDevice) {
  if (!device.energy_load_forecast_provider_id) return null;
  return props.forecastProviders.find(
    (p) => p.id === device.energy_load_forecast_provider_id
  ) ?? null;
}

function getHistoryProvider(device: LoadDevice) {
  if (!device.energy_load_history_provider_id) return null;
  return props.historyProviders.find(
    (p) => p.id === device.energy_load_history_provider_id
  ) ?? null;
}

const mlTypes = ["statsmodels", "xgboost", "skforecast"];
function isMLProvider(device: LoadDevice) {
  const fp = getForecastProvider(device);
  return fp ? mlTypes.includes(fp.adapter_type) : false;
}

function handleDeleteClick(device: LoadDevice) {
  deviceToDelete.value = device;
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  if (deviceToDelete.value) {
    emit("delete", deviceToDelete.value);
  }
  showDeleteConfirm.value = false;
  deviceToDelete.value = null;
}

function cancelDelete() {
  showDeleteConfirm.value = false;
  deviceToDelete.value = null;
}
</script>

<template>
  <div class="overflow-x-auto">
    <table class="table table-sm w-full">
      <thead>
        <tr class="text-base-content/60 text-xs uppercase tracking-wider">
          <th>Name</th>
          <th>Category</th>
          <th>Status</th>
          <th>Forecast Provider</th>
          <th>History Provider</th>
          <th class="text-center">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="device in devices"
          :key="device.id"
          class="hover:bg-base-200/30"
        >
          <td class="font-medium">{{ device.name }}</td>
          <td>
            <span class="badge badge-sm badge-ghost">
              {{ formatType(device.category) }}
            </span>
          </td>
          <td>
            <div class="flex items-center gap-1.5">
              <PhCheckCircle
                v-if="device.enabled"
                :size="16"
                class="text-success"
              />
              <PhXCircle v-else :size="16" class="text-base-content/30" />
              <span
                class="text-xs"
                :class="device.enabled ? 'text-success' : 'text-base-content/40'"
              >
                {{ device.enabled ? "Active" : "Inactive" }}
              </span>
            </div>
          </td>
          <td>
            <div v-if="getForecastProvider(device)" class="flex items-center gap-1.5">
              <PhBrain :size="14" class="text-purple-400 flex-shrink-0" />
              <span class="text-sm truncate max-w-[150px]" :title="getForecastProvider(device)?.name">
                {{ formatType(getForecastProvider(device)?.adapter_type ?? '') }}
              </span>
            </div>
            <span v-else class="text-xs text-base-content/30 italic">None</span>
          </td>
          <td>
            <div v-if="getHistoryProvider(device)" class="flex items-center gap-1.5">
              <PhChartLine :size="14" class="text-cyan-400 flex-shrink-0" />
              <span class="text-sm truncate max-w-[150px]" :title="getHistoryProvider(device)?.name">
                {{ formatType(getHistoryProvider(device)?.adapter_type ?? '') }}
              </span>
            </div>
            <span v-else class="text-xs text-base-content/30 italic">None</span>
          </td>
          <td class="text-center">
            <div class="flex items-center justify-center gap-1">
              <button
                v-if="getHistoryProvider(device)"
                class="btn btn-ghost btn-xs btn-square"
                title="View History & Forecast"
                @click="emit('viewHistory', device)"
              >
                <PhChartLine :size="15" class="text-cyan-400" />
              </button>
              <button
                v-if="isMLProvider(device)"
                class="btn btn-ghost btn-xs btn-square"
                title="Train Model"
                @click="emit('train', device)"
              >
                <PhBrain :size="15" class="text-warning" />
              </button>
              <button
                class="btn btn-ghost btn-xs btn-square"
                title="Edit"
                @click="emit('edit', device)"
              >
                <PhPencil :size="15" class="text-primary" />
              </button>
              <button
                class="btn btn-ghost btn-xs btn-square"
                title="Delete"
                @click="handleDeleteClick(device)"
              >
                <PhTrash :size="15" class="text-error" />
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Load Device"
    :message="`Are you sure you want to delete '${deviceToDelete?.name ?? ''}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>
