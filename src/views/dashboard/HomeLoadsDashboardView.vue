<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useHomeLoadsProfileStore } from "../../core/stores/homeLoadsProfileStore";
import { useOptimizationUnitStore } from "../../core/stores/optimizationUnitStore";
import { useDashboardPolling } from "../../core/composables/useDashboardPolling";
import { formatPower, formatTimeAgo } from "../../core/utils/index";
import KpiCard from "../../components/dashboard/KpiCard.vue";
import ChartPanel from "../../components/dashboard/ChartPanel.vue";
import {
  PhHouseLine,
  PhPlug,
  PhLightning,
  PhChartLine,
  PhArrowsClockwise,
  PhClockCountdown,
  PhThermometer,
  PhTrendUp,
  PhTarget,
  PhCaretDown,
  PhCaretUp,
} from "@phosphor-icons/vue";
import VueApexCharts from "vue3-apexcharts";
import type {
  HomeLoadsConsumption,
  LoadEnergyConsumption,
} from "../../core/models/homeLoad";
import type { HomeLoadEnergyInterval } from "../../core/models/loadTraining";

const profileStore = useHomeLoadsProfileStore();
const optimizationUnitStore = useOptimizationUnitStore();
const { lastUpdated, isPolling, latestDecisionalContexts } = useDashboardPolling(5000);

// ---------- Tick for "time ago" reactivity ----------
const now = ref(Date.now());
let tickTimer: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
  profileStore.loadProfiles();
  tickTimer = setInterval(() => {
    now.value = Date.now();
  }, 1000);
});
onUnmounted(() => {
  if (tickTimer) clearInterval(tickTimer);
});

const lastUpdateLabel = computed(() => {
  void now.value;
  return formatTimeAgo(lastUpdated.value);
});

// ---------- Timeframe selector ----------
type TimeframeOption = { label: string; hours: number };
const timeframeOptions: TimeframeOption[] = [
  { label: "6h", hours: 6 },
  { label: "12h", hours: 12 },
  { label: "24h", hours: 24 },
  { label: "48h", hours: 48 },
];
const selectedTimeframeHours = ref(24);

// ---------- Profile ----------
const selectedProfile = computed(() =>
  profileStore.profiles.find((p) => p.id === profileStore.selectedProfileId)
);
const totalDevices = computed(() => selectedProfile.value?.devices.length ?? 0);
const activeDevices = computed(
  () => selectedProfile.value?.devices.filter((d) => d.enabled).length ?? 0
);

// ---------- Home Load data from DecisionalContexts ----------
interface UnitHomeLoad {
  unitId: string;
  unitName: string;
  homeLoad: HomeLoadsConsumption;
}

const unitHomeLoads = computed<UnitHomeLoad[]>(() => {
  const out: UnitHomeLoad[] = [];
  for (const [unitId, ctx] of latestDecisionalContexts.value.entries()) {
    if (!ctx.home_load) continue;
    const unit = optimizationUnitStore.optimizationUnits.find((u) => u.id === unitId);
    // DEBUG: log raw data to diagnose chart rendering
    console.log("[HomeLoadsDashboard] home_load for unit", unitId, JSON.stringify({
      total_history_intervals: ctx.home_load.total_history?.intervals?.length ?? 0,
      total_forecast_intervals: ctx.home_load.total_forecast?.intervals?.length ?? 0,
      per_device_count: ctx.home_load.per_device?.length ?? 0,
      first_history_interval: ctx.home_load.total_history?.intervals?.[0],
      first_forecast_interval: ctx.home_load.total_forecast?.intervals?.[0],
      first_device_history_interval: ctx.home_load.per_device?.[0]?.history?.intervals?.[0],
      first_device_forecast_interval: ctx.home_load.per_device?.[0]?.forecast?.intervals?.[0],
    }, null, 2));
    out.push({
      unitId,
      unitName: unit?.name || unitId,
      homeLoad: ctx.home_load,
    });
  }
  return out;
});

const hasHomeLoadData = computed(() => unitHomeLoads.value.length > 0);

