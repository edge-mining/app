<script setup lang="ts">
import type { EnergySource } from "../../core/models/energySource";
import { EnergySourceType } from "../../core/models/energySource";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
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
  PhHash,
  PhChartLine,
  PhActivity,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";

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
  switch (props.energySource.type) {
    case EnergySourceType.SOLAR:
      return {
        icon: PhSun,
        gradient: "hover:from-amber-500/20 hover:to-orange-500/10",
        iconColor: "text-amber-400",
        badgeClass: "badge-warning",
        accentBorder: "border-l-border-base-300/50 hover:border-l-amber-500",
      };
    case EnergySourceType.WIND:
      return {
        icon: PhWind,
        gradient: "hover:from-sky-500/20 hover:to-cyan-500/10",
        iconColor: "text-sky-400",
        badgeClass: "badge-info",
        accentBorder: "border-l-border-base-300/50 hover:border-l-sky-500",
      };
    case EnergySourceType.GRID:
      return {
        icon: PhPlug,
        gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
        iconColor: "text-slate-300",
        badgeClass: "badge-neutral",
        accentBorder: "border-l-border-base-300/50 hover:border-l-slate-500",
      };
    case EnergySourceType.HYDROELECTRIC:
      return {
        icon: PhDrop,
        gradient: "hover:from-blue-500/20 hover:to-indigo-500/10",
        iconColor: "text-blue-400",
        badgeClass: "badge-info",
        accentBorder: "border-l-border-base-300/50 hover:border-l-blue-500",
      };
    default:
      return {
        icon: PhLightning,
        gradient: "hover:from-purple-500/20 hover:to-violet-500/10",
        iconColor: "text-purple-400",
        badgeClass: "badge-secondary",
        accentBorder: "border-l-border-base-300/50 hover:border-l-purple-500",
      };
  }
});

// Format power values
function formatPower(watts: number | undefined): string {
  if (watts === undefined || watts === null) return "-";
  if (watts >= 1000000) return `${(watts / 1000000).toFixed(1)} MW`;
  if (watts >= 1000) return `${(watts / 1000).toFixed(1)} kW`;
  return `${watts} W`;
}

function formatCapacity(wh: number | undefined): string {
  if (wh === undefined || wh === null) return "-";
  if (wh >= 1000000) return `${(wh / 1000000).toFixed(1)} MWh`;
  if (wh >= 1000) return `${(wh / 1000).toFixed(1)} kWh`;
  return `${wh} Wh`;
}

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

// Copy ID to clipboard
const idCopied = ref(false);
async function copyId() {
  if (!props.energySource.id) return;
  try {
    await navigator.clipboard.writeText(String(props.energySource.id));
    idCopied.value = true;
    setTimeout(() => (idCopied.value = false), 1500);
  } catch {
    // Fallback for older browsers
    const el = document.createElement("textarea");
    el.value = String(props.energySource.id);
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
    idCopied.value = true;
    setTimeout(() => (idCopied.value = false), 1500);
  }
}
</script>

<template>
  <div
    class="energy-source-card group relative flex flex-col rounded-xl border border-base-300/50 bg-gradient-to-br from-transparent to-transparent transition-all duration-300 hover:border-base-300 hover:shadow-lg hover:shadow-black/20"
    :class="[typeConfig.gradient, `border-l-4 ${typeConfig.accentBorder}`]"
  >
    <!-- Header -->
    <div class="flex items-start justify-between p-4 pb-3">
      <div class="flex items-center gap-3">
        <div
          class="flex h-12 w-12 items-center justify-center rounded-xl bg-base-100/60 backdrop-blur-sm"
        >
          <component
            :is="typeConfig.icon"
            :size="28"
            weight="duotone"
            :class="typeConfig.iconColor"
          />
        </div>
        <div>
          <h3 class="text-lg font-semibold text-base-content leading-tight">
            {{ energySource.name }}
          </h3>
          <div class="flex items-center gap-2 mt-1">
            <span class="badge badge-sm" :class="typeConfig.badgeClass">
              {{ energySource.type }}
            </span>
            <button
              v-if="energySource.id"
              class="tooltip tooltip-top text-xs opacity-50 hover:opacity-100 transition-opacity flex items-center gap-0.5"
              :data-tip="idCopied ? 'Copied!' : `ID: ${energySource.id}`"
              @click="copyId"
            >
              <PhHash :size="12" />
              <span class="font-mono small text-left">{{ energySource.id.split("-")[0] }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
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
      </div>
    </div>

    <!-- Metrics Grid -->
    <div class="px-4 pb-4 grid grid-cols-2 gap-3 flex-grow content-start">
      <!-- Nominal Power -->
      <div
        v-if="energySource.nominal_power_max"
        class="metric-box bg-base-100/40 rounded-lg px-3 py-2"
      >
        <div class="flex items-center gap-1.5 text-xs text-base-content/60 mb-1">
          <PhLightning :size="14" />
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
          <PhBatteryFull :size="14" />
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
          <PhPlug :size="14" />
          <span>Contracted</span>
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
          <PhLightning :size="14" />
          <span>External</span>
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

    <!-- Integrations (always at bottom with mt-auto) -->
    <div
      v-if="energyMonitor || forecastProvider"
      class="border-t border-base-300/30 px-4 py-3 bg-base-100/20 mt-auto"
    >
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
    </div>
  </div>

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
.energy-source-card {
  background-color: oklch(28% 0 0 / 0.8);
}

.metric-box {
  backdrop-filter: blur(4px);
}
</style>
