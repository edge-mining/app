<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useClimateMonitorStore } from "../../core/stores/climateMonitorStore";
import { useClimateZoneStore } from "../../core/stores/climateZoneStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import ClimateMonitorCard from "../../components/climateMonitors/ClimateMonitorCard.vue";
import ClimateMonitorFormModal from "../../components/climateMonitors/ClimateMonitorFormModal.vue";
import type { ClimateMonitor } from "../../core/models/climateMonitor";
import {
  PhPlus,
  PhThermometerSimple,
  PhHouse,
} from "@phosphor-icons/vue";

const climateMonitorStore = useClimateMonitorStore();
const climateZoneStore = useClimateZoneStore();
const externalServiceStore = useExternalServiceStore();

// Modal state
const showModal = ref(false);
const editingMonitor = ref<ClimateMonitor | undefined>(undefined);
const isEditMode = ref(false);

// Filter state
const selectedAdapterFilter = ref<string>("all");

const adapterFilters = computed(() => {
  const types = climateMonitorStore.adapterTypes;
  return [
    { value: "all", label: "All", icon: PhThermometerSimple, iconColor: "" },
    ...types.map((type) => ({
      value: type,
      label: formatAdapterType(type),
      icon: getAdapterIcon(type),
      iconColor: getAdapterIconColor(type),
    })),
  ];
});

const filteredMonitors = computed(() => {
  if (selectedAdapterFilter.value === "all") {
    return climateMonitorStore.climateMonitors;
  }
  return climateMonitorStore.climateMonitors.filter(
    (m) => m.adapter_type === selectedAdapterFilter.value
  );
});