// ---------- Utility: filter intervals within timeframe ----------
function filterIntervals(
  intervals: HomeLoadEnergyInterval[] | undefined,
  windowHours: number,
  reference: "past" | "future"
): HomeLoadEnergyInterval[] {
  if (!intervals?.length) return [];
  const nowMs = Date.now();
  const cutoff =
    reference === "past"
      ? nowMs - windowHours * 3600_000
      : nowMs + windowHours * 3600_000;
  return intervals.filter((i) => {
    const t = new Date(reference === "past" ? i.start : i.end).getTime();
    return reference === "past" ? t >= cutoff : t <= cutoff;
  });
}

// ---------- KPI: Total current power ----------
const totalCurrentPower = computed(() => {
  let total = 0;
  for (const uh of unitHomeLoads.value) {
    // Try total_forecast first, fallback to per-device
    const intervals = uh.homeLoad.total_forecast?.intervals;
    if (intervals?.length && intervals[0].avg_power != null) {
      total += intervals[0].avg_power;
    } else {
      // Fallback: sum first interval from each device forecast
      for (const dev of uh.homeLoad.per_device ?? []) {
        const devIntervals = dev.forecast?.intervals;
        if (devIntervals?.length && devIntervals[0].avg_power != null) {
          total += devIntervals[0].avg_power;
        }
      }
    }
  }
  return total;
});

// ---------- KPI: Total history energy ----------
const totalHistoryEnergy = computed(() => {
  let total = 0;
  for (const uh of unitHomeLoads.value) {
    // Try total_history, fallback to per-device
    let intervals = uh.homeLoad.total_history?.intervals ?? [];
    if (!intervals.length) {
      // Aggregate from per-device
      for (const dev of uh.homeLoad.per_device ?? []) {
        for (const i of dev.history?.intervals ?? []) {
          if (i.energy != null) total += i.energy;
        }
      }
    } else {
      for (const i of intervals) {
        if (i.energy != null) total += i.energy;
      }
    }
  }
  return total;
});

// ---------- KPI: Average forecast power ----------
const avgForecastPower = computed(() => {
  let totalPower = 0;
  let count = 0;
  for (const uh of unitHomeLoads.value) {
    let intervals = uh.homeLoad.total_forecast?.intervals ?? [];
    // Fallback: aggregate from per-device
    if (!intervals.length) {
      for (const dev of uh.homeLoad.per_device ?? []) {
        for (const i of dev.forecast?.intervals ?? []) {
          if (i.avg_power != null && i.avg_power !== 0) { totalPower += i.avg_power; count++; }
        }
      }
    } else {
      for (const i of intervals) {
        if (i.avg_power != null && i.avg_power !== 0) { totalPower += i.avg_power; count++; }
      }
    }
  }
  return count > 0 ? totalPower / count : 0;
});

// ---------- KPI: Peak forecast power ----------
const peakForecastPower = computed(() => {
  let peak = 0;
  for (const uh of unitHomeLoads.value) {
    let intervals = uh.homeLoad.total_forecast?.intervals ?? [];
    if (!intervals.length) {
      for (const dev of uh.homeLoad.per_device ?? []) {
        for (const i of dev.forecast?.intervals ?? []) {
          if (i.avg_power != null && i.avg_power > peak) peak = i.avg_power;
        }
      }
    } else {
      for (const i of intervals) {
        if (i.avg_power != null && i.avg_power > peak) peak = i.avg_power;
      }
    }
  }
  return peak;
});

// ---------- KPI: Total forecast energy ----------
const totalForecastEnergy = computed(() => {
  let total = 0;
  for (const uh of unitHomeLoads.value) {
    let intervals = uh.homeLoad.total_forecast?.intervals ?? [];
    if (!intervals.length) {
      for (const dev of uh.homeLoad.per_device ?? []) {
        for (const i of dev.forecast?.intervals ?? []) {
          if (i.energy != null) total += i.energy;
        }
      }
    } else {
      for (const i of intervals) {
        if (i.energy != null) total += i.energy;
      }
    }
  }
  return total;
});

// ---------- KPI: % Variation (forecast vs history) ----------
const variationPercent = computed(() => {
  if (totalHistoryEnergy.value === 0) return null;
  return ((totalForecastEnergy.value - totalHistoryEnergy.value) / totalHistoryEnergy.value) * 100;
});

