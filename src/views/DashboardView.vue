<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useMinerStore } from "../core/stores/minerStore";
import { useOptimizationUnitStore } from "../core/stores/optimizationUnitStore";
import { useDashboardPolling } from "../core/composables/useDashboardPolling";
import { normalizeHashRate, formatPower, formatTimeAgo } from "../core/utils/index";

const CHART_COLOR_PRIMARY = 'rgba(190, 255, 163, 0.9)';  // #beffa3
const CHART_COLOR_WARNING = 'rgba(244, 184, 96, 0.9)';   // #f4b860
const CHART_COLOR_SOLAR = 'rgba(250, 204, 21, 0.9)';     // yellow-400
const CHART_COLOR_BATTERY = 'rgba(45, 212, 191, 0.9)';   // teal-400
const CHART_COLOR_BATTERY_POWER = 'rgba(129, 140, 248, 0.9)'; // indigo-400
const CHART_COLOR_GRID = 'rgba(56, 189, 248, 0.9)';      // sky-400
const CHART_COLOR_FORECAST = 'rgba(129, 140, 248, 0.9)'; // indigo-400
const CHART_COLOR_CONSUMPTION = 'rgba(251, 146, 60, 0.9)'; // orange-400
import KpiCard from "../components/dashboard/KpiCard.vue";
import MinerTile from "../components/dashboard/MinerTile.vue";
import ChartPanel from "../components/dashboard/ChartPanel.vue";
import RealtimeChart from "../components/dashboard/RealtimeChart.vue";
import ActivityFeed from "../components/dashboard/ActivityFeed.vue";
import {
  PhCpu,
  PhLightning,
  PhPower,
  PhGraph,
  PhSun,
  PhBatteryCharging,
  PhChartLine,
  PhClockCounterClockwise,
  PhShieldCheck,
  PhArrowsClockwise,
  PhPlug,
  PhHouseLine,
  PhThermometer,
  PhSunHorizon,
  PhCloudSun,
} from "@phosphor-icons/vue";

const minerStore = useMinerStore();
const optimizationUnitStore = useOptimizationUnitStore();
const { lastUpdated, isPolling, events, hashRateSeries, powerSeries, energyProductionSeries, batterySOCSeries, batteryPowerSeries, gridPowerSeries, consumptionSeries, minerOnOffEvents, forecastPowerPoints, latestDecisionalContexts } = useDashboardPolling(5000);

// ---------- KPI computations ----------

const totalMiners = computed(() => minerStore.miners.length);

const runningMiners = computed(
  () => minerStore.miners.filter((m) => m.status === "on").length
);

const activeMiners = computed(
  () => minerStore.miners.filter((m) => m.active).length
);

const totalHashRate = computed(() => {
  let total = 0;
  for (const m of minerStore.miners) {
    if (m.status === "on" && m.hash_rate?.value) {
      total += normalizeHashRate(m.hash_rate.value, m.hash_rate.unit || "TH/s");
    }
  }
  return total;
});

const formattedHashRate = computed(() => {
  const val = totalHashRate.value;
  if (val === 0) return "-";
  if (val >= 1000) return `${(val / 1000).toFixed(1)} PH/s`;
  return `${val.toFixed(1)} TH/s`;
});

const totalPowerConsumption = computed(() => {
  return minerStore.miners
    .filter((m) => m.status === "on")
    .reduce((sum, m) => sum + (m.power_consumption || 0), 0);
});

const enabledUnits = computed(
  () => optimizationUnitStore.optimizationUnits.filter((u) => u.is_enabled).length
);

const totalUnits = computed(
  () => optimizationUnitStore.optimizationUnits.length
);

const now = ref(Date.now());
let tickTimer: ReturnType<typeof setInterval> | undefined;
onMounted(() => { tickTimer = setInterval(() => { now.value = Date.now(); }, 1000); });
onUnmounted(() => { if (tickTimer) clearInterval(tickTimer); });

