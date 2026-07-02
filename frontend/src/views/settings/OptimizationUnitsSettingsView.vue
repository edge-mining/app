<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useOptimizationUnitStore } from "../../core/stores/optimizationUnitStore";
import { usePolicyStore } from "../../core/stores/policyStore";
import { useMinerStore } from "../../core/stores/minerStore";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import { useNotifierStore } from "../../core/stores/notifierStore";
import { usePerformanceTrackerStore } from "../../core/stores/performanceTrackerStore";
import { useClimateZoneStore } from "../../core/stores/climateZoneStore";
import OptimizationUnitCard from "../../components/optimizationUnits/OptimizationUnitCard.vue";
import OptimizationUnitFormModal from "../../components/optimizationUnits/OptimizationUnitFormModal.vue";
import type { OptimizationUnit } from "../../core/models/optimizationUnit";
import type { OptimizationUnitCreate } from "../../core/models/optimizationUnit";
import {
  PhPlus,
  PhGear,
  PhPower,
} from "@phosphor-icons/vue";

const optimizationUnitStore = useOptimizationUnitStore();
const policyStore = usePolicyStore();
const minerStore = useMinerStore();
const energySourceStore = useEnergySourceStore();
const forecastProviderStore = useForecastProviderStore();
const notifierStore = useNotifierStore();
const performanceTrackerStore = usePerformanceTrackerStore();
const climateZoneStore = useClimateZoneStore();

// Modal state
const showModal = ref(false);
const editingUnit = ref<OptimizationUnit | undefined>(undefined);
const isEditMode = ref(false);

// Filter state
const selectedFilter = ref<"all" | "enabled" | "disabled">("all");

const filterTabs = [
  { value: "all" as const, label: "All", icon: PhGear },
  { value: "enabled" as const, label: "Enabled", icon: PhPower },
  { value: "disabled" as const, label: "Disabled", icon: PhPower },
];

const filteredUnits = computed(() => {
  if (selectedFilter.value === "enabled") {
    return optimizationUnitStore.optimizationUnits.filter((u) => u.is_enabled);
  }
  if (selectedFilter.value === "disabled") {
    return optimizationUnitStore.optimizationUnits.filter((u) => !u.is_enabled);
  }
  return optimizationUnitStore.optimizationUnits;
});

// Stats
const stats = computed(() => {
  const units = optimizationUnitStore.optimizationUnits;
  const totalUnits = units.length;
  const enabledUnits = units.filter((u) => u.is_enabled).length;
  const withPolicy = units.filter((u) => u.policy_id).length;
  const uniqueMinerIds = new Set(units.flatMap((u) => u.target_miner_ids));
  const totalMiners = uniqueMinerIds.size;

  return { totalUnits, enabledUnits, withPolicy, totalMiners };
});

onMounted(() => {
  optimizationUnitStore.loadOptimizationUnits();
  policyStore.loadPolicies();
  minerStore.loadMiners();
  energySourceStore.loadEnergySources();
  forecastProviderStore.loadForecastProviders();
  notifierStore.loadNotifiers();
  performanceTrackerStore.loadPerformanceTrackers();
  climateZoneStore.loadClimateZones();
});

function openAddModal() {
  editingUnit.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(unit: OptimizationUnit) {
  editingUnit.value = { ...unit };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingUnit.value = undefined;
}

function handleSave(data: OptimizationUnitCreate) {
  if (isEditMode.value && editingUnit.value?.id) {
    optimizationUnitStore
      .updateOptimizationUnit(editingUnit.value.id, data)
      .then(() => {
        optimizationUnitStore.loadOptimizationUnits();
        handleCloseModal();
      })
      .showToasts(
        "Optimization unit updated successfully",
        "Failed to update optimization unit"
      );
  } else {
    optimizationUnitStore
      .addOptimizationUnit(data)
      .then(() => {
        optimizationUnitStore.loadOptimizationUnits();
        handleCloseModal();
      })
      .showToasts(
        "Optimization unit created successfully",
        "Failed to create optimization unit"
      );
  }
}

function handleDelete(unit: OptimizationUnit) {
  optimizationUnitStore
    .deleteOptimizationUnit(unit.id!)
    .then(() => {
      optimizationUnitStore.loadOptimizationUnits();
    })
    .showToasts(
      "Optimization unit deleted successfully",
      "Failed to delete optimization unit"
    );
}

function handleToggleEnabled(unit: OptimizationUnit) {
  const action = unit.is_enabled
    ? optimizationUnitStore.disableOptimizationUnit(unit.id!)
    : optimizationUnitStore.enableOptimizationUnit(unit.id!);

  const verb = unit.is_enabled ? "disabled" : "enabled";
  action
    .then(() => {
      optimizationUnitStore.loadOptimizationUnits();
    })
    .showToasts(
      `Optimization unit ${verb} successfully`,
      `Failed to ${verb.replace("d", "")} optimization unit`
    );
}

function getFilterCount(filter: string): number {
  if (filter === "all") return stats.value.totalUnits;
  if (filter === "enabled") return stats.value.enabledUnits;
  return stats.value.totalUnits - stats.value.enabledUnits;
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <!-- Header -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Optimization Units</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Configure units that orchestrate miners, energy sources, and policies
          </p>
        </div>

        <button class="btn btn-primary gap-2" @click="openAddModal">
          <PhPlus :size="20" weight="bold" />
          Add Unit
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">{{ stats.totalUnits }}</div>
            <div class="stat-label">Total Units</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-teal-400">
              {{ stats.enabledUnits }} / {{ stats.totalUnits }}
            </div>
            <div class="stat-label">Enabled</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-info">{{ stats.withPolicy }}</div>
            <div class="stat-label">With Policy</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-amber-400">{{ stats.totalMiners }}</div>
            <div class="stat-label">Assigned Miners</div>
          </div>
        </div>

        <!-- Filter Tabs -->
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="filter in filterTabs"
            :key="filter.value"
            class="btn btn-sm gap-2 transition-all"
            :class="[
              selectedFilter === filter.value
                ? 'btn-primary'
                : 'btn-ghost opacity-70 hover:opacity-100',
            ]"
            @click="selectedFilter = filter.value"
          >
            <component :is="filter.icon" :size="16" />
            {{ filter.label }}
            <span
              v-if="getFilterCount(filter.value) > 0"
              class="badge badge-sm"
              :class="selectedFilter === filter.value ? 'bg-white/20 text-neutral-900' : 'badge-neutral'"
            >
              {{ getFilterCount(filter.value) }}
            </span>
          </button>
        </div>

        <!-- Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <OptimizationUnitCard
            v-for="unit in filteredUnits"
            :key="unit.id"
            :unit="unit"
            @edit="handleEdit"
            @delete="handleDelete"
            @toggle-enabled="handleToggleEnabled"
          />

          <!-- Empty State -->
          <div
            v-if="filteredUnits.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4">
              <PhGear :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              {{ selectedFilter === "all" ? "No optimization units yet" : "No units with this status" }}
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              {{
                selectedFilter === "all"
                  ? "Create your first optimization unit to coordinate miners, energy sources, and policies."
                  : "Try selecting a different filter or add a new optimization unit."
              }}
            </p>
            <button
              v-if="selectedFilter === 'all'"
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Unit
            </button>
          </div>
        </div>

        <!-- Form Modal -->
        <OptimizationUnitFormModal
          :open="showModal"
          :unit="editingUnit"
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

@media (max-width: 640px) {
  .stat-value {
    font-size: 1.25rem;
  }
}
</style>
