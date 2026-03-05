<script setup lang="ts">
import type { Miner, MinerStatus } from "../../core/models/miner";
import { useMinerControllerStore } from "../../core/stores/minerControllerStore";
import { computed, ref, watch } from "vue";
import {
  PhHash,
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

const props = defineProps<{
  miner: Miner;
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

const minerController = computed(() => {
  if (!props.miner.controller_id) return null;
  return minerControllerStore.minerControllers.find(
    (mc) => mc.id === props.miner.controller_id
  );
});

// Status computations
const isOn = computed(() => props.miner.status === "on");
const isStarting = computed(() => props.miner.status === "starting");
const isStopping = computed(() => props.miner.status === "stopping");
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
  () => props.miner.status,
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
      color: string;
      bgColor: string;
      borderColor: string;
      label: string;
      pulse: boolean;
    }
  > = {
    on: {
      icon: PhPower,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/20",
      borderColor: "border-l-emerald-500",
      label: "Running",
      pulse: true,
    },
    off: {
      icon: PhPower,
      color: "text-slate-400",
      bgColor: "bg-slate-500/20",
      borderColor: "border-l-slate-500",
      label: "Off",
      pulse: false,
    },
    starting: {
      icon: PhCircleNotch,
      color: "text-amber-400",
      bgColor: "bg-amber-500/20",
      borderColor: "border-l-amber-500",
      label: "Starting",
      pulse: true,
    },
    stopping: {
      icon: PhCircleNotch,
      color: "text-orange-400",
      bgColor: "bg-orange-500/20",
      borderColor: "border-l-orange-500",
      label: "Stopping",
      pulse: true,
    },
    error: {
      icon: PhWarningCircle,
      color: "text-red-400",
      bgColor: "bg-red-500/20",
      borderColor: "border-l-red-500",
      label: "Error",
      pulse: false,
    },
    unknown: {
      icon: PhQuestion,
      color: "text-gray-400",
      bgColor: "bg-gray-500/20",
      borderColor: "border-l-gray-500",
      label: "Unknown",
      pulse: false,
    },
  };
  return configs[props.miner.status] || configs.unknown;
});

// Hash rate progress
const hashRateProgress = computed(() => {
  if (!props.miner.hash_rate?.value || !props.miner.hash_rate_max?.value)
    return 0;
  return Math.min(
    (props.miner.hash_rate.value / props.miner.hash_rate_max.value) * 100,
    100
  );
});

// Power consumption progress
const powerProgress = computed(() => {
  if (!props.miner.power_consumption || !props.miner.power_consumption_max)
    return 0;
  return Math.min(
    (props.miner.power_consumption / props.miner.power_consumption_max) * 100,
    100
  );
});

// Format hash rate
function formatHashRate(value?: number, unit?: string): string {
  if (!value) return "-";
  return `${value} ${unit || ""}`;
}

// Format power
function formatPower(watts?: number): string {
  if (!watts) return "-";
  if (watts >= 1000) return `${(watts / 1000).toFixed(1)} kW`;
  return `${watts} W`;
}

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

// Copy ID to clipboard
const idCopied = ref(false);
async function copyId() {
  if (!props.miner.id) return;
  try {
    await navigator.clipboard.writeText(String(props.miner.id));
    idCopied.value = true;
    setTimeout(() => (idCopied.value = false), 1500);
  } catch {
    const el = document.createElement("textarea");
    el.value = String(props.miner.id);
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
    idCopied.value = true;
    setTimeout(() => (idCopied.value = false), 1500);
  }
}
</script>

