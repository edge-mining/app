<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useMinerStore } from "../../core/stores/minerStore";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import MinerCard from "../../components/miners/MinerCard.vue";
import MinerFormModal from "../../components/miners/MinerFormModal.vue";
import type { Miner, MinerFeature, MinerStatus } from "../../core/models/miner";
import {
  PhPlus,
  PhPower,
  PhCpu,
  PhCircleNotch,
  PhWarningCircle,
  PhQuestion,
} from "@phosphor-icons/vue";
import { formatPower, normalizeHashRate } from "../../core/utils/index";

const minerStore = useMinerStore();
const minerControllerStore = useMinerControllerStore();

// Modal state
const showModal = ref(false);
const editingMiner = ref<Miner | undefined>(undefined);
const isEditMode = ref(false);

// Filter state
const selectedStatusFilter = ref<MinerStatus | "all" | "active">("all");

const statusFilters = [
  { value: "all" as const, label: "All", icon: PhCpu },
  { value: "active" as const, label: "Active", icon: PhPower },
  { value: "on" as MinerStatus, label: "Running", icon: PhPower },
  { value: "off" as MinerStatus, label: "Off", icon: PhPower },
  { value: "starting" as MinerStatus, label: "Starting", icon: PhCircleNotch },
  { value: "stopping" as MinerStatus, label: "Stopping", icon: PhCircleNotch },
  { value: "error" as MinerStatus, label: "Error", icon: PhWarningCircle },
  { value: "unknown" as MinerStatus, label: "Unknown", icon: PhQuestion },
];

let statusInterval: number | undefined;

// Helper to get miner status from the state map
function getMinerStatus(miner: Miner): MinerStatus {
  if (!miner.id) return "unknown";
  return minerStore.minerStates.get(miner.id)?.status ?? "unknown";
}

// Computed
const filteredMiners = computed(() => {
  if (selectedStatusFilter.value === "all") {
    return minerStore.miners;
  }
  if (selectedStatusFilter.value === "active") {
    return minerStore.miners.filter((m) => m.active);
  }
  return minerStore.miners.filter((m) => getMinerStatus(m) === selectedStatusFilter.value);
});

