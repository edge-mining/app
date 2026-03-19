<script setup lang="ts">
import type { EnergySource } from "../../core/models/energySource";
import { EnergySourceType } from "../../core/models/energySource";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import { formatType, formatPower, formatCapacity } from "../../core/utils/index";
import { computed, ref } from "vue";
import {
  PhSun,
  PhWind,
  PhPlug,
  PhDrop,
  PhLightning,
  PhPencil,
  PhTrash,
  PhBatteryFull,
  PhChartLine,
  PhActivity,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";

const props = defineProps<{
  energySource: EnergySource;
}>();

const emit = defineEmits<{
  edit: [energySource: EnergySource];
  delete: [energySource: EnergySource];
}>();

const energyMonitorStore = useEnergyMonitorStore();
const forecastProviderStore = useForecastProviderStore();
const showDeleteConfirm = ref(false);

const energyMonitor = computed(() => {
  if (!props.energySource.energy_monitor_id) return null;
  return energyMonitorStore.energyMonitors.find(
    (em) => em.id === props.energySource.energy_monitor_id
  );
});

const forecastProvider = computed(() => {
  if (!props.energySource.forecast_provider_id) return null;
  return forecastProviderStore.forecastProviders.find(
    (fp) => fp.id === props.energySource.forecast_provider_id
  );
});

// Type-specific styling
const typeConfig = computed(() => {
  const type = props.energySource.type;

  // Define configs for known energy source types
  const configs: Record<EnergySourceType, { icon: typeof PhActivity; styleConfig: CardStyleConfig }> = {
    solar: {
      icon: PhSun,
      styleConfig: {
        gradient: "hover:from-amber-500/20 hover:to-orange-500/10",
        iconColor: "text-amber-400",
        badgeClass: "badge-warning",
        accentBorder: "border-l-border-base-300/50 hover:border-l-amber-500",
      },
    },
    wind: {
      icon: PhWind,
      styleConfig: {
        gradient: "hover:from-sky-500/20 hover:to-cyan-500/10",
        iconColor: "text-sky-400",
        badgeClass: "badge-info",
        accentBorder: "border-l-border-base-300/50 hover:border-l-sky-500",
      },
    },
    grid: {
      icon: PhPlug,
      styleConfig: {
        gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
        iconColor: "text-slate-300",
        badgeClass: "badge-neutral",
        accentBorder: "border-l-border-base-300/50 hover:border-l-slate-500",
      },
    },
    hydroelectric: {
      icon: PhDrop,
      styleConfig: {
        gradient: "hover:from-blue-500/20 hover:to-indigo-500/10",
        iconColor: "text-blue-400",
        badgeClass: "badge-info",
        accentBorder: "border-l-border-base-300/50 hover:border-l-blue-500",
      },
    },
    other: {
      icon: PhLightning,
      styleConfig: {
        gradient: "hover:from-purple-500/20 hover:to-violet-500/10",
        iconColor: "text-purple-400",
        badgeClass: "badge-secondary",
        accentBorder: "border-l-border-base-300/50 hover:border-l-purple-500",
      },
    },
  };

  return (
    configs[type] || {
      icon: PhLightning,
      styleConfig: {
        gradient: "hover:from-purple-500/20 hover:to-violet-500/10",
        iconColor: "text-purple-400",
        iconBgColor: "bg-base-100/60",
        badgeClass: "badge-secondary",
        accentBorder: "border-l-border-base-300/50 hover:border-l-purple-500",
      },
    }
  );
});

function handleEdit() {
  emit("edit", props.energySource);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.energySource);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}


</script>

