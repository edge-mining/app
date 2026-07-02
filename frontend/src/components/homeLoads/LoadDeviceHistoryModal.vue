<script setup lang="ts">
import { ref, computed, watch } from "vue";
import VueApexCharts from "vue3-apexcharts";
import type { LoadDevice } from "../../core/models/homeLoadsProfile";
import type { HomeLoadPowerPoint, HomeLoadEnergyInterval } from "../../core/models/loadTraining";
import { useHomeLoadsProfileStore } from "../../core/stores/homeLoadsProfileStore";
import { useEnergyLoadForecastProviderStore } from "../../core/stores/energyLoadForecastProviderStore";
import {
  PhX,
  PhChartLine,
  PhArrowsClockwise,
  PhCloudArrowDown,
  PhTrash,
  PhTrendUp,
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
const forecastProviderStore = useEnergyLoadForecastProviderStore();

const powerPoints = ref<HomeLoadPowerPoint[]>([]);
const forecastIntervals = ref<HomeLoadEnergyInterval[]>([]);
const loading = ref(false);
const loadingForecast = ref(false);
const forecastError = ref<string | null>(null);
const collecting = ref(false);
const clearing = ref(false);
const showClearConfirm = ref(false);
const showCollectDialog = ref(false);
const showRetrainConfirm = ref(false);
const retraining = ref(false);
const retrainOutcome = ref<{ status: string; detail: string } | null>(null);
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

async function fetchForecast() {
  if (!props.profileId || !props.device?.id) return;
  loadingForecast.value = true;
  forecastError.value = null;
  try {
    const provider = forecastProviderStore.providers.find(
      (p) => p.id === props.device?.energy_load_forecast_provider_id
    );
    const historyHours = provider?.min_required_history_hours
      ? Math.ceil(provider.min_required_history_hours * 1.5)
      : 72;
    const result = await profileStore.getDeviceForecast(
      props.profileId,
      props.device.id,
      3,
      historyHours
    );
    forecastIntervals.value = result.intervals;
  } catch (e: any) {
    console.error("Failed to load device forecast:", e);
    forecastIntervals.value = [];
    forecastError.value = e?.response?.data?.detail || e?.message || "Unknown error";
  } finally {
    loadingForecast.value = false;
  }
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen && props.device?.id && props.profileId) {
      fetchHistory();
      fetchForecast();
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
    // Ask the user whether to retrain the forecast model with the freshly
    // collected data (only meaningful if the device has a forecast provider).
    if (props.device.energy_load_forecast_provider_id) {
      showRetrainConfirm.value = true;
    }
  } catch (e) {
    console.error("Failed to collect device history:", e);
  } finally {
    collecting.value = false;
  }
}

