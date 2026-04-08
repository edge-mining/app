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
const CHART_COLOR_CONSUMPTION = 'rgba(251, 146, 60, 0.9)'; // orange-400
import KpiCard from "../components/dashboard/KpiCard.vue";
import MinerTile from "../components/dashboard/MinerTile.vue";
import ChartPanel from "../components/dashboard/ChartPanel.vue";
import RealtimeChart from "../components/dashboard/RealtimeChart.vue";
import ActivityFeed from "../components/dashboard/ActivityFeed.vue";
import SunCard from "../components/dashboard/SunCard.vue";
import ForecastSummaryCard from "../components/dashboard/ForecastSummaryCard.vue";
import ForecastChart from "../components/dashboard/ForecastChart.vue";
import type { ForecastIntervalData } from "../components/dashboard/ForecastChart.vue";
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
  PhCloudSun,
} from "@phosphor-icons/vue";

const minerStore = useMinerStore();
const optimizationUnitStore = useOptimizationUnitStore();
const { lastUpdated, isPolling, events, hashRateSeries, powerSeries, energyProductionSeries, batterySOCSeries, batteryPowerSeries, gridPowerSeries, consumptionSeries, minerOnOffEvents, forecastPowerPoints, latestDecisionalContexts } = useDashboardPolling(5000);

// ---------- KPI computations ----------

const totalMiners = computed(() => minerStore.miners.length);

const runningMiners = computed(
  () => minerStore.miners.filter((m) => {
    const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
    return state?.status === "on";
  }).length
);

const activeMiners = computed(
  () => minerStore.miners.filter((m) => m.active).length
);

const totalHashRate = computed(() => {
  let total = 0;
  for (const m of minerStore.miners) {
    const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
    if (state?.status === "on" && state.hash_rate?.value) {
      total += normalizeHashRate(state.hash_rate.value, state.hash_rate.unit || "TH/s");
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
    .filter((m) => {
      const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
      return state?.status === "on";
    })
    .reduce((sum, m) => {
      const state = m.id ? minerStore.minerStates.get(m.id) : undefined;
      return sum + (state?.power_consumption || 0);
    }, 0);
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
  if (v === 0) return "0";
  const abs = Math.abs(v);
  if (abs >= 1000) return `${Math.round(v / 1000)} PH/s`;
  if (abs >= 1) return `${Math.round(v)} TH/s`;
  if (abs >= 0.001) return `${Math.round(v * 1000)} GH/s`;
  return `${Math.round(v * 1000000)} MH/s`;
}

function formatPowerValue(v: number): string {
  if (v === 0) return "0 W";
  const abs = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (abs >= 1000000) return `${sign}${(abs / 1000000).toFixed(1)} MW`;
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(1)} kW`;
  return `${sign}${Math.round(abs)} W`;
}

function formatBatteryValue(v: number): string {
  return `${Math.round(v)}%`;
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

// Forecast chart data: energy (Wh) per interval + max power per interval
// Uses raw intervals without aggregation
const forecastIntervalData = computed<ForecastIntervalData[]>(() => {
  const ctxs = latestDecisionalContexts.value;
  if (!ctxs || ctxs.size === 0) return [];

  const intervals: ForecastIntervalData[] = [];

  for (const ctx of ctxs.values()) {
    if (!ctx.forecast?.intervals) continue;
    for (const interval of ctx.forecast.intervals) {
      const startMs = new Date(interval.start).getTime();
      const energy = interval.energy ?? 0;
      const maxPower = interval.power_points?.length
        ? Math.max(...interval.power_points.map((p) => p.power))
        : 0;

      intervals.push({ time: startMs, energy, maxPower });
    }
  }

  // Deduplicate by time (multiple units may share same intervals)
  const seen = new Set<number>();
  return intervals
    .filter((item) => {
      if (seen.has(item.time)) return false;
      seen.add(item.time);
      return true;
    })
    .sort((a, b) => a.time - b.time);
});


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
              :has-data="forecastIntervalData.length > 1"
              v-slot="{ expanded, expandedHeight }"
            >
              <ForecastChart
                v-if="forecastIntervalData.length > 1"
                :data="forecastIntervalData"
                :height="expanded ? expandedHeight : 136"
              />
            </ChartPanel>
            <!-- Forecast Summary Card -->
            <ForecastSummaryCard
              :latest-decisional-contexts="latestDecisionalContexts"
              :forecast-power-points="forecastPowerPoints"
            />
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
              :state="miner.id ? minerStore.minerStates.get(miner.id) : undefined"
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
        <SunCard :latest-decisional-contexts="latestDecisionalContexts" />

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