// ---------- KPI: Accuracy ratio (how close forecast is to history for overlapping periods) ----------
const accuracyRatio = computed(() => {
  // Compare avg power between history and forecast (last shared window)
  let histTotal = 0;
  let histCount = 0;
  let foreTotal = 0;
  let foreCount = 0;
  for (const uh of unitHomeLoads.value) {
    for (const i of uh.homeLoad.total_history?.intervals ?? []) {
      if (i.avg_power != null) { histTotal += i.avg_power; histCount++; }
    }
    for (const i of uh.homeLoad.total_forecast?.intervals ?? []) {
      if (i.avg_power != null) { foreTotal += i.avg_power; foreCount++; }
    }
  }
  if (histCount === 0 || foreCount === 0) return null;
  const histAvg = histTotal / histCount;
  const foreAvg = foreTotal / foreCount;
  if (histAvg === 0) return null;
  // Accuracy = 1 - |error|/actual, clamped to [0,1]
  const error = Math.abs(foreAvg - histAvg) / histAvg;
  return Math.max(0, Math.min(100, (1 - error) * 100));
});

// ---------- Chart data ----------
interface ChartPoint {
  x: number;
  y: number;
}

function buildChartData(consumption: LoadEnergyConsumption | undefined): ChartPoint[] {
  if (!consumption?.intervals) return [];
  const points: ChartPoint[] = [];
  for (const interval of consumption.intervals) {
    if (interval.avg_power != null && interval.avg_power !== 0) {
      const start = new Date(interval.start).getTime();
      const end = new Date(interval.end).getTime();
      const mid = start + (end - start) / 2;
      points.push({ x: mid, y: Math.round(interval.avg_power) });
    }
  }
  return points.sort((a, b) => a.x - b.x);
}

// Fallback: aggregate per-device data when total is empty
function buildAggregatedChartData(homeLoad: HomeLoadsConsumption, field: "history" | "forecast"): ChartPoint[] {
  const buckets = new Map<number, number>(); // midTimestamp -> sumPower
  for (const dev of homeLoad.per_device ?? []) {
    const consumption = field === "history" ? dev.history : dev.forecast;
    if (!consumption?.intervals) continue;
    for (const interval of consumption.intervals) {
      if (interval.avg_power != null && interval.avg_power !== 0) {
        const start = new Date(interval.start).getTime();
        const end = new Date(interval.end).getTime();
        const mid = start + (end - start) / 2;
        buckets.set(mid, (buckets.get(mid) ?? 0) + interval.avg_power);
      }
    }
  }
  const points: ChartPoint[] = [];
  for (const [x, y] of buckets) {
    points.push({ x, y: Math.round(y) });
  }
  return points.sort((a, b) => a.x - b.x);
}

// Chart series with fallback: try total, then aggregate per-device
function getChartSeries(homeLoad: HomeLoadsConsumption): { name: string; data: ChartPoint[] }[] {
  const historyData = buildChartData(homeLoad.total_history);
  const forecastData = buildChartData(homeLoad.total_forecast);
  return [
    { name: "History", data: historyData.length > 0 ? historyData : buildAggregatedChartData(homeLoad, "history") },
    { name: "Forecast", data: forecastData.length > 0 ? forecastData : buildAggregatedChartData(homeLoad, "forecast") },
  ];
}

function getDeviceChartSeries(dev: { history?: LoadEnergyConsumption; forecast?: LoadEnergyConsumption }): { name: string; data: ChartPoint[] }[] {
  return [
    { name: "History", data: buildChartData(dev.history) },
    { name: "Forecast", data: buildChartData(dev.forecast) },
  ];
}

