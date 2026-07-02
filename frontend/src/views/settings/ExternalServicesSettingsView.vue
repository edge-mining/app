<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import ExternalServiceCard from "../../components/externalServices/ExternalServiceCard.vue";
import ExternalServiceFormModal from "../../components/externalServices/ExternalServiceFormModal.vue";
import type { ExternalService } from "../../core/models/externalService";
import {
  PhPlus,
  PhPlugs,
  PhHouse,
  PhWifiHigh,
  PhCloud,
  PhCheckCircle,
  PhXCircle,
  PhWarningCircle,
} from "@phosphor-icons/vue";

const externalServiceStore = useExternalServiceStore();
const route = useRoute();

// Modal state
const showModal = ref(false);
const editingExternalService = ref<ExternalService | undefined>(undefined);
const isEditMode = ref(false);

// Filter state
const selectedAdapterFilter = ref<string>("all");

const adapterFilters = computed(() => {
  const types = externalServiceStore.adapterTypes;
  return [
    { value: "all", label: "All", icon: PhPlugs, iconColor: "" },
    ...types.map((type) => ({
      value: type,
      label: formatAdapterType(type),
      icon: getAdapterIcon(type),
      iconColor: getAdapterIconColor(type),
    })),
  ];
});

const filteredServices = computed(() => {
  if (selectedAdapterFilter.value === "all") {
    return externalServiceStore.externalServices;
  }
  return externalServiceStore.externalServices.filter(
    (es) => es.adapter_type === selectedAdapterFilter.value
  );
});

// Stats
const stats = computed(() => {
  const services = externalServiceStore.externalServices;
  const totalServices = services.length;

  // Status counts from store
  let connectedCount = 0;
  let disconnectedCount = 0;
  let unauthorizedCount = 0;
  services.forEach((s) => {
    const st = s.id ? externalServiceStore.serviceStatuses.get(s.id) : undefined;
    if (st?.status === "connected") connectedCount++;
    else if (st?.status === "disconnected") disconnectedCount++;
    else if (st?.status === "unauthorized") unauthorizedCount++;
  });

  // Count by adapter type
  const adapterCounts = services.reduce((acc, s) => {
    acc[s.adapter_type] = (acc[s.adapter_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    totalServices,
    connectedCount,
    disconnectedCount,
    unauthorizedCount,
    adapterCounts,
  };
});

onMounted(() => {
  const adapterQuery = route.query.adapter;
  if (typeof adapterQuery === "string" && adapterQuery) {
    selectedAdapterFilter.value = adapterQuery;
  }

  externalServiceStore.loadExternalServices().then(() => {
    externalServiceStore.loadServicesStatus();
  });
  externalServiceStore.loadAdapterTypes();
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
    home_assistant_mqtt: PhWifiHigh,
    solcast_api: PhCloud,
  };
  return icons[type] || PhPlugs;
}

function getAdapterIconColor(type: string): string {
  const colors: Record<string, string> = {
    home_assistant_api: "text-sky-400",
    home_assistant_mqtt: "text-purple-400",
    solcast_api: "text-amber-400",
  };
  return colors[type] || "text-teal-400";
}

function openAddModal() {
  editingExternalService.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(externalService: ExternalService) {
  editingExternalService.value = {
    ...externalService,
    config: externalService.config ? { ...externalService.config } : {},
  };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingExternalService.value = undefined;
}

function handleSave(externalService: ExternalService) {
  if (isEditMode.value && externalService.id) {
    externalServiceStore
      .updateExternalService(externalService.id.toString(), externalService)
      .then(() => {
        externalServiceStore.loadExternalServices().then(() => {
          externalServiceStore.loadServicesStatus();
        });
        handleCloseModal();
      })
      .showToasts(
        "External service updated successfully",
        "Failed to update external service"
      );
  } else {
    externalServiceStore.addExternalService(externalService)
      .then(() => {
        externalServiceStore.loadExternalServices().then(() => {
          externalServiceStore.loadServicesStatus();
        });
        handleCloseModal();
      })
      .showToasts(
        "External service created successfully",
        "Failed to create external service"
      );
  }
}

function handleDelete(externalService: ExternalService) {
  externalServiceStore
    .deleteExternalService(externalService.id!.toString())
    .then(() => {
      externalServiceStore.loadExternalServices();
    })
    .showToasts(
      "External service deleted successfully",
      "Failed to delete external service"
    );
}

function getFilterCount(adapterType: string): number {
  if (adapterType === "all") return stats.value.totalServices;
  return stats.value.adapterCounts[adapterType] || 0;
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <!-- Header -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-base-content">External Services</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Manage connections to third-party services and APIs
          </p>
        </div>

        <button class="btn btn-primary gap-2" @click="openAddModal">
          <PhPlus :size="20" weight="bold" />
          Add Service
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">{{ stats.totalServices }}</div>
            <div class="stat-label">Total Services</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-emerald-400 flex items-center gap-2">
              {{ stats.connectedCount }}
              <PhCheckCircle :size="20" class="opacity-60" />
            </div>
            <div class="stat-label">Connected</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value flex items-center gap-2">
              <span v-if="stats.disconnectedCount > 0" class="text-red-400">{{ stats.disconnectedCount }}</span>
              <span v-else class="text-base-content/30">0</span>
              <PhXCircle v-if="stats.disconnectedCount > 0" :size="20" class="text-red-400 opacity-60" />
              <span v-if="stats.unauthorizedCount > 0" class="text-amber-400 ml-2">{{ stats.unauthorizedCount }}</span>
              <PhWarningCircle v-if="stats.unauthorizedCount > 0" :size="20" class="text-amber-400 opacity-60" />
            </div>
            <div class="stat-label">Issues</div>
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
          <ExternalServiceCard
            v-for="service in filteredServices"
            :key="service.id"
            :external-service="service"
            @edit="handleEdit"
            @delete="handleDelete"
          />

          <!-- Empty State -->
          <div
            v-if="filteredServices.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhPlugs :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              {{ selectedAdapterFilter === "all" ? "No services yet" : "No services of this type" }}
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              {{
                selectedAdapterFilter === "all"
                  ? "Add your first external service to connect with third-party APIs."
                  : "Try selecting a different filter or add a new service."
              }}
            </p>
            <button
              v-if="selectedAdapterFilter === 'all'"
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Service
            </button>
          </div>
        </div>

        <!-- Form Modal -->
        <ExternalServiceFormModal
          :open="showModal"
          :external-service="editingExternalService"
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
