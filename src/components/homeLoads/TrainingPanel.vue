<script setup lang="ts">
import { computed, ref } from "vue";
import type { LoadConsumptionModel } from "../../core/models/loadTraining";
import type { LoadDevice } from "../../core/models/homeLoadsProfile";
import { useLoadTrainingStore } from "../../core/stores/loadTrainingStore";
import { formatType } from "../../core/utils/index";
import {
  PhBrain,
  PhPlay,
  PhCheckCircle,
  PhXCircle,
  PhArrowsClockwise,
  PhTrash,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";

const props = defineProps<{
  profileId?: string;
  devices: LoadDevice[];
}>();

const emit = defineEmits<{
  trainAll: [];
  trainDevice: [deviceId: string];
}>();

const trainingStore = useLoadTrainingStore();

const modelToDelete = ref<(LoadConsumptionModel & { deviceName: string }) | null>(null);
const showDeleteConfirm = ref(false);

function handleDeleteClick(model: LoadConsumptionModel & { deviceName: string }) {
  modelToDelete.value = model;
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  if (modelToDelete.value?.id) {
    trainingStore.deleteModel(modelToDelete.value.id);
  }
  showDeleteConfirm.value = false;
  modelToDelete.value = null;
}

function cancelDelete() {
  showDeleteConfirm.value = false;
  modelToDelete.value = null;
}

const modelsWithDeviceName = computed(() => {
  return trainingStore.models.map((m) => {
    const device = props.devices.find((d) => d.id === m.device_id);
    return {
      ...m,
      deviceName: device?.name ?? "Unknown",
    };
  });
});

function formatDate(dateStr?: string): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleString();
}

function formatMetric(val?: number): string {
  if (val === undefined || val === null) return "—";
  return val.toFixed(3);
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h2 class="text-lg font-bold text-base-content flex items-center gap-2">
          Trained Models
        </h2>
      </div>
      <button
        class="btn btn-primary gap-2"
        :disabled="trainingStore.trainingInProgress"
        @click="emit('trainAll')"
      >
        <PhArrowsClockwise
          v-if="trainingStore.trainingInProgress"
          :size="18"
          class="animate-spin"
        />
        <PhPlay v-else :size="18" />
        Train All Devices
      </button>
    </div>

    <!-- Training in progress banner -->
    <div
      v-if="trainingStore.trainingInProgress"
      class="alert alert-info bg-info/10 border-info/30"
    >
      <span class="loading loading-spinner loading-sm"></span>
      <span>Training in progress... This may take a few minutes.</span>
    </div>

    <!-- Models Table -->
    <div v-if="modelsWithDeviceName.length > 0" class="overflow-x-auto">
      <table class="table table-sm w-full">
        <thead>
          <tr class="text-base-content/60 text-xs uppercase tracking-wider">
            <th>Device</th>
            <th>Adapter</th>
            <th>Status</th>
            <th class="text-right">MAE</th>
            <th class="text-right">RMSE</th>
            <th class="text-right">Backtest MAE</th>
            <th class="text-right">Backtest RMSE</th>
            <th class="text-right">Folds</th>
            <th class="text-right">Samples</th>
            <th>Tuning</th>
            <th>Trained At</th>
            <th class="text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="model in modelsWithDeviceName"
            :key="model.id"
            class="hover:bg-base-200/30"
          >
            <td class="font-medium">{{ model.deviceName }}</td>
            <td>
              <span class="badge badge-sm badge-ghost">
                {{ formatType(model.adapter_type) }}
              </span>
            </td>
            <td>
              <div class="flex items-center gap-1.5">
                <PhCheckCircle
                  v-if="model.is_active"
                  :size="16"
                  class="text-success"
                />
                <PhXCircle v-else :size="16" class="text-base-content/30" />
                <span
                  class="text-xs"
                  :class="model.is_active ? 'text-success' : 'text-base-content/40'"
                >
                  {{ model.is_active ? "Active" : "Inactive" }}
                </span>
              </div>
            </td>
            <td class="text-right font-mono text-sm">{{ formatMetric(model.mae) }}</td>
            <td class="text-right font-mono text-sm">{{ formatMetric(model.rmse) }}</td>
            <td class="text-right font-mono text-sm">{{ formatMetric(model.backtest_mae) }}</td>
            <td class="text-right font-mono text-sm">{{ formatMetric(model.backtest_rmse) }}</td>
            <td class="text-right font-mono text-sm">{{ model.backtest_folds || '—' }}</td>
            <td class="text-right font-mono text-sm">{{ model.samples_used }}</td>
            <td>
              <div v-if="model.tuning_params && Object.keys(model.tuning_params).length > 0" class="dropdown dropdown-hover dropdown-left">
                <label tabindex="0" class="badge badge-sm badge-ghost cursor-pointer">
                  {{ Object.keys(model.tuning_params).length }} params
                </label>
                <div tabindex="0" class="dropdown-content z-10 p-3 shadow-lg bg-base-200 rounded-lg w-64">
                  <div class="text-xs font-semibold mb-2 text-base-content/60">Tuning Parameters</div>
                  <div v-for="(val, key) in model.tuning_params" :key="key" class="flex justify-between text-xs py-0.5">
                    <span class="text-base-content/60">{{ key }}</span>
                    <span class="font-mono text-base-content">{{ val }}</span>
                  </div>
                </div>
              </div>
              <span v-else class="text-xs text-base-content/30 italic">—</span>
            </td>
            <td class="text-sm text-base-content/60">{{ formatDate(model.trained_at) }}</td>
            <td class="text-center">
              <div class="flex items-center justify-center gap-1">
                <button
                  v-if="model.device_id"
                  class="btn btn-ghost btn-xs gap-1"
                  :disabled="trainingStore.trainingInProgress"
                  title="Retrain this device"
                  @click="emit('trainDevice', model.device_id!)"
                >
                  <PhArrowsClockwise :size="14" />
                  Retrain
                </button>
                <button
                  v-if="model.id"
                  class="btn btn-ghost btn-xs text-error gap-1"
                  title="Delete this model"
                  @click="handleDeleteClick(model)"
                >
                  <PhTrash :size="14" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="flex flex-col items-center justify-center py-16 text-center"
    >
      <div class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4">
        <PhBrain :size="40" class="text-base-content/30" />
      </div>
      <h3 class="text-lg font-semibold text-base-content/80">No trained models</h3>
      <p class="text-sm text-base-content/50 mt-1 max-w-sm">
        Train your first models by clicking "Train All Devices" or train individual devices from the Devices tab.
      </p>
      <button
        class="btn btn-primary btn-sm mt-4 gap-2"
        :disabled="trainingStore.trainingInProgress"
        @click="emit('trainAll')"
      >
        <PhPlay :size="16" />
        Start Training
      </button>
    </div>

    <ConfirmDialog
      :open="showDeleteConfirm"
      title="Delete Model"
      :message="`Are you sure you want to delete the ${modelToDelete ? formatType(modelToDelete.adapter_type) : ''} model for '${modelToDelete?.deviceName ?? ''}'?`"
      confirm-text="Delete"
      variant="danger"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>
