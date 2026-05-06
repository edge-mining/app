<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { usePerformanceTrackerStore } from "../../core/stores/performanceTrackerStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { useOptimizationUnitStore } from "../../core/stores/optimizationUnitStore";
import { useAppStore } from "../../core/stores/appStore";
import PerformanceTrackerCard from "../../components/performanceTrackers/PerformanceTrackerCard.vue";
import PerformanceTrackerFormModal from "../../components/performanceTrackers/PerformanceTrackerFormModal.vue";
import type { PerformanceTracker } from "../../core/models/performanceTracker";
import {
  PhPlus,
  PhChartLineUp,
  PhGear,
  PhBracketsCurly,
  PhWaves,
  PhLightning,
} from "@phosphor-icons/vue";

const performanceTrackerStore = usePerformanceTrackerStore();
const externalServiceStore = useExternalServiceStore();
const optimizationUnitStore = useOptimizationUnitStore();
const appStore = useAppStore();

const showModal = ref(false);
const editingTracker = ref<PerformanceTracker | undefined>(undefined);
const isEditMode = ref(false);

const selectedAdapterFilter = ref<string>("all");

function getAdapterIcon(type: string) {
  const icons: Record<string, typeof PhGear> = {
    dummy: PhBracketsCurly,
    ocean: PhWaves,
    braiins_pool: PhLightning,
  };
  return icons[type.toLowerCase()] || PhChartLineUp;
}

const adapterFilters = computed(() => {
  const types = performanceTrackerStore.adapterTypes;
  return [
    { value: "all", label: "All", icon: PhChartLineUp },
    ...types.map((type) => ({
      value: type,
      label: formatAdapterType(type),
      icon: getAdapterIcon(type),
    })),
  ];
});

const filteredTrackers = computed(() => {
  if (selectedAdapterFilter.value === "all") {
    return performanceTrackerStore.performanceTrackers;
  }
  return performanceTrackerStore.performanceTrackers.filter(
    (t) => t.adapter_type === selectedAdapterFilter.value
  );
});

