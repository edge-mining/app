<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import { useExternalServiceStore } from "../../core/stores/externalServiceStore";
import { useMinerStore } from "../../core/stores/minerStore";
import MinerControllerCard from "../../components/minerControllers/MinerControllerCard.vue";
import MinerControllerFormModal from "../../components/minerControllers/MinerControllerFormModal.vue";
import type { MinerController } from "../../core/models/minerController";
import {
  PhPlus,
  PhCircuitry,
  PhGear,
  PhLego,
  PhHardDrive,
  PhPlug,
} from "@phosphor-icons/vue";

const minerControllerStore = useMinerControllerStore();
const externalServiceStore = useExternalServiceStore();
const minerStore = useMinerStore();

// Modal state
const showModal = ref(false);
const editingMinerController = ref<MinerController | undefined>(undefined);
const isEditMode = ref(false);

// Filter state
const selectedAdapterFilter = ref<string>("all");

// Get icon for adapter type
function getAdapterIcon(type: string) {
  const icons: Record<string, typeof PhGear> = {
    dummy: PhLego,
    pyasic: PhHardDrive,
    generic_socket_home_assistant_api: PhPlug,
  };
  return icons[type.toLowerCase()] || PhGear;
}

const adapterFilters = computed(() => {
  const types = minerControllerStore.adapterTypes;
  return [
    { value: "all", label: "All", icon: PhCircuitry },
    ...types.map((type) => ({
      value: type,
      label: formatAdapterType(type),
      icon: getAdapterIcon(type),
    })),
  ];
});

const filteredControllers = computed(() => {
  if (selectedAdapterFilter.value === "all") {
    return minerControllerStore.minerControllers;
  }
  return minerControllerStore.minerControllers.filter(
    (mc) => mc.adapter_type === selectedAdapterFilter.value
  );
});

// Stats
const stats = computed(() => {
  const controllers = minerControllerStore.minerControllers;
  const totalControllers = controllers.length;
  
  // Count controllers with external service linked
  const linkedControllers = controllers.filter(
    (c) => c.external_service_id
  ).length;

  // Count total assigned miners
  const assignedMinersCount = minerStore.miners.filter(
    (m) => m.controller_ids?.length
  ).length;

  // Count by adapter type
  const adapterCounts = controllers.reduce((acc, c) => {
    acc[c.adapter_type] = (acc[c.adapter_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    totalControllers,
    linkedControllers,
    assignedMinersCount,
    adapterCounts,
  };
});

onMounted(() => {
  minerControllerStore.loadMinerControllers();
  minerControllerStore.loadAdapterTypes();
  externalServiceStore.loadExternalServices();
  minerStore.loadMiners();
});

function formatAdapterType(type: string): string {
  return type
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function openAddModal() {
  editingMinerController.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(minerController: MinerController) {
  editingMinerController.value = { ...minerController };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingMinerController.value = undefined;
}

function handleSave(minerController: MinerController) {
  if (isEditMode.value && minerController.id) {
    minerControllerStore
      .updateMinerController(minerController.id.toString(), minerController)
      .then(() => {
        minerControllerStore.loadMinerControllers();
        handleCloseModal();
      })
      .showToasts(
        "Controller updated successfully",
        "Failed to update controller"
      );
  } else {
    minerControllerStore
      .addMinerController(minerController)
      .then(() => {
        minerControllerStore.loadMinerControllers();
        handleCloseModal();
      })
      .showToasts(
        "Controller created successfully",
        "Failed to create controller"
      );
  }
}

function handleDelete(minerController: MinerController) {
  minerControllerStore.deleteMinerController(minerController.id!.toString())
    .then(() => {
      minerControllerStore.loadMinerControllers();
    })
    .showToasts(
      "Controller deleted successfully",
      "Failed to delete controller"
    );
}

function getFilterCount(adapterType: string): number {
  if (adapterType === "all") return stats.value.totalControllers;
  return stats.value.adapterCounts[adapterType] || 0;
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <!-- Header with Stats -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Miner Controllers</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Configure and manage your mining controller adapters
          </p>
        </div>

        <button class="btn btn-primary gap-2" @click="openAddModal">
          <PhPlus :size="20" weight="bold" />
          Add Controller
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">{{ stats.totalControllers }}</div>
            <div class="stat-label">Total Controllers</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-sky-400">{{ stats.assignedMinersCount }}</div>
            <div class="stat-label">Assigned Miners</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-info">{{ stats.linkedControllers }}</div>
            <div class="stat-label">With External Service</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0 overflow-hidden">
            <div class="flex flex-wrap gap-2 sm:gap-3 items-center min-h-[2rem] sm:min-h-[2.25rem]">
              <div
                v-for="(count, adapterType) in stats.adapterCounts"
                :key="adapterType"
                class="flex items-center gap-0.5 sm:gap-1"
              >
                <component :is="getAdapterIcon(String(adapterType))" :size="18" class="text-cyan-400 flex-shrink-0 sm:w-6 sm:h-6" />
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
          <MinerControllerCard
            v-for="controller in filteredControllers"
            :key="controller.id"
            :miner-controller="controller"
            :all-miners="minerStore.miners"
            @edit="handleEdit"
            @delete="handleDelete"
          />

          <!-- Empty State -->
          <div
            v-if="filteredControllers.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhCircuitry :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              {{ selectedAdapterFilter === "all" ? "No controllers yet" : "No controllers of this type" }}
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              {{
                selectedAdapterFilter === "all"
                  ? "Add your first miner controller to start managing your mining hardware."
                  : "Try selecting a different filter or add a new controller."
              }}
            </p>
            <button
              v-if="selectedAdapterFilter === 'all'"
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Controller
            </button>
          </div>
        </div>

        <!-- Form Modal -->
        <MinerControllerFormModal
          :open="showModal"
          :miner-controller="editingMinerController"
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
