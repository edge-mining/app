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
} from "@phosphor-icons/vue";
import type { ConsumptionForecast } from "../../core/models/homeLoad";

const profileStore = useHomeLoadsProfileStore();
const optimizationUnitStore = useOptimizationUnitStore();
const { lastUpdated, isPolling, latestDecisionalContexts } = useDashboardPolling(5000);

// ---------- Tick for "time ago" reactivity ----------
const now = ref(Date.now());
let tickTimer: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
  profileStore.loadProfiles();
  tickTimer = setInterval(() => { now.value = Date.now(); }, 1000);
});
onUnmounted(() => { if (tickTimer) clearInterval(tickTimer); });

const lastUpdateLabel = computed(() => {
  void now.value;
  return formatTimeAgo(lastUpdated.value);
});

// ---------- Profile KPIs ----------
const selectedProfile = computed(() =>
  profileStore.profiles.find((p) => p.id === profileStore.selectedProfileId)
);

const totalDevices = computed(() => selectedProfile.value?.devices.length ?? 0);
const activeDevices = computed(
  () => selectedProfile.value?.devices.filter((d) => d.enabled).length ?? 0
);

// ---------- Consumption Forecasts from DecisionalContexts ----------
interface UnitForecast {
  unitId: string;
  unitName: string;
  forecast: ConsumptionForecast;
}

const unitForecasts = computed<UnitForecast[]>(() => {
  const out: UnitForecast[] = [];
  for (const [unitId, ctx] of latestDecisionalContexts.value.entries()) {
    if (!ctx.home_load_forecast) continue;
    const unit = optimizationUnitStore.optimizationUnits.find((u) => u.id === unitId);
    out.push({
      unitId,
      unitName: unit?.name || unitId,
      forecast: ctx.home_load_forecast,
    });
  }
  return out;
});

const hasForecastData = computed(() => unitForecasts.value.length > 0);

// Aggregate current consumption (next hour) across all units
const totalNextHourPower = computed(() => {
  let total = 0;
  for (const uf of unitForecasts.value) {
    const intervals = uf.forecast.intervals;
    if (intervals.length > 0 && intervals[0].power_points.length > 0) {
      const avgPower =
        intervals[0].power_points.reduce((s, p) => s + p.power, 0) /
        intervals[0].power_points.length;
      total += avgPower;
    }
  }
  return total;
});

// Average power across all forecast intervals (approx next 4h)
const avgForecastPower = computed(() => {
  let totalPower = 0;
  let totalPoints = 0;
  for (const uf of unitForecasts.value) {
    for (const interval of uf.forecast.intervals) {
      for (const pp of interval.power_points) {
        totalPower += pp.power;
        totalPoints++;
      }
    }
  }
  return totalPoints > 0 ? totalPower / totalPoints : 0;
});

// Peak power across all forecasts
const peakForecastPower = computed(() => {
  let peak = 0;
  for (const uf of unitForecasts.value) {
    for (const interval of uf.forecast.intervals) {
      for (const pp of interval.power_points) {
        if (pp.power > peak) peak = pp.power;
      }
    }
  }
  return peak;
});

// Total forecast energy (sum of interval energies in Wh)
const totalForecastEnergy = computed(() => {
  let total = 0;
  for (const uf of unitForecasts.value) {
    for (const interval of uf.forecast.intervals) {
      if (interval.energy != null) {
        total += interval.energy;
      }
    }
  }
  return total;
});

// ---------- Chart data: consumption forecast timeline ----------
interface ChartPoint {
  x: number; // timestamp ms
  y: number; // watts
}

function buildForecastChartData(forecast: ConsumptionForecast): ChartPoint[] {
  const points: ChartPoint[] = [];
  for (const interval of forecast.intervals) {
    for (const pp of interval.power_points) {
      points.push({ x: new Date(pp.timestamp).getTime(), y: Math.round(pp.power) });
    }
  }
  return points.sort((a, b) => a.x - b.x);
}

// Chart options for ApexCharts
function buildChartOptions(_unitName: string) {
  return {
    chart: {
      type: "area" as const,
      height: 220,
      toolbar: { show: false },
      zoom: { enabled: false },
      background: "transparent",
    },
    stroke: { curve: "smooth" as const, width: 2 },
    fill: {
      type: "gradient",
      gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05, stops: [0, 100] },
    },
    colors: ["#f59e0b"],
    xaxis: {
      type: "datetime" as const,
      labels: {
        style: { colors: "oklch(var(--bc) / 0.4)", fontSize: "10px" },
        datetimeFormatter: { hour: "HH:mm" },
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
      x: { format: "HH:mm" },
      y: { formatter: (val: number) => `${Math.round(val)} W` },
    },
    dataLabels: { enabled: false },
  };
}

// ---------- Formatters ----------
function formatEnergy(wh: number): string {
  if (wh === 0) return "-";
  if (wh >= 1000) return `${(wh / 1000).toFixed(2)} kWh`;
  return `${Math.round(wh)} Wh`;
}
</script>

