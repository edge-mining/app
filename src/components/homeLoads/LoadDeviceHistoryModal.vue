<script setup lang="ts">
import { ref, computed, watch } from "vue";
import VueApexCharts from "vue3-apexcharts";
import type { LoadDevice } from "../../core/models/homeLoadsProfile";
import type { HomeLoadPowerPoint } from "../../core/models/loadTraining";
import { useHomeLoadsProfileStore } from "../../core/stores/homeLoadsProfileStore";
import {
  PhX,
  PhChartLine,
  PhLightning,
  PhArrowsClockwise,
  PhCloudArrowDown,
  PhTrash,
} from "@phosphor-icons/vue";
import ConfirmDialog from "../ConfirmDialog.vue";

const props = defineProps<{
  open: boolean;
  device?: LoadDevice;
  profileId?: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

const profileStore = useHomeLoadsProfileStore();

const powerPoints = ref<HomeLoadPowerPoint[]>([]);
const loading = ref(false);
const collecting = ref(false);
const clearing = ref(false);
const showClearConfirm = ref(false);
const showCollectDialog = ref(false);
const lookbackHours = ref(24);
const selectedRange = ref<"24h" | "7d" | "30d">("24h");

const rangeOptions = [
  { value: "24h" as const, label: "Last 24h" },
  { value: "7d" as const, label: "Last 7 days" },
  { value: "30d" as const, label: "Last 30 days" },
];

function getTimeRange(range: "24h" | "7d" | "30d") {
  const now = new Date();
  const end = now.toISOString();
  let start: string;
  switch (range) {
    case "24h":
      start = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
      break;
    case "7d":
      start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
      break;
    case "30d":
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString();
      break;
  }
  return { start, end };
}

async function fetchHistory() {
  if (!props.profileId || !props.device?.id) return;
  loading.value = true;
  try {
    const { start, end } = getTimeRange(selectedRange.value);
    powerPoints.value = await profileStore.getDeviceHistory(
      props.profileId,
      props.device.id,
      start,
      end
    );
  } catch (e) {
    console.error("Failed to load device history:", e);
    powerPoints.value = [];
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen && props.device?.id && props.profileId) {
      fetchHistory();
    }
  },
  { immediate: true }
);

async function collectHistory() {
  if (!props.profileId || !props.device?.id) return;
  showCollectDialog.value = false;
  collecting.value = true;
  try {
    await profileStore.collectDeviceHistory(props.profileId, props.device.id, lookbackHours.value);
    await fetchHistory();
  } catch (e) {
    console.error("Failed to collect device history:", e);
  } finally {
    collecting.value = false;
  }
}

async function clearHistory() {
  if (!props.profileId || !props.device?.id) return;
  showClearConfirm.value = false;
  clearing.value = true;
  try {
    await profileStore.clearDeviceHistory(props.profileId, props.device.id);
    powerPoints.value = [];
  } catch (e) {
    console.error("Failed to clear device history:", e);
  } finally {
    clearing.value = false;
  }
}

watch(selectedRange, () => {
  if (props.open) fetchHistory();
});

// Stats
const stats = computed(() => {
  const points = powerPoints.value;
  if (points.length === 0)
    return { avgPower: 0, peakPower: 0, totalEnergy: 0, dataPoints: 0 };

  const powers = points.map((p) => p.power);
  const avgPower = powers.reduce((a, b) => a + b, 0) / powers.length;
  const peakPower = Math.max(...powers);

  // Estimate energy: sum of (power * time_interval) in Wh
  let totalEnergy = 0;
  for (let i = 1; i < points.length; i++) {
    const dt =
      (new Date(points[i].timestamp).getTime() -
        new Date(points[i - 1].timestamp).getTime()) /
      3600000; // hours
    totalEnergy += points[i - 1].power * dt;
  }

  return {
    avgPower: Math.round(avgPower),
    peakPower: Math.round(peakPower),
    totalEnergy: Math.round(totalEnergy),
    dataPoints: points.length,
  };
});