const lastUpdateLabel = computed(() => {
  void now.value; // reactive tick
  return formatTimeAgo(lastUpdated.value);
});

function formatHashRateValue(v: number): string {
  if (v <= 0) return "0 TH/s";
  if (v >= 1000) return `${(v / 1000).toFixed(2)} PH/s`;
  if (v >= 1) return `${v.toFixed(2)} TH/s`;
  if (v >= 0.001) return `${(v * 1000).toFixed(2)} GH/s`;
  return `${(v * 1000000).toFixed(2)} MH/s`;
}

function formatPowerValue(v: number): string {
  if (v <= 0) return "0 W";
  if (v >= 1000000) return `${(v / 1000000).toFixed(2)} MW`;
  if (v >= 1000) return `${(v / 1000).toFixed(2)} kW`;
  return `${v.toFixed(0)} W`;
}

function formatBatteryValue(v: number): string {
  return `${v.toFixed(1)}%`;
}

// Energy KPIs from latest decisional contexts
const latestEnergyProduction = computed(() => {
  const last = energyProductionSeries.value;
  return last.length > 0 ? last[last.length - 1].value : 0;
});

const latestBatterySOC = computed(() => {
  const last = batterySOCSeries.value;
  return last.length > 0 ? last[last.length - 1].value : null;
});

const latestGridPower = computed(() => {
  const last = gridPowerSeries.value;
  return last.length > 0 ? last[last.length - 1].value : 0;
});

const latestConsumption = computed(() => {
  const last = consumptionSeries.value;
  return last.length > 0 ? last[last.length - 1].value : 0;
});

// Forecast chart data converted to TimeSeriesPoint format
const forecastSeries = computed(() => {
  return forecastPowerPoints.value
    .filter((p) => p.power > 0 || forecastPowerPoints.value.indexOf(p) === 0 || forecastPowerPoints.value.indexOf(p) === forecastPowerPoints.value.length - 1)
    .map((p) => ({
      time: Math.floor(new Date(p.timestamp).getTime() / 1000),
      value: p.power,
    }));
});

// Sun data from latest decisional contexts
const latestSun = computed(() => {
  for (const ctx of latestDecisionalContexts.value.values()) {
    if (ctx.sun) return ctx.sun;
  }
  return null;
});

const sunInfo = computed(() => {
  const sun = latestSun.value;
  if (!sun) return null;
  const nowMs = now.value;
  const sunrise = new Date(sun.sunrise).getTime();
  const sunset = new Date(sun.sunset).getTime();
  const isDay = nowMs >= sunrise && nowMs < sunset;
  return {
    sunriseTime: new Date(sun.sunrise).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
    sunsetTime: new Date(sun.sunset).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
    dawnTime: new Date(sun.dawn).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
    duskTime: new Date(sun.dusk).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }),
    daylightHours: (sun.daylight / 3600).toFixed(1),
    isDay,
    timeToSunrise: sunrise - nowMs,
    timeToSunset: sunset - nowMs,
    elevation: sun.elevation,
  };
});

