<script setup lang="ts">
import type { Miner, MinerStatus, MinerStateSnapshot } from "../../core/models/miner";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import { computed, ref, watch } from "vue";
import {
  PhPlay,
  PhStop,
  PhArrowClockwise,
  PhPencil,
  PhTrash,
  PhCpu,
  PhLightning,
  PhPower,
  PhGear,
  PhCircleNotch,
  PhWarningCircle,
  PhQuestion,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";
import EdgeMiningCard, { type CardStyleConfig } from "../EdgeMiningCard.vue";
import ResourceId from "../ResourceId.vue";
import { formatPower, formatHashRate, normalizeHashRate } from "../../core/utils/index";

const props = defineProps<{
  miner: Miner;
  state?: MinerStateSnapshot;
}>();

const emit = defineEmits<{
  edit: [miner: Miner];
  delete: [miner: Miner];
  start: [miner: Miner];
  stop: [miner: Miner];
  refresh: [miner: Miner];
  activate: [miner: Miner];
  deactivate: [miner: Miner];
}>();

const minerControllerStore = useMinerControllerStore();
const showDeleteConfirm = ref(false);
const isProcessing = ref(false);

const minerControllers = computed(() => {
  if (!props.miner.controller_ids?.length) return [];
  return minerControllerStore.minerControllers.filter(
    (mc) => props.miner.controller_ids!.includes(mc.id!)
  );
});

const hasController = computed(() => minerControllers.value.length > 0);

// Runtime state
const currentStatus = computed<MinerStatus>(() => props.state?.status ?? 'unknown');

// Status computations
const isOn = computed(() => currentStatus.value === "on");
const isStarting = computed(() => currentStatus.value === "starting");
const isStopping = computed(() => currentStatus.value === "stopping");
const canStart = computed(
  () =>
    props.miner.active &&
    !isOn.value &&
    (!isStarting.value || isStopping.value) &&
    !isProcessing.value
);
const canStop = computed(
  () =>
    props.miner.active &&
    (isOn.value || isStarting.value) &&
    !isProcessing.value
);

// Reset isProcessing when status changes
watch(
  currentStatus,
  (newStatus, oldStatus) => {
    if (newStatus !== oldStatus && isProcessing.value) {
      isProcessing.value = false;
    }
  }
);

// Status configuration
const statusConfig = computed(() => {
  const configs: Record<
    MinerStatus,
    {
      icon: typeof PhPower;
      label: string;
      pulse: boolean;
      styleConfig: CardStyleConfig;
      badgeClass: string;
    }
  > = {
    on: {
      icon: PhPower,
      label: "Running",
      pulse: true,
      badgeClass: "badge-success",
      styleConfig: {
        gradient: "hover:from-emerald-500/20 hover:to-green-500/10",
        iconColor: "text-emerald-400",
        iconBgColor: "bg-emerald-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-emerald-500",
      },
    },
    off: {
      icon: PhPower,
      label: "Off",
      pulse: false,
      badgeClass: "badge-ghost",
      styleConfig: {
        gradient: "hover:from-slate-500/20 hover:to-gray-500/10",
        iconColor: "text-slate-400",
        iconBgColor: "bg-slate-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-slate-500",
      },
    },
    starting: {
      icon: PhCircleNotch,
      label: "Starting",
      pulse: true,
      badgeClass: "badge-warning",
      styleConfig: {
        gradient: "hover:from-amber-500/20 hover:to-yellow-500/10",
        iconColor: "text-amber-400",
        iconBgColor: "bg-amber-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-amber-500",
      },
    },
    stopping: {
      icon: PhCircleNotch,
      label: "Stopping",
      pulse: true,
      badgeClass: "badge-warning",
      styleConfig: {
        gradient: "hover:from-orange-500/20 hover:to-amber-500/10",
        iconColor: "text-orange-400",
        iconBgColor: "bg-orange-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-orange-500",
      },
    },
    error: {
      icon: PhWarningCircle,
      label: "Error",
      pulse: false,
      badgeClass: "badge-error",
      styleConfig: {
        gradient: "hover:from-red-500/20 hover:to-rose-500/10",
        iconColor: "text-red-400",
        iconBgColor: "bg-red-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-red-500",
      },
    },
    unknown: {
      icon: PhQuestion,
      label: "Unknown",
      pulse: false,
      badgeClass: "badge-ghost",
      styleConfig: {
        gradient: "hover:from-gray-500/20 hover:to-slate-500/10",
        iconColor: "text-gray-400",
        iconBgColor: "bg-gray-500/20",
        accentBorder: "border-l-base-300/50 hover:border-l-gray-500",
      },
    },
  };
  return configs[currentStatus.value] || configs.unknown;
});

// Hash rate progress (normalize units before comparing)
const hashRateProgress = computed(() => {
  if (!props.state?.hash_rate?.value || !props.miner.hash_rate_max?.value)
    return 0;
  const current = normalizeHashRate(props.state.hash_rate.value, props.state.hash_rate.unit || "TH/s");
  const max = normalizeHashRate(props.miner.hash_rate_max.value, props.miner.hash_rate_max.unit || "TH/s");
  if (max === 0) return 0;
  return Math.min((current / max) * 100, 100);
});

// Power consumption progress
const powerProgress = computed(() => {
  if (!props.state?.power_consumption || !props.miner.power_consumption_max)
    return 0;
  return Math.min(
    (props.state.power_consumption / props.miner.power_consumption_max) * 100,
    100
  );
});

// Actions
function handleEdit() {
  emit("edit", props.miner);
}

function handleDeleteClick() {
  showDeleteConfirm.value = true;
}

function confirmDelete() {
  showDeleteConfirm.value = false;
  emit("delete", props.miner);
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}

function handleStart() {
  if (!canStart.value) return;
  isProcessing.value = true;
  emit("start", props.miner);
}

function handleStop() {
  if (!canStop.value) return;
  isProcessing.value = true;
  emit("stop", props.miner);
}

function handleRefresh() {
  emit("refresh", props.miner);
}

function handleActivate() {
  emit("activate", props.miner);
}

function handleDeactivate() {
  emit("deactivate", props.miner);
}
</script>

<template>
  <EdgeMiningCard :icon="statusConfig.icon" :icon-size="26" :style-config="statusConfig.styleConfig"
    :dimmed="!miner.active" :pulse="isOn">
    <!-- Custom Icon Slot for spinning animation -->
    <template #icon>
      <component :is="statusConfig.icon" :size="26" weight="duotone"
        :class="[statusConfig.styleConfig.iconColor, { 'animate-spin': statusConfig.pulse && (isStarting || isStopping) }]" />
    </template>

    <!-- Title -->
    <template #title>
      {{ miner.name }}
    </template>

    <!-- Badges -->
    <template #badges>
      <!-- Status Badge -->
      <span class="badge badge-sm" :class="statusConfig.badgeClass">
        {{ statusConfig.label }}
      </span>
      <!-- Active Badge -->
      <span v-if="!miner.active" class="badge badge-sm badge-ghost">
        Inactive
      </span>

      <!-- ID -->
      <ResourceId v-if="miner.id" :id="miner.id" />
    </template>

    <!-- Actions -->
    <template #actions>
      <button class="btn btn-ghost btn-sm btn-square hover:bg-primary/20" @click="handleEdit" title="Edit">
        <PhPencil :size="18" class="text-primary" />
      </button>
      <button class="btn btn-ghost btn-sm btn-square hover:bg-error/20" @click="handleDeleteClick" title="Delete">
        <PhTrash :size="18" class="text-error" />
      </button>
    </template>

    <!-- Main Content -->
    <div class="space-y-3">
      <!-- Model info -->
      <div v-if="miner.model" class="-mt-2 pb-1">
        <span class="text-xs text-base-content/50">{{ miner.model }}</span>
      </div>

      <!-- Hash Rate -->
      <div class="metric-box bg-base-100/40 rounded-lg px-3 py-2">
        <div class="flex items-center justify-between mb-1.5">
          <div class="flex items-center gap-1.5 text-xs text-base-content/60">
            <PhCpu :size="14" />
            <span>Hash Rate</span>
          </div>
          <div class="text-sm font-medium text-base-content">
            {{ formatHashRate(state?.hash_rate?.value, state?.hash_rate?.unit) }}
            <span class="text-base-content/40">
              / {{ formatHashRate(miner.hash_rate_max?.value, miner.hash_rate_max?.unit) }}
            </span>
          </div>
        </div>
        <div class="h-1.5 bg-base-300/50 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500"
            :class="isOn ? 'bg-emerald-500' : 'bg-base-content/20'" :style="{ width: `${hashRateProgress}%` }"></div>
        </div>
      </div>

      <!-- Power Consumption -->
      <div class="metric-box bg-base-100/40 rounded-lg px-3 py-2">
        <div class="flex items-center justify-between mb-1.5">
          <div class="flex items-center gap-1.5 text-xs text-base-content/60">
            <PhLightning :size="14" />
            <span>Power</span>
          </div>
          <div class="text-sm font-medium text-base-content">
            {{ formatPower(state?.power_consumption) }}
            <span class="text-base-content/40">
              / {{ formatPower(miner.power_consumption_max) }}
            </span>
          </div>
        </div>
        <div class="h-1.5 bg-base-300/50 rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500"
            :class="powerProgress > 90 ? 'bg-red-500' : powerProgress > 70 ? 'bg-amber-500' : 'bg-sky-500'"
            :style="{ width: `${powerProgress}%` }"></div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-center gap-2">
        <!-- Controller -->
        <div v-if="minerControllers.length" class="flex items-center gap-2 min-w-0 flex-shrink">
          <div class="h-6 w-6 rounded-full bg-info/20 flex items-center justify-center">
            <PhGear :size="14" class="text-info" />
          </div>
          <div>
            <div class="text-[10px] uppercase tracking-wider text-base-content/40">
              {{ minerControllers.length === 1 ? 'Controller' : 'Controllers' }}
            </div>
            <div class="text-sm text-base-content/80 leading-tight truncate max-w-[120px] sm:max-w-none">
              {{ minerControllers.map(mc => mc.name).join(', ') }}
            </div>
          </div>
        </div>
        <div v-else class="text-xs text-base-content/40 italic">No controller</div>

        <!-- Control Buttons -->
        <div class="flex items-center gap-1 flex-shrink-0 ml-auto">
          <div class="divider divider-horizontal mx-1 h-12"></div>
          <div class="flex flex-col items-end gap-1">
            <!-- Activate/Deactivate -->
            <div>
              <button v-if="!miner.active" class="btn btn-xs btn-info" @click="handleActivate" title="Activate">
                Activate
              </button>
              <button v-else class="btn btn-xs btn-ghost" @click="handleDeactivate" title="Deactivate">
                Deactivate
              </button>
            </div>

            <!-- Start/Stop/Refresh -->
            <div class="join">
              <button class="btn btn-xs join-item" :class="canStart ? 'btn-success' : 'btn-ghost opacity-40'"
                :disabled="!canStart || !hasController" @click="handleStart" title="Start">
                <PhPlay :size="14" />
              </button>
              <button class="btn btn-xs join-item" :class="canStop ? 'btn-warning' : 'btn-ghost opacity-40'"
                :disabled="!canStop || !hasController" @click="handleStop" title="Stop">
                <PhStop :size="14" />
              </button>
              <button class="btn btn-xs btn-info join-item" 
                :disabled="!hasController" @click="handleRefresh" title="Refresh">
                <PhArrowClockwise :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </EdgeMiningCard>

  <ConfirmDialog :open="showDeleteConfirm" title="Delete Miner"
    :message="`Are you sure you want to delete '${miner.name}'?`" confirm-text="Delete"
    variant="danger" @confirm="confirmDelete" @cancel="cancelDelete" />
</template>

<style scoped>
.metric-box {
  backdrop-filter: blur(4px);
}
</style>