// Chart
const series = computed(() => [
  {
    name: "Power",
    data: powerPoints.value.map((p) => ({
      x: new Date(p.timestamp).getTime(),
      y: Math.round(p.power),
    })),
  },
]);

const chartOptions = computed(() => ({
  chart: {
    id: "device-history",
    type: "area" as const,
    height: 320,
    toolbar: { show: true, tools: { download: true, selection: true, zoom: true, zoomin: true, zoomout: true, pan: true, reset: true } },
    zoom: { enabled: true },
    background: "transparent",
  },
  colors: ["rgba(38, 198, 218, 0.9)"],
  fill: {
    type: "gradient",
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.4,
      opacityTo: 0.05,
      stops: [0, 100],
    },
  },
  stroke: { curve: "smooth" as const, width: 2 },
  dataLabels: { enabled: false },
  xaxis: {
    type: "datetime" as const,
    labels: { style: { colors: "oklch(80% 0 0 / 0.5)", fontSize: "11px" } },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: {
      style: { colors: "oklch(80% 0 0 / 0.5)", fontSize: "11px" },
      formatter: (v: number) => `${Math.round(v)} W`,
    },
  },
  grid: {
    borderColor: "oklch(30% 0 0 / 0.3)",
    strokeDashArray: 3,
  },
  tooltip: {
    theme: "dark",
    x: { format: "dd MMM yyyy HH:mm" },
    y: { formatter: (v: number) => `${Math.round(v)} W` },
  },
}));

function handleClose() {
  emit("close");
}

function formatWatts(v: number): string {
  if (v >= 1000) return `${(v / 1000).toFixed(1)} kW`;
  return `${v} W`;
}

function formatWh(v: number): string {
  if (v >= 1000) return `${(v / 1000).toFixed(1)} kWh`;
  return `${v} Wh`;
}
</script>

