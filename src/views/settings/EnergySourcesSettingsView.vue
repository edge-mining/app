<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import { useEnergyMonitorStore } from "../../core/stores/energyMonitorStore";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import EnergySourceCard from "../../components/energySources/EnergySourceCard.vue";
import EnergySourceFormModal from "../../components/energySources/EnergySourceFormModal.vue";
import type { EnergySource } from "../../core/models/energySource";
import { EnergySourceType } from "../../core/models/energySource";
import { PhPlus, PhSun, PhWind, PhPlug, PhDrop, PhLightning } from "@phosphor-icons/vue";

const energySourceStore = useEnergySourceStore();
const energyMonitorStore = useEnergyMonitorStore();
const forecastProviderStore = useForecastProviderStore();

// Modal state
const showModal = ref(false);
const editingEnergySource = ref<EnergySource | undefined>(undefined);
const isEditMode = ref(false);

// Filter state
const selectedTypeFilter = ref<EnergySourceType | "all">("all");

const typeFilters = [
  { value: "all" as const, label: "All", icon: PhLightning },
  { value: EnergySourceType.SOLAR, label: "Solar", icon: PhSun },
  { value: EnergySourceType.WIND, label: "Wind", icon: PhWind },
  { value: EnergySourceType.GRID, label: "Grid", icon: PhPlug },
  { value: EnergySourceType.HYDROELECTRIC, label: "Hydro", icon: PhDrop },
  { value: EnergySourceType.OTHER, label: "Other", icon: PhLightning },
];

const filteredEnergySources = computed(() => {
  if (selectedTypeFilter.value === "all") {
    return energySourceStore.energySources;
  }
  return energySourceStore.energySources.filter(
    (es) => es.type === selectedTypeFilter.value
  );
});