const stats = computed(() => {
  const trackers = performanceTrackerStore.performanceTrackers;
  const totalTrackers = trackers.length;

  const linkedTrackers = trackers.filter((t) => t.external_service_id).length;

  const trackerIdsInUnits = new Set(
    optimizationUnitStore.optimizationUnits
      .map((u) => u.performance_tracker_id)
      .filter(Boolean) as string[]
  );
  const trackersInUse = trackers.filter((t) =>
    t.id ? trackerIdsInUnits.has(t.id) : false
  ).length;

  const adapterCounts = trackers.reduce((acc, t) => {
    acc[t.adapter_type] = (acc[t.adapter_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    totalTrackers,
    linkedTrackers,
    trackersInUse,
    adapterCounts,
  };
});

onMounted(() => {
  performanceTrackerStore.loadPerformanceTrackers();
  performanceTrackerStore.loadAdapterTypes();
  externalServiceStore.loadExternalServices();
  optimizationUnitStore.loadOptimizationUnits();
});

function formatAdapterType(type: string): string {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function openAddModal() {
  editingTracker.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(tracker: PerformanceTracker) {
  editingTracker.value = { ...tracker };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingTracker.value = undefined;
}

function handleSave(tracker: PerformanceTracker) {
  if (isEditMode.value && tracker.id) {
    performanceTrackerStore
      .updatePerformanceTracker(tracker.id.toString(), tracker)
      .then(() => {
        performanceTrackerStore.loadPerformanceTrackers();
        handleCloseModal();
      })
      .showToasts(
        "Performance tracker updated successfully",
        "Failed to update performance tracker"
      );
  } else {
    performanceTrackerStore
      .addPerformanceTracker(tracker)
      .then(() => {
        performanceTrackerStore.loadPerformanceTrackers();
        handleCloseModal();
      })
      .showToasts(
        "Performance tracker created successfully",
        "Failed to create performance tracker"
      );
  }
}

function handleDelete(tracker: PerformanceTracker) {
  performanceTrackerStore
    .deletePerformanceTracker(tracker.id!.toString())
    .then(() => {
      performanceTrackerStore.loadPerformanceTrackers();
      optimizationUnitStore.loadOptimizationUnits();
    })
    .showToasts(
      "Performance tracker deleted successfully",
      "Failed to delete performance tracker"
    );
}

function handleTest(tracker: PerformanceTracker) {
  if (!tracker.id) return;
  performanceTrackerStore
    .testPerformanceTracker(tracker.id.toString())
    .then((result) => {
      appStore.showSuccessToast(
        result?.message || "Performance tracker is reachable"
      );
    })
    .catch((err) => {
      const detail = err?.response?.data?.detail || err?.message || "Failed to test performance tracker";
      appStore.showErrorToast(detail);
    });
}

function getFilterCount(adapterType: string): number {
  if (adapterType === "all") return stats.value.totalTrackers;
  return stats.value.adapterCounts[adapterType] || 0;
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Performance Trackers</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Configure mining pool performance trackers for hashrate and rewards monitoring
          </p>
        </div>

        <button class="btn btn-primary gap-2" @click="openAddModal">
          <PhPlus :size="20" weight="bold" />
          Add Tracker
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">{{ stats.totalTrackers }}</div>
            <div class="stat-label">Total Trackers</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-teal-400">{{ stats.trackersInUse }}</div>
            <div class="stat-label">In Use</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-info">{{ stats.linkedTrackers }}</div>
            <div class="stat-label">With External Service</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0 overflow-hidden">
            <div class="flex flex-wrap gap-2 sm:gap-3 items-center min-h-[2rem] sm:min-h-[2.25rem]">
              <div
                v-for="(count, adapterType) in stats.adapterCounts"
                :key="adapterType"
                class="flex items-center gap-0.5 sm:gap-1"
              >
                <component
                  :is="getAdapterIcon(String(adapterType))"
                  :size="18"
                  class="text-cyan-400 flex-shrink-0 sm:w-6 sm:h-6"
                />
                <span class="stat-type-count">{{ count }}</span>
              </div>
              <div
                v-if="Object.keys(stats.adapterCounts).length === 0"
                class="text-base-content/40"
              >
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
              :class="
                selectedAdapterFilter === filter.value
                  ? 'bg-white/20 text-neutral-900'
                  : 'badge-neutral'
              "
            >
              {{ getFilterCount(filter.value) }}
            </span>
          </button>
        </div>

        <!-- Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <PerformanceTrackerCard
            v-for="tracker in filteredTrackers"
            :key="tracker.id"
            :tracker="tracker"
            :all-optimization-units="optimizationUnitStore.optimizationUnits"
            @edit="handleEdit"
            @delete="handleDelete"
            @test="handleTest"
          />

          <!-- Empty state -->
          <div
            v-if="filteredTrackers.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhChartLineUp :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              {{
                selectedAdapterFilter === "all"
                  ? "No performance trackers yet"
                  : "No trackers of this type"
              }}
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              {{
                selectedAdapterFilter === "all"
                  ? "Add your first performance tracker to monitor hashrate and rewards from your mining pool."
                  : "Try selecting a different filter or add a new tracker."
              }}
            </p>
            <button
              v-if="selectedAdapterFilter === 'all'"
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Tracker
            </button>
          </div>
        </div>

        <!-- Form Modal -->
        <PerformanceTrackerFormModal
          :open="showModal"
          :performance-tracker="editingTracker"
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

.stat-type-count {
  font-weight: 600;
  font-size: clamp(0.875rem, 2.5vw, 1.25rem);
}

@media (max-width: 640px) {
  .stat-value {
    font-size: 1.25rem;
  }

  .stat-type-count {
    font-size: 0.875rem;
  }
}
</style>