function formatDuration(ms: number): string {
  const totalSec = Math.abs(Math.floor(ms / 1000));
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

const sunArcProgress = computed(() => {
  if (!sunInfo.value) return 0.5;
  const sun = sunInfo.value;
  // Calculate progress along the sun's arc over 24-hour cycle
  // -1 to 0: before sunrise (approaching from left)
  // 0 to 1: from sunrise to sunset
  // 1+: after sunset (moving to right)
  const dayDuration = sun.timeToSunset - sun.timeToSunrise;
  const progress = -sun.timeToSunrise / dayDuration;
  // Clamp to visible range: -0.2 to 1.2 to show sun before/after arc
  return Math.max(-0.2, Math.min(1.2, progress));
});

// Forecast summary: today, remaining today, tomorrow
const forecastSummary = computed(() => {
  const ctxs = latestDecisionalContexts.value;
  let todayEnergy = 0;
  let remainingToday = 0;
  let tomorrowEnergy = 0;
  let hasData = false;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dayAfter = new Date(tomorrow);
  dayAfter.setDate(dayAfter.getDate() + 1);

  for (const ctx of ctxs.values()) {
    if (!ctx.forecast?.intervals) continue;
    hasData = true;
    for (const interval of ctx.forecast.intervals) {
      const start = new Date(interval.start).getTime();
      if (start >= today.getTime() && start < tomorrow.getTime()) {
        todayEnergy += interval.energy ?? 0;
        remainingToday += interval.energy_remaining ?? 0;
      } else if (start >= tomorrow.getTime() && start < dayAfter.getTime()) {
        tomorrowEnergy += interval.energy ?? 0;
      }
    }
  }

  return hasData ? { todayEnergy, remainingToday, tomorrowEnergy } : null;
});

function formatEnergy(wh: number): string {
  if (wh <= 0) return '0 Wh';
  if (wh >= 1000000) return `${(wh / 1000000).toFixed(1)} MWh`;
  if (wh >= 1000) return `${(wh / 1000).toFixed(1)} kWh`;
  return `${wh.toFixed(0)} Wh`;
}
</script>

<template>
  <div class="dashboard-root space-y-5">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-base-content">Dashboard</h1>
        <p class="text-sm text-base-content/50 mt-0.5">
          Real-time mining &amp; energy overview
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
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-3">
      <KpiCard
        label="Total Hash Rate"
        :value="formattedHashRate"
        :icon="PhCpu"
        icon-color="text-primary"
        icon-bg-color="bg-primary/15"
        :value-color="totalHashRate > 0 ? 'text-primary' : 'text-base-content/30'"
      />
      <KpiCard
        label="Power Draw"
        :value="totalPowerConsumption > 0 ? formatPower(totalPowerConsumption) : '-'"
        :sub-value="latestConsumption > 0 ? `Home: ${formatPower(latestConsumption)}` : ''"
        :icon="PhLightning"
        icon-color="text-warning"
        icon-bg-color="bg-warning/15"
        :value-color="totalPowerConsumption > 0 ? 'text-warning' : 'text-base-content/30'"
      />
      <KpiCard
        label="Energy Production"
        :value="latestEnergyProduction > 0 ? formatPower(latestEnergyProduction) : '-'"
        :icon="PhSun"
        icon-color="text-yellow-400"
        icon-bg-color="bg-yellow-400/15"
        :value-color="latestEnergyProduction > 0 ? 'text-yellow-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Battery"
        :value="latestBatterySOC !== null ? `${latestBatterySOC.toFixed(0)}%` : '-'"
        :icon="PhBatteryCharging"
        icon-color="text-teal-400"
        icon-bg-color="bg-teal-400/15"
        :value-color="latestBatterySOC !== null ? 'text-teal-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Grid"
        :value="latestGridPower !== 0 ? formatPower(Math.abs(latestGridPower)) : '-'"
        :sub-value="latestGridPower > 0 ? 'importing' : latestGridPower < 0 ? 'exporting' : ''"
        :icon="PhPlug"
        icon-color="text-sky-400"
        icon-bg-color="bg-sky-400/15"
        :value-color="latestGridPower !== 0 ? 'text-sky-400' : 'text-base-content/30'"
      />
      <KpiCard
        label="Miners"
        :value="`${runningMiners} / ${activeMiners}`"
        :sub-value="`of ${totalMiners} total`"
        :icon="PhPower"
        icon-color="text-primary"
        icon-bg-color="bg-primary/15"
        value-color="text-primary"
      />
      <KpiCard
        label="Optimization Units"
        :value="`${enabledUnits} / ${totalUnits}`"
        sub-value="units enabled"
        :icon="PhGraph"
        icon-color="text-teal-400"
        icon-bg-color="bg-teal-400/15"
        value-color="text-teal-400"
      />
    </div>

    <!-- Main Content: 2/3 + 1/3 layout -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-5">
      <!-- Left Column: Charts -->
      <div class="xl:col-span-2 space-y-5">
        <!-- Mining Charts -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhCpu :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Mining
            </h2>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-3">
            <ChartPanel
              title="Hash Rate"
              :icon="PhCpu"
              icon-color="text-primary"
              :chart-height="160"
              :has-data="hashRateSeries.length > 1"
              v-slot="{ expanded, expandedHeight, showMinerEvents }"
            >
              <RealtimeChart
                v-if="hashRateSeries.length > 1"
                :data="hashRateSeries"
                :height="expanded ? expandedHeight : 136"
                class="w-full h-full"
                series-name="Hash Rate"
                :line-color="CHART_COLOR_PRIMARY"
                :format-value="formatHashRateValue"
                :miner-events="minerOnOffEvents"
                :show-miner-events="showMinerEvents"
              />
            </ChartPanel>
            <ChartPanel
              title="Power Consumption"
              :icon="PhLightning"
              icon-color="text-warning"
              :chart-height="160"
              :has-data="powerSeries.length > 1"
              v-slot="{ expanded, expandedHeight, showMinerEvents }"
            >
              <RealtimeChart
                v-if="powerSeries.length > 1"
                :data="powerSeries"
                :height="expanded ? expandedHeight : 136"
                class="w-full h-full"
                series-name="Power"
                :line-color="CHART_COLOR_WARNING"
                :format-value="formatPowerValue"
                :miner-events="minerOnOffEvents"
                :show-miner-events="showMinerEvents"
              />
            </ChartPanel>
            <ChartPanel
              title="Temperature"
              :icon="PhThermometer"
              icon-color="text-red-400"
              :chart-height="160"
            />
          </div>
        </div>

        <!-- Energy Charts -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhSun :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Energy
            </h2>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <ChartPanel
              title="Home Consumption"
              :icon="PhHouseLine"
              icon-color="text-orange-400"
              :chart-height="160"
              :has-data="consumptionSeries.length > 1"
              v-slot="{ expanded, expandedHeight, showMinerEvents }"
            >
              <RealtimeChart
                v-if="consumptionSeries.length > 1"
                :data="consumptionSeries"
                :height="expanded ? expandedHeight : 136"
                class="w-full h-full"
                series-name="Consumption"
                :line-color="CHART_COLOR_CONSUMPTION"
                :format-value="formatPowerValue"
                :miner-events="minerOnOffEvents"
                :show-miner-events="showMinerEvents"
              />
            </ChartPanel>
            <ChartPanel
              title="Energy Production"
              :icon="PhSun"
              icon-color="text-yellow-400"
              :chart-height="160"
              :has-data="energyProductionSeries.length > 1"
              v-slot="{ expanded, expandedHeight, showMinerEvents }"
            >
              <RealtimeChart
                v-if="energyProductionSeries.length > 1"
                :data="energyProductionSeries"
                :height="expanded ? expandedHeight : 136"
                class="w-full h-full"
                series-name="Production"
                :line-color="CHART_COLOR_SOLAR"
                :format-value="formatPowerValue"
                :miner-events="minerOnOffEvents"
                :show-miner-events="showMinerEvents"
              />
            </ChartPanel>
            <ChartPanel
              title="Battery"
              :icon="PhBatteryCharging"
              icon-color="text-teal-400"
              :chart-height="160"
              :has-data="batterySOCSeries.length > 1"
              v-slot="{ expanded, expandedHeight, showMinerEvents }"
            >
              <RealtimeChart
                v-if="batterySOCSeries.length > 1"
                :data="batterySOCSeries"
                :height="expanded ? expandedHeight : 136"
                class="w-full h-full"
                series-name="SOC %"
                :line-color="CHART_COLOR_BATTERY"
                :format-value="formatBatteryValue"
                :secondary-data="batteryPowerSeries"
                secondary-series-name="Power"
                :secondary-line-color="CHART_COLOR_BATTERY_POWER"
                :secondary-format-value="formatPowerValue"
                :miner-events="minerOnOffEvents"
                :show-miner-events="showMinerEvents"
              />
            </ChartPanel>
            <ChartPanel
              title="Grid Power"
              :icon="PhPlug"
              icon-color="text-sky-400"
              :chart-height="160"
              :has-data="gridPowerSeries.length > 1"
              v-slot="{ expanded, expandedHeight, showMinerEvents }"
            >
              <RealtimeChart
                v-if="gridPowerSeries.length > 1"
                :data="gridPowerSeries"
                :height="expanded ? expandedHeight : 136"
                class="w-full h-full"
                series-name="Grid"
                :line-color="CHART_COLOR_GRID"
                :format-value="formatPowerValue"
                :miner-events="minerOnOffEvents"
                :show-miner-events="showMinerEvents"
              />
            </ChartPanel>
          </div>
        </div>

        <!-- Forecast Section -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhCloudSun :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Forecast
            </h2>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <ChartPanel
              title="Energy Forecast"
              :icon="PhChartLine"
              icon-color="text-indigo-400"
              :chart-height="160"
              :has-data="forecastSeries.length > 1"
              v-slot="{ expanded, expandedHeight }"
            >
              <RealtimeChart
                v-if="forecastSeries.length > 1"
                :data="forecastSeries"
                :height="expanded ? expandedHeight : 136"
                class="w-full h-full"
                series-name="Forecast"
                :line-color="CHART_COLOR_FORECAST"
                :format-value="formatPowerValue"
                :range="24 * 60 * 60 * 1000"
              />
            </ChartPanel>
            <!-- Forecast Summary Card -->
            <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-4">
              <div class="flex items-center gap-2 mb-4">
                <div class="w-7 h-7 rounded-lg bg-indigo-400/15 flex items-center justify-center">
                  <PhChartLine :size="14" class="text-indigo-400" />
                </div>
                <span class="text-sm font-medium text-base-content/70">Forecast Summary</span>
              </div>
              <div v-if="forecastSummary" class="grid grid-cols-3 gap-2">
                <div class="flex flex-col items-center gap-1 rounded-lg bg-base-content/5 p-3">
                  <span class="text-base font-bold text-indigo-400 leading-tight">{{ formatEnergy(forecastSummary.todayEnergy) }}</span>
                  <span class="text-[10px] text-base-content/40 uppercase tracking-wider mt-0.5">Today</span>
                </div>
                <div class="flex flex-col items-center gap-1 rounded-lg bg-base-content/5 p-3">
                  <span class="text-base font-bold text-indigo-300 leading-tight">{{ formatEnergy(forecastSummary.remainingToday) }}</span>
                  <span class="text-[10px] text-base-content/40 uppercase tracking-wider mt-0.5">Remaining</span>
                </div>
                <div class="flex flex-col items-center gap-1 rounded-lg bg-base-content/5 p-3">
                  <span class="text-base font-bold text-indigo-400/70 leading-tight">{{ formatEnergy(forecastSummary.tomorrowEnergy) }}</span>
                  <span class="text-[10px] text-base-content/40 uppercase tracking-wider mt-0.5">Tomorrow</span>
                </div>
              </div>
              <div v-else class="flex flex-col items-center justify-center py-6 text-center">
                <PhCloudSun :size="28" class="text-base-content/15 mb-2" />
                <span class="text-sm text-base-content/30">No forecast data</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Miner Fleet + Sun + Activity + Policy -->
      <div class="space-y-5">
        <!-- Miner Fleet -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhCpu :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Miner Fleet
            </h2>
            <span class="text-xs text-base-content/30 ml-auto">
              {{ runningMiners }} running
            </span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <MinerTile
              v-for="miner in minerStore.miners"
              :key="miner.id"
              :miner="miner"
            />
            <div
              v-if="minerStore.miners.length === 0"
              class="col-span-full flex flex-col items-center py-12 text-center"
            >
              <PhCpu :size="36" class="text-base-content/15 mb-2" />
              <span class="text-sm text-base-content/30">No miners configured</span>
              <RouterLink to="/settings/miners" class="text-xs text-primary/60 hover:text-primary mt-1">
                Add miners in Settings
              </RouterLink>
            </div>
          </div>
        </div>

        <!-- Sun Section -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhSunHorizon :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Sun
            </h2>
          </div>
          <div v-if="sunInfo" class="relative rounded-xl overflow-hidden border border-base-300/20 backdrop-blur-sm p-5 bg-base-100/30">
            <!-- Sun position arc -->
            <div class="flex flex-col items-center gap-4">
              <!-- Visual sun position indicator -->
              <div class="w-full flex justify-center">
                <div class="relative w-32 h-24">
                  <!-- Arc background -->
                  <svg class="absolute inset-0 w-full h-full" viewBox="0 0 120 60" preserveAspectRatio="xMidYMid meet">
                    <path d="M 10 55 Q 60 15 110 55" stroke="currentColor" stroke-width="1.5" fill="none" class="text-base-content/10"/>
                  </svg>
                  <!-- Sun position marker -->
                  <div class="absolute inset-0 flex items-end justify-center pb-1">
                    <div class="relative w-full h-full flex items-end justify-center">
                      <div
                        class="absolute transition-all duration-1000"
                        :style="{
                          left: `${sunArcProgress * 100}%`,
                          bottom: `${Math.sin(Math.PI * sunArcProgress) * 35}%`,
                          transform: 'translateX(-50%)'
                        }"
                      >
                        <div :class="sunInfo.isDay ? 'text-yellow-400 drop-shadow-lg' : 'text-slate-400 drop-shadow-lg'">
                          <PhSun :size="28" weight="fill" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Day/Night status badge -->
              <div class="w-full flex justify-center">
                <div :class="[
                  'px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-2',
                  sunInfo.isDay
                    ? 'bg-yellow-400/20 text-yellow-500 border border-yellow-400/30'
                    : 'bg-slate-600/20 text-slate-300 border border-slate-600/30'
                ]">
                  <div :class="[
                    'w-2 h-2 rounded-full',
                    sunInfo.isDay ? 'bg-yellow-400 animate-pulse' : 'bg-slate-400'
                  ]" />
                  {{ sunInfo.isDay ? 'Daytime' : 'Nighttime' }}
                </div>
              </div>

              <!-- Sunrise / Sunset row -->
              <div class="grid grid-cols-2 gap-3 w-full">
                <div class="rounded-lg bg-base-content/5 border border-base-content/10 p-4 flex flex-col items-center gap-3">
                  <span class="text-[10px] text-base-content/40 uppercase tracking-wider font-medium">Sunrise</span>
                  <div class="relative">
                    <PhSun :size="40" class="text-yellow-400" weight="fill" />
                    <div class="absolute inset-0 animate-pulse text-yellow-400 opacity-20">
                      <PhSun :size="40" weight="fill" />
                    </div>
                  </div>
                  <div class="flex flex-col items-center gap-1">
                    <span class="text-sm font-bold text-base-content/90">{{ sunInfo.sunriseTime }}</span>
                    <span v-if="sunInfo.timeToSunrise > 0" class="text-[10px] text-yellow-500 font-medium">
                      in {{ formatDuration(sunInfo.timeToSunrise) }}
                    </span>
                    <span v-else class="text-[10px] text-base-content/40 font-medium">
                      {{ formatDuration(sunInfo.timeToSunrise) }} ago
                    </span>
                  </div>
                </div>
                <div class="rounded-lg bg-base-content/5 border border-base-content/10 p-4 flex flex-col items-center gap-3">
                  <span class="text-[10px] text-base-content/40 uppercase tracking-wider font-medium">Sunset</span>
                  <div class="relative">
                    <PhSunHorizon :size="40" class="text-orange-400" weight="fill" />
                    <div class="absolute inset-0 animate-pulse text-orange-400 opacity-20">
                      <PhSunHorizon :size="40" weight="fill" />
                    </div>
                  </div>
                  <div class="flex flex-col items-center gap-1">
                    <span class="text-sm font-bold text-base-content/90">{{ sunInfo.sunsetTime }}</span>
                    <span v-if="sunInfo.timeToSunset > 0" class="text-[10px] text-orange-500 font-medium">
                      in {{ formatDuration(sunInfo.timeToSunset) }}
                    </span>
                    <span v-else class="text-[10px] text-base-content/40 font-medium">
                      {{ formatDuration(sunInfo.timeToSunset) }} ago
                    </span>
                  </div>
                </div>
              </div>

              <!-- Extra info row -->
              <div class="w-full flex items-center justify-between px-2 py-2 rounded-lg bg-base-content/5 border border-base-content/10">
                <div class="flex flex-col items-center gap-0.5">
                  <span class="text-xs text-base-content/40 uppercase tracking-wider">Daylight</span>
                  <span class="text-sm font-bold text-base-content/80">{{ sunInfo.daylightHours }}h</span>
                </div>
                <div class="h-8 w-px bg-base-content/10" />
                <div class="flex flex-col items-center gap-0.5">
                  <span class="text-xs text-base-content/40 uppercase tracking-wider">Elevation</span>
                  <span v-if="sunInfo.elevation != null" class="text-sm font-bold text-base-content/80">{{ sunInfo.elevation.toFixed(1) }}°</span>
                  <span v-else class="text-sm text-base-content/40">N/A</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-4 flex flex-col items-center justify-center py-6 text-center">
            <PhSunHorizon :size="28" class="text-base-content/15 mb-2" />
            <span class="text-sm text-base-content/30">No sun data</span>
          </div>
        </div>

        <!-- Activity Feed -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhClockCounterClockwise :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Activity
            </h2>
          </div>
          <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-3 max-h-[420px] overflow-y-auto">
            <ActivityFeed :events="events" />
          </div>
        </div>

        <!-- Last Policy Action (placeholder) -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <PhShieldCheck :size="16" class="text-base-content/40" />
            <h2 class="text-sm font-semibold text-base-content/60 uppercase tracking-wider">
              Last Policy Rule
            </h2>
          </div>
          <div class="rounded-xl border border-base-300/20 bg-base-100/30 backdrop-blur-sm p-4">
            <div class="flex flex-col items-center justify-center py-6 text-center">
              <div class="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                <PhShieldCheck :size="24" class="text-primary/30" />
              </div>
              <span class="text-sm text-base-content/30">No rule engaged yet</span>
              <span class="text-[11px] text-base-content/20 mt-1">
                Rules trigger based on energy conditions
              </span>
            </div>
          </div>
        </div>

        <!-- Miner On/Off Events -->
        <ChartPanel
          title="Miner On/Off Events"
          :icon="PhPower"
          icon-color="text-sky-400"
          :chart-height="140"
          :has-data="minerOnOffEvents.length > 0"
          :maximizable="false"
        >
          <div v-if="minerOnOffEvents.length > 0" class="space-y-1.5 max-h-[120px] overflow-y-auto">
            <div
              v-for="(evt, i) in [...minerOnOffEvents].reverse().slice(0, 20)"
              :key="i"
              class="flex items-center gap-2 text-xs px-1 py-1 rounded hover:bg-base-content/5"
            >
              <span
                class="w-2 h-2 rounded-full shrink-0"
                :class="evt.action === 'on' ? 'bg-emerald-400' : 'bg-red-400'"
              />
              <span class="text-base-content/50 tabular-nums shrink-0">
                {{ new Date(evt.time * 1000).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }}
              </span>
              <span class="text-base-content/70 truncate">{{ evt.minerName }}</span>
              <span
                class="ml-auto text-[10px] font-semibold uppercase tracking-wider shrink-0"
                :class="evt.action === 'on' ? 'text-emerald-400' : 'text-red-400'"
              >
                {{ evt.action }}
              </span>
            </div>
          </div>
        </ChartPanel>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
