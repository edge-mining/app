<script setup lang="ts">
import type { LoadDevice } from "../../core/models/homeLoadsProfile";
import type { EnergyLoadForecastProvider } from "../../core/models/energyLoadForecastProvider";
import type { EnergyLoadHistoryProvider } from "../../core/models/energyLoadHistoryProvider";
import { formatType } from "../../core/utils/index";
import { computed, ref } from "vue";
import {
  PhPencil,
  PhTrash,
  PhChartLine,
  PhBrain,
  PhToggleLeft,
  PhToggleRight,
  PhPlug,
  PhCloudArrowDown,
  PhGear,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";

const props = defineProps<{
  device: LoadDevice;
  forecastProviders: EnergyLoadForecastProvider[];
  historyProviders: EnergyLoadHistoryProvider[];
}>();

const emit = defineEmits<{
  edit: [device: LoadDevice];
  delete: [device: LoadDevice];
  viewHistory: [device: LoadDevice];
  train: [device: LoadDevice];
}>();

const showDeleteConfirm = ref(false);

const assignedForecastProvider = computed(() => {
  if (!props.device.energy_load_forecast_provider_id) return null;
  return props.forecastProviders.find(
    (p) => p.id === props.device.energy_load_forecast_provider_id
  );
});

const assignedHistoryProvider = computed(() => {
  if (!props.device.energy_load_history_provider_id) return null;
  return props.historyProviders.find(
    (p) => p.id === props.device.energy_load_history_provider_id
  );
});

const isMLProvider = computed(() => {
  if (!assignedForecastProvider.value) return false;
  const mlTypes = ["statsmodels", "xgboost"];
  return mlTypes.includes(assignedForecastProvider.value.adapter_type);
});

const categoryConfig = computed(() => {
  const configs: Record<string, { styleConfig: CardStyleConfig; icon: typeof PhGear }> = {
    controllable: {
      icon: PhToggleRight,
      styleConfig: {
        gradient: "hover:from-sky-500/20 hover:to-cyan-500/10",
        iconColor: "text-sky-400",
        badgeClass: "badge-info",
        accentBorder: "border-l-base-300/50 hover:border-l-sky-500",
      },
    },
    continuous: {
      icon: PhPlug,
      styleConfig: {
        gradient: "hover:from-teal-500/20 hover:to-emerald-500/10",
        iconColor: "text-teal-400",
        badgeClass: "bg-teal-500/20 text-teal-400",
        accentBorder: "border-l-base-300/50 hover:border-l-teal-500",
      },
    },
    seasonal: {
      icon: PhCloudArrowDown,
      styleConfig: {
        gradient: "hover:from-amber-500/20 hover:to-orange-500/10",
        iconColor: "text-amber-400",
        badgeClass: "badge-warning",
        accentBorder: "border-l-base-300/50 hover:border-l-amber-500",
      },
    },
    occasional: {
      icon: PhGear,
      styleConfig: {
        gradient: "hover:from-purple-500/20 hover:to-violet-500/10",
        iconColor: "text-purple-400",
        badgeClass: "bg-purple-500/20 text-purple-400",
        accentBorder: "border-l-base-300/50 hover:border-l-purple-500",
      },
    },
  };
  return (
    configs[props.device.category] || {
      icon: PhGear,
      styleConfig: {
        gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
        iconColor: "text-slate-400",
        badgeClass: "badge-neutral",
        accentBorder: "border-l-base-300/50 hover:border-l-slate-500",
      },
    }
  );
});

function handleEdit() {
  emit("edit", props.device);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.device);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}
</script>

<template>
  <EdgeMiningCard
    :icon="categoryConfig.icon"
    :style-config="categoryConfig.styleConfig"
    :dimmed="!device.enabled"
    card-class="min-h-[220px]"
  >
    <template #title>
      {{ device.name }}
    </template>

    <template #badges>
      <span
        class="badge badge-sm max-w-[10rem] px-2 overflow-hidden"
        :class="categoryConfig.styleConfig.badgeClass"
        :title="formatType(device.category)"
      >
        <span class="marquee-on-overflow">{{ formatType(device.category) }}</span>
      </span>
      <span
        v-if="!device.enabled"
        class="badge badge-sm badge-ghost opacity-60"
      >
        Disabled
      </span>
      <ResourceId v-if="device.id" :id="device.id" />
    </template>

    <template #actions>
      <button
        v-if="assignedHistoryProvider"
        class="btn btn-ghost btn-sm btn-square hover:bg-info/20"
        title="View History"
        @click="$emit('viewHistory', device)"
      >
        <PhChartLine :size="18" class="text-info" />
      </button>
      <button
        v-if="isMLProvider"
        class="btn btn-ghost btn-sm btn-square hover:bg-warning/20"
        title="Train Model"
        @click="$emit('train', device)"
      >
        <PhBrain :size="18" class="text-warning" />
      </button>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-primary/20"
        title="Edit"
        @click="handleEdit"
      >
        <PhPencil :size="18" class="text-primary" />
      </button>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-error/20"
        title="Delete"
        @click="handleDeleteClick"
      >
        <PhTrash :size="18" class="text-error" />
      </button>
    </template>

    <!-- Main Content -->
    <div class="space-y-3">
      <!-- Status -->
      <div class="flex items-center gap-2">
        <component
          :is="device.enabled ? PhToggleRight : PhToggleLeft"
          :size="18"
          :class="device.enabled ? 'text-success' : 'text-base-content/30'"
        />
        <span class="text-sm" :class="device.enabled ? 'text-success' : 'text-base-content/40'">
          {{ device.enabled ? "Active" : "Inactive" }}
        </span>
      </div>

      <!-- Providers summary -->
      <div class="space-y-1.5">
        <div class="flex items-center gap-2 text-sm">
          <PhBrain :size="14" class="text-base-content/50 flex-shrink-0" />
          <span class="text-base-content/60 truncate">
            {{ assignedForecastProvider ? assignedForecastProvider.name : "No forecast provider" }}
          </span>
        </div>
        <div class="flex items-center gap-2 text-sm">
          <PhChartLine :size="14" class="text-base-content/50 flex-shrink-0" />
          <span class="text-base-content/60 truncate">
            {{ assignedHistoryProvider ? assignedHistoryProvider.name : "No history provider" }}
          </span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-center justify-between gap-2">
        <div v-if="assignedForecastProvider" class="flex items-center gap-1 text-xs text-base-content/40">
          <PhGear :size="14" />
          <span>{{ formatType(assignedForecastProvider.adapter_type) }}</span>
        </div>
        <div v-if="assignedHistoryProvider" class="flex items-center gap-1 text-xs text-base-content/40">
          <PhChartLine :size="14" />
          <span>{{ formatType(assignedHistoryProvider.adapter_type) }}</span>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Load Device"
    :message="`Are you sure you want to delete '${device.name}'?`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>