// Stats
const stats = computed(() => {
  const monitors = climateMonitorStore.climateMonitors;
  const totalMonitors = monitors.length;
  const linkedMonitors = monitors.filter((m) => m.external_service_id).length;
  const assignedZonesCount = climateZoneStore.climateZones.filter(
    (z) => z.climate_monitor_id
  ).length;
  const adapterCounts = monitors.reduce((acc, m) => {
    acc[m.adapter_type] = (acc[m.adapter_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return { totalMonitors, linkedMonitors, assignedZonesCount, adapterCounts };
});

onMounted(() => {
  climateMonitorStore.loadClimateMonitors();
  climateMonitorStore.loadAdapterTypes();
  climateZoneStore.loadClimateZones();
  externalServiceStore.loadExternalServices();
});

function formatAdapterType(type: string): string {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function getAdapterIcon(type: string) {
  const icons: Record<string, any> = {
    home_assistant_api: PhHouse,
  };
  return icons[type] || PhThermometerSimple;
}

function getAdapterIconColor(type: string): string {
  const colors: Record<string, string> = {
    home_assistant_api: "text-orange-400",
  };
  return colors[type] || "text-slate-400";
}

function getAssignedZonesCount(monitorId: string | undefined): number {
  if (!monitorId) return 0;
  return climateZoneStore.climateZones.filter(
    (z) => z.climate_monitor_id === monitorId
  ).length;
}

function openAddModal() {
  editingMonitor.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(monitor: ClimateMonitor) {
  editingMonitor.value = { ...monitor };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingMonitor.value = undefined;
}

function handleSave(monitor: ClimateMonitor) {
  if (isEditMode.value && monitor.id) {
    climateMonitorStore
      .updateClimateMonitor(monitor.id.toString(), monitor)
      .then(() => {
        climateMonitorStore.loadClimateMonitors();
        handleCloseModal();
      })
      .showToasts(
        "Climate monitor updated successfully",
        "Failed to update climate monitor"
      );
  } else {
    climateMonitorStore
      .addClimateMonitor(monitor)
      .then(() => {
        climateMonitorStore.loadClimateMonitors();
        handleCloseModal();
      })
      .showToasts(
        "Climate monitor created successfully",
        "Failed to create climate monitor"
      );
  }
}

function handleDelete(monitor: ClimateMonitor) {
  climateMonitorStore
    .deleteClimateMonitor(monitor.id!.toString())
    .then(() => {
      climateMonitorStore.loadClimateMonitors();
    })
    .showToasts(
      "Climate monitor deleted successfully",
      "Failed to delete climate monitor"
    );
}

function handleCheck(monitor: ClimateMonitor) {
  climateMonitorStore
    .checkMonitor(monitor.id!.toString())
    .showToasts(
      "Climate monitor is reachable",
      "Climate monitor check failed"
    );
}

function getFilterCount(adapterType: string): number {
  if (adapterType === "all") return stats.value.totalMonitors;
  return stats.value.adapterCounts[adapterType] || 0;
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <!-- Header with Stats -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Climate Monitors</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Configure adapters for monitoring room temperature and humidity
          </p>
        </div>

        <button class="btn btn-primary gap-2" @click="openAddModal">
          <PhPlus :size="20" weight="bold" />
          Add Monitor
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">{{ stats.totalMonitors }}</div>
            <div class="stat-label">Total Monitors</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-teal-400">{{ stats.assignedZonesCount }}</div>
            <div class="stat-label">Monitored Zones</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-info">{{ stats.linkedMonitors }}</div>
            <div class="stat-label">With External Service</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0 overflow-hidden">
            <div class="flex flex-wrap gap-2 sm:gap-3 items-center min-h-[2rem] sm:min-h-[2.25rem]">
              <div
                v-for="(count, adapterType) in stats.adapterCounts"
                :key="adapterType"
                class="flex items-center gap-0.5 sm:gap-1"
              >
                <component :is="getAdapterIcon(String(adapterType))" :size="18" :class="[getAdapterIconColor(String(adapterType)), 'flex-shrink-0 sm:w-6 sm:h-6']" />
                <span class="stat-type-count">{{ count }}</span>
              </div>
              <div v-if="Object.keys(stats.adapterCounts).length === 0" class="text-base-content/40">
                -
              </div>
            </div>
            <div class="stat-label">By Adapter</div>
          </div>
        </div>

        <!-- Filter Tabs -->
        <div v-if="climateMonitorStore.adapterTypes.length > 1" class="flex gap-2 flex-wrap">
          <button
            v-for="filter in adapterFilters"
            :key="filter.value"
            class="btn btn-sm gap-2 transition-all"
            :class="[
              selectedAdapterFilter === filter.value
                ? 'btn-primary'
                : 'btn-ghost opacity-70 hover:opacity-100',
            ]"
            @click="selectedAdapterFilter = filter.value"
          >
            <component :is="filter.icon" :size="16" />
            {{ filter.label }}
            <span
              v-if="getFilterCount(filter.value) > 0"
              class="badge badge-sm"
              :class="selectedAdapterFilter === filter.value ? 'bg-white/20 text-neutral-900' : 'badge-neutral'"
            >
              {{ getFilterCount(filter.value) }}
            </span>
          </button>
        </div>

        <!-- Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <ClimateMonitorCard
            v-for="monitor in filteredMonitors"
            :key="monitor.id"
            :climate-monitor="monitor"
            :assigned-zones-count="getAssignedZonesCount(monitor.id)"
            @edit="handleEdit"
            @delete="handleDelete"
            @check="handleCheck"
          />

          <!-- Empty State -->
          <div
            v-if="filteredMonitors.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhThermometerSimple :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              {{ selectedAdapterFilter === "all" ? "No climate monitors yet" : "No monitors of this type" }}
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              {{
                selectedAdapterFilter === "all"
                  ? "Add your first climate monitor to start reading temperature data."
                  : "Try selecting a different filter or add a new monitor."
              }}
            </p>
            <button
              v-if="selectedAdapterFilter === 'all'"
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Monitor
            </button>
          </div>
        </div>

        <!-- Form Modal -->
        <ClimateMonitorFormModal
          :open="showModal"
          :climate-monitor="editingMonitor"
          :is-edit="isEditMode"
          @close="handleCloseModal"
          @save="handleSave"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  transition: all 0.2s ease;
}
</style>