function buildOverlaidChartOptions(title?: string) {
  return {
    chart: {
      type: "area" as const,
      height: 280,
      toolbar: { show: false },
      zoom: { enabled: true },
      background: "transparent",
    },
    stroke: { curve: "smooth" as const, width: [2, 2] },
    fill: {
      type: "gradient",
      gradient: { shadeIntensity: 1, opacityFrom: 0.35, opacityTo: 0.05, stops: [0, 100] },
    },
    colors: ["#3b82f6", "#f59e0b"], // blue=history, amber=forecast
    xaxis: {
      type: "datetime" as const,
      labels: {
        style: { colors: "oklch(var(--bc) / 0.4)", fontSize: "10px" },
        datetimeFormatter: { hour: "HH:mm", day: "dd MMM" },
      },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: {
      labels: {
        style: { colors: "oklch(var(--bc) / 0.4)", fontSize: "10px" },
        formatter: (val: number) => `${Math.round(val)} W`,
      },
    },
    grid: { borderColor: "oklch(var(--bc) / 0.05)", strokeDashArray: 3 },
    tooltip: {
      theme: "dark",
      x: { format: "dd MMM HH:mm" },
      y: { formatter: (val: number) => `${Math.round(val)} W` },
    },
    legend: {
      show: true,
      position: "top" as const,
      labels: { colors: "oklch(var(--bc) / 0.5)" },
    },
    dataLabels: { enabled: false },
    ...(title ? { title: { text: title, style: { color: "oklch(var(--bc) / 0.5)", fontSize: "12px" } } } : {}),
  };
}

function buildDeviceChartOptions() {
  return {
    ...buildOverlaidChartOptions(),
    chart: {
      ...buildOverlaidChartOptions().chart,
      height: 200,
    },
  };
}

// ---------- Expanded devices ----------
const expandedDevices = ref<Set<string>>(new Set());

function toggleDevice(deviceId: string) {
  if (expandedDevices.value.has(deviceId)) {
    expandedDevices.value.delete(deviceId);
  } else {
    expandedDevices.value.add(deviceId);
  }
}

// ---------- Formatters ----------
function formatEnergy(wh: number): string {
  if (wh === 0) return "-";
  if (wh >= 1000) return `${(wh / 1000).toFixed(2)} kWh`;
  return `${Math.round(wh)} Wh`;
}

function formatPercent(val: number | null): string {
  if (val == null) return "-";
  return `${val >= 0 ? "+" : ""}${val.toFixed(1)}%`;
}
</script>

<template>
  <div class="dashboard-root space-y-5">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-2">
      <div>
        <h1 class="text-2xl font-bold text-base-content">Home Loads</h1>
        <p class="text-sm text-base-content/50 mt-0.5">
          History &amp; forecast of household consumption
        </p>
      </div>
      <div class="flex items-center gap-3">
        <!-- Timeframe selector -->
        <div class="btn-group">
          <button
            v-for="tf in timeframeOptions"
            :key="tf.hours"
            class="btn btn-xs"
            :class="selectedTimeframeHours === tf.hours ? 'btn-primary' : 'btn-ghost'"
            @click="selectedTimeframeHours = tf.hours"
          >
            {{ tf.label }}
          </button>
        </div>
        <div class="flex items-center gap-2 text-xs text-base-content/40">
          <PhArrowsClockwise :size="14" :class="{ 'animate-spin': isPolling }" />
          <span>{{ lastUpdateLabel }}</span>
        </div>
      </div>
    </div>

    <!-- KPI Strip -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-8 gap-3">
      <KpiCard
        label="Devices"
        :value="`${activeDevices}/${totalDevices}`"
        subValue="active"
        :icon="PhPlug"
        icon-color="text-primary"
        icon-bg-color="bg-primary/15"
        value-color="text-primary"
      />
      <KpiCard
        label="Current Load"
        :value="totalCurrentPower > 0 ? formatPower(totalCurrentPower) : '-'"
        subValue="real-time"
        :icon="PhLightning"
        icon-color="text-amber-400"
        icon-bg-color="bg-amber-400/15"
        :value-color="totalCurrentPower > 0 ? 'text-amber-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="History Energy"
        :value="totalHistoryEnergy > 0 ? formatEnergy(totalHistoryEnergy) : '-'"
        :subValue="`last ${selectedTimeframeHours}h`"
        :icon="PhClockCountdown"
        icon-color="text-blue-400"
        icon-bg-color="bg-blue-400/15"
        :value-color="totalHistoryEnergy > 0 ? 'text-blue-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Forecast Energy"
        :value="totalForecastEnergy > 0 ? formatEnergy(totalForecastEnergy) : '-'"
        :subValue="`next ${selectedTimeframeHours}h`"
        :icon="PhChartLine"
        icon-color="text-amber-500"
        icon-bg-color="bg-amber-500/15"
        :value-color="totalForecastEnergy > 0 ? 'text-amber-500' : 'text-base-content/30'"
      />
      <KpiCard
        label="Avg Forecast"
        :value="avgForecastPower > 0 ? formatPower(avgForecastPower) : '-'"
        subValue="avg power"
        :icon="PhChartLine"
        icon-color="text-orange-400"
        icon-bg-color="bg-orange-400/15"
        :value-color="avgForecastPower > 0 ? 'text-orange-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Peak"
        :value="peakForecastPower > 0 ? formatPower(peakForecastPower) : '-'"
        subValue="max forecast"
        :icon="PhThermometer"
        icon-color="text-red-400"
        icon-bg-color="bg-red-400/15"
        :value-color="peakForecastPower > 0 ? 'text-red-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Variation"
        :value="formatPercent(variationPercent)"
        subValue="forecast vs history"
        :icon="PhTrendUp"
        icon-color="text-violet-400"
        icon-bg-color="bg-violet-400/15"
        :value-color="variationPercent != null ? (variationPercent > 0 ? 'text-red-400' : 'text-green-400') : 'text-base-content/30'"
      />
      <KpiCard
        label="Accuracy"
        :value="accuracyRatio != null ? `${accuracyRatio.toFixed(0)}%` : '-'"
        subValue="hist/forecast"
        :icon="PhTarget"
        icon-color="text-emerald-400"
        icon-bg-color="bg-emerald-400/15"
        :value-color="accuracyRatio != null ? 'text-emerald-400' : 'text-base-content/30'"
      />
    </div>

    <!-- Empty state -->
    <div
      v-if="!hasHomeLoadData"
      class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-8 text-center"
    >
      <PhHouseLine :size="36" class="mx-auto text-base-content/15 mb-2" />
      <span class="block text-sm text-base-content/40">
        No home load data available
      </span>
      <span class="block text-xs text-base-content/30 mt-1">
        Configure a Home Loads profile with history/forecast providers and assign it to an optimization unit.
      </span>
    </div>

    <!-- Per-unit sections -->
    <div v-for="uh in unitHomeLoads" :key="uh.unitId" class="space-y-4">
      <div class="flex items-center gap-2">
        <PhHouseLine :size="16" class="text-base-content/40" />
        <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
          {{ uh.unitName }}
        </h2>
        <span class="text-[10px] text-base-content/30 ml-auto">
          {{ formatTimeAgo(new Date(uh.homeLoad.total_forecast?.timestamp || uh.homeLoad.total_history?.timestamp || Date.now())) }}
        </span>
      </div>

      <!-- Main overlaid chart: History + Forecast -->
      <ChartPanel
        v-if="uh.homeLoad.total_history?.intervals?.length || uh.homeLoad.total_forecast?.intervals?.length || uh.homeLoad.per_device?.length"
        title="Total Consumption — History & Forecast"
        :icon="PhChartLine"
        :has-data="true"
      >
        <VueApexCharts
          type="area"
          height="280"
          :options="buildOverlaidChartOptions()"
          :series="getChartSeries(uh.homeLoad)"
        />
      </ChartPanel>

      <!-- 2-column layout: Interval tables -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- History table -->
        <div
          v-if="uh.homeLoad.total_history?.intervals?.length"
          class="rounded-xl border border-base-300/20 bg-base-100/40 backdrop-blur-sm overflow-hidden"
        >
          <div class="px-4 py-2 border-b border-base-300/20 flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-blue-400"></span>
            <span class="text-xs font-semibold text-base-content/50 uppercase tracking-wider">History</span>
          </div>
          <div class="max-h-60 overflow-y-auto">
            <table class="table table-xs w-full">
              <thead class="sticky top-0 bg-base-100/90 backdrop-blur-sm">
                <tr class="text-xs text-base-content/40 uppercase">
                  <th>Interval</th>
                  <th>Avg Power</th>
                  <th>Energy</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(interval, idx) in filterIntervals(uh.homeLoad.total_history.intervals, selectedTimeframeHours, 'past')"
                  :key="idx"
                  class="text-sm"
                >
                  <td class="text-base-content/70 text-xs">
                    {{ new Date(interval.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}–{{ new Date(interval.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                  </td>
                  <td>
                    <span v-if="interval.avg_power != null" class="font-medium text-blue-400 text-xs">
                      {{ formatPower(interval.avg_power) }}
                    </span>
                    <span v-else class="text-base-content/30">-</span>
                  </td>
                  <td>
                    <span v-if="interval.energy != null" class="text-blue-300 text-xs">
                      {{ formatEnergy(interval.energy) }}
                    </span>
                    <span v-else class="text-base-content/30">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Forecast table -->
        <div
          v-if="uh.homeLoad.total_forecast?.intervals?.length"
          class="rounded-xl border border-base-300/20 bg-base-100/40 backdrop-blur-sm overflow-hidden"
        >
          <div class="px-4 py-2 border-b border-base-300/20 flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-amber-400"></span>
            <span class="text-xs font-semibold text-base-content/50 uppercase tracking-wider">Forecast</span>
          </div>
          <div class="max-h-60 overflow-y-auto">
            <table class="table table-xs w-full">
              <thead class="sticky top-0 bg-base-100/90 backdrop-blur-sm">
                <tr class="text-xs text-base-content/40 uppercase">
                  <th>Interval</th>
                  <th>Avg Power</th>
                  <th>Energy</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(interval, idx) in filterIntervals(uh.homeLoad.total_forecast.intervals, selectedTimeframeHours, 'future')"
                  :key="idx"
                  class="text-sm"
                >
                  <td class="text-base-content/70 text-xs">
                    {{ new Date(interval.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}–{{ new Date(interval.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                  </td>
                  <td>
                    <span v-if="interval.avg_power != null" class="font-medium text-amber-400 text-xs">
                      {{ formatPower(interval.avg_power) }}
                    </span>
                    <span v-else class="text-base-content/30">-</span>
                  </td>
                  <td>
                    <span v-if="interval.energy != null" class="text-amber-300 text-xs">
                      {{ formatEnergy(interval.energy) }}
                    </span>
                    <span v-else class="text-base-content/30">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Per-device expandable cards -->
      <div v-if="uh.homeLoad.per_device?.length" class="space-y-2">
        <div class="flex items-center gap-2 mb-2">
          <PhPlug :size="14" class="text-base-content/40" />
          <span class="text-xs font-semibold text-base-content/50 uppercase tracking-wider">
            Per-Device Detail ({{ uh.homeLoad.per_device.length }})
          </span>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
          <div
            v-for="dev in uh.homeLoad.per_device"
            :key="dev.device_id"
            class="rounded-xl border border-base-300/20 bg-base-100/40 backdrop-blur-sm overflow-hidden"
          >
            <!-- Device header (clickable) -->
            <button
              class="w-full px-4 py-3 flex items-center justify-between hover:bg-base-300/10 transition-colors"
              @click="toggleDevice(dev.device_id)"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="font-medium text-sm text-base-content truncate">{{ dev.device_name }}</span>
                  <span class="badge badge-xs badge-outline capitalize flex-shrink-0">{{ dev.device_category }}</span>
                </div>
              </div>
              <div class="flex items-center gap-3 flex-shrink-0">
                <!-- Quick avg power -->
                <span
                  v-if="dev.forecast?.intervals?.length && dev.forecast.intervals[0].avg_power != null"
                  class="text-xs font-medium text-amber-400"
                >
                  {{ formatPower(dev.forecast.intervals[0].avg_power) }}
                </span>
                <component
                  :is="expandedDevices.has(dev.device_id) ? PhCaretUp : PhCaretDown"
                  :size="14"
                  class="text-base-content/30"
                />
              </div>
            </button>

            <!-- Expanded: full chart -->
            <div
              v-if="expandedDevices.has(dev.device_id)"
              class="px-4 pb-4 border-t border-base-300/10 space-y-3"
            >
              <!-- Device KPIs row -->
              <div class="flex items-center gap-4 pt-3 text-xs text-base-content/60">
                <div>
                  <span class="text-base-content/40">History: </span>
                  <span class="font-medium text-blue-400">{{ dev.history?.intervals?.length ?? 0 }} intervals</span>
                </div>
                <div>
                  <span class="text-base-content/40">Forecast: </span>
                  <span class="font-medium text-amber-400">{{ dev.forecast?.intervals?.length ?? 0 }} intervals</span>
                </div>
              </div>

              <!-- Device chart -->
              <div v-if="dev.history?.intervals?.length || dev.forecast?.intervals?.length">
                <VueApexCharts
                  type="area"
                  height="200"
                  :options="buildDeviceChartOptions()"
                  :series="getDeviceChartSeries(dev)"
                />
              </div>
              <div v-else class="text-center text-xs text-base-content/30 py-4">
                No data available for this device
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