<template>
  <div
    class="miner-card group relative flex flex-col rounded-xl border border-base-300/50 transition-all duration-300 hover:border-base-300 hover:shadow-lg hover:shadow-black/20"
    :class="[
      `border-l-4 border-l-transparent hover:${statusConfig.borderColor}`,
      { 'opacity-50': !miner.active },
    ]"
  >
    <!-- Header with Status Indicator -->
    <div class="flex items-start justify-between p-4 pb-2">
      <div class="flex items-center gap-3">
        <!-- Status Icon -->
        <div
          class="relative flex h-12 w-12 items-center justify-center rounded-xl backdrop-blur-sm"
          :class="statusConfig.bgColor"
        >
          <component
            :is="statusConfig.icon"
            :size="26"
            weight="duotone"
            :class="[statusConfig.color, { 'animate-spin': statusConfig.pulse && (isStarting || isStopping) }]"
          />
          <!-- Pulse animation for running -->
          <span
            v-if="isOn"
            class="absolute -top-1 -right-1 h-3 w-3"
          >
            <span
              class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"
            ></span>
            <span
              class="relative inline-flex h-3 w-3 rounded-full bg-emerald-500"
            ></span>
          </span>
        </div>

        <div class="min-w-0">
          <h3 class="text-lg font-semibold text-base-content leading-tight truncate">
            {{ miner.name }}
          </h3>
          <div class="flex items-center gap-2 mt-1 flex-wrap">
            <!-- Status Badge -->
            <span
              class="badge badge-sm"
              :class="{
                'badge-success': isOn,
                'badge-warning': isStarting || isStopping,
                'badge-error': miner.status === 'error',
                'badge-ghost': miner.status === 'off' || miner.status === 'unknown',
              }"
            >
              {{ statusConfig.label }}
            </span>
            <!-- Active Badge -->
            <span
              v-if="!miner.active"
              class="badge badge-sm badge-ghost"
            >
              Inactive
            </span>
            <!-- ID -->
            <button
              v-if="miner.id"
              class="tooltip tooltip-top text-xs opacity-50 hover:opacity-100 transition-opacity flex items-center gap-0.5"
              :data-tip="idCopied ? 'Copied!' : `ID: ${miner.id}`"
              @click="copyId"
            >
              <PhHash :size="12" />
              <span class="font-mono text-left">{{ miner.id.split('-')[0] }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          class="btn btn-ghost btn-sm btn-square hover:bg-primary/20"
          @click="handleEdit"
          title="Edit"
        >
          <PhPencil :size="18" class="text-primary" />
        </button>
        <button
          class="btn btn-ghost btn-sm btn-square hover:bg-error/20"
          @click="handleDeleteClick"
          title="Delete"
        >
          <PhTrash :size="18" class="text-error" />
        </button>
      </div>
    </div>

    <!-- Model info -->
    <div v-if="miner.model" class="px-4 pb-2">
      <span class="text-xs text-base-content/50">{{ miner.model }}</span>
    </div>

    <!-- Metrics -->
    <div class="px-4 pb-4 space-y-3 flex-grow">
      <!-- Hash Rate -->
      <div class="metric-box bg-base-100/40 rounded-lg px-3 py-2">
        <div class="flex items-center justify-between mb-1.5">
          <div class="flex items-center gap-1.5 text-xs text-base-content/60">
            <PhCpu :size="14" />
            <span>Hash Rate</span>
          </div>
          <div class="text-sm font-medium text-base-content">
            {{ formatHashRate(miner.hash_rate?.value, miner.hash_rate?.unit) }}
            <span class="text-base-content/40">
              / {{ formatHashRate(miner.hash_rate_max?.value, miner.hash_rate_max?.unit) }}
            </span>
          </div>
        </div>
        <div class="h-1.5 bg-base-300/50 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="isOn ? 'bg-emerald-500' : 'bg-base-content/20'"
            :style="{ width: `${hashRateProgress}%` }"
          ></div>
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
            {{ formatPower(miner.power_consumption) }}
            <span class="text-base-content/40">
              / {{ formatPower(miner.power_consumption_max) }}
            </span>
          </div>
        </div>
        <div class="h-1.5 bg-base-300/50 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="powerProgress > 90 ? 'bg-red-500' : powerProgress > 70 ? 'bg-amber-500' : 'bg-sky-500'"
            :style="{ width: `${powerProgress}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- Footer: Controller & Controls -->
    <div class="border-t border-base-300/30 px-4 py-3 bg-base-100/20 mt-auto">
      <div class="flex items-start justify-between gap-2">
        <!-- Controller -->
        <div v-if="minerController" class="flex items-center gap-2 min-w-0 flex-shrink">
          <div class="h-6 w-6 rounded-full bg-info/20 flex items-center justify-center">
            <PhGear :size="14" class="text-info" />
          </div>
          <div>
            <div class="text-[10px] uppercase tracking-wider text-base-content/40">
              Controller
            </div>
            <div class="text-sm text-base-content/80 leading-tight truncate max-w-[120px] sm:max-w-none">
              {{ minerController.name }}
            </div>
          </div>
        </div>
        <div v-else class="text-xs text-base-content/40 italic">No controller</div>

        <!-- Control Buttons -->
        <div class="flex items-center gap-1 flex-shrink-0 ml-auto">
          <!-- Activate/Deactivate -->
          <button
            v-if="!miner.active"
            class="btn btn-xs btn-info"
            @click="handleActivate"
            title="Activate"
          >
            Activate
          </button>
          <button
            v-else
            class="btn btn-xs btn-ghost"
            @click="handleDeactivate"
            title="Deactivate"
          >
            Deactivate
          </button>

          <div class="divider divider-horizontal mx-0.5 h-6"></div>

          <!-- Start/Stop/Refresh -->
          <div class="join">
            <button
              class="btn btn-xs join-item"
              :class="canStart ? 'btn-success' : 'btn-ghost opacity-40'"
              :disabled="!canStart"
              @click="handleStart"
              title="Start"
            >
              <PhPlay :size="14" />
            </button>
            <button
              class="btn btn-xs join-item"
              :class="canStop ? 'btn-warning' : 'btn-ghost opacity-40'"
              :disabled="!canStop"
              @click="handleStop"
              title="Stop"
            >
              <PhStop :size="14" />
            </button>
            <button
              class="btn btn-xs btn-info join-item"
              @click="handleRefresh"
              title="Refresh"
            >
              <PhArrowClockwise :size="14" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <ConfirmDialog
    :open="showDeleteConfirm"
    title="Delete Miner"
    :message="`Are you sure you want to delete '${miner.name}'? This action cannot be undone.`"
    confirm-text="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>

<style scoped>
.miner-card {
  background-color: oklch(28% 0 0 / 0.8);
}

.metric-box {
  backdrop-filter: blur(4px);
}
</style>
