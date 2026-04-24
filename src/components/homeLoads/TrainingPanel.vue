<script setup lang="ts">
import { computed } from "vue";
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
} from "@phosphor-icons/vue";

const props = defineProps<{
  profileId?: string;
  devices: LoadDevice[];
}>();

const emit = defineEmits<{
  trainAll: [];
  trainDevice: [deviceId: string];
}>();

const trainingStore = useLoadTrainingStore();

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
          <PhBrain :size="22" class="text-purple-400" />
          Trained Models
        </h2>
        <p class="text-sm text-base-content/50 mt-0.5">
          View and manage forecast models for your devices
        </p>
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
            <th class="text-right">Samples</th>
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
            <td class="text-right font-mono text-sm">{{ model.samples_used }}</td>
            <td class="text-sm text-base-content/60">{{ formatDate(model.trained_at) }}</td>
            <td class="text-center">
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
  </div>
</template>