<template>
  <dialog class="modal" :class="{ 'modal-open': open }">
    <div class="modal-box max-w-4xl bg-base-100 border border-base-300/60">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-base-200/60 flex items-center justify-center">
            <PhChartLine :size="22" class="text-info" />
          </div>
          <div>
            <h3 class="text-xl font-bold">
              {{ device?.name ?? "Device" }} — History
            </h3>
            <p class="text-sm text-base-content/50">Power consumption over time</p>
          </div>
        </div>
        <button class="btn btn-ghost btn-sm btn-square" @click="handleClose">
          <PhX :size="20" />
        </button>
      </div>

      <!-- Range selector -->
      <div class="flex items-center gap-2 mb-4">
        <button
          v-for="opt in rangeOptions"
          :key="opt.value"
          class="btn btn-sm"
          :class="selectedRange === opt.value ? 'btn-primary' : 'btn-ghost'"
          @click="selectedRange = opt.value"
        >
          {{ opt.label }}
        </button>
        <button
          class="btn btn-sm btn-ghost gap-1 ml-auto"
          :disabled="collecting"
          @click="showCollectDialog = true"
        >
          <span v-if="collecting" class="loading loading-spinner loading-xs"></span>
          <PhCloudArrowDown v-else :size="16" />
          Collect
        </button>
        <button
          class="btn btn-sm btn-ghost gap-1"
          :disabled="loading"
          @click="fetchHistory"
        >
          <span v-if="loading" class="loading loading-spinner loading-xs"></span>
          <PhArrowsClockwise v-else :size="16" />
          Refresh
        </button>
        <button
          class="btn btn-sm btn-ghost text-error gap-1"
          :disabled="clearing || powerPoints.length === 0"
          @click="showClearConfirm = true"
        >
          <span v-if="clearing" class="loading loading-spinner loading-xs"></span>
          <PhTrash v-else :size="16" />
          Clear
        </button>
      </div>

      <!-- Stats cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3">
          <div class="text-lg font-bold text-primary">{{ formatWatts(stats.avgPower) }}</div>
          <div class="text-xs text-base-content/50">Avg Power</div>
        </div>
        <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3">
          <div class="text-lg font-bold text-error">{{ formatWatts(stats.peakPower) }}</div>
          <div class="text-xs text-base-content/50">Peak Power</div>
        </div>
        <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3">
          <div class="text-lg font-bold text-warning">{{ formatWh(stats.totalEnergy) }}</div>
          <div class="text-xs text-base-content/50">Total Energy</div>
        </div>
        <div class="stat-card bg-neutral-800/80 border border-base-300/40 rounded-xl p-3">
          <div class="text-lg font-bold text-info">{{ stats.dataPoints }}</div>
          <div class="text-xs text-base-content/50">Data Points</div>
        </div>
      </div>

      <!-- Chart -->
      <div class="bg-neutral-800/50 rounded-xl border border-base-300/40 p-3">
        <div v-if="loading" class="flex items-center justify-center h-[320px]">
          <span class="loading loading-spinner loading-lg text-primary"></span>
        </div>
        <div
          v-else-if="powerPoints.length === 0"
          class="flex flex-col items-center justify-center h-[320px] text-base-content/40"
        >
          <PhChartLine :size="48" />
          <p class="mt-2 text-sm">No history data available for this period</p>
        </div>
        <VueApexCharts
          v-else
          type="area"
          height="320"
          :options="chartOptions"
          :series="series"
        />
      </div>
    </div>

    <form method="dialog" class="modal-backdrop bg-black/50">
      <button @click="handleClose">close</button>
    </form>
  </dialog>

  <ConfirmDialog
    :open="showClearConfirm"
    title="Clear Device History"
    :message="`Are you sure you want to delete all history data for '${device?.name ?? 'this device'}'? This action cannot be undone.`"
    confirm-text="Delete All"
    variant="danger"
    @confirm="clearHistory"
    @cancel="showClearConfirm = false"
  />

  <!-- Collect Dialog -->
  <dialog class="modal" :class="{ 'modal-open': showCollectDialog }">
    <div class="modal-box max-w-sm bg-base-100 border border-base-300/60">
      <h3 class="font-bold text-lg flex items-center gap-2 mb-4">
        <PhCloudArrowDown :size="22" class="text-info" />
        Collect History
      </h3>
      <p class="text-sm text-base-content/70 mb-4">
        Fetch power data from the external history provider for
        <span class="font-semibold">{{ device?.name ?? 'this device' }}</span>.
      </p>
      <div class="form-control mb-6">
        <label class="label">
          <span class="label-text font-medium">Lookback period</span>
        </label>
        <div class="flex gap-2 flex-wrap mb-2">
          <button
            v-for="p in [{ value: 24, label: '24 hours' }, { value: 48, label: '48 hours' }, { value: 168, label: '7 days' }, { value: 720, label: '30 days' }]"
            :key="p.value"
            class="btn btn-xs"
            :class="lookbackHours === p.value ? 'btn-primary' : 'btn-ghost'"
            @click="lookbackHours = p.value"
          >{{ p.label }}</button>
        </div>
        <div class="flex items-center gap-2">
          <input
            v-model.number="lookbackHours"
            type="number"
            min="1"
            max="720"
            class="input input-bordered input-sm w-24"
          />
          <span class="text-sm text-base-content/50">hours (1–720)</span>
        </div>
      </div>
      <div class="modal-action">
        <button class="btn btn-ghost btn-sm" @click="showCollectDialog = false">Cancel</button>
        <button class="btn btn-primary btn-sm gap-1" @click="collectHistory">
          <PhCloudArrowDown :size="16" />
          Start Collection
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop bg-black/50">
      <button @click="showCollectDialog = false">close</button>
    </form>
  </dialog>
</template>