<template>
  <div class="dashboard-root space-y-5">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-base-content">Home Loads</h1>
        <p class="text-sm text-base-content/50 mt-0.5">
          Consumption forecast &amp; device overview
        </p>
      </div>
      <div class="flex items-center gap-2 text-xs text-base-content/40">
        <PhArrowsClockwise
          :size="14"
          :class="{ 'animate-spin': isPolling }"
        />
        <span>Updated {{ lastUpdateLabel }}</span>
      </div>
    </div>

    <!-- KPI Strip -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      <KpiCard
        label="Devices"
        :value="`${activeDevices} / ${totalDevices}`"
        sub-value="active"
        :icon="PhPlug"
        icon-color="text-primary"
        icon-bg-color="bg-primary/15"
        value-color="text-primary"
      />
      <KpiCard
        label="Current Load"
        :value="totalNextHourPower > 0 ? formatPower(totalNextHourPower) : '-'"
        sub-value="next hour avg"
        :icon="PhLightning"
        icon-color="text-amber-400"
        icon-bg-color="bg-amber-400/15"
        :value-color="totalNextHourPower > 0 ? 'text-amber-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Avg Forecast"
        :value="avgForecastPower > 0 ? formatPower(avgForecastPower) : '-'"
        sub-value="all intervals"
        :icon="PhChartLine"
        icon-color="text-orange-400"
        icon-bg-color="bg-orange-400/15"
        :value-color="avgForecastPower > 0 ? 'text-orange-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Peak Forecast"
        :value="peakForecastPower > 0 ? formatPower(peakForecastPower) : '-'"
        :icon="PhThermometer"
        icon-color="text-red-400"
        icon-bg-color="bg-red-400/15"
        :value-color="peakForecastPower > 0 ? 'text-red-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Energy Forecast"
        :value="totalForecastEnergy > 0 ? formatEnergy(totalForecastEnergy) : '-'"
        sub-value="total"
        :icon="PhClockCountdown"
        icon-color="text-teal-400"
        icon-bg-color="bg-teal-400/15"
        :value-color="totalForecastEnergy > 0 ? 'text-teal-400' : 'text-base-content/30'"
      />
    </div>

    <!-- Empty state when no forecast data -->
    <div
      v-if="!hasForecastData"
      class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-8 text-center"
    >
      <PhHouseLine :size="36" class="mx-auto text-base-content/15 mb-2" />
      <span class="block text-sm text-base-content/40">
        No home load forecast data available
      </span>
      <span class="block text-xs text-base-content/30 mt-1">
        Configure a home loads profile with forecast providers and assign it to an optimization unit.
      </span>
    </div>

    <!-- Per-unit Forecast Charts -->
    <div
      v-for="uf in unitForecasts"
      :key="uf.unitId"
      class="space-y-3"
    >
      <div class="flex items-center gap-2">
        <PhHouseLine :size="16" class="text-base-content/40" />
        <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
          {{ uf.unitName }}
        </h2>
        <span class="text-[10px] text-base-content/30 ml-auto">
          {{ formatTimeAgo(new Date(uf.forecast.timestamp)) }}
        </span>
      </div>

      <!-- Forecast Chart -->
      <ChartPanel title="Consumption Forecast" :icon="PhChartLine">
        <apexchart
          type="area"
          height="220"
          :options="buildChartOptions(uf.unitName)"
          :series="[{ name: 'Forecast Power', data: buildForecastChartData(uf.forecast) }]"
        />
      </ChartPanel>

      <!-- Interval Summary Table -->
      <div class="rounded-xl border border-base-300/20 bg-base-100/40 backdrop-blur-sm overflow-hidden">
        <table class="table table-sm w-full">
          <thead>
            <tr class="text-xs text-base-content/40 uppercase">
              <th>Interval</th>
              <th>Avg Power</th>
              <th>Energy</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(interval, idx) in uf.forecast.intervals"
              :key="idx"
              class="text-sm"
            >
              <td class="text-base-content/70">
                {{ new Date(interval.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
                –
                {{ new Date(interval.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
              </td>
              <td>
                <span v-if="interval.power_points.length > 0" class="font-medium text-amber-400">
                  {{ formatPower(interval.power_points.reduce((s, p) => s + p.power, 0) / interval.power_points.length) }}
                </span>
                <span v-else class="text-base-content/30">-</span>
              </td>
              <td>
                <span v-if="interval.energy != null" class="text-teal-400">
                  {{ formatEnergy(interval.energy) }}
                </span>
                <span v-else class="text-base-content/30">-</span>
              </td>
              <td class="text-base-content/50">
                {{ interval.power_points.length }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Device Overview (from selected profile) -->
    <div v-if="selectedProfile && selectedProfile.devices.length > 0" class="space-y-3">
      <div class="flex items-center gap-2">
        <PhPlug :size="16" class="text-base-content/40" />
        <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
          Devices — {{ selectedProfile.name }}
        </h2>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        <div
          v-for="device in selectedProfile.devices"
          :key="device.id"
          class="rounded-xl border border-base-300/20 bg-base-100/40 backdrop-blur-sm p-4 space-y-2"
        >
          <div class="flex items-center justify-between">
            <span class="font-medium text-sm text-base-content">{{ device.name }}</span>
            <span
              class="badge badge-xs"
              :class="device.enabled ? 'badge-success' : 'badge-ghost'"
            >
              {{ device.enabled ? 'Active' : 'Inactive' }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="badge badge-sm badge-outline capitalize">{{ device.category }}</span>
            <span
              v-if="device.energy_load_forecast_provider_id"
              class="text-[10px] text-base-content/40"
            >
              Forecast ✓
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
