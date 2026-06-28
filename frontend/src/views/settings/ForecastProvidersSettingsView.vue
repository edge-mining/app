<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useForecastProviderStore } from "../../core/stores/forecastProviderStore";
import { useEnergySourceStore } from "../../core/stores/energySourceStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import ForecastProviderCard from "../../components/forecastProviders/ForecastProviderCard.vue";
import ForecastProviderFormModal from "../../components/forecastProviders/ForecastProviderFormModal.vue";
import type { ForecastProvider } from "../../core/models/forecastProvider";
import {
  PhPlus,
  PhChartLine,
  PhSun,
  PhCloudSun,
} from "@phosphor-icons/vue";

const forecastProviderStore = useForecastProviderStore();
const energySourceStore = useEnergySourceStore();
const externalServiceStore = useExternalServiceStore();

// Modal state
const showModal = ref(false);
const editingForecastProvider = ref<ForecastProvider | undefined>(undefined);
const isEditMode = ref(false);

// Filter state
const selectedAdapterFilter = ref<string>("all");

const adapterFilters = computed(() => {
  const types = forecastProviderStore.adapterTypes;
  return [
    { value: "all", label: "All", icon: PhChartLine, iconColor: "" },
    ...types.map((type) => ({
      value: type,
      label: formatAdapterType(type),
      icon: getAdapterIcon(type),
      iconColor: getAdapterIconColor(type),
    })),
  ];
});

const filteredProviders = computed(() => {
  if (selectedAdapterFilter.value === "all") {
    return forecastProviderStore.forecastProviders;
  }
  return forecastProviderStore.forecastProviders.filter(
    (fp) => fp.adapter_type === selectedAdapterFilter.value
  );
});

// Stats
const stats = computed(() => {
  const providers = forecastProviderStore.forecastProviders;
  const totalProviders = providers.length;

  // Count providers with external service linked
  const linkedProviders = providers.filter(
    (p) => p.external_service_id
  ).length;

  // Count total assigned energy sources
  const assignedSourcesCount = energySourceStore.energySources.filter(
    (es) => es.forecast_provider_id
  ).length;

  // Count by adapter type
  const adapterCounts = providers.reduce((acc, p) => {
    acc[p.adapter_type] = (acc[p.adapter_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    totalProviders,
    linkedProviders,
    assignedSourcesCount,
    adapterCounts,
  };
});

onMounted(() => {
  forecastProviderStore.loadForecastProviders();
  forecastProviderStore.loadAdapterTypes();
  energySourceStore.loadEnergySources();
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
    solcast_api: PhSun,
    open_meteo_api: PhCloudSun,
    dummy_solar: PhSun,
  };
  return icons[type] || PhChartLine;
}

function getAdapterIconColor(type: string): string {
  const colors: Record<string, string> = {
    solcast_api: "text-amber-400",
    open_meteo_api: "text-sky-400",
    dummy_solar: "text-yellow-400",
  };
  return colors[type] || "text-indigo-400";
}

function openAddModal() {
  editingForecastProvider.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(forecastProvider: ForecastProvider) {
  editingForecastProvider.value = { ...forecastProvider };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingForecastProvider.value = undefined;
}

function handleSave(forecastProvider: ForecastProvider) {
  if (isEditMode.value && forecastProvider.id) {
    forecastProviderStore
      .updateForecastProvider(forecastProvider.id.toString(), forecastProvider)
      .then(() => {
        forecastProviderStore.loadForecastProviders();
        handleCloseModal();
      })
      .showToasts(
        "Forecast provider updated successfully",
        "Failed to update forecast provider"
      );
  } else {
    forecastProviderStore.addForecastProvider(forecastProvider)
      .then(() => {
        forecastProviderStore.loadForecastProviders();
        handleCloseModal();
      })
      .showToasts(
        "Forecast provider created successfully",
        "Failed to create forecast provider"
      );
  }
}

function handleDelete(forecastProvider: ForecastProvider) {
  forecastProviderStore
    .deleteForecastProvider(forecastProvider.id!.toString())
    .then(() => {
      forecastProviderStore.loadForecastProviders();
    })
    .showToasts(
      "Forecast provider deleted successfully",
      "Failed to delete forecast provider"
    );
}

function getFilterCount(adapterType: string): number {
  if (adapterType === "all") return stats.value.totalProviders;
  return stats.value.adapterCounts[adapterType] || 0;
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <!-- Header with Stats -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Forecast Providers</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Configure adapters for forecasting your energy production
          </p>
        </div>

        <button class="btn btn-primary gap-2" @click="openAddModal">
          <PhPlus :size="20" weight="bold" />
          Add Provider
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">{{ stats.totalProviders }}</div>
            <div class="stat-label">Total Providers</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-teal-400">{{ stats.assignedSourcesCount }}</div>
            <div class="stat-label">Forecasted Sources</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-info">{{ stats.linkedProviders }}</div>
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
          <ForecastProviderCard
            v-for="provider in filteredProviders"
            :key="provider.id"
            :forecast-provider="provider"
            :all-energy-sources="energySourceStore.energySources"
            @edit="handleEdit"
            @delete="handleDelete"
          />

          <!-- Empty State -->
          <div
            v-if="filteredProviders.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhChartLine :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              {{ selectedAdapterFilter === "all" ? "No providers yet" : "No providers of this type" }}
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              {{
                selectedAdapterFilter === "all"
                  ? "Add your first forecast provider to start predicting energy production."
                  : "Try selecting a different filter or add a new provider."
              }}
            </p>
            <button
              v-if="selectedAdapterFilter === 'all'"
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Provider
            </button>
          </div>
        </div>

        <!-- Form Modal -->
        <ForecastProviderFormModal
          :open="showModal"
          :forecast-provider="editingForecastProvider"
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