async function retrainModel() {
  showRetrainConfirm.value = false;
  if (!props.profileId || !props.device?.id) return;
  retraining.value = true;
  retrainOutcome.value = null;
  try {
    const res = await profileStore.trainDevice(props.profileId, props.device.id);
    retrainOutcome.value = { status: res.status ?? "completed", detail: res.detail ?? "" };
    // Only a real (re)training changes the active model: refresh the forecast.
    if (res.status === "trained") {
      await fetchForecast();
    }
  } catch (e: any) {
    console.error("Failed to retrain model:", e);
    retrainOutcome.value = {
      status: "failed",
      detail: e?.response?.data?.detail || e?.message || "Unknown error",
    };
  } finally {
    retraining.value = false;
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

// Forecast stats
const forecastStats = computed(() => {
  const intervals = forecastIntervals.value.filter((i) => i.avg_power != null);
  if (intervals.length === 0)
    return { avgPower: 0, peakPower: 0, totalEnergy: 0, dataPoints: 0 };

  const powers = intervals.map((i) => i.avg_power!);
  const avgPower = powers.reduce((a, b) => a + b, 0) / powers.length;
  const peakPower = Math.max(...powers);

  let totalEnergy = 0;
  for (const i of intervals) {
    if (i.energy != null) {
      totalEnergy += i.energy;
    } else if (i.avg_power != null) {
      const dt =
        (new Date(i.end).getTime() - new Date(i.start).getTime()) / 3600000;
      totalEnergy += i.avg_power * dt;
    }
  }

  return {
    avgPower: Math.round(avgPower),
    peakPower: Math.round(peakPower),
    totalEnergy: Math.round(totalEnergy),
    dataPoints: intervals.length,
  };
});

// Chart
const series = computed(() => {
  const s: { name: string; data: { x: number; y: number }[] }[] = [
    {
      name: "Power",
      data: powerPoints.value.map((p) => ({
        x: new Date(p.timestamp).getTime(),
        y: Math.round(p.power),
      })),
    },
  ];

  if (forecastIntervals.value.length > 0) {
    s.push({
      name: "Forecast",
      data: forecastIntervals.value
        .filter((i) => i.avg_power != null)
        .map((i) => ({
          x: new Date(i.start).getTime(),
          y: Math.round(i.avg_power!),
        })),
    });
  }

  return s;
});

// Average line annotation
const avgAnnotation = computed(() => {
  if (stats.value.avgPower === 0) return { yaxis: [] };
  return {
    yaxis: [
      {
        y: stats.value.avgPower,
        borderColor: "rgba(250, 204, 21, 0.5)",
        strokeDashArray: 4,
        label: {
          text: `Avg ${formatWatts(stats.value.avgPower)}`,
          borderColor: "transparent",
          style: {
            background: "rgba(250, 204, 21, 0.12)",
            color: "#facc15",
            fontSize: "10px",
            padding: { left: 6, right: 6, top: 2, bottom: 2 },
          },
          position: "front" as const,
        },
      },
    ],
  };
});

const chartOptions = computed(() => {
  // Force reactivity on data change
  void powerPoints.value;

  return {
    chart: {
      id: "device-history",
      type: "area" as const,
      height: 320,
      toolbar: {
        show: false,
      },
      zoom: { enabled: true, type: "x" as const },
      animations: {
        enabled: true,
        easing: "easeinout" as const,
        speed: 500,
      },
      background: "transparent",
      fontFamily: "inherit",
      selection: { enabled: true },
    },
    colors: ["rgba(38, 198, 218, 0.9)", "rgba(168, 85, 247, 0.9)"],
    fill: {
      type: "gradient" as const,
      gradient: {
        shade: "dark" as const,
        type: "vertical" as const,
        opacityFrom: 0.35,
        opacityTo: 0.02,
        stops: [0, 100],
      },
    },
    stroke: {
      curve: "smooth" as const,
      width: [2.5, 2],
      dashArray: [0, 6],
    },
    dataLabels: { enabled: false },
    xaxis: {
      type: "datetime" as const,
      labels: {
        show: true,
        style: { colors: "rgba(255,255,255,0.3)", fontSize: "10px" },
        datetimeFormatter: {
          year: "yyyy",
          month: "MMM 'yy",
          day: "dd MMM",
          hour: "HH:mm",
          minute: "HH:mm",
        },
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
      tooltip: { enabled: false },
      crosshairs: {
        show: true,
        stroke: { color: "rgba(38, 198, 218, 0.3)", width: 1, dashArray: 3 },
      },
    },
    yaxis: {
      decimalsInFloat: 0,
      labels: {
        show: true,
        style: { colors: "rgba(255,255,255,0.3)", fontSize: "10px" },
        formatter: (v: number) => formatWatts(v),
      },
      title: { text: undefined },
    },
    grid: {
      borderColor: "rgba(255,255,255,0.04)",
      strokeDashArray: 3,
      xaxis: { lines: { show: true } },
      yaxis: { lines: { show: true } },
      padding: { left: 8, right: 8, top: 0, bottom: 0 },
    },
    tooltip: {
      enabled: true,
      shared: true,
      intersect: false,
      followCursor: true,
      theme: "dark" as const,
      x: { show: true, format: "dd MMM yyyy HH:mm" },
      y: {
        formatter: (v: number) => (v != null ? formatWatts(v) : "—"),
      },
      marker: { show: true },
    },
    markers: {
      size: powerPoints.value.length > 500 ? [0, 0] : [2, 3],
      colors: ["rgba(38, 198, 218, 0.9)", "rgba(168, 85, 247, 0.9)"],
      strokeColors: ["rgba(38, 198, 218, 0.4)", "rgba(168, 85, 247, 0.4)"],
      strokeWidth: 1,
      hover: { size: 5, sizeOffset: 2 },
    },
    annotations: avgAnnotation.value,
    legend: {
      show: forecastIntervals.value.length > 0,
      position: "top" as const,
      horizontalAlign: "right" as const,
      labels: { colors: "rgba(255,255,255,0.5)" },
      markers: { size: 4 },
    },
  };
});

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
              {{ device?.name ?? "Device" }} — History & Forecast
            </h3>
            <p class="text-sm text-base-content/50">Power consumption history and forecast</p>
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
          class="btn btn-sm btn-ghost text-cyan-400 gap-1 ml-auto"
          :disabled="collecting"
          @click="showCollectDialog = true"
        >
          <span v-if="collecting" class="loading loading-spinner loading-xs"></span>
          <PhCloudArrowDown v-else :size="16" />
          Collect
        </button>
        <button
          class="btn btn-sm btn-ghost text-cyan-400 gap-1"
          :disabled="loading"
          @click="fetchHistory"
        >
          <span v-if="loading" class="loading loading-spinner loading-xs"></span>
          <PhArrowsClockwise v-else :size="16" />
          Refresh
        </button>
        <button
          class="btn btn-sm btn-ghost text-purple-400 gap-1"
          :disabled="loadingForecast"
          @click="fetchForecast"
        >
          <span v-if="loadingForecast" class="loading loading-spinner loading-xs"></span>
          <PhTrendUp v-else :size="16" />
          Forecast
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
        <div class="stat-card bg-neutral-800/80 border border-cyan-500/30 rounded-xl p-3">
          <div class="text-lg font-bold text-cyan-400">{{ formatWatts(stats.avgPower) }}</div>
          <div class="text-xs text-base-content/50">Avg Power</div>
        </div>
        <div class="stat-card bg-neutral-800/80 border border-cyan-500/30 rounded-xl p-3">
          <div class="text-lg font-bold text-cyan-300">{{ formatWatts(stats.peakPower) }}</div>
          <div class="text-xs text-base-content/50">Peak Power</div>
        </div>
        <div class="stat-card bg-neutral-800/80 border border-cyan-500/30 rounded-xl p-3">
          <div class="text-lg font-bold text-cyan-200">{{ formatWh(stats.totalEnergy) }}</div>
          <div class="text-xs text-base-content/50">Total Energy</div>
        </div>
        <div class="stat-card bg-neutral-800/80 border border-cyan-500/30 rounded-xl p-3">
          <div class="text-lg font-bold text-cyan-100">{{ stats.dataPoints }}</div>
          <div class="text-xs text-base-content/50">Data Points</div>
        </div>
      </div>

      <!-- Forecast stats cards -->
      <div v-if="forecastStats.dataPoints > 0" class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div class="stat-card bg-neutral-800/80 border border-purple-500/30 rounded-xl p-3">
          <div class="text-lg font-bold text-purple-400">{{ formatWatts(forecastStats.avgPower) }}</div>
          <div class="text-xs text-base-content/50">Forecast Avg Power</div>
        </div>
        <div class="stat-card bg-neutral-800/80 border border-purple-500/30 rounded-xl p-3">
          <div class="text-lg font-bold text-purple-300">{{ formatWatts(forecastStats.peakPower) }}</div>
          <div class="text-xs text-base-content/50">Forecast Peak Power</div>
        </div>
        <div class="stat-card bg-neutral-800/80 border border-purple-500/30 rounded-xl p-3">
          <div class="text-lg font-bold text-purple-200">{{ formatWh(forecastStats.totalEnergy) }}</div>
          <div class="text-xs text-base-content/50">Forecast Energy</div>
        </div>
        <div class="stat-card bg-neutral-800/80 border border-purple-500/30 rounded-xl p-3">
          <div class="text-lg font-bold text-purple-100">{{ forecastStats.dataPoints }}</div>
          <div class="text-xs text-base-content/50">Forecast Points</div>
        </div>
      </div>

      <!-- Forecast error alert -->
      <div v-if="forecastError" class="alert alert-warning shadow-sm py-2 px-3 mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-5 w-5" fill="none" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span class="text-xs">Forecast unavailable: {{ forecastError }}</span>
        <button class="btn btn-ghost btn-xs" @click="forecastError = null">
          <PhX :size="14" />
        </button>
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

  <ConfirmDialog
    :open="showRetrainConfirm"
    title="Retrain forecast model"
    :message="`History updated for '${device?.name ?? 'this device'}'. Retrain the forecast model now with the new data?`"
    confirm-text="Retrain"
    @confirm="retrainModel"
    @cancel="showRetrainConfirm = false"
  />

  <!-- Retrain status toast — teleported to body and given a very high z-index
       so it renders above the open History & Forecast modal instead of behind it. -->
  <Teleport to="body">
    <div v-if="retraining || retrainOutcome" class="toast toast-end z-[9999]">
      <div v-if="retraining" class="alert alert-info">
        <span>Retraining forecast model…</span>
      </div>
      <div
        v-else-if="retrainOutcome"
        class="alert"
        :class="{
          'alert-success': retrainOutcome.status === 'trained',
          'alert-warning': retrainOutcome.status === 'skipped',
          'alert-error': retrainOutcome.status === 'failed',
          'alert-info': !['trained', 'skipped', 'failed'].includes(retrainOutcome.status),
        }"
      >
        <span>{{ retrainOutcome.detail }}</span>
        <button class="btn btn-ghost btn-xs" @click="retrainOutcome = null">Dismiss</button>
      </div>
    </div>
  </Teleport>

  <!-- Collect Dialog -->
  <dialog class="modal" :class="{ 'modal-open': showCollectDialog }">
    <div class="modal-box max-w-md bg-base-100 border border-base-300/60">
      <!-- Header -->
      <div class="flex items-center gap-3 mb-5">
        <div class="h-10 w-10 rounded-xl bg-info/10 flex items-center justify-center shrink-0">
          <PhCloudArrowDown :size="22" class="text-info" />
        </div>
        <div>
          <h3 class="font-bold text-lg leading-tight">Collect History</h3>
          <p class="text-xs text-base-content/50 mt-0.5">
            Fetch power data from the external history provider for
            <span class="font-semibold text-base-content/70">{{ device?.name ?? 'this device' }}</span>
          </p>
        </div>
      </div>

      <!-- Lookback period -->
      <div class="mb-6">
        <label class="text-sm font-medium text-base-content/70 mb-3 block">Lookback period</label>
        <div class="grid grid-cols-4 gap-2 mb-4">
          <button
            v-for="p in [{ value: 24, label: '24h' }, { value: 48, label: '48h' }, { value: 168, label: '7d' }, { value: 720, label: '30d' }]"
            :key="p.value"
            class="btn btn-sm"
            :class="lookbackHours === p.value ? 'btn-primary' : 'btn-ghost border border-base-300/50'"
            @click="lookbackHours = p.value"
          >{{ p.label }}</button>
        </div>
        <div class="flex items-center gap-3 bg-base-200/40 rounded-xl px-4 py-3">
          <span class="text-sm text-base-content/50 shrink-0">Custom</span>
          <input
            v-model.number="lookbackHours"
            type="number"
            min="1"
            max="720"
            class="input input-bordered input-sm w-20 text-center"
          />
          <span class="text-sm text-base-content/40">hours</span>
          <span class="text-xs text-base-content/30 ml-auto">max 720</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-2">
        <button class="btn btn-ghost btn-sm" @click="showCollectDialog = false">Cancel</button>
        <button class="btn btn-primary btn-sm gap-1.5" @click="collectHistory">
          <PhCloudArrowDown :size="16" />
          Collect
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop bg-black/50">
      <button @click="showCollectDialog = false">close</button>
    </form>
  </dialog>
</template>
