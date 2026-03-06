<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import EnergyMonitorCard from "../../components/energyMonitors/EnergyMonitorCard.vue";
import EnergyMonitorFormModal from "../../components/energyMonitors/EnergyMonitorFormModal.vue";
import type { EnergyMonitor } from "../../core/models/energyMonitor";
import {
  PhPlus,
  PhActivity,
  PhHouse,
  PhBroadcast,
} from "@phosphor-icons/vue";
import DummySolarIcon from "../../components/icons/DummySolarIcon.vue";

const energyMonitorStore = useEnergyMonitorStore();
const energySourceStore = useEnergySourceStore();
const externalServiceStore = useExternalServiceStore();

// Modal state
const showModal = ref(false);
const editingEnergyMonitor = ref<EnergyMonitor | undefined>(undefined);
const isEditMode = ref(false);

// Filter state
const selectedAdapterFilter = ref<string>("all");

const adapterFilters = computed(() => {
  const types = energyMonitorStore.adapterTypes;
  return [
    { value: "all", label: "All", icon: PhActivity, iconColor: "" },
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
    return energyMonitorStore.energyMonitors;
  }
  return energyMonitorStore.energyMonitors.filter(
    (em) => em.adapter_type === selectedAdapterFilter.value
  );
});

// Stats
const stats = computed(() => {
  const monitors = energyMonitorStore.energyMonitors;
  const totalMonitors = monitors.length;
  
  // Count monitors with external service linked
  const linkedMonitors = monitors.filter(
    (m) => m.external_service_id
  ).length;

  // Count total assigned energy sources
  const assignedSourcesCount = energySourceStore.energySources.filter(
    (es) => es.energy_monitor_id
  ).length;

  // Count by adapter type
  const adapterCounts = monitors.reduce((acc, m) => {
    acc[m.adapter_type] = (acc[m.adapter_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    totalMonitors,
    linkedMonitors,
    assignedSourcesCount,
    adapterCounts,
  };
});

onMounted(() => {
  energyMonitorStore.loadEnergyMonitors();
  energyMonitorStore.loadAdapterTypes();
  energySourceStore.loadEnergySources();
  externalServiceStore.loadExternalServices();
});

function formatAdapterType(type: string): string {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

// Get icon for adapter type
function getAdapterIcon(type: string) {
  const icons: Record<string, any> = {
    dummy_solar: DummySolarIcon,
    home_assistant_api: PhHouse,
    home_assistant_mqtt: PhBroadcast,
  };
  return icons[type] || PhActivity;
}

// Get icon color for adapter type
function getAdapterIconColor(type: string): string {
  const colors: Record<string, string> = {
    dummy_solar: "text-amber-400",
    home_assistant_api: "text-sky-400",
    home_assistant_mqtt: "text-purple-400",
  };
  return colors[type] || "text-slate-400";
}

function openAddModal() {
  editingEnergyMonitor.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(energyMonitor: EnergyMonitor) {
  editingEnergyMonitor.value = { ...energyMonitor };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingEnergyMonitor.value = undefined;
}

function handleSave(energyMonitor: EnergyMonitor) {
  if (isEditMode.value && energyMonitor.id) {
    energyMonitorStore
      .updateEnergyMonitor(energyMonitor.id.toString(), energyMonitor)
      .then(() => {
        energyMonitorStore.loadEnergyMonitors();
        handleCloseModal();
      });
  } else {
    energyMonitorStore.addEnergyMonitor(energyMonitor).then(() => {
      energyMonitorStore.loadEnergyMonitors();
      handleCloseModal();
    });
  }
}

function handleDelete(energyMonitor: EnergyMonitor) {
  energyMonitorStore.deleteEnergyMonitor(energyMonitor.id!.toString())
    .then(() => {
      energyMonitorStore.loadEnergyMonitors();
    })
    .showToasts(
      "Energy monitor deleted successfully",
      "Failed to delete energy monitor"
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
          <h1 class="text-2xl font-bold text-base-content">Energy Monitors</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Configure adapters for monitoring your energy sources
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
            <div class="stat-value text-teal-400">{{ stats.assignedSourcesCount }}</div>
            <div class="stat-label">Monitored Sources</div>
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
        <div class="flex gap-2 flex-wrap">
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
          <EnergyMonitorCard
            v-for="monitor in filteredMonitors"
            :key="monitor.id"
            :energy-monitor="monitor"
            :all-energy-sources="energySourceStore.energySources"
            @edit="handleEdit"
            @delete="handleDelete"
          />

          <!-- Empty State -->
          <div
            v-if="filteredMonitors.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhActivity :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              {{ selectedAdapterFilter === "all" ? "No monitors yet" : "No monitors of this type" }}
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              {{
                selectedAdapterFilter === "all"
                  ? "Add your first energy monitor to start tracking your energy sources."
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
        <EnergyMonitorFormModal
          :open="showModal"
          :energy-monitor="editingEnergyMonitor"
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

.stat-card:hover {
  border-color: oklch(50% 0 0 / 0.5);
}

/* Responsive stat values */
.stat-value {
  font-weight: 700;
  font-size: clamp(1.25rem, 4vw, 1.875rem);
  line-height: 1.2;
}

.stat-label {
  font-size: clamp(0.7rem, 2vw, 0.875rem);
  color: oklch(80% 0 0 / 0.6);
  margin-top: 0.125rem;
}

.stat-type-count {
  font-weight: 600;
  font-size: clamp(0.875rem, 2.5vw, 1.25rem);
}

/* Ensure text doesn't overflow on small screens */
@media (max-width: 640px) {
  .stat-value {
    font-size: 1.25rem;
  }
  
  .stat-type-count {
    font-size: 0.875rem;
  }
}
</style>