const stats = computed(() => {
  const miners = minerStore.miners;
  const totalMiners = miners.length;
  const activeMiners = miners.filter((m) => m.active).length;
  const runningMiners = miners.filter((m) => getMinerStatus(m) === "on").length;

  // Calculate current total hash rate (only from running miners)
  const runningMinersData = miners.filter((m) => getMinerStatus(m) === "on");
  let totalHashRate = 0;
  let hashRateUnit = "TH/s";

  runningMinersData.forEach((m) => {
    const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
    if (state?.hash_rate?.value) {
      // Normalize to TH/s for aggregation
      const normalized = normalizeHashRate(state.hash_rate.value, state.hash_rate.unit || "TH/s");
      totalHashRate += normalized;
    }
  });

  // Calculate total power consumption
  const totalPowerConsumption = runningMinersData.reduce(
    (sum, m) => {
      const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
      return sum + (state?.power_consumption || 0);
    },
    0
  );

  // Status counts
  const statusCounts = miners.reduce((acc, m) => {
    const status = getMinerStatus(m);
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    totalMiners,
    activeMiners,
    runningMiners,
    totalHashRate,
    hashRateUnit,
    totalPowerConsumption,
    statusCounts,
  };
});

async function refreshMinersStatus() {
  const activeMiners = minerStore.miners.filter(
    (miner) => miner.id != null && miner.active
  );
  if (activeMiners.length > 0) {
    const statusPromises = activeMiners.map((miner) =>
      minerStore.getMinerStatus(miner.id!.toString())
    );
    await Promise.all(statusPromises);
  }
}

onMounted(async () => {
  await minerStore.loadMiners();
  minerControllerStore.loadMinerControllers();
  await refreshMinersStatus();

  statusInterval = window.setInterval(() => {
    refreshMinersStatus();
  }, 2000);
});

onUnmounted(() => {
  if (statusInterval !== undefined) {
    clearInterval(statusInterval);
  }
});

function openAddModal() {
  editingMiner.value = undefined;
  isEditMode.value = false;
  showModal.value = true;
}

function handleEdit(miner: Miner) {
  editingMiner.value = { ...miner };
  isEditMode.value = true;
  showModal.value = true;
}

function handleCloseModal() {
  showModal.value = false;
  editingMiner.value = undefined;
}

async function applyControllerChanges(minerId: string, changes: { add: string[]; remove: string[] }) {
  const promises: Promise<any>[] = [];
  for (const controllerId of changes.add) {
    promises.push(minerStore.setMinerController(minerId, controllerId));
  }
  for (const controllerId of changes.remove) {
    promises.push(minerStore.unlinkMinerController(minerId, controllerId));
  }
  if (promises.length > 0) {
    await Promise.all(promises);
  }
}

async function applyFeatureChanges(minerId: string, features: MinerFeature[], originalMiner?: Miner) {
  const originalFeatures = originalMiner?.features ?? [];
  const promises: Promise<any>[] = [];
  for (const feature of features) {
    const original = originalFeatures.find(
      (f) => f.feature_type === feature.feature_type && f.controller_id === feature.controller_id
    );
    if (!original) continue; // New features are auto-created by set-controller
    if (feature.enabled !== original.enabled) {
      if (feature.enabled) {
        promises.push(minerStore.enableFeature(minerId, feature.controller_id, feature.feature_type));
      } else {
        promises.push(minerStore.disableFeature(minerId, feature.controller_id, feature.feature_type));
      }
    }
    if (feature.priority !== original.priority) {
      promises.push(minerStore.setFeaturePriority(minerId, feature.controller_id, feature.feature_type, feature.priority));
    }
  }
  if (promises.length > 0) {
    await Promise.all(promises);
  }
}

function handleSave(miner: Miner, controllerChanges: { add: string[]; remove: string[] }, featureUpdates: MinerFeature[]) {
  if (isEditMode.value && miner.id) {
    minerStore
      .updateMiner(miner.id.toString(), miner)
      .then(async () => {
        await applyControllerChanges(miner.id!.toString(), controllerChanges);
        await applyFeatureChanges(miner.id!.toString(), featureUpdates, editingMiner.value);
        minerStore.loadMiners();
        handleCloseModal();
      })
      .showToasts(
        "Miner updated successfully",
        "Failed to update miner"
      );
  } else {
    minerStore
      .addMiner(miner)
      .then(async (created) => {
        if (created.id) {
          await applyControllerChanges(created.id.toString(), controllerChanges);
        }
        minerStore.loadMiners();
        handleCloseModal();
      })
      .showToasts(
        "Miner created successfully",
        "Failed to create miner"
      );
  }
}

function handleDelete(miner: Miner) {
  minerStore.deleteMiner(miner.id!.toString())
    .then(() => {
      minerStore.loadMiners();
    })
    .showToasts(
      "Miner deleted successfully",
      "Failed to delete miner"
    );
}

function handleStart(miner: Miner) {
  minerStore.startMiner(miner.id!.toString()).then(() => {
    minerStore.loadMiners();
  });
}

function handleStop(miner: Miner) {
  minerStore.stopMiner(miner.id!.toString()).then(() => {
    minerStore.loadMiners();
  });
}

function handleActivate(miner: Miner) {
  minerStore.activateMiner(miner.id!.toString()).then(() => {
    minerStore.loadMiners();
  });
}

function handleDeactivate(miner: Miner) {
  minerStore.deactivateMiner(miner.id!.toString()).then(() => {
    minerStore.loadMiners();
  });
}

function handleRefresh(miner: Miner) {
  minerStore.getMinerStatus(miner.id!.toString());
}

function formatHashRate(value: number, unit: string): string {
  if (value >= 1000) {
    // Upgrade unit
    const units = ["H/s", "KH/s", "MH/s", "GH/s", "TH/s", "PH/s", "EH/s"];
    const idx = units.indexOf(unit);
    if (idx < units.length - 1) {
      return `${(value / 1000).toFixed(1)} ${units[idx + 1]}`;
    }
  }
  return `${value.toFixed(1)} ${unit}`;
}

function getFilterCount(filter: string): number {
  if (filter === "all") return stats.value.totalMiners;
  if (filter === "active") return stats.value.activeMiners;
  return stats.value.statusCounts[filter] || 0;
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <!-- Header -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-base-content">Miners</h1>
          <p class="text-sm text-base-content/60 mt-1">
            Manage and monitor your mining hardware
          </p>
        </div>

        <button class="btn btn-primary gap-2" @click="openAddModal">
          <PhPlus :size="20" weight="bold" />
          Add Miner
        </button>
      </div>
    </div>
    <div class="card-body">
      <div class="space-y-6">
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">{{ stats.totalMiners }}</div>
            <div class="stat-label">Total Miners</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-primary">
              {{ stats.runningMiners }} / {{ stats.activeMiners }}
            </div>
            <div class="stat-label">Running / Active</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-sky-400 truncate">
              {{ stats.totalHashRate > 0 ? formatHashRate(stats.totalHashRate, stats.hashRateUnit) : "-" }}
            </div>
            <div class="stat-label">Total Hash Rate</div>
          </div>
          <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3 sm:p-4 min-w-0">
            <div class="stat-value text-amber-400 truncate">
              {{ stats.totalPowerConsumption > 0 ? formatPower(stats.totalPowerConsumption) : "-" }}
            </div>
            <div class="stat-label">Power Consumption</div>
          </div>
        </div>

        <!-- Filter Tabs -->
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="filter in statusFilters"
            :key="filter.value"
            class="btn btn-sm gap-2 transition-all"
            :class="[
              selectedStatusFilter === filter.value
                ? 'btn-primary'
                : 'btn-ghost opacity-70 hover:opacity-100',
            ]"
            @click="selectedStatusFilter = filter.value"
          >
            <component :is="filter.icon" :size="16" />
            {{ filter.label }}
            <span
              v-if="getFilterCount(filter.value) > 0"
              class="badge badge-sm"
              :class="selectedStatusFilter === filter.value ? 'bg-white/20 text-neutral-900' : 'badge-neutral'"
            >
              {{ getFilterCount(filter.value) }}
            </span>
          </button>
        </div>

        <!-- Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          <MinerCard
            v-for="miner in filteredMiners"
            :key="miner.id"
            :miner="miner"
            :state="miner.id ? minerStore.minerStates.get(miner.id) : undefined"
            @edit="handleEdit"
            @delete="handleDelete"
            @start="handleStart"
            @stop="handleStop"
            @activate="handleActivate"
            @deactivate="handleDeactivate"
            @refresh="handleRefresh"
          />

          <!-- Empty State -->
          <div
            v-if="filteredMiners.length === 0"
            class="col-span-full flex flex-col items-center justify-center py-16 text-center"
          >
            <div
              class="w-20 h-20 rounded-full bg-base-200 flex items-center justify-center mb-4"
            >
              <PhCpu :size="40" class="text-base-content/30" />
            </div>
            <h3 class="text-lg font-semibold text-base-content/80">
              {{ selectedStatusFilter === "all" ? "No miners yet" : "No miners with this status" }}
            </h3>
            <p class="text-sm text-base-content/50 mt-1 max-w-sm">
              {{
                selectedStatusFilter === "all"
                  ? "Add your first miner to start managing your mining operation."
                  : "Try selecting a different filter or add a new miner."
              }}
            </p>
            <button
              v-if="selectedStatusFilter === 'all'"
              class="btn btn-primary btn-sm mt-4 gap-2"
              @click="openAddModal"
            >
              <PhPlus :size="16" />
              Add Miner
            </button>
          </div>
        </div>

        <!-- Form Modal -->
        <MinerFormModal
          :open="showModal"
          :miner="editingMiner"
          :all-miners="minerStore.miners"
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

/* Ensure text doesn't overflow on small screens */
@media (max-width: 640px) {
  .stat-value {
    font-size: 1.25rem;
  }
}
</style>