<template>
  <EdgeMiningCard
    :icon="typeConfig.icon"
    :style-config="typeConfig.styleConfig"
  >
    <!-- Title -->
    <template #title>
      {{ energySource.name }}
    </template>

    <!-- Badges -->
    <template #badges>
      <!-- Adapter Type Badge -->
      <span class="badge badge-sm" :class="typeConfig.styleConfig.badgeClass">
        {{ formatType(energySource.type) }}
      </span>

      <!-- ID -->
      <ResourceId v-if="energySource.id" :id="energySource.id" />
    </template>

    <!-- Actions -->
    <template #actions>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-primary/20"
        @click="handleEdit"
        title="Edit"
      >
        <PhPencil :size="18" class="text-primary" />
      </button>
      <button
        class="btn btn-ghost btn-sm btn-square hover:bg-error/20"
        @click="handleDeleteClick"
        title="Delete"
      >
        <PhTrash :size="18" class="text-error" />
      </button>
    </template>

    <!-- Main Content -->
    <div class="grid grid-cols-2 gap-3">
      <!-- Nominal Power -->
      <div
        v-if="energySource.nominal_power_max"
        class="metric-box bg-base-100/40 rounded-lg px-3 py-2"
      >
        <div class="flex items-center gap-1.5 text-xs text-base-content/60 mb-1">
          <PhLightning :size="16" />
          <span>Max Power</span>
        </div>
        <div class="text-lg font-semibold text-base-content">
          {{ formatPower(energySource.nominal_power_max) }}
        </div>
      </div>

      <!-- Storage Capacity -->
      <div
        v-if="energySource.storage?.nominal_capacity"
        class="metric-box bg-base-100/40 rounded-lg px-3 py-2"
      >
        <div class="flex items-center gap-1.5 text-xs text-base-content/60 mb-1">
          <PhBatteryFull :size="16" />
          <span>Storage</span>
        </div>
        <div class="text-lg font-semibold text-base-content">
          {{ formatCapacity(energySource.storage?.nominal_capacity) }}
        </div>
      </div>

      <!-- Grid Contracted Power -->
      <div
        v-if="energySource.grid?.contracted_power"
        class="metric-box bg-base-100/40 rounded-lg px-3 py-2"
      >
        <div class="flex items-center gap-1.5 text-xs text-base-content/60 mb-1">
          <PhPlug :size="16" />
          <span>Grid Contracted</span>
        </div>
        <div class="text-lg font-semibold text-base-content">
          {{ formatPower(energySource.grid?.contracted_power) }}
        </div>
      </div>

      <!-- External Source -->
      <div
        v-if="energySource.external_source"
        class="metric-box bg-base-100/40 rounded-lg px-3 py-2"
      >
        <div class="flex items-center gap-1.5 text-xs text-base-content/60 mb-1">
          <PhLightning :size="16" />
          <span>External Source</span>
        </div>
        <div class="text-lg font-semibold text-base-content">
          {{ formatPower(energySource.external_source) }}
        </div>
      </div>

      <!-- Empty State for no metrics -->
      <div
        v-if="
          !energySource.nominal_power_max &&
          !energySource.storage?.nominal_capacity &&
          !energySource.grid?.contracted_power &&
          !energySource.external_source
        "
        class="col-span-2"
      >
        <div class="text-sm text-base-content/40 italic">No metrics configured</div>
      </div>
    </div>

    <!-- Footer -->
    <template #footer v-if="energyMonitor || forecastProvider">
      <div class="flex flex-wrap gap-4">
        <!-- Energy Monitor -->
        <div v-if="energyMonitor" class="flex items-center gap-2">
          <div
            class="h-6 w-6 rounded-full bg-success/20 flex items-center justify-center"
          >
            <PhActivity :size="14" class="text-success" />
          </div>
          <div>
            <div class="text-[10px] uppercase tracking-wider text-base-content/40">
              Monitor
            </div>
            <div class="text-sm text-base-content/80 leading-tight">
              {{ energyMonitor.name }}
            </div>
          </div>
        </div>

        <!-- Forecast Provider -->
        <div v-if="forecastProvider" class="flex items-center gap-2">
          <div
            class="h-6 w-6 rounded-full bg-info/20 flex items-center justify-center"
          >
            <PhChartLine :size="14" class="text-info" />
          </div>
          <div>
            <div class="text-[10px] uppercase tracking-wider text-base-content/40">
              Forecast
            </div>
            <div class="text-sm text-base-content/80 leading-tight">
              {{ forecastProvider.name }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Energy Source"
    :message="`Are you sure you want to delete '${energySource.name}'? This action cannot be undone.`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

<style scoped>
.metric-box {
  backdrop-filter: blur(4px);
}
</style>