// Stats
const stats = computed(() => {
  const sources = energySourceStore.energySources;
  const totalPower = sources.reduce(
    (sum, es) => sum + (es.nominal_power_max || 0),
    0
  );
  const totalStorage = sources.reduce(
    (sum, es) => sum + (es.storage?.nominal_capacity || 0),
    0
  );
  const typeCounts = sources.reduce((acc, es) => {
    acc[es.type] = (acc[es.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return { totalSources: sources.length, totalPower, totalStorage, typeCounts };
});

onMounted(() => {
  energySourceStore.loadEnergySources();
  energyMonitorStore.loadEnergyMonitors();
  forecastProviderStore.loadForecastProviders();
});

function cleanEnergySource(energySource: EnergySource): EnergySource {
  const cleaned = { ...energySource };
  if (cleaned.energy_monitor_id === "") {
    delete cleaned.energy_monitor_id;
  }
  if (cleaned.forecast_provider_id === "") {
    delete cleaned.forecast_provider_id;
  }
  // Clean up empty/zero values
  if (!cleaned.nominal_power_max) {
    delete cleaned.nominal_power_max;
  }
  if (!cleaned.external_source) {
    delete cleaned.external_source;
  }
  if (cleaned.storage && !cleaned.storage.nominal_capacity) {
    delete cleaned.storage;
  }
  if (cleaned.grid && !cleaned.grid.contracted_power) {
    delete cleaned.grid;
  }
  return cleaned;
}

function openAddModal() {
  editingEnergySource.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(energySource: EnergySource) {
  editingEnergySource.value = { ...energySource };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingEnergySource.value = undefined;
}

function handleSave(energySource: EnergySource) {
  const cleaned = cleanEnergySource(energySource);

  if (isEditMode.value && energySource.id) {
    energySourceStore
      .updateEnergySource(energySource.id.toString(), cleaned)
      .then(() => {
        energySourceStore.loadEnergySources();
        handleCloseModal();
      });
  } else {
    energySourceStore.addEnergySource(cleaned).then(() => {
      energySourceStore.loadEnergySources();
      handleCloseModal();
    });
  }
}

function handleDelete(energySource: EnergySource) {
  energySourceStore.deleteEnergySource(energySource.id!.toString())
    .then(() => {
      energySourceStore.loadEnergySources();
    })
    .showToasts(
      "Energy source deleted successfully",
      "Failed to delete energy source"
    );
}

function formatPower(watts: number): string {
  if (watts >= 1000000) return `${(watts / 1000000).toFixed(1)} MW`;
  if (watts >= 1000) return `${(watts / 1000).toFixed(1)} kW`;
  return `${watts} W`;
}

function formatCapacity(wh: number): string {
  if (wh >= 1000000) return `${(wh / 1000000).toFixed(1)} MWh`;
  if (wh >= 1000) return `${(wh / 1000).toFixed(1)} kWh`;
  return `${wh} Wh`;
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <!-- Header with Stats -->
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 class="text-2xl font-bold text-base-content">Energy Sources</h1>
            <p class="text-sm text-base-content/60 mt-1">
              Manage your energy generation and storage sources
            </p>
          </div>

          <button class="btn btn-primary gap-2" @click="openAddModal">
            <PhPlus :size="20" weight="bold" />
            Add Source
          </button>
        </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards  -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">{{ stats.totalSources }}</div>
            <div class="stat-label">Total Sources</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-warning truncate">
              {{ stats.totalPower > 0 ? formatPower(stats.totalPower) : "-" }}
            </div>
            <div class="stat-label">Total Capacity</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-success truncate">
              {{ stats.totalStorage > 0 ? formatCapacity(stats.totalStorage) : "-" }}
            </div>
            <div class="stat-label">Storage Capacity</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0 overflow-hidden">
            <div class="flex flex-wrap gap-2 sm:gap-3 items-center min-h-[2rem] sm:min-h-[2.25rem]">
              <div v-if="stats.typeCounts[EnergySourceType.SOLAR]" class="flex items-center gap-0.5 sm:gap-1">
                <PhSun :size="18" class="text-amber-400 flex-shrink-0 sm:w-6 sm:h-6" />
                <span class="stat-type-count">{{ stats.typeCounts[EnergySourceType.SOLAR] }}</span>
              </div>
              <div v-if="stats.typeCounts[EnergySourceType.WIND]" class="flex items-center gap-0.5 sm:gap-1">
                <PhWind :size="18" class="text-sky-400 flex-shrink-0 sm:w-6 sm:h-6" />
                <span class="stat-type-count">{{ stats.typeCounts[EnergySourceType.WIND] }}</span>
              </div>
              <div v-if="stats.typeCounts[EnergySourceType.GRID]" class="flex items-center gap-0.5 sm:gap-1">
                <PhPlug :size="18" class="text-slate-300 flex-shrink-0 sm:w-6 sm:h-6" />
                <span class="stat-type-count">{{ stats.typeCounts[EnergySourceType.GRID] }}</span>
              </div>
              <div v-if="stats.typeCounts[EnergySourceType.HYDROELECTRIC]" class="flex items-center gap-0.5 sm:gap-1">
                <PhDrop :size="18" class="text-blue-400 flex-shrink-0 sm:w-6 sm:h-6" />
                <span class="stat-type-count">{{ stats.typeCounts[EnergySourceType.HYDROELECTRIC] }}</span>
              </div>
              <div v-if="stats.typeCounts[EnergySourceType.OTHER]" class="flex items-center gap-0.5 sm:gap-1">
                <PhLightning :size="18" class="text-purple-400 flex-shrink-0 sm:w-6 sm:h-6" />
                <span class="stat-type-count">{{ stats.typeCounts[EnergySourceType.OTHER] }}</span>
              </div>
            </div>
            <div class="stat-label">By Type</div>
          </div>
        </div>

        <!-- Filter Tabs -->
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="filter in typeFilters"
            :key="filter.value"
            class="btn btn-sm gap-2 transition-all"
            :class="[
              selectedTypeFilter === filter.value
                ? 'btn-primary'
                : 'btn-ghost opacity-70 hover:opacity-100',
            ]"
            @click="selectedTypeFilter = filter.value"
          >
            <component :is="filter.icon" :size="16" />
            {{ filter.label }}
            <span
              v-if="
                filter.value === 'all'
                  ? stats.totalSources > 0
                  : stats.typeCounts[filter.value]
              "
              class="badge badge-sm"
              :class="selectedTypeFilter === filter.value ? 'bg-white/20 text-neutral-900' : 'badge-neutral'"
            >
              {{
                filter.value === "all"
                  ? stats.totalSources
                  : stats.typeCounts[filter.value] || 0
              }}
            </span>
          </button>
        </div>

        <!-- Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <EnergySourceCard
            v-for="energySource in filteredEnergySources"
            :key="energySource.id"
            :energy-source="energySource"
            @edit="handleEdit"
            @delete="handleDelete"
          />

          <!-- Empty State -->
          <div
            v-if="filteredEnergySources.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhLightning :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              {{ selectedTypeFilter === "all" ? "No energy sources yet" : "No sources of this type" }}
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              {{
                selectedTypeFilter === "all"
                  ? "Add your first energy source to start monitoring and optimizing your energy usage."
                  : "Try selecting a different filter or add a new source."
              }}
            </p>
            <button
              v-if="selectedTypeFilter === 'all'"
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Energy Source
            </button>
          </div>
        </div>

        <!-- Form Modal -->
        <EnergySourceFormModal
          :open="showModal"
          :energy-source="editingEnergySource"
          :all-energy-sources="energySourceStore.energySources"
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
